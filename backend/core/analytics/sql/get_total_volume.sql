WITH pre_agg AS (
    -- this is per leaf since we only have leaves in fact table
    SELECT
        fw.exercise_id,
        SUM(
            fw.repetitions::numeric * fw.load::numeric *
            CASE WHEN fw.unit = 'LBS' THEN 0.45359237 ELSE 1 END
        ) AS total_volume_kg
    FROM core.fact_workouts fw
    WHERE fw.user_id = %(user_id)s
      AND (%(start_date)s IS NULL OR fw.date_id >= %(start_date)s::date)
      AND (%(end_date)s IS NULL OR fw.date_id <= %(end_date)s::date)
    GROUP BY fw.exercise_id
),

-- aggregate leaf totals under their parent
-- starts at parent_id NULL to get depth 0 parents
-- once parent_id is specified it's a smooth ride
parent_agg AS (
    SELECT
        dh_parent.current_id AS exercise_id,
        dh_parent.is_leaf AS is_leaf, -- adding this here to let frontend know if it can drill down or not
        dh_parent.current_name AS exercise_name,
        SUM(fw.total_volume_kg) AS total_volume_kg
    FROM core.dimension_hierarchies dh_parent
    LEFT JOIN core.dimension_hierarchies dh_leaf
        ON dh_leaf.dimension = dh_parent.dimension
       AND dh_leaf.parent_id = dh_parent.current_id
    LEFT JOIN pre_agg fw
        ON fw.exercise_id = dh_leaf.current_id
    WHERE dh_parent.dimension = 'exercise'
      AND (
          (%(parent_id)s IS NULL AND dh_parent.parent_id IS NULL)
          OR (%(parent_id)s IS NOT NULL AND dh_parent.parent_id = %(parent_id)s)
      )
    GROUP BY dh_parent.current_id, dh_parent.current_name, dh_parent.is_leaf
),

-- Include dimensions with parent_id IS NULL but are actually leaves ( no hierarchy for them )
leaf_only AS (
    SELECT
        dh.current_id AS exercise_id,
        dh.is_leaf AS is_leaf,
        dh.current_name AS exercise_name,
        fw.total_volume_kg
    FROM core.dimension_hierarchies dh
    LEFT JOIN pre_agg fw
        ON fw.exercise_id = dh.current_id
    WHERE dh.dimension = 'exercise'
      AND NOT EXISTS (
          SELECT 1
          FROM core.dimension_hierarchies c
          WHERE c.parent_id = dh.current_id
            AND c.dimension = 'exercise'
      )
      AND (
          (%(parent_id)s IS NULL AND dh.parent_id IS NULL)
          OR (%(parent_id)s IS NOT NULL AND dh.parent_id = %(parent_id)s)
      )
)

-- Combine parent aggregates and standalone leaves
SELECT * FROM parent_agg
WHERE total_volume_kg IS NOT NULL
UNION ALL
SELECT * FROM leaf_only
WHERE total_volume_kg IS NOT NULL
ORDER BY total_volume_kg DESC;

