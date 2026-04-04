{{ config(
    materialized='table',
    post_hook=create_indexes('core.dimension_hierarchies', [['current_id', 'dimension']])
) }}

WITH RECURSIVE exercise_tree AS (
    SELECT
        'exercise' AS dimension,
        e.exercise_name AS current_name,
        e.exercise_id AS current_id,
        e.exercise_parent_id AS parent_id,
        0 AS depth
    FROM {{ ref('dim_exercises') }} e
    WHERE e.exercise_parent_id IS NULL -- gets depth 0

    UNION ALL

    SELECT
        'exercise' AS dimension,
        e.exercise_name AS current_name,
        e.exercise_id AS current_id,
        e.exercise_parent_id AS parent_id,
        c.depth + 1
    FROM exercise_tree c
    JOIN {{ ref('dim_exercises') }} e
      ON e.exercise_parent_id = c.current_id
),

muscle_tree AS (
    SELECT
        'muscle' AS dimension,
        m.muscle_name AS current_name,
        m.muscle_id AS current_id,
        m.muscle_parent_id AS parent_id,
        0 AS depth
    FROM {{ ref('dim_muscles') }} m
    WHERE m.muscle_parent_id IS NULL

    UNION ALL

    SELECT
        'muscle' AS dimension,
        m.muscle_name AS current_name,
        m.muscle_id AS current_id,
        m.muscle_parent_id AS parent_id,
        c.depth + 1
    FROM muscle_tree c
    JOIN {{ ref('dim_muscles') }} m
      ON m.muscle_parent_id = c.current_id
),

attachment_tree AS (
    SELECT
        'attachment' AS dimension,
        a.attachment_name AS current_name,
        a.attachment_id AS current_id,
        a.attachment_parent_id AS parent_id,
        0 AS depth
    FROM {{ ref('dim_attachments') }} a
    WHERE a.attachment_parent_id IS NULL

    UNION ALL

    SELECT
        'attachment' AS dimension,
        a.attachment_name AS current_name,
        a.attachment_id AS current_id,
        a.attachment_parent_id AS parent_id,
        c.depth + 1
    FROM attachment_tree c
    JOIN {{ ref('dim_attachments') }} a
      ON a.attachment_parent_id = c.current_id
),

equipment_tree AS (
    SELECT
        'equipment' AS dimension,
        eq.equipment_name AS current_name,
        eq.equipment_id AS current_id,
        eq.equipment_parent_id AS parent_id,
        0 AS depth
    FROM {{ ref('dim_equipment') }} eq
    WHERE eq.equipment_parent_id IS NULL

    UNION ALL

    SELECT
        'equipment' AS dimension,
        eq.equipment_name AS current_name,
        eq.equipment_id AS current_id,
        eq.equipment_parent_id AS parent_id,
        c.depth + 1
    FROM equipment_tree c
    JOIN {{ ref('dim_equipment') }} eq
      ON eq.equipment_parent_id = c.current_id
)

SELECT dimension, current_name, current_id, parent_id, depth
FROM exercise_tree
UNION ALL
SELECT dimension, current_name, current_id, parent_id, depth
FROM muscle_tree
UNION ALL
SELECT dimension, current_name, current_id, parent_id, depth
FROM attachment_tree
UNION ALL
SELECT dimension, current_name, current_id, parent_id, depth
FROM equipment_tree
