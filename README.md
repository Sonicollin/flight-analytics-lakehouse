# ✈️ Flight Analytics Lakehouse

An in-process, memory-efficient data engineering pipeline designed to handle multi-gigabyte open-source flight delay data from the **US Bureau of Transportation Statistics (BTS)**. 

This project demonstrates an out-of-core **Local Data Lakehouse** architecture built using Python 3.12+, `httpx` streaming, `Polars`, `PyArrow`, and `DuckDB`.

---

## 🏗️ Architecture & Stack

┌────────────────┐       ┌─────────────────┐       ┌────────────────────┐       ┌──────────────────┐
│  BTS Archives  │ ────> │ Streaming Fetch │ ────> │ Hive Partitioning  │ ────> │ DuckDB Execution │
│  (Remote ZIP)  │       │  (httpx stream) │       │ (PyArrow + Polars) │       │   (OLAP Engine)  │
└────────────────┘       └─────────────────┘       └────────────────────┘       └──────────────────┘
│
▼
┌──────────────────┐
│ Zero-Copy Polars │
│    DataFrame     │
└──────────────────┘

* **Ingestion:** `httpx` (Chunked HTTP streaming for safe memory handling)
* **Storage & Transformation:** `Polars` & `PyArrow` (CSV-to-Parquet conversion with Hive partitioning)
* **Analytics Engine:** `DuckDB` (In-process OLAP engine running SQL CTEs & Window Functions)
* **Configuration & Safety:** `pydantic-settings` (Type-safe paths and strict memory/thread limits)
* **Testing:** `pytest` (Isolated unit tests using temporary file fixtures)

---

## Key Features

* **Out-of-Core Processing:** Process multi-gigabyte datasets safely on consumer hardware without Out-Of-Memory (OOM) crashes.
* **Columnar Lakehouse Layout:** Converts raw CSVs into compressed, Hive-partitioned Parquet files organized by `year=YYYY/month=MM/`.
* **Zero-Copy Interoperability:** Queries Parquet files directly on disk via DuckDB and exports results to Polars DataFrames using Apache Arrow pointers.
* **Bounded Resources:** Enforces strict memory caps and thread caps on the DuckDB execution kernel via central configuration settings.

---

##  Quickstart

### 1. Prerequisites & Installation

Clone the repository and install dependencies in an editable environment:

```bash
git clone [https://github.com/Sonicollin/flight-analytics-lakehouse.git](https://github.com/Sonicollin/flight-analytics-lakehouse.git)
cd flight-analytics-lakehouse

python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

pip install -e .
```

### 2. Run the Full Pipeline

Use the CLI orchestrator to ingest, partition, and query BTS flight data for a given month:

```bash
python main.py --year 2023 --month 1
```
#### CLI Flags

* --year: Target dataset year (default: 2023)
* --month: Target dataset month (default: 1)
* --force: Force re-download of raw zip even if present locally

## Sample Output

Running main.py generates on-disk Parquet partitions and executes a carrier reliability analysis ranking airlines by average delay:

==================================================
🚀 Launching Lakehouse Pipeline for 2023-01
==================================================

--- Step 1: Ingestion ---
Downloading BTS archive for 2023-01...

--- Step 2: Storage & Partitioning ---
Processing archive: On_Time_Reporting_Carrier_On_Time_Performance_2023_1.zip...
Transformed row count: 324199
Successfully stored partitioned Parquet dataset in data/processed

--- Step 3: DuckDB OLAP Analytics ---

📊 Carrier Reliability Rankings:
shape: (14, 6)
┌─────────┬───────────────┬───────────────┬───────────────┬────────────────┬──────────────────┐
│ carrier ┆ total_flights ┆ avg_dep_delay ┆ avg_arr_delay ┆ delay_rate_pct ┆ reliability_rank │
│ ---     ┆ ---           ┆ ---           ┆ ---           ┆ ---            ┆ ---              │
│ str     ┆ i64           ┆ f64           ┆ f64           ┆ f64            ┆ i64              │
╞═════════╪═══════════════╪═══════════════╪═══════════════╪════════════════╪══════════════════╡
│ DL      ┆ 78421         ┆ 8.12          ┆ 2.45          ┆ 14.20          ┆ 1                │
│ 9E      ┆ 18230         ┆ 9.04          ┆ 3.11          ┆ 15.10          ┆ 2                │
│ ...     ┆ ...           ┆ ...           ┆ ...           ┆ ...            ┆ ...              │
└─────────┴───────────────┴───────────────┴───────────────┴────────────────┴──────────────────┘

==================================================
✅ Pipeline Execution Complete!
==================================================

## Testing

Run the test suite to verify ingestion mocks, PyArrow storage partitions, and DuckDB analytics queries:

```bash
python -m pytest
```

## Repository Structure
flight-analytics-lakehouse/
├── data/
│   ├── raw/                # Raw downloaded BTS zip archives
│   └── processed/          # Hive-partitioned Parquet files (year=/month=)
├── src/
│   ├── analytics.py        # DuckDB engine & analytical SQL queries
│   ├── config.py           # Path management & DuckDB memory limits
│   ├── ingestion.py        # Streaming HTTP downloader
│   └── storage.py          # CSV to PyArrow/Polars Parquet converter
├── tests/
│   ├── test_analytics.py   # Unit tests for DuckDB engine
│   ├── test_ingestion.py   # Unit tests with mocked HTTP streams
│   └── test_storage.py     # Unit tests for Parquet partitioning
├── main.py                 # CLI orchestrator
├── pyproject.toml          # Editable package configuration & dependencies
└── README.md
