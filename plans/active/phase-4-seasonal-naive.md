# Phase 4 — Seasonal Naive Baseline (Design and Execution Plan)

**Status:** PLANNING / DESIGN REVIEW — proposed methodology awaits explicit user approval. No
forecasting code, forecasts, or metrics have been produced.

## 1. Objective and current state

Phase 4 will establish the required weekly Seasonal Naive benchmark for 14-day, store-level
monetary Rossmann `Sales` forecasting. This document records the proposed validation windows,
multi-step semantics, operational routing, evaluation population, metrics, output record, test
coverage, and implementation boundary so later work does not invent methodology.

Phase 3 is COMPLETE on `main`. The implementation was merged in PR #3; its formal documentation
closeout is also merged on `main` at `c016c4e3a2c33da278ebdbbe074b3e1d4f13fe70`. The completed
Phase 3 plan is `plans/completed/phase-3-feature-engineering.md`. No Phase 4 implementation exists.

This is a planning checkpoint only. The proposed choices below are not accepted architectural
decisions. Implementation must wait for explicit design approval, and only approved choices may be
implemented.

## 2. Scope and exclusions

### Phase 4 objective after approval

- Implement a reusable weekly Seasonal Naive forecaster for the 14-day horizon.
- Implement reusable forecast metrics under the approved population and aggregation rules.
- Produce rolling-origin predictions on the approved development windows.
- Preserve auditable forecast, label, routing, and eligibility fields in output artifacts.
- Add focused tests and a thin command only if a command is useful and justified.

### Explicitly out of scope

- Any work before the user approves the design recorded here.
- Exponential Smoothing / Holt-Winters, LightGBM, tuning, model selection, or later phases.
- Final-holdout evaluation, inspection of holdout outcomes, or holdout-guided design changes.
- Prediction intervals, inventory simulation, synthetic supply-chain data, API, dashboard, or
  deployment.
- Rewriting, expanding, imputing, or otherwise modifying raw/interim historical data.
- Using future actual `Sales`, future `Customers`, `Customers`-derived information, or future
  outcome-derived features to generate a forecast.

## 3. Already-approved project constraints

These are established by the proposal, project plan, progress record, feature contract, and
decision log; they are not reopened by this design review.

| Constraint | Established rule |
|---|---|
| Unit | Store × Date; no SKU-level forecasting. |
| Target and units | Rossmann `Sales`, a monetary turnover measure, not physical product units. |
| Primary horizon | 14 calendar days. |
| Required baseline | Seasonal Naive, using weekly seasonality (seven calendar days). |
| Time integrity | No random shuffling; use rolling-origin / walk-forward validation. |
| Validation count | At least three 14-day development validation windows. |
| Final holdout | Latest 28 labelled calendar days, frozen as 2015-07-04 through 2015-07-31; untouched until methodology is locked. |
| Primary metric | MAE. Secondary metrics: RMSE, MAPE with caution, and WAPE. |
| Primary evaluation population | Actual source `Open == 1` observations with an observed `Sales` label. |
| Closed-store business rule | A target date known to be closed receives an operational zero forecast. This routing is separate from the raw baseline. |
| Information boundary | Future `Customers` and future actual `Sales` must not enter a forecast. |
| Missing target history | Preserve sparse Store × Date coverage; an absent exact date is not a zero and is not replaced by another observed row. |

## 4. Phase 2 and Phase 3 interfaces to reuse

Phase 2's `build_prepared_tables` in `src/rossmann_forecasting/data/preparation.py` returns a
source-faithful historical table and a separate future-covariate table after a many-to-one Store
metadata join. The historical table carries `Store`, `Date`, `Sales`, and source `Open`; the
inference covariate table has no `Sales` or `Customers`. Prepared tables preserve source keys and
sparse coverage. Phase 2's `derive_test_open_resolution` is audit-only; its uncertain candidate
must not replace source `Open` or determine evaluation eligibility.

Phase 3's `canonicalize_store_date_keys` and date-normalization helpers provide validated exact
Store × Date keys. `build_origin_history_features` accepts `actual_history_through_origin`, rejects
actuals after the declared origin, and can accept earlier recursive predictions. It documents the
correct information boundary, though Phase 4 may use a smaller exact-date lookup for this baseline.
Do not reuse precomputed historical `sales_lag_7` values for validation targets after an origin:
those one-step historical features may contain actual Sales that were still in the future at that
validation origin. The baseline must construct each origin's history from actuals available through
that origin, then use only predictions made earlier in that same forecast run.

