{{ config(
    post_hook=create_indexes('analytics.volume_prev_month', [['user_id', 'exercise_id', 'scenario']])
) }}

{# Complete prior calendar month, computed from the daily fact as-of current_date. #}
SELECT
  user_id,
  exercise_id,
  scenario,
  SUM(volume) AS volume
FROM {{ ref('total_daily_volume') }}
WHERE date_id >= (date_trunc('month', current_date) - INTERVAL '1 month')::date
  AND date_id < date_trunc('month', current_date)::date
GROUP BY 1, 2, 3
