"""
Some stuff I will need to update at some point
"""

from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

from django.utils import timezone

from backend.core.workout_constants import TIME_FILTER_ALL, TIME_FILTER_CURRENT

from .common import (
    _build_children,
    _subtree_terminal_exercise_ids,
    execute_sql,
    get_dimension_hierarchies,
    rollup_exercise_total_volume,
)

SQL_DIR = Path(__file__).resolve().parent.parent / "sql"

_VOLUME_METRIC_KEYS = (
    "total_volume_kg",
    "prev_week_volume_kg",
    "prev_month_volume_kg",
    "prev_year_volume_kg",
    "plan_volume_kg",
)


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


def _rollup_volume_rows(volume_rows, parent_id):
    hierarchy_rows = get_dimension_hierarchies("exercise")
    by_metric = {key: {row["exercise_id"]: row[key] or 0 for row in volume_rows} for key in _VOLUME_METRIC_KEYS}

    current = rollup_exercise_total_volume(hierarchy_rows, by_metric["total_volume_kg"], parent_id)
    rolled = {
        key: {
            row["exercise_id"]: row["total_volume_kg"]
            for row in rollup_exercise_total_volume(hierarchy_rows, by_metric[key], parent_id)
        }
        for key in _VOLUME_METRIC_KEYS[1:]
    }

    for row in current:
        eid = row["exercise_id"]
        row["prev_week_volume_kg"] = rolled["prev_week_volume_kg"].get(eid, 0)
        row["prev_month_volume_kg"] = rolled["prev_month_volume_kg"].get(eid, 0)
        row["prev_year_volume_kg"] = rolled["prev_year_volume_kg"].get(eid, 0)
        row["plan_volume_kg"] = rolled["plan_volume_kg"].get(eid, 0)

    return current


def get_total_volume(
    user_id: int,
    parent_id: int | None,
    period: str = TIME_FILTER_ALL,
    start_date: date | None = None,
    end_date: date | None = None,
):
    """Read precomputed volume facts; hierarchy rollup is the only app-side work.

    - period=all           → dated daily fact (analytics.total_daily_volume), any/no range
    - period=wtd|mtd|ytd    → analytics.volume_to_date, filtered by the matching flag
    - prev week/month/year  → always their own complete-period dbt models (ref() chained
      from total_daily_volume), regardless of which current period was requested
    """
    time_filter = (period or TIME_FILTER_ALL).lower()
    if time_filter not in TIME_FILTER_CURRENT:
        time_filter = TIME_FILTER_ALL

    if time_filter == TIME_FILTER_ALL:
        current_rows = execute_sql(
            (SQL_DIR / "get_total_volume_custom_range.sql").read_text(),
            {"user_id": user_id, "start_date": start_date, "end_date": end_date},
        )
        prev_rows = execute_sql(
            (SQL_DIR / "get_volume_prev_periods.sql").read_text(),
            {"user_id": user_id},
        )
        prev_by_id = {row["exercise_id"]: row for row in prev_rows}
        current_by_id = {row["exercise_id"]: row for row in current_rows}
        exercise_ids = set(current_by_id) | set(prev_by_id)
        volume_rows = []
        for eid in exercise_ids:
            cur = current_by_id.get(eid) or {}
            prev = prev_by_id.get(eid) or {}
            volume_rows.append(
                {
                    "exercise_id": eid,
                    "total_volume_kg": cur.get("total_volume_kg") or 0,
                    "prev_week_volume_kg": prev.get("prev_week_volume_kg") or 0,
                    "prev_month_volume_kg": prev.get("prev_month_volume_kg") or 0,
                    "prev_year_volume_kg": prev.get("prev_year_volume_kg") or 0,
                    "plan_volume_kg": cur.get("plan_volume_kg") or 0,
                }
            )
        return _rollup_volume_rows(volume_rows, parent_id)

    volume_rows = execute_sql(
        (SQL_DIR / "get_total_volume_periods.sql").read_text(),
        {"user_id": user_id, "time_filter": time_filter},
    )
    return _rollup_volume_rows(volume_rows, parent_id)


def get_total_volume_per_day(
    user_id: int,
    start_date: date | None,
    end_date: date | None,
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

    volume_by_date: defaultdict[date, dict[str, dict[int, float]]] = defaultdict(lambda: {"actuals": {}, "plan": {}})
    for row in rows:
        d = row["date_id"]
        eid = row["exercise_id"]
        scenario = row.get("scenario") or "actuals"
        bucket = "plan" if scenario == "plan" else "actuals"
        volume_by_date[d][bucket][eid] = row["total_volume_kg"] or 0

    results = []
    for d, buckets in volume_by_date.items():
        actuals_total = sum(buckets["actuals"].get(eid, 0) for eid in terminals)
        plan_total = sum(buckets["plan"].get(eid, 0) for eid in terminals)
        if actuals_total <= 0 and plan_total <= 0:
            continue

        results.append(
            {
                "date": d,
                "actuals_volume_kg": actuals_total,
                "plan_volume_kg": plan_total,
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
    """Start/end for home-summary workout counts (this/last week and month)."""
    if unit == "week":
        cur_start = today - timedelta(days=today.isoweekday() - 1)
        cur_end = today
    elif unit == "year":
        cur_start = today.replace(month=1, day=1)
        cur_end = today
    else:
        cur_start = today.replace(day=1)
        cur_end = today

    prev_end = cur_start - timedelta(days=1)
    if unit == "week":
        prev_start = prev_end - timedelta(days=6)
    elif unit == "year":
        prev_start = cur_start.replace(year=cur_start.year - 1)
        prev_end = prev_start.replace(month=12, day=31)
    else:
        prev_start = prev_end.replace(day=1)

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
