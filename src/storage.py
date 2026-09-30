import tempfile
import zipfile
from pathlib import Path
import polars as pl
import pyarrow.dataset as ds
from .config import config

class ParquetStorageEngine:
    """Process one monthly archive eagerly; memory must fit the decompressed month."""

    @staticmethod
    def process_and_partition_archive(zip_path: Path) -> Path:
        mapping = {"Year": "year", "Month": "month", "DayofMonth": "day",
                   "FlightDate": "flight_date", "Reporting_Airline": "carrier",
                   "Origin": "origin", "Dest": "dest", "DepDelay": "dep_delay",
                   "ArrDelay": "arr_delay", "AirTime": "air_time", "Distance": "distance",
                   "Cancelled": "cancelled", "Diverted": "diverted"}
        with zipfile.ZipFile(zip_path) as archive:
            csvs = [n for n in archive.namelist() if n.lower().endswith(".csv")]
            if len(csvs) != 1:
                raise ValueError("Expected exactly one BTS CSV per monthly archive")
            with archive.open(csvs[0]) as stream:
                # Eager read, selected columns only. Parsing failures are not silently ignored.
                df = pl.read_csv(stream.read(), columns=list(mapping), infer_schema=False)
        df = df.rename(mapping).with_row_index("source_row", offset=1)
        df = df.with_columns(
            pl.col("year", "month", "day").cast(pl.Int32),
            pl.col("flight_date").str.to_date("%Y-%m-%d"),
            pl.col("dep_delay", "arr_delay", "air_time", "distance").cast(pl.Float64),
            pl.col("cancelled", "diverted").cast(pl.Float64),
        )
        if df.is_empty() or df.select("year", "month").unique().height != 1:
            raise ValueError("Archive must contain one nonempty year/month")
        year, month = df.select("year", "month").row(0)
        if year is None or month is None or not 1 <= month <= 12:
            raise ValueError("Invalid BTS partition year/month")
        for flag in ["cancelled", "diverted"]:
            if df[flag].null_count() or not df[flag].is_in([0, 1]).all():
                raise ValueError(f"Invalid BTS {flag} flag")
        if df["flight_date"].null_count() or not df.select(
            ((pl.col("flight_date").dt.year() == pl.col("year")) &
             (pl.col("flight_date").dt.month() == pl.col("month")) &
             (pl.col("flight_date").dt.day() == pl.col("day"))).all()
        ).item():
            raise ValueError("BTS date does not match partition/date fields")
        root = config.PROCESSED_DATA_DIR
        root.mkdir(parents=True, exist_ok=True)
        partition = root / f"year={year}" / f"month={month}"
        # Write fully before replacing this month, so reruns do not retain stale files.
        # Replacement is single-writer and not crash-atomic across both renames.
        with tempfile.TemporaryDirectory(dir=root.parent) as staging:
            ds.write_dataset(df.to_arrow(), staging, format="parquet",
                             partitioning=["year", "month"], partitioning_flavor="hive")
            staged = Path(staging) / f"year={year}" / f"month={month}"
            backup = Path(staging) / "previous"
            partition.parent.mkdir(parents=True, exist_ok=True)
            if partition.exists():
                partition.rename(backup)
            try:
                staged.rename(partition)
            except Exception:
                if backup.exists():
                    backup.rename(partition)
                raise
        print(f"Stored {df.height} BTS rows: {partition}")
        return root
