-- period=all always reads the dated daily fact directly (no precomputed "all" slice) —
-- open start_date means all history, open end_date means through today.
-- Comparisons still come from the prev_week/prev_month/prev_year models (see get_total_volume).
SELECT
  exercise_id,
  SUM(volume) AS total_volume_kg
FROM analytics.total_daily_volume
WHERE user_id = %(user_id)s
  AND scenario = 'actuals'
  AND (%(start_date)s IS NULL OR date_id >= %(start_date)s::date)
  AND (%(end_date)s IS NULL OR date_id <= %(end_date)s::date)
GROUP BY exercise_id
