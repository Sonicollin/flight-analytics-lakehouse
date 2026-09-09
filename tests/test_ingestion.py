from pathlib import Path
import pytest
import httpx
from src.ingestion import BTSDataIngestor

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