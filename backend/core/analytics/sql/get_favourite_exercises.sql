SELECT 
  fw.exercise_id,
  e.exercise_name,
  count(fw.exercise_id) AS counter
FROM core.fact_workouts fw
JOIN core.dim_exercises e ON fw.exercise_id = e.exercise_id 
WHERE fw.user_id = %(user_id)s
  AND (%(start_date)s IS NULL OR fw.date_id >= %(start_date)s::date)
  AND (%(end_date)s IS NULL OR fw.date_id <= %(end_date)s::date)
GROUP BY 1, 2
ORDER BY counter DESC