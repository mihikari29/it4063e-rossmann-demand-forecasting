# Progress and Verified Results

This is the current evidence summary, not an execution diary. Results below are retained from
reviewed development records; this cleanup does not rerun historical analytics or inspect source
or artifact contents. Git retains implementation/review history. Original structured manifests
and the runtime's pinned identities retain machine-readable provenance.

## Current status

| Workstream | Completed evidence | Still incomplete |
|---|---|---|
| Analytics and local applications | Phases 0–12 complete: acquisition/validation, preparation/EDA, features, three-model comparison/selection, uncertainty, scenarios, inventory and local services/API/dashboard | Final course delivery is not complete. |
| Scenario comparison | Common population, metrics, restricted fixture verifier, fixture preparation/independent reference verification and copy-safe provider bridge reviewed/integrated | No real-data scenario experiment; real preparation/verification/binding and analysis remain unauthorized. Volume segmentation remains blocked. |
| Weekly STL | Diagnostic/provider/preparation reviewed and integrated; one-use custodian readiness corrections integrated, focused Sol 6.1 re-review unrecorded | No real development bundle, provider binding, Rossmann STL run or published STL findings |
| Controlled synthetic demo | Bundle, provider/services, FastAPI and separate Streamlit dashboard reviewed/integrated; minor unit-label/test corrections integrated | Independent Sol 6.1 corrective acceptance and Milestone B closeout unrecorded; staging/release Milestone C unauthorized |
| Final evaluation | Input/provider, fresh-fit issuance, uncertainty/target fixture milestones integrated | Independent Sol 6.1 uncertainty/target review and remaining milestones; Phase 13 PLANNED / NOT APPROVED; no rehearsal, protected release or final evaluation established |
| Reporting/public delivery | Development evidence and local demonstration available | Final monitoring/report, public API/dashboard URLs, PDF, slides and final presentation incomplete |

The protected period is **2015-07-04–2015-07-31**. Earlier descriptive exposure is disclosed in
[EDA findings](EDA_FINDINGS.md); it authorizes no new reads or model selection. Current runtime
exposure remains localhost. [Remaining deliverables](PROJECT_PLAN.md) and the three
[active plans](../plans/active/) own the next approvals.

Integrated robustness corrections reject invalid LightGBM history/model origins before recursive
prediction, validate original inventory periods/horizons before narrowing, and enforce source Store,
Id and weekday domains. The last implementation record still requests independent Sol 6.1
re-review; integration alone does not establish it. The separate large-Store identifier finding
and later audit items were not implemented in that scope.

## Data and feature foundation

The official snapshot contains 1,017,209 training rows, 41,088 competition-test rows and 1,115
metadata stores. Acquisition/validation and preparation evidence is retained in
[acquisition](DATA_ACQUISITION.md), [validation](DATA_VALIDATION.md) and [EDA](EDA_FINDINGS.md).
Sparse dates, source nulls and valid spikes were preserved. The
[29-predictor feature contract](FEATURE_CONTRACT.md) uses exact prior dates and complete calendar
windows. Development model reads stop at July 3, and fit/history inputs stop at each origin.

## Forecast development results

Three non-overlapping H14 windows use origins May 22, June 5 and June 19, with targets ending
July 3. Each contains 15,610 observed targets; open-label denominators are 11,678, 13,438 and
13,437. All candidates and the three-way common population had **100%** forecast availability
in each window. Pooled metrics use 38,553 common observed Open=1 labels, without averaging window
scores. MAPE includes all 38,553 positive-actual rows, with no zero-actual exclusions; WAPE is a ratio.

| Candidate | Pooled MAE | Pooled RMSE | MAPE | WAPE |
|---|---:|---:|---:|---:|
| Seasonal Naive | 1,681.2703 | 2,416.9677 | 26.2671% | 0.232748 |
| Additive Holt-Winters | 1,281.7446 | 1,708.3073 | 18.3669% | 0.177439 |
| Global LightGBM | 871.0612 | 1,350.9138 | 11.3531% | 0.120586 |

