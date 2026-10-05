# Phase 3 — Feature Engineering (Execution Plan)

## 1. Objective and current state

Define a reproducible, auditable feature dataset for Store × Date Rossmann sales forecasts, with
every predictor available at the forecast origin. This plan follows the completed Phase 2
preparation and EDA. FE-01 through FE-07 have now been approved by the user after final design
review, including the amendments recorded below. The design-approval checkpoint precedes
implementation; forecasting models and results remain out of scope for this phase.

The project remains store-level monetary Sales forecasting at a 14-day primary horizon. It is not
SKU forecasting, and Sales must not be described as physical units. The raw Rossmann files remain
immutable. Prepared historical train and future-covariate test remain separate inputs.

## 2. Scope and exclusions

### Approved Phase 3 implementation scope

- Establish a single documented feature contract shared by historical feature construction and
  future inference.
- Add reusable feature logic under `src/rossmann_forecasting/`, with thin scripts and fixture tests.
- Define calendar, holiday/promotion, store, competition, exact-date lag, and trailing rolling
  features listed in Section 5.
- Preserve observed Store × Date keys and sparse coverage; retain missingness when source history
  cannot support a feature.
- Produce reproducible local, ignored feature outputs from the prepared Phase 2 Parquet tables.
- Update the Data Dictionary and progress record with the implemented definitions and actual
  validation results.

### Explicitly out of scope

- Seasonal Naive, Exponential Smoothing, LightGBM, any other model, model selection, feature
  importance, hyperparameter tuning, and forecast evaluation.
- Temporal validation-window selection, final-holdout inspection, or any random split.
- Forecast metrics, inventory simulation, synthetic supply-chain fields, APIs, dashboards, or
  deployment.
- Imputing Sales, inserting missing Store × Date rows into the canonical history, or changing any
  raw or prepared source values.
- Using future actual Customers, future actual Sales, or the Kaggle sample-submission placeholders
  as predictors or labels.

## 3. Inputs, invariants, and current implementation

Inputs are `data/interim/train.parquet`, `data/interim/test.parquet`, and the separately stored
store metadata already joined by Phase 2. Phase 2 exposes `build_prepared_tables` and
`derive_test_open_resolution` in `src/rossmann_forecasting/data/preparation.py`; it preserves
train/test roles, source order and keys, the sparse 184-day absence, and nulls. The latter Open
resolution is a separate uncertain audit candidate, not source truth. Phase 3 must consume these
existing interfaces rather than duplicating preparation or silently merging the candidate into
`Open`.

Fixed constraints:

- Unique key: `(Store, Date)`. Do not sort/change key values in source tables or expand the canonical
  history to a complete calendar.
- `Store` is both the unchanged identity key and a candidate categorical predictor. Preserve its
  source `int64` dtype and ID values; do not interpret magnitude, one-hot encode, or target encode it
  in Phase 3. Its later model treatment is categorical. `Date` is a key/time field only; derive
  calendar predictors from it and exclude raw Date from the predictor matrix.
- Target: `Sales` turnover. Keep labels outside the predictor matrix.
- `Customers` remains available only for historical description, never in the feature matrix,
  joins for inference, or future prediction inputs. No feature may be derived from future
  Customers, directly or indirectly.
- Forecast horizon: 14 days. Forecasting is recursive per the proposal, so later horizons may use
  earlier predictions in a temporary history, never later actual Sales.
- Future-known calendar, observed holiday indicators, planned Promo, and store metadata may be
  used. Each use still needs an explicit source and availability rule.
- Preserve the final chronological 28-day holdout untouched; Phase 3 may build point-in-time
  historical features but must not use this holdout for feature selection or tuning.
- Primary later model-label/evaluation population is source `Open == 1`. Keep all source rows and
  distinguish history retention, training-label eligibility, evaluation eligibility, and
  operational post-processing.

Phase 3 must carry forward the approved Phase 2 dispositions without reinterpretation: preserve the
sparse historical calendar and the shared 184-day gap; do not fabricate absent Store × Date rows or
zero-fill absent Sales; retain all 54 observed `Open=1, Sales=0` rows; preserve the 11 original
Store 622 test `Open` nulls and keep their unanimous historical-context resolutions uncertain and
separate; leave unexplained competition metadata missing; preserve structural Promo2 schedule
nulls for nonparticipants; and treat both raw and Phase 2 interim files as immutable inputs.

## 4. Point-in-time design and information sets

For a prediction row `(s, d)`, define:

