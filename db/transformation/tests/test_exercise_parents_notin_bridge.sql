-- check all exercise parents don't exist in the bridge table
WITH parent_nodes AS (
  SELECT e.exercise_id
  FROM {{ ref('seed_exercises') }} e
  LEFT JOIN {{ ref('seed_exercises') }} p
    ON e.exercise_id = p.exercise_parent_id
  WHERE p.exercise_id IS NOT NULL
)
SELECT p.exercise_id
FROM parent_nodes p
WHERE EXISTS (
  SELECT 1
  FROM {{ ref('seed_exercise_muscle') }} em
  WHERE p.exercise_id = em.exercise_id
)