The accepted selection rule retained Seasonal Naive over Holt-Winters because the latter exceeded
the h8–14 regression cap, then selected LightGBM: 48.1903% pooled MAE improvement over Seasonal
Naive, three window wins, all window/horizon-block caps passed. These are transparent project
heuristics chosen after initial candidate results, without significance or preregistration claims.
The operational acceptance applies to an offline CPU course demonstration, without a measured
production latency, throughput or memory claim.

| Window | Seasonal Naive MAE | Holt-Winters MAE (change; cap) | LightGBM MAE (change; cap) |
|---|---:|---:|---:|
| validation_1 | 1,101.5940 | 1,195.5661 (+8.5306%; pass) | 1,051.4335 (-4.5534%; pass) |
| validation_2 | 2,269.7721 | 1,136.8306 (-49.9143%; pass) | 790.9941 (-65.1509%; pass) |
| validation_3 | 1,596.5170 | 1,501.5664 (-5.9474%; pass) | 794.3741 (-50.2433%; pass) |

The pooled horizon-block comparisons also pass for LightGBM and fail only for Holt-Winters h8–14:

| Horizon block | Seasonal Naive MAE | Holt-Winters MAE (change; cap) | LightGBM MAE (change; cap) |
|---|---:|---:|---:|
| h1–7 | 2,136.3558 | 1,155.6570 (-45.9052%; pass) | 643.0551 (-69.8994%; pass) |
| h8–14 | 1,235.4154 | 1,405.2746 (+13.7492%; fail) | 1,094.4426 (-11.4110%; pass) |


LightGBM is weaker at h2, h9 and h10: MAE **1,572.8966**, **1,707.5285** and **2,280.9889**
on 97, 96 and 3,344 rows, versus Seasonal Naive **861.8763**, **752.7188** and **1,025.8322**.
No per-horizon veto or replacement model was introduced. For reference, the full baseline horizon
profile remains:

| Horizon | Eligible | MAE | RMSE | MAPE | WAPE |
|---:|---:|---:|---:|---:|---:|
| 1 | 3,344 | 672.2425 | 981.3211 | 11.9931% | 0.114442 |
| 2 | 97 | 861.8763 | 1,187.4567 | 14.7578% | 0.108050 |
| 3 | 2,262 | 4,259.5504 | 4,747.9555 | 72.8666% | 0.677632 |
| 4 | 3,344 | 2,307.4554 | 2,739.8971 | 39.9556% | 0.368580 |
| 5 | 3,344 | 2,131.9731 | 2,459.9699 | 38.2207% | 0.362656 |
| 6 | 3,344 | 2,405.0329 | 3,161.1523 | 42.6760% | 0.407425 |
| 7 | 3,344 | 1,765.8403 | 2,232.6592 | 30.0997% | 0.273202 |
| 8 | 3,344 | 832.9013 | 1,125.0257 | 14.0842% | 0.135236 |
| 9 | 96 | 752.7188 | 1,039.2468 | 10.4863% | 0.089113 |
| 10 | 3,344 | 1,025.8322 | 1,418.5733 | 9.7639% | 0.097370 |
| 11 | 3,344 | 1,141.4202 | 1,587.1030 | 11.6617% | 0.122944 |
| 12 | 3,343 | 1,124.9399 | 1,441.6304 | 13.9331% | 0.137552 |
| 13 | 2,660 | 2,460.7320 | 3,971.0272 | 33.6384% | 0.324489 |
| 14 | 3,343 | 1,091.0808 | 1,453.2243 | 13.6778% | 0.136541 |


Holt-Winters completed 3,345 successful fits without warnings or convergence failures; 1,085 of
46,830 internal predictions (2.3169%) were clipped, minimum unclipped value -4,175.2857.
LightGBM's fixed inner tuning ran 109 checkpoints (A:23, B:6, C:40, D:40), selected A at 180
rounds with inner MAE 1,305.1707 and 100% coverage; outer fits had no failures or clipping.

The selected identity is `global_lightgbm_gbdt_regression_l1`: CPU GBDT regression L1, learning
rate .05, 15 leaves, max depth 4, min_data_in_leaf 200, 180 rounds and the fixed 29 predictors.
Selection froze a recipe, without fitting a future July model. Legacy Seasonal Naive/Holt-Winters
manifests lack modern source/lock identity, and the original LightGBM run records a modified
worktree. These provenance limitations remain; no historical manifest was rewritten.

