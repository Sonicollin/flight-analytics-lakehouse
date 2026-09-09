import argparse
import sys
from src.ingestion import BTSDataIngestor
from src.storage import ParquetStorageEngine
from src.analytics import FlightAnalyticsEngine

def run_pipeline(year: int, month: int, force_download: bool) -> None:
    """Executes the complete end-to-end data lakehouse pipeline."""
    print("==================================================")
    print(f"🚀 Launching Lakehouse Pipeline for {year}-{month:02d}")
    print("==================================================")

    # Step 1. Raw Ingestion
    print("\n--- Step 1: Ingestion ---")
    ingestor = BTSDataIngestor()
    zip_path = ingestor.download_monthly_archive(year=year, month=month, force=force_download)

    # Step 2. Storage & Partitioning
    print("\n--- Step 2: Storage & Partitioning ---")
    storage_engine = ParquetStorageEngine()
    storage_engine.process_and_partition_archive(zip_path)

    # Step 3. OLAP Analytics Query
    print("\n--- Step 3: OLAP Analytics Query")
    analytics_engine = FlightAnalyticsEngine()
    rankings = analytics_engine.get_carrier_delay_rankings()

    print("\n📊 Carrier Reliability Rankings:")
    print(rankings)
    print("\n==================================================")
    print("✅ Pipeline Execution Complete!")
    print("==================================================")


def main() -> None:
    parser = argparse.ArgumentParser(
        description = "Flight Analytics Lakehouse: In-process Data Pipeline CLI"
    )
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
        help="Force re-download raw ZIP archive even if it exists locally"
    )

    args = parser.parse_args()
    run_pipeline(year=args.year, month=args.month, force_download=args.force)

if __name__ == "__main__":
    main()