import polars as pl

def model(dbt, session):
    # Enable dbt Python model materialization
    dbt.config(materialized="table")

    # Fetch staging refs as Arrow tables
    bts_df = pl.from_arrow(dbt.ref("stg_bts_flights").arrow())
    opensky_df = pl.from_arrow(dbt.ref("stg_opensky_states").arrow())

    # Aggregate historical carrier metrics
    carrier_summary = (
        bts_df.group_by("carrier")
        .agg([
            pl.count("flight_date").alias("total_historical_flights"),
            pl.col("dep_delay").mean().round(2).alias("avg_dep_delay"),
            pl.col("arr_delay").mean().round(2).alias("avg_arr_delay"),
        ])
    )

    # Return summary as PyArrow table for DuckDB persistence
    return carrier_summary.to_arrow()