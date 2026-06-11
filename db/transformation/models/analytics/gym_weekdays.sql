{{ config(
    post_hook=create_indexes('analytics.gym_weekdays', [['user_id', 'day_number_in_week']])
) }}

SELECT
  w.user_id,
  c.day_number_in_week,
  TRIM(TO_CHAR(c.date_id, 'Day')) AS day_name,
  COUNT(DISTINCT w.date_id) AS gym_days
FROM {{ ref('workout_sets_daily') }} w
JOIN {{ ref('dim_calendar') }} c ON w.date_id = c.date_id
GROUP BY 1, 2, 3
