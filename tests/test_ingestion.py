from pathlib import Path
import pytest
import httpx
from src.ingestion import BTSDataIngestor, OpenSkyIngestor

# --- BTS Data Ingestor Unit Tests ---
def test_download_monthly_archive_already_exists(tmp_path, monkeypatch):
    """Verify that existing archives are skipped unless force=True."""
    # Point RAW_DATA_DIR to a temporary test directory 
    monkeypatch.setattr("src.ingestion.config.RAW_DATA_DIR", tmp_path)

    year, month = 2023, 1
    filename = f"On_Time_Reporting_Carrier_On_Time_Performance_1987_present_{year}_{month}.zip"
    existing_file = tmp_path / filename
    existing_file.write_text("mock zip content")

    ingestor = BTSDataIngestor()
    result_path = ingestor.download_monthly_archive(year, month, force=False)

    assert result_path == existing_file
    assert result_path.read_text() == "mock zip content"

def test_download_monthly_archive_success(tmp_path, monkeypatch):
    """Verify streaming download logic using a mocked httpx response."""
    monkeypatch.setattr("src.ingestion.config.RAW_DATA_DIR", tmp_path)

    # Mock class to simulate httpx stream response context manager
    class MockStreamResponse:
        def raise_for_status(self):
            pass

        def iter_bytes(self, chunk_size=1024):
            yield b"chunk_1_"
            yield b"chunk_2"

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    def mock_stream(method, url, **kwargs):
        return MockStreamResponse()

    monkeypatch.setattr(httpx, "stream", mock_stream)

    ingestor = BTSDataIngestor()
    result_path = ingestor.download_monthly_archive(year=2023, month=1, force=True)

    assert result_path.exists()
    assert result_path.read_bytes() == b"chunk_1_chunk_2"

# --- OpenSky Ingestor Unit Tests ---

def test_fetch_live_states_success(monkeypatch):
    """Verify parsing and normalization of raw OpenSky state vector arrays."""
    mock_payload = {
        "time": 1700000000,
        "states": [
            [
                "4b1812", "SWR126  ", "Switzerland", 1700000000, 1700000000,
                8.54, 47.45, 10000.0, False, 220.5, 180.0, 0.0
            ]
        ]
    }

    class MockResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return mock_payload

    test_bbox = (24.39, 49.38, -124.84, -66.88)

    def mock_get(url, params=None, **kwargs):
        # Verify bbox query parameters are passed correctly
        assert params is not None
        assert params.get("lamin") == test_bbox[0]
        assert params.get("lamax") == test_bbox[1]
        assert params.get("lomin") == test_bbox[2]
        assert params.get("lomax") == test_bbox[3]
        return MockResponse()

    monkeypatch.setattr(httpx, "get", mock_get)

    ingestor = OpenSkyIngestor()
    records = ingestor.fetch_live_states(bbox=test_bbox)

    assert len(records) == 1
    record = records[0]
    assert record["snapshot_time"] == 1700000000
    assert record["icao24"] == "4b1812"
    assert record["callsign"] == "SWR126"  # Stripped whitespace
    assert record["origin_country"] == "Switzerland"
    assert record["baro_altitude"] == 10000.0
    assert record["on_ground"] is False

def test_run_pipeline_execution(tmp_path, monkeypatch):
    """Verify dlt pipeline initialization and execution with mock DuckDB path."""
    mock_db_path = tmp_path / "lakehouse.duckdb"
    monkeypatch.setattr("src.ingestion.config.DUCKDB_PATH", mock_db_path)

    ingestor = OpenSkyIngestor()

    # Mock fetch_live_states directly on the ingestor instance to prevent httpx calls
    def mock_fetch(bbox=None):
        return [{
            "snapshot_time": 1700000000,
            "icao24": "4b1812",
            "callsign": "SWR126",
            "origin_country": "Switzerland",
            "time_position": 1700000000,
            "last_contact": 1700000000,
            "longitude": 8.54,
            "latitude": 47.45,
            "baro_altitude": 10000.0,
            "on_ground": False,
            "velocity": 220.5,
            "true_track": 180.0,
            "vertical_rate": 0.0,
        }]

    monkeypatch.setattr(ingestor, "fetch_live_states", mock_fetch)

    class MockPipeline:
        def run(self, resource):
            return "Pipeline run succeeded"

    def mock_pipeline(*args, **kwargs):
        return MockPipeline()

    monkeypatch.setattr("dlt.pipeline", mock_pipeline)

    pipeline = ingestor.run_pipeline()
    assert isinstance(pipeline, MockPipeline)