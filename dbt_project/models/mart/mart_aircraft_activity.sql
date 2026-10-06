SELECT
    snapshot_timestamp,
    COUNT(*) AS aircraft_observed,
    SUM(CASE WHEN on_ground THEN 1 ELSE 0 END) AS aircraft_on_ground,
    SUM(CASE WHEN NOT on_ground THEN 1 ELSE 0 END) AS aircraft_airborne,
    ROUND(AVG(velocity), 2) AS avg_velocity,
    ROUND(AVG(baro_altitude), 2) AS avg_baro_altitude
FROM {{ ref('stg_opensky_states') }}
GROUP BY snapshot_timestamp
ORDER BY snapshot_timestamp