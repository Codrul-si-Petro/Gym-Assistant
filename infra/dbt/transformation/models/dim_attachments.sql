{{ config(
    materialized='view',
    schema='staging',
    pre_hook="SELECT 1 FROM {{ ref('seed_attachments') }} LIMIT 1",
    post_hook="
        MERGE INTO core.dim_attachments AS target
        USING staging.seed_dim_attachments AS source
        ON target.attachment_id = source.attachment_id
        WHEN MATCHED THEN
            UPDATE SET
                attachment_name = source.attachment_name,
                attachment_description = source.attachment_description,
                ta_updated_at = NOW()
        WHEN NOT MATCHED THEN
            INSERT (attachment_id, attachment_name, attachment_description, ta_created_at, ta_updated_at)
            VALUES (source.attachment_id, source.attachment_name, source.attachment_description, source.ta_created_at::TIMESTAMP WITH TIME ZONE, NOW())
    "
) }}

SELECT * FROM {{ ref('seed_attachments') }}
