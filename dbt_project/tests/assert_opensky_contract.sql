select * from {{ ref('stg_opensky_states') }}
where not regexp_full_match(icao24, '[0-9a-f]{6}')
   or (latitude is null) != (longitude is null)
   or latitude not between -90 and 90 or longitude not between -180 and 180
   or velocity < 0 or true_track < 0 or true_track >= 360
