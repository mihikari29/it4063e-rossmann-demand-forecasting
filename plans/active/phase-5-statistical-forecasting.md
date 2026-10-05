# Phase 5 — Statistical Forecasting (Design and Execution Plan)

**Status:** IMPLEMENTED / UNDER REVIEW. The user explicitly approved the Phase 5 methodology on
2026-10-05. The accepted design is recorded in ADR-014. Implementation and the development-only
evaluation are complete; this plan remains active for external review and explicit closeout.

## 1. Objective and current state

Phase 4 is COMPLETE. Its Seasonal Naive implementation and development evaluation were merged in
PR #5; formal closeout was merged in PR #6. The Phase 4 plan is archived at
`plans/completed/phase-4-seasonal-naive.md`, and accepted ADR-013 remains the source of truth for
the fixed windows, baseline, routing, eligibility, and metric contract.

Phase 5 evaluates one classical additive Holt-Winters candidate against the reviewed Seasonal
Naive implementation on the same three development windows. This phase evaluates a fixed candidate,
not the final project model. At the original approval checkpoint no statistical model had been
fitted or forecast; the implementation results are recorded in Section 15. The final holdout remains
untouched.

## 2. Fixed project constraints — already accepted

These constraints are inherited from the proposal and earlier accepted phases; this plan does not
reopen them:

- Unit: Store × Date. Target: monetary Rossmann `Sales`; this is not SKU or physical-unit demand.
- Primary horizon: 14 calendar days.
- Use exactly the approved, chronological Phase 4 development windows and compare to Seasonal
  Naive on those same origins and target dates:

  | Window | Forecast origin | Target dates |
  |---|---|---|
  | `validation_1` | 2015-05-22 | 2015-05-23 through 2015-06-05 |
  | `validation_2` | 2015-06-05 | 2015-06-06 through 2015-06-19 |
  | `validation_3` | 2015-06-19 | 2015-06-20 through 2015-07-03 |

- Final holdout: 2015-07-04 through 2015-07-31; it remains unevaluated and inaccessible to model
  fitting, validation, tuning, or reporting in this phase.
- Primary metric: MAE. Also report RMSE, MAPE with the approved caution/zero handling, and WAPE.
- Primary metric population: observed target rows with actual source `Open == 1`, observed Sales,
  and an available raw forecast.
- Preserve the Phase 4 raw-forecast versus operational-forecast separation. After raw forecast
  generation, known source `Open == 0` routes operational output to zero; `Open == 1` routes to the
  raw output; unknown Open routes to null.
- Future actual Sales and future Customers are prohibited as forecast inputs. No random shuffling.
- Recompute Seasonal Naive through the reviewed Phase 4 implementation for comparisons; do not
  depend on a pre-existing generated forecast artifact or change the Phase 4 algorithm.

The Phase 4 zero-handling contract is unchanged: MAPE uses only eligible rows with actual Sales
greater than zero, adds no epsilon, and reports excluded-zero counts and coverage. WAPE is null
with a reason if the eligible actual-Sales denominator is zero. Pooled metrics are calculated on
the pooled eligible rows, not as averages of window metrics.

## 3. Approved primary model

**APPROVED:** one classical additive Holt-Winters model per Store and forecast origin, with this
fixed structure:

| Component | Approved setting |
|---|---|
| Level | Estimated |
| Trend | Additive |
| Damped trend | False |
| Seasonality | Additive |
| Seasonal period | 7 observations on a regular daily series (seven calendar days) |
| Initialization | Estimated |
| Smoothing parameters | Estimated from that origin-censored training series during ordinary fitting |
| Exogenous inputs | None |
| Transformation | None; specifically no Box-Cox transformation |

Conceptually, `Sales_t = Level_t + Trend_t + WeeklySeasonality_t + Error_t`. The proposal calls
for level, trend, and weekly seasonality. Additive Holt-Winters is the simplest transparent
statistical implementation of those components. Observed Sales can equal zero, so multiplicative
seasonality is unsuitable for this primary candidate. The structure is fixed before validation
performance is observed: do not compare additive with multiplicative, damped with undamped, or
other structural variants by metrics in this planning task or tune structure from development
results.

