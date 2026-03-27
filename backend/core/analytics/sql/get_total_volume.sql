WITH pre_agg AS (
SELECT 
  fw.exercise_id,
  SUM(fw.repetitions) AS total_reps,
  SUM(load) AS total_load
FROM core.fact_workouts fw
WHERE fw.user_id = %(user_id)s
  AND (%(start_date)s IS NULL OR fw.date_id >= %(start_date)s::date)
  AND (%(end_date)s IS NULL OR fw.date_id <= %(end_date)s::date)
GROUP BY fw.exercise_id 
)
SELECT
  fw.exercise_id,
  e.exercise_name,
  m.muscle_name,
  fw.total_reps * fw.total_load AS total_volume_kg
FROM pre_agg fw 
JOIN core.dim_exercises e ON fw.exercise_id = e.exercise_id  
JOIN core.exercise_muscle_bridge em ON e.exercise_id = em.exercise_id 
JOIN core.dim_muscles m ON em.muscle_id = m.muscle_id
WHERE em.muscle_role = 'Primary'
ORDER BY total_volume_kg DESC
