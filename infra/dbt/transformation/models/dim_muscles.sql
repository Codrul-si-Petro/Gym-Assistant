{{ config(
    materialized='view',
    schema='staging',
    pre_hook="SELECT 1 FROM {{ ref('seed_muscles') }} LIMIT 1",
    post_hook="
        MERGE INTO core.dim_muscles AS target
        USING staging.seed_dim_muscles AS source
        ON target.muscle_id = source.muscle_id
        WHEN MATCHED THEN
            UPDATE SET
                muscle_name = source.muscle_name,
                muscle_group = source.muscle_group,
                ta_updated_at = NOW()
        WHEN NOT MATCHED THEN
            INSERT (muscle_id, muscle_name, muscle_group, ta_created_at, ta_updated_at)
            VALUES (source.muscle_id, source.muscle_name, source.muscle_group, source.ta_created_at::TIMESTAMP WITH TIME ZONE, NOW())
    "
) }}

SELECT * FROM {{ ref('seed_muscles') }}