Do not include Open, promotions, calendar fields, store metadata, future-known regressors, or
other Phase 3 features in this univariate candidate.

## 4. Approved daily series and sparse-history contract

**APPROVED:** fit on a regular daily calendar series built only from observed source Store × Date
rows and Sales available at or before the forecast origin.

- Include observed closed-store rows and their observed Sales values, including Sales equal to
  zero. Do not remove `Open == 0` rows, compress the index to business days, use Open as a
  regressor, fill absent dates with zero, or interpolate.
- Do not bridge source gaps or combine an older pre-gap segment with a newer post-gap segment.
- For each Store and origin, use the most recent contiguous observed daily Sales segment ending
  exactly at the origin. Eligibility requires an observed Store row on the origin and one observed
  Store × Date row for each consecutive calendar date in the segment. Every included Sales value
  must be finite and non-negative. A missing date or unusable Sales value ends the usable segment;
  do not skip it or bridge it.
- If there is no observed row for the Store at the origin, history length is zero and a forecast
  is unavailable.
- Minimum eligibility is **28 consecutive daily observations ending at the origin**, corresponding
  to four complete weekly cycles.
- Use the entire most-recent contiguous segment when eligible, not a fixed 28-day lookback. Thus,
  28 days is only the minimum; if 300 contiguous daily observations end at the origin, use all 300.
  Do not select a lookback length using validation performance.

Source `Open` is post-forecast evaluation/routing information only. It does not determine the
training series or whether the model fits.

### Date-only history-availability audit

This mechanical audit used `data/processed/features_train.parquet` as the source of observed
Store × Date keys, projected only the `Store` and `Date` columns, and filtered Date to no later
than 2015-07-03 before calculating runs. No Sales, Open, Customers, forecast, or metric values
were read for the audit; the audit output contains only development dates through the cutoff. A
contiguous run was counted backward from the origin only
when that Store had an observed origin key; target Stores were the unique Stores with at least one
observed target key in the respective window.

| Window | Target Stores | Origin-row Stores | ≥28 days | 14–27 days | 7–13 days | 2–6 days | 0–1 day | Eligible ≥28 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `validation_1` | 1,115 | 1,115 | 1,115 | 0 | 0 | 0 | 0 | 1,115 / 1,115 (100.00%) |
| `validation_2` | 1,115 | 1,115 | 1,115 | 0 | 0 | 0 | 0 | 1,115 / 1,115 (100.00%) |
| `validation_3` | 1,115 | 1,115 | 1,115 | 0 | 0 | 0 | 0 | 1,115 / 1,115 (100.00%) |

This is a calendar/history-availability result only. Under the proposed threshold, the audit shows
no date-history eligibility loss in these windows, so insufficient history alone does not appear
to create a material coverage issue or require a fallback design. It does not establish that Sales
is usable or that a statistical fit will succeed; numerical fit failures and resulting forecast
coverage have not been measured.

## 5. Approved forecasting semantics

**APPROVED:** for each Store with at least one observed target key in a window:

1. Censor the Store's historical input at the window's forecast origin.
2. Extract the eligible most-recent contiguous daily segment defined in Section 4.
3. Fit one fixed additive Holt-Winters model on that series only.
4. From that single fitted model, issue one 14-step calendar forecast operation, producing all
   internal states for horizons `h = 1..14`.
5. Do not refit within the target window and do not insert actual target-window Sales into the
   series. This is genuine multi-step forecasting; unlike the later LightGBM design, it requires
   neither recursive target-window actual insertion nor ML lag features.
6. Emit evaluation records only for source-observed target Store × Date keys. The full 14-step
   model path is internal; missing target keys are not synthesized as labels or records.

Generate raw forecasts without target Sales or Open attached. Attach observed target Sales, source
Open, and the validation-window label only after raw forecast generation has completed.