- `d`: target date.
- `o`: forecast origin, when the forecast is issued; for the one-step training analogue, features
  for `d` are built from information available before `d`.
- `H_o`: actual Sales observations with the same Store and observation date no later than `o`.
- `P_(o,d)`: predictions already generated recursively for dates after `o` and before `d`.

Target-history features at `d` may read only same-store values from `H_o` whose date is earlier
than `d`, plus explicitly supplied earlier recursive predictions `P_(o,d)`. They may not read an
actual Sales value dated after `o`, even when that value exists in the full historical frame. The
feature builder must receive an explicitly origin-censored history (and optional prior predictions)
or an equivalent auditable point-in-time interface; it must not infer availability merely from a
row's position in a full-sample DataFrame. Historical training features use only dates strictly
before their target date. At inference horizon `h > 1`, earlier steps in `P_(o,d)` are model
predictions generated in that recursive run, never teacher-forced actual Sales. Inference features
use actuals through the declared origin, then those prior predictions for recursive steps; no
future actual target is required or permitted.

Calendar and other future-known features are derived from target-date covariates and store metadata.
They do not use future target values. Source `Open` is a routing/evaluation attribute, not a Sales
predictor. The separate `Open_resolved` candidate remains uncertain and cannot become source `Open`
or a primary training/evaluation label.

### Historical feature rows versus recursive inference

A historical feature row for target date `d` may use actual same-store Sales strictly before `d`;
its date-specific values are one-step historical features. That precomputed row is not automatically
valid for a multi-step forecast from an earlier origin. For a recursive forecast issued at origin
`o`, actual Sales are available only through `o`. For each later target date `d`, dynamic history is
origin-censored actual history plus optional predictions generated earlier in that same recursive
forecast, with dates `o < date < d`. Actual Sales after `o` are never available to the inference
feature builder, even if they exist in a full historical table. This phase implements only that
feature API; it does not implement the forecasting model that will generate optional predictions.

The internal API should separate small, testable functions for (A) future-known/static predictors
(Store, calendar, holiday, promotions, store and competition metadata) and (B) dynamic target-history
predictors (exact Sales lags and trailing Sales statistics). The public assembly function may
combine their results without introducing a feature framework.

### Final Holdout Firewall

The proposal reserves the latest 28 labelled calendar days as final holdout. Phase 3 feature
definitions are frozen by this approval before implementation. Do not use final-holdout target
values, feature distributions, null/coverage statistics, or other descriptive statistics to choose
features, change semantics, select missing-value treatments, compare contract alternatives, or fit
learned preprocessing. No forecast metrics are computed in Phase 3.

For audits that may inform Phase 3 implementation decisions, use only the development period before
the final 28-day holdout. Holdout checks are limited to mechanical integrity: keys/row coverage,
schema, dtype compatibility, deterministic output generation, and input non-mutation. A later
phase may mechanically generate the already-frozen contract on holdout rows for evaluation; this
does not authorize examining holdout performance or using holdout statistics to revise the
contract. Temporal model validation and model selection remain out of scope.

## 5. Proposed feature contract

The following manifest is the approved Phase 3 predictor schema. Names are lower snake case for
derived fields; source-coded category values retain their source meaning. `Store` is both key and
predictor and appears once in the artifact; its unchanged source `int64` value is a categorical
identity, not a numeric magnitude. Raw `Date` is key-only. `Sales` is label/history source only,
never a predictor.

