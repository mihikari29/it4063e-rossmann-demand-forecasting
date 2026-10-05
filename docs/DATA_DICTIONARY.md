# Data Dictionary

Real-field observations below were measured from the official Kaggle Rossmann Store Sales snapshot
validated on 2026-10-05. Category codes are recorded as observed without inventing unsupported
business meanings. Derived features remain planned and unimplemented; synthetic variables remain
simulated and are not Rossmann operational data.

## A. Real Rossmann Variables

| Name | Source file(s) | Meaning / unit | Observed type | Observed values or range | Missingness | Forecast-time availability and notes |
|---|---|---|---|---|---|---|
| `Id` | `test.csv`, `sample_submission.csv` | Competition row identifier | `int64` | 1–41,088; unique in both files | 0 | Supplied for future rows; test and submission identifier sets match |
| `Store` | `train.csv`, `test.csv`, `store.csv` | Store identifier | `int64` | 1–1,115; 1,115 train/metadata stores and 856 test stores | 0 | Primary unit key with `Date`; supplied for future rows |
| `DayOfWeek` | `train.csv`, `test.csv` | Source-provided weekday code | `int64` | 1–7 | 0 | Supplied for future rows; code meanings are not inferred here |
| `Date` | `train.csv`, `test.csv` | Calendar day | parsed date from source string | Train: 2013-01-01–2015-07-31; test: 2015-08-01–2015-09-17 | 0 | Primary unit key with `Store`; future-known |
| `Sales` | `train.csv` | Daily store sales turnover; monetary value | `int64` | 0–41,551 | 0 | Historical target only; not a physical-unit quantity |
| `Customers` | `train.csv` | Customers observed for a store-day | `int64` | 0–7,388 | 0 | Historical observation only; future actual values must not be production features |
| `Open` | `train.csv`, `test.csv` | Store-open indicator | train `int64`; test `float64` because of nulls | {0, 1} when present | Train: 0; test: 11 (0.026772%) | Supplied for future rows but incomplete in test; Phase 2 must document a policy rather than silently fill it |
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

| Name | Category | Source | Meaning | Unit | Known Range | Generation / Derivation Rule | Availability at Forecast Time | Notes |
|---|---|---|---|---|---|---|---|---|
| `day_of_week` | Calendar feature | Derived | Day of week for `Date` | Calendar category | TBD | Derived from `Date` | Yes | Future-known |
| `week_of_year` | Calendar feature | Derived | Week number for `Date` | Calendar week | TBD | Derived from `Date` | Yes | Future-known |
| `month` | Calendar feature | Derived | Month for `Date` | Calendar month | TBD | Derived from `Date` | Yes | Future-known |
| `quarter` | Calendar feature | Derived | Calendar quarter for `Date` | Calendar quarter | TBD | Derived from `Date` | Yes | Future-known |
| `year` | Calendar feature | Derived | Calendar year for `Date` | Calendar year | TBD | Derived from `Date` | Yes | Future-known |
| `is_weekend` | Calendar feature | Derived | Weekend indicator | Binary indicator | TBD | Derived from `Date` | Yes | Exact weekend definition to be documented |
| `is_month_start` | Calendar feature | Derived | Month-start indicator | Binary indicator | TBD | Derived from `Date` | Yes | Future-known |
| `is_month_end` | Calendar feature | Derived | Month-end indicator | Binary indicator | TBD | Derived from `Date` | Yes | Future-known |
| `CompetitionOpenDate` | Competition feature | Derived | Constructed competition opening date | Calendar date | TBD | Derived from competition opening month and year | Yes | Missing-value rules are TBD |
| `CompetitionAge` | Competition feature | Derived | Time since the competition opened | TBD | TBD | `Date - CompetitionOpenDate` | Yes | Unit and treatment before opening are TBD |
| `IsPromo2Active` | Promotion feature | Derived | Whether Promo2 applies on the date | Binary indicator | TBD | Derived from `Promo2`, its start, interval, and `Date` | Yes | Logic must use only known schedule information |
| `Sales_lag_1` | Lag feature | Derived | Sales one day earlier | Monetary value | TBD | Historical `Sales` at $t-1$ | Yes, from history | Must be forecast-origin-safe |
| `Sales_lag_7` | Lag feature | Derived | Sales seven days earlier | Monetary value | TBD | Historical `Sales` at $t-7$ | Yes, from history | Seasonal Naive uses this lag |
| `Sales_lag_14` | Lag feature | Derived | Sales fourteen days earlier | Monetary value | TBD | Historical `Sales` at $t-14$ | Yes, from history | Must be forecast-origin-safe |
| `Sales_lag_28` | Lag feature | Derived | Sales twenty-eight days earlier | Monetary value | TBD | Historical `Sales` at $t-28$ | Yes, from history | Must be forecast-origin-safe |
| `MA_7` | Rolling feature | Derived | Seven-day rolling mean of historical sales | Monetary value | TBD | Historical-only rolling calculation | Yes, from history | Window alignment must prevent leakage |
| `MA_14` | Rolling feature | Derived | Fourteen-day rolling mean of historical sales | Monetary value | TBD | Historical-only rolling calculation | Yes, from history | Window alignment must prevent leakage |
| `MA_28` | Rolling feature | Derived | Twenty-eight-day rolling mean of historical sales | Monetary value | TBD | Historical-only rolling calculation | Yes, from history | Window alignment must prevent leakage |
| `STD_7` | Rolling feature | Derived | Seven-day rolling standard deviation of historical sales | Monetary value | TBD | Historical-only rolling calculation | Yes, from history | Window alignment must prevent leakage |
| `STD_14` | Rolling feature | Derived | Fourteen-day rolling standard deviation of historical sales | Monetary value | TBD | Historical-only rolling calculation | Yes, from history | Window alignment must prevent leakage |
| `STD_28` | Rolling feature | Derived | Twenty-eight-day rolling standard deviation of historical sales | Monetary value | TBD | Historical-only rolling calculation | Yes, from history | Window alignment must prevent leakage |
| Same-weekday statistics | Rolling feature | Derived | Historical statistics for matching weekdays | Monetary value | TBD | Historical same-weekday observations only | Yes, from history | Exact windows and names are TBD |

## C. Synthetic Operational Variables

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
listed above are definitions for later phases, not implemented Phase 1 outputs. Synthetic variables
remain proposed simulation inputs and must never be presented as observed Rossmann data.
