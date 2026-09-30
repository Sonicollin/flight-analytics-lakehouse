-- Compare monthly carrier arrival delays with transparent sample sizes.
select year, month, carrier, total_flights, eligible_arrivals,
       avg_arr_delay, arrival_delay_rate_pct, cancellation_rate_pct, arrival_delay_rank
from {{ ref('mart_bts_carrier_monthly') }}
order by year, month, arrival_delay_rank, carrier;

-- Snapshot-level observed activity, not flights or cumulative unique aircraft.
select * from {{ ref('mart_opensky_snapshot_activity') }}
order by snapshot_timestamp desc;
