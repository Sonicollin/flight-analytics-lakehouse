
  
  create view "lakehouse"."main"."stg_opensky_states__dbt_tmp" as (
    SELECT
    to_timestamp(snapshot_time) AS snapshot_timestamp,
    icao24,
    TRIM(callsign) AS callsign,
    origin_country,
    to_timestamp(time_position) AS position_timestamp,
    to_timestamp(last_contact) AS last_contact_timestamp,
    longitude,
    latitude,
    baro_altitude,
    on_ground,
    velocity,
    true_track,
    vertical_rate
FROM main.raw_opensky_states
  );