## 6. Approved unavailable-forecast and fallback policy

**APPROVED; NO FALLBACK:**

```text
if contiguous origin-ending history has at least 28 daily rows:
    fit the fixed additive Holt-Winters candidate
else:
    statistical forecast unavailable

if model fitting or forecasting fails numerically:
    statistical forecast unavailable; record the failure reason
```

Do not silently fall back to Seasonal Naive: it is Model 0 and using it as a fallback would blur
the candidate comparison. Do not fall back to Holt or Simple Exponential Smoothing. The date-only
audit finds no Stores below the proposed history threshold, so there is no date-availability
evidence requiring a short-history fallback. Numerical failure prevalence is unknown until an
approved implementation is run. Keep failures explicit and coverage visible; if numerical
failures later appear material, return for design review rather than silently changing the model
contract.

For emitted rows without an available forecast, preserve the row and set forecast values to null,
`forecast_available` false, `model_fit_success` false, and an explicit `fit_failure_reason` such
as `insufficient_contiguous_history` or a sanitized numerical-failure category/detail. A successful
fit has a null failure reason. Do not treat a skipped fit due to insufficient history as a fit
attempt.

## 7. Approved non-negative forecast and Open-routing policy

Additive Holt-Winters may produce negative values even though Sales is non-negative.

**APPROVED:** preserve both values:

- `model_forecast_unclipped`: the direct numeric model output;
- `raw_statistical_forecast`: `max(0, model_forecast_unclipped)`, the business-feasible forecast
  used for primary metrics and the raw statistical comparison.

Retain a per-record clipping flag. For unavailable forecasts, that flag is null because no value
was available to clip. Report clipping count and minimum unclipped forecast as window-level and
pooled diagnostics, without using them to tune the model. Clipping is a fixed target-domain
constraint, not validation-based tuning.

After raw forecast generation, apply the inherited Phase 4 operational rule:

| Target source Open | `operational_forecast` |
|---|---|
| `0` | `0`, even when raw statistical forecast is unavailable |
| `1` | `raw_statistical_forecast`, including null when unavailable |
| Unknown | Null; do not infer closure |

Do not use operationally routed forecasts as model-quality inputs. Primary metrics use the clipped
raw statistical forecast on the Phase 4-compatible open-label population.

## 8. Approved fitting implementation and dependency

Use `statsmodels.tsa.holtwinters.ExponentialSmoothing`, configured as:

```python
ExponentialSmoothing(
    daily_sales,
    trend="add",
    damped_trend=False,
    seasonal="add",
    seasonal_periods=7,
    initialization_method="estimated",
    use_boxcox=False,
).fit(optimized=True)
```

The model's smoothing-parameter optimization is ordinary per-origin model fitting against the
origin-censored training series, not validation hyperparameter tuning. The approved runtime bound
is `statsmodels>=0.15,<0.16`; no other direct dependency is added solely for a transitive need.

The project requires Python `>=3.14,<3.15` (current environment: Python 3.14.5), with hand-managed
runtime dependency bounds in `pyproject.toml`. The external design review verified statsmodels
0.15.0 supports Python 3.14 and provides CPython 3.14 Windows wheels. Preserve the project's
Python bound and resolve/install the approved dependency through the normal project workflow.

## 9. Approved output contract

**APPROVED:** emit one auditable row per observed target Store × Date, Store, and forecast origin,
with at least:

