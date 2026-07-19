-- "Workout" here means a gym day (a date with >=1 logged set), matching the
-- gym_weekdays convention. FILTER lets us get all 4 period counts in one pass
-- over workout_sets_daily instead of 4 separate queries.
SELECT
  COUNT(DISTINCT w.date_id) FILTER (WHERE w.date_id BETWEEN %(cur_week_start)s AND %(cur_week_end)s) AS workouts_this_week,
  COUNT(DISTINCT w.date_id) FILTER (WHERE w.date_id BETWEEN %(prev_week_start)s AND %(prev_week_end)s) AS workouts_last_week,
  COUNT(DISTINCT w.date_id) FILTER (WHERE w.date_id BETWEEN %(cur_month_start)s AND %(cur_month_end)s) AS workouts_this_month,
  COUNT(DISTINCT w.date_id) FILTER (WHERE w.date_id BETWEEN %(prev_month_start)s AND %(prev_month_end)s) AS workouts_last_month
FROM analytics.workout_sets_daily w
WHERE w.user_id = %(user_id)s
  -- prev_month_start is always the earliest bound of the 4 periods; this lets the
  -- (user_id, date_id) index skip everything older instead of scanning all history.
  AND w.date_id >= %(prev_month_start)s
