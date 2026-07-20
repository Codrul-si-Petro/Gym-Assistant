{{ config(
    post_hook=create_indexes('analytics.volume_prev_month_to_date', [['user_id', 'exercise_id', 'scenario']])
) }}

{#
  Prior month, but only through the same day-of-month as today — the apples-to-apples
  counterpart to the current MTD window (1st..today). Months vary in length, so the
  day offset from this month's start is capped to the last valid day of the prior month
  (e.g. on Mar 31, "prev month to date" is capped at Feb 28/29, not Mar 3 of Feb).
  Compare against volume_prev_month.sql for the *complete* prior month instead.
#}
WITH bounds AS (
  SELECT
    date_trunc('month', current_date)::date AS cur_month_start,
    (date_trunc('month', current_date) - INTERVAL '1 month')::date AS prev_month_start
),
date_bounds AS (
  SELECT
    prev_month_start,
    prev_month_start + LEAST(
      current_date - cur_month_start,
      (cur_month_start - prev_month_start) - 1
    ) AS prev_month_to_date_end
  FROM bounds
)
SELECT
  f.user_id,
  f.exercise_id,
  f.scenario,
  SUM(f.volume) AS volume
FROM {{ ref('total_daily_volume') }} f, date_bounds w
WHERE f.date_id >= w.prev_month_start
  AND f.date_id <= w.prev_month_to_date_end
GROUP BY 1, 2, 3
