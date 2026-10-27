# Development Model Selection

Selection is complete. The accepted simple-first rule selected Global LightGBM trial A at 180 rounds. Numerical evidence is in the results summary; this reference retains selection and refit contracts.

[Verified results](../../docs/PROGRESS.md) · [Decisions](../../docs/DECISIONS.md)

## 3. Accepted deterministic selection policy, version phase-7-v1

This is a proposed model ladder with hard integrity/coverage gates, MAE promotion gates, and
explicit operational acceptance. It is not a weighted composite score or statistical test.
Thresholds 5% and 10%, the simplicity order, common-coverage gate and operational acceptance are
**newly proposed after seeing results**; they have no preregistration, significance or financial
savings interpretation. Freeze them before implementing/applying the decision runner. Any later
change requires a recorded reviewed policy version; do not sweep thresholds to obtain a winner.

### 3.1 Population and integrity gates

1. Require exactly the three candidate identities and exact approved window tuples, with unique
   `(Store, forecast_origin, Date)` keys, horizon = Date minus origin in 1..14, finite nonnegative
   available raw values, and identical label/target universes. Reject extra/missing candidates,
   keys or windows and disagreement in horizon/window/actual_sales/source_open. Use a validated
   outer join, not an inner join that discards mismatches. No absent source date becomes zero.
2. Verify manifest hashes, reviewed candidate specifications, feature/configuration identity,
   and development ceiling. Missing/stale/incompatible evidence gives `evidence_review_required`,
   with no selected model. Preserve legacy provenance limitations (§6); do not invent metadata.
3. Report standalone numerators/denominators separately: raw availability / all observed targets;
   and available raw on Open=1 with observed Sales / all Open=1 labels with observed Sales.
   Closed/unknown Open rows cannot improve the open-label denominator.
4. Preserve inherited advanced-model 99% guards and **propose extending 99% to SN and the
   three-way common available population in every window**. The latter denominator is all
   observed open labels, not each model's available rows. Any failure or zero denominator gives
   `coverage_review_required`, no automatic selection and suppressed superiority claims.
   Export missingness/failure diagnostics; do not fill forecasts, assign zero error or penalize
   missing rows with an invented monetary value.
5. Rank on the three-way common primary population (Open=1, observed actual, all three raw
   values available). Also retain inherited standalone and exact pairwise summaries, with counts
   by window and horizon. Reuse `summarize_forecast_metrics` after copying/adapting the reviewed
   raw column names; masks must match actual nullness. Do not substitute routed operational
   forecasts. Report pooled weeks 1–7/8–14 and every individual horizon with eligible counts.

Also report descriptive per-Store eligible counts, MAEs and paired changes from these same
records to expose concentration of gains/losses. No per-store winner, subgroup reranking or
new weighting enters the decision; low-count store summaries do not establish reliability.

### 3.2 MAE promotion and simpler-model preference

Initialize incumbent = SN. Visit HW, then LightGBM, in that fixed order; compare each to the
current incumbent on the same three-way population. A candidate qualifies for promotion only if:

- its pooled MAE is at least 5% lower: `M_candidate <= 0.95 * M_incumbent`, with strict reduction;
- it has strictly lower MAE in at least two of the three windows;
- its MAE in **every** window is <= `1.10 * M_incumbent_window`;
- its pooled MAE in **each** horizon block 1–7 and 8–14 is <= `1.10 * M_incumbent_block`.

Use full-precision row aggregates in canonical sorted key order, never rounded report values.
All required strata must be nonempty; otherwise return `evidence_review_required`. If incumbent
MAE is zero, no nonnegative-error candidate can promote; percentage change is null with a reason.
Exact ties, improvements below 5%, insufficient window wins or a failed regression cap retain the
simpler incumbent. No RMSE/MAPE/WAPE tie-break or store-weight redefinition. Failed HW promotion
does not prevent considering LightGBM directly against SN; ladder path dependence is deliberate.