| Field | Role / semantics |
|---|---|
| `Store`, `forecast_origin`, `Date` | Composite forecast key; Date is an observed target key. |
| `horizon` | Integer calendar lead `Date - forecast_origin`, 1 through 14. |
| `statistical_model` | Fixed model identifier, e.g. `holt_winters_additive_weekly`. |
| `training_history_start`, `training_history_end` | Endpoints of the usable contiguous fit series; unavailable if no fit series. |
| `training_history_rows` | Number of consecutive source Sales observations passed to the fit. |
| `model_fit_success` | Whether fitting/forecast generation succeeded for this Store-origin. |
| `fit_failure_reason` | Null on success; explicit reason when unavailable. |
| `model_forecast_unclipped` | Direct model value for this horizon. |
| `raw_statistical_forecast` | Non-negative clipped value used for metrics; null if unavailable. |
| `forecast_was_clipped` | Nullable flag; true only when the unclipped value is below zero. |
| `operational_forecast` | Post-forecast source-Open routing output. |
| `actual_sales`, `source_open` | Evaluation/routing labels attached only after forecasts are generated. |
| `forecast_available` | Whether `raw_statistical_forecast` is non-null. |
| `primary_evaluation_eligible` | Open=1, observed Sales, and raw statistical forecast available. |
| `validation_window` | One of the three approved window names. |

Do not include Customers, Customers-derived fields, future actuals as predictors, or future-known
feature fields. Validate unique `(Store, forecast_origin, Date)` keys and `horizon == Date -
forecast_origin`. Keep model inputs limited to origin-censored Sales; labels and Open are attached
after forecast generation.

## 10. Approved evaluation and fair baseline comparison

**APPROVED:** retain the Phase 4 definitions and produce two views.

The existing package exposes `forecast_seasonal_naive`,
`build_development_evaluation_records`, and `summarize_forecast_metrics`. The first implements the
reviewed exact-weekly baseline; the development evaluator recomputes it and attaches labels after
forecast generation. Phase 4 metrics originally expected `raw_baseline_forecast`; the Phase 5
implementation reuses the exact metric definitions through a `forecast_column` parameter, with a
regression test proving equivalent outputs when both candidate columns contain the same values.
The Seasonal Naive algorithm remains unchanged, and the comparison does not rely on generated
Phase 4 forecast artifacts.

### A. Standalone Holt-Winters coverage and metrics

Report observed target count, available raw statistical forecast count and coverage, open-label
coverage, and MAE/RMSE/MAPE/WAPE by window, pooled over eligible development rows, and by horizon
`1..14`. Primary evaluation uses observed source `Open == 1`, observed actual Sales, and an
available clipped raw statistical forecast. Match Phase 4 zero handling and metric denominators
exactly. Clearly report unavailable forecasts rather than silently removing them from coverage.

### B. Paired comparison with Seasonal Naive

For each window, pooled development population, and horizon, first restrict to identical target
rows where both the reviewed Seasonal Naive forecast and Holt-Winters forecast are available and
the target is primary-evaluation eligible under the same actual source Open/Sales labels. Report
the paired row count and, for both models on that exact paired population, MAE, RMSE, MAPE, and
WAPE. Also report:

- absolute MAE difference: `Holt-Winters MAE - Seasonal Naive MAE`;
- relative MAE change: `(Holt-Winters MAE - Seasonal Naive MAE) / Seasonal Naive MAE`, with an
  explicit unavailable reason if the Seasonal Naive MAE denominator is zero;
- which model has lower paired MAE.

Recompute the Seasonal Naive forecasts through the already-reviewed Phase 4 implementation for
the same development run; do not depend on a user's generated artifact. Join by the forecast
composite keys and calculate both candidates on identical rows. Do not call Holt-Winters superior
from standalone metrics when its population differs from Seasonal Naive.

## 11. Model-selection boundary and holdout firewall

Phase 5 evaluates this fixed statistical candidate. It does not select the final production model.
Do not modify model structure from development results, tune seasonal period, search ETS variants,
implement Phase 6 Global LightGBM, or declare the project winner. Phase 7 owns model-ladder
selection after LightGBM exists. Phase 5 may report whether this fixed candidate has lower paired
development MAE than Seasonal Naive, with its limitations and coverage.

The protected holdout is 2015-07-04 through 2015-07-31. Any eventual Phase 5 runner must filter
inputs to dates no later than 2015-07-03 before model fitting/evaluation code can access target
outcomes. This planning task performed only a date-only key-availability audit through 2015-07-03.
No holdout Sales, distributions, forecast, or metrics were read or produced.

