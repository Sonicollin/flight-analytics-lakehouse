-- Select rows from a Table or View 'TableOrViewName' in schema 'SchemaName'
SELECT
    carrier,
    COUNT(*) AS total_flights,
    ROUND(AVG(dep_delay), 2) AS avg_dep_delay,
    ROUND(AVG(arr_delay), 2) AS avg_arr_delay,
    ROUND(
        100.0 * SUM(CASE WHEN is_delayed THEN 1 ELSE 0 END) 
        / COUNT(is_delayed), 
        2
    ) AS delayed_flight_pct
FROM {{ ref('stg_bts_flights') }}
GROUP BY carrier