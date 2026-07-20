{{ config(
    post_hook=create_indexes('analytics.volume_prev_year', [['user_id', 'exercise_id', 'scenario']])
) }}

{# Complete prior calendar year, computed from the daily fact as-of current_date. #}
SELECT
  user_id,
  exercise_id,
  scenario,
  SUM(volume) AS volume
FROM {{ ref('total_daily_volume') }}
WHERE date_id >= (date_trunc('year', current_date) - INTERVAL '1 year')::date
  AND date_id < date_trunc('year', current_date)::date
GROUP BY 1, 2, 3
