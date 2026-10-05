# Phase 3 Feature Contract

Contract version: `phase-3-v1`. This is the approved, implemented predictor schema for the
store-level `Sales` target. It contains 29 ordered predictors. `Store` is retained unchanged as
`int64` and serves as both the Store key and a categorical identity input for later modeling;
Phase 3 does not treat its magnitude as continuous, encode it, or target-encode it. `Date` is a key
only; calendar inputs are derived. Same-weekday statistics, encoding, scaling, imputations, and
availability flags are deferred.

The shared ordered schema is defined in
[`src/rossmann_forecasting/features/contract.py`](../src/rossmann_forecasting/features/contract.py).
Historical and inference outputs use the same predictor functions and exact predictor ordering and
dtypes. Categorical dtype names below refer to pandas' Python-backed nullable string dtype.

## Predictor manifest

Every listed field has role `PREDICTOR`; all are emitted in both train and inference feature views.
Null behavior and leakage notes are feature-specific below. Unless otherwise noted, future-known
fields derive only from the row's Date, supplied future covariates, or joined static Store metadata.

| Predictor | Category and source | Derivation | Artifact dtype | Forecast availability / history dependency | Null behavior and leakage control |
|---|---|---|---|---|---|
| `Store` | Store identity; source `Store` | Preserve ID unchanged; no magnitude transform | `int64` | Known for each target; no Sales history | Required, non-null. Static identity only; later model treatment is categorical. |
| `day_of_week` | Calendar; `Date` | ISO weekday, Monday=1 through Sunday=7; checked against source `DayOfWeek` | `int8` | Known from target Date; no history | Non-null. A source mismatch fails validation. |
| `week_of_year` | Calendar; `Date` | ISO week number | `int8` | Known from target Date; no history | Non-null; ISO week may be 53. |
| `month` | Calendar; `Date` | Calendar month, 1–12 | `int8` | Known from target Date; no history | Non-null. |
| `quarter` | Calendar; `Date` | Calendar quarter, 1–4 | `int8` | Known from target Date; no history | Non-null. |
| `year` | Calendar; `Date` | Calendar year | `int16` | Known from target Date; no history | Non-null. |
| `is_weekend` | Calendar; `Date` | True for ISO weekday 6 or 7 | `bool` | Known from target Date; no history | Non-null. |
| `is_month_start` | Calendar; `Date` | Date is first calendar day of its month | `bool` | Known from target Date; no history | Non-null. |
| `is_month_end` | Calendar; `Date` | Date is last calendar day of its month | `bool` | Known from target Date; no history | Non-null. |
| `state_holiday` | Holiday; source `StateHoliday` | Preserve source category as a string | `string[python]` | Known from target-date input; no history | Required by source; no inferred holiday meanings or target-derived effects. |
| `school_holiday` | Holiday; source `SchoolHoliday` | Validate 0/1 and cast to Boolean | `bool` | Known from target-date input; no history | Required binary source; no inference from Sales. |
| `promo` | Promotion; source `Promo` | Validate 0/1 and cast to Boolean | `bool` | Planned target-date promotion; no history | Required binary source; no inferred promotion effect. |
| `promo2` | Promotion; source `Promo2` | Validate 0/1 and cast to Boolean | `bool` | Static participation metadata; no history | Required binary source. Structural schedule nulls for nonparticipants are allowed. |
| `is_promo2_active` | Promotion schedule; `Promo2`, since year/week, interval, target `Date` | Nonparticipant → False. Participant → validate ISO year/week, use that week's Monday as start, then require target date on/after start and its month in the recurring interval; normalize `Sept` only for matching. | `boolean` | Future-known schedule and target Date; no Sales history | Invalid/incomplete participant schedule → null plus audit finding; no schedule imputation. |
| `store_type` | Store; source `StoreType` | Preserve source category as a string | `string[python]` | Static Store metadata; no history | Required and non-null; no model-specific encoding in Phase 3. |
| `assortment` | Store; source `Assortment` | Preserve source category as a string | `string[python]` | Static Store metadata; no history | Required and non-null; no model-specific encoding in Phase 3. |
| `competition_distance` | Competition; source `CompetitionDistance` | Preserve numeric source value as float | `float64` | Static Store metadata; no history | Source null remains null; no imputation. |
| `competition_has_opened` | Competition; source opening month/year and target `Date` | Compare calendar-month indices. Before opening → False; opening month or later → True. | `boolean` | Static opening metadata plus target Date; no Sales history | Paired missing metadata → null; partial or invalid pair fails. No day-level opening assertion. |
| `competition_age_months` | Competition; source opening month/year and target `Date` | `max(0, target year/month index − opening year/month index)` | `Int16` | Static opening metadata plus target Date; no Sales history | Paired missing metadata → null; known pre-opening → 0. Partial or invalid pair fails. |
| `sales_lag_1` | Target history; historical `Sales` | Exact same-Store Sales at `d−1` calendar day | `float64` | Historical row: actual history strictly before target. Recursive inference: actuals through origin plus earlier recursive predictions. | Null if exact date/value unavailable. No prior-row fallback or gap fill. Origin API rejects future actuals. |
| `sales_lag_7` | Target history; historical `Sales` | Exact same-Store Sales at `d−7` calendar days | `float64` | Same point-in-time rule as `sales_lag_1` | Null if exact date/value unavailable; no seasonal substitution or gap fill. |
| `sales_lag_14` | Target history; historical `Sales` | Exact same-Store Sales at `d−14` calendar days | `float64` | Same point-in-time rule as `sales_lag_1` | Null if exact date/value unavailable; no prior-row fallback. |
| `sales_lag_28` | Target history; historical `Sales` | Exact same-Store Sales at `d−28` calendar days | `float64` | Same point-in-time rule as `sales_lag_1` | Null if exact date/value unavailable; no prior-row fallback. |
| `sales_ma_7` | Target history; historical `Sales` | Mean over all exact calendar dates `d−7` through `d−1` | `float64` | Only values available before target under the applicable origin information set | Null unless all 7 exact dates are present. Target date excluded; no partial window/gap fill. |
| `sales_ma_14` | Target history; historical `Sales` | Mean over all exact calendar dates `d−14` through `d−1` | `float64` | Same point-in-time rule as `sales_ma_7` | Null unless all 14 exact dates are present. Target date excluded; no partial window/gap fill. |
| `sales_ma_28` | Target history; historical `Sales` | Mean over all exact calendar dates `d−28` through `d−1` | `float64` | Same point-in-time rule as `sales_ma_7` | Null unless all 28 exact dates are present. Target date excluded; no partial window/gap fill. |
| `sales_std_7` | Target history; historical `Sales` | Sample standard deviation (`ddof=1`) for exact dates `d−7` through `d−1` | `float64` | Same point-in-time rule as `sales_ma_7` | Null unless all 7 exact dates are present; target excluded. |
| `sales_std_14` | Target history; historical `Sales` | Sample standard deviation (`ddof=1`) for exact dates `d−14` through `d−1` | `float64` | Same point-in-time rule as `sales_ma_7` | Null unless all 14 exact dates are present; target excluded. |
| `sales_std_28` | Target history; historical `Sales` | Sample standard deviation (`ddof=1`) for exact dates `d−28` through `d−1` | `float64` | Same point-in-time rule as `sales_ma_7` | Null unless all 28 exact dates are present; target excluded. |

