SELECT 
  fw.exercise_id,
  e.exercise_name,
  count(fw.exercise_id) AS counter
FROM core.fact_workouts fw
JOIN core.dim_exercises e ON fw.exercise_id = e.exercise_id 
WHERE user_id = %(user_id)s
GROUP BY 1, 2
ORDER BY counter desc
