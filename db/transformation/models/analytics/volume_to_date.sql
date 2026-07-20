{{ config(
    post_hook=create_indexes('analytics.volume_to_date', [['user_id', 'exercise_id', 'scenario', 'date_id']])
) }}

{#
  Dated rows (not pre-summed) for the current WTD / MTD / YTD windows, as-of
  current_date at dbt run time. A date can satisfy more than one flag (today
  is in all three). The API sums by flag — no period-boundary math at request time.
#}
SELECT
  d.date_id,
  d.user_id,
  d.exercise_id,
  d.scenario,
  d.volume,
  d.date_id >= date_trunc('week', current_date)::date AS is_wtd,
  d.date_id >= date_trunc('month', current_date)::date AS is_mtd,
  d.date_id >= date_trunc('year', current_date)::date AS is_ytd
FROM {{ ref('total_daily_volume') }} d
WHERE d.date_id BETWEEN date_trunc('year', current_date)::date AND current_date