| Feature(s) | Group and source | Availability and derivation | Null/edge policy and leakage boundary |
|---|---|---|---|
| `Store` | Store identity; source `Store` | Preserve source ID unchanged as `int64`; available for every train/inference row and treated as a categorical candidate by later models. | Serves as both `(Store, Date)` key and predictor, present once. Never transform into an ordinal/continuous magnitude, one-hot encode, or target encode in Phase 3. |
| `day_of_week` | Calendar; `Date` | ISO weekday, Monday=1 through Sunday=7; assert equality with source `DayOfWeek`. | Derive for both roles from Date; fail on disagreement rather than silently prefer a conflicting value. Keep source DayOfWeek as audit, not duplicate predictor. |
| `week_of_year` | Calendar; `Date` | ISO week number, 1–53. | ISO calendar convention; test year-boundary dates. |
| `month` | Calendar; `Date` | Calendar month, 1–12. | Always known for historical and future dates. |
| `quarter` | Calendar; `Date` | Calendar quarter, 1–4. | Always known. |
| `year` | Calendar; `Date` | Calendar year. | Always known. |
| `is_weekend` | Calendar; `Date` | Boolean for ISO weekdays 6–7. | Always known; defined by ISO weekday convention. |
| `is_month_start` | Calendar; `Date` | Boolean from calendar date. | Always known. |
| `is_month_end` | Calendar; `Date` | Boolean from calendar date. | Always known. |
| `state_holiday` | Holiday; row covariate `StateHoliday` | Preserve the observed source category/code. | No category meaning is invented beyond verified dictionary semantics; require known target-date covariate. |
| `school_holiday` | Holiday; row covariate `SchoolHoliday` | Preserve validated source indicator. | Require known target-date covariate; reject invalid domain. |
| `promo` | Promotion; row covariate `Promo` | Preserve validated planned/current promotion indicator for the target date. | Require known target-date covariate; reject invalid domain. |
| `promo2` | Promotion; store metadata `Promo2` | Preserve participation status. | Must be valid and present. Do not turn structural missing schedule fields for Promo2=0 into fake values. |
| `is_promo2_active` | Promotion; `Promo2`, `Promo2SinceWeek`, `Promo2SinceYear`, `PromoInterval`, target `Date` | For Promo2=0, False. For Promo2=1, require valid schedule; compute ISO Monday of start year/week, require `Date >=` start, and require target month in the recurring PromoInterval. Normalize the source spelling `Sept` to September for month comparison only. | Promo2=1 with incomplete/invalid schedule yields missing plus an audit error/flag; never infer a schedule. Validate week using ISO calendar rules. Do not use realized future Sales or Customers. |
| `store_type` | Store; metadata `StoreType` | Preserve verified source category. | Required and nonmissing after the Phase 2 many-to-one join; category encoding is deferred to model work. |
| `assortment` | Store; metadata `Assortment` | Preserve verified source category. | Required and nonmissing; no ordinal meaning is assumed. |
| `competition_distance` | Store; metadata `CompetitionDistance` | Preserve source numeric value in its documented source unit. | Keep the three source nulls missing; no imputation or unsupported unit claim. |
| `competition_has_opened` | Competition; `Date`, `CompetitionOpenSinceMonth`, `CompetitionOpenSinceYear` | Nullable boolean comparing target year/month with the reported opening year/month. | False and age zero before opening; True and age zero in the opening month; True after it. Null when both source fields are missing. Partial/invalid pairs fail validation and are audited. |
| `competition_age_months` | Competition; same metadata and target `Date` | Nullable integer calendar-month offset: `12 × (target_year - open_year) + (target_month - open_month)`. | Zero before opening and in opening month; positive month offsets after opening. Null when opening pair is missing. Month-level, not day-level, precision. |
| `sales_lag_1` | Sales history; same-store Sales | Value at exact calendar date `d - 1 day`. | Null if exact date is not present/available in origin-censored actual/prediction history. Never substitute previous observed row. |
| `sales_lag_7` | Sales history; same-store Sales | Value at exact calendar date `d - 7 days`. | Same exact-date availability rule. |
| `sales_lag_14` | Sales history; same-store Sales | Value at exact calendar date `d - 14 days`. | Same exact-date availability rule. |
| `sales_lag_28` | Sales history; same-store Sales | Value at exact calendar date `d - 28 days`. | Same exact-date availability rule. |
| `sales_ma_7` | Sales history; same-store Sales | Mean over the 7 calendar dates `d-7` through `d-1`. | Require all seven exact calendar dates to have available values; otherwise null. Include observed closed-day zeros and valid open/zero-Sales values. No gap bridging or partial-window mean. |
| `sales_ma_14` | Sales history; same-store Sales | Mean over `d-14` through `d-1`. | Require all 14 exact calendar dates and available values; otherwise null. |
| `sales_ma_28` | Sales history; same-store Sales | Mean over `d-28` through `d-1`. | Require all 28 exact calendar dates and available values; otherwise null. |
| `sales_std_7` | Sales history; same-store Sales | Sample standard deviation (`ddof=1`) over the same 7-day trailing calendar window. | Require all 7 dates; otherwise null. |
| `sales_std_14` | Sales history; same-store Sales | Sample standard deviation (`ddof=1`) over the same 14-day trailing calendar window. | Require all 14 dates; otherwise null. |
| `sales_std_28` | Sales history; same-store Sales | Sample standard deviation (`ddof=1`) over the same 28-day trailing calendar window. | Require all 28 dates; otherwise null. |

### Additional contract decisions

