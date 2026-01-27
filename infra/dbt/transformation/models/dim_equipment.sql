{{ config(
    materialized='view',
    schema='staging',
    pre_hook="SELECT 1 FROM {{ ref('seed_equipment') }} LIMIT 1",
    post_hook="
        MERGE INTO core.dim_equipment AS target
        USING staging.seed_dim_equipment AS source
        ON target.equipment_id = source.equipment_id
        WHEN MATCHED THEN
            UPDATE SET
                equipment_name = source.equipment_name,
                equipment_description = source.equipment_description,
                equipment_category = source.equipment_category,
                ta_updated_at = NOW()
        WHEN NOT MATCHED THEN
            INSERT (equipment_id, equipment_name, equipment_description, equipment_category, ta_created_at, ta_updated_at)
            VALUES (source.equipment_id, source.equipment_name, source.equipment_description, source.equipment_category, source.ta_created_at::TIMESTAMP WITH TIME ZONE, NOW())
    "
) }}

SELECT * FROM {{ ref('seed_equipment') }}
