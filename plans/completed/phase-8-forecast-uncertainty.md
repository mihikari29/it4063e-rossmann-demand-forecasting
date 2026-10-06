# Phase 8 — Forecast Uncertainty Methodology (Approved)

**Status: COMPLETE.** Formal closeout was recorded on 2026-10-07 after verifying that PR #15
([implementation](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/15)) was
squash-merged into `main` at `c694f5922a1c1e58ffaf9c2437fd9698ca3e5821` and PR #16
([results acceptance](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/16))
was squash-merged into `main` at `4dd7717fed57ff3b1f14789b980772c1968f3cba`. The external
numerical-results decision is ACCEPTED, and Fit B fitted quantile values are frozen for the exact
canonical run recorded in Section 17. The method remains ADR-021. The Open information boundary
below remains mandatory.

## 1. Authority, base and boundary

PR #14 integrated the methodology approval and Phase 7 closeout into `main`. The current task
explicitly authorizes implementing and evaluating only this protocol. The approval-sync checkpoint
below remains a historical record of the earlier documentation-only task; implementation does not
expand its methodology or information boundary. Point-model selection/tuning/refits, new
origins, final-holdout reads, and Phase 9/10 work are outside this plan's authorization.

At the original design audit checkpoint, GitHub confirmed PR #13 merged at
`89bcb861642ee28259e4a402e8e8ee98a999a6e5` and a clean `docs/phase-8-uncertainty-design` branch
was based on that reviewed tree. PR #14 later integrated the approved design and Phase 7 closeout;
the implementation branch is based on that merged commit. Phase 7 is **COMPLETE** and its
[archived plan](../completed/phase-7-model-selection.md) retains historical checkpoints.
[PROGRESS](../../docs/PROGRESS.md#phase-7-formal-closeout-and-phase-8-evidence-audit--2026-10-06)
owns the closeout and current audit evidence.

The fixed method is `global_lightgbm_gbdt_regression_l1`, trial A / exactly 180 rounds, using
the ordered 29 Phase 3 predictors. ADR-017/019/020 raw recursion, clipping, model recipe,
selection thresholds and post-path Open routing are unchanged. No fitted July model exists from
this task. The forecast horizon remains 14 calendar days, with development labels restricted to
Date <= 2015-07-03. The protected 2015-07-04 through 2015-07-31 outcomes require the separately
authorized, frozen Phase 13 protocol in ADR-015.
Earlier full-source descriptive EDA exposure remains disclosed in ADR-015 and
[EDA_FINDINGS](../../docs/EDA_FINDINGS.md); the eventual holdout is not a pristine
never-inspected dataset. That history permits no new protected outcome use in this task.

Sources reviewed: [AGENTS](../../AGENTS.md), [WORKFLOW](../../docs/WORKFLOW.md),
[proposal](../../docs/proposal.md), [DECISIONS](../../docs/DECISIONS.md) including ADR-015–017,
019–020, [PROJECT_PLAN](../../docs/PROJECT_PLAN.md), [PROGRESS](../../docs/PROGRESS.md),
[FEATURE_CONTRACT](../../docs/FEATURE_CONTRACT.md), [DATA_DICTIONARY](../../docs/DATA_DICTIONARY.md),
[README](../../README.md), completed
[Phase 4](../completed/phase-4-seasonal-naive.md),
[Phase 5](../completed/phase-5-statistical-forecasting.md) and
[Phase 6](../completed/phase-6-global-lightgbm.md) plans, and the selected
[model-selection implementation](../../src/rossmann_forecasting/forecasting/model_selection.py),
[validation](../../src/rossmann_forecasting/forecasting/validation.py) and
[metrics](../../src/rossmann_forecasting/forecasting/metrics.py) interfaces.

## 2. Existing evidence and information boundary

The read-only audit verified the saved Phase 7 manifest and every listed output hash, original
candidate artifacts, selected identity/recipe and residual schema/masks. Hashes and numerical
counts are maintained in PROGRESS, rather than copied into another results table here. The input
selection run is `365f22d4c3f94722a594ab934a22c4f6`; the selected model configuration hash and
refit-recipe file hash are separate identities and must not be confused.

### Input contract

The existing `data/processed/model_selection/development_residual_paths.parquet` has one row per
`(Store, forecast_origin, Date)`, with `Date = forecast_origin + horizon`. There are exactly h1–14
per audited Store-origin; `validation_window` identifies an approved development window.

| Existing fields | Meaning and permitted use |
|---|---|
| `raw_forecast` / `raw_model_forecast` / `raw_lightgbm_forecast` | Equal selected nonnegative clipped raw forecasts. `model_forecast_unclipped` and `forecast_was_clipped` preserve clipping audit information. Phase 8 uses the saved clipped path and never feeds interval bounds into recursion. |
| `operational_forecast` | After the entire raw path exists: source Open=1 uses raw; source Open=0 routes to zero; unknown Open gives unavailable. It is not a raw predictor or recursive feedback input. |
| `actual_sales`, `source_open`, `target_key_observed` | Observed turnover label, historical source Open and whether the original Store-Date key exists. An absent key is not zero. These are outcome/evaluation fields, not proof of an origin-time schedule. |
| `raw_residual`, `operational_residual` | Signed `actual_sales - raw_forecast` and `actual_sales - operational_forecast` wherever their components exist. A numeric raw closed-day residual does not make that row primary-eligible. |
| `forecast_available`, `operational_forecast_available`, `primary_evaluation_eligible` | Raw/operational forecast availability. In this residual-grid export, `primary_evaluation_eligible` equals `raw_primary_error_available` and includes forecast availability; derive the label-only denominator separately from observed key/Open=1/finite Sales. Check masks against components rather than inferring eligibility from a numeric residual alone. |
| `raw_primary_error_available` | Observed key, Open=1, observed finite Sales and available finite raw forecast/residual. Daily raw calibration uses this population. |
| `operational_error_available` | Observed key, observed finite Sales and available finite routed forecast/residual. Includes observed closed-day turnover under the declared routing assumption. |
| `raw_primary_path_complete` / `operational_path_complete` | All 14 component error masks true for the respective population. `raw_primary_missing_horizons` / `operational_missing_horizons` count unavailable components. Prefix completeness must be checked independently for each k. |
| `candidate_id`, `model_config_identity`, `model_configuration_sha256`, `model_selection_run_id`, `source_manifest_sha256` | `model_config_identity` contains the candidate ID; the configuration SHA hashes the canonical serialized recipe. Selection-run and candidate-manifest lineage are separate. Verify against JSON inputs and manifests, not just row strings. |
| Unavailability and unseen-category flags | Preserve forecast reasons and category audit flags; they do not authorize a new predictor, stratum or fallback model. |

All 46,830 audited rows end by July 3; all 3,345 operational H14 paths are complete. Only 96
raw-primary H14 paths are complete, with 3,249 partial paths. Those 96 are the same 32 stores in
each of three origins, so restricting all uncertainty to complete raw paths would select an
unrepresentative always-open-in-these-windows cohort. Daily intervals should retain eligible
individual horizons of partial paths. Raw cumulative calibration is outside this design;
raw-complete paths are not a substitute for the operational population.

There are 8,277 observed closed-day records, all actual Sales=0 and routed forecasts=0. Their
operational errors are observed zeros, which explains much of the completeness difference.
They are not fabricated missing residuals, uncensored latent demand, physical units or evidence
that demand would have been zero had the store been open. Sales is monetary turnover.

### Approved development opening-schedule interpretation and holdout firewall

ADR-021 approves `saved_source_open_assumed_known_at_origin` solely to reproduce existing
DEVELOPMENT operational forecasts as a **conditional historical course replay**. It assumes the
recorded opening/closure schedule was known at each historical origin and that a planned closure
implies zero operational Sales. The dataset does not establish that availability. Label all
operational development calibration and assessment as conditional replay; make no prospective
availability claim.

For a Phase 13 operational issuance, actual holdout Open must never be read, hashed, loaded or
substituted as a planned schedule before the corresponding forecast issuance. No protected July
4–31 Open, Sales or Customers value may be revealed early. An operational forecast requires a
separately reviewed origin-known schedule source with provenance, or a separately approved
synthetic/conditional schedule that does not derive from protected future actual Open. Without
such an authorized schedule, operational forecasts, routed intervals and cumulative bounds that
depend on future Open remain unavailable. Future actual Open may be joined only after issuance
and the separately authorized sequential outcome reveal. Development replay approval alone does
not authorize final-holdout operational replay.

For any authorized schedule input, distinguish `known_open`, `known_closed` and `unknown` from
its source/version/hash, issue-time evidence <= forecast origin and declared availability
assumption. If no authorized schedule exists, operational intervals and every prefix crossing an
unknown day remain unavailable. Historical actual Open must not silently populate a supposedly
verified origin-time schedule.

The raw model and raw interval calibration never use future actual Open as predictors and remain
unchanged for every day; daily raw calibration applies only to observed Open=1 Sales. Raw
intervals displayed on closed/unknown days are audit outputs, with no claimed coverage for
closed-day or hypothetical latent-demand outcomes. Interval routing occurs after raw construction
and never changes future raw features, feedback or model fitting. A closed-day `[0,0]` operational
bound is permitted only for an explicitly known or approved assumed closure and describes
turnover, not latent demand. Preserve separate Open=1, Open=0 and pooled operational diagnostics,
including deterministic-closure inflation.

## 3. Approved method and alternatives

ADR-021 accepts empirical signed residual order statistics pooled across stores within each exact
horizon, with the exact outward finite-sample ranks below. This preserves asymmetry and observed
horizon effects, is easy to audit and requires no new model or resampling. Use separately fitted
cumulative operational-prefix errors for one-sided upper monetary bounds.

| Alternative | Decision under the approved protocol |
|---|---|
| Interpolated empirical quantiles | Valid descriptive estimators, but interpolation creates a convention-dependent tail value in sparse strata. Prefer explicit observed order statistics and exact rank arithmetic. |
| Absolute-error symmetric bands | Simple, but discard signed bias/asymmetry. Do not combine them with signed bands after seeing assessment results. |
| Per-store, weekday or promotion/holiday strata | Too little temporal replication, especially Sundays; no approved extra covariate projection in the export. Use pooled horizon strata and disclose heterogeneity. |
| Borrowing adjacent horizons or baseline errors | Changes the error population and hides unsupported strata; no fallback in version 1. |
| Conformal or block-bootstrap methods | Do not claim conformal validity or bootstrap uncertainty here. Only one/two calibration-origin clusters and selected development data do not support an exchangeable calibration/test argument or a reliable temporal block resampling assessment. |

NumPy's default `linear` quantile interpolates using q(n-1); specifying a method changes the
estimator. The approved method therefore defines ranks directly rather than relying on
default interpolation or an ambiguous `higher` option.
[NumPy quantile documentation](https://numpy.org/doc/2.4/reference/generated/numpy.quantile.html)
describes these conventions.

Exchangeability is required for standard finite-sample conformal coverage arguments.
[Angelopoulos and Bates](https://arxiv.org/abs/2107.07511) explain the calibration assumptions
and marginal interpretation. Our rank rounding is a transparent empirical tail convention, not
a conformal guarantee under these dependent, model-selected records. Correlation still affects
representativeness and effective sample size; rounding cannot repair that limitation.

## 4. Chronological calibration, assessment and freeze

Only the ADR-013 approved windows are used:

| Window | Forecast origin | Target dates |
|---|---|---|
| validation_1 | 2015-05-22 | 2015-05-23 through 2015-06-05 |
| validation_2 | 2015-06-05 | 2015-06-06 through 2015-06-19 |
| validation_3 | 2015-06-19 | 2015-06-20 through 2015-07-03 |

ADR-021 approves two predetermined expanding calibration fits, shared by daily and cumulative
estimators:

| Fit | Calibration windows / last calibration label | Assessment issuance and targets |
|---|---|---|
| A | validation_1 / 2015-06-05 | validation_2 at origin 2015-06-05 |
| B | validation_1 + validation_2 / 2015-06-19 | validation_3 at origin 2015-06-19 |

At issuance, all calibration targets must be <= that origin, and all assessment targets strictly
later. Follow the accepted end-of-origin-day information convention. Reject own-window/later
labels even when supplied in the same file. Separate calibration projections from assessment
label joins; later outcomes enter only after bounds are fixed. Filter development exports at the
storage/read boundary to Date <= July 3, verify metadata/row counts and reject an unexpected
post-cutoff input; never read or hash protected source files.

Fit A may be sparse; Fit B adds an origin at the cost of pooling older conditions. Assess them
separately rather than describing the combined assessment rows as one stationary experiment.
Calibration-set coverage is a fitted descriptive diagnostic, not assessment coverage.
Calculate it retrospectively after each fit, label it `calibration_descriptive`, and keep it
out of issued interval records: it must not masquerade as origin-valid historical issuance.
Later-origin coverage is useful development evidence. All three windows informed Phase 7 point
model selection, so none is an independent untouched test of the whole modeling process.
Final-holdout coverage is unavailable.

The policy is approved, but its fitted values are not frozen. After authorized implementation,
Fit B's tables, diagnostics, hashes and availability must receive external implementation/results
review before those values are frozen. Fit B remains calibrated on validation_1+2 and assessed on
validation_3. Do not refit quantiles on all three windows: that would create an unassessed final
calibration.
Fit B occurs by the predeclared schedule regardless of Fit A's diagnostics, not as a remedial
adjustment. Do not change levels, ranks, samples, strata or widths after adverse assessment
without a separately approved methodology revision. Poor or unavailable results must be reported
and reviewed; design approval is not an automatic coverage-acceptance decision.

Phase 13 may use only the frozen reviewed policy/tables with its separately approved model
refit/release protocol. This approval does not authorize a July forecast, refit, recalibration,
holdout-derived interval correction or automatic post-origin update.

## 5. Daily two-sided marginal 95% intervals

Under the approved ADR-021 policy, for each fit and exact h in 1..14:

1. Select calibration rows with `raw_primary_error_available=true`, consistent observed Open=1
   labels and finite clipped raw forecasts. Partial H14 paths may contribute eligible h rows.
2. Use signed monetary residual `e = actual_sales - raw_forecast`. Pool equally weighted
   Store-origin rows at that h across only the prescribed earlier windows. No store weighting,
   scale normalization, cross-horizon borrowing or additional strata.
3. Sort finite residuals `e_(1) <= ... <= e_(n)`. Ties are retained with multiplicity.
   Use 1-indexed ranks:
   `r_low = floor((n+1)/40)` and `r_high = ceil(39*(n+1)/40)`.
   The two tail levels are 0.025 and 0.975. Use exact integer/rational rank arithmetic and
   `q_low=e_(r_low)`, `q_high=e_(r_high)`; no interpolation or rank clamping.
4. Require both ranks in 1..n and **at least 40 eligible residual rows** at that h.
   The approved 40-row rule is a pragmatic tail-resolution floor, not a statistical-power or
   independence guarantee; n=39 can already have valid extreme ranks, but is below the approved
   minimum. Report distinct stores/origins and do not describe 40 rows as 40 independent trials.
5. For the issued nonnegative raw point forecast f, retain pre-support bounds
   `a=f+q_low`, `b=f+q_high`. Publish `lower=max(0,a)`, `upper=max(0,b)` and
   `width=upper-lower`. Clip both endpoints to the nonnegative support; retain clipping flags and
   zero-width intervals. The point need not lie inside a signed-residual interval. Never force
   it inside, swap bounds or repair nonfinite/inconsistent bounds.
6. If sample/rank/forecast requirements fail, publish null bounds/width and an explicit reason,
   along with n, ranks and availability counts. There is no fallback hierarchy or model mixing.

The sample floor and ranks were accepted after reviewing availability counts; this chronology is
not a claim that the rules were preregistered. In Fit A, h2, h3 and h9 have 32, 33 and 32 rows
and remain unavailable under this policy.
Fit B's h2/h9 have 65/64 rows, from only 33/32 distinct stores across two origins. Their estimates
would use extreme tail observations and remain fragile even when the sample rule passes.
No quantile values or intervals have been computed in this design task.

A daily 95% interval has a nominal two-sided **marginal**, horizon-specific Open=1 turnover
interpretation under a stable pooled calibration population. It is not a simultaneous 14-day
band, per-store/conditional coverage guarantee or one-sided 95% service bound.
[Forecasting: Principles and Practice](https://otexts.com/fpp3/prediction-intervals.html)
explains the prediction-interval interpretation; our empirical reliability must still be
assessed chronologically.

### Operational daily routing

Under the approved conditional replay interpretation: known Open=1 copies raw bounds;
known Open=0 yields `[0,0]` for operational turnover only; unknown Open yields null operational
bounds with `opening_schedule_unknown`. Keep raw and operational records distinct, with schedule
provenance and a closure-assumption flag. This zero is a stated known-closure routing rule, never
an imputation for missing Sales, a missing key or an unknown schedule.

Assess raw intervals only on the raw-primary mask. Assess operational intervals on the
operational mask, reporting Open=1 and Open=0 branches separately as well as any pooled total.
Many deterministic closed zeros can inflate pooled operational coverage. A nonzero observed
closed-day Sales outcome is an assumption-violation diagnostic; preserve it as a miss and do not
overwrite it, change the point forecast or recalibrate automatically.

## 6. Cumulative operational-prefix uncertainty

The all-store operational population is suitable only for the disclosed schedule-conditional
monetary course replay, not physical/latent-demand calibration or a production service promise.
If no authorized schedule applies, this component remains unavailable; do not silently replace it
with raw errors from the 32-store complete-path cohort.

For each Store-origin and k=1..14, use exactly the first k calendar components. A prefix is
complete only if every h=1..k has its observed target key, observed finite Sales, finite routed
forecast/residual, `operational_error_available=true` and an allowed known opening interpretation.
Check sequence/uniqueness and routing invariants. Missing h after k does not invalidate an
otherwise complete prefix; missing h within it does. Never drop a component and sum the rest or
fill any missing residual with zero.

Define `E_(s,o,k) = sum[h=1..k](actual_sales_(s,o,h) - operational_forecast_(s,o,h))`,
with a fixed ascending-horizon floating-point summation order. This one signed monetary prefix
error is one calibration observation. At each k, pool equally weighted complete Store-origin
prefixes from the same Fit A/B chronology. Retain excluded-path counts/reasons. The audit implies
1,115 complete prefixes per k in Fit A and 2,230 in Fit B; Fit B reuses the same 1,115 stores,
and neither count is a count of independent temporal replications.
Pooling includes different numbers and placements of closed days; it supplies no coverage
guarantee conditional on a particular future opening schedule.

Use the approved nominal one-sided levels **p in {0.90, 0.95, 0.98}**, a transparent small
service-level grid. Sort complete `E_k` values with multiplicity; use
`r_p = ceil((n+1)*p)`, `q_p(E_k)=E_(r_p)`, exact rational ranks and no interpolation.
Require a valid rank in 1..n and **at least 50 complete prefixes** for the requested (k,p).
The approved 50-path floor allows a finite extreme 0.98 rank; n=49 also has a valid such rank,
but is below this pragmatic floor. Neither floor demonstrates tail reliability.
No pooling across k, clipping residuals to positive errors or fallback to daily interval bounds.

For a complete issued operational forecast prefix, use ADR-016's accepted equations:

```text
D_k = sum(h=1..k) operational_forecast_h
U_k = max(0, D_k + q_p(E_k))
SafetyStock_k = max(0, U_k - D_k)
Target_k = max(D_k, U_k)
```

D and all outputs are monetary retail-equivalent values. A negative q is permitted: U may be
below D, safety stock is then zero, and Target remains D. Preserve q and support-clipping flags
rather than silently making every residual/quantile positive.

Summing each observed prefix before estimating its quantile preserves within-path dependence;
do not sum marginal daily 95% upper endpoints or independently resample daily errors. Correlated
same-date stores and repeated origins still limit transportability. There is no joint guarantee
across k/p/stores, no aggregate multi-store bound and no latent-demand correction.

A one-sided p quantile concerns the terminal cumulative monetary outcome over that particular
prefix. It differs from a two-sided daily 95% interval. Calling p a nominal inventory service
parameter does not establish the probability of avoiding stockout at every point in a cycle;
terminal cumulative Sales coverage is not an observed cycle-service KPI.

## 7. Phase 10 handoff and scope limits

Inherited ADR-016 context: retail-equivalent monetary stock state, daily review R=1, lead time
L in 2..7 and protection period P=L+R in 3..8, all <=14. Supply prefix tables for k=1..14,
with inventory consumers restricted to the approved L/P values, selected identity, origin,
policy/fit identity, p and availability. No currency-to-SKU conversion or physical demand claim.

Handoff rows contain `D_k, q_p, U_k, SafetyStock_k, Target_k`, completeness,
sample counts, schedule assumptions and provenance. Phase 10 must check identities, supported
horizons and all required availability before applying its separately approved inventory rules;
it must propagate unavailability and may not replace it with zero stock, a baseline or a point
forecast passed off as a calibrated bound. Phase 10 must freeze its chosen p, scenarios, costs,
schedule and policy before Phase 13; the approved uncertainty grid does not select the inventory
policy.

These quantiles describe **prefixes anchored at the forecasting origin**. At a later daily
review inside a saved H14 block, a P-day suffix is a different error population: q_P for h1..P
cannot be reused as a calibrated h(t+1)..h(t+P) bound. Phase 10's daily issuance/suffix calibration,
event ordering, final-window truncation and state replay need their own authorized design.
This task neither adds origins nor supplies an unreviewed rolling-origin workaround. A supported
course demonstration may use only origin-anchored prefixes until that handoff gap is resolved.
No inventory outcomes, service levels, costs or savings are computed here.

## 8. Dependence, sparse evidence and diagnostic contract

The windows share store populations and contemporaneous calendar shocks; within-store errors
are serially dependent. Only one/two earlier origins calibrate and two/one later origins assess.
All origins are Fridays, so horizon and weekday are confounded. Sunday Open=1 samples are tiny
and selected. Promotions, holidays and changing closure patterns can shift error distributions;
pooling stores does not erase these shifts. LightGBM's recorded h10 weakness remains visible;
no interval adjustment or model change is justified by that finding alone.

Approved diagnostics, separately for Fit A/B and calibration/assessment:

- Per h and raw/operational branch: expected target count, observed keys, label-eligible count
  (derived without requiring forecast availability),
  forecast availability, interval availability, usable hit denominator, hits and coverage.
  Report interval availability against all eligible labels even when no interval exists.
- Inclusive hits (`lower <= actual <= upper`), lower/upper tail misses, mean/median width and
  support/zero-width counts on evaluable rows. Zero denominator produces null coverage; it is
  never 0% or 100%. All widths and coverage are empirical outputs for future implementation.
- Per h: calibration n, distinct stores/origins, observed Open=0/1/unknown counts, missing reasons,
  ranks and quantile availability. Report poor Sunday support without aggregating it away.
- Per k,p: total Store-origin paths, complete/excluded prefixes, calibration n/store/origin
  counts, assessed complete actual totals, bound availability, inclusive `sum(actual) <= U_k`
  hits and upper misses. Optionally report Target coverage separately, never label it U coverage.
- Per assessment origin: coverage and widths by h/k, raw-primary completeness and operational
  completeness, h2/h9/h10 diagnostics and closed-branch assumption violations. Pooled diagnostics
  remain row/path weighted, with explicit denominators and origin-specific results alongside.

The current export contains no Promo, holiday or store-segment metadata. Record those diagnostics
as unavailable rather than inferring them from weekday or joining a full source dataset. Any
later approved covariate diagnostics must use a separately scoped development-only projection
and a declared availability contract.

No IID standard errors, significance claims, binomial confidence intervals or reliable temporal
bootstrap claims are permitted. Dependence-aware bootstrap would require defensible blocks and
more temporal replication; independently redrawing rows/days would lose dependence.
[FPP3's block-bootstrap discussion](https://otexts.com/fpp3/bootstrap.html) motivates that
distinction, but this plan does not define a bootstrap with only one/two calibration origins.
Report descriptive counts and coverage limits; do not invent a numerical coverage acceptance
threshold or claim the approved nominal levels have been achieved.

## 9. Failure and publication policies

| Condition | Approved response |
|---|---|
| Missing residual/label/key or an incomplete path | Daily: exclude the affected component; unaffected eligible horizons remain usable. Cumulative: exclude any prefix containing the missing component and report why; a later missing day does not erase a complete shorter prefix. Missing assessment labels give null hit indicators and explicit unavailable denominators. |
| Too few calibration samples or rank outside 1..n | Null quantile/bounds for that stratum with `insufficient_calibration` or `quantile_rank_unavailable`; keep counts. No rank clamping, borrowing, baseline or model fallback. |
| Calibration labels later than issuance, own assessment labels included or unexpected windows | Reject the run before calibration/publication with `chronology_violation`. An issuance earlier than required calibration history is unsupported, not silently recalibrated on a shorter history. |
| Provenance/hash/identity mismatch, duplicate keys, inconsistent masks/signs/routing or a claimed-complete malformed path | Fail integrity checks before fitting tables or publishing official outputs. Preserve originals; do not repair records or regenerate forecasts. |
| Nonfinite forecast/residual | Never treat it as a valid sample. Explicitly unavailable components invalidate their prefix; a saved record claiming eligibility despite nonfinite components is an integrity failure. Nonfinite estimator results invalidate the stratum/output. |
| Negative issued point despite frozen nonnegative raw/routed contract | Integrity failure; do not add a new point-forecast clipping policy. |
| Bound lower > upper, nonfinite bound or negative width | Null affected output with `invalid_bounds`, visibly flag failure and prohibit downstream use. Do not swap or force bounds around the point. |
| Unsupported h/k/p/L/P | Reject the request with supported-domain details. Do not truncate horizons or substitute another level. |
| Unknown/unverified operational Open | Operational result unavailable unless a supported schedule or the explicit approved replay assumption applies; raw Open=1-calibrated audit output remains separate. |
| Adverse coverage/width diagnostics | Report and request methodology review; no automatic widening/narrowing, retuning or model mixing. |

Expected per-stratum unavailability may coexist with available strata, with run status
`complete_with_unavailable_strata` and explicit reasons. Fatal integrity/chronology failures
publish no calibration tables, intervals, official diagnostics or new current-run pointer.
An optional failure-only log must be marked failed and cannot be consumed as uncertainty output.
Stage a fresh immutable run directory, verify outputs, publish the manifest last and update a
current-run pointer only after success. Preserve prior immutable runs; never leave a stale
pointer appearing to describe a failed/new run.

## 10. Implementation artifacts and provenance

Ignored root: `data/processed/uncertainty/<run_id>/`, following
[data artifact conventions](../../data/README.md). The original design and approval-sync
checkpoints generated no uncertainty files. The authorized implementation command now publishes
immutable, ignored run directories here and updates `current.json` only after validation.
All error/bound/stock fields use the source Sales monetary scale; no physical units.

| Artifact | Keys and minimum content |
|---|---|
| `calibration_config.json` | Approved policy `phase-8-uncertainty-v1`, frozen selected identity/recipe hash, Fit A/B window/date sets, masks/signs, pooling/rank conventions, levels, minimum samples, no-fallback rules, support/routing/schedule assumptions and the pending Fit B implementation/results review gate. Includes the split specification. |
| `daily_residual_quantiles.csv` | `(fit_id, horizon, tail_level)`; error population, n/distinct stores/origins, last calibration label, rank, nullable signed quantile, availability/reason and policy/model identity. |
| `cumulative_error_quantiles.csv` | `(fit_id, k, p)`; operational prefix definition, total/complete/excluded paths, n/stores/origins, rank, nullable signed quantile, completeness/schedule scope and identities. |
| `daily_intervals.parquet` | `(fit_id, Store, forecast_origin, Date, interval_kind)`, kind raw/operational; h, point, pre-support/post-support endpoints, width, clipping/availability/reason, schedule and fit/model provenance. Assessment labels/masks/hits are joined only after bounds are fixed and clearly marked outcome fields. |
| `cumulative_uncertainty.parquet` | `(fit_id, Store, forecast_origin, k, p)`; D/q/U/SafetyStock/Target, issued-prefix completeness, availability/reason, units/schedule and fit/model provenance. Actual cumulative Sales/errors/hits are later assessment fields, never issuance inputs. |
| `coverage_diagnostics.csv` | `(fit_id, role, assessment_origin, population, h_or_k, p_or_tail_scope, diagnostic)`; denominators, hit/tail/width counts and summaries, sample/availability reasons. `role` distinguishes calibration descriptive from chronological assessment; null values retained. |
| `manifest.json` | Run status, all input/output paths and SHA-256 hashes, selected/candidate manifest lineage, config and fitted-table hashes, code revision/source hash/modified-worktree state, command, Python/package versions and uv.lock hash, counts/date ranges, schedule provenance and explicit no-holdout/no-refit flags. |

Verify every Phase 7 published input and original candidate manifest/output identity, retain
legacy provenance disclosures, and never modify the selected exports or source datasets. Read
only the bounded development artifacts required by this design. The manifest must distinguish
raw model configuration identity from file hashes, policy identity from fitted-table identity,
and calibration dates from assessment dates.

Use deterministic key sorting, signed float64 values, ascending-h prefix summation and exact
integer ranks; canonical JSON configuration hashing (UTF-8, sorted keys, no nonfinite JSON values)
must have a specified serialization in implementation review. No stochastic algorithm is used:
seed is `not_applicable`. Record environment/lock identity for numerical reproducibility; runtime
IDs/timestamps and library-dependent Parquet bytes need not be identical across separate runs.

Freeze the approved policy hash only after it is implemented and validated; freeze Fit B
quantile-table hashes only after separate external implementation/results review. Carry
sample/failure flags into the frozen package; freezing does not turn unavailable strata into
available ones. Phase 13 must verify that package before any separately authorized outcome
release.

## 11. Fixture-test design and implementation acceptance

These fixture scenarios were approved as future acceptance criteria at design review. The
implementation and test evidence for this checkpoint is summarized in Section 15 and recorded
numerically in PROGRESS:

1. Signed errors: positive underprediction and negative overprediction for raw and routed paths;
   reject inconsistent saved signs/identity/masks.
2. Exact chronology: approved three windows, labels <= issue origin, targets > origin, reject
   own-window/later assessment contamination and earlier unsupported issuances.
3. Quantiles: hand-sorted fixtures, ties, exact two-sided ranks and p-grid upper ranks; n=39/40
   daily and n=49/50 cumulative distinguish valid ranks from the approved sample floors.
4. Nonnegative support: clip both endpoints, retain zero width/pre-support values; the point
   need not be enclosed. Invalid/nonfinite/inverted bounds remain unavailable.
5. Sparse strata: no cross-horizon/store/baseline fallback; null values/reasons and denominators
   survive serialization and downstream handoff.
6. Incomplete paths: absent key is not zero; missing h invalidates every prefix containing it;
   a later missing day leaves a shorter prefix usable.
7. Dependence: offsetting within-path signed errors can cancel and coherent errors accumulate;
   prefix-quantile results differ from summing daily upper limits or resampling daily errors.
8. Horizon/domain: k<=14, L=2..7, R=1 and P=3..8; unsupported requests reject and suffixes cannot
   masquerade as origin-anchored prefixes.
9. Raw/operational separation: known closure routes only operational bounds; unknown schedule
   is unavailable; raw recursion/forecasts are unchanged. Nonzero closed actuals remain recorded
   assumption violations, not overwritten zeros.
10. Diagnostics: inclusive hits/ties, zero denominator -> null, availability denominator
    includes eligible missing intervals, closed and open branches reported separately.
11. Determinism: input-row permutation/ties preserve values/ranks with canonical sorting;
    fixed environment preserves numerical results and logical config identity.
12. Source immutability: before/after hashes of selected and candidate artifacts unchanged;
    legacy manifest limitations remain visible.
13. Manifest/hash integrity: missing/tampered artifacts, recipe/run mismatch or malformed
    masks fail before calibration and before publication; no new official pointer/results.
14. Holdout firewall: synthetic post-July-3 labels are excluded/rejected before calibration;
    changes to protected fixture outcomes cannot alter any development result. Fixture sentinels
    prove no protected source path is opened or hashed.
15. Publication: stage/output verification/manifest-last behavior, partial-stratum status,
    fatal failure with no official artifacts and preservation of prior immutable runs.

With PR #14 integrated, implementation acceptance requires these fixtures, normal locked quality
checks, one authorized development-only uncertainty run, complete provenance and
chronological diagnostics with limitations. No numeric coverage-passage threshold is currently
approved. External review must adjudicate usefulness and failures before freeze/closeout.

## 12. Historical draft ADR-021 — superseded by accepted ADR-021

**Historical status at the original PR #14 design checkpoint: PROPOSED / AWAITING APPROVAL.**
This draft is superseded by accepted [ADR-021](../../docs/DECISIONS.md#adr-021--chronological-empirical-forecast-uncertainty-and-conditional-operational-replay),
which is authoritative for current methodology. The historical wording below records the draft
recommendation before external approval; it does not describe current approval status.

**Context:** Development selection under ADR-020 chose a frozen global LightGBM method; ADR-015
protects the final holdout and ADR-016 requires cumulative errors preserving path dependence.
Three selected development origins provide sparse and dependent raw-primary evidence, while saved operational
paths are complete under a historically unverified opening-schedule availability assumption.

**Draft recommendation at that checkpoint:** adopt sections 4–10: earlier-window Fit A/B calibration, pooled signed
horizon order statistics for marginal daily 95% intervals, complete operational-prefix upper
quantiles for the small service grid, explicit sample floors/no fallback, conditional schedule
replay, descriptive coverage and Fit B/policy freeze. All numerical and operational choices
remain proposals until approved; accepted point-model methodology is unchanged.

**Consequences:** simple auditable asymmetric uncertainty and preserved within-path dependence;
unavailable sparse horizons, fragile pooled tails, weak temporal replication and no conformal,
per-store, simultaneous, cycle-service or production guarantees. Rolling daily-review suffix
calibration and actual origin-time schedule availability remain separate review questions.
Implementation and final evaluation need their own authorizations.

## 13. Methodology approval-sync checkpoint (historical)

At the approval-sync checkpoint, PR #14 combined the Phase 7 closeout and Phase 8 design
integration. That task updated the accepted Phase 8 policy/status only, generated no uncertainty
artifact and stopped before implementation. Its quality-check results are recorded in
[PROGRESS](../../docs/PROGRESS.md#phase-8-design-delivery-validation). PR #14 has since integrated;
current implementation evidence appears in Section 15.

## 14. Numbered approval checklist

ADR-021 accepts the listed methodology and inherited contracts. Fit B's actual fitted tables
remain pending a separate external implementation/results review before freeze.

1. **Accepted in ADR-021 — daily interval method:** signed residual, two-sided
   marginal 95% intervals for each h, clipped saved raw forecast and nonnegative bounds.
2. **Accepted in ADR-021 — quantile convention:** exact outward (n+1) order
   ranks, ties retained, no interpolation/clamping; no conformal guarantee.
3. **Accepted in ADR-021 — calibration/assessment chronology:** Fit A v1 -> v2;
   Fit B v1+v2 -> v3, with no own/later targets in calibration.
4. **Accepted in ADR-021 — pooled calibration:** equal Store-origin weights
   within exact h or k, no store/segment normalization or cross-horizon borrowing.
5. **Accepted in ADR-021 — sample floors/fallback:** daily n>=40; cumulative
   complete-prefix n>=50; invalid ranks/unavailable strata stay null; no fallback.
6. **Inherited from accepted ADR-013/017/020 — raw/operational definitions:** observed Open=1
   raw-primary mask versus routed operational error mask, signed actual-minus-forecast errors,
   unchanged raw recursion/point identity and explicit missingness.
7. **Accepted in ADR-021 — cumulative population:** all-store complete
   operational prefixes, conditional on the explicit offline known-opening replay assumption;
   no replacement by the small raw-complete cohort.
8. **Accepted in ADR-021 — one-sided service quantiles:** exact upper (n+1)
   ranks with p={0.90,0.95,0.98}; signed q retained; nominal parameter, not verified cycle service.
9. **Accepted in ADR-021 — diagnostics:** inclusive coverage/width/tail and
   availability denominators, fit/assessment/origin/open-branch separation; no IID inference
   or pretense that model-selected development origins are an untouched test.
10. **Accepted in ADR-021 — freeze/provenance:** immutable approved policy, then Fit B tables
    only after separate external implementation/results review; no v3 recalibration,
    hash-verified inputs/outputs and atomic publication rules.
11. **Inherited from accepted ADR-016 — Phase 10 equations/domain:** monetary D/U/SafetyStock/
    Target, R=1, L=2..7, P=3..8 <=14; cumulative errors rather than sums of marginal uppers.
12. **Inherited from accepted ADR-015 — protected Phase 13 boundary:** no holdout outcomes
    before separately authorized sequential release of the fully frozen pipeline/policies.
13. **Accepted in ADR-021 — operational daily replay routing:** explicit
    assumed-known Open=0 -> [0,0], Open=1 copies raw, unknown remains unavailable; closed
    turnover is not latent/physical demand.
14. **Unresolved schedule provenance, with mandatory boundary — actual future Open availability:**
    separately reviewed origin-known schedule or a separately approved synthetic/conditional
    schedule not derived from protected future actual Open; absent an authorized schedule,
    operational outputs requiring future Open remain unavailable. This dataset cannot establish
    historical schedule availability. The development-only conditional replay is not a Phase 13
    authorization.
15. **Unresolved with alternatives — later daily Phase 10 review:** authorize fresh issuance/
    suffix calibration in its own design, or restrict this package to origin-anchored prefixes;
    no reuse of q_P as an unvalidated later suffix bound.
16. **Accepted in ADR-021 — implementation/artifact/failure contract:** fixtures
    and bounded development-only run after PR #14 integration, explicit null/fatal statuses, no automatic
    adverse-diagnostic correction and external review before freeze/Phase 8 closeout.

## 15. Implementation checkpoint - 2026-10-06

Phase 8 is **IMPLEMENTED / UNDER REVIEW**. The runner reads only hash-verified Phase 7 selected
development artifacts, checks candidate-manifest lineage, masks, residual signs, routing and the
July 3 cutoff, then calculates the fixed Fit A/Fit B estimators. It does not read source datasets,
refit the model, change the selected candidate, or access the protected holdout. The accepted
LightGBM identity is `global_lightgbm_gbdt_regression_l1`.

The reproducible entry point is `python scripts/run_forecast_uncertainty.py`. The canonical successful run
`phase8-impl-20261006-final` is under the ignored `data/processed/uncertainty/` root and is selected
by `current.json`. The earlier implementation-validation run remains preserved as a prior immutable
run. The canonical run contains the six data/config outputs and manifest-last provenance package
defined above. Its input snapshots were SHA-256 checked before and after publication and remained
unchanged. Quantile availability,
chronological diagnostics, output hashes and detailed data counts are recorded in the
[Phase 8 implementation checkpoint in PROGRESS](../../docs/PROGRESS.md#phase-8-development-only-implementation-checkpoint---2026-10-06).

Fit A's h2, h3 and h9 daily tails remain unavailable at the approved minimum sample size; every
other daily stratum and all cumulative strata are present for this run. These empirical assessment
results do not establish a passage threshold or a coverage guarantee. Saved Open values are used
only under `saved_source_open_assumed_known_at_origin` for conditional historical development
replay. Fit B tables, diagnostics, hashes and availability remain **unfrozen** pending external
implementation/results review. Phase 8 remains active until that review, PR integration and
explicit closeout. Phases 9-10 and final-holdout evaluation have not started.

The authorized Phase 8 fixtures and whole-repository validation run with this implementation;
actual check results are recorded alongside its implementation checkpoint in PROGRESS.

## 16. Targeted provenance/results-review follow-up - 2026-10-06

PR #15 remains open and unmerged. A post-computation integrity pass now reruns the allowlisted
Phase 7 verifier after estimation and staged-output verification, compares the full input-lineage
snapshot to the pre-computation snapshot, and fails before the run manifest, run-directory publish,
or `current.json` update if any referenced input changed. A fixture mutates an upstream artifact
during computation and confirms failed publication preserves earlier runs and the prior pointer.

The new canonical run and all empirical daily, operational and cumulative assessment values are
recorded in the [provenance/results follow-up in PROGRESS](../../docs/PROGRESS.md#phase-8-targeted-provenance-and-results-review-2026-10-06).
Both prior immutable runs remain unchanged. The old canonical run's source hash matched the code
before this fix; it differs from the post-fix source hash recorded by the new run. ADR-021,
Fit A/Fit B chronology, selected LightGBM identity, conditional saved-Open assumption and holdout
firewall are unchanged. Fit B remains unfrozen pending external results review.

## 17. External results acceptance and Fit B freeze — 2026-10-07 (historical acceptance checkpoint)

PR #15 is integrated into `main` at squash-merge commit
`c694f5922a1c1e58ffaf9c2437fd9698ca3e5821`. The external reviewer decision supplied for the
canonical numerical results is **ACCEPT**. Independent review covered all 56 daily quantiles, 84
cumulative quantiles, 62,440 issued daily records, 93,660 cumulative records, and all 392
diagnostics. The Fit B fitted quantile values are frozen for canonical run
`phase8-impl-20261006-provenance-review` with this identity:

| Identity | SHA-256 |
|---|---|
| Run manifest | `63a00fc8c50ccff99360cd8790498e977e08ec6a9846780a4e1a8ab3498d71c2` |
| Daily quantile table | `5c985c912d14b502a5d370090353624907e7fddd6d0d8552c102ee3a1ad7eda8` |
| Cumulative quantile table | `1a0bba7916b498f2048f080dcd3b24f6cd47472d2f71fca92b94f1b678cb70ff` |
| Canonical policy/config identity | `49f4811bf7b01ffe6472ea76233eefa50e211207aa0b6246dada934cd4611d93` |
| Config file SHA-256 (`calibration_config.json`) | `afe563632a2ebff937f1500f568d53cdb93be35d6dc299654464c2615ae64a08` |

The last row is the serialized file hash; it is distinct from the canonical policy/config identity.
The immutable run's manifest and config retain their publication-time pending-review and
unfrozen flags. This dated acceptance record freezes the fitted values for the listed identities;
the run directory, quantiles, source artifacts, manifest and current pointer were not changed or
regenerated.

The accepted assessment still has limitations: Fit B raw-primary daily coverage is
12,263/13,437 (91.26%), below nominal 95%; conditional saved-Open operational pooled coverage is
closure-inflated; h2/h9 use 65/64 calibration rows from only 33/32 distinct stores; and origins and
stores are dependent. These are descriptive empirical results, not conformal, per-store, or
production guarantees. Cumulative quantiles authorize origin-anchored prefixes only; they do not
authorize Phase 10 daily-review suffix calibration. The ADR-015 final-holdout firewall remains in
force, and no Phase 9/10 work has started.

Phase 8 was **REVIEWED / FORMAL CLOSEOUT PENDING** at this historical acceptance checkpoint.
The subsequent explicit closeout is recorded in Section 18.

## 18. Formal closeout — 2026-10-07

### Verified integration and external acceptance

At closeout, `origin/main` was `4dd7717fed57ff3b1f14789b980772c1968f3cba`. GitHub showed both
implementation PR #15 and results-acceptance PR #16 as merged. The verified squash-merge commits
are:

| Pull request | Merged commit | Evidence |
|---|---|---|
| [PR #15](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/15) | `c694f5922a1c1e58ffaf9c2437fd9698ca3e5821` | Phase 8 implementation integrated; external numerical review later accepted the canonical results |
| [PR #16](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/16) | `4dd7717fed57ff3b1f14789b980772c1968f3cba` | Independent results acceptance and Fit B freeze recorded; this commit is a child of the PR #15 merge |

The independent reviewer ACCEPTED all 56 daily quantiles, 84 cumulative quantiles, 62,440 issued
daily interval records, 93,660 cumulative records, and 392 diagnostics. The merged main branch
contains the accepted Fit B freeze record. This closeout does not change ADR-021 or the selected
`global_lightgbm_gbdt_regression_l1` recipe.

### Canonical run identity verification

The approved canonical run is `phase8-impl-20261006-provenance-review`. Its immutable local
artifacts were available and checked without regenerating them:

| Identity | Expected SHA-256 | Local verification |
|---|---|---|
| `manifest.json` | `63a00fc8c50ccff99360cd8790498e977e08ec6a9846780a4e1a8ab3498d71c2` | Match |
| `daily_residual_quantiles.csv` | `5c985c912d14b502a5d370090353624907e7fddd6d0d8552c102ee3a1ad7eda8` | Match |
| `cumulative_error_quantiles.csv` | `1a0bba7916b498f2048f080dcd3b24f6cd47472d2f71fca92b94f1b678cb70ff` | Match |
| Canonical policy/config identity | `49f4811bf7b01ffe6472ea76233eefa50e211207aa0b6246dada934cd4611d93` | Match to the config's self-excluding canonical identity |
| `calibration_config.json` file | `afe563632a2ebff937f1500f568d53cdb93be35d6dc299654464c2615ae64a08` | Match |

The immutable manifest retains `external_fit_b_results_review_pending=true` and
`fit_b_quantiles_frozen=false`, the values recorded when the run was published. The later
governance freeze applies to the listed identities and does not rewrite or regenerate the manifest,
configuration, quantile tables, other run artifacts, or current pointer.

### Explicit closeout decision and limitations

Phase 8 is **COMPLETE** as of 2026-10-07. The closeout follows verified PR #15/#16 integration,
independent results acceptance, the exact Fit B identity checks above, and confirmation that the
holdout boundary remains intact. No Python implementation, calibration result, quantile table,
model artifact, or dependency is changed by this documentation closeout.

The following limitations remain part of the accepted result:

- Fit B raw-primary coverage is 12,263/13,437 (91.26%), below nominal 95%.
- Sunday h2/h9 calibration is sparse: 65/64 rows from only 33/32 distinct stores across two
  origins.
- Forecast errors are dependent across stores and forecast origins.
- Operational coverage is a conditional historical replay assuming saved source Open was known
  at origin; deterministic closure routing inflates pooled coverage.
- The results provide no conformal, per-store, production, or service-level guarantee.
- Cumulative quantiles are valid only for approved origin-anchored prefixes. No later daily-review
  suffix calibration is authorized.
- The protected 2015-07-04 through 2015-07-31 final holdout remains unreleased.
- The target is monetary Sales turnover, not SKU-level physical demand.

Phase 9 remains PLANNED and not started; separate design and authorization are required. Phase 10
also remains unstarted. Neither phase is approved or initiated by this closeout.
