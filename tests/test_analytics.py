"""Real integration: ZIP -> Parquet; Pydantic -> dlt -> DuckDB; dbt build -> marts."""
import json
import zipfile
from pathlib import Path
import duckdb
import polars as pl
import pytest
from main import run_dbt_build
from src.analytics import FlightAnalyticsEngine
from src.config import config
from src.ingestion import OpenSkyIngestor
from src.storage import ParquetStorageEngine

FIXTURES = Path(__file__).parent / "fixtures"

@pytest.fixture
def built_lakehouse(tmp_path, monkeypatch):
    archive = tmp_path / "bts.zip"
    with zipfile.ZipFile(archive, "w") as z:
        z.write(FIXTURES / "bts.csv", arcname="bts.csv")
    storage = ParquetStorageEngine()
    storage.process_and_partition_archive(archive)
    # A stale file must disappear on monthly replacement; no duplicate month on rerun.
    partition = config.PROCESSED_DATA_DIR / "year=2023/month=1"
    (partition / "stale.parquet").write_bytes(b"invalid stale file")
    storage.process_and_partition_archive(archive)
    assert not (partition / "stale.parquet").exists()
    ingestor = OpenSkyIngestor()
    records = ingestor.normalize_payload(json.loads((FIXTURES / "opensky.json").read_text()))
    monkeypatch.setattr(ingestor, "fetch_live_states", lambda bbox=None: records)
    ingestor.run_pipeline()
    ingestor.run_pipeline()  # merge the same snapshot; don't double-count observations
    run_dbt_build()
    return config.DUCKDB_PATH


def test_carrier_delay_rankings(built_lakehouse):
    with FlightAnalyticsEngine() as engine:
        result = engine.get_carrier_delay_rankings()
        snapshots = engine.get_snapshot_activity()
    assert isinstance(result, pl.DataFrame)
    aa = result.filter(pl.col("carrier") == "AA").row(0, named=True)
    dl = result.filter(pl.col("carrier") == "DL").row(0, named=True)
    assert aa["total_flights"] == 5
    assert aa["eligible_arrivals"] == 2  # cancel, diversion, missing delay excluded
    assert aa["delayed_arrivals"] == 1  # exactly 15 minutes is delayed
    assert aa["arrival_delay_rate_pct"] == 50
    assert aa["cancellation_rate_pct"] == 20
    assert aa["avg_arr_delay"] == 2.5
    assert aa["arrival_delay_rank"] == 2
    assert dl["arrival_delay_rank"] == 1
    assert dl["arrival_delay_rate_pct"] == 0
    assert snapshots["observed_aircraft"][0] == 2
    assert snapshots["airborne_aircraft"][0] == 1
    assert snapshots["positioned_aircraft"][0] == 1
    assert snapshots["avg_airborne_ground_speed_mps"][0] == 220.5
    with duckdb.connect(str(built_lakehouse), read_only=True) as con:
        assert con.sql("select count(*) from raw.raw_opensky_states").fetchone()[0] == 2
        assert con.sql("select count(*) from main.stg_bts_flights").fetchone()[0] == 7


def test_empty_sources_build(tmp_path):
    run_dbt_build()
    with FlightAnalyticsEngine() as engine:
        assert engine.get_carrier_delay_rankings().is_empty()
        assert engine.get_snapshot_activity().is_empty()
