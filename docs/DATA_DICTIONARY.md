# Data Dictionary

Real-field observations below were measured from the official Kaggle Rossmann Store Sales snapshot
validated on 2026-10-05. Category codes are recorded as observed without inventing unsupported
business meanings. Phase 3 engineered predictors are implemented separately from source fields and
documented in Section B and the [Feature Contract](FEATURE_CONTRACT.md). Phase 2 diagnostic
derivations remain audit-only and are not model inputs. Synthetic variables remain simulated and
are not Rossmann operational data.

## A. Real Rossmann Variables

| Name | Source file(s) | Meaning / unit | Observed type | Observed values or range | Missingness | Forecast-time availability and notes |
|---|---|---|---|---|---|---|
| `Id` | `test.csv`, `sample_submission.csv` | Competition row identifier | `int64` | 1–41,088; unique in both files | 0 | Supplied for future rows; test and submission identifier sets match |
| `Store` | `train.csv`, `test.csv`, `store.csv` | Store identifier | `int64` | 1–1,115; 1,115 train/metadata stores and 856 test stores | 0 | Primary unit key with `Date`; supplied for future rows |
| `DayOfWeek` | `train.csv`, `test.csv` | Source-provided weekday code | `int64` | 1–7 | 0 | Supplied for future rows; code meanings are not inferred here |
| `Date` | `train.csv`, `test.csv` | Calendar day | parsed date from source string | Train: 2013-01-01–2015-07-31; test: 2015-08-01–2015-09-17 | 0 | Primary unit key with `Store`; future-known |
| `Sales` | `train.csv` | Daily store sales turnover; monetary value | `int64` | 0–41,551 | 0 | Historical target only; not a physical-unit quantity |
| `Customers` | `train.csv` | Customers observed for a store-day | `int64` | 0–7,388 | 0 | Historical observation only; future actual values must not be production features |
| `Open` | `train.csv`, `test.csv` | Store-open indicator | train `int64`; test `float64` because of nulls | {0, 1} when present | Train: 0; test: 11 (0.026772%) | Source field is preserved in prepared data; test unknowns have a separate auditable, uncertain historical-context candidate in `test_open_resolution.parquet` |
| `Promo` | `train.csv`, `test.csv` | Store-promotion indicator | `int64` | {0, 1} | 0 | Future-known when the promotion is planned |
| `StateHoliday` | `train.csv`, `test.csv` | State-holiday code | string | Train: {0, a, b, c}; test: {0, a} | 0 | Future-known calendar field; category meanings are not inferred from values alone |
| `SchoolHoliday` | `train.csv`, `test.csv` | School-holiday indicator | `int64` | {0, 1} | 0 | Future-known calendar field |
| `StoreType` | `store.csv` | Store type code | string | {a, b, c, d} | 0 | Static store attribute; category meanings are not inferred from values alone |
| `Assortment` | `store.csv` | Assortment code | string | {a, b, c} | 0 | Static store attribute; category meanings are not inferred from values alone |
| `CompetitionDistance` | `store.csv` | Source competition-distance measure; source unit not asserted here | `float64` | 20–75,860 when present | 3 (0.269058%) | Static metadata; missing-value handling is deferred |
| `CompetitionOpenSinceMonth` | `store.csv` | Calendar month competition began operating | `float64` because of nulls | 1–12 when present | 354 (31.748879%) | Static metadata; month/year are jointly missing for all 354 rows |
| `CompetitionOpenSinceYear` | `store.csv` | Calendar year competition began operating | `float64` because of nulls | 1900–2015 when present | 354 (31.748879%) | Static metadata; the source does not establish the missingness cause |
| `Promo2` | `store.csv` | Continuing-promotion participation indicator | `int64` | {0, 1} | 0 | Static, schedule-related metadata |
| `Promo2SinceWeek` | `store.csv` | Calendar week Promo2 participation began | `float64` because of nulls | 1–50 when present | 544 (48.789238%) | Missing exactly for all `Promo2 = 0` stores; structurally absent for non-participants |
| `Promo2SinceYear` | `store.csv` | Calendar year Promo2 participation began | `float64` because of nulls | 2009–2015 when present | 544 (48.789238%) | Missing exactly for all `Promo2 = 0` stores; structurally absent for non-participants |
| `PromoInterval` | `store.csv` | Months when Promo2 is active | string with nulls | `Jan,Apr,Jul,Oct`; `Feb,May,Aug,Nov`; `Mar,Jun,Sept,Dec` | 544 (48.789238%) | Missing exactly for all `Promo2 = 0` stores; schedule is future-known when present |

## B. Derived / Engineered Features

Phase 3 now implements a frozen 29-predictor schema, `phase-3-v1`. It includes unchanged `Store`
as both a key and a categorical-source predictor; calendar, holiday, promotion, store, and
competition features; exact-date Sales lags; and complete calendar-window Sales statistics. `Date`
is key-only. The detailed per-feature source, derivation, dtype, availability, null, leakage, and
train/inference rules are in the [Phase 3 Feature Contract](FEATURE_CONTRACT.md).

