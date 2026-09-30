import pytest
from src.config import config

@pytest.fixture(autouse=True)
def isolated_paths(tmp_path, monkeypatch):
    for key, suffix in {"RAW_DATA_DIR": "raw", "PROCESSED_DATA_DIR": "processed",
                        "DUCKDB_PATH": "lakehouse.duckdb", "DLT_PIPELINES_DIR": "dlt",
                        "REJECTED_DATA_DIR": "rejected"}.items():
        monkeypatch.setattr(config, key, tmp_path / suffix)
    monkeypatch.setattr(config, "OPENSKY_TOKEN", None)
