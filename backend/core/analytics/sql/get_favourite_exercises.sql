SELECT
  w.exercise_id,
  e.exercise_name,
  SUM(w.set_count) AS counter
FROM analytics.workout_sets_daily w
JOIN core.dim_exercises e ON w.exercise_id = e.exercise_id
WHERE w.user_id = %(user_id)s
  AND w.scenario = 'actuals'
  AND (%(start_date)s IS NULL OR w.date_id >= %(start_date)s::date)
  AND (%(end_date)s IS NULL OR w.date_id <= %(end_date)s::date)
GROUP BY 1, 2
ORDER BY counter DESC