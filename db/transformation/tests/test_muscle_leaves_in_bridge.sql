-- check all muscle ids in bridge table exist as a leaf node in the muscle table
WITH leaf_nodes AS (
  SELECT m.muscle_id
  FROM {{ ref('seed_muscles') }} m
  LEFT JOIN {{ ref('seed_muscles') }} c
    ON m.muscle_id = c.muscle_parent_id::INT
  WHERE c.muscle_id IS NULL
)
SELECT DISTINCT em.muscle_id
FROM {{ ref('seed_exercise_muscles') }} em
WHERE NOT EXISTS (
    SELECT 1
    FROM leaf_nodes l
    WHERE l.muscle_id = em.muscle_id
)
