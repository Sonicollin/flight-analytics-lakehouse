select
    concat(snapshot_time, '-', icao24) as observation_id,
    snapshot_time, to_timestamp(snapshot_time) as snapshot_timestamp,
    lower(icao24) as icao24, nullif(trim(callsign), '') as callsign,
    origin_country as registration_country,
    to_timestamp(time_position) as position_timestamp,
    to_timestamp(last_contact) as last_contact_timestamp,
    longitude, latitude, baro_altitude, on_ground, velocity, true_track, vertical_rate
from {{ source('raw', 'raw_opensky_states') }}
