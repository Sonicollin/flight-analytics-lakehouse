import zipfile
from pathlib import Path
import polars as pl
import pytest
from src.storage import ParquetStorageEngine

def test_process_and_partition_archive(tmp_path, monkeypatch):
    """Verify raw zip extraction, column transformation, and Parquet Hive partitioning."""
    # Point processed output path to tmp_path
    monkeypatch.setattr("src.storage.config.PROCESSED_DATA_DIR", tmp_path / "processed")

    # 1. Create dummy CSV data matching BTS structure
    csv_content = (
        "Year,Month,DayofMonth,FlightDate,Reporting_Airline,Origin,Dest,DepDelay,ArrDelay,AirTime,Distance\n"
        "2023,1,15,2023-01-15,AA,JFK,LAX,10.0,5.0,300.0,2475.0\n"
        "2023,1,16,2023-01-16,DL,ATL,ORD,-2.0,-10.0,120.0,606.0\n"
    )

    # 2. Package dummy CSV into a zip archive inside tmp_path
    zip_path = tmp_path / "test_flight_data.zip"
    with zipfile.ZipFile(zip_path, "w") as z:
        z.writestr("On_Time_Reporting_Carrier_On_Time_Performance_2023_1.csv", csv_content)

    # 3. Process archive using storage engine
    engine = ParquetStorageEngine()
    processed_dir = engine.process_and_partition_archive(zip_path)

    # 4. Assert Hive partition directory structure (year=2023/month=1/)
    partition_folder = processed_dir / "year=2023" / "month=1"
    assert partition_folder.exists()

    parquet_files = list(partition_folder.glob("*.parquet"))
    assert len(parquet_files) > 0

    # 5. Read generated Parquet back into Polars to check schema & values
    result_df = pl.read_parquet(parquet_files[0])
    assert result_df.shape == (2, 9)  # 2 rows, 9 remaining non-partition columns
    assert "carrier" in result_df.columns
    assert "origin" in result_df.columns