WITH raw_parquet AS (
    SELECT *
    FROM read_parquet('../data/processed/**/*.parquet', hive_partitioning=true)
)
SELECT
    year,
    month,
    day,
    flight_date,
    carrier,
    origin,
    dest,
    dep_delay,
    arr_delay,
    air_time,
    distance,
    CASE WHEN arr_delay > 15 THEN TRUE ELSE FALSE END AS is_delayed
FROM raw_parquet    