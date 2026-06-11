SELECT
  w.workout_split,
  SUM(w.set_count) AS set_count
FROM analytics.workout_sets_daily w
WHERE w.user_id = %(user_id)s
  AND (%(start_date)s IS NULL OR w.date_id >= %(start_date)s::date)
  AND (%(end_date)s IS NULL OR w.date_id <= %(end_date)s::date)
GROUP BY w.workout_split
ORDER BY set_count DESC
