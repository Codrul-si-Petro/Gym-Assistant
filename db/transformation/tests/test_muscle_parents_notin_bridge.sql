-- check all muscle parents don't exist in the bridge table
WITH parent_nodes AS (
  SELECT e.muscle_id
  FROM {{ ref('seed_muscles') }} e
  LEFT JOIN {{ ref('seed_muscles') }} p
    ON e.muscle_id = p.muscle_parent_id::INT
  WHERE p.muscle_id IS NOT NULL
)
SELECT p.muscle_id
FROM parent_nodes p
WHERE EXISTS (
  SELECT 1
  FROM {{ ref('seed_exercise_muscle') }} em
  WHERE p.muscle_id = em.muscle_id
)
