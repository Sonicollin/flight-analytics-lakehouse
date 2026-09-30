import json
from datetime import datetime, timezone
import dlt
import httpx
from pathlib import Path
from .config import config
from .contracts import validate_state_vectors

class BTSDataIngestor:
    """Streams and manages raw BTS Flight Delay data archives."""

    def __init__(self, base_url: str | None = None) -> None:
        # Default BTS On-Time Performance zip download endpoint template
        self.base_url = base_url or "https://transtats.bts.gov/PREZIP/"

    def download_monthly_archive(self, year: int, month: int, force: bool = False) -> Path:
        """
        Stream-downloads a specific year/month zip file from BTS.
        
        Args:
            year: Four-digit year (e.g., 2023)
            month: Month integer (1-12)
            force: Re-download if file already exists locally

        Returns:
            Path object pointing to the downloaded raw zip file.
        """
        if year < 1987 or not 1 <= month <= 12:
            raise ValueError("BTS year must be >=1987 and month must be 1..12")
        config.RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
        filename = f"On_Time_Reporting_Carrier_On_Time_Performance_1987_present_{year}_{month}.zip"
        target_path = config.RAW_DATA_DIR / filename
        download_url = f"{self.base_url}{filename}"

        if target_path.exists() and not force:
            print(f"Archive already exists locally: {target_path}")
            return target_path

        print(f"Downloading BTS archive for {year}-{month}...")
        
        # Download to a temporary name so interrupted requests are never cached as complete.
        partial = target_path.with_suffix(".zip.part")
        try:
            with httpx.stream("GET", download_url, timeout=120.0, follow_redirects=True) as response:
                response.raise_for_status()
                with partial.open("wb") as f:
                    for chunk in response.iter_bytes(chunk_size=1024 * 1024):
                        f.write(chunk)
            partial.replace(target_path)
        finally:
            partial.unlink(missing_ok=True)

        print(f"Successfully saved to {target_path}")
        return target_path

class OpenSkyIngestor:
    """Programmatic REST API ingestion using dlt."""

    def __init__(self, base_url: str = "https://opensky-network.org/api") -> None:
        self.base_url = base_url.rstrip("/")

    def fetch_live_states(self, bbox: tuple[float, float, float, float] | None = (24.39, 49.38, -124.84, -66.88)) -> list[dict]:
        """
        Fetches live aircraft state vectors from OpenSky REST API and normalizes
        raw position arrays into key-value JSON records.

        Args:
            bbox: Tuple of (lamin, lamax, lomin, lomax) to bound search region.
                  Defaults to contiguous US coordinates.
        
        Returns:
            List of parsed state vector dictionaries.
        """
        endpoint = f"{self.base_url}/states/all"
        if bbox is None:
            bbox = (24.39, 49.38, -124.84, -66.88)

        params = {
            "lamin": bbox[0],
            "lamax": bbox[1],
            "lomin": bbox[2],
            "lomax": bbox[3],
        }

        print("Fetching live state vectors from OpenSky API...")
        headers = {}
        if config.OPENSKY_TOKEN:
            headers["Authorization"] = f"Bearer {config.OPENSKY_TOKEN.get_secret_value()}"
        response = httpx.get(endpoint, params=params, headers=headers, timeout=30.0)
        response.raise_for_status()
        return self.normalize_payload(response.json())

    @staticmethod
    def normalize_payload(data: dict) -> list[dict]:
        """Fail on malformed envelopes/vectors; validate individual field values at load time."""
        if not isinstance(data, dict) or not isinstance(data.get("time"), int):
            raise ValueError("OpenSky payload requires integer time")
        raw_states = data.get("states")
        if raw_states is None:
            raw_states = []
        if not isinstance(raw_states, list):
            raise ValueError("OpenSky states must be a list or null")
        names = ["icao24", "callsign", "origin_country", "time_position", "last_contact",
                 "longitude", "latitude", "baro_altitude", "on_ground", "velocity",
                 "true_track", "vertical_rate"]
        parsed_records = []
        for state in raw_states:
            if not isinstance(state, list) or len(state) < len(names):
                raise ValueError("OpenSky state vector requires at least 12 fields")
            record = dict(zip(names, state))
            if isinstance(record["callsign"], str):
                record["callsign"] = record["callsign"].strip() or None
            record["snapshot_time"] = data["time"]
            parsed_records.append(record)

        print(f"Successfully fetched and parsed {len(parsed_records)} aircraft records.")
        return parsed_records

    def run_pipeline(
        self,
        table_name: str = "raw_opensky_states",
        bbox: tuple[float, float, float, float] | None = (24.39, 49.38, -124.84, -66.88),
        records: list[dict] | None = None,
    ) -> dlt.Pipeline:
        """
        Executes a dlt pipeline loading normalized state vector streams into persistent DuckDB.
        
        Args:
            table_name: Target landing table name in DuckDB.
            bbox: Bounding box geographical constraints.
            records: Optional normalized records from a saved response (None fetches HTTP).
        
        Returns:
            dlt Pipeline instance; failed loading jobs raise before return.
        """
        raw_records = self.fetch_live_states(bbox=bbox) if records is None else records

        # Enforce Pydantic Data Contract
        valid_records, rejected = validate_state_vectors(raw_records)

        if rejected:
            print(f"Warning: {len(rejected)} records failed contract validation and were withheld from loading.")

        config.ensure_directories_exist()
        if rejected:
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
            path = config.REJECTED_DATA_DIR / f"opensky-{stamp}.json"
            path.write_text(json.dumps(rejected, indent=2))
            print(f"Rejected records retained at {path}")
        if raw_records and not valid_records:
            raise ValueError("All OpenSky records failed validation; see rejected records")
        pipeline = dlt.pipeline(
            pipeline_name="opensky_ingestion",
            pipelines_dir=str(config.DLT_PIPELINES_DIR),
            destination=dlt.destinations.duckdb(credentials=str(config.DUCKDB_PATH.resolve())),
            dataset_name="raw",
            runtime={"dlthub_telemetry": False},
        )
        # Explicit types preserve nullable fields even when a snapshot contains only nulls.
        types = {"snapshot_time": "bigint", "icao24": "text", "callsign": "text",
                 "origin_country": "text", "time_position": "bigint", "last_contact": "bigint",
                 "longitude": "double", "latitude": "double", "baro_altitude": "double",
                 "on_ground": "bool", "velocity": "double", "true_track": "double",
                 "vertical_rate": "double"}
        columns = {k: {"data_type": v, "nullable": k not in
                   ["snapshot_time", "icao24", "origin_country", "last_contact", "on_ground"]}
                   for k, v in types.items()}
        @dlt.resource(name=table_name, write_disposition="merge",
                      primary_key=["snapshot_time", "icao24"], columns=columns)
        def opensky_resource():
            # Materialize a typed empty table for a valid snapshot with no observations.
            if valid_records:
                yield valid_records
            else:
                yield dlt.mark.materialize_table_schema()

        info = pipeline.run(opensky_resource())
        info.raise_on_failed_jobs()
        print(f"Loaded {len(valid_records)} validated OpenSky observations")
        return pipeline
