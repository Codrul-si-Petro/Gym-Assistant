SELECT 
  attachment_id,
  attachment_name,
  attachment_parent_id,
  attachment_description,
  ta_created_at::timestamptz,
  NOT EXISTS (
    SELECT 1
    FROM {{ ref('seed_attachments') }} c
    WHERE c.attachment_parent_id = e.attachment_id
  ) AS is_leaf,
  NOW() AS last_built
FROM {{ ref('seed_attachments') }} e
