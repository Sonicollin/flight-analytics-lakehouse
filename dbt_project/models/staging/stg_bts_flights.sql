select
    concat(year, '-', month, '-', source_row) as bts_row_id,
    source_row, year::integer as year, month::integer as month,
    day::integer as day, flight_date::date as flight_date,
    trim(carrier) as carrier, trim(origin) as origin, trim(dest) as dest,
    dep_delay, arr_delay, air_time, distance,
    cancelled::integer as cancelled, diverted::integer as diverted
from {{ source('raw', 'bts_flights') }}
