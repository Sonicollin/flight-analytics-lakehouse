"""Register stable dbt sources in the shared DuckDB database."""
import duckdb
from .config import config

def empty_projection(columns: str) -> str:
    expressions = []
    for definition in columns.split(","):
        name, sql_type = definition.strip().rsplit(" ", 1)
        expressions.append(f"CAST(NULL AS {sql_type}) AS {name}")
    return ", ".join(expressions)


BTS_COLUMNS = """source_row BIGINT, year INTEGER, month INTEGER, day INTEGER,
flight_date DATE, carrier VARCHAR, origin VARCHAR, dest VARCHAR,
dep_delay DOUBLE, arr_delay DOUBLE, air_time DOUBLE, distance DOUBLE,
cancelled DOUBLE, diverted DOUBLE"""
def prepare_sources() -> dict[str, int]:
    """Absent datasets get typed empty sources; never populate them with demo data."""
    config.ensure_directories_exist()
    with duckdb.connect(str(config.DUCKDB_PATH.resolve())) as con:
        exists = con.execute("SELECT count(*) FROM information_schema.tables WHERE table_schema = 'raw' AND table_name = 'raw_opensky_states'").fetchone()[0]
    if not exists:
        # Let dlt own its table schema, including metadata columns, even before the first snapshot.
        from .ingestion import OpenSkyIngestor
        OpenSkyIngestor().run_pipeline(records=[])
    with duckdb.connect(str(config.DUCKDB_PATH.resolve())) as con:
        con.execute("CREATE SCHEMA IF NOT EXISTS raw")
        glob = str(config.PROCESSED_DATA_DIR.resolve() / "**/*.parquet").replace("'", "''")
        if any(config.PROCESSED_DATA_DIR.rglob("*.parquet")):
            con.execute(f"CREATE OR REPLACE VIEW raw.bts_flights AS SELECT * FROM read_parquet('{glob}', hive_partitioning=true)")
        else:
            con.execute(f"CREATE OR REPLACE VIEW raw.bts_flights AS SELECT * FROM (SELECT {empty_projection(BTS_COLUMNS)}) WHERE FALSE")
        counts = {name: con.execute(f"SELECT count(*) FROM raw.{name}").fetchone()[0]
                  for name in ["bts_flights", "raw_opensky_states"]}
    print(f"Source counts: {counts}; zero means absent/empty, not verified ingestion")
    return counts
