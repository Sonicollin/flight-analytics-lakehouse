from pathlib import Path
import httpx
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

        print(f"Downloading {filename} from BTS...")
        
        # Stream response in chunks to prevent high memory consumption
        with httpx.stream("GET", download_url, timeout=120.0, follow_redirects=True) as response:
            response.raise_for_status()
            
            with open(target_path, "wb") as f:
                for chunk in response.iter_bytes(chunk_size=1024 * 1024):  # 1MB chunks
                    f.write(chunk)

        print(f"Successfully saved to {target_path}")
        return target_path


if __name__ == "__main__":
    # Smoke test: Download January 2023 archive
    ingestor = BTSDataIngestor()
    path = ingestor.download_monthly_archive(year=2023, month=1)
    print(f"Downloaded file location: {path}")