{{ config(
    depends_on={'model': ['dim_exercises']}
) }}

SELECT
    exercise_id AS media_id,
    exercise_id,
    youtube_url,
    display_title,
    NULLIF(TRIM(notes), '') AS notes,
    NOW() AS ta_created_at,
    NULL::timestamptz AS ta_updated_at
FROM {{ ref('seed_exercise_media') }}
