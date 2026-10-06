# Phase 7 — Walk-Forward Validation and Model Selection

**Status: APPROVED / IMPLEMENTATION NOT STARTED** (WORKFLOW: APPROVED).
Methodology approved after external review on 2026-10-06; implementation has not started and no
final model is officially selected. The approval accepts this policy after observing the Phase 4–6
results; it does not make the thresholds preregistered or select a model. Implementation may begin
only after design PR #12 merges into `main`.

## 1. Authority, verified base, and execution boundary

Branch: `docs/phase-7-model-selection-design`, created from fetched `origin/main` at
`0b8d55144ace29cb8b5367d11aeedc59cfb33a65`. GitHub confirms
[PR #11](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/11) merged there.
Phases 0–6 are COMPLETE; Phase 6 implementation PR #10 is integrated and its plan archived.
The starting worktree was clean. There is no Phase 7 implementation or official final selection.

Read completely: AGENTS, [WORKFLOW](../../docs/WORKFLOW.md),
[proposal](../../docs/proposal.md), [DECISIONS](../../docs/DECISIONS.md),
[PROJECT_PLAN](../../docs/PROJECT_PLAN.md), [PROGRESS](../../docs/PROGRESS.md),
[FEATURE_CONTRACT](../../docs/FEATURE_CONTRACT.md), README, and the completed
[Phase 3](../completed/phase-3-feature-engineering.md),
[Phase 4](../completed/phase-4-seasonal-naive.md),
[Phase 5](../completed/phase-5-statistical-forecasting.md), and
[Phase 6](../completed/phase-6-global-lightgbm.md) plans.
Inspected validation, metrics, three forecasters, evaluation interfaces, and LightGBM runner.
ADR-008/013/014/015/017/019 remain authoritative; accepted Phase 7 policy is recorded in ADR-020.
No proposal is amended.

The reviewed implementation scope remains limited to this design. Methodology is approved, but
implementation starts only after PR #12 is integrated; the active phase plan stays active through
review/integration/closeout.
No selection runner, new tests, model changes, dependencies, tuning, additional windows, final
evaluation, or Phase 8 interval work is part of this design task.

## 2. Inherited contracts and observed evidence

Exactly three fixed candidates: Seasonal Naive, additive weekly Holt-Winters, global recursive
LightGBM. Proposed canonical selection IDs are `seasonal_naive`,
`holt_winters_additive_weekly`, and `global_lightgbm_gbdt_regression_l1`, mapped explicitly to
their reviewed interfaces below. Forecast monetary Sales at Store × Date, H=14 calendar days,
without log transformation.
The accepted outer windows are immutable:

| Window | Forecast origin | Target dates, inclusive |
|---|---|---|
| validation_1 | 2015-05-22 | 2015-05-23–2015-06-05 |
| validation_2 | 2015-06-05 | 2015-06-06–2015-06-19 |
| validation_3 | 2015-06-19 | 2015-06-20–2015-07-03 |

MAE is primary on observed source Open=1 labels with available **raw** predictions. RMSE,
cautious positive-actual MAPE, and WAPE are supplementary. Keep reviewed zero-denominator/null
reasons and coverage definitions. Pool eligible rows; never average the three window MAEs.
ADR-014/019 already require at least 99% advanced-candidate open-label coverage in every window
before comparative interpretation. Fit/history inputs stop at their origin; development reads
filter Date <= 2015-07-03 before labels enter modeling/evaluation. Raw paths precede Open routing.

Canonical numerical evidence is in [Phase 4–6 PROGRESS](../../docs/PROGRESS.md), with the
[Phase 7 evidence audit](../../docs/PROGRESS.md#phase-7-design-and-development-evidence-audit--2026-10-06)
recording newly verified horizon/compute/provenance details. Do not copy historical result tables
into a second maintained source. Saved development forecast/metric/diagnostic hashes were checked
against their original manifests; joining all three gives 46,830 matching targets and 38,553
common eligible rows, exactly the historical paired population.

Descriptive interpretation, **not an approved decision**:

- Pooled MAEs reproduce 1,681.2703 / 1,281.7446 / 871.0612 for SN/HW/LightGBM. LightGBM's
  improvement is 48.19% versus SN and 32.04% versus HW; HW improves 23.76% versus SN.
- LightGBM has lower MAE than both in each window, but only a 4.55% advantage over SN in
  validation_1. HW improves in two windows and worsens in the first. Relative errors are not
  constant across periods; neither the best single window nor the average window decides.
- All three have 100% all-target and open-label availability in these windows. All pairwise
  and three-way comparisons use the same 38,553 rows here; this equality must be checked anew,
  never inferred from 100% coverage claims or silently preserved by an inner join.
- LightGBM also leads pooled RMSE/MAPE/WAPE. This supports the MAE description without creating
  three additional votes. Large squared errors remain, and these metrics do not prove value for
  a simulated inventory policy or physical demand.
- Horizon behavior is uneven: LightGBM leads SN on 11/14 and HW on 11/14 horizons. It loses
  to both on Sunday horizons 2/9, and to SN substantially on horizon 10; it loses slightly to
  HW on horizon 8. Pooled week 2 is worse than week 1 for LightGBM and HW. The proposed block
  rule below permits individual-horizon regressions; that tradeoff needs explicit approval.
- Existing SN forecasts are available; HW has 3,345 successful fits, no recorded warnings,
  nonconvergence or fit failures, and 1,085 clipped internal predictions. LightGBM's three
  outer fits succeed with no unavailable or clipped predictions. These observations do not
  replace the frozen missingness/failure policies or establish future failure probabilities.
- SN has exact weekly lookups and minimal state; HW adds per-store optimizers and contiguous
  histories; LightGBM adds features, categorical adaptation, native-library dependence and
  recursive state. The maintenance order SN < HW < LightGBM is a proposed policy judgement,
  not an observed runtime ranking. HW's many fits can cost more than one global booster.
- Saved LightGBM outer training times are about 6.04–6.26 seconds **for fitting only** on the
  recorded environment. Feature building, recursive inference, I/O, memory peaks, and SN/HW
  comparative timings were not measured. No end-to-end speed or service SLA is claimed.
- Replay assumes calendar/holiday/planned promotion and static snapshot values known at the
  origin, without verified publication histories. Future Customers are forbidden; source Open
  is routing/eligibility only. Historical closed-day zeros versus raw future recursive feedback
  remain the disclosed Phase 6 mismatch. Selection does not repair these assumptions.

## 3. Newly proposed deterministic selection policy, version phase-7-v1

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
| Seasonal Naive | ADR-013; `forecast_seasonal_naive` in [seasonal_naive.py](../../src/rossmann_forecasting/forecasting/seasonal_naive.py). Exact same-store date-minus-7 observed Sales for week 1; its own earlier raw predictions for week 2. No fit/optimizer/categories. Missing exact history or earlier prediction remains unavailable; no last-observation, mean or cross-store substitution. All observed history Sales, including closed zeros, supplies lookups. |
| Holt-Winters | ADR-014; `holt_winters_additive_weekly` / `forecast_holt_winters` in [holt_winters.py](../../src/rossmann_forecasting/forecasting/holt_winters.py). Per store, latest contiguous daily segment ending at origin, at least 28 finite nonnegative observed Sales (closed zeros retained). No gap filling. statsmodels additive trend + additive weekly seasonality 7, undamped, estimated initialization, no Box-Cox; optimized fit, single multi-step H14 forecast. No external categories/features or teacher forcing. Clip finite negatives to zero and retain unclipped values; construction/fit/invalid-output failure makes the store-origin path unavailable. Warnings/convergence remain diagnostics under reviewed behavior, not a newly imposed fallback/failure criterion. |
| Global LightGBM | ADR-019; `global_lightgbm_gbdt_regression_l1` in [lightgbm.py](../../src/rossmann_forecasting/forecasting/lightgbm.py), feature contract `phase-3-v1`. Expanding observed training dates <= origin, with historical features strictly prior to each training date, eligible labels source Open=1 and observed Sales. All observed Sales through origin, including closed zeros, supplies dynamic feature history. Freeze trial A: learning_rate=0.05, num_leaves=15, max_depth=4, min_data_in_leaf=200, exactly 180 rounds. Shared fixed parameters and dataset flags are copied exactly, including l1 objective, CPU/4 threads, deterministic/force_col_wise, seeds 42, max_bin=63, feature_pre_filter=false, zero_as_missing=false. No outer-window/holdout early stopping or tuning. |

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
Only after sequential revelation authorized by ADR-015, origin 2015-07-17 forecasts July 18–31
using actuals already revealed <= July 17 with the same frozen selected recipe. Newly observed
rows can update fit/history/vocabularies under that recipe, not method selection, 180-round
choice or policy/calibration thresholds. Keep the current development ceiling in force; this
plan does not authorize bypassing existing development runners to read July 4–17 now.
ADR-015 requires separately authorized frozen final protocol after model/preprocessing/refit,
intervals, inventory policies and monitoring are frozen. Neither final fit/evaluation is performed
in Phase 7. Earlier full-source EDA exposure remains disclosed; do not call the holdout pristine.

## 5. Phase 8 handoff and proposed ignored artifacts

Future approved runner: lightweight evaluation/selection orchestration in existing forecasting
package with a thin script; reuse validation/metrics and cached reviewed development artifacts.
Do not call the LightGBM tuning runner or refit HW merely to compute selection summaries.
Validate the exact approved window tuple beyond the general window-validation helper.
Reuse reviewed pairing contracts without depending on LightGBM's private `_paired_records` as a
new public API. No speculative service/model registry or dependency is needed.

Planned output directory `data/processed/model_selection/` is already Git-ignored; no artifacts
are generated in this task. Do not commit residuals, data or model binaries.

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
Respect ADR-016: do not sum marginal upper bounds or assume independent errors. Phase 8 cannot
revise selection from interval outcomes without a separately authorized methodological review.

## 6. Provenance compatibility and approval checkpoint

Cached outputs are useful but not claimed to have been regenerated at this branch's base:
legacy SN/HW manifests lack modern code/lock identity. LightGBM records code revision
`79ddb510e94fe5695c4bc17814153fd47695e16f`, `code_worktree_modified=true` and a working-tree
source hash. Review fixes subsequently preserved successful forecast semantics/results without
rerunning tuning. Preserve these original records and output hashes; current source identity
belongs to the selection aggregation, not retroactively to old fits. The reviewer must accept
this documented evidence lineage or require a separately scoped reproducibility audit. Hash
verification and exact label/key agreement alone do not reconstruct unrecorded historical code.

ADR-020 records the externally approved methodology and durable refit/Phase 8 boundary. The
approval accepts the 5% promotion threshold, two-of-three window wins, 10% per-window and pooled
horizon-block caps, simpler-model ladder, 99% standalone/common coverage gates, individual-horizon
reporting, qualitative offline operational scope, and disclosed cached-provenance lineage. It
does not declare any model selected. The thresholds were introduced after results were observed;
that disclosure, individual-horizon losses, lack of statistical significance/generalization claims,
and origin/holdout protections remain permanent parts of the decision.

Implementation status remains not started. PR #12's merge into `main` is the required integration
gate before implementation begins. No final model selection is approved by methodology acceptance.

## 7. Future fixture test and execution plan

After approval, implement one focused runner and fixture tests; do not add these tests now:

| Test group | Required assertions |
|---|---|
| Population/windows | Exactly three distinct fixed candidate IDs; reject extras/duplicates; exact window tuples including Friday origins, H14, no extra dates/windows or future labels. |
| Pairing/coverage | One-to-one keys and label equality; missing keys rejected; unequal raw availability yields explicit pairwise/common masks. Standalone all-target/open-label denominators remain unchanged; closed/unknown and unavailable rows cannot disappear; 99% boundaries and null strata stop states tested. |
| Metrics | Pooled sum-absolute-error/count on unequal window sizes, not mean of MAEs; raw versus routed distinction; horizon/week-block counts; MAPE/WAPE zero/null reasons; identical-row relative changes and zero incumbent handling. |
| Selection | Permuted input order yields same decision; canonical sorted full-precision metrics; fixed ladder path, >=5% boundary, strict wins, <=10% caps, exact ties and near ties retain simpler; rejected/unknown operational states; failed HW does not prevent LightGBM consideration. |
| Failures/schema | Never synthesize unavailable predictions or residuals; all target rows retained; keys/sign/masks/schema and complete versus partial 14-step operational/raw paths; missing dates are not observed zeros; inner tuning rows excluded. |
| Refit/firewall | Configuration equality with each reviewed algorithm; LightGBM A/180/shared/dataset flags and vocabulary/feedback identity; all fits/history stop at origin; reject unsafe precomputed lags. Selection reads only validated cached development outputs, never raw/interim/final-label files; mutated protected input cannot affect it. Future July 17 recipe invocation requires separate ADR-015 release authority. |
| Non-mutation/provenance | Caller frames/configs unchanged; mismatched hashes/schema/config or absent provenance-review acceptance stops selection; original dirty/legacy manifest metadata preserved; output hash/count/policy/recipe consistency and no selected output in review states. |

Execution order after authorization: validate cached lineage and identities; aggregate immutable
records; apply approved policy and operational review inputs; export evidence/freeze/handoff;
run fixture/full quality gates and inspect all generated bounds/masks; update canonical PROGRESS;
external review, authorized integration and explicit Phase 7 closeout. No expensive tuning rerun
or protected-target read is required for selection aggregation. A discovered evidence defect
requires review of remediation scope before rerunning a model or changing methodology.

## 8. Design delivery checkpoint

For this initial design PR, only this plan and the current-state/evidence-audit addition in PROGRESS
changed. Run full pytest,
Ruff lint/format, Markdown links, `git diff --check` and `uv lock --check`; inspect the complete
diff, then commit `docs: propose Phase 7 model selection design`, push and open the design PR.
Record actual outcomes before publication. Do not merge the design PR.

Design validation on 2026-10-06: full pytest **152 passed** on Python 3.14.5 and **152 passed**
on Python 3.12.15; Ruff lint passed; Ruff format check passed (70 files); Markdown checker passed
(107 local destinations/anchors across 22 Markdown files); `uv lock --check` and `git diff --check`
passed. Complete documentation diff inspected for scope and holdout boundary. No new fixture
tests or generated selection outputs were added; the table above is the future test plan.

### Methodology approval synchronization — 2026-10-06

External approval for PR #12 reviewed head `1c15ab0b6ee94f3ecccb8f04c84da97d58bbb225` was
recorded in ADR-020. It accepts the policy exactly as written, including its post-observation
threshold disclosure and individual-horizon reporting; it does not select a model. Qualitative
operational assessment is accepted only for the existing offline CPU course demonstration, and
historical artifact lineage is accepted only with the required integrity rechecks. Design PR #12
remains the integration gate before implementation.

The approval sync changes only this plan, DECISIONS, PROGRESS, PROJECT_PLAN and README. Full pytest
passed (152 tests on Python 3.14.5 and 152 on Python 3.12.15); Ruff lint/format, Markdown links,
`uv lock --check` and `git diff --check` passed. No forecasting code, tests, dependencies, model
selection, generated artifacts, new validation windows, holdout access or Phase 8 work were added.