Observed zero Sales is a valid history value. The source is sparse: an absent Store × Date row is
not a zero and does not get synthesized. Rolling standard deviations use sample `ddof=1`.

## Non-predictor roles

| Field(s) | Role | Contract |
|---|---|---|
| `Store` | `KEY` + `PREDICTOR` | Same unchanged `int64` value serves both purposes once in the artifact. |
| `Date` | `KEY` only | Kept outside the predictor selection; calendar fields derive from it. |
| `Sales` | `LABEL` / historical `HISTORY SOURCE` only | Training target and history source. Target-date Sales is never used for its own row. |
| `Customers` and any Customers-derived source field | `HISTORICAL DESCRIPTIVE SOURCE` only | Excluded from predictors and inference input. |
| `Open` | `AUDIT` / `ELIGIBILITY` / later operational routing | Never a predictor; missing source status remains unknown. Training and primary evaluation eligibility use source `Open == 1`. |
| `Open_resolved`, resolution fields, and Store 622 candidates | `AUDIT` only | Never overwrite source Open, determine eligibility, establish evaluation truth, or force a zero forecast. |
| Kaggle `Id`, source `DayOfWeek`, `row_role`, and availability/null diagnostics | `KEY` or `AUDIT` only | Kept outside predictor selection. `DayOfWeek` is used to validate the derived ISO weekday. |

Training output contains the 29 predictors plus Date, Sales, source Open, eligibility masks, and
row-role metadata. Inference output contains the same 29 predictors plus Date and optional Open/Id/
Open-resolution audit metadata; it contains no Sales, Customers, or Customers-derived fields.
Future-known/static predictors are precomputed for all inference rows. Before a model has generated
recursive predictions, any dynamic feature requiring an exact date after the declared origin stays
null; later horizon steps can rebuild those values with earlier predictions through the origin API.
Generated files are local and ignored: `data/processed/features_train.parquet`,
`data/processed/features_inference.parquet`, and `data/processed/feature_manifest.json`.

## Historical features versus recursive inference

Historical training features are one-step historical rows: each target date uses actual same-Store
Sales only at strictly earlier exact dates. Such precomputed rows are not automatically valid for
a recursive forecast from an earlier origin. The inference API
`build_origin_history_features` requires `actual_history_through_origin`; any actual row after the
declared origin is rejected. Optional `prior_recursive_predictions` can supply predicted history
after the origin. For each target, only exact prior dates can satisfy a lag/window; actual future
Sales are never substituted. Overlapping actual/predicted Store × Date keys fail explicitly, and
each supplied prediction must precede at least one requested target for that Store. In a batch of
targets, exact-date lookups ensure predictions at or after a particular target cannot enter that
row's features. A missing exact date or incomplete window remains null.

The implementation separates future-known/static derivation from dynamic target-history
derivation, then assembles a shared ordered predictor matrix for train and inference.

## Final Holdout Firewall

The final holdout is the latest 28 labeled calendar days, 2015-07-04 through 2015-07-31 for the
current prepared snapshot. Feature definitions were approved before implementation. Development
coverage/null audits stop before the holdout and do not inspect Sales labels. Holdout contact is
limited to mechanical schema, key uniqueness, dtype compatibility, deterministic generation, and
non-mutation checks. No holdout target or feature distribution is summarized; no forecasting
metrics, feature selection, or learned preprocessing is performed here. This firewall applies to
later modeling work as well: do not use holdout outcomes to revise this contract.
