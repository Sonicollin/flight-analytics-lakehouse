# Flight Analytics Lakehouse

A local analytics engineering project that ingests historical U.S. flight-performance data and live aircraft-state data, models both datasets with dbt, and exposes analytical outputs through DuckDB and Python.

The project is designed to demonstrate a small, defensible analytics engineering workflow: ingestion, validation, analytical storage, transformation, testing, and consumption.

## Architecture

The project contains two independent data flows with different grains and analytical purposes.

```text
Historical BTS flight data
        |
        v
Python ingestion
        |
        v
Polars / PyArrow
        |
        v
Hive-partitioned Parquet
        |
        +-------------------+
                            |
                            v
                          dbt
                            |
                            v
                  stg_bts_flights
                            |
                            v
               mart_carrier_performance


Live OpenSky aircraft states
        |
        v
REST API
        |
        v
Pydantic validation
        |
        v
dlt
        |
        v
DuckDB raw_opensky_states
        |
        v
      dbt
        |
        v
stg_opensky_states
```

The BTS and OpenSky datasets are intentionally not joined.

BTS data represents completed commercial flight-performance records, while OpenSky provides point-in-time aircraft state vectors. Because the datasets do not share a reliable flight-level key or the same grain, forcing them into a direct join would create an artificial relationship.

## Tech Stack

- Python
- SQL
- dbt
- DuckDB
- dlt
- Pydantic
- Polars
- PyArrow
- Parquet
- httpx
- pytest
- Git

## Data Sources

### Bureau of Transportation Statistics

Historical U.S. airline on-time performance data is downloaded from the Bureau of Transportation Statistics.

The pipeline:

1. downloads a monthly ZIP archive
2. processes the source data with Python
3. writes Hive-partitioned Parquet files
4. exposes the data to dbt through DuckDB

The BTS dataset is used to build carrier-level analytical metrics such as:

- total flights
- average departure delay
- average arrival delay
- percentage of flights arriving more than 15 minutes late

### OpenSky Network

Live aircraft state vectors are retrieved from the OpenSky REST API for a geographic bounding box covering the contiguous United States.

The pipeline:

1. requests the latest OpenSky state vectors
2. converts positional API arrays into named records
3. validates records using Pydantic
4. loads validated records into DuckDB with dlt
5. stages the data with dbt

The grain of the staging model is one aircraft observation per `icao24` and snapshot timestamp.

## dbt Models

### `stg_bts_flights`

Stages historical BTS flight data from partitioned Parquet files.

The model standardizes the fields used for downstream analysis and creates an `is_delayed` field:

- `TRUE` when arrival delay exceeds 15 minutes
- `FALSE` when arrival delay is 15 minutes or less
- `NULL` when arrival-delay information is unavailable

### `stg_opensky_states`

Stages validated OpenSky aircraft state vectors loaded into DuckDB.

The model preserves aircraft identifiers, snapshot timestamps, position, velocity, and other state-vector attributes.

Data tests verify required identifiers and the expected observation grain.

### `mart_carrier_performance`

Produces one row per reporting carrier with historical performance metrics:

- `total_flights`
- `avg_dep_delay`
- `avg_arr_delay`
- `delayed_flight_pct`

The delay percentage is calculated only for records with known arrival-delay status.

dbt tests enforce the carrier-level grain using `not_null` and `unique` tests on the carrier field.

## Repository Structure

```text
flight-analytics-lakehouse/
├── data/
│   ├── raw/
│   └── processed/
├── dbt_project/
│   ├── models/
│   │   ├── staging/
│   │   └── marts/
│   ├── dbt_project.yml
│   └── profiles.yml
├── src/
│   ├── analytics.py
│   ├── config.py
│   ├── contracts.py
│   ├── ingestion.py
│   └── storage.py
├── tests/
├── main.py
├── pyproject.toml
└── README.md
```

Generated data, DuckDB files, dbt build artifacts, logs, Python caches, and other local runtime files are excluded from source control.

## Installation

Python 3.11+ is recommended.

Clone the repository and install the project with development dependencies:

```bash
git clone <repository-url>
cd flight-analytics-lakehouse
pip install -e ".[dev]"
```

The project uses `pyproject.toml` as its dependency definition.

## Running the Pipeline

The main CLI allows each part of the project to be executed independently.

### Historical BTS ingestion

```bash
python main.py --run-parquet --year 2023 --month 1
```

This downloads the requested BTS archive and converts it into partitioned Parquet files.

Use `--force` to re-download an archive that already exists locally:

```bash
python main.py --run-parquet --year 2023 --month 1 --force
```

### OpenSky ingestion

```bash
python main.py --run-opensky
```

This retrieves a live aircraft-state snapshot, validates the records, and loads them into DuckDB using dlt.

### dbt models and tests

```bash
python main.py --run-dbt
```

The Python CLI supplies dbt with the same DuckDB and Parquet paths used by the rest of the application.

The command executes `dbt build`, which builds models and runs their associated data tests.

### Analytical output

```bash
python main.py --run-analytics
```

This queries the dbt-built `mart_carrier_performance` model from DuckDB and returns carrier reliability rankings.

### Full end-to-end pipeline

```bash
python main.py --run-all --year 2023 --month 1
```

This executes:

```text
BTS ingestion
    ->
OpenSky ingestion
    ->
dbt build and tests
    ->
analytical query
```

## Running Tests

Run the Python test suite with:

```bash
pytest
```

The tests cover key parts of the ingestion and storage workflow, including:

- BTS download behavior
- mocked HTTP responses
- OpenSky record normalization
- Pydantic validation
- dlt ingestion behavior
- partitioned Parquet storage
- DuckDB analytical queries

dbt model and data tests are executed through:

```bash
python main.py --run-dbt
```

or directly from the dbt project:

```bash
dbt build
```

## Configuration

Application paths are defined relative to the repository through the Python configuration layer.

dbt receives the DuckDB database path through the `LAKEHOUSE_DB_PATH` environment variable when executed from `main.py`.

The BTS Parquet source path is defined as a dbt variable and can be overridden when necessary.

This avoids machine-specific absolute paths and allows the project to be cloned and executed on another system without editing local filesystem paths.

## Design Decisions

### Separate BTS and OpenSky models

The two datasets are intentionally modeled independently because they represent different entities and grains.

A direct join would require an assumed flight-level relationship that the available source data does not reliably provide.

### Parquet for historical data

Historical BTS data is stored as Hive-partitioned Parquet rather than loaded entirely into a database table.

This provides a compact analytical format and allows DuckDB to query the files directly.

### DuckDB as the analytical engine

DuckDB provides a lightweight local analytical database that can query both persisted database tables and Parquet files without requiring external infrastructure.

This keeps the project reproducible while still demonstrating warehouse-style analytical workflows.

### dbt owns analytical transformations

Carrier-performance business logic is modeled in dbt rather than duplicated inside Python.

Python is responsible primarily for ingestion, validation, storage, orchestration, and consuming analytical outputs.

This gives metric definitions a single source of truth.

### Data quality is explicit

Pydantic validates OpenSky records before loading, while dbt tests enforce assumptions about analytical models and model grain.

Python tests cover application behavior and pipeline components separately from dbt's data-quality tests.

## Limitations

This is a local portfolio project rather than a production deployment.

Current limitations include:

- OpenSky ingestion captures snapshots rather than maintaining a continuously running stream
- local DuckDB storage is intended for single-user analytical workloads
- historical BTS ingestion is executed by requested month rather than through a production scheduler
- no attempt is made to create an artificial flight-level relationship between BTS and OpenSky
- operational monitoring and alerting are outside the current scope

These constraints are intentional. The project focuses on demonstrating a coherent analytics engineering workflow without introducing infrastructure that is unnecessary for the problem being solved.

## Example Analytical Output

The carrier-performance mart can be queried directly through DuckDB or through the project's Python analytics layer.

Example fields include:

```text
carrier
total_flights
avg_dep_delay
avg_arr_delay
delayed_flight_pct
reliability_rank
```

The ranking output orders carriers by average arrival delay while preserving the dbt mart as the source of the underlying carrier-performance metrics.