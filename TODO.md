# Flight-Analytics-Lakehouse: Phase 2 Roadmap

## 🛫 Milestone 1: Storage Architecture & Raw Ingestion
- [x] **Setup Configuration** (`src/config.py`)
  - [x] Define environment-agnostic paths with `pathlib` (`data/raw`, `data/processed`)
  - [x] Configure DuckDB memory caps and thread allocations
- [x] **Raw Data Streamer** (`src/ingestion.py`)
  - [x] Fetch multi-gigabyte BTS Flight Delay archives programmatically
  - [x] Implement chunked downloading with retry mechanisms using `httpx`

## 📦 Milestone 2: Columnar Lakehouse Engine (PyArrow & Polars)
- [x] **Chunked CSV-to-Parquet Converter** (`src/storage.py`)
  - [x] Process incoming raw CSV streams using out-of-core chunking
  - [x] Enforce schema typing using PyArrow schema objects
  - [x] Export Hive-partitioned Parquet datasets (`year=YYYY/month=MM`)

## 🦆 Milestone 3: In-Process OLAP & SQL Layer (DuckDB)
- [x] **DuckDB Execution Layer** (`src/analytics.py`)
  - [x] Register partitioned Parquet paths as virtual DuckDB views
  - [x] Write SQL analytical queries (CTEs, Window Functions like `DENSE_RANK()`, rolling flight delays)
  - [x] Execute out-of-core queries keeping memory footprint under defined limits
- [x] **Arrow/Polars Interoperability**
  - [x] Return DuckDB SQL query results as zero-copy Polars DataFrames

## 🧪 Milestone 4: Testing & CLI Driver
- [x] **Unit Testing** (`tests/`)
  - [x] Test schema validation and partition layout using `pytest`
- [x] **CLI Execution Driver** (`main.py`)
  - [x] Build argparse/click CLI to run ingestion, lakehouse conversion, and analytical queries

# Phase 3 Roadmap: Analytics Engineering, Data Contract, and Programmatic Ingestion

## Milestone 1: Automated REST API Ingestion with `dlt`
- [x] Configure `dlt` pipeline environment and dependencies in `pyproject.toml`
- [x] Update `src/config.py` to support persistent DuckDB storage (`DUCKDB_PATH`) alongside existing memory caps
- [x] Implement `OpenSkyIngestor` in `src/ingestion.py` using `dlt` REST API connector targeting OpenSky state vectors
- [x] Configure `dlt` state management for incremental loads, schema evolution, and bounding box filters
- [x] Write unit tests for `dlt` pipeline extraction in `tests/test_ingestion.py`

## Milestone 2: Schema Enforcement & Data Contracts with `Pydantic`
- [x] Create `src/contracts.py` with Pydantic models for incoming payload validation
- [x] Implement strict field typing, range checks, and nullability rules
- [x] Integrate contract verification prior to persistence step
- [x] Write unit/contract tests verifying failure handling for schema drift in `tests/test_contracts.py`

## Milestone 3: Declarative Transformations with `dbt` & `dbt-duckdb`
- [ ] Initialize `dbt` project directory (`dbt_project/`) with DuckDB adapter (`dbt-duckdb`)
- [ ] Configure `profiles.yml` and `dbt_project.yml` targeting the local lakehouse/DuckDB storage
- [ ] Build staging (`stg_*.sql`) and intermediate models for flight/carrier transformations
- [ ] Implement a `dbt` Python model (`.py`) for advanced statistical calculations or custom metrics
- [ ] Define data tests (`schema.yml`) and documentation across dbt models

## Milestone 4: Integration, Orchestration & CLI Expansion
- [ ] Update CLI driver (`main.py`) to orchestrate dlt ingestion, Pydantic validation, and dbt execution
- [ ] Ensure end-to-end integration tests pass with zero static typing or runtime errors
- [ ] Update repository `README.md` with Phase 3 architectural diagrams and usage commands