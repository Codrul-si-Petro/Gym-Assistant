-- Comparison columns for the "all" / custom-range path — each period is its own
-- dbt model (see get_total_volume_periods.sql for the wtd/mtd/ytd path), with both a
-- "full" complete-prior-period variant and a "to date" (same relative day) variant.
SELECT
  COALESCE(w.exercise_id, wt.exercise_id, m.exercise_id, mt.exercise_id, y.exercise_id, yt.exercise_id) AS exercise_id,
  COALESCE(w.volume, 0) AS prev_week_volume_kg,
  COALESCE(wt.volume, 0) AS prev_week_to_date_volume_kg,
  COALESCE(m.volume, 0) AS prev_month_volume_kg,
  COALESCE(mt.volume, 0) AS prev_month_to_date_volume_kg,
  COALESCE(y.volume, 0) AS prev_year_volume_kg,
  COALESCE(yt.volume, 0) AS prev_year_to_date_volume_kg
FROM (
  SELECT exercise_id, volume FROM analytics.volume_prev_week
  WHERE user_id = %(user_id)s AND scenario = 'actuals'
) w
FULL OUTER JOIN (
  SELECT exercise_id, volume FROM analytics.volume_prev_week_to_date
  WHERE user_id = %(user_id)s AND scenario = 'actuals'
) wt USING (exercise_id)
FULL OUTER JOIN (
  SELECT exercise_id, volume FROM analytics.volume_prev_month
  WHERE user_id = %(user_id)s AND scenario = 'actuals'
) m USING (exercise_id)
FULL OUTER JOIN (
  SELECT exercise_id, volume FROM analytics.volume_prev_month_to_date
  WHERE user_id = %(user_id)s AND scenario = 'actuals'
) mt USING (exercise_id)
FULL OUTER JOIN (
  SELECT exercise_id, volume FROM analytics.volume_prev_year
  WHERE user_id = %(user_id)s AND scenario = 'actuals'
) y USING (exercise_id)
FULL OUTER JOIN (
  SELECT exercise_id, volume FROM analytics.volume_prev_year_to_date
  WHERE user_id = %(user_id)s AND scenario = 'actuals'
) yt USING (exercise_id)