- Preserve observed Sales=0, including all 54 `Open=1, Sales=0` rows, as a valid observed history
  value unless later evidence approves a separate correction. Closed-day Sales=0 is also retained
  in lag/rolling context because it is actual store-day turnover, not a fabricated fill.
- A missing Store × Date row is not equivalent to a zero. The shared 184-day gap and any other
  missing exact dates produce null lag/rolling values until their exact calendar windows are
  available. Never bridge using “previous row” semantics.
- At the beginning of a store's observed history, every lag is null unless its exact required
  calendar-date observation exists; a trailing window is null unless every calendar date in that
  window exists and has an available actual/predicted value. There is no shorter warm-up window,
  expanding-window fallback, row-count fallback, imputation, or date reindexing. After any gap,
  each feature becomes available independently on the first target date for which its exact lag or
  entire trailing calendar window is supported. Thus, after the 184-day gap, a 1-day lag can resume
  on the second observed date, a 7-day lag / MA_7 / STD_7 only after seven consecutive observed
  dates, 14-day windows after fourteen, and 28-day windows after twenty-eight. This rule is
  deterministic from Store, target Date, and available-history dates.
- Do not impute, clip, or add a missingness indicator to the initial predictor schema. Record
  feature-availability counts in audit output; reconsider model-facing flags only if later evidence
  justifies them.
- Same-weekday rolling statistics are optional in the proposal and are deferred from the initial
  schema. Revisit only with a documented operational definition and validation evidence in a later
  reviewed scope; no feature selection occurs in Phase 3 planning.
- No target encoding, learned category mapping, scaling, global statistic, or data-derived
  transformation is part of this contract. Any later model-specific transform must be fit using
  training history available at the appropriate origin.
- `competition_open_date_proxy`, if materialized for audit/helper calculations, is not a predictor
  and must be excluded by the explicit predictor-column list. It is the first calendar day of the
  reported month only as a computational proxy and must never be presented as the actual opening
  day. Known not-yet-open is `competition_has_opened=False` and
  `competition_age_months=0`; unknown start metadata is null for both features.

## 6. Open status, label eligibility, and inference routing

Use separate concepts; do not overwrite source `Open`:

1. **History retention:** retain every prepared historical row and Sales value. `Open=0` rows and
   the 54 observed `Open=1, Sales=0` rows remain in the history used by target lags/rolling windows.
2. **Training-label eligibility metadata:** emit an auditable boolean for actual source
   `Open == 1` and nonmissing historical Sales. This marks the proposal-aligned primary label
   population but does not delete other feature/history rows or settle later model-window policy.
   Keep an explicit actual-source Open indicator/state separate from feature values.
3. **Evaluation eligibility:** for later primary forecast metrics, require actual source `Open == 1`
   and an observed actual Sales label for that forecast target. Do not use a candidate Open status
   to make a row eligible. Keep any calendar-level operational assessment separate from primary
   open-day model metrics.
4. **Operational post-processing / inference:** never include Open, Open_resolved, Customers,
   Customers-derived fields, or Sales label fields in the common
   predictor matrix. For eventual operational routing, known source `Open=0` follows the proposal's
   zero-forecast rule; known source `Open=1` is eligible for a Sales forecast. A missing source Open
   is unknown, not closed: retain forecast/status as unresolved and do not force zero or score it
   as known-open. The existing uncertain `Open_resolved=1` candidate may be shown in audit metadata
   only; it is not ground truth and is not used for primary training/evaluation eligibility or
   forced-zero routing.

This plan defines the safe default for Phase 3 and the later interface. Any change to candidate
Open use requires a separate user-reviewed decision that accepts and documents its uncertainty.

## 7. Train/inference schema and reproducible outputs

Use the same ordered predictor columns and derivation functions for historical and future rows.
The common predictor list begins with unchanged source `Store` (`int64`) as categorical identity,
followed by the derived/source-coded predictors in the contract. `Store` is physically present once
while serving as both key and predictor; `Date` is key-only and never a raw predictor. Keep
row-role/audit metadata, training `Sales` labels, and training/evaluation eligibility outside the
predictor matrix. Test/inference contains no `Sales`, `Customers`, or Customers-derived field. Keep
`Open`, any Open candidate/resolution, Kaggle `Id`, and other source audit fields outside
predictors. Assert exact predictor schema, column order, and dtypes equality between roles.

Proposed implementation layout (subject to review):

- `src/rossmann_forecasting/features/` for the shared contract and reusable calendar, schedule,
  competition, lag, rolling, and point-in-time assembly functions; avoid a framework beyond small,
  testable functions.
