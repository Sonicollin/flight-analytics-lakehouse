from pathlib import Path
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

class SystemConfig(BaseSettings):
    """Paths default to this checkout; relative overrides resolve from the caller's cwd."""
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", extra="ignore")
    RAW_DATA_DIR: Path = BASE_DIR / "data/raw"
    PROCESSED_DATA_DIR: Path = BASE_DIR / "data/processed/bts"
    DUCKDB_PATH: Path = BASE_DIR / "data/lakehouse.duckdb"
    DLT_PIPELINES_DIR: Path = BASE_DIR / "data/dlt"
    REJECTED_DATA_DIR: Path = BASE_DIR / "data/rejected"
    DUCKDB_MEMORY_LIMIT: str = "4GB"
    DUCKDB_THREADS: int = Field(default=4, ge=1)
    OPENSKY_TOKEN: SecretStr | None = None

    def ensure_directories_exist(self) -> None:
        for path in [self.RAW_DATA_DIR, self.PROCESSED_DATA_DIR,
                     self.DUCKDB_PATH.parent, self.DLT_PIPELINES_DIR, self.REJECTED_DATA_DIR]:
            path.mkdir(parents=True, exist_ok=True)

config = SystemConfig()
