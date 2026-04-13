{{ config(
    depends_on={'model': ['dim_exercises', 'dim_muscles']}
) }}

SELECT 
    id,
    exercise_id,
    muscle_id,
    muscle_role,
    NOW() AS last_built
FROM {{ ref('seed_exercise_muscle') }}
