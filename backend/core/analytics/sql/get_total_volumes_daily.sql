SELECT
  date_id,
  exercise_id,
  scenario,
  SUM(volume) AS total_volume_kg
FROM analytics.total_daily_volume
WHERE user_id = %(user_id)s
  AND (%(start_date)s IS NULL OR date_id >= %(start_date)s::date)
  AND (%(end_date)s IS NULL OR date_id <= %(end_date)s::date)
GROUP BY exercise_id, date_id, scenario
ORDER BY
  exercise_id,
  date_id ASC
