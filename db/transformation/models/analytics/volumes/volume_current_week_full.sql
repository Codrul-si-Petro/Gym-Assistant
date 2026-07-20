{{ config(
    post_hook=create_indexes('analytics.volume_current_week_full', [['user_id', 'exercise_id', 'scenario']])
) }}

{#
  The *entire* current ISO week (Mon..Sun), including days that haven't happened yet.
  Unlike volume_to_date's WTD slice (which stops at today), this lets the UI compare
  actuals-so-far against the *full* weekly plan target, not just the plan-to-date.
#}
SELECT
  user_id,
  exercise_id,
  scenario,
  SUM(volume) AS volume
FROM {{ ref('total_daily_volume') }}
WHERE date_id >= date_trunc('week', current_date)::date
  AND date_id < date_trunc('week', current_date)::date + INTERVAL '7 days'
GROUP BY 1, 2, 3
