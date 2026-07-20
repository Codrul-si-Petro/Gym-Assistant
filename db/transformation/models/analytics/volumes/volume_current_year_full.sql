{{ config(
    post_hook=create_indexes('analytics.volume_current_year_full', [['user_id', 'exercise_id', 'scenario']])
) }}

{#
  The *entire* current calendar year (Jan 1..Dec 31), including days that haven't
  happened yet. Unlike volume_to_date's YTD slice (which stops at today), this lets
  the UI compare actuals-so-far against the *full* yearly plan target, not just the
  plan-to-date.
#}
SELECT
  user_id,
  exercise_id,
  scenario,
  SUM(volume) AS volume
FROM {{ ref('total_daily_volume') }}
WHERE date_id >= date_trunc('year', current_date)::date
  AND date_id < (date_trunc('year', current_date) + INTERVAL '1 year')::date
GROUP BY 1, 2, 3
