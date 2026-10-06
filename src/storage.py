import zipfile
from pathlib import Path
import polars as pl
import pyarrow as pa
import pyarrow.dataset as ds
from src.config import config

class ParquetStorageEngine:
    """Converts raw BTS CSV archives into Hive-partitioned Parquet datasets."""

    @staticmethod
    def process_and_partition_archive(zip_path: Path) -> Path:
        """
        Extracts raw CSV from zip, converts to Polars DataFrame,
        and writes Hive-partitioned Parquet files (year=/month=).
        
        Args:
            zip_path: Path to the raw BTS zip archive.
        
        Returns:
            Path to processed root directory.
        """
        print(f"Processing archive: {zip_path.name}...")

        # Read CSV directly from memory without extracting to disk
        with zipfile.ZipFile(zip_path, "r") as z:
            csv_filename = [f for f in z.namelist() if f.endswith(".csv")][0]
            with z.open(csv_filename) as csv_file:
                df = pl.read_csv(
                    csv_file.read(),
                    infer_schema_length=10000,
                    ignore_errors=True
                )

        # Select & clean core analytical columns
        transformed_df = df.select([
            pl.col("Year").cast(pl.Int32).alias("year"),
            pl.col("Month").cast(pl.Int32).alias("month"),
            pl.col("DayofMonth").cast(pl.Int32).alias("day"),
            pl.col("FlightDate").alias("flight_date"),
            pl.col("Reporting_Airline").alias("carrier"),
            pl.col("Origin").alias("origin"),
            pl.col("Dest").alias("dest"),
            pl.col("DepDelay").cast(pl.Float64).alias("dep_delay"),
            pl.col("ArrDelay").cast(pl.Float64).alias("arr_delay"),
            pl.col("AirTime").cast(pl.Float64).alias("air_time"),
            pl.col("Distance").cast(pl.Float64).alias("distance"),
        ])

        # Convert Polars DataFrame to PyArrow Table for Hive partitioning
        arrow_table = transformed_df.to_arrow()

        # Examine row count of PyArrow Table
        print(f"Transformed row count: {transformed_df.height}")

        # Write dataset using PyArrow with Hive partitioning (year/month)
        ds.write_dataset(
            data=arrow_table,
            base_dir=config.PROCESSED_DATA_DIR,
            format="parquet",
            partitioning=["year", "month"],
            partitioning_flavor="hive",
            existing_data_behavior="overwrite_or_ignore"
        )

        print(f"Successfully stored partitioned Parquet dataset in {config.PROCESSED_DATA_DIR}")
        return config.PROCESSED_DATA_DIR

if __name__ == "__main__":
    # Smoke test over downloaded raw archive
    raw_zips = list(config.RAW_DATA_DIR.glob("*.zip"))
    if raw_zips:
        engine = ParquetStorageEngine()
        engine.process_and_partition_archive(raw_zips[0])
    else:
        print("No raw zip archives found in data/raw. Run src/ingestion.py first.")