Phase 4 must not alter Phase 2 or Phase 3 interfaces, the `phase-3-v1` contract, or the prepared
inputs. Raw and interim data remain immutable.

## 5. Proposed development validation windows

**PROPOSED / REQUIRES USER APPROVAL.** The final holdout boundary remains fixed at 2015-07-04.

| Window | Forecast origin | Target dates | Calendar days |
|---|---|---|---:|
| Validation 1 | 2015-05-22 | 2015-05-23 through 2015-06-05 | 14 |
| Validation 2 | 2015-06-05 | 2015-06-06 through 2015-06-19 | 14 |
| Validation 3 | 2015-06-19 | 2015-06-20 through 2015-07-03 | 14 |

The target windows are chronologically ordered and non-overlapping. Each begins the calendar day
after its origin; the next origin is the prior window's final target date, so each later origin may
use the expanded actual history available by that date. The final target window ends immediately
before the protected 2015-07-04–2015-07-31 holdout. The three target ranges were verified
mechanically against the historical calendar using only its `Date` column: every origin is present,
and each requested range contains exactly the 14 expected consecutive dates. No Sales values,
forecast outputs, or metrics were read or calculated for this check.

For a later backtest, use only historical Store × Date target keys actually present in the prepared
source within each window; do not create a full Store-by-calendar cross product or synthetic target
labels. This is a proposed target-row universe consistent with source-faithful sparse coverage and
requires approval. Missing target keys have no actual `Open`/`Sales` label and therefore cannot be
silently scored as zero.

Why these windows are proposed: they provide three non-overlapping two-week tests, move forward in
time, allow the actual history to expand at each origin, and finish directly before the untouched
holdout. Do not choose or revise windows based on their eventual forecast performance.

## 6. Proposed 14-day Seasonal Naive semantics

**PROPOSED / REQUIRES USER APPROVAL.** For store `s`, forecast origin `o`, and target calendar date
`d`, use the exact same-Store date `d - 7 calendar days`:

```text
if d - 7 days <= o:
    raw_forecast(s, d) = actual Sales(s, d - 7 days)
else:
    raw_forecast(s, d) = previously generated raw_forecast(s, d - 7 days)
```

Consequently, horizons 1–7 use the exact seven calendar dates immediately preceding or including
the origin, while horizons 8–14 repeat the corresponding already-generated forecasts from horizons
1–7. The second week is recursive: actual Sales revealed inside the 14-day target window never
enters later predictions. In particular, horizon 8 must use the horizon 1 forecast, not actual
Sales at horizon 1 (teacher forcing is rejected).

Lookup is exact by Store and calendar date. If the required `d - 7` source date is absent or its
Sales value is unavailable, the raw forecast is null. Do not search backward for a previous
observed row, interpolate, impute, or replace the missing value with zero. Any later recursive
forecast depending on that unavailable weekly value is also null. An observed `Sales == 0` on the
exact weekly source date is a valid value and yields a raw forecast of zero.

Generate the raw 14-day sequence independently for each store and origin. State transitions between
validation windows are walk-forward: at a later origin, actual observations through that new origin
are available. Within a single origin's 14-day run, only the origin-censored actual history and
earlier predictions from that run are available.

## 7. Proposed raw and operational forecast separation

**PROPOSED / REQUIRES USER APPROVAL.** Keep model quality separate from business routing:

- `raw_baseline_forecast` is the pure Seasonal Naive result from Section 6. It is generated without
  consulting target-date `Open` and is retained unchanged for evaluation.
- `operational_forecast` applies the known-closed rule after the raw forecast is generated:
  - source `Open == 0` → `0`, even if the raw forecast is unavailable;
  - source `Open == 1` → the raw forecast, including null if raw history is unavailable;
  - missing/unknown source `Open` → null, never silently treated as closed.
- For historical validation, source target-date `Open` is an evaluation/routing attribute attached
  after raw predictions have been generated; it is never a predictor or input to the raw rule.
  `Open_resolved` remains uncertain audit data and cannot establish known-open/known-closed status.
- In a future operational application, zero routing is permitted only when target-date closure is
  known from an approved source; this design does not authorize inferring closure from unknown
  `Open`.

Define `forecast_available` as whether `raw_baseline_forecast` is non-null. If useful for audit,
also emit `operational_forecast_available`; do not overload raw forecast availability with the
closed-store zero rule. Primary model metrics use raw forecasts on open rows; on those rows the
operational forecast equals the raw forecast whenever available.

## 8. Proposed evaluation eligibility and coverage

**PROPOSED / REQUIRES USER APPROVAL.** A primary-evaluation row must satisfy all of the following:

