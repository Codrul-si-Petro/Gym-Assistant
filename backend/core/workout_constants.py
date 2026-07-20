"""Workout fact scenario and analytics time-filter values."""

SCENARIO_ACTUALS = "actuals"
SCENARIO_PLAN = "plan"
SCENARIO_CHOICES = (SCENARIO_ACTUALS, SCENARIO_PLAN)

# `period` query param values the total-volume API accepts.
# all           -> analytics.total_daily_volume (dated fact, any/no range)
# wtd|mtd|ytd   -> analytics.volume_to_date (dated fact + is_wtd/is_mtd/is_ytd flags)
TIME_FILTER_ALL = "all"
TIME_FILTER_WTD = "wtd"
TIME_FILTER_MTD = "mtd"
TIME_FILTER_YTD = "ytd"
TIME_FILTER_CURRENT = (TIME_FILTER_ALL, TIME_FILTER_WTD, TIME_FILTER_MTD, TIME_FILTER_YTD)

# Comparison periods (vs W / M / Y columns) — each backed by its own dbt model:
# analytics.volume_prev_week / volume_prev_month / volume_prev_year.
TIME_FILTER_PREV_WEEK = "prev_week"
TIME_FILTER_PREV_MONTH = "prev_month"
TIME_FILTER_PREV_YEAR = "prev_year"
TIME_FILTER_PREV = (TIME_FILTER_PREV_WEEK, TIME_FILTER_PREV_MONTH, TIME_FILTER_PREV_YEAR)
