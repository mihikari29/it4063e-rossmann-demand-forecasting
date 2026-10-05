# Phase 4 — Seasonal Naive Baseline (Design and Execution Plan)

**Status:** COMPLETE. The design was explicitly approved by the user on 2026-10-05; implementation
was reviewed and merged in PR #5. This completed plan preserves the design, implementation, and
development-result history.

## 1. Objective and current state

Phase 4 establishes the required weekly Seasonal Naive benchmark for 14-day, store-level
monetary Rossmann `Sales` forecasting. This document records the approved validation windows,
multi-step semantics, operational routing, evaluation population, metrics, output record, test
coverage, and implementation boundary so later work does not invent methodology.

Phase 3 is COMPLETE on `main`. The implementation was merged in PR #3; its formal documentation
closeout is also merged on `main` at `c016c4e3a2c33da278ebdbbe074b3e1d4f13fe70`. The completed
Phase 3 plan is `plans/completed/phase-3-feature-engineering.md`. The approved Phase 4 baseline,
development evaluator, tests, and real-data development results were reviewed and merged in PR #5;
this plan is archived under `plans/completed/` following formal closeout.

The user has approved the methodology in this plan, including the sparse-label/internal-path
clarification in Section 5. Durable decisions are recorded as ADR-013. Implementation is limited
to these approved choices; any material change requires renewed review.

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

## 5. Approved development validation windows

**APPROVED.** The final holdout boundary remains fixed at 2015-07-04.

| Window | Forecast origin | Target dates | Calendar days |
|---|---|---|---:|
| `validation_1` | 2015-05-22 | 2015-05-23 through 2015-06-05 | 14 |
| `validation_2` | 2015-06-05 | 2015-06-06 through 2015-06-19 | 14 |
| `validation_3` | 2015-06-19 | 2015-06-20 through 2015-07-03 | 14 |

The target windows are chronologically ordered and non-overlapping. Each begins the calendar day
after its origin; the next origin is the prior window's final target date, so each later origin may
use the expanded actual history available by that date. The final target window ends immediately
before the protected 2015-07-04–2015-07-31 holdout. The three target ranges were verified
mechanically against the historical calendar using only its `Date` column: every origin is present,
and each requested range contains exactly the 14 expected consecutive dates. No Sales values,
forecast outputs, or metrics were read or calculated for this check.

### Approved distinction: internal forecast path vs. observed target rows

Emit and evaluate only Store × Date target keys actually present in the source validation window.
Do not synthesize Store × Date label rows, fake `Open`, or treat absent target rows as zero Sales.
However, for every Store with at least one observed target row in a window, internally construct
the complete calendar path `h = 1..14`. An intermediate date without an observed target key still
gets an internal forecast state, with no target label; that state may feed a later recursive
forecast. For example, if h=1 has no observed target row but h=8 does, generate internal h=1 from
origin-safe history and use that forecast for h=8. Only the observed h=8 key is emitted/scored.
Internal states are ephemeral forecast state, not synthetic labels or evaluation records.

Why these windows were selected: they provide three non-overlapping two-week tests, move forward in
time, allow the actual history to expand at each origin, and finish directly before the untouched
holdout. Do not choose or revise windows based on their eventual forecast performance.

## 6. Approved 14-day Seasonal Naive semantics

**APPROVED.** For store `s`, forecast origin `o`, and target calendar date
`d`, use the exact same-Store date `d - 7 calendar days`:

```text
if d - 7 days <= o:
    raw_forecast(s, d) = actual Sales(s, d - 7 days)
else:
    raw_forecast(s, d) = previously generated raw_forecast(s, d - 7 days)
```

Consequently, h=1 uses actual Sales at `o-6`, h=2 at `o-5`, through h=7 at `o`; horizons 8–14 use
the previously generated forecasts at h=1–7 respectively. The second week is recursive: actual
Sales revealed inside the 14-day target window never enters later predictions. In particular,
horizon 8 must use the horizon 1 forecast, not actual Sales at horizon 1 (teacher forcing is
rejected).

