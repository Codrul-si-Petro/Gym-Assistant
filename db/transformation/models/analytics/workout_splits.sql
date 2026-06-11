{{ config(
    post_hook=create_indexes('analytics.workout_splits', [['user_id', 'workout_split']])
) }}

SELECT
  user_id,
  workout_split,
  SUM(set_count) AS set_count
FROM {{ ref('workout_sets_daily') }}
GROUP BY 1, 2
