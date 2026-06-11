{{ config(
    post_hook=create_indexes('analytics.home_summary', [['user_id']])
) }}

SELECT
  user_id,
  MAX(date_id) AS last_workout_date,
  COALESCE(SUM(total_volume_kg), 0) AS total_volume_kg
FROM {{ ref('workout_sets_daily') }}
GROUP BY 1
