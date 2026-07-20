-- period=all always reads the dated daily fact directly (no precomputed "all" slice) —
-- open start_date means all history, open end_date means through today.
-- Comparisons still come from the prev_week/prev_month/prev_year models (see get_total_volume).
-- plan_volume backs the "vs Plan" column for the same date range.
SELECT
  exercise_id,
  SUM(volume) FILTER (WHERE scenario = 'actuals') AS total_volume,
  SUM(volume) FILTER (WHERE scenario = 'plan') AS plan_volume
FROM analytics.total_daily_volume
WHERE user_id = %(user_id)s
  AND (%(start_date)s IS NULL OR date_id >= %(start_date)s::date)
  AND (%(end_date)s IS NULL OR date_id <= %(end_date)s::date)
GROUP BY exercise_id
