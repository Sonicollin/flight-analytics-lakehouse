from typing import cast
import duckdb
import polars as pl
from config import config

class FlightAnalyticsEngine:
    """In-process DuckDB OLAP engine querying local Hive-partitioned Parquet files."""

    def __init__(self) -> None:
        # Initialize DuckDB connection with strict memory caps from config
        self.con = duckdb.connect(database=":memory:")
        self._configure_engine()
        self._register_parquet_views()

    def _configure_engine(self) -> None:
        """Apply memory limits and thread allocations to enforce out-of-core safety."""
        self.con.execute(f"SET memory_limit = '{config.DUCKDB_MEMORY_LIMIT}';")
        self.con.execute(f"SET threads = {config.DUCKDB_THREADS};")

    def _register_parquet_views(self) -> None:
        """Scan Hive-partitioned Parquet directory directly without loading into memory."""
        parquet_path = str(config.PROCESSED_DATA_DIR / "**" / "*.parquet")

        # Register view over local files using DuckDB's native read_parquet
        self.con.execute(f"""
            CREATE VIEW IF NOT EXISTS flights AS
            SELECT * FROM read_parquet('{parquet_path}', hive_partitioning=true);
        """)

    def get_carrier_delay_rankings(self) -> pl.DataFrame:
        """
        Calculates carrier performance metrics using SQL CTEs and Window Functions.
        
        Returns:
            Polars DataFrame zero-copied from DuckDB Arrow execution.
        """
        query = """
            WITH carrier_stats AS (
                SELECT 
                    carrier,
                    COUNT(*) AS total_flights,
                    ROUND(AVG(dep_delay), 2) AS avg_dep_delay,
                    ROUND(AVG(arr_delay), 2) AS avg_arr_delay,
                    SUM(CASE WHEN arr_delay > 15 THEN 1 ELSE 0 END) AS delayed_flights
                FROM flights
                GROUP BY carrier
            )
            SELECT 
                carrier,
                total_flights,
                avg_dep_delay,
                avg_arr_delay,
                ROUND((delayed_flights * 100.0 / total_flights), 2) AS delay_rate_pct,
                DENSE_RANK() OVER (ORDER BY avg_arr_delay ASC) AS reliability_rank
            FROM carrier_stats
            WHERE total_flights > 100
            ORDER BY reliability_rank;
        """
        # Execute query, fetch as PyArrow Table, and convert to Polars (Zero-Copy)
        arrow_table = self.con.execute(query).to_arrow_table()
        return cast(pl.DataFrame, pl.from_arrow(arrow_table))

if __name__ == "__main__":
    # Smoke test: Query local Lakehouse
    analytics = FlightAnalyticsEngine()
    rankings = analytics.get_carrier_delay_rankings()
    print("--- Carrier Delay Rankings (DuckDB OLAP) ---")
    print(rankings)
