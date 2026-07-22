-- "Workout" here means a gym day (a date with >=1 set), matching the
-- gym_weekdays convention. FILTER lets us get all period counts in one pass
-- over workout_sets_daily instead of separate queries.
-- Actuals and plan are both counted (scenario moved into each FILTER).
SELECT
  COUNT(DISTINCT w.date_id) FILTER (
    WHERE w.scenario = 'actuals' AND w.date_id BETWEEN %(cur_week_start)s AND %(cur_week_end)s
  ) AS workouts_this_week,
  COUNT(DISTINCT w.date_id) FILTER (
    WHERE w.scenario = 'actuals' AND w.date_id BETWEEN %(prev_week_start)s AND %(prev_week_end)s
  ) AS workouts_last_week,
  COUNT(DISTINCT w.date_id) FILTER (
    WHERE w.scenario = 'actuals' AND w.date_id BETWEEN %(cur_month_start)s AND %(cur_month_end)s
  ) AS workouts_this_month,
  COUNT(DISTINCT w.date_id) FILTER (
    WHERE w.scenario = 'actuals' AND w.date_id BETWEEN %(prev_month_start)s AND %(prev_month_end)s
  ) AS workouts_last_month,
  COUNT(DISTINCT w.date_id) FILTER (
    WHERE w.scenario = 'actuals' AND w.date_id BETWEEN %(cur_year_start)s AND %(cur_year_end)s
  ) AS workouts_this_year,
  COUNT(DISTINCT w.date_id) FILTER (
    WHERE w.scenario = 'actuals' AND w.date_id BETWEEN %(prev_year_start)s AND %(prev_year_end)s
  ) AS workouts_last_year,
  COUNT(DISTINCT w.date_id) FILTER (
    WHERE w.scenario = 'plan' AND w.date_id BETWEEN %(cur_week_start)s AND %(cur_week_end)s
  ) AS workouts_planned_this_week,
  COUNT(DISTINCT w.date_id) FILTER (
    WHERE w.scenario = 'plan' AND w.date_id BETWEEN %(cur_month_start)s AND %(cur_month_end)s
  ) AS workouts_planned_this_month,
  COUNT(DISTINCT w.date_id) FILTER (
    WHERE w.scenario = 'plan' AND w.date_id BETWEEN %(cur_year_start)s AND %(cur_year_end)s
  ) AS workouts_planned_this_year,
  COUNT(DISTINCT w.date_id) FILTER (
    WHERE w.scenario = 'plan' AND w.date_id BETWEEN %(cur_week_start)s AND %(week_full_end)s
  ) AS workouts_planned_week_full,
  COUNT(DISTINCT w.date_id) FILTER (
    WHERE w.scenario = 'plan' AND w.date_id BETWEEN %(cur_month_start)s AND %(month_full_end)s
  ) AS workouts_planned_month_full,
  COUNT(DISTINCT w.date_id) FILTER (
    WHERE w.scenario = 'plan' AND w.date_id BETWEEN %(cur_year_start)s AND %(year_full_end)s
  ) AS workouts_planned_year_full
FROM analytics.workout_sets_daily w
WHERE w.user_id = %(user_id)s
  -- prev_year_start is the earliest bound of the periods; this lets the
  -- (user_id, date_id) index skip everything older instead of scanning all history.
  AND w.date_id >= %(prev_year_start)s
  AND w.date_id <= %(year_full_end)s
