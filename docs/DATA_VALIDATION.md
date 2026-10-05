# Data Validation

## Result

The official Kaggle Rossmann Store Sales snapshot was validated on 2026-10-05 with:

```powershell
python scripts/validate_data.py --report reports/validation/rossmann.json
```

Result: **PASS — 0 errors, 4 warnings, and 12 informational findings.** The validator confirmed
that raw-file SHA-256 hashes were unchanged before and after reading. The generated JSON report is
ignored because it is reproducible; this document is the concise version-controlled record.

This Phase 1 source-quality inspection covered the full labeled history through 2015-07-31,
including descriptive Sales/Customers summaries for dates later reserved for final forecasting
evaluation. It produced no model or holdout forecasting score. These historical inspections are
disclosed in [EDA Findings](EDA_FINDINGS.md#historical-source-exposure-and-later-modeling); later
modeling must follow the [Phase 3 firewall](FEATURE_CONTRACT.md#final-holdout-firewall), not treat
full-source summaries as training references or claim the final-period labels were never read.

## Source Snapshot

| File | Rows | Columns | Bytes | SHA-256 |
|---|---:|---:|---:|---|
| `train.csv` | 1,017,209 | 9 | 38,057,952 | `f6e4597c142d7d909a13d53b68a8e85c00b9a4c7b5ff40adbb37d6829cc1f4cc` |
| `test.csv` | 41,088 | 8 | 1,427,425 | `e75f79972de046d88c2fd55da19df627f5ca654aaf418090d4d30c60ea7dbe26` |
| `store.csv` | 1,115 | 10 | 45,010 | `f56bd124a2849489e6bbb5c000f5fc9640204355e316475c918ae4d089afb344` |
| `sample_submission.csv` | 41,088 | 2 | 317,611 | `592d892eb07072ddfa3773f13c4822ce5d01981243134c8d512ae30f016805db` |

The user confirmed that these files were downloaded manually from the official Kaggle competition.
The earlier Kaggle API HTTP 403 response is not a validation finding and is no longer a blocker.

## Schema, Keys, and Coverage

- `train.csv` columns: `Store`, `DayOfWeek`, `Date`, `Sales`, `Customers`, `Open`, `Promo`,
  `StateHoliday`, `SchoolHoliday`.
- `test.csv` columns: `Id`, `Store`, `DayOfWeek`, `Date`, `Open`, `Promo`, `StateHoliday`,
  `SchoolHoliday`; it contains neither `Sales` nor `Customers`.
- `store.csv` columns: `Store`, `StoreType`, `Assortment`, `CompetitionDistance`,
  `CompetitionOpenSinceMonth`, `CompetitionOpenSinceYear`, `Promo2`, `Promo2SinceWeek`,
  `Promo2SinceYear`, `PromoInterval`.
- `sample_submission.csv` columns: `Id`, `Sales`; its 41,088 rows and identifier set match test.
- Train covers 1,115 stores from 2013-01-01 through 2015-07-31. Test covers 856 stores from
  2015-08-01 through 2015-09-17.
- Both train and test have zero duplicate Store × Date keys. Store metadata has 1,115 unique Store
  keys.
- Train and test have zero unmatched Store keys. Many-to-one joins preserve 1,017,209 train rows
  and 41,088 test rows without multiplying keys.

## Missingness and Domains

- Train has no missing values in any field.
- Test has 11 missing `Open` values (0.026772%); all belong to Store 622. No Phase 1 fill was made.
- Store metadata has 3 missing `CompetitionDistance` values (0.269058%); 354 jointly missing
  competition-open month/year pairs (31.748879%); and 544 missing values in each Promo2 detail
  field (48.789238%).
- The 544 Promo2-detail missing rows are exactly the 544 stores with `Promo2 = 0`; none of the 571
  participating stores is missing a Promo2 detail. This is structural missingness.
- Competition-open month and year are jointly missing for 354 stores with no partial pairs. The
  source does not establish why, so Phase 1 does not label the cause.
- Train domains are `Open` {0, 1}, `Promo` {0, 1}, `StateHoliday` {0, a, b, c}, and
  `SchoolHoliday` {0, 1}. Test has the same binary domains and `StateHoliday` {0, a}.
- Store domains are `StoreType` {a, b, c, d}, `Assortment` {a, b, c}, `Promo2` {0, 1}, and
  `PromoInterval` {`Jan,Apr,Jul,Oct`, `Feb,May,Aug,Nov`, `Mar,Jun,Sept,Dec`} when present.

## Target and Business-Rule Checks

- `Sales` is finite and non-negative, ranging from 0 to 41,551; median is 5,744 and the 99th
  percentile is 17,160. High positive observations remain untouched as review candidates.
- `Customers` is finite and non-negative, ranging from 0 to 7,388; median is 609 and the 99th
  percentile is 2,267.
- There are 172,871 zero-sales rows and 172,869 zero-customer rows.
- No `Open = 0` row has positive `Sales` or positive `Customers`.
- There are 54 `Open = 1, Sales = 0` rows across 41 stores; 52 have zero customers and 2 have
  positive customers. These records remain unchanged.
- The maximum observed Sales value is 41,551 at Store 909 on 2015-06-22. It is non-negative and
  otherwise schema-valid, so Phase 1 does not remove or cap it.
- `Customers` is historical-only and must not be used as an actual future production feature.

## Warning Disposition

| Validator warning | Evidence | Classification and disposition |
|---|---|---|
| `DATE_GAPS` | 180 stores each omit the same 184 calendar days from 2014-07-01 through 2014-12-31; 33,120 missing store-days total | **D — later modelling consideration.** Preserve the source and account for coverage during Phase 2 time-series preparation. |
| `OPEN_WITH_ZERO_SALES` | 54 rows across 41 stores | **D — later modelling consideration.** Retain and investigate context; do not rewrite source values. |
| `MISSING_FUTURE_OPEN` | 11 test rows, all Store 622 | **D — later modelling consideration.** Define a documented policy in Phase 2; Phase 1 performs no imputation. |
| `UNUSED_STORE_METADATA` | Test uses 856 of 1,115 metadata stores; all test stores still match exactly one metadata row | **A — expected dataset characteristic.** No join-integrity failure exists. |

No warning was suppressed, and no validator implementation problem was found.

## Phase 1 Validation Scope and Output Policy

Validation is descriptive data-quality inspection only. It creates no lags, rolling features,
splits, shuffled rows, models, inventory logic, or synthetic operational data. The JSON report at
`reports/validation/rossmann.json` is small but fully reproducible and remains ignored under the
project's generated-report policy. Verified facts are maintained here and in the Data Dictionary.

## Phase 2 Prepared Data and Diagnostic Outputs

The Phase 2 preparation command verified the four source SHA-256 values above both before and
after processing. It wrote ignored Parquet outputs with PyArrow 24.0.0 on Python 3.14.5 / pandas
3.0.6:

| Output | Rows | Columns | Notes |
|---|---:|---:|---|
| `data/interim/train.parquet` | 1,017,209 | 18 | Historical source rows joined many-to-one to store metadata; includes Sales and Customers |
| `data/interim/test.parquet` | 41,088 | 17 | Future covariates joined many-to-one to metadata; no Sales or Customers column |
| `data/interim/test_open_resolution.parquet` | 41,088 | 12 | Separate audited Open view; preserves source Open and records an uncertain historical-context candidate separately |

The historical base retained every source row, including 172,817 closed rows and all 54 open/zero-
Sales rows. No rows were inserted into the shared 184-day gap. Source nulls remain unchanged,
including the 11 test `Open` values in `test.parquet`. The resolution audit uses only earlier
historical `Open` and the exact known `DayOfWeek`, `Promo`, `StateHoliday`, and `SchoolHoliday`
context; it never reads future Sales or Customers. Full row schemas, dependency versions, output
hashes, and source hashes are recorded in the ignored `data/interim/preparation_manifest.json`.

Descriptive EDA ran from the prepared Parquet tables and wrote its schema, summary, tables, and 14
figures under ignored `reports/eda/`. See [Phase 2 EDA findings](EDA_FINDINGS.md) for the concise,
version-controlled interpretation and policy dispositions.
