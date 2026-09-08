# Flight-Analytics-Lakehouse: Phase 2 Roadmap

## 🛫 Phase 1: Storage Architecture & Raw Ingestion
- [ ] **Setup Configuration** (`src/config.py`)
  - [x] Define environment-agnostic paths with `pathlib` (`data/raw`, `data/processed`)
  - [x] Configure DuckDB memory caps and thread allocations
- [ ] **Raw Data Streamer** (`src/ingestion.py`)
  - [ ] Fetch multi-gigabyte BTS Flight Delay archives programmatically
  - [ ] Implement chunked downloading with retry mechanisms using `httpx`

## 📦 Phase 2: Columnar Lakehouse Engine (PyArrow & Polars)
- [ ] **Chunked CSV-to-Parquet Converter** (`src/storage.py`)
  - [ ] Process incoming raw CSV streams using out-of-core chunking
  - [ ] Enforce schema typing using PyArrow schema objects
  - [ ] Export Hive-partitioned Parquet datasets (`year=YYYY/month=MM`)

## 🦆 Phase 3: In-Process OLAP & SQL Layer (DuckDB)
- [ ] **DuckDB Execution Layer** (`src/analytics.py`)
  - [ ] Register partitioned Parquet paths as virtual DuckDB views
  - [ ] Write SQL analytical queries (CTEs, Window Functions like `DENSE_RANK()`, rolling flight delays)
  - [ ] Execute out-of-core queries keeping memory footprint under defined limits
- [ ] **Arrow/Polars Interoperability**
  - [ ] Return DuckDB SQL query results as zero-copy Polars DataFrames

## 🧪 Phase 4: Testing & CLI Driver
- [ ] **Unit Testing** (`tests/`)
  - [ ] Test schema validation and partition layout using `pytest`
  - [ ] Test DuckDB memory limit safety against sample datasets
- [ ] **CLI Execution Driver** (`main.py`)
  - [ ] Build argparse/click CLI to run ingestion, lakehouse conversion, and analytical queries