- `scripts/build_features.py` as a thin deterministic command using Phase 2 prepared Parquet.
- `tests/test_feature_engineering.py` with constructed fixtures only.
- `docs/FEATURE_CONTRACT.md` as the version-controlled detailed manifest; update the relevant
  derived-feature section in `docs/DATA_DICTIONARY.md` to link to and summarize that contract.
- Ignored `data/processed/` outputs such as `features_train.parquet` and
  `features_inference.parquet`, with deterministic schemas, row counts, and source/output hashes in
  a local manifest. Do not commit processed datasets or generated model artifacts.

The train artifact may carry predictor columns plus key/label/audit/eligibility fields; because
Store is also a predictor, store its value once and treat it as both key and predictor. It may
include Date, Sales label, source Open, row role, and training/evaluation eligibility as separate
non-predictor columns. The inference artifact may include Store, Date, source Open, optional
separately named Open-candidate audit fields, row role, and Kaggle Id outside its predictors. No
such field is in the predictor selection. Without a model-supplied recursive prediction, future
dynamic features whose exact required history dates fall after the origin remain null; later model
code can rebuild them stepwise by passing prior predictions.

Reuse Phase 2 source hash and join checks where practical. Generated outputs must be reproducible
from the command, must not mutate `data/raw/` or `data/interim/`, and must preserve row counts and
Store × Date keys for each respective input role. Any output materialized from real data stays
ignored.

## 8. Test and validation plan

Use small in-memory synthetic fixtures, never copied real Rossmann rows. At minimum test:

- Calendar derivation, ISO weekday assertion, year/week boundaries, month boundaries, weekends,
  quarter, month start/end, and deterministic output.
- Promo2=0 is inactive despite structural schedule nulls; Promo2=1 schedule boundaries, ISO week
  validation, repeated interval months, and `Sept` normalization; incomplete participant metadata
  remains unresolved and is auditable.
- Competition month/year pairs, month-level age, dates before opening, same-month opening, paired
  missing values, invalid month/year, and partial-pair rejection.
- Exact 1/7/14/28-day lags, current-target exclusion, retained valid zeros, missing-date no-fallback,
  first-date/first-28-days-of-history deterministic null behavior, and 184-day-gap-like sparse
  history behavior, including the exact first post-gap availability date for each lag/window.
- Trailing 7/14/28 calendar windows use only dates before target, have exact expected row counts,
  use the documented sample standard deviation, require complete windows, and return null across
  holes; closed-day zeros count as observed values.
- Recursive prediction history may fill earlier horizon steps, while actual Sales after the
  declared origin cannot enter any feature. Mutating later actual Sales must not alter the same
  origin's prediction features.
- Reject an `actual_history_through_origin` containing any date after the declared origin; validate
  optional prior predictions are unique, strictly after origin, and before the requested target
  date. Keep predictions distinct from actual history.
- Store appears unchanged and deterministic with `int64` dtype in both predictor schemas; Date is
  key-only; the competition proxy date cannot enter the explicit predictor list.
- Competition tests cover known future opening, opening month, one month after, cross-year offsets,
  paired missing fields, partial pairs, invalid months, and invalid/implausible years according to
  the Phase 1 validation contract. Before opening status/age are False/0; opening month is True/0;
  unknown fields are null/null.
- Promo2 tests cover valid ISO week 53 in a year that has it, invalid year/week pairs, schedule
  starts before/in/after an interval month, and `Sept` normalization.
- Holdout firewall tests/audits ensure coverage summaries use only development-period rows; any
  holdout interaction is limited to mechanical schema, key, dtype, deterministic-generation, and
  non-mutation checks. No holdout outcome or distribution informs a design choice.
- `Customers`, every Customers-derived field, target-date `Sales`, `Open`, uncertain
  `Open_resolved`, Kaggle submission values, and row-role identifiers never appear among model
  predictors. The future test input is validated to contain no Customers source field.
- Train/inference predictors have identical names, order, and dtypes; target labels and eligibility
  remain separate; missing Open remains unknown; known Open is never overwritten.
- Store × Date uniqueness, exact input key/row coverage, metadata join cardinality, stable schema,
  non-mutation of inputs, deterministic reruns, and output-manifest consistency.