## 12. Tests required after approval

Use synthetic fixtures; no final-holdout outcomes or real-data model-performance tests are allowed.

| ID | Required test |
|---|---|
| A | Exact origin censoring: fitting history includes no date after the origin. |
| B | Extract the complete most-recent contiguous daily segment ending at the origin. |
| C | A missing calendar date breaks the usable contiguous segment. |
| D | An older pre-gap segment is not bridged into the recent segment. |
| E | No observed Store row on the origin makes statistical history unavailable. |
| F | Minimum-history threshold behavior, including 27 versus 28 consecutive observations. |
| G | The model fit receives only Sales through the origin. |
| H | Mutating target-window Sales cannot change raw statistical forecasts. |
| I | Mutating target Open cannot change raw statistical forecasts. |
| J | Output emits only observed target Store × Date keys. |
| K | The model creates all internal horizons `h=1..14` in one forecast operation. |
| L | Each emitted horizon equals calendar `Date - forecast_origin`. |
| M | Negative forecasts preserve the unclipped value and are clipped only under the approved rule. |
| N | Open routing is separate from raw forecasts; closed/unknown/open cases follow the contract. |
| O | Primary evaluation population matches Phase 4 source-Open rules. |
| P | MAPE and WAPE zero handling remains exactly Phase 4-compatible. |
| Q | Paired comparison uses identical Seasonal Naive/Holt-Winters target rows. |
| R | Fit or forecast failures become explicit unavailable forecasts, never silent fallbacks. |
| S | Caller-owned DataFrames are not mutated. |
| T | No Customers or future actual fields enter model-fitting inputs. |
| U | Validation windows are exactly the Phase 4 windows. |
| V | Final holdout dates are rejected/excluded before fitting and evaluation. |

Also assert output-key uniqueness, fit-series row counts/endpoints, clipping counts/minimum
diagnostics, explicit coverage denominators, and that Sales/Open labels are attached only after raw
forecasts are complete. No test may fit against or calculate performance on holdout outcomes.

## 13. Approved Phase 5 implementation scope

The implementation includes only:

- reusable per-Store, per-origin fixed Holt-Winters fitting and origin-safe 14-step forecasting;
- contiguous-history eligibility and explicit failure diagnostics;
- clipped raw forecasts and post-forecast Open routing;
- Phase 4-compatible standalone evaluation and fair paired Seasonal Naive comparison;
- deterministic ignored development artifacts, focused tests, and a thin runner if useful.

Do not add SARIMA, large ETS searches, validation-driven variant tuning, Global LightGBM, final
model selection, holdout evaluation, uncertainty intervals, inventory simulation, API, or dashboard
in Phase 5.

## 14. Approval record and approved implementation clarifications

The user explicitly approved the methodology in Sections 3–13 on 2026-10-05. The durable contract
is recorded in ADR-014. Additional approved implementation clarifications are:

- Any history ineligibility, model-construction exception, fit exception, forecast exception,
  forecast length other than 14, non-numeric/non-finite forecast, or other unusable model output
  makes that Store-origin forecast unavailable. No fallback model is permitted.
- Record deterministic sanitized failure categories without stack traces in forecast artifacts.
  Capture relevant warnings and aggregate warning/failure counts by category. Record optimizer or
  convergence status separately from forecast availability when the installed result API exposes
  it.
- Before interpreting accuracy, calculate Open-label forecast availability by window. If any
  window is below 99%, produce auditable forecasts, coverage, and diagnostics, mark the result as
  requiring coverage review, report affected Store-origin fits, and suppress comparative
  superiority/inferiority interpretation. If every window is at least 99%, continue to the paired
  comparison. This is a precommitted coverage-quality guardrail, not a tuning parameter.
- Generate Holt-Winters raw forecasts before attaching target Sales, Open, or validation labels;
  target-window Sales and Open mutations must not affect raw statistical forecasts.
