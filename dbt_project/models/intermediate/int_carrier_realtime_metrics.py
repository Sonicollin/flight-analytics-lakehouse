import polars as pl

def fetch_ref_or_empty(dbt, model_name: str) -> pl.DataFrame:
    """Attempts to fetch a dbt ref as a Polars DataFrame;
    
    returns an empty DataFrae if non-existent or unpopulated.
    """
    try:
        arrow_table = dbt.ref(model_name).arrow()
        # Ensure it returns an empty DataFrame if the table exists but is empty
        if arrow_table is None or arrow_table.num_rows == 0:
            return pl.DataFrame()
        return pl.from_arrow(arrow_table)
    except Exception:
        # Catch exception if table/view hasn't been built yet in the database
        return pl.DataFrame()
    
def model(dbt, session):
    # Enable dbt Python model materialization
    dbt.config(materialized="table")

    # Safely load staging dataframes
    bts_df = fetch_ref_or_empty(dbt, "stg_bts_flights")
    opensky_df = fetch_ref_or_empty(dbt, "stg_opensky_states")

    has_bts = not bts_df.is_empty()
    has_opensky = not opensky_df.is_empty()

    if not has_bts and not has_opensky:
        # Neither populated: retrun empty schema or early exits
        return pl.DataFrame()
    
    if has_bts and has_opensky:
        final_df = bts_df.join(opensky_df, on="flight_id", how="inner")
    elif has_bts:
        final_df = bts_df
    else:
        final_df = opensky_df

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