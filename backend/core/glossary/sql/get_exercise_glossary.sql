SELECT
  e.exercise_id,
  e.exercise_name,
  e.exercise_movement_type,
  m.youtube_url,
  m.display_title,
  m.notes,
  mu.muscle_id,
  mu.muscle_name,
  b.muscle_role
FROM core.dim_exercises e
LEFT JOIN core.exercise_media m ON e.exercise_id = m.exercise_id
LEFT JOIN core.exercise_muscle_bridge b ON e.exercise_id = b.exercise_id
LEFT JOIN core.dim_muscles mu ON b.muscle_id = mu.muscle_id
WHERE e.is_leaf = true
  AND e.exercise_id != -1
  AND (%(exercise_id)s IS NULL OR e.exercise_id = %(exercise_id)s)
ORDER BY
  e.exercise_name,
  CASE WHEN b.muscle_role = 'Primary' THEN 0 ELSE 1 END,
  mu.muscle_name