The horizon cap is on row-weighted week blocks, **not every individual horizon**. This retains the
approved open-label weighting while limiting a broad second-week loss. Publish individual-horizon
regressions prominently, including sparse Sundays and horizon 10; approval must accept this
tradeoff. A per-horizon veto or revised weights would be a different policy needing approval,
not an implementation-time adjustment to make a model pass.

### 3.3 Operational acceptance and failure semantics

Before recording a selection, require a versioned, auditable operational input per potential
incumbent: `operational_acceptance = approved | rejected | unknown`, evidence references and
rationale. The methodology review accepts a qualitative assessment for the existing offline CPU
course demonstration without requiring a new benchmark before selection. Assess known fit-time
evidence, explicitly missing full-pipeline/inference and memory measurements, maintenance burden,
locked environment/configuration, availability assumptions and the unchanged failure policy.
Record the approved scope; do not silently invent measurements or extend acceptance to an
unexamined deployment environment.
SN must be approved to initialize the ladder; otherwise return `operational_review_required`.
For a candidate that passes the MAE gates: approved permits promotion; rejected retains the
incumbent and records the cost/maintenance/assumption reason; unknown stops with that review
status and no official selection. Candidates failing MAE gates cannot be promoted by cost votes.

This project has no approved latency/memory SLA. The external review explicitly accepts qualitative
operational assessment for the existing offline course demonstration; no new benchmark is a
precondition to its Phase 7 selection. This does not establish API latency, throughput, production
reliability, comparative end-to-end speed, measured memory requirements or real operational
savings. If a broader measured resource envelope is later needed, approve its scope separately;
do not add scoring windows or tuning. None is run here.
Reproducibility mismatch is an integrity failure, not a tradeoff for better accuracy. Identical
numeric results are expected in the pinned environment; no universal cross-platform bitwise
guarantee is asserted. Unavailable predictions remain null with reasons; no model fallback is
introduced. Selecting a simpler method is a project decision, not row-wise fallback mixing.

### 3.4 Sufficiency and inference limits

Current development evidence and its scoped original-manifest lineage are accepted for applying
the approved descriptive MAE/coverage policy in this course project, provided the implementation
rechecks hashes, keys, labels, masks and configuration identities and stops on any mismatch.
Preserve source/version metadata; never rewrite old manifests or claim regeneration from current
`main`. On the observed common rows HW fails the week-2 cap against SN (about +13.75%); LightGBM
passes the numeric gates against SN. This remains a conditional rule illustration, not a selected
winner. Approval of qualitative offline operations/provenance does not waive those implementation
integrity checks or support broader runtime or generalization claims.

There are only 42 late-May–early-July target days, three non-overlapping 14-day blocks, repeated
Friday origins and shared stores. Horizon and weekday are confounded; shared holidays/promotions
and cross-store/serial error correlation reduce independent information. Window wins summarize
consistency, not independent replications. Thousands of store-days do not justify a p-value,
IID bootstrap or significance claim. Annual/other-season generalization and future superiority
remain unproven. No confidence intervals or paired uncertainty analysis are proposed here.
Any supplementary origins, uncertainty analysis or sensitivity protocol needs separate prior
review, applies to all candidates consistently, and remains exploratory after observed results.

## 4. Frozen selected-method and origin refit contract

Freeze the **recipe**, not the fitted parameters or a July 17 category vocabulary. Identity includes
candidate algorithm ID, policy version, full configuration, predictor schema/hash where relevant,
refit-recipe hash, code revision/source identity, Python/package versions and uv.lock hash.
Serialize configuration from the reviewed code and checked saved Phase 6 configuration, not a
partial prose recreation. Review equality tests before any recipe is used.

Common: H14 raw monetary Sales at requested Store × Date keys; fit/history from observed rows
through the authorized origin only, preserving gaps/nulls/closed-day zeros as specified by each
algorithm. No future actuals, Customers or Open predictors; no learned full-period preprocessing.
Compute required internal calendar steps without inventing observed target labels. Produce raw
paths first, then source/planned Open routing (closed -> 0, open -> raw, unknown -> null).
Open_resolved is audit-only; unavailable raw forecasts stay unavailable in raw evaluation even
if a known closure allows operational zero. Outcome-derived routing never changes raw recursion.

