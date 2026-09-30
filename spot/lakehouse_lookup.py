from pathlib import Path
import sys

root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))

from src.config import config
import duckdb
import polars as pl

db_path = config.DUCKDB_PATH

# 1. Connect to your local DuckDB database file
with duckdb.connect(str(db_path)) as con:
    con.execute("SELECT * FROM raw_opensky_states LIMIT 10;").pl()