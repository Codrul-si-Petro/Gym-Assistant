SELECT  
 c.date_id
FROM core.dim_calendar c
LEFT JOIN core.fact_workouts fw ON c.date_id = fw.date_id
WHERE fw.date_id IS null
AND c.date_id BETWEEN
  (SELECT min(date_id) FROM core.fact_workouts WHERE user_id = %(user_id)s)
  AND
  (SELECT max(date_id) FROM core.fact_workouts WHERE user_id = %(user_id)s)

