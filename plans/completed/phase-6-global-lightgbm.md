# Phase 6 — Global LightGBM (Design and Execution Plan)

**Status: COMPLETE.** Phase 6 follows the methodology externally reviewed and approved in ADR-019,
integrated into `main` by PR #9 at `79ddb510e94fe5695c4bc17814153fd47695e16f`. The implementation
was reviewed and merged by [PR #10](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/10)
at `dac71d26bd8a9e43eff7d33592460906ae6fee6f`; formal closeout is recorded in section 14.

## 1. Objective, scope, and boundaries

Phase 6 will implement and evaluate exactly one global CPU LightGBM forecasting candidate for the
existing Store × Date monetary Sales target. It will forecast a recursive 14-calendar-day path
using the frozen Phase 3 phase-3-v1 predictor contract. It is a development candidate, not a final
model selection exercise.

The scope is limited to one pooled/global model, the finite recipe below, the three existing
development windows, comparison with recomputed Seasonal Naive and Holt-Winters forecasts, and
reproducible ignored outputs. It adds no predictor, shared feature schema, target transformation,
inventory or synthetic predictor, model family, or business claim. It does not select a winning
project model; Phase 7 owns selection. The protected final holdout (2015-07-04 through 2015-07-31)
is excluded from fitting, tuning, evaluation, diagnostics, and model decisions.

This proposal starts from Phase 5 COMPLETE (PR #7 integration and PR #8 closeout). It does not
change either baseline or its historical results. The governing existing decision for raw recursive
feedback and the known closed-day mismatch is ADR-017.

## 2. Training population and point-in-time boundary

For every fit, use only historical target rows with Date <= forecast_origin and
training_label_eligible == True, which is exactly source Open == 1 and observed Sales.
Observed open-day zero Sales remains a valid fitting label. Select Sales as the sole label and
exactly PREDICTOR_COLUMNS as the model matrix; Date, Open, eligibility fields, row role,
Customers, Open_resolved, resolution/audit fields, and all other columns are excluded.

The label population and history population are intentionally different:

- The model is fitted only on eligible open-store labels.
- Feature history retains **all** observed pre-origin Sales for every store, including closed-day
  zero Sales. It is used only to build the exact lag/rolling state and is not itself a fitting-label
  population.

For an historical fitting row at date d, its dynamic features use actual Sales strictly before d,
as produced by the reviewed Phase 3 historical feature builder. At a model origin, fitting
rows, category vocabularies, and actual history are all censored at that origin. Do not compute
global/full-period statistics or preprocessing from later dates. Do not use the precomputed
teacher-forced historical feature rows as recursive validation inputs.

Use the existing fixed inner tuning origin **2015-04-24**, with recursive targets 2015-04-25 through
2015-05-08. Its fitting labels/history end on April 24. This block ends before the first approved
outer origin (May 22) and target window (May 23 onward). After freezing the selected configuration
and boosting-round count, refit independently at each approved outer origin using eligible labels
and actual history only through that origin. Later outer fits may use then-observed earlier
development labels, but may not retune the recipe.

For inference, supply target-date covariates without target Sales, Customers, or Open to the raw
forecast path. Keep raw-stage inputs in separate projections: historical key/Sales rows through
the fixed origin for fitting and history; future key plus frozen predictors only from origin+1
through the window end; and a key-only requested target list. Sales, Customers, and Open are absent
from the future predictor projection. Only after the complete raw path is emitted may a separate
evaluation-label projection attach target Sales and source Open for scoring/routing. Enforce the
development ceiling 2015-07-03 before model/history/label processing; do not read or summarize
final-holdout outcomes.

## 3. Frozen predictor audit and future availability

The implementation must select the exact following ordered contract from
src/rossmann_forecasting/features/contract.py. This table classifies every predictor without
changing its artifact name, dtype, derivation, or null semantics.

| # | Predictor | Phase 6 role | Origin-time availability / treatment |
|---:|---|---|---|
| 1 | Store | Static identity; categorical | Target key is known. Preserve its integer ID in the shared artifact; treat it as a category only inside this model adapter. |
| 2 | day_of_week | Deterministic calendar | Derived from target Date; known in advance. |
| 3 | week_of_year | Deterministic calendar | ISO week derived from target Date; known in advance. |
| 4 | month | Deterministic calendar | Derived from target Date; known in advance. |
| 5 | quarter | Deterministic calendar | Derived from target Date; known in advance. |
| 6 | year | Deterministic calendar | Derived from target Date; known in advance. |
| 7 | is_weekend | Deterministic calendar | Derived from target Date; known in advance. |
| 8 | is_month_start | Deterministic calendar | Derived from target Date; known in advance. |
| 9 | is_month_end | Deterministic calendar | Derived from target Date; known in advance. |
| 10 | state_holiday | Future-known covariate | Use the supplied/planned target-date holiday calendar under the explicit assumption it is published and available at the origin; never infer it from target outcomes. |
| 11 | school_holiday | Future-known covariate | Use supplied/planned target-date calendar under the explicit assumption it is available at the origin. |
| 12 | promo | Future-known covariate | Use the planned target-date promotion value under the explicit assumption promotion plans are available at the origin. |
| 13 | promo2 | Static participation metadata | Store participation is treated as known from the available static Store metadata snapshot at the origin. |
| 14 | is_promo2_active | Future-known covariate | Derive only from Promo2 schedule metadata and target Date; the schedule is assumed available at the origin. Invalid/incomplete schedules retain contract nulls. |
| 15 | store_type | Static Store metadata; categorical | Use the available Store metadata snapshot, assumed known at the origin. |
| 16 | assortment | Static Store metadata; categorical | Use the available Store metadata snapshot, assumed known at the origin. |
| 17 | competition_distance | Static Store metadata | Use the available CompetitionDistance snapshot, assumed known at the origin; preserve source nulls. |
| 18 | competition_has_opened | Future-known covariate | Derive from opening-month/year metadata and target Date; metadata is assumed known at the origin. Preserve paired-metadata nulls. |
| 19 | competition_age_months | Future-known covariate | Derive from opening-month/year metadata and target Date; metadata is assumed known at the origin. Preserve paired-metadata nulls. |
| 20 | sales_lag_1 | Recursive/history-dependent | Exact same-Store d−1 value from actuals through origin or earlier clipped recursive predictions. |
| 21 | sales_lag_7 | Recursive/history-dependent | Exact same-Store d−7 value from actuals through origin or earlier clipped recursive predictions. |
| 22 | sales_lag_14 | Recursive/history-dependent | Exact same-Store d−14 value from actuals through origin or earlier clipped recursive predictions. |
| 23 | sales_lag_28 | Recursive/history-dependent | Exact same-Store d−28 value from actuals through origin or earlier clipped recursive predictions. |
| 24 | sales_ma_7 | Recursive/history-dependent | Mean over all exact same-Store dates d−7…d−1; requires all seven states. |
| 25 | sales_ma_14 | Recursive/history-dependent | Mean over all exact same-Store dates d−14…d−1; requires all fourteen states. |
| 26 | sales_ma_28 | Recursive/history-dependent | Mean over all exact same-Store dates d−28…d−1; requires all twenty-eight states. |
| 27 | sales_std_7 | Recursive/history-dependent | Sample standard deviation over all exact same-Store dates d−7…d−1; requires all seven states. |
| 28 | sales_std_14 | Recursive/history-dependent | Sample standard deviation over all exact same-Store dates d−14…d−1; requires all fourteen states. |
| 29 | sales_std_28 | Recursive/history-dependent | Sample standard deviation over all exact same-Store dates d−28…d−1; requires all twenty-eight states. |

For this course replay, supplied/planned holiday, school-holiday, promotion-plan, Promo2 schedule,
competition metadata, and static Store metadata used for future target dates are treated as
known/planned at the forecast origin. This is an explicit evaluation/operational assumption, not
historically verified Rossmann information availability. Record that assumption in configuration
and reporting. The future covariate table may contain known/planned calendar, holiday, promotion,
and static metadata only. Open is not a predictor and cannot affect raw fitting or recursion. Even
if future Open is supplied, it is used only after raw-path generation for the separately
routed operational series. Customers, Open_resolved, and historical candidate Open resolutions
are never predictors or raw-state inputs.

## 4. LightGBM adapter, categories, and missingness

Keep phase-3-v1, PREDICTOR_COLUMNS, their order, and shared artifact dtypes unchanged. The
adapter receives only that ordered matrix and performs all model-specific conversion on copies.
Use pandas unordered categorical columns for exactly Store, state_holiday, store_type, and
assortment; keep the original predictor artifact values untouched. All remaining predictors are
numeric, with booleans converted to numeric 0/1 in the adapter. Do not one-hot encode, target
encode, scale, impute, or add missingness features.

For each fit, derive each categorical vocabulary from that fit's **eligible fitting matrix only**.
Use the same learned category lists, in the same order, to construct its training and prediction
matrices. Persist vocabulary values or their ordered hashes in fit metadata. No outer validation
labels/covariates or global full-history category scan may expand a vocabulary.

- An inference Store absent from the fitting vocabulary has no learned identity. Mark that Store's
  requested forecast steps unavailable as unseen_store_category; do not map it to a numeric ID,
  fabricate training rows, or fall back to a baseline.
- An unobserved non-Store category value (state_holiday, store_type, or assortment) is mapped
  to pandas categorical missing using the fitting vocabulary, never added to the vocabulary.
  LightGBM may route it through its learned missing branch; record per-column unseen-category
  counts. This does not change the source artifact.
- Source-null Store, state_holiday, store_type, or assortment violates the Phase 3 required
  field contract and makes that target step unavailable with
  missing_required_covariate:<column>. Do not convert a source null into a sentinel category.
- Also require non-null school_holiday, promo, and promo2 on an existing target feature row;
  missing values in those required binary source fields yield
  missing_required_covariate:<column>. Date/Store key absence is handled as an unavailable/missing
  key, not a nullable predictor. competition_distance, paired competition metadata,
  is_promo2_active, and exact-history predictors retain their documented nullable semantics.
- Preserve numeric NaNs in the adapter. LightGBM's native missing-value handling may consume
  numeric NaNs in competition distance/metadata, invalid-but-audited is_promo2_active, and
  exact-history lag/rolling fields. Convert nullable numeric/Boolean extension values to floating
  values with NaN, not zero. Keep zero_as_missing=false, so real zero Sales history/lag values
  remain zero. Do not impute or rewrite Phase 3 artifacts.
- A missing target Store × Date covariate row is not synthesized. If a requested key is absent,
  record missing_target_key; if an intermediate recursive calendar step lacks a source row,
  record missing_future_covariate_row. Required source covariate values that are missing on an
  existing row yield missing_required_covariate:<column>. Other allowed numeric nulls remain
  native missing values.
- A predictor name/order/dtype mismatch, invalid duplicate key, or categorical conversion/API
  incompatibility is a hard invalid_feature_schema or
  categorical_adapter_incompatibility failure, not an imputation opportunity.

Official LightGBM documentation describes pandas categorical support and native missing-value
handling in [Advanced Topics](https://lightgbm.readthedocs.io/en/latest/Advanced-Topics.html) and
CPU reproducibility controls in [Parameters](https://lightgbm.readthedocs.io/en/latest/Parameters.html).
Implementation must validate those behaviors against the specific locked package version; no
dependency/version is installed or selected by this design task.

## 5. Model, objective, prediction, and recursion

Use one global lightgbm.train CPU GBDT booster shared across stores. Train a single row-level
regression model; do not fit per-store models. The response is untransformed monetary Sales.
Use LightGBM objective regression_l1 (absolute-error/L1), because MAE is the project's primary
evaluation metric and this gives a direct, proportionate training objective. Do not log-transform,
scale, or otherwise transform the target.

For each inner or outer origin, forecast calendar steps h=1 through h=14 recursively:

1. Freeze the origin. Construct features using the shared inference/history functions from actual
   same-Store Sales on or before that origin plus only earlier predictions from this path.
2. At each calendar step, build predictors in the frozen contract order and apply the fit's fixed
   categorical vocabularies. Never read future Sales, Customers, or Open for feature/state creation;
   never teacher-force a validation step with actual target Sales.
3. Save the finite model output as model_forecast_unclipped. Set the raw forecast and recursive
   PredictedSales state to max(0, model_forecast_unclipped). Thus a finite negative output is
   allowed as an internal model output, retained for audit, but clipped to zero immediately for
   reported raw forecasts and for later lag/rolling state. Record a clipping flag/count.
4. A non-finite output is unavailable (non_finite_prediction), is not clipped into a value, and
   is never fed into recursive state. Later steps may continue if the required row exists; exact
   missing lags/windows remain null and are handled by the approved native numeric-NaN policy.
5. Complete all raw recursion before attaching target labels or applying operational routing.
   Thereafter, source Open == 0 routes operational forecast to 0, source Open == 1 routes it to
   the clipped raw forecast, and unknown Open routes operational output to null. This routing never
   changes raw forecasts, model inputs, or recursive history.

This intentionally preserves ADR-017's known limitation: historical training lag/rolling state
includes actual closed-day zero Sales, while raw future recursive history does not automatically
replace predictions with closure zeros. This train/inference mismatch must be reported, not fixed
implicitly. Closure-aware feedback or direct multi-horizon modeling requires a separate reviewed
methodology change.

## 6. Finite inner tuning and early stopping

The tuning budget is fixed before real-data execution:

| Trial | learning_rate | num_leaves | max_depth | min_data_in_leaf |
|---|---:|---:|---:|---:|
| A | 0.05 | 15 | 4 | 200 |
| B | 0.05 | 31 | 5 | 200 |
| C | 0.03 | 15 | 4 | 100 |
| D | 0.03 | 31 | 5 | 100 |

There are exactly four configurations and no random search, feature search, or extra trials. Shared
parameters are fixed: boosting_type=gbdt, objective=regression_l1, metric=l1,
device_type=cpu, num_threads=4, deterministic=true, force_col_wise=true,
feature_fraction=1.0, bagging_fraction=1.0, bagging_freq=0, lambda_l2=1.0,
max_bin=63, zero_as_missing=false, verbosity=-1, and seed 42 for seed,
data_random_seed, feature_fraction_seed, and bagging_seed. The finite trial-specific
parameters above replace only their corresponding values. No GPU, categorical target encoding,
or stochastic row/feature subsampling is used.

Use the single chronological inner split at origin 2015-04-24; the 14-day recursive validation block
is 2015-04-25…2015-05-08. Fit rows and actual feature history are censored at April 24. Score labels
only after each complete raw recursive checkpoint path is generated. For each trial, train in
continuation chunks of 10 boosting rounds, score recursive open-label MAE at each checkpoint, stop
after five consecutive checkpoints without strict improvement, or at 400 rounds maximum. Select
that trial's best checkpoint by lowest recursive MAE among checkpoints with at least 99% open-label
forecast coverage; if checkpoint MAE ties, keep the earlier checkpoint. This is the early-stopping
metric/procedure. The LightGBM l1 metric may describe training loss only; do not pass the inner
block as a one-step LightGBM validation set or use built-in teacher-forced early stopping. Do not
use any approved outer window to stop or tune.

Choose the configuration by lowest eligible inner recursive MAE; deterministic ties resolve by
fewer leaves, then larger min_data_in_leaf, then listed trial order. Freeze the chosen trial and
its best checkpoint round count before any outer forecast is produced. If no trial has a checkpoint
with at least 99% open-label coverage, stop Phase 6 evaluation and report the tuning/coverage
failure; do not lower the threshold, choose by another metric, or fall back to another model.

The tuning ceiling is four trials × 400 rounds (1,600 inner boosting rounds) plus at most one
400-round refit for each of three outer origins (1,200 outer rounds). Early stopping will normally
reduce this bound. Record LightGBM/Python/platform versions and all fixed parameters. CPU
determinism is practical for the same data, package/build, parameters, and thread configuration,
not a promise of bit-identical results across platforms or LightGBM versions.

## 7. Outer development evaluation

Use exactly the approved windows from Phase 4/5:

| Window | Forecast origin | 14 target dates |
|---|---|---|
| validation_1 | 2015-05-22 | 2015-05-23 through 2015-06-05 |
| validation_2 | 2015-06-05 | 2015-06-06 through 2015-06-19 |
| validation_3 | 2015-06-19 | 2015-06-20 through 2015-07-03 |

After the inner recipe is frozen, independently refit one global booster at each origin using
training_label_eligible rows and actual history through that origin; use the frozen trial,
parameters, seed, category policy, and boosting-round count. Do not early-stop or retune on an
outer window. Forecast its complete 14-day raw recursive path first, then attach labels and
operational Open routing.

For each window, pooled development rows, and each horizon h=1…14, report standalone forecast
coverage and MAE, RMSE, MAPE, and WAPE. The primary metric population is observed target rows with
source Open == 1, observed Sales, and an available clipped raw forecast. Also report denominators,
all-target coverage, open-label coverage, MAPE coverage, and unavailable reasons. MAPE uses only
eligible rows with actual Sales > 0, no epsilon, and explicit zero exclusions/coverage. WAPE is
sum(abs(error))/sum(actual Sales) and is null with an explicit reason when the eligible denominator
is zero. Pooled metrics are recomputed over pooled eligible rows, not averaged from window metrics.

Recompute Seasonal Naive and Holt-Winters with their reviewed implementations for the same origins
and target keys. Construct separate paired records against each baseline on the exact intersection
of eligible Store × Date rows where both candidate and baseline raw forecasts are available; verify
actual Sales/source Open agree by key. Report paired row counts and the same metrics. Never copy
historical metric values into the paired comparison path.

Precommitted coverage guardrail: every outer window must achieve at least **99% open-label raw
forecast coverage**, matching Phase 5. If any window fails, publish standalone predictions,
coverage, metrics, missingness/failure diagnostics, and paired rows/metrics, but flag
requires_coverage_review and suppress claims of paired superiority or inferiority for the
candidate. Do not relax the threshold or remove failed stores/steps from coverage denominators.
Passing the guardrail permits descriptive paired comparison only; Phase 6 still does not select the
final model.

## 8. Failure and availability policy

Keep an explicit forecast status/reason for every requested or attempted step. Preserve the
Phase 4/5 evaluation population: the requested target-key set is the Store × Date keys present in
the source rows for the approved 14 target dates, projected to keys before feature assembly. Do
not create a Cartesian Store × Date grid. Coverage denominators come from that precommitted key
set, not from successful model outputs. Primary open-label denominators are determined only after
the raw path is complete and source Open/Sales labels are attached. If a requested key is missing
from the predictor/covariate projection, it is unavailable against that key denominator. A
calendar key not present in the declared target universe has no forecast and is not synthesized.
Minimum reasons:

| Condition | Result |
|---|---|
| Requested Store × Date key absent from the future-covariate table | No synthetic row; missing_target_key; unavailable against the precommitted target-key denominator. |
| An intermediate recursive date has no supplied future covariate row | missing_future_covariate_row; no prediction/state is fabricated. Later exact-history features may be null. |
| Required source covariate is null on an existing row | missing_required_covariate:<column> for that step. |
| Contract columns/order/dtypes, duplicate-key constraints, or required input shape invalid | invalid_feature_schema; fail the origin/run before fitting or forecasting. |
| No eligible fitting rows or unsupported Store category for a requested path | no_eligible_training_rows or unseen_store_category; no fallback. |
| Booster fit/update or prediction API fails | model_fit_failure or categorical_adapter_incompatibility; affected origin is unavailable and reported. |
| Shared feature/history construction fails for a step | recursive_state_construction_failure; step unavailable, no substitute value. |
| Model output is NaN or infinite | non_finite_prediction; do not clip, route, or feed it into state. |

Allowed numeric NaNs are not failures by themselves. Do not silently substitute Seasonal Naive,
Holt-Winters, zero, a prior prediction, or a fabricated calendar observation. Continue subsequent
steps only when their own key, required covariates, and state construction are valid; a missing
prior prediction naturally leaves the affected exact-history fields null.

## 9. Outputs, provenance, and resource constraints

Generated files belong only in Git-ignored data/processed/lightgbm/ and
artifacts/lightgbm/; do not commit datasets, boosters, or experiment outputs. Before writing,
verify both target paths with git check-ignore.

Minimum processed outputs:

- configuration.json: selected frozen trial, complete shared/trial parameters, seeds, rounds,
  objective, category/null policy, availability assumptions, windows, tuning split, guardrail, and
  software identity.
- tuning_results.csv: one row per trial/checkpoint summary including inner recursive MAE,
  coverage, best round, stop reason, and deterministic selection status.
- inner_validation_forecasts.parquet: raw recursive checkpoint/result forecasts and audit fields;
  attach actual labels only after each path is complete.
- fit_diagnostics.csv: per-origin eligible row counts, category vocabulary hashes, fit status,
  missing/unseen counts, failed-step counts, training duration, selected rounds, and clipped-output
  counts.
- internal_recursive_paths.parquet: the full h=1…14 path and step status for attempted Stores,
  including unclipped model output, clipped raw forecast/feedback state, clipping flag, and model
  identity; keep target labels out of this raw-path artifact.
- development_forecasts.parquet: observed target keys with post-path actual Sales/source Open,
  raw/unclipped/clipped predictions, operational forecast, availability, origin, horizon, and
  reason.
- metrics_by_window.csv, metrics_pooled.json, metrics_by_horizon.csv,
  coverage_guardrail.json, plus per-baseline paired forecast and paired-metric outputs.
- Optional feature_importance.csv from frozen outer fits (gain/split only), explicitly descriptive
  and not an outer-window tuning or selection signal.
- manifest.json: code revision; filtered input/source snapshot identifiers and SHA-256 hashes;
  config, model, and output hashes; row counts/date bounds; exact run parameters/windows; Python,
  OS, CPU/thread, LightGBM and lock/environment identities; and holdout-firewall status.

To honor the holdout firewall, hash only the date-censored development inputs actually passed into
the run (labels through the permitted origin and covariates through the approved development
target end) plus previously recorded source-snapshot identifiers. Do not hash/scan the full
holdout-containing training file as a Phase 6 operation. Outer model files may be serialized as
LightGBM text under artifacts/lightgbm/, one per validation origin; record each file hash and
link it to its fit metadata. The locked LightGBM dependency/version is selected only in an approved
implementation task. No GPU, per-Store model, Spark, distributed infrastructure, SHAP pipeline, or
broad experiment platform is required.

## 10. Required fixture tests before real-data execution

Add focused synthetic tests before any expensive real-data development run:

1. Exact PREDICTOR_COLUMNS names/order/dtypes; no Date, Sales, Customers, Open, eligibility, or
   Open-resolution field in the model matrix.
2. Fitting labels equal only training_label_eligible / observed source Open == 1, including
   valid zero-Sales labels; closed rows remain present in history.
3. Origin censoring for labels, fitting rows, dynamic features, category vocabularies, and raw
   recursive history; reject future actual history.
4. Mutation invariance: changing future Sales, Customers, or Open cannot change raw predictions or
   recursive feature matrices.
5. h>1 uses earlier clipped prediction state, not actual intermediate validation Sales (include a
   case with an altered future label that must leave the second-step raw forecast unchanged).
6. Store is categorical, vocabulary is fit-only and shared consistently with prediction; unseen
   Store is unavailable, unseen non-Store categories become categorical missing and are counted.
7. Required source-null categorical fields are unavailable without sentinel encoding; numeric NaNs
   and structural nulls remain NaN; real zero remains zero.
8. Missing target key, intermediate covariate row, required covariate, and invalid schema each
   produce their specified reason without synthetic rows or fallback.
9. Negative finite model output is retained unclipped and clipped to zero for raw output/feedback;
   NaN/±infinity is unavailable and never enters recursive state.
10. Raw prediction is invariant to future Open; operational Open routing is applied afterward for
    open, closed, and unknown statuses.
11. Missing/unavailable reason accounting, all-target/open-label coverage denominators, the 99%
    guardrail and interpretation suppression at threshold failure.
12. Paired comparison against each recomputed baseline uses identical eligible Store × Date keys
    and consistent labels/status; no pasted metrics.
13. Fixed seeds/configuration and same-environment fixture repeatability; avoid claiming
    cross-platform bitwise determinism.
14. Input DataFrames are not mutated; output/provenance hashes and ignored output-path checks work.
15. Holdout firewall rejects or filters any target/training/history label date after
    2015-07-03 before downstream feature/model/metric work; changing synthetic post-boundary values
    cannot affect development outputs.

After this methodology was approved and PR #9 was integrated into `main`, implementation may run
the predeclared inner tuning and three outer development origins only after the required fixture
tests pass. The final holdout remains untouched.

## 11. Accepted durable decision

ADR-019 — Global Recursive LightGBM Phase 6 Contract is accepted and recorded in
docs/DECISIONS.md. This plan remains the detailed implementation reference for that decision.

## 12. Approval gate and completion boundary

The methodology is approved and PR #9 integrated this design into `main`. The implementation task
authorizes the scoped Phase 6 dependency, code, fixtures, tuning, development forecasts, artifacts,
quality checks, commit, push, and pull request. It does not authorize final-holdout access, Phase 7
model selection, or Phase 7 implementation.

## 13. Implementation checkpoint — 2026-10-06

The authorized code, fixture suite, and real-data development run are implemented on
`feat/phase-6-global-lightgbm`. The final inner tuning selected trial A at 180 rounds; the three
outer origins passed the 99% coverage guardrail. The [Phase 6 section in PROGRESS](../../docs/PROGRESS.md#phase-6-global-lightgbm-implementation--2026-10-06)
records metrics, paired baseline comparisons, provenance and checks. A semantics-preserving
origin-history cache and `feature_pre_filter=false` on the shared Dataset address run-time costs and
the frozen trials' differing `min_data_in_leaf` values; no feature, trial recipe, objective,
selection rule, or evaluation boundary changed.

At this implementation checkpoint, external review, integration, and explicit Phase 6 closeout
were still pending. Their completion is recorded in section 14. Phase 7 remains outside this plan's
scope.

## 14. Formal Phase 6 Closeout — 2026-10-06

Phase 6 is **COMPLETE**. PR #10 was merged into `main` at
`dac71d26bd8a9e43eff7d33592460906ae6fee6f`. The external-review findings were addressed in final
fix commit `9a33e8f673ec438fe4a5546011d06219d66e6a92`; the PR's final-head
[Quality workflow run #12](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/actions/runs/37419362812)
passed on Python 3.12 and 3.14. The final full fixture suite contained 152 passing tests.

The approved development run used LightGBM 4.7.0, selected trial A at 180 rounds, achieved 100%
development open-label coverage, and recorded pooled MAE 871.0612 with the 99% coverage guardrail
passed. The [Phase 6 results in PROGRESS](../../docs/PROGRESS.md#phase-6-global-lightgbm-implementation--2026-10-06)
remain authoritative; these results were not changed by review fixes. No final-holdout forecast or
evaluation occurred. Phase 7 has not started and awaits its own approved design and authorization.
