-- each exercise–muscle pair may appear only once in the bridge
SELECT exercise_id, muscle_id
FROM {{ ref('seed_exercise_muscle') }}
GROUP BY exercise_id, muscle_id
HAVING COUNT(*) > 1
