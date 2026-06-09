WITH workout_dates AS (
  SELECT DISTINCT date_id
  FROM analytics.workout_sets_daily
  WHERE user_id = %(user_id)s
),
date_bounds AS (
  SELECT MIN(date_id) AS min_date, MAX(date_id) AS max_date
  FROM workout_dates
)
SELECT c.date_id
FROM core.dim_calendar c
LEFT JOIN workout_dates w ON c.date_id = w.date_id
JOIN date_bounds b ON b.min_date IS NOT NULL
WHERE w.date_id IS NULL
  AND c.date_id BETWEEN b.min_date AND b.max_date

