SELECT 
  e.*,
  NOT EXISTS (
    SELECT 1
    FROM {{ ref('seed_muscles') }} c
    WHERE c.muscle_parent_id = e.muscle_id
  ) AS is_leaf,
  NOW() AS last_built
FROM {{ ref('seed_muscles') }} e
