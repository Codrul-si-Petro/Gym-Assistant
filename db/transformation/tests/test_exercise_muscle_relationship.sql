-- check all muscle ids from the dimension table appear in the bridge table

SELECT m.muscle_id
FROM core.dim_muscles m
LEFT JOIN core.exercise_muscle_bridge em
  ON em.muscle_id = m.muscle_id
WHERE em.muscle_id IS NULL