On the real prepared snapshot, validate row/key preservation, predictor schema and dtypes,
calendar consistency, promotion/competition edge cases, source hash stability, and feature
availability. Any diagnostic null rates, distributions, or coverage summaries that can influence
Phase 3 decisions use development-period rows only. Holdout checks are mechanical integrity checks
only, as defined by the Final Holdout Firewall. Report that sparse coverage reduces usable
histories rather than hiding it. Do not compute forecast metrics or select features by observed
Sales performance.

Run relevant pytest and configured Ruff checks during implementation; record only checks actually
run in `docs/PROGRESS.md`. Review the diff for leakage and unintended scope.

## 9. Implementation sequence and acceptance criteria

Execution sequence for the approved Phase 3 scope:

1. Record this user-approved design checkpoint and update the plan before coding.
2. Add shared point-in-time feature assembly and focused unit tests using fixtures.
3. Build train and inference feature views with a common ordered predictor schema and separated
   labels/audit columns.
4. Add the thin command, local ignored outputs, provenance manifest, and Data Dictionary contract
   reference.
5. Run fixture tests, lint/format checks, and real-data integrity/availability audits.
6. Self-review schemas, null handling, exact-date behavior, and every target-history access for
   leakage; inspect `git diff` and `git status`.
7. Update `docs/PROGRESS.md` with actual results. Keep this plan active and do not archive it until
   the user has reviewed the implementation and explicitly accepts Phase 3 closure.

Phase 3 implementation is done only when the shared feature contract and train/inference schema
are documented; every feature has source, derivation, availability, null, and leakage rules; sparse
coverage and Open states retain the dispositions above; fixture tests cover the cases in Section 8;
real-data outputs preserve keys and source files; all actual tests/checks are recorded; no models,
splits, holdout tuning, or forecasting claims were introduced; and plan, code, Data Dictionary, and
progress agree.

## Approved Design Decisions

The user approved FE-01 through FE-07 before implementation. These decisions govern Phase 3; no
additional feature behavior is inferred from them.

### FE-01 — Initial feature schema and same-weekday extension

- **Status:** APPROVED WITH AMENDMENT.
- **Question:** Approve the manifest in Section 5 as the initial feature contract, and defer the
  proposal's optional same-weekday rolling statistics?
- **Approved option:** Use the listed calendar, holiday/promotion, store, competition, four exact
  Sales lags, and six trailing Sales statistics; defer same-weekday features. Include `Store`
  unchanged as both key and categorical predictor (`int64`, present once); never interpret ID
  magnitude, one-hot encode, or target encode it in Phase 3. `Date` is a key only. Preserve source
  category values without model-specific encoding/scaling; defer those treatments to later model
  work.
- **Alternatives considered:** Add same-weekday summaries in Phase 3; or reduce the initial feature
  list before implementation. Encoding/scaling the features now is a separate model-preparation
  activity and is not recommended in this phase.
- **Reason:** This is a compact, inspectable first contract that covers the proposal's required
  groups without adding another history-window definition before any model validation.
- **Consequences:** The schema stays fixed and easier to audit; optional weekday-conditioned
  information will not be available to later model experiments unless a reviewed follow-up adds it.
- **Leakage implications:** The proposed fields use target-date calendar/schedule/static data or
  point-in-time Sales history only. Deferral avoids ambiguous same-weekday windows; any later
  addition must obey the same origin-censored history rule and cannot be selected on the final
  holdout.
- **Reversible later?:** Yes. A later reviewed contract version can add/remove fields before
  fitting a model; changing the schema requires regenerated features and comparable validation.

### FE-02 — Exact lag and complete rolling-window semantics

- **Status:** APPROVED.
- **Question:** Approve exact-calendar-date lags and complete trailing calendar windows that return
  missing when any required date/value is unavailable?
- **Recommended option:** Lags use exactly `d-1`, `d-7`, `d-14`, or `d-28`. Each rolling statistic
  uses the `n` calendar dates `d-n` through `d-1`, requires all `n` values, and never includes
  `Sales_d`. Missing source dates, unavailable origin values, and warm-up windows yield null; no
  partial mean, expanding fallback, prior-observed-row substitution, or gap fill.
- **Alternatives considered:** Permit partial windows; use the previous `n` observed rows regardless
  of elapsed calendar time; or reindex and fill absent dates. These are rejected for the initial
  contract because they respectively change the statistic's meaning, bridge the shared gap, or
  invent observations.
- **Reason:** Calendar-time semantics match “daily” lags/rolling features and keep the sparse source
  truth intact.
- **Consequences:** Some rows, notably at series starts and around gaps, will have null history
  features. Availability resumes independently when each exact lag or complete window is
  supported; the initial implementation must audit these null counts.
