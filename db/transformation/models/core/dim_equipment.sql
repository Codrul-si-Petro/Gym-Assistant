SELECT 
  equipment_id,
  equipment_name,
  equipment_description,
  equipment_parent_id,
  equipment_category,
  ta_created_at::timestamptz,
  NOT EXISTS (
    SELECT 1
    FROM {{ ref('seed_equipment') }} c
    WHERE c.equipment_parent_id = e.equipment_id
  ) AS is_leaf,
  NOW() as last_built
FROM {{ ref('seed_equipment') }} e
