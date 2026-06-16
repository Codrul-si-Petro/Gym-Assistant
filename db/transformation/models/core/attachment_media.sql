{{ config(
    depends_on={'model': ['dim_attachments']}
) }}

SELECT
    attachment_id AS media_id,
    attachment_id,
    image_url,
    NULLIF(TRIM(display_title), '') AS display_title,
    NULLIF(TRIM(notes), '') AS notes,
    NOW() AS ta_created_at,
    NULL::timestamptz AS ta_updated_at
FROM {{ ref('seed_attachment_media') }}
