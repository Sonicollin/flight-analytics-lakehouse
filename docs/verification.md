# Verification record

Verified on 2026-09-30 using Linux, Python 3.12.14, DuckDB 1.5.6, dlt 1.30.0, dbt-core 1.12.5 and dbt-duckdb 1.11.0. Starting repository commit: `14d5076d65afe97a9bc9938cf48c64dda4c217b0`.

## Actual source run

Executed `python main.py run --year 2023 --month 1` against both real HTTP endpoints, followed by a final `python main.py build` and direct DuckDB inspection. No API fixtures were substituted in this warehouse. A second full run of the final code reused the cached BTS ZIP, replaced the month without changing its 538,837-row count, ingested a fresh 635-observation OpenSky snapshot, and again passed all five models and 40 tests. The two snapshots total 1,307 raw observations; the per-snapshot airborne/ground counts reconcile.

| Check | Observed result |
| --- | --- |
| BTS January 2023 ZIP download and CSV conversion | 538,837 rows in year=2023/month=1 Parquet |
| BTS staging rows | 538,837 |
| Carrier-month mart rows | 15 |
| Sum of carrier total flights | 538,837, matching the raw source |
| Cancelled flights | 10,295 |
| Diverted flights | 1,345 |
| Eligible arrivals | 527,197 |
| OpenSky snapshot | 2026-09-30 06:40:27 UTC |
| OpenSky valid observations | 672 |
| Observed airborne / ground aircraft | 550 / 122, reconciling to 672 |
| Observations with position | 672 |
| Mean observed airborne ground speed | 182.89 m/s |
| dbt build | 5 models and 40 data tests passed; no warnings, errors or skipped nodes |

Sample BTS results from the actual month:

| Carrier | Reported rows | Eligible arrivals | Mean arrival delay (min) | Delay rate | Cancellation rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| YX | 24,476 | 24,049 | -1.62 | 16.44% | 1.58% |
| OH | 15,456 | 15,165 | 0.56 | 14.64% | 1.62% |
| AS | 19,801 | 19,421 | 3.27 | 21.17% | 1.41% |

These are descriptive metrics for the ingested month and observed snapshot, not guarantees about airline quality or complete US aircraft activity.

## Deterministic verification

The full pytest suite passes: **20 tests passed**. Tests use isolated temporary storage and no network. The integration tests execute actual dlt loads and `dbt build`, rather than mocking those libraries. The synthetic `python main.py demo` also builds five models and passes 40 data tests in a separate database.

Checked the exactly-15-minute boundary, cancelled/diverted/unknown-delay exclusions, negative delays, repeated snapshot merge, monthly replacement and preservation of other months, interrupted download behavior, malformed payloads, retained rejected records, empty-source builds, and loading observations after empty-source initialization.

## Scope and limits

The actual workflow was verified for one historical month and one anonymous OpenSky snapshot. OAuth token authentication/refresh, Windows/macOS execution, multi-writer behavior, crash recovery, multi-year scale and bounded peak memory were not verified. Monthly BTS CSV conversion remains eager. The documented pinned dependency installation was checked in a fresh Python 3.12 environment: `pip check` found no conflicts and all 20 pytest tests passed there. Two sequential demo runs and repeated builds also passed. An earlier throwaway demo database encountered a WAL recovery error during development; it was preserved for diagnosis, and only synthetic demo storage was recreated. Automatic recovery from a damaged database is not implemented or verified.

GitHub Actions is supplied for repeatable offline testing, but a hosted Actions run has not been observed here. Generated DuckDB databases, source downloads, logs and dbt target outputs are intentionally excluded from source control.
