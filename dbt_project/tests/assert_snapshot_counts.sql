select * from {{ ref('mart_opensky_snapshot_activity') }}
where observed_aircraft <= 0 or airborne_aircraft + ground_aircraft != observed_aircraft
   or positioned_aircraft > observed_aircraft or airborne_speed_observations > airborne_aircraft
