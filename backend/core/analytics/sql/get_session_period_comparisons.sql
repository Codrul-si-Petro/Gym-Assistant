-- Distinct session counts (date_id + workout_number) for current and prior
-- week/month/year windows, plus plan targets. Used by the Sessions metrics
-- Total row (vs PW / vs PM / vs PY and vs plan columns).
SELECT
  COUNT(*) FILTER (
    WHERE w.scenario = 'actuals' AND w.date_id BETWEEN %(cur_week_start)s AND %(cur_week_end)s
  ) AS sessions_this_week,
  COUNT(*) FILTER (
    WHERE w.scenario = 'actuals' AND w.date_id BETWEEN %(prev_week_start)s AND %(prev_week_end)s
  ) AS previous_week,
  COUNT(*) FILTER (
    WHERE w.scenario = 'actuals' AND w.date_id BETWEEN %(prev_week_start)s AND %(prev_week_to_date_end)s
  ) AS previous_week_to_date,
  COUNT(*) FILTER (
    WHERE w.scenario = 'actuals' AND w.date_id BETWEEN %(cur_month_start)s AND %(cur_month_end)s
  ) AS sessions_this_month,
  COUNT(*) FILTER (
    WHERE w.scenario = 'actuals' AND w.date_id BETWEEN %(prev_month_start)s AND %(prev_month_end)s
  ) AS previous_month,
  COUNT(*) FILTER (
    WHERE w.scenario = 'actuals' AND w.date_id BETWEEN %(prev_month_start)s AND %(prev_month_to_date_end)s
  ) AS previous_month_to_date,
  COUNT(*) FILTER (
    WHERE w.scenario = 'actuals' AND w.date_id BETWEEN %(cur_year_start)s AND %(cur_year_end)s
  ) AS sessions_this_year,
  COUNT(*) FILTER (
    WHERE w.scenario = 'actuals' AND w.date_id BETWEEN %(prev_year_start)s AND %(prev_year_end)s
  ) AS previous_year,
  COUNT(*) FILTER (
    WHERE w.scenario = 'actuals' AND w.date_id BETWEEN %(prev_year_start)s AND %(prev_year_to_date_end)s
  ) AS previous_year_to_date,
  COUNT(*) FILTER (
    WHERE w.scenario = 'plan' AND w.date_id BETWEEN %(cur_week_start)s AND %(cur_week_end)s
  ) AS plan_week,
  COUNT(*) FILTER (
    WHERE w.scenario = 'plan' AND w.date_id BETWEEN %(cur_month_start)s AND %(cur_month_end)s
  ) AS plan_month,
  COUNT(*) FILTER (
    WHERE w.scenario = 'plan' AND w.date_id BETWEEN %(cur_year_start)s AND %(cur_year_end)s
  ) AS plan_year,
  COUNT(*) FILTER (
    WHERE w.scenario = 'plan' AND w.date_id BETWEEN %(cur_week_start)s AND %(week_full_end)s
  ) AS plan_week_full,
  COUNT(*) FILTER (
    WHERE w.scenario = 'plan' AND w.date_id BETWEEN %(cur_month_start)s AND %(month_full_end)s
  ) AS plan_month_full,
  COUNT(*) FILTER (
    WHERE w.scenario = 'plan' AND w.date_id BETWEEN %(cur_year_start)s AND %(year_full_end)s
  ) AS plan_year_full
FROM (
  SELECT DISTINCT user_id, date_id, workout_number, scenario
  FROM core.fact_workouts
  WHERE user_id = %(user_id)s
    AND date_id >= %(prev_year_start)s
    AND date_id <= %(year_full_end)s
) w
