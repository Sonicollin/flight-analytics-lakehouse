"""Canonical checkout CLI: ingestion -> source registration -> dbt build -> inspection."""
import argparse
import os
from pathlib import Path
import sys
import subprocess
from src.analytics import FlightAnalyticsEngine
from src.config import BASE_DIR, config
from src.ingestion import BTSDataIngestor, OpenSkyIngestor
from src.storage import ParquetStorageEngine
from src.warehouse import prepare_sources


def run_dbt_build() -> None:
    prepare_sources()
    env = os.environ.copy()
    env.update(DUCKDB_PATH=str(config.DUCKDB_PATH.resolve()),
               DUCKDB_THREADS=str(config.DUCKDB_THREADS),
               DUCKDB_MEMORY_LIMIT=config.DUCKDB_MEMORY_LIMIT,
               DBT_SEND_ANONYMOUS_USAGE_STATS="false")
    project = BASE_DIR / "dbt_project"
    subprocess.run([sys.executable, "-c", "from dbt.cli.main import cli; cli()", "build", "--project-dir", str(project), "--profiles-dir", str(project)],
                   env=env, cwd=BASE_DIR, check=True)


def inspect_outputs() -> None:
    with FlightAnalyticsEngine() as engine:
        print("Carrier-month performance:\n", engine.get_carrier_delay_rankings())
        print("Latest observed snapshot activity:\n", engine.get_snapshot_activity())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["run", "bts", "opensky", "build", "inspect", "demo"])
    parser.add_argument("--year", type=int, default=2023)
    parser.add_argument("--month", type=int, choices=range(1, 13), default=1)
    parser.add_argument("--force", action="store_true", help="Redownload BTS archive")
    parser.add_argument("--bts-archive", type=Path, help="Use a local BTS ZIP instead of HTTP")
    parser.add_argument("--opensky-json", type=Path, help="Load a saved OpenSky API response instead of HTTP")
    args = parser.parse_args()
    config.ensure_directories_exist()
    if args.command == "demo":
        from src.demo import run_demo
        run_demo()
        return
    if args.command in ["run", "bts"]:
        archive = args.bts_archive or BTSDataIngestor().download_monthly_archive(args.year, args.month, args.force)
        ParquetStorageEngine().process_and_partition_archive(archive)
    if args.command in ["run", "opensky"]:
        ingestor = OpenSkyIngestor()
        records = None
        if args.opensky_json:
            import json
            records = ingestor.normalize_payload(json.loads(args.opensky_json.read_text()))
        ingestor.run_pipeline(records=records)
    if args.command in ["run", "bts", "opensky", "build"]:
        run_dbt_build()
    if args.command in ["run", "bts", "opensky", "inspect"]:
        inspect_outputs()

if __name__ == "__main__":
    main()