- **Leakage implications:** The target date is excluded by construction; only actual values known by
  the origin or earlier recursive predictions are eligible. Partial windows do not create target
  leakage by themselves but can conceal sparse coverage; previous-row semantics can incorrectly
  treat a distant past value as yesterday.
- **Reversible later?:** Yes, with a new versioned feature definition and regenerated data; any
  alternative must pass gap and point-in-time tests and be evaluated without touching the holdout.

### FE-03 — `competition_age` meaning and missing policy

- **Status:** APPROVED WITH AMENDMENT.
- **Question:** How should the month/year-only competition start metadata become target-date status
  and age features?
- **Approved option:** Emit `competition_has_opened` and `competition_age_months` using year/month
  arithmetic. Before opening: False/0. In opening month: True/0. After opening: True and the
  calendar-month offset (e.g. March 2014 to May 2014 gives 2). When both source values are missing,
  emit null/null. Reject partial pairs or invalid/implausible month/year values under the Phase 1
  validation contract; do not impute the 354 unexplained pairs. An optional first-of-month
  `competition_open_date_proxy` is helper/audit metadata only, never a predictor or claimed exact
  open day.
- **Alternatives considered:** Treat the proxy as an exact day and compute elapsed days; preserve
  signed negative ages; or omit status/age features. These alternatives do not express the approved
  distinction between known not-yet-open and unknown metadata as directly.
- **Reason:** Source precision is month/year only; calendar-month arithmetic is reproducible and
  does not assert day precision.
- **Consequences:** Known not-yet-open is False/0; unknown opening metadata is null/null. Age is
  month-granular. The first-of-month proxy is not an observed event date.
- **Leakage implications:** Uses only static source metadata and the target Date; it does not use
  Sales or future observations. The missingness policy cannot consult later outcomes.
- **Reversible later?:** Yes, but changing units or pre-opening semantics changes feature meaning
  and requires a versioned contract and regenerated outputs.

### FE-04 — `is_promo2_active` schedule semantics

- **Status:** APPROVED.
- **Question:** How should the Promo2 start week interact with recurring active months?
- **Recommended option:** `Promo2=0` means False despite structural schedule nulls. For `Promo2=1`,
  require all schedule fields; validate the ISO year/week; define start as Monday of that ISO week;
  active is true only on/after that start and in a listed recurring calendar month. Normalize
  `Sept` to September for matching. Incomplete/invalid participant schedules remain null and are
  reported, not inferred.
- **Alternatives considered:** Apply listed months for the entire calendar year regardless of
  start week; treat the start week as a month-only start; or impute incomplete participant
  schedules. These would change schedule boundaries or assert unsupported information.
- **Reason:** The recommendation uses both supplied schedule components, handles year boundaries
  consistently, and retains structural versus unexplained missingness distinctions.
- **Consequences:** The resulting indicator is deterministic for every target date with a valid
  schedule; nonparticipants remain false, and unresolved participant schedules are null.
- **Leakage implications:** Only target-date future-known schedule metadata and Date are used. No
  future Sales/Customers or outcome-derived “promotion effect” is consulted.
- **Reversible later?:** Yes, through a reviewed rule/version change and regenerated feature data;
  boundary behavior must remain covered by tests.

### FE-05 — Feature-availability indicators

- **Status:** APPROVED.
- **Question:** Should the initial predictor matrix add one or more flags indicating unavailable
  lag/rolling history?
- **Recommended option:** No model-facing availability flags initially. Keep per-feature
  availability counts and masks in audit output only; leave the predictor value null when history
  is insufficient.
- **Alternatives considered:** Add a general history-available flag; add one flag per lag/window;
  or impute values with a corresponding flag. The latter is not proposed because it combines a
  methodological choice with the initial feature contract.
- **Reason:** Null values already express unavailable history without expanding the schema or
  implying that a source omission is a zero. Whether a model benefits from flags is unknown before
  validation.
- **Consequences:** A later model must explicitly support or handle nulls using training-only
  rules; audit outputs must expose the practical coverage loss by store and date.
- **Leakage implications:** Date/source-coverage flags could be computed without future targets,
  but may encode acquisition gaps. Deferring them avoids accidentally turning future target
  availability into a predictor; no flag may be based on future Sales/Customers.
- **Reversible later?:** Yes. Flags may be introduced as separately versioned features after
  evidence from permitted validation windows; never tune them on the final holdout.

### FE-06 — Use of uncertain Store 622 `Open_resolved` candidates

