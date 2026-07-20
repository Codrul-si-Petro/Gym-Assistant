{{ config(
    post_hook=create_indexes('analytics.workout_sets_daily', [['user_id', 'date_id', 'exercise_id', 'scenario'], ['user_id', 'workout_split']])
) }}

SELECT
  date_id,
  user_id,
  exercise_id,
  scenario,
  workout_split,
  COUNT(*) AS set_count,
  SUM(
    repetitions * load *
    CASE WHEN unit = 'LBS' THEN 0.45359237 ELSE 1 END
  ) AS total_volume_kg
FROM {{ source('core', 'fact_workouts') }}
GROUP BY 1, 2, 3, 4, 5
