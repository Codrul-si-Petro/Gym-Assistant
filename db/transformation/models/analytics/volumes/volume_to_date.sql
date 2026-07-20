{{ config(
    post_hook=create_indexes('analytics.volume_to_date', [['user_id', 'time_filter', 'exercise_id', 'scenario', 'date_id']])
) }}

{#
  Dated rows for current WTD / MTD / YTD windows (one row per date per applicable slice).
  API filters WHERE time_filter = 'WTD'|'MTD'|'YTD' — no boolean flags.
#}
SELECT date_id, user_id, exercise_id, scenario, volume, 'WTD' AS time_filter
FROM {{ ref('total_daily_volume') }}
WHERE date_id >= date_trunc('week', current_date)::date
  AND date_id <= current_date

UNION ALL

SELECT date_id, user_id, exercise_id, scenario, volume, 'MTD' AS time_filter
FROM {{ ref('total_daily_volume') }}
WHERE date_id >= date_trunc('month', current_date)::date
  AND date_id <= current_date

UNION ALL

SELECT date_id, user_id, exercise_id, scenario, volume, 'YTD' AS time_filter
FROM {{ ref('total_daily_volume') }}
WHERE date_id >= date_trunc('year', current_date)::date
  AND date_id <= current_date
