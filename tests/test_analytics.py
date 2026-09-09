from pathlib import Path
import polars as pl
import pytest
from src.analytics import FlightAnalyticsEngine

@pytest.fixture
def sample_parquet_lakehouse(tmp_path, monkeypatch):
    """
    Creates a mock Hive-partitioned Parquet dataset inside tmp_path
    and patches config.PROCESSED_DATA_DIR to point to it.
    """
    processed_dir = tmp_path / "processed"
    monkeypatch.setattr("src.analytics.config.PROCESSED_DATA_DIR", processed_dir)

    # 1. Generate synthetic flight data with 2 carriers (DL with fewer delays, AA with more)
    # Total flights per carrier > 100 to pass the analytics HAVING/WHERE threshold
    data_dl = {
        "year": [2023] * 105,
        "month": [1] * 105,
        "carrier": ["DL"] * 105,
        "dep_delay": [5.0] * 105,
        "arr_delay": [2.0] * 105,  # Avg arr delay = 2.0
    }
    
    data_aa = {
        "year": [2023] * 105,
        "month": [1] * 105,
        "carrier": ["AA"] * 105,
        "dep_delay": [20.0] * 105,
        "arr_delay": [25.0] * 105, # Avg arr delay = 25.0 (>15 min delay threshold)
    }

    df_dl = pl.DataFrame(data_dl)
    df_aa = pl.DataFrame(data_aa)
    full_df = pl.concat([df_dl, df_aa])

    # 2. Write as Hive-partitioned Parquet file (year=2023/month=1/)
    partition_path = processed_dir / "year=2023" / "month=1"
    partition_path.mkdir(parents=True, exist_ok=True)
    full_df.write_parquet(partition_path / "test_data.parquet")

    return processed_dir


def test_carrier_delay_rankings(sample_parquet_lakehouse):
    """Verify DuckDB SQL query execution, window ranking, and delay percentage calculations."""
    engine = FlightAnalyticsEngine()
    result_df = engine.get_carrier_delay_rankings()

    # 1. Assert return type and row count
    assert isinstance(result_df, pl.DataFrame)
    assert result_df.height == 2  # Both DL and AA have >100 flights

    # 2. Assert schema columns
    expected_cols = [
        "carrier",
        "total_flights",
        "avg_dep_delay",
        "avg_arr_delay",
        "delay_rate_pct",
        "reliability_rank",
    ]
    assert result_df.columns == expected_cols

    # 3. Assert rankings (DL should be rank 1 due to lower avg_arr_delay)
    dl_row = result_df.filter(pl.col("carrier") == "DL")
    aa_row = result_df.filter(pl.col("carrier") == "AA")

    assert dl_row["reliability_rank"][0] == 1
    assert aa_row["reliability_rank"][0] == 2

    # 4. Assert delay rate percentage calculation
    # DL had 0 flights >15 min delay -> 0.0%
    # AA had 105 flights >15 min delay -> 100.0%
    assert dl_row["delay_rate_pct"][0] == 0.0
    assert aa_row["delay_rate_pct"][0] == 100.0