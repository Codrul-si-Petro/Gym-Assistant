{{ config(
    materialized='view',
    schema='staging',
    pre_hook="SELECT 1 FROM {{ ref('seed_exercises') }} LIMIT 1",
    post_hook="
        MERGE INTO core.dim_exercises AS target
        USING staging.seed_dim_exercises AS source
        ON target.exercise_id = source.exercise_id
        WHEN MATCHED THEN
            UPDATE SET
                exercise_name = source.exercise_name,
                exercise_movement_type = source.exercise_movement_type,
                ta_updated_at = NOW()
        WHEN NOT MATCHED THEN
            INSERT (exercise_id, exercise_name, exercise_movement_type, ta_created_at, ta_updated_at)
            VALUES (source.exercise_id, source.exercise_name, source.exercise_movement_type, source.ta_created_at::TIMESTAMP WITH TIME ZONE, NOW())
    "
) }}

SELECT * FROM {{ ref('seed_exercises') }}
