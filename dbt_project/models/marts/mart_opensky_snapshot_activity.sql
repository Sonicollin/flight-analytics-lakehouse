select snapshot_time, snapshot_timestamp,
    count(*) as observed_aircraft,
    count(*) filter (where not on_ground) as airborne_aircraft,
    count(*) filter (where on_ground) as ground_aircraft,
    count(*) filter (where latitude is not null and longitude is not null) as positioned_aircraft,
    count(*) filter (where not on_ground and velocity is not null) as airborne_speed_observations,
    round(avg(velocity) filter (where not on_ground), 2) as avg_airborne_ground_speed_mps
from {{ ref('stg_opensky_states') }}
group by snapshot_time, snapshot_timestamp
