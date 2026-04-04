SELECT 
  e.*,
  NOT EXISTS (
    SELECT 1
    FROM {{ ref('seed_equipment') }} c
    WHERE c.equipment_parent_id = e.equipment_id
  ) AS is_leaf,
  NOW() AS last_built
FROM {{ ref('seed_equipment') }} e