- Recompute Seasonal Naive through the reviewed Phase 4 implementation and preserve its algorithm
  and existing metric outputs. Shared/column-aware metric logic must have regression coverage.

No methodology question remains open. Keep this execution plan under `plans/active/` and Phase 5
status at IMPLEMENTED / UNDER REVIEW; do not evaluate the final holdout, archive this plan, or begin
Phase 6.

## 15. Implementation and development results

Implementation is complete on `feat/holt-winters`; Phase 5 is **IMPLEMENTED / UNDER REVIEW**.
Source code, tests, and documentation are ready for external review. This checkpoint does not merge
the branch, archive this plan, or select the final project model.

The runner uses statsmodels 0.15.0 and completed against Phase 2 `train.parquet`. At the Parquet
read boundary it projects Store, Date, Sales, and Open and filters to Date <= 2015-07-03. It
recomputed the Phase 4 Seasonal Naive comparator from the reviewed implementation. The raw Rossmann
and Phase 2 provenance checks passed before and after the run. No final-holdout forecast, score,
target statistic, or metric was produced.

Across the three windows, there were 3,345 Store-origin fits and 46,830 observed target records.
All fits succeeded, all 14-step forecasts were finite, and there were no warnings, failures, or
optimizer non-convergence flags. Forecast availability was 100% both overall and among Open=1
labels in every window, so the approved 99% coverage guardrail passed. The paired comparison
contains 38,553 identical Open=1, observed-Sales, two-model-available rows.

Standalone Holt-Winters metrics on eligible open-label rows:

| Window | Eligible rows | MAE | RMSE | MAPE | WAPE |
|---|---:|---:|---:|---:|---:|
| validation_1 | 11,678 | 1,195.5661 | 1,617.4146 | 15.2155% | 0.155442 |
| validation_2 | 13,438 | 1,136.8306 | 1,483.1660 | 16.9474% | 0.162669 |
| validation_3 | 13,437 | 1,501.5664 | 1,974.7435 | 22.5253% | 0.212929 |
| Pooled | 38,553 | 1,281.7446 | 1,708.3073 | 18.3669% | 0.177439 |

Identical-row paired MAE comparison (difference = Holt-Winters minus Seasonal Naive):

| Population | Paired rows | Holt-Winters MAE | Seasonal Naive MAE | Difference | Relative change | Lower MAE |
|---|---:|---:|---:|---:|---:|---|
| validation_1 | 11,678 | 1,195.5661 | 1,101.5940 | +93.9721 | +8.5306% | Seasonal Naive |
| validation_2 | 13,438 | 1,136.8306 | 2,269.7721 | -1,132.9415 | -49.9143% | Holt-Winters |
| validation_3 | 13,437 | 1,501.5664 | 1,596.5170 | -94.9506 | -5.9474% | Holt-Winters |
| Pooled | 38,553 | 1,281.7446 | 1,681.2703 | -399.5257 | -23.7633% | Holt-Winters |

Holt-Winters had lower paired development MAE in two windows and pooled, while Seasonal Naive was
lower in validation_1. This is a report of the fixed candidates on the approved development rows,
not a declaration of the final model. Clipping affected 1,085 / 46,830 internal forecasts (2.3169%);
the minimum unclipped forecast was -4,175.2857. The minimum is retained for audit and was not used
to tune the model.

Ignored reproducible artifacts are under `data/processed/holt_winters/`, including observed-key
forecasts, full internal paths, per-fit diagnostics, standalone and paired metrics, coverage
guardrail, clipping diagnostics, and a provenance/hash manifest. All 46,830 target keys are unique
and dates end on 2015-07-03.

Validation: full `pytest` suite **95 passed**; Ruff check and format check passed. All planned
artifact destinations passed `git check-ignore`. The final real-data runner completed with exit
code 0. Phase 5 remains under external review; no holdout evaluation, merge, final model selection,
plan archival, or Phase 6 work is included.
