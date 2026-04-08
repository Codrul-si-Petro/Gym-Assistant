SELECT 
  current_id,
  parent_id,
  is_leaf,
  current_name
FROM core.dimension_hierarchies
WHERE dimension = %(dimension_name)s
