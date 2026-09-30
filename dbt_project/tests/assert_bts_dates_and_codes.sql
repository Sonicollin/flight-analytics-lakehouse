select * from {{ ref('stg_bts_flights') }}
where year != year(flight_date) or month != month(flight_date) or day != day(flight_date)
   or source_row <= 0 or carrier = '' or origin = '' or dest = ''
   or distance < 0 or air_time < 0
