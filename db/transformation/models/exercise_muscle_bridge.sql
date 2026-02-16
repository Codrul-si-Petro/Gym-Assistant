{{ config(
    depends_on={'model': ['dim_exercises', 'dim_muscles']}
) }}

SELECT 
    em.id,
    em.exercise_id,
    e.exercise_name,
    em.muscle_id,
    m.muscle_name,
    em.muscle_role,
    em.ta_created_at,
    em.ta_updated_at
FROM core.exercise_muscle_bridge em
JOIN core.dim_exercises e ON e.exercise_id = em.exercise_id
JOIN core.dim_muscles m ON m.muscle_id = em.muscle_id
