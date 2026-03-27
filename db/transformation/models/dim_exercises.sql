SELECT 
  e.*,
  NOT EXISTS (
    SELECT 1
    FROM {{ ref('seed_exercises') }} c
    WHERE c.exercise_parent_id = e.exercise_id
  ) AS is_leaf,
  NOW() AS last_built
FROM {{ ref('seed_exercises') }} e
