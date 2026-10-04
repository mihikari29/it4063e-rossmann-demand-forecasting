# Initial Data Dictionary

This framework contains only variables named or defined in the [project proposal](proposal.md). Types, observed ranges, missingness, and source-specific coding remain **TBD** until the actual Rossmann files are validated. Synthetic variables are simulated and are not Rossmann operational data.

## A. Real Rossmann Fields

| Name | Category | Source | Meaning | Unit | Known Range | Generation / Derivation Rule | Availability at Forecast Time | Notes |
|---|---|---|---|---|---|---|---|---|
| `Store` | Identifier | Rossmann | Store identifier | Store ID | TBD | Provided | Yes | Primary unit key with `Date` |
| `Date` | Time key | Rossmann | Observation date | Calendar day | TBD | Provided | Yes | Primary unit key with `Store` |
| `Sales` | Target | Rossmann | Daily store sales turnover | Monetary value | TBD | Provided | Historical observations only | Not a physical unit quantity |
| `Customers` | Observed covariate | Rossmann | Customers observed for a store-day | Customers | TBD | Provided | No for future dates | Must not be used as a production forecasting feature |
| `Open` | Operational status | Rossmann | Whether the store is open | Binary indicator | 0 or 1 | Provided | TBD | Forecast is set to zero when `Open = 0`; primary metrics use `Open = 1` |
| `Promo` | Promotion | Rossmann | Whether a store promotion is active | Binary indicator | 0 or 1 | Provided | Yes when the promotion is planned | Future-known planned promotion information may be used |
| `StateHoliday` | Calendar | Rossmann | State-holiday status | TBD | TBD | Provided | Yes | Coding must be validated from source data |
| `SchoolHoliday` | Calendar | Rossmann | School-holiday status | TBD | TBD | Provided | Yes | Coding must be validated from source data |
| `StoreType` | Store attribute | Rossmann | Store format/type | TBD | TBD | Provided in `store.csv` | Yes | Category definitions require source validation |
| `Assortment` | Store attribute | Rossmann | Store assortment classification | TBD | TBD | Provided in `store.csv` | Yes | Category definitions require source validation |
| `CompetitionDistance` | Competition | Rossmann | Distance to competition | TBD | TBD | Provided in `store.csv` | Yes | Missingness requires validation |
| `CompetitionOpenSinceMonth` | Competition | Rossmann | Month competition began operating | Calendar month | TBD | Provided in `store.csv` | Yes | Structural and true missingness must be distinguished |
| `CompetitionOpenSinceYear` | Competition | Rossmann | Year competition began operating | Calendar year | TBD | Provided in `store.csv` | Yes | Structural and true missingness must be distinguished |
| `Promo2` | Promotion | Rossmann | Participation in the continuing promotion program | TBD | TBD | Provided in `store.csv` | Yes | Coding requires source validation |
| `Promo2SinceWeek` | Promotion | Rossmann | Week Promo2 participation began | Calendar week | TBD | Provided in `store.csv` | Yes | Structural and true missingness must be distinguished |
| `Promo2SinceYear` | Promotion | Rossmann | Year Promo2 participation began | Calendar year | TBD | Provided in `store.csv` | Yes | Structural and true missingness must be distinguished |
| `PromoInterval` | Promotion | Rossmann | Months when Promo2 is active | TBD | TBD | Provided in `store.csv` | Yes | Parsing rules require source validation |

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

During Phase 1, update this document only from inspected source data. Record observed types, missingness, categories, and valid ranges without silently replacing the distinction between Rossmann-provided, derived, and simulated fields.
