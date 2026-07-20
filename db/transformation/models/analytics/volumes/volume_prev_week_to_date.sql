{{ config(
    post_hook=create_indexes('analytics.volume_prev_week_to_date', [['user_id', 'exercise_id', 'scenario']])
) }}

{#
  Prior week, but only through the same weekday as today — the apples-to-apples
  counterpart to the current WTD window (Mon..today). Weeks are a fixed 7 days,
  so this is just last week's window shifted back exactly 7 days.
  Compare against volume_prev_week.sql for the *complete* prior week instead.
#}
SELECT
  user_id,
  exercise_id,
  scenario,
  SUM(volume) AS volume
FROM {{ ref('total_daily_volume') }}
WHERE date_id >= date_trunc('week', current_date)::date - INTERVAL '7 days'
  AND date_id <= current_date - INTERVAL '7 days'
GROUP BY 1, 2, 3
