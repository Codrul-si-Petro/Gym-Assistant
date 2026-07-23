-- Distinct workout sessions for the authenticated user.
-- Reads core.fact_workouts directly (not an analytics mart) so the list stays
-- fresh after each logged set; other analytics endpoints use dbt marts that lag
-- up to the 4-hour dbt build schedule.
SELECT
  w.date_id AS date,
  w.workout_number,
  MIN(w.workout_split) AS workout_split,
  COUNT(*) AS set_count
FROM core.fact_workouts w
WHERE w.user_id = %(user_id)s
  AND w.scenario = 'actuals'
  AND (%(start_date)s IS NULL OR w.date_id >= %(start_date)s::date)
  AND (%(end_date)s IS NULL OR w.date_id <= %(end_date)s::date)
GROUP BY w.date_id, w.workout_number
ORDER BY w.date_id DESC, w.workout_number DESC