| Method | Frozen fit/history, prediction and failure specification |
|---|---|
| Seasonal Naive | chronological evaluation contract; `forecast_seasonal_naive` in [seasonal_naive.py](../../src/rossmann_forecasting/forecasting/seasonal_naive.py). Exact same-store date-minus-7 observed Sales for week 1; its own earlier raw predictions for week 2. No fit/optimizer/categories. Missing exact history or earlier prediction remains unavailable; no last-observation, mean or cross-store substitution. All observed history Sales, including closed zeros, supplies lookups. |
| Holt-Winters | Holt-Winters contract; `holt_winters_additive_weekly` / `forecast_holt_winters` in [holt_winters.py](../../src/rossmann_forecasting/forecasting/holt_winters.py). Per store, latest contiguous daily segment ending at origin, at least 28 finite nonnegative observed Sales (closed zeros retained). No gap filling. statsmodels additive trend + additive weekly seasonality 7, undamped, estimated initialization, no Box-Cox; optimized fit, single multi-step H14 forecast. No external categories/features or teacher forcing. Clip finite negatives to zero and retain unclipped values; construction/fit/invalid-output failure makes the store-origin path unavailable. Warnings/convergence remain diagnostics under reviewed behavior, not a newly imposed fallback/failure criterion. |
| Global LightGBM | LightGBM development contract; `global_lightgbm_gbdt_regression_l1` in [lightgbm.py](../../src/rossmann_forecasting/forecasting/lightgbm.py), feature contract `phase-3-v1`. Expanding observed training dates <= origin, with historical features strictly prior to each training date, eligible labels source Open=1 and observed Sales. All observed Sales through origin, including closed zeros, supplies dynamic feature history. Freeze trial A: learning_rate=0.05, num_leaves=15, max_depth=4, min_data_in_leaf=200, exactly 180 rounds. Shared fixed parameters and dataset flags are copied exactly, including l1 objective, CPU/4 threads, deterministic/force_col_wise, seeds 42, max_bin=63, feature_pre_filter=false, zero_as_missing=false. No outer-window/holdout early stopping or tuning. |

LightGBM detail: fit-only ordered vocabularies for Store/state_holiday/store_type/assortment from
eligible fit rows; native numeric NaN handling, no imputation/scaling/new predictors. Unseen Store
is unavailable; unseen other categories become categorical missing with diagnostic counts.
Rebuild inference features from actuals <= origin plus this run's earlier clipped raw predictions,
using the reviewed history cache. Never feed precomputed future lag rows. Missing required
covariates/keys, failed fit/adapter/state construction or nonfinite outputs preserve reviewed
unavailable reasons; unavailable steps are not appended as fabricated zeros. Later steps may
still predict with permitted native NaNs. Retain unclipped values and clipping flags; use clipped
raw values for feedback. Freeze the origin-known covariate assumption and closure/history
mismatch disclosure. Models/vocabularies are fitted anew per authorized origin, not pooled across
outer windows or warm-started as a new method.

Future Phase 13, **not released now**: origin 2015-07-03 forecasts July 4–17 using actuals <= July 3.
Only after sequential revelation authorized by final-release contract, origin 2015-07-17 forecasts July 18–31
using actuals already revealed <= July 17 with the same frozen selected recipe. Newly observed
rows can update fit/history/vocabularies under that recipe, not method selection, 180-round
choice or policy/calibration thresholds. Keep the current development ceiling in force; this
plan does not authorize bypassing existing development runners to read July 4–17 now.
final-release contract requires separately authorized frozen final protocol after model/preprocessing/refit,
intervals, inventory policies and monitoring are frozen. Neither final fit/evaluation is performed
in Phase 7. Earlier full-source EDA exposure remains disclosed; do not call the holdout pristine.

## 5. Uncertainty integration and artifacts

Future approved runner: lightweight evaluation/selection orchestration in existing forecasting
package with a thin script; reuse validation/metrics and cached reviewed development artifacts.
Do not call the LightGBM tuning runner or refit HW merely to compute selection summaries.
Validate the exact approved window tuple beyond the general window-validation helper.
Reuse reviewed pairing contracts without depending on LightGBM's private `_paired_records` as a
new public API. No speculative service/model registry or dependency is needed.

