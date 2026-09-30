select * from {{ ref('mart_bts_carrier_monthly') }}
where total_flights <= 0 or eligible_arrivals > total_flights
   or delayed_arrivals > eligible_arrivals or cancelled_flights > total_flights
   or diverted_flights > total_flights or departure_delay_observations > total_flights
   or arrival_delay_rate_pct not between 0 and 100
   or cancellation_rate_pct not between 0 and 100
   or (eligible_arrivals = 0 and (arrival_delay_rate_pct is not null or avg_arr_delay is not null))
