# Forecast Uncertainty

The implementation and numerical results are accepted and complete. Exact accepted Fit B values remain frozen. This reference defines the daily and cumulative estimators and their distinct interpretation.

[Verified results](../../docs/PROGRESS.md) · [Decisions](../../docs/DECISIONS.md)

## 2. Existing evidence and information boundary

The read-only audit verified the saved Phase 7 manifest and every listed output hash, original
candidate artifacts, selected identity/recipe and residual schema/masks. Hashes and numerical
counts are maintained in PROGRESS, rather than copied into another results table here. The selected model configuration and refit-recipe file hashes remain separate identities;
verify exact upstream runtime bindings rather than a mutable latest pointer.

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

uncertainty contract approves `saved_source_open_assumed_known_at_origin` solely to reproduce existing
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

uncertainty contract accepts empirical signed residual order statistics pooled across stores within each exact
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

Only the chronological evaluation contract approved windows are used:

| Window | Forecast origin | Target dates |
|---|---|---|
| validation_1 | 2015-05-22 | 2015-05-23 through 2015-06-05 |
| validation_2 | 2015-06-05 | 2015-06-06 through 2015-06-19 |
| validation_3 | 2015-06-19 | 2015-06-20 through 2015-07-03 |

uncertainty contract approves two predetermined expanding calibration fits, shared by daily and cumulative
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

The reviewed Fit B tables and diagnostics were accepted and their exact values are frozen.
Fit B remains calibrated on validation_1+2 and assessed on validation_3; no quantiles are refit
on all three windows. Preserve the original immutable publication metadata and runtime pins.
Fit B occurs by the predeclared schedule regardless of Fit A's diagnostics, not as a remedial
adjustment. Do not change levels, ranks, samples, strata or widths after adverse assessment
without a separately approved methodology revision. Poor or unavailable results must be reported
and reviewed; design approval is not an automatic coverage-acceptance decision.

Phase 13 may use only the frozen reviewed policy/tables with its separately approved model
refit/release protocol. This approval does not authorize a July forecast, refit, recalibration,
holdout-derived interval correction or automatic post-origin update.

## 5. Daily two-sided marginal 95% intervals

Under the approved uncertainty contract policy, for each fit and exact h in 1..14:

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
Numerical assessment is recorded in the results summary.

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

For a complete issued operational forecast prefix, use the
[accepted monetary-bound formulas](../../docs/DECISIONS.md#adr-016--inventory-proxy-values-and-cumulative-uncertainty):

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

## 7. Inventory integration

Consumers require exact model/recipe/origin/fit/p/prefix/schedule identities and complete
`D_k, q_p, U_k, SafetyStock_k, Target_k` inputs with reasons/provenance. Keep R=1, L=2..7,
P=L+1=3..8. Missing inputs stay unavailable, without zero/baseline/point-only fallback.
The approved inventory method freezes targets once at origin; later reviews execute the same
target, without borrowing origin-prefix quantiles as calibrated suffix bounds. Historical q on
synthetic stress is explicitly uncalibrated. See the
[inventory specification](phase-10-inventory-simulation.md) for accepted mechanics.

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
[data artifact conventions](../../data/README.md). The implementation publishes
immutable, ignored run directories here and updates `current.json` only after validation.
All error/bound/stock fields use the source Sales monetary scale; no physical units.

| Artifact | Keys and minimum content |
|---|---|
| `calibration_config.json` | Approved policy `phase-8-uncertainty-v1`, frozen selected identity/recipe hash, Fit A/B window/date sets, masks/signs, pooling/rank conventions, levels, minimum samples, no-fallback rules, support/routing/schedule assumptions and the original publication-time Fit B review flag, preserved after later acceptance. Includes the split specification. |
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

These fixtures verify the accepted contract. Numerical evidence is recorded in the results summary:

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

Implementation acceptance requires these fixtures, normal locked quality
checks, one authorized development-only uncertainty run, complete provenance and
chronological diagnostics with limitations. No numeric coverage-passage threshold was approved. External review accepted the recorded results
and exact Fit B freeze, retaining the unfavorable coverage and sparse support.
