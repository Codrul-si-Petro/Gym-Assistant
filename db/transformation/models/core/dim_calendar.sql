{#
Calendar table used for time slicing and dicing
#}

SELECT
    d::date AS date_id,
    EXTRACT(ISODOW FROM d)::smallint AS week_day,                 -- 1=Monday .. 7=Sunday
    EXTRACT(DAY FROM d)::smallint AS day_number_in_month,
    EXTRACT(DOW FROM d)::smallint AS day_number_in_week,            -- 0=Sunday .. 6=Saturday
    EXTRACT(MONTH FROM d)::smallint AS calendar_month_number,
    TO_CHAR(d, 'Month') AS calendar_month_name,
    EXTRACT(YEAR FROM d)::smallint AS calendar_year,
    CASE WHEN EXTRACT(DOW FROM d) IN (0,6) THEN true ELSE false END AS is_weekend
FROM
    generate_series('2025-01-01'::date, '2035-12-31'::date, '1 day') AS d
ORDER BY d
