{{ config(
    post_hook=create_indexes('analytics.total_daily_volume', [['user_id', 'date_id', 'exercise_id', 'scenario']])
) }}

SELECT 
 date_id,
 user_id,
 exercise_id,
 scenario,
 SUM(
  repetitions * LOAD *
  CASE WHEN unit = 'LBS' THEN 0.45359237 ELSE 1 END
 ) AS volume
FROM {{ source('core', 'fact_workouts') }} 
GROUP BY 1, 2, 3, 4
