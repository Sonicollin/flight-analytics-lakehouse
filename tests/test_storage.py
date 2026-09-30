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
        "Year,Month,DayofMonth,FlightDate,Reporting_Airline,Origin,Dest,DepDelay,ArrDelay,AirTime,Distance,Cancelled,Diverted\n"
        "2023,1,15,2023-01-15,AA,JFK,LAX,10.0,5.0,300.0,2475.0,0,0\n"
        "2023,1,16,2023-01-16,DL,ATL,ORD,-2.0,-10.0,120.0,606.0,0,0\n"
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
    assert result_df.shape == (2, 12)  # 2 rows, 9 remaining non-partition columns
    assert "carrier" in result_df.columns
    assert "origin" in result_df.columns

def test_invalid_archive_leaves_existing_partition(tmp_path):
    from src.config import config
    fixtures = Path(__file__).parent / "fixtures"
    archive = tmp_path / "bts.zip"
    with zipfile.ZipFile(archive, "w") as z:
        z.write(fixtures / "bts.csv", arcname="bts.csv")
    ParquetStorageEngine().process_and_partition_archive(archive)
    partition = config.PROCESSED_DATA_DIR / "year=2023/month=1"
    files_before = {p.name: p.read_bytes() for p in partition.glob("*.parquet")}
    csv = (fixtures / "bts.csv").read_text().replace('2475,0,0', '2475,9,0')
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("bts.csv", csv)
    with pytest.raises(ValueError, match="cancelled"):
        ParquetStorageEngine().process_and_partition_archive(archive)
    assert files_before == {p.name: p.read_bytes() for p in partition.glob("*.parquet")}


def test_new_month_preserves_previous_partition(tmp_path):
    from src.config import config
    csv = (Path(__file__).parent / "fixtures/bts.csv").read_text()
    for month, content in [(1, csv), (2, csv.replace('2023,1,', '2023,2,').replace('2023-01-', '2023-02-'))]:
        archive = tmp_path / f"month-{month}.zip"
        with zipfile.ZipFile(archive, "w") as z:
            z.writestr("bts.csv", content)
        ParquetStorageEngine().process_and_partition_archive(archive)
    assert len(list(config.PROCESSED_DATA_DIR.rglob("*.parquet"))) == 2
    assert (config.PROCESSED_DATA_DIR / "year=2023/month=1").exists()
    assert (config.PROCESSED_DATA_DIR / "year=2023/month=2").exists()
