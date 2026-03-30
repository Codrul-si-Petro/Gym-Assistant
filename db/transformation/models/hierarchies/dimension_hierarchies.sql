{{ config(
    materialized='table',
    post_hook=create_indexes('core.dimension_hierarchies', [['ancestor_id', 'dimension']])
) }}

WITH RECURSIVE exercise_tree AS (
    SELECT
        'exercise' AS dimension,
        e.exercise_name AS ancestor_name,
        e.exercise_id AS ancestor_id,
        e.exercise_id AS current_id,
        0 AS depth
    FROM {{ ref('dim_exercises') }} e

    UNION ALL

    SELECT
        'exercise' AS dimension,
        c.ancestor_name,
        c.ancestor_id,
        e.exercise_id AS current_id,
        c.depth + 1
    FROM exercise_tree c
    JOIN {{ ref('dim_exercises') }} e
      ON e.exercise_parent_id = c.current_id
),

muscle_tree AS (
    SELECT
        'muscle' AS dimension,
        m.muscle_name AS ancestor_name,
        m.muscle_id AS ancestor_id,
        m.muscle_id AS current_id,
        0 AS depth
    FROM {{ ref('dim_muscles') }} m

    UNION ALL

    SELECT
        'muscle' AS dimension,
        c.ancestor_name,
        c.ancestor_id,
        m.muscle_id AS current_id,
        c.depth + 1
    FROM muscle_tree c
    JOIN {{ ref('dim_muscles') }} m
      ON m.muscle_parent_id = c.current_id
),

attachment_tree AS (
    SELECT
        'attachment' AS dimension,
        a.attachment_name AS ancestor_name,
        a.attachment_id AS ancestor_id,
        a.attachment_id AS current_id,
        0 AS depth
    FROM {{ ref('dim_attachments') }} a

    UNION ALL

    SELECT
        'attachment' AS dimension,
        c.ancestor_name,
        c.ancestor_id,
        a.attachment_id AS current_id,
        c.depth + 1
    FROM attachment_tree c
    JOIN {{ ref('dim_attachments') }} a
      ON a.attachment_parent_id = c.current_id
),

equipment_tree AS (
    SELECT
        'equipment' AS dimension,
        eq.equipment_name AS ancestor_name,
        eq.equipment_id AS ancestor_id,
        eq.equipment_id AS current_id,
        0 AS depth
    FROM {{ ref('dim_equipment') }} eq

    UNION ALL

    SELECT
        'equipment' AS dimension,
        c.ancestor_name,
        c.ancestor_id,
        eq.equipment_id AS current_id,
        c.depth + 1
    FROM equipment_tree c
    JOIN {{ ref('dim_equipment') }} eq
      ON eq.equipment_parent_id = c.current_id
)

SELECT dimension, ancestor_name, ancestor_id, current_id, depth
FROM exercise_tree
UNION ALL
SELECT dimension, ancestor_name, ancestor_id, current_id, depth
FROM muscle_tree
UNION ALL
SELECT dimension, ancestor_name, ancestor_id, current_id, depth
FROM attachment_tree
UNION ALL
SELECT dimension, ancestor_name, ancestor_id, current_id, depth
FROM equipment_tree
