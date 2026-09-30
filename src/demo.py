"""Deterministic synthetic example using the same ingestion/storage/dbt workflow."""
import json
import zipfile
from .config import BASE_DIR, config
from .ingestion import OpenSkyIngestor
from .storage import ParquetStorageEngine


def run_demo() -> None:
    from main import run_dbt_build, inspect_outputs
    # Explicitly isolate synthetic data from live/default storage.
    root = BASE_DIR / "data/demo"
    config.RAW_DATA_DIR = root / "raw"
    config.PROCESSED_DATA_DIR = root / "processed/bts"
    config.DUCKDB_PATH = root / "lakehouse.duckdb"
    config.DLT_PIPELINES_DIR = root / "dlt"
    config.REJECTED_DATA_DIR = root / "rejected"
    config.ensure_directories_exist()
    fixtures = BASE_DIR / "tests/fixtures"
    archive = config.RAW_DATA_DIR / "synthetic-bts.zip"
    with zipfile.ZipFile(archive, "w") as z:
        z.write(fixtures / "bts.csv", arcname="bts.csv")
    ParquetStorageEngine().process_and_partition_archive(archive)
    ingestor = OpenSkyIngestor()
    records = ingestor.normalize_payload(json.loads((fixtures / "opensky.json").read_text()))
    ingestor.run_pipeline(records=records)
    run_dbt_build()
    print("SYNTHETIC DEMO ONLY; not observations downloaded from BTS/OpenSky")
    inspect_outputs()
    print(f"Demo database: {config.DUCKDB_PATH}")