- **Status:** APPROVED.
- **Question:** May the 11 uncertain unanimous-history Open candidates affect model eligibility or
  operational zero-forecast post-processing?
- **Recommended option:** No. Preserve source `Open` nulls, keep `Open_resolved` in separate audit
  metadata, exclude those rows from known-open/known-closed decisions and primary evaluation, and
  do not force zero for unknown status.
- **Alternatives considered:** Treat candidate values as true Open status; use them only for
  operational routing but not evaluation; or require a separate explicit adjudication before any
  use. Only the last is acceptable if the recommendation is later changed.
- **Reason:** Phase 2 explicitly labels the consensus rule uncertain; historical unanimity does not
  prove actual future opening status.
- **Consequences:** Missing-Open future rows retain an unresolved operational status; the later
  application must surface that uncertainty rather than calling it closed or known-open.
- **Leakage implications:** The candidate uses only earlier exact-context Open history, but its
  uncertainty creates a target-eligibility/operational-label risk. It cannot be used as actual
  evaluation truth or joined into the predictor matrix.
- **Reversible later?:** Yes, only through a separate documented, user-approved policy; source
  `Open` must remain null and source data must never be rewritten.

### FE-07 — Shared train/inference output contract and artifact layout

- **Status:** APPROVED WITH FE-01 AMENDMENT.
- **Question:** Approve one common ordered predictor schema with separate role-specific outputs and
  a versioned human-readable contract?
- **Approved option:** Reuse the same feature functions and exact ordered predictor columns for
  train/inference, including unchanged `Store` categorical identity as the first predictor; keep
  Date, labels, role/audit/eligibility fields separate from predictors; write distinct ignored
  Parquet outputs under `data/processed/`; maintain `docs/FEATURE_CONTRACT.md` and link it from the
  Data Dictionary.
- **Alternatives considered:** Store both roles in one role-labeled table while maintaining one
  strict predictor schema; or implement separate training and inference feature logic. Separate
  logic is rejected because it invites schema drift; the unified role-labeled artifact remains
  possible if consumers and validation make it clearer.
- **Reason:** The current Phase 2 preparation keeps train and test as distinct roles; a shared
  derivation contract prevents train/serve skew while role-specific artifacts prevent accidental
  test labeling.
- **Consequences:** Feature datasets and their hashes remain local/ignored; the contract is
  version-controlled; train-only labels and masks cannot leak into inference predictors.
- **Leakage implications:** Matching schemas alone do not prove point-in-time safety, so each role
  still uses the Section 4 information set. The inference artifact cannot contain Sales,
  Customers, Customers-derived fields, or target labels.
- **Reversible later?:** Yes. Storage layout can change without changing feature meanings, provided
  the common predictor schema, role separation, and point-in-time rules remain enforced.

## Implementation Execution Record — Review Pending

Implementation is checkpointed in focused commits on `feat/feature-engineering` for external code
review. Phase 3 is not formally closed and this plan remains active. No Phase 4 or forecasting work
was started.

- Reusable implementation: `src/rossmann_forecasting/features/{contract,calendar,promotion,competition,history,pipeline,runner}.py`.
- Command: `scripts/build_features.py`, backed by `rossmann-build-features`.
- Documentation: `docs/FEATURE_CONTRACT.md`; Section B of `docs/DATA_DICTIONARY.md`; ADR-012;
  progress results in `docs/PROGRESS.md`.
- Tests: `tests/test_feature_engineering.py`; full repository suite passed, 45 tests.
- Real-data build: 1,017,209 train rows and 41,088 inference rows; same ordered 29-predictor
  schema and matching dtypes. Raw source hashes (4 files) and Phase 2 prepared Parquet hashes
  (3 files) matched before/after. Outputs and local manifest are ignored.
- Development diagnostics stop at 2015-07-03. Final holdout integrity-only range is 2015-07-04
  through 2015-07-31; no holdout outcome/distribution summary or forecast metric was produced.
- Gap audit for Store 13: no dynamic history on Jan 1, 2015; exact lag/window availability resumes
  incrementally, with all ten dynamic features available Jan 29 after 28 complete prior dates.
- Checks actually run: raw validator (0 errors, 4 warnings, 12 info); repeated deterministic builds
  matched each corresponding artifact hash; pytest (45 passed); Ruff check; Ruff format check (44
  files); `git diff --check`; relative Markdown links.

The execution record documents completed technical work, not final phase acceptance. Do not move
the plan to `plans/completed/` or mark Phase 3 complete before user review.
