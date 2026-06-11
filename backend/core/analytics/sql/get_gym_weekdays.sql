SELECT
  dc.day_number_in_week,
  TRIM(TO_CHAR(dc.date_id, 'Day')) AS day_name,
  COUNT(DISTINCT w.date_id) AS gym_days
FROM analytics.workout_sets_daily w
JOIN core.dim_calendar dc ON w.date_id = dc.date_id
WHERE w.user_id = %(user_id)s
  AND (%(start_date)s IS NULL OR w.date_id >= %(start_date)s::date)
  AND (%(end_date)s IS NULL OR w.date_id <= %(end_date)s::date)
GROUP BY dc.day_number_in_week, TRIM(TO_CHAR(dc.date_id, 'Day'))
ORDER BY gym_days DESC, dc.day_number_in_week ASC
