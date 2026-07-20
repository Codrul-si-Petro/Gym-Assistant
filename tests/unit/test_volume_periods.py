from pathlib import Path

from backend.core.workout_constants import (
    SCENARIO_ACTUALS,
    SCENARIO_PLAN,
    TIME_FILTER_ALL,
    TIME_FILTER_CURRENT,
    TIME_FILTER_MTD,
    TIME_FILTER_PREV,
    TIME_FILTER_PREV_MONTH,
    TIME_FILTER_PREV_WEEK,
    TIME_FILTER_PREV_YEAR,
    TIME_FILTER_WTD,
    TIME_FILTER_YTD,
)

ANALYTICS_SQL_DIR = Path(__file__).resolve().parents[2] / "backend" / "core" / "analytics" / "sql"
DBT_ANALYTICS_DIR = Path(__file__).resolve().parents[2] / "db" / "transformation" / "models" / "analytics"


def test_scenario_constants():
    assert SCENARIO_ACTUALS == "actuals"
    assert SCENARIO_PLAN == "plan"


def test_time_filter_current_slices_are_stable():
    assert TIME_FILTER_CURRENT == (
        TIME_FILTER_ALL,
        TIME_FILTER_WTD,
        TIME_FILTER_MTD,
        TIME_FILTER_YTD,
    )


def test_time_filter_prev_slices_are_stable():
    assert TIME_FILTER_PREV == (
        TIME_FILTER_PREV_WEEK,
        TIME_FILTER_PREV_MONTH,
        TIME_FILTER_PREV_YEAR,
    )


def test_prev_period_slices_are_separate_dbt_models():
    """Each comparison period is its own model chained with ref() — not one monolith."""
    for model_name in ("volume_prev_week", "volume_prev_month", "volume_prev_year"):
        model_path = DBT_ANALYTICS_DIR / f"{model_name}.sql"
        assert model_path.exists(), f"missing dbt model {model_path}"
        model_sql = model_path.read_text()
        assert "ref('total_daily_volume')" in model_sql
        assert "GROUP BY" in model_sql


def test_volume_to_date_model_is_dated_with_current_period_flags():
    """ALL and X-to-date live in dated fact tables, not pre-summed single rows."""
    model_sql = (DBT_ANALYTICS_DIR / "volume_to_date.sql").read_text()
    assert "date_id" in model_sql
    assert "ref('total_daily_volume')" in model_sql
    for flag in ("is_wtd", "is_mtd", "is_ytd"):
        assert flag in model_sql


def test_total_daily_volume_is_dated_and_backs_the_all_period():
    """'all' reads real per-date rows — no precomputed 'all' aggregate slice."""
    model_sql = (DBT_ANALYTICS_DIR / "total_daily_volume.sql").read_text()
    assert "date_id" in model_sql


def test_total_volume_extract_reads_dated_facts_only():
    sql = (ANALYTICS_SQL_DIR / "get_total_volume_periods.sql").read_text()
    assert "volume_to_date" in sql
    assert "volume_prev_week" in sql
    assert "volume_prev_month" in sql
    assert "volume_prev_year" in sql
    assert "%(time_filter)s" in sql
    # No request-time period window math (no calendar arithmetic in the extract)
    assert "date_trunc" not in sql
    assert "INTERVAL" not in sql


def test_custom_range_extract_reads_daily_fact_directly():
    sql = (ANALYTICS_SQL_DIR / "get_total_volume_custom_range.sql").read_text()
    assert "total_daily_volume" in sql
    assert "%(start_date)s" in sql
    assert "%(end_date)s" in sql