Across 3,345 Store-origin paths, only 96 raw-primary H14 paths are complete (the same 32 stores
at three origins), with 3,249 partial paths. All 3,345 operational paths are complete under the
conditional saved-Open assumption. Partial paths still contribute eligible daily errors.

## Uncertainty assessment

The implementation and numerical results were accepted; **Fit B values are frozen for the exact
accepted artifact**, not refitted on the third development window. Runtime identities remain in
[the pinned artifact catalog](../src/rossmann_forecasting/app/artifacts.py) and upstream bindings;
[uncertainty methodology](../plans/completed/phase-8-forecast-uncertainty.md) defines the estimators.


The run covers 46,830 selected residual-path rows from 2015-05-23 through 2015-07-03, with 38,553
raw-primary Open=1 errors and 46,830 conditional operational errors. Fit A assesses validation_2
(origin 2015-06-05); Fit B assesses validation_3 (origin 2015-06-19). Daily widths below use only
available raw-primary intervals; coverage denominators are the usable assessed interval rows.

| Fit | Open=1 labels | Daily intervals available | Availability | Hits / usable denominator | Empirical coverage | Width n | Mean width | Median width |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A | 13,438 | 12,258 | 91.22% | 10,344 / 12,258 | 84.39% | 12,258 | 4,128.75 | 4,203.37 |
| B | 13,437 | 13,437 | 100.00% | 12,263 / 13,437 | 91.26% | 13,437 | 4,116.49 | 4,152.12 |

Individual horizon diagnostics retain the approved sparse-stratum reasons and expose calibration
sample sizes separately from assessment denominators:

| Fit / horizon | Calibration n (distinct stores) | Assessment Open=1 eligible | Available / usable | Hits / usable | Coverage | Mean / median width |
|---|---:|---:|---:|---:|---:|---:|
| A / h2 | 32 (32) | 33 | 0 / 0 | - | unavailable | - |
| A / h3 | 33 (33) | 1,115 | 0 / 0 | - | unavailable | - |
| A / h9 | 32 (32) | 32 | 0 / 0 | - | unavailable | - |
| A / h10 | 1,115 | 1,114 | 1,114 / 1,114 | 1,084 / 1,114 | 97.31% | 7,382.53 / 7,382.53 |
| B / h2 | 65 (33) | 32 | 32 / 32 | 32 / 32 | 100.00% | 13,870.23 / 13,870.23 |
| B / h9 | 64 (32) | 32 | 32 / 32 | 32 / 32 | 100.00% | 15,183.32 / 15,212.95 |
| B / h10 | 2,229 | 1,115 | 1,115 / 1,115 | 1,069 / 1,115 | 95.87% | 6,873.54 / 6,873.54 |

Both tails at Fit A h2, h3, and h9 remain unavailable as `insufficient_calibration`; their
assessment populations include 33, 1,115, and 32 Open=1 labels respectively, with zero usable
intervals. No coverage value is reported where the issued interval is unavailable. Fit B h2/h9
results use only 33/32 distinct calibration stores across two origins and remain fragile despite
valid support.

| Fit | Operational population | Label-eligible rows | Available / eligible | Hits / usable denominator | Coverage |
|---|---|---:|---:|---:|---:|
| A | Open=1 | 13,438 | 12,258 / 13,438 (91.22%) | 10,344 / 12,258 | 84.39% |
| A | Open=0 | 2,172 | 2,172 / 2,172 (100.00%) | 2,172 / 2,172 | 100.00% |
| A | Pooled | 15,610 | 14,430 / 15,610 (92.44%) | 12,516 / 14,430 | 86.74% |
| B | Open=1 | 13,437 | 13,437 / 13,437 (100.00%) | 12,263 / 13,437 | 91.26% |
| B | Open=0 | 2,173 | 2,173 / 2,173 (100.00%) | 2,173 / 2,173 | 100.00% |
| B | Pooled | 15,610 | 15,610 / 15,610 (100.00%) | 14,436 / 15,610 | 92.48% |