Dynamic features use exact same-Store Sales dates at d-1/d-7/d-14/d-28 and exact prior calendar
windows d-n through d-1 for n=7/14/28. Windows require every exact date and use sample standard
deviation (`ddof=1`); current-target Sales, absent dates, partial windows, and gap filling are
prohibited. Historical training rows use only Sales strictly before their target. Recursive
inference requires actual history censored at the declared origin and accepts optional earlier
predictions. No model-specific encoding, scaling, same-weekday features, or imputation is included.

Competition opening status and age use month-level arithmetic, not an asserted day: known
pre-opening is False/0, opening month is True/0, later age is completed calendar-month offsets,
and paired missing source metadata stays null/null. Promo2 nonparticipants are inactive; valid
participant schedules use the Monday of the ISO start week, recurring interval months, and target
Date. Incomplete/invalid schedules stay null and are audited. Availability/null diagnostics are
audit-only, not predictors.

The final 28 labeled calendar days remain behind the holdout firewall: feature coverage diagnostics
use development rows only; holdout contact is limited to mechanical schema, key, dtype,
determinism, and non-mutation checks. No forecast metrics or holdout-guided feature choices are
made in Phase 3.

## C. Phase 2 Diagnostic Derivations

These audit-only fields are stored separately from the source-faithful prepared `test.parquet`.
They are not forecast features, and a candidate status is not guaranteed ground truth.

| Name | Source | Meaning | Rule | Availability / caution |
|---|---|---|---|---|
| `Open_resolved` | Prepared test `Open`; historical train `Open`; exact known covariates | Source Open when known; otherwise a candidate status when supported | For the same Store and exact `DayOfWeek`, `Promo`, `StateHoliday`, and `SchoolHoliday`, require at least 30 prior historical rows and unanimous observed `Open`; otherwise leave missing | Candidate is marked uncertain and kept in separate `test_open_resolution.parquet`; no future Sales or Customers are used |
| `Open_resolution_method` | Same as above | Distinguishes source status, unanimous historical context, and unresolved status | Deterministic label emitted by the audited rule | Phase 3 keeps this candidate audit-only; it never overwrites source Open or establishes eligibility/evaluation truth |
| `historical_match_rows` | Historical train `Open` and known covariates | Number of earlier matching historical records with known Open | Count exact-context prior rows | Evidence size, not a probability guarantee |
| `historical_open_rate` | Historical train `Open` and known covariates | Historical fraction with Open=1 in the matching context | Mean of known matching Open statuses | Descriptive evidence only |
| `resolution_uncertain` | Derived audit metadata | Flags a candidate or unresolved missing source status as uncertain | `True` for missing source statuses; `False` when the source status was present | Does not alter source `Open` |

## D. Synthetic Operational Variables

All random synthetic generation will use a documented fixed seed for reproducibility.

| Name | Category | Source | Meaning | Unit | Known Range | Generation / Derivation Rule | Availability at Forecast Time | Notes |
|---|---|---|---|---|---|---|---|---|
| `SupplierLeadTime` | Supply-chain input | Synthetic / simulated | Store-specific replenishment lead time | Days | Approximately 2–7 days in proposed scenarios | Generated from documented store-level assumptions with a fixed seed | Yes, as simulated input | Not Rossmann data |
| `StockOnHandValue` | Inventory input | Synthetic / simulated | Current inventory monetary value | Monetary value | $\ge 0$ | Based on recent demand and inventory coverage | Yes, as simulated input | Not physical stock units and not Rossmann data |
| `ServiceLevelTarget` | Policy input | Synthetic / simulated | Target product availability | Percent | 90%–98%; 95% base scenario | Assigned by documented scenario | Yes, as simulated input | Not Rossmann data |
| `HoldingCostRate` | Cost input | Synthetic / simulated | Inventory holding-cost assumption | Percent of inventory value | TBD | Generated from documented business assumptions | Yes, as simulated input | Not Rossmann data |
| `StockoutPenalty` | Cost input | Synthetic / simulated | Lost-sales or service-cost assumption | Monetary value | TBD | Generated from documented business assumptions | Yes, as simulated input | Not Rossmann data |
| `AverageUnitValue` | Conversion input | Synthetic / simulated | Average value used to illustrate equivalent units | Monetary value per equivalent unit | TBD | Store-level simulated variable | Yes, as simulated input | Does not identify real products or SKUs |
| `DiscountDepth` | Promotion input | Synthetic / simulated | Simulated promotion intensity | Proportion | $0 \le x < 1$ | Zero when `Promo = 0`; positive when `Promo = 1` | Yes, as simulated input | Not Rossmann data |
| `InventoryCoverageDays` | Inventory-policy input | Synthetic / simulated | Initial inventory coverage assumption | Days | TBD | Generated within a documented reasonable business range | Yes, as simulated input | Not Rossmann data |

## Validation Notes

The real-variable observations are tied to the validated 2026-10-05 source hashes recorded in
[Data Acquisition](DATA_ACQUISITION.md) and [Data Validation](DATA_VALIDATION.md). Derived features
in Section B are Phase 3 outputs, not source variables. Synthetic variables remain proposed
simulation inputs and must never be presented as observed Rossmann data.
