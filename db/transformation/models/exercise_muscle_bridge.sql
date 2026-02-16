{{ config(
    depends_on={'model': ['dim_exercises', 'dim_muscles']}
) }}

SELECT 
    id,
    exercise_id,
    muscle_id,
    muscle_role,
    ta_created_at,
    ta_updated_at
FROM {{ ref('seed_exercise_muscle') }}
