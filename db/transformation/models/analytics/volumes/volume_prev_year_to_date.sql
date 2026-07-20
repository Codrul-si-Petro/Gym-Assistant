{{ config(
    post_hook=create_indexes('analytics.volume_prev_year_to_date', [['user_id', 'exercise_id', 'scenario']])
) }}

{#
  Prior year, but only through the same month/day as today — the apples-to-apples
  counterpart to the current YTD window (Jan 1..today). Postgres's date/interval
  arithmetic already clamps Feb 29 -> Feb 28 in non-leap years, so no extra handling
  is needed there. Compare against volume_prev_year.sql for the *complete* prior year.
#}
SELECT
  user_id,
  exercise_id,
  scenario,
  SUM(volume) AS volume
FROM {{ ref('total_daily_volume') }}
WHERE date_id >= (date_trunc('year', current_date) - INTERVAL '1 year')::date
  AND date_id <= (current_date - INTERVAL '1 year')::date
GROUP BY 1, 2, 3
