# Data Validation

## Current Status

**Blocked on real-data acquisition.** The validator and constructed-fixture tests are complete, but
the official files were unavailable after Kaggle returned HTTP 403 Forbidden on 2026-10-05.
Therefore no real row count, header, date range, missingness rate, category, numerical range,
checksum, or anomaly count is claimed here. Those facts remain `TBD` in the Data Dictionary.

## Command

```powershell
python scripts/validate_data.py --report reports/validation/rossmann.json
```

The command exits 0 only when there are no `ERROR` findings. Warnings identify source conditions
that need a documented later rule without altering raw data. Generated JSON reports are ignored by
Git and contain aggregates rather than raw rows.

## Implemented Checks

- all four files exist, are non-empty and parse as CSV;
- file byte sizes, SHA-256 checksums, row counts, headers, and parsed dtypes;
- minimum schemas and unexpected columns;
- strict dates, date ranges, per-store order, and calendar gaps;
- unique Store x Date keys and unique store metadata keys;
- many-to-one store joins, unmatched stores, unused metadata, and preserved row counts;
- numeric, finite, non-negative `Sales` and `Customers` values;
- binary `Open`, `Promo`, `SchoolHoliday`, and `Promo2` domains;
- category profiles and metadata month, week, and year ranges;
- null counts and percentages, competition date pairing, and Promo2 conditional missingness;
- closed/open store cross-tabs against zero and positive Sales and Customers;
- sample-submission row count and identifier consistency with test data;
- numeric quantiles and extremes for review without removing or capping observations;
- before/after checksums proving that validation leaves raw inputs unchanged.

`Customers` is explicitly reported as historical-only and unavailable as a future production
feature. This phase creates no lags, rolling features, splits, shuffled rows, models, inventory
logic, or synthetic operational data.

## Fixture Verification

The constructed test suite uses temporary synthetic rows written only by the tests. It covers valid
inputs, missing files and columns, unexpected columns, duplicate keys, invalid joins and dates,
invalid binary values, negative and non-finite measures, closed-store inconsistencies, conditional
Promo2 missingness, checksum preservation, portable paths, CLI exit behavior, and JSON output.

Result on Python 3.14.5 with pytest 9.1.1: **12 passed**. Real-data validation must still run after
Kaggle access is restored before Phase 1 can be completed.
