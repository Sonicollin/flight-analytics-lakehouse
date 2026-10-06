# Flight Analytics Lakehouse

A local analytics engineering project that ingests historical U.S. flight-performance data and live aircraft-state data, models both datasets with dbt, and exposes analytical outputs through DuckDB and Python.

The project is designed to demonstrate a small, defensible analytics engineering workflow: ingestion, validation, analytical storage, transformation, testing, and consumption.

## Architecture

The project contains two separate data flows with different grains and analytical purposes.

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
        v
       dbt
        |
        v
 stg_bts_flights
        |
        v
mart_carrier_performance
        |
        v
Python analytics
        |
        v
Carrier reliability rankings


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
      DuckDB
        |
        v
       dbt
        |
        v
stg_opensky_states
        |
        v
mart_aircraft_activity
        |
        v
Python analytics
        |
        v
Aircraft activity summary
```

BTS data represents completed commercial flight-performance records, while OpenSky provides point-in-time aircraft state vectors. Because the datasets do not share a reliable flight-level key or the same grain, they are not joined.

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
4. exposes the Parquet dataset to dbt through DuckDB and dbt
5. builds analytical models for carrier performance

### OpenSky Network

Live aircraft state vectors are retrieved from the OpenSky REST API for a geographic bounding box covering the contiguous United States.

The pipeline:

1. requests the latest OpenSky state vectors
2. converts positional API arrays into named records
3. validates records using Pydantic
4. loads validated records into DuckDB with dlt
5. stages and tests the data with dbt
6. builds a snapshot-level aircraft activity mart

## dbt Models

### `stg_bts_flights`

Stages historical BTS flight data from partitioned Parquet files.

The model standardizes the fields used for downstream analysis and creates an `is_delayed` field:

- `TRUE` when arrival delay exceeds 15 minutes
- `FALSE` when arrival delay is 15 minutes or less
- `NULL` when arrival-delay information is unavailable

### `mart_carrier_performance`

Produces one row per reporting carrier with historical performance metrics:

- `total_flights`
- `avg_dep_delay`
- `avg_arr_delay`
- `delayed_flight_pct`

### `stg_opensky_states`

Stages validated OpenSky aircraft state vectors loaded into DuckDB.

The model includes fields such as:

- `aircraft ICAO identifier`
- `snapshot timestamp`
- `latitude and longitude`
- `velocity`
- `altitude`
- `ground status`

The model grain is one aircraft observation per icao24 and snapshot timestamp.

dbt tests enforce required identifiers and composite uniqueness at that grain.

### `mart_aircraft_activity`

Produces one row per OpenSky snapshot.

Metrics include:

- `aircraft observed`
- `aircraft airborne`
- `aircraft on the ground`
- `average velocity`
- `average barometric altitude`

## Repository Structure

```text
flight-analytics-lakehouse/
├── data/
│   ├── raw/
│   └── processed/
├── dbt_project/
│   ├── models/
│   │   ├── staging/
│   │   │    ├── stg_bts_flights.sql
│   │   │    ├── stg_opensky_states.sql
│   │   └── marts/
│   │   │    ├── mart_carrier_performance.sql
│   │   │    ├── mart_aircraft_activity.sql
│   ├── dbt_project.yml
│   └── profiles.yml
├── src/
│   ├── analytics.py
│   ├── config.py
│   ├── contracts.py
│   ├── ingestion.py
│   └── storage.py
├── tests/
│   ├── test_analytics.py
│   ├── test_config.py
│   ├── test_contracts.py
│   ├── test_ingestion.py
├── main.py
├── pyproject.toml
└── README.md
```

Generated data, DuckDB files, dbt build artifacts, logs, Python caches, and other local runtime files are excluded from source control.

## Installation

Clone the repository and install the project with development dependencies:

```bash
git clone https://github.com/Sonicollin/flight-analytics-lakehouse.git
cd flight-analytics-lakehouse
pip install -e .
```

## Running the Pipeline

The main CLI allows each part of the project to be executed independently or as one end-to-end workflow.

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

This queries both dbt-built marts.

The historical branch returns carrier reliability rankings derived from `mart_carrier_performance`.

The OpenSky branch returns snapshot-level aircraft activity from `mart_aircraft_activity`.

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

## Design Decisions

### DuckDB as the analytical engine

DuckDB provides a lightweight local analytical database that can query both persisted database tables and Parquet files without requiring external infrastructure.

This keeps the project reproducible while still demonstrating warehouse-style analytical workflows.

### Data quality is explicit

Pydantic validates OpenSky records before loading, while dbt tests enforce assumptions about analytical models and model grain.

Python tests cover application behavior and pipeline components separately from dbt's data-quality tests.

## Limitations

This is a local portfolio project rather than a production deployment.

Current limitations include:

- OpenSky ingestion captures snapshots rather than maintaining a continuously running stream
- local DuckDB storage is intended for single-user analytical workloads
- historical BTS ingestion is executed by requested month rather than through a production scheduler

These constraints are intentional. The project focuses on demonstrating a coherent analytics engineering workflow.

## Example Analytical Output

```text
Carrier Reliability Rankings:
shape: (15, 6)
┌─────────┬───────────────┬───────────────┬───────────────┬────────────────────┬──────────────────┐
│ carrier ┆ total_flights ┆ avg_dep_delay ┆ avg_arr_delay ┆ delayed_flight_pct ┆ reliability_rank │
│ ---     ┆ ---           ┆ ---           ┆ ---           ┆ ---                ┆ ---              │
│ str     ┆ i64           ┆ f64           ┆ f64           ┆ f64                ┆ i64              │
╞═════════╪═══════════════╪═══════════════╪═══════════════╪════════════════════╪══════════════════╡
│ AS      ┆ 61185         ┆ 5.83          ┆ 1.7           ┆ 18.34              ┆ 1                │
│ DL      ┆ 250146        ┆ 8.16          ┆ 2.02          ┆ 15.53              ┆ 2                │
│ OH      ┆ 55097         ┆ 7.67          ┆ 2.21          ┆ 16.3               ┆ 3                │
│ YX      ┆ 83136         ┆ 6.6           ┆ 2.65          ┆ 18.63              ┆ 4                │
│ MQ      ┆ 71367         ┆ 6.78          ┆ 3.79          ┆ 18.11              ┆ 5                │
│ …       ┆ …             ┆ …             ┆ …             ┆ …                  ┆ …                │
│ NK      ┆ 51062         ┆ 13.62         ┆ 7.52          ┆ 21.88              ┆ 11               │
│ B6      ┆ 57865         ┆ 14.78         ┆ 8.12          ┆ 23.9               ┆ 12               │
│ AA      ┆ 237788        ┆ 15.26         ┆ 9.75          ┆ 21.62              ┆ 13               │
│ G4      ┆ 26010         ┆ 11.87         ┆ 9.76          ┆ 22.16              ┆ 14               │
│ F9      ┆ 45116         ┆ 16.71         ┆ 11.51         ┆ 24.69              ┆ 15               │
└─────────┴───────────────┴───────────────┴───────────────┴────────────────────┴──────────────────┘
OpenSky Aircraft Activity:
shape: (4, 6)
┌──────────────────────────┬───────────────────┬───────────────────┬────────────────────┬──────────────┬───────────────────┐
│ snapshot_timestamp       ┆ aircraft_observed ┆ aircraft_airborne ┆ aircraft_on_ground ┆ avg_velocity ┆ avg_baro_altitude │
│ ---                      ┆ ---               ┆ ---               ┆ ---                ┆ ---          ┆ ---               │
│ datetime[μs, Asia/Tokyo] ┆ i64               ┆ decimal[38,0]     ┆ decimal[38,0]      ┆ f64          ┆ f64               │
╞══════════════════════════╪═══════════════════╪═══════════════════╪════════════════════╪══════════════╪═══════════════════╡
│ 2026-10-06 13:33:48 JST  ┆ 2256              ┆ 1910              ┆ 346                ┆ 149.8        ┆ 6784.6            │
│ 2026-10-06 11:18:45 JST  ┆ 4406              ┆ 3894              ┆ 512                ┆ 154.3        ┆ 6675.74           │
│ 2026-10-06 10:27:44 JST  ┆ 5067              ┆ 4432              ┆ 635                ┆ 143.62       ┆ 6200.83           │
│ 2026-10-06 10:05:16 JST  ┆ 5307              ┆ 4680              ┆ 627                ┆ 142.23       ┆ 6074.85           │
└──────────────────────────┴───────────────────┴───────────────────┴────────────────────┴──────────────┴───────────────────┘
```