1. Its target date lies in one of the approved development windows.
2. The observed source target-date `Open` equals 1.
3. Actual target `Sales` is present.
4. The raw Seasonal Naive forecast is available.

Preserve every observed target row in forecast outputs, including closed, unknown-Open, and
unavailable-forecast rows. Do not delete closed rows to make metrics easier. Closed and unknown
rows are excluded from primary forecasting metrics; known-closed rows still retain their
operational zero. Uncertain `Open_resolved` candidates are not evaluation truth.

Report raw-forecast availability coverage so missing predictions cannot disappear silently. At a
minimum, report available raw forecasts divided by observed historical target rows in each
window, plus available raw forecasts divided by observed `Open == 1` rows with actual Sales. State
both numerator and denominator. Primary metric eligibility is then the intersection of observed
open labels and available raw forecasts. Coverage is descriptive; it must not be used to select a
window or change missing-history semantics based on performance.

No final-holdout forecast, evaluation, or result is allowed in Phase 4.

## 9. Proposed metric contract

**PROPOSED / REQUIRES USER APPROVAL.** Use the primary eligible population from Section 8. For
each validation window, for pooled development rows across the three windows, and by forecast
horizon `h = 1..14`, calculate:

- **MAE (primary):** `mean(abs(actual_sales - raw_baseline_forecast))` over eligible rows.
- **RMSE:** `sqrt(mean((actual_sales - raw_baseline_forecast) ** 2))` over the same eligible rows.
- **MAPE (caution):** calculate only on primary-eligible rows with `actual_sales > 0`, as
  `mean(abs(actual - forecast) / actual) * 100`. Do not add epsilon or alter zero Sales. Report the
  count of primary-eligible zero-actual rows excluded from MAPE, the MAPE denominator row count,
  and MAPE coverage (`positive-actual MAPE rows / primary-eligible rows`). If there are no positive
  actual rows, return null with an explicit unavailable reason.
- **WAPE:** `sum(abs(actual_sales - raw_baseline_forecast)) / sum(actual_sales)` over the primary
  eligible rows. If the actual-Sales denominator is zero, return null with a clear reason; never
  divide by zero or add an epsilon.

For the pooled result, concatenate the eligible observations from the approved development windows
and compute each metric over that pooled row set; do not substitute an unweighted average of
window-level metrics. For horizon results, apply the same definitions to eligible rows with that
horizon. Record row counts and availability coverage alongside metrics. MAE remains the primary
comparison metric; MAPE and WAPE are not replacements for it.

## 10. Proposed forecast record and field roles

**PROPOSED / REQUIRES USER APPROVAL.** Use one auditable record per observed target Store × Date
and forecast origin. The proposed composite key is `(Store, forecast_origin, Date)`; `horizon` is
also stored and checked against the date difference. The same Store × Date may appear at distinct
origins only if the approved windows ever overlap (the current proposal does not overlap).

| Field | Proposed role and timing |
|---|---|
| `Store` | Key; unchanged source store identity. |
| `forecast_origin` | Key/audit field; date at which the forecast information set is cut off. |
| `Date` | Key; forecast target date. |
| `horizon` | Forecast audit field; integer calendar lead `1..14`, not an independent key. |
| `raw_baseline_forecast` | Forecast output; pure recursive weekly Seasonal Naive. |
| `operational_forecast` | Forecast output after known-closed routing; unknown Open stays null. |
| `actual_sales` | Label joined only after raw forecasts are generated; never a forecast input for dates after origin. |
| `source_open` | Evaluation/routing audit field joined after raw generation; not a predictor. |
| `forecast_available` | Audit flag for non-null raw forecast. |
| `operational_forecast_available` | Optional audit flag, distinct from raw availability and useful when Open is unknown. |
| `primary_evaluation_eligible` | Evaluation mask derived from window membership, source Open, actual Sales availability, and raw forecast availability. |
| `validation_window` | Evaluation/audit label, e.g. `validation_1`, `validation_2`, or `validation_3`. |

No `Customers`, Customers-derived field, future-actual predictor, model feature, or holdout result
belongs in this record. Keep forecast generation and post-forecast label/routing joins as separate
steps so evaluation labels cannot influence raw predictions.

## 11. Final-holdout firewall

The final holdout remains 2015-07-04 through 2015-07-31. During Phase 4 development, its Sales,
forecast errors, metric distributions, and performance must not be inspected or used to:

