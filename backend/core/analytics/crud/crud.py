"""
Some stuff I will need to update at some point
"""

from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

from django.utils import timezone

from backend.core.constants import TIME_FILTER_ALL, TIME_FILTER_CURRENT

from .common import (
    _build_children,
    _subtree_terminal_exercise_ids,
    execute_sql,
    get_dimension_hierarchies,
    rollup_exercise_total_volume,
)

SQL_DIR = Path(__file__).resolve().parent.parent / "sql"

_VOLUME_METRIC_KEYS = (
    "total_volume",
    "previous_week",
    "previous_week_to_date",
    "previous_month",
    "previous_month_to_date",
    "previous_year",
    "previous_year_to_date",
    "plan_volume",
    # Full-period (not just to-date) plan targets — only meaningful for period=wtd/mtd/ytd;
    # the "all"/custom-range path has no enclosing week/month/year, so these stay None there.
    "plan_week_full",
    "plan_month_full",
    "plan_year_full",
)

# Plan metrics use NULL = "no plan for this grain" (distinct from a real 0 target).
_PLAN_METRIC_KEYS = frozenset(
    {
        "plan_volume",
        "plan_week_full",
        "plan_month_full",
        "plan_year_full",
    }
)


def _metric_value(row: dict, key: str):
    """Coerce missing actuals to 0; preserve None for plan metrics (no plan)."""
    val = row.get(key)
    if key in _PLAN_METRIC_KEYS:
        return None if val is None else float(val)
    return float(val or 0)


def _sum_nullable(values) -> float | None:
    """Sum non-None values; return None when every input is None (no plan anywhere)."""
    present = [v for v in values if v is not None]
    if not present:
        return None
    return float(sum(present))


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


def _rollup_nullable_by_parent(hierarchy_rows, by_exercise_id: dict, parent_id) -> dict:
    """Roll up a nullable metric (plan_*) to each direct child of parent_id."""
    children, _ = _build_children(hierarchy_rows)
    cache: dict = {}
    out: dict = {}
    for r in hierarchy_rows:
        if r["parent_id"] != parent_id:
            continue
        cid = r["current_id"]
        terminals = _subtree_terminal_exercise_ids(cid, children, cache)
        out[cid] = _sum_nullable(by_exercise_id.get(eid) for eid in terminals)
    return out


