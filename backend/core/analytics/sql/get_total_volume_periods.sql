-- Thin extract for period in {wtd, mtd, ytd}.
-- Current window: sum dated rows from analytics.volume_to_date filtered by time_filter.
-- Prior windows: each is its own dbt model, joined here by exercise_id. Each has a
-- "full" complete-prior-period variant and a "to date" variant capped at the same
-- relative day as today, so the UI can show both vs the *complete* prior period and
-- an apples-to-apples vs the prior period *as far as it has run so far*.
-- Plan gets the same duality: plan_volume_kg is plan-to-date (same window as
-- current_volume, for an apples-to-apples "on pace" read), while plan_*_full_volume_kg
-- is the *entire* current week/month/year's plan (the actual target to hit).
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
prev_week_td AS (
  SELECT exercise_id, volume AS prev_week_to_date_volume_kg
  FROM analytics.volume_prev_week_to_date
  WHERE user_id = %(user_id)s AND scenario = 'actuals'
),
prev_month AS (
  SELECT exercise_id, volume AS prev_month_volume_kg
  FROM analytics.volume_prev_month
  WHERE user_id = %(user_id)s AND scenario = 'actuals'
),
prev_month_td AS (
  SELECT exercise_id, volume AS prev_month_to_date_volume_kg
  FROM analytics.volume_prev_month_to_date
  WHERE user_id = %(user_id)s AND scenario = 'actuals'
),
prev_year AS (
  SELECT exercise_id, volume AS prev_year_volume_kg
  FROM analytics.volume_prev_year
  WHERE user_id = %(user_id)s AND scenario = 'actuals'
),
prev_year_td AS (
  SELECT exercise_id, volume AS prev_year_to_date_volume_kg
  FROM analytics.volume_prev_year_to_date
  WHERE user_id = %(user_id)s AND scenario = 'actuals'
),
plan_week_full AS (
  SELECT exercise_id, volume AS plan_week_full_volume_kg
  FROM analytics.volume_current_week_full
  WHERE user_id = %(user_id)s AND scenario = 'plan'
),
plan_month_full AS (
  SELECT exercise_id, volume AS plan_month_full_volume_kg
  FROM analytics.volume_current_month_full
  WHERE user_id = %(user_id)s AND scenario = 'plan'
),
plan_year_full AS (
  SELECT exercise_id, volume AS plan_year_full_volume_kg
  FROM analytics.volume_current_year_full
  WHERE user_id = %(user_id)s AND scenario = 'plan'
),
exercise_ids AS (
  SELECT exercise_id FROM current_volume
  UNION
  SELECT exercise_id FROM current_plan
  UNION
  SELECT exercise_id FROM prev_week
  UNION
  SELECT exercise_id FROM prev_week_td
  UNION
  SELECT exercise_id FROM prev_month
  UNION
  SELECT exercise_id FROM prev_month_td
  UNION
  SELECT exercise_id FROM prev_year
  UNION
  SELECT exercise_id FROM prev_year_td
  UNION
  SELECT exercise_id FROM plan_week_full
  UNION
  SELECT exercise_id FROM plan_month_full
  UNION
  SELECT exercise_id FROM plan_year_full
)
SELECT
  e.exercise_id,
  COALESCE(c.total_volume_kg, 0) AS total_volume_kg,
  COALESCE(p.plan_volume_kg, 0) AS plan_volume_kg,
  COALESCE(w.prev_week_volume_kg, 0) AS prev_week_volume_kg,
  COALESCE(wt.prev_week_to_date_volume_kg, 0) AS prev_week_to_date_volume_kg,
  COALESCE(m.prev_month_volume_kg, 0) AS prev_month_volume_kg,
  COALESCE(mt.prev_month_to_date_volume_kg, 0) AS prev_month_to_date_volume_kg,
  COALESCE(y.prev_year_volume_kg, 0) AS prev_year_volume_kg,
  COALESCE(yt.prev_year_to_date_volume_kg, 0) AS prev_year_to_date_volume_kg,
  COALESCE(pwf.plan_week_full_volume_kg, 0) AS plan_week_full_volume_kg,
  COALESCE(pmf.plan_month_full_volume_kg, 0) AS plan_month_full_volume_kg,
  COALESCE(pyf.plan_year_full_volume_kg, 0) AS plan_year_full_volume_kg
FROM exercise_ids e
LEFT JOIN current_volume c USING (exercise_id)
LEFT JOIN current_plan p USING (exercise_id)
LEFT JOIN prev_week w USING (exercise_id)
LEFT JOIN prev_week_td wt USING (exercise_id)
LEFT JOIN prev_month m USING (exercise_id)
LEFT JOIN prev_month_td mt USING (exercise_id)
LEFT JOIN prev_year y USING (exercise_id)
LEFT JOIN prev_year_td yt USING (exercise_id)
LEFT JOIN plan_week_full pwf USING (exercise_id)
LEFT JOIN plan_month_full pmf USING (exercise_id)
LEFT JOIN plan_year_full pyf USING (exercise_id)
