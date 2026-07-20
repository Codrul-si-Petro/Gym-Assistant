"""
Some stuff I will need to update at some point
"""

from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

from django.utils import timezone

from .common import (
    _build_children,
    _subtree_terminal_exercise_ids,
    execute_sql,
    get_dimension_hierarchies,
    rollup_exercise_total_volume,
)

SQL_DIR = Path(__file__).resolve().parent.parent / "sql"


def get_rest_days(user_id):
    query_file = SQL_DIR / "get_user_rest_days.sql"
    query = query_file.read_text()

    return execute_sql(
        query,
        {
            "user_id": user_id,
        },
    )


def get_favourite_exercises(user_id, start_date, end_date):
    query_file = SQL_DIR / "get_favourite_exercises.sql"
    query = query_file.read_text()

    return execute_sql(
        query,
        {
            "user_id": user_id,
            "start_date": start_date,
            "end_date": end_date,
        },
    )


def get_total_volume(user_id: int, start_date: date, end_date: date, parent_id: int | None):
    query_file = SQL_DIR / "get_total_volume.sql"
    query = query_file.read_text()

    volume_rows = execute_sql(
        query,
        {
            "user_id": user_id,
            "start_date": start_date,
            "end_date": end_date,
        },
    )

    hierarchy_rows = get_dimension_hierarchies("exercise")

    volume_by_exercise_id = {row["exercise_id"]: row["total_volume_kg"] or 0 for row in volume_rows}

    return rollup_exercise_total_volume(hierarchy_rows, volume_by_exercise_id, parent_id)


def get_total_volume_per_day(
    user_id: int,
    start_date: date,
    end_date: date,
    exercise_id: int,
):
    query_file = SQL_DIR / "get_total_volumes_daily.sql"
    query = query_file.read_text()

    rows = execute_sql(
        query,
        {
            "user_id": user_id,
            "start_date": start_date,
            "end_date": end_date,
        },
    )

    hierarchy_rows = get_dimension_hierarchies("exercise")

    children, _ = _build_children(hierarchy_rows)
    cache: dict[int, frozenset[int]] = {}

    terminals = _subtree_terminal_exercise_ids(
        exercise_id,
        children,
        cache,
    )

    volume_by_date: defaultdict[date, dict[int, float]] = defaultdict(dict)
    for row in rows:
        d = row["date_id"]
        eid = row["exercise_id"]
        volume_by_date[d][eid] = row["total_volume_kg"] or 0

    results = []
    for d, volume_by_exercise_id in volume_by_date.items():
        total = sum(volume_by_exercise_id.get(eid, 0) for eid in terminals)
        if total <= 0:
            continue

        results.append(
            {
                "date": d,
                "total_volume_kg": total,
            }
        )

    results.sort(key=lambda x: x["date"])

    return results


def get_workout_splits(user_id: int, start_date: date | None, end_date: date | None):
    query_file = SQL_DIR / "get_workout_splits.sql"
    query = query_file.read_text()
    return execute_sql(
        query,
        {
            "user_id": user_id,
            "start_date": start_date,
            "end_date": end_date,
        },
    )


def get_gym_weekdays(user_id: int, start_date: date | None, end_date: date | None):
    query_file = SQL_DIR / "get_gym_weekdays.sql"
    query = query_file.read_text()
    return execute_sql(
        query,
        {
            "user_id": user_id,
            "start_date": start_date,
            "end_date": end_date,
        },
    )


def _period_bounds(today: date, unit: str) -> dict[str, date]:
    """Start/end dates for the current and prior Mon–Sun week or calendar month.

    Current periods end "today" rather than the natural week/month end, since a
    period isn't over yet — this keeps this-week/this-month counts from silently
    including future dates that can't have workouts.
    """
    if unit == "week":
        cur_start = today - timedelta(days=today.isoweekday() - 1)
        cur_end = today
    else:
        cur_start = today.replace(day=1)
        cur_end = today

    prev_end = cur_start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=6) if unit == "week" else prev_end.replace(day=1)
    return {"cur_start": cur_start, "cur_end": cur_end, "prev_start": prev_start, "prev_end": prev_end}


def get_workout_counts(user_id: int) -> dict[str, int]:
    """Count distinct gym days (see `workout_sets_daily`) for this/last week and month."""
    today = timezone.localdate()
    week = _period_bounds(today, "week")
    month = _period_bounds(today, "month")

    query = (SQL_DIR / "get_workout_counts.sql").read_text()
    rows = execute_sql(
        query,
        {
            "user_id": user_id,
            "cur_week_start": week["cur_start"],
            "cur_week_end": week["cur_end"],
            "prev_week_start": week["prev_start"],
            "prev_week_end": week["prev_end"],
            "cur_month_start": month["cur_start"],
            "cur_month_end": month["cur_end"],
            "prev_month_start": month["prev_start"],
            "prev_month_end": month["prev_end"],
        },
    )

    row = rows[0] if rows else {}
    return {
        key: int(row.get(key) or 0)
        for key in ("workouts_this_week", "workouts_last_week", "workouts_this_month", "workouts_last_month")
    }


def get_home_summary(user_id: int):
    query_file = SQL_DIR / "get_home_summary.sql"
    query = query_file.read_text()
    rows = execute_sql(query, {"user_id": user_id})
    # Merged in regardless of whether `rows` is empty — a brand-new user with no
    # lifetime volume can still have workout counts once seeded/backfilled data lands.
    workout_counts = get_workout_counts(user_id)

    if not rows:
        return {
            "days_since_last_workout": None,
            "total_volume_kg": 0,
            "total_volume_lbs": 0,
            **workout_counts,
        }

    row = rows[0]
    last_date = row.get("last_workout_date")
    days_since = None
    if last_date:
        today = timezone.localdate()
        days_since = (today - last_date).days

    total_kg = float(row.get("total_volume_kg") or 0)
    return {
        "days_since_last_workout": days_since,
        "total_volume_kg": round(total_kg, 2),
        "total_volume_lbs": round(total_kg * 2.20462, 2),
        **workout_counts,
    }
