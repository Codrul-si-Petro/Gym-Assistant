{{ config(
    post_hook=create_indexes('analytics.volume_current_month_full', [['user_id', 'exercise_id', 'scenario']])
) }}

{#
  The *entire* current calendar month (1st..last day), including days that haven't
  happened yet. Unlike volume_to_date's MTD slice (which stops at today), this lets
  the UI compare actuals-so-far against the *full* monthly plan target, not just the
  plan-to-date.
#}
SELECT
  user_id,
  exercise_id,
  scenario,
  SUM(volume) AS volume
FROM {{ ref('total_daily_volume') }}
WHERE date_id >= date_trunc('month', current_date)::date
  AND date_id < (date_trunc('month', current_date) + INTERVAL '1 month')::date
GROUP BY 1, 2, 3
