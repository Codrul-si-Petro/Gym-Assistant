SELECT 
  *,
  NOW() AS last_built
FROM {{ ref('seed_equipment') }}