Deterministic closed `[0,0]` routes account for 15.05% of Fit A's pooled usable denominator and
13.92% of Fit B's. Pooled coverage is respectively 2.35 and 1.22 percentage points above the
Open=1 branch. The diagnostics record zero Open=0 / positive-Sales violations for both fits.
This closure-driven increase is conditional-replay coverage inflation, not raw-model accuracy.

Cumulative upper-bound results are coverage of assessed actual operational prefixes `actual_total
<= U_k`. Every cell has 1,115 complete assessment prefixes and 1,115 available bounds; calibration
support is 1,115 prefixes for Fit A and 2,230 for Fit B. There are no unavailable reasons for
k=3..8.

| k | Fit A p=.90 | Fit A p=.95 | Fit A p=.98 | Fit B p=.90 | Fit B p=.95 | Fit B p=.98 |
|---:|---:|---:|---:|---:|---:|---:|
| 3 | 861/1,115 (77.22%) | 970/1,115 (87.00%) | 1,075/1,115 (96.41%) | 1,040/1,115 (93.27%) | 1,079/1,115 (96.77%) | 1,101/1,115 (98.74%) |
| 4 | 1,044/1,115 (93.63%) | 1,070/1,115 (95.96%) | 1,101/1,115 (98.74%) | 1,095/1,115 (98.21%) | 1,102/1,115 (98.83%) | 1,107/1,115 (99.28%) |
| 5 | 1,044/1,115 (93.63%) | 1,084/1,115 (97.22%) | 1,100/1,115 (98.65%) | 1,096/1,115 (98.30%) | 1,101/1,115 (98.74%) | 1,107/1,115 (99.28%) |
| 6 | 1,047/1,115 (93.90%) | 1,091/1,115 (97.85%) | 1,100/1,115 (98.65%) | 1,098/1,115 (98.48%) | 1,107/1,115 (99.28%) | 1,110/1,115 (99.55%) |
| 7 | 1,100/1,115 (98.65%) | 1,105/1,115 (99.10%) | 1,107/1,115 (99.28%) | 1,106/1,115 (99.19%) | 1,110/1,115 (99.55%) | 1,111/1,115 (99.64%) |
| 8 | 1,103/1,115 (98.92%) | 1,106/1,115 (99.19%) | 1,111/1,115 (99.64%) | 1,106/1,115 (99.19%) | 1,110/1,115 (99.55%) | 1,110/1,115 (99.55%) |

Across k=1..14 pooled by the 15,610 assessed prefixes per level, Fit A coverage is 15,009/15,610
(96.15%) at p=.90, 15,271/15,610 (97.83%) at p=.95, and 15,467/15,610 (99.08%) at p=.98.
Fit B coverage is 15,058/15,610 (96.46%), 15,317/15,610 (98.12%), and 15,477/15,610 (99.15%),
respectively. These repeated, dependent prefixes are descriptive, not independent replications or
service guarantees.


Daily intervals are nominal marginal horizon-specific empirical intervals, without conformal,
per-store, simultaneous or service guarantees. Operational diagnostics assume historical source
Open was known at origin. Actual future Open cannot be reused as a planned final-period schedule.

## Synthetic scenarios and inventory results

The accepted generator uses seed **4209**, five paired replicates, eight synthetic families and
a separate historical reference at June 5 and June 19. It produced 82 catalog rows, 2,230 origin
anchors, 91,430 Store-parameter rows and 1,280,020 daily-context rows. Illustrative costs, schedules
and turnover paths remain separate from Rossmann observations and public-demo fixtures.

The accepted simulation contains **383,560** targets/summaries, **5,753,400** ledger rows,
**172** cases and **1,720** comparisons. All tracks are complete; no unavailable/incomplete tracks,
historical Open-assumption violations or post-cutoff outcomes were recorded.

| Reference | Historical-mean policy cost | Forecast policy cost | Forecast minus baseline |
|---|---:|---:|---:|
| Synthetic base | 90,786,517.967853 | 113,929,065.505821 | +23,142,547.537968 |
| Conditional historical replay | 15,100,677.170801 | 19,376,775.902140 | +4,276,098.731339 |