Lookup is exact by Store and calendar date. If the required `d - 7` source date is absent, the raw
forecast is null. Do not search backward for a previous observed row, interpolate, impute, or
replace the missing value with zero. Any later recursive forecast depending on that unavailable
weekly value is also null. An observed `Sales == 0` on the exact weekly source date is valid and
yields a raw forecast of zero. The public API rejects null, non-finite, or negative Sales values in
the supplied actual-history frame; a missing exact Store × Date key is represented as unavailable.

Generate the raw 14-day sequence independently for each store and origin. State transitions between
validation windows are walk-forward: at a later origin, actual observations through that new origin
are available. Within a single origin's 14-day run, only the origin-censored actual history and
earlier predictions from that run are available.

## 7. Approved raw and operational forecast separation

**APPROVED.** Keep model quality separate from business routing:

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

## 8. Approved evaluation eligibility and coverage

**APPROVED.** A primary-evaluation row must satisfy all of the following:

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

## 9. Approved metric contract

**APPROVED.** Use the primary eligible population from Section 8. For
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

## 10. Approved forecast record and field roles

**APPROVED.** Use one auditable record per observed target Store × Date and forecast origin. The
composite key is `(Store, forecast_origin, Date)`; `horizon` is also stored and checked against the
date difference. The approved validation windows do not overlap.

| Field | Role and timing |
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
command is in this phase's scope. The three approved validation windows end on 2015-07-03.

## 12. Required tests for the approved design

Use compact synthetic fixtures; no real Sales values are needed for unit tests.

| ID | Test requirement |
|---|---|
| A | Exact `d - 7` same-Store calendar-date lookup. |
| B | Missing exact weekly date returns null; a previous observed date cannot substitute. |
| C | Exact-history `Sales == 0` remains a valid raw forecast. |
| D | Horizon 8 uses the internally generated horizon 1 forecast, not actual horizon 1 Sales. |
| E | Horizon 14 uses the internally generated horizon 7 forecast. |
| F | Mutating actual target-window Sales cannot change raw forecasts from the same origin. |
| G | An actual-history row after forecast origin is rejected. |
| H | Store histories are isolated; another Store cannot satisfy a lookup. |
| I | Fractional or invalid Store keys are rejected through shared key validation. |
| J | Caller-owned inputs are not mutated. |
| K | Mutating target-window Open cannot change raw forecasts. |
| L | `Open == 0` routes operational forecast to zero without changing raw forecast. |
| M | `Open == 1` routes operational forecast to raw forecast. |
| N | Unknown Open remains unresolved and does not route to zero. |
| O | Primary metrics exclude closed rows while retaining eligible open zero-Sales rows. |
| P | MAPE excludes zero actuals only from MAPE and reports counts/coverage. |
| Q | WAPE zero denominator returns null with an explicit reason. |
| R | Empty eligible metric population has explicit null/reason behavior. |
| S | Three validation windows are exactly 14 days and finish before the holdout. |
| T | Emitted forecast rows contain only observed target Store × Date keys. |
| U | An observed h=8 target with no h=1 label uses its internally generated h=1 state. |
| V | Future Customers and future actual Sales do not enter forecast inputs. |
| W | Output composite keys are unique and horizon agrees with date minus origin. |

Also test output-key uniqueness, horizon/date consistency, null propagation through recursive
weekly dependencies, observed zero Sales as a valid raw value, metric empty-population behavior,
and that labels/Open are attached only after the raw forecast stage. No test may calculate
performance on the final holdout.

## 13. Approved implementation sequence

1. Add a small reusable forecaster that canonicalizes keys, takes actual history through one origin,
   performs exact same-Store `d - 7` lookups, and feeds only earlier raw predictions into recursive
   steps.
2. Add reusable, population-explicit metric functions and coverage summaries.
3. Add a rolling-origin evaluator over only the approved development windows. Generate raw forecasts
   before attaching target Sales/Open; preserve every observed target row and output eligibility
   fields.