- change Seasonal Naive or recursive semantics;
- choose or revise development windows based on performance;
- choose missing-history behavior;
- choose metric or eligibility rules;
- decide Open routing;
- compare variants, inspect performance, or report forecast metrics.

Prefer no holdout contact in Phase 4. If a later implementation requires a check, it must be
strictly mechanical (date boundary, key uniqueness, schema compatibility, or row integrity) and
must not summarize targets, forecasts, or their distributions. No holdout forecast or evaluation
command is in this phase's scope. The three proposed validation windows end on 2015-07-03.

## 12. Required tests after design approval

Use compact synthetic fixtures; no real Sales values are needed for unit tests.

| ID | Test requirement |
|---|---|
| A | Exact weekly lookup: a target uses the same Store's exact `d - 7` calendar date. |
| B | Missing exact weekly date returns null; no previous-observed-row fallback. |
| C | Fourteen-day recursion: horizon 8 uses the horizon 1 forecast, not actual Sales from horizon 1. |
| D | Teacher-forcing guard: mutating actual Sales after an origin cannot change that origin's 14-day raw forecast. |
| E | Store histories are isolated; another Store's exact date/value cannot satisfy a lookup. |
| F | Known `Open == 0` makes operational forecast zero without changing raw forecast. |
| G | Known `Open == 1` retains raw forecast as operational forecast. |
| H | Missing/unknown `Open` is not treated as closed; operational forecast remains unresolved/null. |
| I | Primary metrics use only actual source `Open == 1` rows with observed Sales and available raw forecast. |
| J | MAPE excludes actual Sales equal to zero only from MAPE and reports the exclusion and denominator. |
| K | WAPE returns null/unavailable with a reason when its actual-Sales denominator is zero. |
| L | Missing raw forecasts are excluded only by the approved availability rule and coverage is reported. |
| M | Validation ranges are exactly 14 days, chronologically ordered, non-overlapping, and end before the holdout. |
| N | No future Customers or post-origin actual Sales enters forecast inputs; verify by input/schema checks and a post-origin Sales mutation guard. |
| O | Forecast construction and evaluation do not mutate supplied DataFrames. |

Also test output-key uniqueness, horizon/date consistency, null propagation through recursive
weekly dependencies, observed zero Sales as a valid raw value, metric empty-population behavior,
and that labels/Open are attached only after the raw forecast stage. No test may calculate
performance on the final holdout.

## 13. Proposed implementation sequence after approval

1. Record explicit user approval and resolve any requested changes in this plan before coding.
2. Add a small reusable forecaster that canonicalizes keys, takes actual history through one origin,
   performs exact same-Store `d - 7` lookups, and feeds only earlier raw predictions into recursive
   steps.
3. Add reusable, population-explicit metric functions and coverage summaries.
4. Add a rolling-origin evaluator over only the approved development windows. Generate raw forecasts
   before attaching target Sales/Open; preserve every observed target row and output eligibility
   fields.
5. Add a thin script only if useful, deterministic local outputs, and synthetic unit tests. Keep
   generated results out of Git unless explicitly required by repository policy.
6. Run tests, Ruff, schema/leakage checks, and inspect the complete diff. Record only commands
   actually run in `docs/PROGRESS.md`.
7. Do not access final-holdout outcomes. Update `docs/DECISIONS.md` only for choices explicitly
   approved as durable decisions; never record this proposal as accepted before approval.

## 14. Approval checklist and open methodology questions

All entries in Sections 5–10 are **PROPOSED / REQUIRES USER APPROVAL**, not accepted decisions.
Explicitly confirm or amend:

1. The three exact validation origins and target windows.
2. The exact-date `d - 7` recursion for horizons 8–14, rejection of teacher forcing, and null
   propagation when weekly history is missing.
3. Separate raw and operational forecasts, including routing for known-closed and unknown-Open
   rows.
4. Use of only observed historical target Store × Date keys (no synthetic target grid), plus the
   evaluation eligibility and availability-coverage denominators.
5. MAE/RMSE/MAPE/WAPE formulas, zero handling, per-window/pooled/horizon reporting, and MAPE
   coverage definition.
6. The proposed forecast record, field roles, and post-forecast attachment of labels/routing data.

There is one additional operational clarification for approval: the source is sparse, so the target
row universe and the forecast-availability coverage denominator must remain explicit. This plan
proposes observed historical Store × Date target keys and reports both all-observed-target coverage
and open-labelled-target coverage; no absent Store × Date row is synthesized or treated as a
failure/zero. No other contradiction with the approved project constraints was identified during
planning. Phase 4 remains PLANNING / DESIGN REVIEW until the user explicitly approves the design.
