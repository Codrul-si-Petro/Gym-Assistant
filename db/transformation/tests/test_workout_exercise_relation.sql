-- check all exercise ids from the fact table appear in the dimension table

SELECT fw.exercise_id
FROM core.fact_workouts fw
LEFT JOIN core.dim_exercise de
  ON fw.exercise_id = de.exercise_id
WHERE de.exercise_id IS NULL
