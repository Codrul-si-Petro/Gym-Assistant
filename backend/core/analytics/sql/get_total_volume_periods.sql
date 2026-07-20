-- Thin extract for period in {wtd, mtd, ytd}.
-- Current window: sum dated rows from analytics.volume_to_date filtered by time_filter.
-- Prior windows: each is its own complete-period dbt model, joined here by exercise_id.
WITH current_volume AS (
  SELECT exercise_id, SUM(volume) AS total_volume_kg
  FROM analytics.volume_to_date
  WHERE user_id = %(user_id)s
    AND scenario = 'actuals'
    AND time_filter = UPPER(%(time_filter)s)
  GROUP BY exercise_id
),
current_plan AS (
  -- Same window as current_volume, scenario='plan' — backs the "vs Plan" column.
  SELECT exercise_id, SUM(volume) AS plan_volume_kg
  FROM analytics.volume_to_date
  WHERE user_id = %(user_id)s
    AND scenario = 'plan'
    AND time_filter = UPPER(%(time_filter)s)
  GROUP BY exercise_id
),
prev_week AS (
  SELECT exercise_id, volume AS prev_week_volume_kg
  FROM analytics.volume_prev_week
  WHERE user_id = %(user_id)s AND scenario = 'actuals'
),
prev_month AS (
  SELECT exercise_id, volume AS prev_month_volume_kg
  FROM analytics.volume_prev_month
  WHERE user_id = %(user_id)s AND scenario = 'actuals'
),
prev_year AS (
  SELECT exercise_id, volume AS prev_year_volume_kg
  FROM analytics.volume_prev_year
  WHERE user_id = %(user_id)s AND scenario = 'actuals'
),
exercise_ids AS (
  SELECT exercise_id FROM current_volume
  UNION
  SELECT exercise_id FROM current_plan
  UNION
  SELECT exercise_id FROM prev_week
  UNION
  SELECT exercise_id FROM prev_month
  UNION
  SELECT exercise_id FROM prev_year
)
SELECT
  e.exercise_id,
  COALESCE(c.total_volume_kg, 0) AS total_volume_kg,
  COALESCE(p.plan_volume_kg, 0) AS plan_volume_kg,
  COALESCE(w.prev_week_volume_kg, 0) AS prev_week_volume_kg,
  COALESCE(m.prev_month_volume_kg, 0) AS prev_month_volume_kg,
  COALESCE(y.prev_year_volume_kg, 0) AS prev_year_volume_kg
FROM exercise_ids e
LEFT JOIN current_volume c USING (exercise_id)
LEFT JOIN current_plan p USING (exercise_id)
LEFT JOIN prev_week w USING (exercise_id)
LEFT JOIN prev_month m USING (exercise_id)
LEFT JOIN prev_year y USING (exercise_id)
