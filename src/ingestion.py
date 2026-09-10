import dlt
import httpx
from pathlib import Path
from config import config

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
        filename = f"On_Time_Reporting_Carrier_On_Time_Performance_1987_present_{year}_{month}.zip"
        target_path = config.RAW_DATA_DIR / filename
        download_url = f"{self.base_url}{filename}"

        if target_path.exists() and not force:
            print(f"Archive already exists locally: {target_path}")
            return target_path

        print(f"Downloading BTS archive for {year}-{month}...")
        
        # Stream response in chunks to prevent high memory consumption
        with httpx.stream("GET", download_url, timeout=120.0, follow_redirects=True) as response:
            response.raise_for_status()
            
            with open(target_path, "wb") as f:
                for chunk in response.iter_bytes(chunk_size=1024 * 1024):  # 1MB chunks
                    f.write(chunk)

        print(f"Successfully saved to {target_path}")
        return target_path

class OpenSkyIngestor:
    """Programmatic REST API ingestion using dlt."""

    def __init__(self, base_url: str = "https://opensky-network.org/api") -> None:
        self.base_url = base_url.rstrip("/")

    def fetch_live_states(self, bbox: tuple[float, float, float, float] | None = None) -> list[dict]:
                                # bbox means "Bounding Box" -> defines a rectangular geographical region on a map using four coordinates.
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
        params = {}

        if bbox:
            params = {
                "lamin": bbox[0], # South boundary
                "lamax": bbox[1], # North boundary
                "lomin": bbox[2], # West boundary
                "lomax": bbox[3], # East boundary
            }

        print("Fetching live state vectors from OpenSky API...")
        response = httpx.get(endpoint, params=params, timeout=30.0)
        response.raise_for_status()

        data = response.json()
        raw_states = data.get("states") or []
        time_snapshot = data.get("time")

        parsed_records = []
        for state in raw_states:
            # Map positional state vectors to named attributes
            parsed_records.append({
                "snapshot_time": time_snapshot,
                "icao24": state[0],
                "callsign": state[1].strip() if state[1] else None,
                "origin_country": state[2],
                "time_position": state[3],
                "last_contact": state[4],
                "longitude": state[5],
                "latitude": state[6],
                "baro_altitude": state[7],
                "on_ground": state[8],
                "velocity": state[9],
                "true_track": state[10],
                "vertical_rate": state[11],
            })

        print(f"Successfully fetched and parsed {len(parsed_records)} aircraft records.")
        return parsed_records

    def run_pipeline(
        self,
        table_name: str = "raw_opensky_states",
        bbox: tuple[float, float, float, float] | None = (24.39, 49.38, -124.84, -66.88) # These coordinates bound to the contiguous United States
    ) -> dlt.Pipeline:
        """
        Executes a dlt pipeline loading normalized state vector streams into persistent DuckDB.
        
        Args:
            table_name: Target landing table name in DuckDB.
            bbox: Bounding box geographical constraints.
        
        Returns:
            dlt.Pipeline execution report instance.
        """
        records = self.fetch_live_states(bbox=bbox)

        # Configure dlt pipeline to target local DuckDB file
        pipeline = dlt.pipeline(
            pipeline_name="opensky_ingestion",
            destination=dlt.destinations.duckdb(credentials=str(config.DUCKDB_PATH)),
            dataset_name="main"
        )

        @dlt.resource(name=table_name, write_disposition="append")
        def opensky_resource():
            yield records

        print(f"Executing dlt pipeline -> Loading into table '{table_name}'...")
        load_info = pipeline.run(opensky_resource())
        print(load_info)        

        return pipeline

if __name__ == "__main__":
    # Smoke test 1: Download January 2023 archive
    bts_ingestor = BTSDataIngestor()
    path = bts_ingestor.download_monthly_archive(year=2023, month=1)
    print(f"Downloaded file location: {path}")

    # Smoke test 2: OpenSky API ingestion via dlt
    opensky_ingestor = OpenSkyIngestor()
    opensky_ingestor.run_pipeline()