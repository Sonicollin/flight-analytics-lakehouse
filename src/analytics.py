from pathlib import Path
from typing import cast
import duckdb
import polars as pl
from src.config import config

class FlightAnalyticsEngine:
    """Queries analytical models built by dbt in the local DuckDB lakehouse."""

    def __init__(self) -> None:
        self.con = duckdb.connect(database=str(config.DUCKDB_PATH))

    def get_carrier_delay_rankings(self) -> pl.DataFrame:
        """
        Returns carrier performance metrics from the dbt mart,
        ranked by average arrival delay.
        """
        query = """
            SELECT
                carrier,
                total_flights,
                avg_dep_delay,
                avg_arr_delay,
                delayed_flight_pct,
                DENSE_RANK() OVER (
                    ORDER BY avg_arr_delay ASC
                ) AS reliability_rank
            FROM mart_carrier_performance
            WHERE total_flights > 100
            ORDER BY reliability_rank
        """
        # Execute query, fetch as PyArrow Table, and convert to Polars
        arrow_table = self.con.execute(query).to_arrow_table()
        return cast(pl.DataFrame, pl.from_arrow(arrow_table))

if __name__ == "__main__":
    # Smoke test: Query local Lakehouse
    analytics = FlightAnalyticsEngine()
    rankings = analytics.get_carrier_delay_rankings()
    print("--- Carrier Delay Rankings (DuckDB OLAP) ---")
    print(rankings)
