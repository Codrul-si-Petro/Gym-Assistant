-- check all exercise leaves exist in the bridge table
WITH leaf_nodes AS (
  SELECT e.exercise_id
  FROM {{ ref('seed_exercises') }} e
  LEFT JOIN {{ ref('seed_exercises') }} c
    ON e.exercise_id = c.exercise_parent_id
  WHERE c.exercise_id IS NULL
)
SELECT l.exercise_id
FROM leaf_nodes l
WHERE NOT EXISTS (
  SELECT 1
  FROM {{ ref('seed_exercise_muscle') }} em
  WHERE l.exercise_id = em.exercise_id
)
