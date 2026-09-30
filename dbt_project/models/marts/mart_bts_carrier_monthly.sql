with summary as (
    select year, month, carrier,
        count(*) as total_flights,
        count(*) filter (where cancelled = 1) as cancelled_flights,
        count(*) filter (where diverted = 1) as diverted_flights,
        count(observed_departure_delay) as departure_delay_observations,
        count(*) filter (where is_arrival_eligible) as eligible_arrivals,
        count(*) filter (where is_arrival_delayed) as delayed_arrivals,
        round(avg(observed_departure_delay), 2) as avg_dep_delay,
        round(avg(observed_arrival_delay), 2) as avg_arr_delay,
        round(100.0 * count(*) filter (where is_arrival_delayed)
              / nullif(count(*) filter (where is_arrival_eligible), 0), 2) as arrival_delay_rate_pct,
        round(100.0 * count(*) filter (where cancelled = 1) / count(*), 2) as cancellation_rate_pct
    from {{ ref('int_bts_flight_outcomes') }}
    group by year, month, carrier
)
select concat(year, '-', month, '-', carrier) as carrier_month_id, *,
    case when eligible_arrivals > 0 then dense_rank() over (
        partition by year, month order by avg_arr_delay asc nulls last) end as arrival_delay_rank
from summary
