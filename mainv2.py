import argparse
import subprocess
import sys
from pathlib import Path
from src.ingestion import BTSDataIngestor, OpenSkyIngestor
from src.storage import ParquetStorageEngine
from src.analytics import FlightAnalyticsEngine

DBT_PROJECT_DIR = Path(__file__).resolve().parent / "dbt_project"


def run_parquet_pipeline(year: int, month: int, force_download: bool) -> None:
    """Ingests raw BTS data and processes it into partitioned Parquet files."""
    print("==================================================")
    print(f"🚀 Running Parquet Storage Pipeline ({year}-{month:02d})")
    print("==================================================")

    # 1. BTS Raw Ingestion
    ingestor = BTSDataIngestor()
    zip_path = ingestor.download_monthly_archive(year=year, month=month, force=force_download)

    # 2. Parquet Storage Processing
    storage_engine = ParquetStorageEngine()
    storage_engine.process_and_partition_archive(zip_path)

    print("✅ Parquet Ingestion Pipeline Complete!\n")


def run_opensky_pipeline() -> None:
    """Fetches live aircraft state vectors via OpenSky REST API into DuckDB."""
    print("==================================================")
    print("🚀 Running OpenSky Live Vector Ingestion")
    print("==================================================")

    opensky_ingestor = OpenSkyIngestor()
    opensky_ingestor.run_pipeline()

    print("✅ OpenSky Ingestion Complete!\n")


def run_dbt_transformations() -> None:
    """Executes dbt models (staging views and intermediate tables)."""
    print("==================================================")
    print("🛠️ Running dbt Transformations")
    print("==================================================")

    if not DBT_PROJECT_DIR.exists():
        print(f"Error: dbt project directory not found at {DBT_PROJECT_DIR}")
        sys.exit(1)

    result = subprocess.run(
        ["dbt", "run", "--project-dir", str(DBT_PROJECT_DIR)],
        check=False
    )

    if result.returncode != 0:
        print("❌ dbt transformation failed.")
        sys.exit(result.returncode)

    print("✅ dbt Transformations Complete!\n")


def run_analytics_query() -> None:
    """Executes the DuckDB in-process OLAP analytics engine query."""
    print("==================================================")
    print("📊 Executing Lakehouse Analytics Engine")
    print("==================================================")

    analytics_engine = FlightAnalyticsEngine()
    rankings = analytics_engine.get_carrier_delay_rankings()

    print("\nCarrier Reliability Rankings:")
    print(rankings)
    print("\n✅ Analytics Execution Complete!")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Flight Analytics Lakehouse CLI Driver"
    )

    # Independent Pipeline Action Flags
    parser.add_argument(
        "--run-parquet",
        action="store_true",
        help="Run BTS raw download and Parquet Hive-partitioning pipeline"
    )
    parser.add_argument(
        "--run-opensky",
        action="store_true",
        help="Run OpenSky REST API ingestion pipeline"
    )
    parser.add_argument(
        "--run-dbt",
        action="store_true",
        help="Run dbt models (staging views and intermediate Python models)"
    )
    parser.add_argument(
        "--run-analytics",
        action="store_true",
        help="Execute DuckDB OLAP query over ingested data"
    )
    parser.add_argument(
        "--run-all",
        action="store_true",
        help="Run full end-to-end pipeline sequentially (Parquet -> OpenSky -> dbt -> Analytics)"
    )

    # Dataset Arguments
    parser.add_argument(
        "--year",
        type=int,
        default=2023,
        help="Year of BTS dataset to process (default: 2023)"
    )
    parser.add_argument(
        "--month",
        type=int,
        default=1,
        help="Month of BTS dataset to process (default: 1)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-download raw ZIP archive even if present locally"
    )

    args = parser.parse_args()

    # Default to showing help if no pipeline action flag is set
    if not any([args.run_parquet, args.run_opensky, args.run_dbt, args.run_analytics, args.run_all]):
        parser.print_help()
        sys.exit(1)

    # Execute selected tasks independently
    if args.run_all or args.run_parquet:
        run_parquet_pipeline(year=args.year, month=args.month, force_download=args.force)

    if args.run_all or args.run_opensky:
        run_opensky_pipeline()

    if args.run_all or args.run_dbt:
        run_dbt_transformations()

    if args.run_all or args.run_analytics:
        run_analytics_query()


if __name__ == "__main__":
    main()