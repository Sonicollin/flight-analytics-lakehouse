select *,
    cancelled = 0 and diverted = 0 and arr_delay is not null as is_arrival_eligible,
    case when cancelled = 0 and diverted = 0 and arr_delay is not null
         then arr_delay >= 15 end as is_arrival_delayed,
    case when cancelled = 0 and dep_delay is not null then dep_delay end
        as observed_departure_delay,
    case when cancelled = 0 and diverted = 0 then arr_delay end
        as observed_arrival_delay
from {{ ref('stg_bts_flights') }}
