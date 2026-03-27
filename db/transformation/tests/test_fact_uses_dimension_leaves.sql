-- fact table must use only leaf nodes for all hierarchical dimensions

WITH exercise_non_leaf AS (
    SELECT e.exercise_id
    FROM {{ ref('seed_exercises') }} e
    INNER JOIN {{ ref('seed_exercises') }} c
        ON e.exercise_id = c.exercise_parent_id
),

equipment_non_leaf AS (
    SELECT m.equipment_id
    FROM {{ ref('seed_equipment') }} m
    INNER JOIN {{ ref('seed_equipment') }} c
        ON m.equipment_id = c.equipment_parent_id::INT -- no idea why this shit thinks this is not an INT
)

-- EXERCISE violations
SELECT
    'exercise' AS dimension,
    f.exercise_id AS offending_id
FROM {{ source('core', 'fact_workouts') }} f
JOIN exercise_non_leaf nl
  ON f.exercise_id = nl.exercise_id

UNION ALL

-- EQUIPMENT violations 
SELECT
    'equipment' AS dimension,
    f.equipment_id AS offending_id
FROM {{ source('core', 'fact_workouts') }} f
JOIN equipment_non_leaf nl
  ON f.equipment_id = nl.equipment_id::INT
