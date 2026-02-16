-- check all equipment ids from the fact table appear in the dimension table

SELECT fw.equipment_id
FROM core.fact_workouts fw
LEFT JOIN core.dim_equipment de
  ON fw.equipment_id = de.equipment_id
WHERE de.equipment_id IS NULL
