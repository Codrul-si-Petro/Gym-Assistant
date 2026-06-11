SELECT
  h.last_workout_date,
  h.total_volume_kg
FROM analytics.home_summary h
WHERE h.user_id = %(user_id)s