Planned output directory `data/processed/model_selection/` is already Git-ignored; no artifacts
are generated by the selection runner. Do not commit residuals, data or model binaries.

| Artifact | Required content |
|---|---|
| `model_comparison.csv` | Long-form candidate, population (standalone/pairwise/three-way), scope/window/horizon/week-block, raw metric, numerator/denominator, eligible count, missing/zero exclusions, paired change, gate result. Include both candidates' identical-row MAEs. |
| `selection_decision.json` | Policy/config hash, exact candidate order, input artifact hashes, each gate/incumbent transition, operational acceptance references, status/reasons, selected identity only when all gates permit. No selected identity in unresolved states. |
| `selected_model_config.json`, `refit_recipe.json` | Full frozen method/settings, categorical/feature/failure/routing policies, versions and authorized-origin procedure; distinguish recipe from a fitted model. Emitted only for a resolved selection. |
| `selected_development_forecasts.parquet` | Original target universe, selected raw/unclipped/operational forecasts, actual_sales, source_open, Store/origin/Date/horizon/window, availability/primary masks, diagnostic reasons and model/config identity. Keep excluded/unavailable rows. |
| `development_residual_paths.parquet` | Calendar path grid per Store-origin, horizons 1..14, selected raw/operational values, observed-label flag, source Open, signed errors `actual_sales - forecast`, separate raw-primary and operational-error masks, unavailable reason and complete-path flags. |
| `manifest.json` | Command/configuration, source-manifest/file and output hashes/counts/date bounds, code revision/worktree/source hashes, seeds or explicit not-applicable, Python/package/lock identity, no-holdout declaration, legacy limitations, policy/recipe identity and review acceptance. Hash censored inputs only, never full protected source outcomes. |

Forecast residuals are out-of-sample outer-window predictions from the frozen candidate;
exclude LightGBM inner tuning/fit residuals. For raw-primary residuals require source Open=1,
observed actual and available raw. Preserve closed/unknown/unavailable rows with masks rather
than deleting them. An operational residual requires an observed label and available routed
forecast under the declared routing assumption; unknown Open remains unresolved.

The calendar grid is diagnostic, not an assertion that absent source dates were observed.
Never fill absent actuals or pad errors with zeros. `raw_primary_path_complete` requires all
14 raw-primary errors; `operational_path_complete` requires all 14 operational errors. Weekday
closures often prevent the former but may allow the latter. Attach missing-horizon counts/reasons
and Store-origin-level path completeness; complete vectors preserve serial/cross-horizon dependence
for cumulative errors. Internal HW/LightGBM forecasts may supply existing raw steps but never
invent labels; SN steps can be reconstructed from the frozen lookup without a model refit if
needed and origin-censored input is explicitly verified. Path inputs end July 3.

Phase 8 receives selected identity/configuration, original OOS rows, row/path masks, residual
definition, complete vectors where available, missingness/failure/clipping diagnostics, assumptions
and refit/provenance identities. It owns daily/cumulative interval calibration, chronological
earlier-calibration/later-assessment assignment and all interval calculations. All outer windows
have already informed selection: later development assessment is not an independent final test.
Respect monetary inventory contract: do not sum marginal upper bounds or assume independent errors. Phase 8 cannot
revise selection from interval outcomes without a separately authorized methodological review.

## 6. Provenance compatibility

Preserve original candidate manifests and output hashes rather than claiming regeneration from
current code. Legacy Seasonal Naive/Holt-Winters manifests lack modern source/lock identities;
the historical LightGBM manifest records a modified worktree. These limitations were accepted
for the scoped cached development comparison. Validate original manifests, configuration/feature
identities, target keys, labels and masks and stop on mismatch. Never rewrite old metadata.

The versioned operational review applies only to the offline CPU course demonstration. It is not
a production latency, throughput, memory or reliability assessment. Independent implementation and
selection review are complete; [results](../../docs/PROGRESS.md) owns the recorded outcome.
