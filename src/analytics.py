"""Read modeled outputs; analytical business logic lives in dbt SQL."""
import duckdb
import polars as pl
from .config import config

class FlightAnalyticsEngine:
    def __init__(self) -> None:
        self.con = duckdb.connect(str(config.DUCKDB_PATH.resolve()), read_only=True)
        self.con.execute("SET TimeZone = 'UTC'")

    def close(self) -> None:
        self.con.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def get_carrier_delay_rankings(self) -> pl.DataFrame:
        return self.con.sql("SELECT * FROM main.mart_bts_carrier_monthly ORDER BY year, month, arrival_delay_rank, carrier").pl()

    def get_snapshot_activity(self) -> pl.DataFrame:
        return self.con.sql("SELECT * FROM main.mart_opensky_snapshot_activity ORDER BY snapshot_timestamp DESC LIMIT 20").pl()