def _rollup_volume_rows(volume_rows, parent_id):
    hierarchy_rows = get_dimension_hierarchies("exercise")
    by_metric = {
        key: {row["exercise_id"]: _metric_value(row, key) for row in volume_rows} for key in _VOLUME_METRIC_KEYS
    }

    # total_volume / prior-period metrics: missing → 0 (existing rollup).
    current = rollup_exercise_total_volume(hierarchy_rows, by_metric["total_volume"], parent_id)
    rolled = {}
    for key in _VOLUME_METRIC_KEYS[1:]:
        if key in _PLAN_METRIC_KEYS:
            rolled[key] = _rollup_nullable_by_parent(hierarchy_rows, by_metric[key], parent_id)
        else:
            rolled[key] = {
                row["exercise_id"]: row["total_volume"]
                for row in rollup_exercise_total_volume(hierarchy_rows, by_metric[key], parent_id)
            }

    for row in current:
        eid = row["exercise_id"]
        for key in _VOLUME_METRIC_KEYS[1:]:
            if key in _PLAN_METRIC_KEYS:
                row[key] = rolled[key].get(eid)  # may be None
            else:
                row[key] = rolled[key].get(eid, 0)

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
    - prev week/month/year  → always their own dbt models (ref() chained from
      total_daily_volume), regardless of which current period was requested. Each has
      a "full" (complete prior period) and a "to date" (capped at today's relative day)
      variant, e.g. previous_month vs previous_month_to_date.
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
            plan_vol = cur.get("plan_volume")
            volume_rows.append(
                {
                    "exercise_id": eid,
                    "total_volume": cur.get("total_volume") or 0,
                    "previous_week": prev.get("previous_week") or 0,
                    "previous_week_to_date": prev.get("previous_week_to_date") or 0,
                    "previous_month": prev.get("previous_month") or 0,
                    "previous_month_to_date": prev.get("previous_month_to_date") or 0,
                    "previous_year": prev.get("previous_year") or 0,
                    "previous_year_to_date": prev.get("previous_year_to_date") or 0,
                    # NULL when no plan rows in range (SQL FILTER returns NULL).
                    "plan_volume": None if plan_vol is None else float(plan_vol),
                    # No enclosing week/month/year for a custom range.
                    "plan_week_full": None,
                    "plan_month_full": None,
                    "plan_year_full": None,
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
        volume_by_date[d][bucket][eid] = row["total_volume"] or 0

    results = []
    for d, buckets in volume_by_date.items():
        actuals_total = sum(buckets["actuals"].get(eid, 0) for eid in terminals)
        plan_total = sum(buckets["plan"].get(eid, 0) for eid in terminals)
        if actuals_total <= 0 and plan_total <= 0:
            continue

        results.append(
            {
                "date": d,
                "actuals_volume": actuals_total,
                "plan_volume": plan_total,
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


def get_workout_sessions(user_id: int, start_date: date | None, end_date: date | None):
    """List distinct workout sessions (date + workout_number) with split label.

    Also returns period comparison counts for the Sessions Total row (vs prior
    week/month/year and vs plan), keyed like the volume table metrics.
    """
    query = (SQL_DIR / "get_workout_sessions.sql").read_text()
    results = execute_sql(
        query,
        {
            "user_id": user_id,
            "start_date": start_date,
            "end_date": end_date,
        },
    )
    comparisons = get_session_period_comparisons(user_id)
    return {"results": results, "comparisons": comparisons, "total": len(results)}


_SESSION_COMPARISON_KEYS = (
    "sessions_this_week",
    "previous_week",
    "previous_week_to_date",
    "sessions_this_month",
    "previous_month",
    "previous_month_to_date",
    "sessions_this_year",
    "previous_year",
    "previous_year_to_date",
    "plan_week",
    "plan_month",
    "plan_year",
    "plan_week_full",
    "plan_month_full",
    "plan_year_full",
)


def get_session_period_comparisons(user_id: int) -> dict[str, int | None]:
    """Session counts for current/prior week/month/year + plan targets.

    Plan keys are None when the count is 0 *and* we want N/A semantics… actually
    0 planned sessions is a real zero target when the user has plans elsewhere;
    we treat 0 as a real baseline (frontend can still show +100%). Callers that
    need "no plan at all" can check home-level flags later.
    """
    today = timezone.localdate()
    week = _period_bounds(today, "week")
    month = _period_bounds(today, "month")
    year = _period_bounds(today, "year")

    def to_date_end(cur_start: date, cur_end: date, prev_start: date) -> date:
        return prev_start + timedelta(days=(cur_end - cur_start).days)

    query = (SQL_DIR / "get_session_period_comparisons.sql").read_text()
    rows = execute_sql(
        query,
        {
            "user_id": user_id,
            "cur_week_start": week["cur_start"],
            "cur_week_end": week["cur_end"],
            "prev_week_start": week["prev_start"],
            "prev_week_end": week["prev_end"],
            "prev_week_to_date_end": to_date_end(week["cur_start"], week["cur_end"], week["prev_start"]),
            "week_full_end": week["full_end"],
            "cur_month_start": month["cur_start"],
            "cur_month_end": month["cur_end"],
            "prev_month_start": month["prev_start"],
            "prev_month_end": month["prev_end"],
            "prev_month_to_date_end": to_date_end(month["cur_start"], month["cur_end"], month["prev_start"]),
            "month_full_end": month["full_end"],
            "cur_year_start": year["cur_start"],
            "cur_year_end": year["cur_end"],
            "prev_year_start": year["prev_start"],
            "prev_year_end": year["prev_end"],
            "prev_year_to_date_end": to_date_end(year["cur_start"], year["cur_end"], year["prev_start"]),
            "year_full_end": year["full_end"],
        },
    )
    row = rows[0] if rows else {}
    out: dict[str, int | None] = {}
    for key in _SESSION_COMPARISON_KEYS:
        val = row.get(key)
        if key.startswith("plan_"):
            # NULL plan count from SQL is rare (COUNT returns 0); keep int.
            # Frontend treats plan_volume null as N/A; for sessions we use 0 as
            # "no planned sessions in window" and still compute a delta, unless
            # we later add a has_plan flag. Match volume's null-for-no-plan by
            # returning None when count is 0 so Total shows N/A when nothing planned.
            out[key] = None if val is None or int(val) == 0 else int(val)
        else:
            out[key] = int(val or 0)
    return out


def _period_bounds(today: date, unit: str) -> dict[str, date]:
    """Start/end for home-summary workout counts (this/last week, month, year).

    Returns to-date bounds (cur_end = today) plus full-period ends for plan targets
    (week_full_end / month_full_end / year_full_end = last day of the enclosing period).
    """
    if unit == "week":
        cur_start = today - timedelta(days=today.isoweekday() - 1)
        cur_end = today
        full_end = cur_start + timedelta(days=6)
    elif unit == "year":
        cur_start = today.replace(month=1, day=1)
        cur_end = today
        full_end = today.replace(month=12, day=31)
    else:
        cur_start = today.replace(day=1)
        cur_end = today
        if today.month == 12:
            full_end = today.replace(day=31)
        else:
            full_end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)

    prev_end = cur_start - timedelta(days=1)
    if unit == "week":
        prev_start = prev_end - timedelta(days=6)
    elif unit == "year":
        prev_start = cur_start.replace(year=cur_start.year - 1)
        prev_end = prev_start.replace(month=12, day=31)
    else:
        prev_start = prev_end.replace(day=1)

    return {
        "cur_start": cur_start,
        "cur_end": cur_end,
        "prev_start": prev_start,
        "prev_end": prev_end,
        "full_end": full_end,
    }


_WORKOUT_COUNT_KEYS = (
    "workouts_this_week",
    "workouts_last_week",
    "workouts_this_month",
    "workouts_last_month",
    "workouts_this_year",
    "workouts_last_year",
    "workouts_planned_this_week",
    "workouts_planned_this_month",
    "workouts_planned_this_year",
    "workouts_planned_week_full",
    "workouts_planned_month_full",
    "workouts_planned_year_full",
)


def get_workout_counts(user_id: int) -> dict[str, int]:
    """Count distinct gym days (see `workout_sets_daily`) for this/last week, month, year.

    Includes planned gym days for the same to-date windows and for the full
    enclosing week/month/year (mirroring volume's plan-to-date vs plan-full).
    """
    today = timezone.localdate()
    week = _period_bounds(today, "week")
    month = _period_bounds(today, "month")
    year = _period_bounds(today, "year")

    query = (SQL_DIR / "get_workout_counts.sql").read_text()
    rows = execute_sql(
        query,
        {
            "user_id": user_id,
            "cur_week_start": week["cur_start"],
            "cur_week_end": week["cur_end"],
            "prev_week_start": week["prev_start"],
            "prev_week_end": week["prev_end"],
            "week_full_end": week["full_end"],
            "cur_month_start": month["cur_start"],
            "cur_month_end": month["cur_end"],
            "prev_month_start": month["prev_start"],
            "prev_month_end": month["prev_end"],
            "month_full_end": month["full_end"],
            "cur_year_start": year["cur_start"],
            "cur_year_end": year["cur_end"],
            "prev_year_start": year["prev_start"],
            "prev_year_end": year["prev_end"],
            "year_full_end": year["full_end"],
        },
    )

    row = rows[0] if rows else {}
    return {key: int(row.get(key) or 0) for key in _WORKOUT_COUNT_KEYS}


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
