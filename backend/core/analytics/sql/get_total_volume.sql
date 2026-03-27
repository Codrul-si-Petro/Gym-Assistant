WITH pre_agg AS (
SELECT
  fw.exercise_id,
  SUM(
    fw.repetitions::numeric * fw.load::numeric *
    CASE WHEN fw.unit = 'LBS' THEN 0.45359237 ELSE 1 END
  ) AS total_volume_kg
FROM core.fact_workouts fw
WHERE fw.user_id = %(user_id)s
  AND (%(start_date)s IS NULL OR fw.date_id >= %(start_date)s::date)
  AND (%(end_date)s IS NULL OR fw.date_id <= %(end_date)s::date)
GROUP BY fw.exercise_id
)
SELECT
  fw.exercise_id,
  e.exercise_name,
  fw.total_volume_kg
FROM pre_agg fw
JOIN core.dim_exercises e ON fw.exercise_id = e.exercise_id
ORDER BY fw.total_volume_kg DESC