These are **higher simulated holding-plus-shortfall costs**, without evidence of real losses or
savings. Sensitivity differences remain positive: +32.403m (p=.90), +9.034m (p=.98), +22.349m
(L=2), +14.593m (L=7), +25.857m (coverage=1), +23.147m (annual holding=.10), +23.138m (.30),
+12.759m (goodwill=.10) and +33.473m (.75). Cost-only overlays preserve identical stock trajectories.

For baseline/forecast at synthetic base, terminal stock is 8.830303m/7.551179m, terminal pipeline
292.442932m/274.096540m, stock-cost exposure 6.155105m/5.259219m and outstanding procurement
commitment 204.447440m/191.629078m. Exposures stay outside the primary objective. Final positive
receipt is before T for 108,556 tracks, on T for 236,743 and absent for 38,261. All 383,560 final
intervals are right-censored, including receipt-on-T tracks; summary mismatch count was zero.
A representative replay covered 16 tracks and 240 ledger rows.

The [scenario specification](../plans/completed/phase-9-synthetic-inventory.md) and
[inventory specification](../plans/completed/phase-10-inventory-simulation.md) define event order,
standing targets, denominators and terminal treatment. Short episodes, cold starts, dependent
stores, artificial costs and unvalidated uncertainty transport limit business inference.

## Application evidence and unresolved limitations

Shared read-only services, seven API GET routes and five Streamlit screens are complete locally.
The user attested that all five canonical screens passed human visual review; automated checks
are separate evidence. Canonical artifacts are local and ignored. Health reports liveness,
without implying artifact readiness or analytical-view availability.

Controlled synthetic fixtures prove interface contracts and arithmetic only. Their review did not
approve public content or deployment. The restricted scenario Parquet verifier also cannot bound
peak process memory: post-materialization checks reject eventual output only. The original
untrusted-decoder memory requirement remains unresolved; the owner accepted only trusted fixture
use. Matching hashes/receipts/bindings establish consistency, without authenticating custody,
historical availability or real-source permission.

Three late-season Friday origins confound horizon with weekday. Shared stores/date shocks and
sparse Sunday labels limit interval and scenario inference. No final-period metrics, empirical
July coverage, actual inventory, SKU procurement, optimality or production readiness is established.

## Cleanup validation

The cleanup shares the three development metric-summary paths and the two API error handlers,
fixes documentation discovery of deleted tracked files, and consolidates human-facing guidance.
Exact comparison of **18 complete before/after fixture summaries** preserves values, dtypes,
ordering, coverage, reasons and output keys. The isolated locked Python 3.12 suite passed before
and after the refactor: **2,229 passed, 8 skipped, one existing Starlette/httpx warning**. Seven
skips reflect Windows symlink privileges; one is the absent optional canonical-artifact integration.
Final Python 3.14 API/metrics/documentation checks passed **104 tests**, with the same warning.
The checker regression first reproduced the deleted-file count defect and passed after correction.

Locked environment sync, dependency/lock consistency, Ruff lint/format, local-link validation,
16 script help commands and whitespace checks passed. Model algorithms, recipes, feature/uncertainty/
inventory/custody logic, dependencies, CI and runtime exposure remain unchanged. No real-source or
canonical artifact contents, protected outcomes, analytical pipeline, listener or deployment were
accessed/run. Fixture fits use artificial inputs only. No performance improvement is claimed.

Follow-up corrections restore the original missing-field exception types/messages through a shared
metric-table builder, while preserving the Seasonal Naive wrapper's explicit guard. Twenty-nine
regression cases were added: 16 for model-summary errors, three for the baseline guard and ten for
valid tables/schemas. The focused metrics file passed 32 tests; seven forecasting fixture suites
passed 417 tests. Eighteen complete pre-cleanup/current summary comparisons matched exactly.
Targeted documentation wording and decision links were corrected without changing scientific
definitions, proposal math or approval gates. Ruff, formatting, local links, lock/dependency and
whitespace checks passed. Independent reviewer acceptance remains outstanding.
