import os
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings

# Base Directory: Resolves to project root (flight-analytics-lakehouse)
BASE_DIR = Path(__file__).resolve().parent.parent

class SystemConfig(BaseSettings):
    """Global configuration settings for data paths and DuckDB execution limits."""
    
    # Data Storage Paths
    RAW_DATA_DIR: Path = BASE_DIR / "data" / "raw"
    PROCESSED_DATA_DIR: Path = BASE_DIR / "data" / "processed"

    # Persistent Storage Target
    DUCKDB_PATH: Path = BASE_DIR / "data" / "lakehouse.duckdb"

    # DuckDB In-Process Engine Limits
    # Prevents OOM by capping maximum RAM allocation for query execution
    DUCKDB_MEMORY_LIMIT: str = Field(default="4GB", description="Maximum RAM allocated to DuckDB")
    DUCKDB_THREADS: int = Field(default=4, description="Maximum CPU threads allocated to DuckDB")

    def ensure_directories_exist(self) -> None:
        """Create local data directories if they do not exist."""
        SystemConfig().RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
        SystemConfig().PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
        SystemConfig().DUCKDB_PATH.parent.mkdir(parents=True, exist_ok=True)

# Instantiate singleton configuration
config = SystemConfig()
config.ensure_directories_exist()