{{ config(
    post_hook=create_indexes('analytics.total_volume_daily', [['user_id', 'date_id', 'exercise_id']])
) }}

SELECT 
 date_id,
 user_id,
 exercise_id,
 SUM(
  repetitions * LOAD *
  CASE WHEN unit = 'LBS' THEN 0.45359237 ELSE 1 END
 ) AS volume
FROM {{ source('core', 'fact_workouts') }} 
GROUP BY 1, 2, 3