4. Add a thin script only if useful, deterministic local outputs, and synthetic unit tests. Keep
   generated results out of Git unless explicitly required by repository policy.
5. Run tests, Ruff, schema/leakage checks, and inspect the complete diff. Record only commands
   actually run in `docs/PROGRESS.md`.
6. Do not access final-holdout outcomes. Update `docs/DECISIONS.md` only if an explicitly approved
   durable decision requires a superseding record.

## 14. Approval record and implementation clarifications

The user explicitly approved all choices in Sections 5–10 on 2026-10-05. These decisions are
recorded in ADR-013. The sparse target-row / internal-path clarification is part of the approval:
emit only observed historical target keys, but internally forecast h=1..14 for each Store with at
least one observed target row. Internal forecast states have no labels and are not emitted unless
the corresponding target key exists.

Implementation-time constraints: the real-data runner filters historical inputs to dates no
later than 2015-07-03 before any forecast/evaluation code can access target Sales; raw forecasts
are generated from keys plus origin-censored Sales only, and target Sales/Open labels are joined
afterward; the final holdout is not forecast or evaluated. No further methodology question
is unresolved. At the implementation checkpoint, the plan remained active and Phase 4 remained
IMPLEMENTED / UNDER REVIEW pending external review and explicit closeout; the closeout is recorded
in Section 16 below.

## 15. Implementation execution record (2026-10-05)

- Implemented reusable logic in `src/rossmann_forecasting/forecasting/`: exact weekly Seasonal
  Naive forecasts with recursive h=8..14 state, post-forecast Open routing and label attachment,
  approved development-window evaluation, pooled/window/horizon metrics, and explicit coverage.
- Added the `rossmann-seasonal-naive` project command and `scripts/run_seasonal_naive.py`. The
  runner validates raw and Phase 2 provenance, reads only Store/Date/Sales/Open through
  2015-07-03, evaluates only the three approved windows, and writes deterministic Git-ignored
  outputs under `data/processed/seasonal_naive/`.
- Added synthetic tests for exact and missing calendar lookup, recursive values and nulls, sparse
  observed targets, Store isolation, target-label/Open independence, routing, metric populations,
  zero handling, coverage, and forecast-key/horizon consistency.
- The real-data run emitted 46,830 observed development targets: 15,610 in each window. Raw
  availability was 46,830/46,830 overall and 100% among Open=1 labelled targets in every window;
  no raw forecasts were unavailable. Primary eligible rows were 11,678, 13,438, and 13,437 by
  window. Window MAE was 1,101.5940, 2,269.7721, and 1,596.5170; pooled MAE was 1,681.2703.
  Full metric tables and all horizon-level results are in `docs/PROGRESS.md`.
- The runner reported input provenance unchanged before/after execution. No final-holdout forecast,
  score, metric, or summary was produced. At this implementation checkpoint Phase 4 was
  IMPLEMENTED / UNDER REVIEW and the plan remained active; both were subsequently closed as
  recorded below.

## 16. Formal Phase 4 closeout

- The Phase 4 methodology was approved by the user and recorded in ADR-013.
- External review found no blocking issue. PR #5, “feat: implement Phase 4 seasonal naive
  baseline,” received final approval and merged into `main` at
  `12f80b5fe8a8580b3d8367cd473766decd3ebf31`.
- The final implementation suite had **73 tests passed**. The real-data development runner
  succeeded on the three approved windows; all **46,830 / 46,830** observed validation targets had
  available raw forecasts.
- Pooled development metrics remain MAE **1,681.2703**, RMSE **2,416.9677**, MAPE **26.2671%**,
  and WAPE **0.232748**. Per-window and horizon results remain recorded in `docs/PROGRESS.md`;
  they are not recalculated or reinterpreted here.
- The final holdout, 2015-07-04 through 2015-07-31, remained unevaluated: no holdout forecast,
  score, metric, or outcome summary was produced.
- Phase 4 is formally **COMPLETE**. This execution plan is archived under `plans/completed/`.
  Phase 5 planning is separate and no Phase 5 implementation is included in this closeout.
