
-- check all attachment ids from the fact table appear in the dimension table

SELECT fw.attachment_id
FROM core.fact_workouts fw
LEFT JOIN core.dim_attachments de
  ON fw.attachment_id = de.attachment_id
WHERE de.attachment_id IS NULL
