{{ config(
    post_hook=create_indexes('analytics.volume_prev_week', [['user_id', 'exercise_id', 'scenario']])
) }}

{# Complete prior ISO week (Mon–Sun), computed from the daily fact as-of current_date. #}
SELECT
  user_id,
  exercise_id,
  scenario,
  SUM(volume) AS volume
FROM {{ ref('total_daily_volume') }}
WHERE date_id >= date_trunc('week', current_date)::date - INTERVAL '7 days'
  AND date_id < date_trunc('week', current_date)::date
GROUP BY 1, 2, 3
