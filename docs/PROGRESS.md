# Project Progress

## Current implementation and Git state — 2026-10-06

| Scope | State | Integration |
|---|---|---|
| Phases 0–4 | COMPLETE | On `main`; Phase 3 PR #3/#4, Phase 4 PR #5/#6 |
| Phase 5 — additive Holt-Winters | COMPLETE | PR #7 squash-merged into `main` at `76707a03b7d10dbaa79d3ef26b39e31994431d70`; formal closeout recorded here |
| Repository architecture/governance review | COMPLETE | Integrated with Phase 5 by PR #7 at `76707a03b7d10dbaa79d3ef26b39e31994431d70` |
| Phase 6 — Global LightGBM | COMPLETE | [PR #10](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/10) merged into `main` at `dac71d26bd8a9e43eff7d33592460906ae6fee6f`; [completed plan](../plans/completed/phase-6-global-lightgbm.md) |
| Phase 7 — model selection | APPROVED; implementation not started | [Approved plan](../plans/active/phase-7-model-selection.md), ADR-020; PR #12 is the required integration gate; no final model officially selected |
| Phase 8 and later | PLANNED; not started | Await their dependencies and separate authorization |

At closeout start, the clean `docs/phase-5-closeout` branch was created from fetched latest
`origin/main`; both resolved to `76707a03b7d10dbaa79d3ef26b39e31994431d70`, the actual PR #7
squash-merge commit reported by GitHub. PR #7 is merged into `main`. The merged tree contains the
reusable Holt-Winters forecaster, development runner, evaluation code, and tests. The closeout
changes lifecycle/documentation only: no forecasting algorithm or historical metric is changed, and
no final-holdout forecast or evaluation was performed. Main protection was reported disabled in
the 2026-10-05 branch-metadata snapshot; no settings were changed.

Completed plans under `plans/completed/` preserve their historical approval/results/checkpoint
records, including the [completed Phase 5 plan](../plans/completed/phase-5-statistical-forecasting.md).
PROGRESS is the canonical maintained numerical-results record; duplicated plan tables are dated
snapshots, not separate results to update. No final project model has been selected.

## Immediate next boundary

Phase 5 is formally COMPLETE following PR #7 integration and PR #8 closeout. Phase 6 is **COMPLETE**:
ADR-019 remains accepted, and [PR #10](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/10)
was merged into `main` at `dac71d26bd8a9e43eff7d33592460906ae6fee6f`; its completed plan is
archived.
The Phase 6 development-only results and coverage evidence remain recorded below. Phase 6 closeout
[PR #11](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/11) merged at
`0b8d55144ace29cb8b5367d11aeedc59cfb33a65`. Phase 7 design has started in the
[approved plan](../plans/active/phase-7-model-selection.md) and ADR-020; implementation has not
started, and no final model is officially selected. Implementation may begin only after design
PR #12 integrates into `main`. Phase 8 is not started, and final-holdout evaluation remains
unreleased. The
[historical Phase 6 implementation handoff](PROJECT_PLAN.md#phase-6-implementation-handoff-historical)
records the interfaces and boundary used.

The current forecasting firewall excludes July 4–31 from tuning/selection/calibration and has
produced no final-holdout forecasts/metrics; final-holdout evaluation remains unreleased. Earlier
full-source validation and descriptive EDA
did include those labels; [EDA_FINDINGS](EDA_FINDINGS.md) records that exposure. Do not claim an
entirely never-inspected test set or reuse those full-period cohorts for modeling. ADR-015 defers
the single authorized sequential final evaluation until model, intervals and policies are frozen.

## Branch cleanup inventory

GitHub snapshot, 2026-10-05; cleanup is recommended only after checking unique commits and working
changes. No local or remote branches were deleted in this review.

| Candidate branch | Merged work | Disposition |
|---|---|---|
| `feat/data-preparation-eda` | [PR #2](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/2) | Retire after unique-change check |
| `feat/feature-engineering` | [PR #3](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/3) | Retire after unique-change check |
| `docs/phase-3-closeout` | [PR #4](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/4) | Retire after unique-change check |
| `feat/seasonal-naive` | [PR #5](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/5) | Retire after unique-change check |
| `docs/phase-4-closeout` | [PR #6](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/6) | Retire after unique-change check |

`feat/holt-winters` is active, not a cleanup candidate. The old
`origin/feat/data-acquisition-validation` exists only as a stale local tracking ref: that branch
is absent from GitHub's current branch list. Prune it during authorized maintenance. Main and this
review branch are retained; fresh work should not continue on merged branches.

## Source and Preparation Evidence

- Official raw CSVs remain unchanged and Git-ignored; their four SHA-256 hashes matched the
  documented source snapshot before and after preparation.
- Historical train: 1,017,209 rows, 1,115 stores, 2013-01-01 through 2015-07-31. Test: 41,088
  future-covariate rows, 856 stores, 2015-08-01 through 2015-09-17. Both metadata joins preserve
  row counts and unique Store × Date keys.
- The sparse historical output retains all source rows, including closed and open/zero-Sales days.
  No synthetic calendar rows or zero fills were added. Test remains separate and has no Sales or
  Customers.
- The 180-store 184-day gap, 54 open/zero-Sales rows, 11 missing test Open statuses, and 259
  metadata stores unused by test have documented evidence and dispositions. Store 622's original
  missing Open statuses remain null in `test.parquet`; the separate audit output contains 11
  uncertain unanimous historical-context candidates.
- Promo2 details retain structural nulls for all 544 nonparticipants. The 354 paired missing
  competition-open dates remain unexplained and unfilled; three missing CompetitionDistance
  values remain missing.
- Ignored Parquet outputs are reproducible through PyArrow 24.0.0. EDA tables, manifests, and
  figures are local generated artifacts under `reports/eda/`.

## Phase 3 Implementation and Closeout Evidence

- `python scripts/build_features.py` completed with contract `phase-3-v1`: 1,017,209 training
  rows and 41,088 inference rows, preserving input Store × Date keys and the shared ordered
  29-predictor schema. The outputs and manifest are ignored under `data/processed/`.
- Development feature-coverage diagnostics end on 2015-07-03. They record 313,436 nulls each for
  `competition_has_opened` and `competition_age_months` (the 354 jointly missing competition
  metadata stores), 2,558 missing `competition_distance` values, and expected exact-history warm-up
  and sparse-gap nulls. No imputations were introduced. Promo2 produced no invalid/incomplete
  schedule findings in the prepared snapshot; nonparticipants remain inactive despite structural
  schedule nulls.
- For a gap-affected store, all dynamic history fields are unavailable on 2015-01-01; lag 1 resumes
  on Jan 2; lag 7 and the 7-day window resume Jan 8; lag 14 and the 14-day windows resume Jan 15;
  all ten dynamic fields resume Jan 29 after the complete 28-day window exists. No absent dates
  were bridged or synthesized.
- The final holdout remains 2015-07-04 through 2015-07-31 (31,220 store-days). Its audit is
  mechanical only: predictor schema/order, unique keys, and dtype compatibility. No holdout
  distribution or forecast metric was summarized. Development coverage stops July 3.
- The feature runner verified all four raw-source hashes and the three prepared Parquet hashes
  against the approved source snapshot and Phase 2 manifest before and after the build. The raw
  validator also passed without errors. Store 622 Open candidates remain audit fields; inference
  contains no Sales, Customers, or Customers-derived fields.
- Future-known/static inference predictors are materialized for all test rows. Without recursive
  predictions, dynamic values needing exact dates after the forecast origin remain null; later
  recursive steps can supply predictions through the origin-censored history API.
- Repeated deterministic builds produced the same SHA-256 for each corresponding artifact:
  `features_train.parquet` matched its prior build, and `features_inference.parquet` matched its
  prior build. These two distinct artifacts do not share a hash. No holdout distributions were
  summarized.
- Detailed field semantics, roles, dtypes, null behavior, and point-in-time rules are in
  [Feature Contract](FEATURE_CONTRACT.md); the completed execution plan is archived at
  `plans/completed/phase-3-feature-engineering.md`.
- External review follow-up canonicalizes history keys before duplicate/overlap checks, grouping,
  or exact-date lookup: Store IDs are validated positive exact integers representable as int64;
  Dates are parsed as midnight calendar values and stored as datetime64[ns]. The shared key path
  copies inputs and is also used by static predictor assembly. Focused regression coverage now
  includes fractional/out-of-range IDs, canonical Store/Date collisions, valid coercion, and input
  non-mutation.

## Phase 3 Quality Checkpoint (Historical)

- `python scripts/validate_data.py --report reports/validation/rossmann.json`: PASS — 0 errors,
  4 reviewed warnings, 12 informational findings.
- `python scripts/build_features.py`: PASS — raw/interim provenance checks, key preservation,
  matching predictor schemas/dtypes, holdout mechanical audit, and output generation.
- Full suite chronology: 45 passed before the external-review key-canonicalization fix; 56 passed
  after the fix and again at PR readiness, including the key-canonicalization regression cases.
- `ruff check .`: passed; `ruff format --check .`: 45 files already formatted.
- `git diff --check`: passed. Relative Markdown links in changed user-facing documentation: passed.
- Preparation and EDA commands completed against the official data; both notebooks validated and
  executed successfully with cleared committed outputs.

## Phase 4 Scope Confirmation at Closeout

At the Phase 4 closeout checkpoint, only the explicitly approved Seasonal Naive baseline was
implemented; Holt-Winters and later-phase work had not begun. Sales remains monetary turnover at
Store × Date; future Customers remain unavailable to forecasts. Primary evaluation uses actual
source Open=1 observations, while the known-closed zero rule is applied only to the separate
operational forecast after raw generation.

## Phase 4 Implementation and Development Results

- The approved methodology is recorded in accepted ADR-013, which remains unchanged. External
  review found no blocking issue; PR #5 received final approval and merged into `main` at
  `12f80b5fe8a8580b3d8367cd473766decd3ebf31`. The completed execution plan is archived at
  [`plans/completed/phase-4-seasonal-naive.md`](../plans/completed/phase-4-seasonal-naive.md).
- `python scripts/run_seasonal_naive.py` completed successfully against the existing prepared
  Rossmann historical table. The runner read only `Store`, `Date`, `Sales`, and source `Open`, and
  applied the Parquet Date filter through 2015-07-03 before evaluation. It ran exactly the three
  approved development windows and emitted 46,830 observed target records. Generated outputs are
  ignored under `data/processed/seasonal_naive/`; the manifest records the methodology, windows,
  source hashes, and artifact hashes.
- Coverage and primary metrics by window (coverage is available raw forecasts / denominator):

  | Window | Observed targets | Eligible open labels | All-target coverage | Open-label coverage | MAE | RMSE | MAPE | MAPE rows / eligible | Zero rows excluded from MAPE | WAPE |
  |---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
  | validation_1 | 15,610 | 11,678 | 15,610 / 15,610 (100%) | 11,678 / 11,678 (100%) | 1,101.5940 | 1,444.9870 | 15.0088% | 11,678 / 11,678 (100%) | 0 | 0.143224 |
  | validation_2 | 15,610 | 13,438 | 15,610 / 15,610 (100%) | 13,438 / 13,438 (100%) | 2,269.7721 | 3,141.3506 | 36.1046% | 13,438 / 13,438 (100%) | 0 | 0.324782 |
  | validation_3 | 15,610 | 13,437 | 15,610 / 15,610 (100%) | 13,437 / 13,437 (100%) | 1,596.5170 | 2,253.3165 | 26.2135% | 13,437 / 13,437 (100%) | 0 | 0.226393 |

- Pooled eligible development rows: 38,553. Pooled MAE **1,681.2703**, RMSE **2,416.9677**,
  MAPE **26.2671%** (38,553 MAPE rows, 0 zero-actual rows excluded, 100% MAPE coverage), and
  WAPE **0.232748**. These are computed over pooled eligible observations, not averaged window
  metrics.
- Horizon-level eligible counts and metrics (WAPE is a ratio; MAPE is a percent):

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

- All 46,830 observed target records had an available raw forecast (46,830 / 46,830); therefore
  there were no unavailable weekly baseline forecasts, no affected Store × Date rows, and no
  unavailable-store cases to report. Open-labelled forecast coverage was also 100% in each window.
- No final-holdout forecast, score, metric, or target summary was produced. Phase 4 reads are
  restricted to dates through 2015-07-03 before the evaluation layer; only development outputs
  appear in the generated artifact directory.
- Raw Rossmann inputs and Phase 2 `train.parquet` hashes matched their recorded provenance before
  and after the run. The runner wrote only Git-ignored generated files; no raw, interim, or Phase 3
  files were modified, and generated results remain ignored and untracked. `docs/proposal.md` is
  unchanged.
- Validation at Phase 4 completion: full pytest suite **73 passed**; `ruff check .`,
  `ruff format --check .`, and `git diff --check` passed. The Seasonal Naive CLI completed
  successfully with unchanged input provenance. Phase 4 is formally COMPLETE. At the Phase 4
  closeout checkpoint, Phase 5 implementation had not begun; no final-holdout result was produced.

## Phase 5 Statistical Forecasting Approval and Implementation

- Status at approval checkpoint: **APPROVED / IMPLEMENTATION IN PROGRESS**. The user explicitly
  approved the fixed Holt-Winters methodology and its 99% coverage guardrail on 2026-10-05. Phase 5
  implementation and real-data results are recorded below as they are produced.
- The archived design plan is [`plans/completed/phase-5-statistical-forecasting.md`](../plans/completed/phase-5-statistical-forecasting.md).
- A mechanical history-availability audit projected only `Store` and `Date` from the existing
  training feature Parquet and filtered dates to `<= 2015-07-03`. It used no Sales, Open,
  Customers, forecast, metric, or holdout field/value. All 1,115 target Stores in each approved
  development window had at least 28 consecutive observed dates ending at the origin:

  | Window | Target Stores | Origin-row Stores | ≥28 days | 14–27 days | 7–13 days | 2–6 days | 0–1 day | Eligible |
  |---|---:|---:|---:|---:|---:|---:|---:|---:|
  | validation_1 | 1,115 | 1,115 | 1,115 | 0 | 0 | 0 | 0 | 1,115 / 1,115 (100.00%) |
  | validation_2 | 1,115 | 1,115 | 1,115 | 0 | 0 | 0 | 0 | 1,115 / 1,115 (100.00%) |
  | validation_3 | 1,115 | 1,115 | 1,115 | 0 | 0 | 0 | 0 | 1,115 / 1,115 (100.00%) |

- At the approval checkpoint, this date-only result suggested no date-availability coverage loss
  under the minimum-history rule. It did not establish Sales validity or model-fit success;
  numerical failures were then unmeasured. The implementation evidence below records the later
  successful fits. The approved policy has no fallback.
- The audit stopped at 2015-07-03 and did not read holdout Sales. It produced no holdout forecast
  or evaluation; the earlier descriptive exposure is disclosed above.

### Phase 5 Implementation and Development Results

- The approved design is implemented on `feat/holt-winters` under accepted ADR-014. The package
  provides origin-censored, per-Store additive Holt-Winters fitting, latest-contiguous-history
  eligibility, a single internal 14-step forecast operation, clipped raw forecasts with retained
  unclipped values, explicit unavailable reasons, and post-forecast Open routing. There is no
  fallback model. The dependency resolved to statsmodels 0.15.0.
- `python scripts/run_holt_winters.py` completed successfully against the existing Phase 2
  `train.parquet`. Its Parquet projection includes only Store, Date, Sales, and Open, and the Date
  predicate is applied at read time through 2015-07-03. It evaluated the three approved development
  windows and recomputed Seasonal Naive from the reviewed Phase 4 implementation. Raw Rossmann and
  Phase 2 hashes matched before and after the run. No final-holdout forecast, score, or metric was
  produced.
- The run generated 46,830 observed target forecasts and 46,830 internal 14-step path records
  across 3,345 Store-origin fits. All 3,345 fits succeeded; there were no unavailable forecasts,
  fit/forecast failures, warnings, or optimizer non-convergence flags. All three windows achieved
  100% raw and Open-label forecast coverage, above the precommitted 99% coverage guardrail.
- Standalone Holt-Winters metrics (primary population: observed source Open=1 and Sales, with
  available clipped raw forecast):

  | Window | Observed targets | Eligible open labels | Open-label coverage | MAE | RMSE | MAPE | WAPE |
  |---|---:|---:|---:|---:|---:|---:|---:|
  | validation_1 | 15,610 | 11,678 | 11,678 / 11,678 (100%) | 1,195.5661 | 1,617.4146 | 15.2155% | 0.155442 |
  | validation_2 | 15,610 | 13,438 | 13,438 / 13,438 (100%) | 1,136.8306 | 1,483.1660 | 16.9474% | 0.162669 |
  | validation_3 | 15,610 | 13,437 | 13,437 / 13,437 (100%) | 1,501.5664 | 1,974.7435 | 22.5253% | 0.212929 |

- Pooled over 38,553 eligible rows, Holt-Winters MAE was **1,281.7446**, RMSE **1,708.3073**,
  MAPE **18.3669%**, and WAPE **0.177439**. MAPE included 38,553 positive-actual rows, excluded
  zero rows: 0, and had 100% MAPE coverage. Pooled values are calculated over rows, not averaged
  from window metrics.
- Paired comparison uses the identical 38,553 eligible Store-origin-Date rows where both
  recomputed Seasonal Naive and Holt-Winters forecasts were available. A negative MAE difference
  means Holt-Winters MAE is lower; this fixed-candidate development comparison is not final model
  selection:

  | Window | Paired rows | Holt-Winters MAE | Seasonal Naive MAE | Difference (HW - SN) | Relative change | Lower paired MAE |
  |---|---:|---:|---:|---:|---:|---|
  | validation_1 | 11,678 | 1,195.5661 | 1,101.5940 | +93.9721 | +8.5306% | Seasonal Naive |
  | validation_2 | 13,438 | 1,136.8306 | 2,269.7721 | -1,132.9415 | -49.9143% | Holt-Winters |
  | validation_3 | 13,437 | 1,501.5664 | 1,596.5170 | -94.9506 | -5.9474% | Holt-Winters |
  | pooled | 38,553 | 1,281.7446 | 1,681.2703 | -399.5257 | -23.7633% | Holt-Winters |

- Additive forecasts below zero were clipped only for the raw metric forecast; unclipped values
  remain in the audit output. In the full internal paths, 1,085 of 46,830 forecasts (2.3169%)
  were clipped. The minimum unclipped forecast was -4,175.2857. By window, clipping was
  354 / 15,610 (2.2678%), 408 / 15,610 (2.6137%), and 323 / 15,610 (2.0692%), respectively.
- Ignored artifacts and a manifest are under `data/processed/holt_winters/`: observed-key
  forecasts, internal 14-step paths, per-fit and aggregated diagnostics, window/pooled/horizon
  metrics, coverage guardrail, identical-row paired forecasts and metrics, and clipping
  diagnostics. All emitted dates are 2015-05-23 through 2015-07-03; all 46,830 composite keys are
  unique. The generated forecast table does not expose the protected holdout.
- Initial executions exposed two post-fit reporting defects (strict JSON serialization of a
  missing pooled label, and a clipping-rate denominator reference); both were corrected and covered
  by tests. The final real-data runner completed with exit code 0 and regenerated all artifacts.
- Initial Phase 5 implementation checks: full pytest suite **95 passed**;
  `ruff check src tests scripts` and `ruff format --check src tests scripts` passed. Artifact paths
  were verified Git-ignored;
  provenance checks passed before and after evaluation. At this implementation checkpoint, Phase 5
  was **IMPLEMENTED / UNDER REVIEW**, not formally closed. `docs/proposal.md`, reviewed Phase 4 model code/artifacts, raw data,
  and Phase 2 prepared data were not modified.
- External review found that the reusable Holt-Winters API validated horizons from 1–14 but still
  generated a fixed 14-step path. The forecaster now consistently uses the validated
  horizon for model forecasts, output-length validation, and internal path rows, records
  `forecast_horizon` for successful and failed fits, and computes clipping rates over successful
  requested forecast steps. Regression tests cover 7- and 14-step behavior, target bounds, output
  lengths, failed-fit paths, and horizon-aware clipping rates. The approved Phase 5 runner continues
  to request 14 days. Its post-fix rerun reproduced the recorded metrics unchanged: 46,830 forecasts,
  3,345 successful Store-origin fits, 100% availability in every window, and a passed 99% coverage
  guardrail. The ignored fit-diagnostics artifact now includes `forecast_horizon`; artifact hashes
  were regenerated for the updated output schema. Full-repository validation passed: pytest **102
  passed**, `ruff check .`, `ruff format --check .`, `git diff --check`, and relative Markdown-link
  validation across 19 files. No holdout forecast or evaluation occurred; at that review checkpoint,
  Phase 5 was **IMPLEMENTED / UNDER REVIEW**.

## Repository Architecture/Governance Review — 2026-10-05

The [completed review task plan](../plans/completed/repository-architecture-governance-review.md)
records scope and cross-review. Verdict: **READY for the next authorized design task**, not an
authorization to implement Phase 6 or a declaration that Phase 5 is closed.

- Reviewed all listed governance/data docs, active/completed plans, source/script/test/notebook
  structure, and public branch/merged-PR metadata. Current-state, branch, phase, artifact-path,
  terminology and local Markdown references were cross-checked; archived evidence was preserved.
- ADR-015–018 trace the fixes: final evaluation after all choices freeze, disclosed descriptive
  exposure, consistent simulated inventory values/cumulative uncertainty, simpler application and
  work-package boundaries, portable locked environments and fixture CI. AGENTS/WORKFLOW now own
  approval/lifecycle rules; this document owns maintained results, not duplicated plan tables.
- The Phase 6 handoff specifies origin-censored fitting/history, future-known covariates,
  categorical/null adapter design, raw recursion versus Open routing, metric/coverage interfaces,
  outputs, tests and approval. No LightGBM or later-phase module/dependency was implemented.
- Forecast algorithms/configurations and existing numerical evidence were unchanged. Three
  exception clauses gained tuple parentheses for Python 3.12 compatibility. Source hash-only
  verification matched all four documented raw hashes; no data/model pipeline or holdout
  forecasting/evaluation was run for this review.

The continuation recovered the existing dirty review branch at HEAD `3d4fbfd`: 18 modified and
five new files, nothing staged. Full-file rereads, diff/history inspection and a fresh repository-
only Phase 6 handoff audit preserved that work. Two residual ambiguities were corrected: LightGBM
feeds predictions, never unrevealed target actuals; final scheduled preprocessing/model refits may
update fitted state only under the frozen recipe using already revealed training rows. No new
phase scope or methodology search was introduced. The quality gate was rerun after these fixes.

Final checks actually executed:

| Check | Result |
|---|---|
| `python -m pytest` in the original Python 3.14.5 environment | 106 passed; includes four new Markdown-checker fixtures |
| Complete fixture suite in isolated locked Python 3.12.15 / 3.14.5 | 106 passed in each environment |
| `python -m ruff check .` | PASS |
| `python -m ruff format --check .` | PASS; 63 files already formatted |
| `python scripts/check_docs.py` | PASS; local files/directories/common heading anchors across 20 Markdown files |
| `git diff --check` | PASS |
| `uv lock --check` / `uv pip check` | PASS; current lock and compatible installed packages |
| Numbering and math checks | Phase 0–14, proposal 1–30, ADR-001–018 and paired proposal dollar delimiters PASS |

Remaining non-blocking limits: only 42 development target days and prior descriptive holdout
exposure; pooled empirical intervals/simulated policies require their later reviewed designs.
At the review checkpoint recorded here, main protection was not enabled, and stale branch cleanup
needed separate authorization/unique-change checks. PR #7 integration followed by Phase 5 explicit
closeout remained the immediate project gate. Phase 6 had not started.

## Phase 5 Formal Closeout — 2026-10-05

PR #7 was squash-merged into `main` at `76707a03b7d10dbaa79d3ef26b39e31994431d70`. The GitHub
PR metadata's `merge_commit_sha` matches the fetched `origin/main` and the closeout branch base.
Phase 5 is **COMPLETE**; its fixed additive Holt-Winters implementation and development-only
evaluation are integrated. The completed execution plan is archived at
[`plans/completed/phase-5-statistical-forecasting.md`](../plans/completed/phase-5-statistical-forecasting.md).
No final-holdout forecasting or evaluation was performed, and Phase 6 implementation began only
after the separate authorization recorded in its active plan. The historical metric tables and
methodology above are unchanged.

## Phase 6 Global LightGBM Implementation — 2026-10-06

At the implementation checkpoint, Phase 6 was **IMPLEMENTED / UNDER REVIEW** on
`feat/phase-6-global-lightgbm`. The candidate follows
ADR-019 and the [completed Phase 6 plan](../plans/completed/phase-6-global-lightgbm.md). It is a
development candidate only; Phase 7 has not started, and no final project model has been selected.

- `lightgbm>=4.7,<4.8` resolved to LightGBM 4.7.0 in the locked Python 3.14.5 / Windows 11
  environment. The runner writes ignored outputs only under `data/processed/lightgbm/` and
  `artifacts/lightgbm/`; `git check-ignore` confirmed the generated outputs are ignored.
- The exact 29-predictor phase-3-v1 matrix and four frozen trial recipes were used. Inner tuning
  ran 109 recursive checkpoints: A 23, B 6, C 40, and D 40. It selected trial A at 180 rounds
  (learning rate 0.05, 15 leaves, max depth 4, min_data_in_leaf 200), with inner open-label MAE
  **1,305.1707** and **100%** open-label coverage. Trials C and D reached the 400-round cap; A and
  B stopped after five checkpoints without strict improvement. Every fit succeeded.
- The predeclared outer refits completed for all three origins. Each 14-day window emitted 15,610
  target rows; the 46,830 pooled target rows include 38,553 eligible observed source Open=1 labels.
  Open-label coverage was 100% in every window (11,678/11,678; 13,438/13,438; and
  13,437/13,437), exceeding the frozen 99% guardrail. There were no unavailable forecasts and no
  negative-output clipping events.

Standalone development metrics use the primary population of observed source Open=1 and Sales with
an available clipped raw forecast. MAPE is reported as a percentage; WAPE is a ratio.

| Scope | Eligible rows | Open-label coverage | MAE | RMSE | MAPE | WAPE |
|---|---:|---:|---:|---:|---:|---:|
| validation_1 | 11,678 | 100% | 1,051.4335 | 1,512.2577 | 12.5686% | 0.136702 |
| validation_2 | 13,438 | 100% | 790.9941 | 1,193.4810 | 10.9700% | 0.113184 |
| validation_3 | 13,437 | 100% | 794.3741 | 1,350.5876 | 10.6797% | 0.112646 |
| pooled | 38,553 | 100% | **871.0612** | 1,350.9138 | 11.3531% | 0.120586 |

The pooled values are recomputed over eligible rows. Paired baseline summaries use the identical
38,553 eligible Store × Date rows with both forecasts available; these are descriptive Phase 6
development comparisons, not final model selection.

| Scope | Paired rows | LightGBM MAE | Seasonal Naive MAE | Holt-Winters MAE | LightGBM MAE change vs SN | vs Holt-Winters |
|---|---:|---:|---:|---:|---:|---:|
| validation_1 | 11,678 | 1,051.4335 | 1,101.5940 | 1,195.5661 | -4.55% | -12.06% |
| validation_2 | 13,438 | 790.9941 | 2,269.7721 | 1,136.8306 | -65.15% | -30.42% |
| validation_3 | 13,437 | 794.3741 | 1,596.5170 | 1,501.5664 | -50.24% | -47.10% |
| pooled | 38,553 | **871.0612** | 1,681.2703 | 1,281.7446 | -48.19% | -32.04% |

The final manifest records `development_only_through=2015-07-03`,
`final_holdout_forecast_or_evaluation=false`, and that Phase 6 neither read nor hashed final-holdout
outcomes. Emitted inner forecasts end on 2015-05-08; outer forecasts end on 2015-07-03. Phase 7
and the protected 2015-07-04 through 2015-07-31 holdout remain outside this implementation.

Implementation tuning exposed a repeated history-index build across recursive steps; a reusable
origin-censored history cache now matches the reviewed builder exactly across fixture horizons and
preserves missing-date behavior. LightGBM also required `feature_pre_filter=false` on the shared
Dataset because the frozen trial grid varies `min_data_in_leaf`; the four recipes and objective
were unchanged. The final real-data run completed without fit failures.

Final quality checks after the documentation update:

| Check | Result |
|---|---|
| Full fixture suite (`python -m pytest`, Python 3.14.5) | PASS — 151 passed in 22.39s |
| PR #10 GitHub Quality workflow | PASS — Python 3.12 and 3.14 jobs; tests, dependency check, Ruff, formatting, and Markdown links |
| `python -m ruff check .` | PASS |
| `python -m ruff format --check .` | PASS — 69 files already formatted |
| `python scripts/check_docs.py` | PASS — 85 local destinations/anchors across 21 Markdown files |
| `uv lock --check` | PASS — 84 packages resolved |
| `python -m pip check` | PASS — no broken requirements |
| `git diff --check` | PASS — Git reported only the existing uv.lock LF-to-CRLF working-copy warning |

At the implementation checkpoint, the runner completed successfully and its manifest hashed the
ignored development outputs and date-censored input projections. External review, authorized
integration, and formal closeout were then pending; the closeout is recorded below.

### External-review follow-up — 2026-10-06

- Recursive feature/history construction now has its own failure boundary; prediction API errors
  use the approved `model_fit_failure` reason, while explicit schema and categorical-adapter
  failures keep their approved reasons. The fake-booster regression and feature-construction
  failure fixture pass.
- Removed the `narwhals!=2.27.0` resolver exclusion after the LightGBM fixtures passed with
  LightGBM 4.7.0 and Narwhals 2.27.0 on Python 3.12.15 and 3.14.5 (46 passed in each
  environment). PyPI marks 2.27.0 yanked for Pointblank breakage; no incompatibility relevant to
  this repository or LightGBM was reproduced. The normal resolver therefore keeps the yanked
  release out and `uv.lock` remains at Narwhals 2.26.0; the effective locked runtime is unchanged.
- The review fixes do not alter the successful Phase 6 forecasts or recorded metrics. The
  approved real-data development command was not rerun because the locked runtime did not change.
  At this follow-up checkpoint Phase 6 remained **IMPLEMENTED / UNDER REVIEW**; Phase 7 and the
  final holdout remained untouched.
- Follow-up validation passed: full suite **152 passed** on Python 3.12.15 and **152 passed** on
  Python 3.14.5; Ruff lint and formatting, documentation links, `uv lock --check`, dependency
  consistency in both environments, and `git diff --check` passed.

## Phase 6 Formal Closeout — 2026-10-06

Phase 6 is **COMPLETE**. PR #10 merged into `main` at
`dac71d26bd8a9e43eff7d33592460906ae6fee6f`; its completed execution plan is
[archived](../plans/completed/phase-6-global-lightgbm.md). The external-review fixes are in final
commit `9a33e8f673ec438fe4a5546011d06219d66e6a92`, and final-head
[Quality workflow run #12](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/actions/runs/37419362812)
passed on Python 3.12 and 3.14. Review did not change the approved development results documented
above: trial A at 180 rounds, 100% open-label coverage, pooled MAE 871.0612, and the 99% coverage
guardrail passed. The full
fixture suite finished with 152 passing tests. No final-holdout forecast or evaluation occurred.
Phase 7 has not started and requires a separate approved design and authorization.

## Phase 7 Design and Development Evidence Audit — 2026-10-06

**At the evidence-audit checkpoint: design started, implementation not started, methodology
awaiting approval, and no final model officially selected.** The [active plan](../plans/active/phase-7-model-selection.md)
was PROPOSED / AWAITING APPROVAL on `docs/phase-7-model-selection-design`, based on verified PR #11
integration. Its thresholds were proposed after observing the existing results, not
preregistered. Historical Phase 4–6 result records above remain unchanged.

Read-only audit of ignored development outputs: SHA-256 checks match the original manifests for
all three candidates' forecast, pooled/window/horizon metric files and saved HW/LightGBM fit
diagnostics. Exact label/key joining reproduces 46,830 targets and 38,553 common eligible rows
(11,678 / 13,438 / 13,437 per window); recomputed pooled MAEs match the reported values above.
No model/tuning runner or source-data read was needed. Newly verified horizon block MAEs,
pooled over the same common eligible rows rather than averaged daily metrics:

| Horizon block | Seasonal Naive | Holt-Winters | LightGBM |
|---|---:|---:|---:|
| 1–7 | 2,136.3558 | 1,155.6570 | 643.0551 |
| 8–14 | 1,235.4154 | 1,405.2746 | 1,094.4426 |

LightGBM beats each baseline on 11 of 14 pooled horizons, but Sunday h2/h9 MAEs are
1,572.8966 / 1,707.5285 versus SN 861.8763 / 752.7188 and HW 879.1219 / 903.0457;
these strata contain only 97 / 96 eligible rows. At h10 LightGBM MAE 2,280.9889 is worse
than SN 1,025.8322, though below HW 2,341.7674. At h8 it is slightly worse than HW
(733.6691 versus 716.2542). Friday origins confound horizon/weekday; these are descriptive
tradeoffs, not independent replication or confidence evidence.

Saved LightGBM outer `training_seconds` are 6.0427 / 6.1840 / 6.2647 on the recorded
Python 3.14.5, LightGBM 4.7.0 Windows CPU environment with four model threads. Runner inspection
confirms the timer surrounds fitting only. No comparable SN/HW times, end-to-end inference
timings or peak-memory measurements are available; none are fabricated here.

Cached provenance limits remain visible: SN/HW manifests lack modern code/lock identity;
LightGBM records revision `79ddb510e94fe5695c4bc17814153fd47695e16f` with modified worktree and
working-tree source hash, preceding the committed review fixes. The plan requires explicit
acceptance of that lineage and unchanged reviewed specifications, not a claim that these outputs
were regenerated from current main. This audit accessed only saved development evidence ending
July 3; no final-holdout read, hashing, fit, forecast or evaluation, nor Phase 8 work, occurred.

Design quality gate passed: full pytest **152 passed** on each of Python 3.14.5 and 3.12.15,
Ruff lint/format (70 files), Markdown links (107 local destinations/anchors, 22 documents),
`uv lock --check` and `git diff --check`. Only documentation changes; no new tests, models,
dependencies, selection artifacts or interval calculations. Full diff reviewed before publication.

## Phase 7 Methodology Approval Sync — 2026-10-06

External methodology approval was synchronized for reviewed PR #12 head
`1c15ab0b6ee94f3ecccb8f04c84da97d58bbb225`. Phase 7 is **APPROVED / IMPLEMENTATION NOT
STARTED**, and [ADR-020](DECISIONS.md#adr-020--development-only-model-selection-and-frozen-refit-policy)
records the accepted policy. PR #12 remains the open design integration gate; implementation may
begin only after it merges into `main`.

The approved phase-7-v1 rule is unchanged: SN → HW → LightGBM; same three-way eligible/available
open-label population; ≥5% pooled MAE improvement, lower MAE in at least 2/3 windows, and ≤10%
regression in each window and pooled horizon block 1–7/8–14; ties or failed gates retain the
simpler incumbent. Each standalone candidate and the common population must meet 99% coverage in
every approved window, with integrity checks passing. Thresholds remain disclosed as introduced
after observing results, not preregistered; there is no significance or generalization claim.
Keep individual-horizon weaknesses visible, including sparse Sundays and horizon 10; no horizon
veto or forecast mixing is added.

Qualitative operational assessment is accepted for the existing offline CPU course demonstration
without a new benchmark. This grants no API, production, end-to-end runtime, measured-memory or
savings claims. The existing artifact lineage is accepted only for this development selection,
subject to rechecking hashes, keys, labels, masks and configurations; original metadata remains
unchanged. Later operational inputs must be explicit, versioned and auditable.

The selection runner remains unimplemented; no final model is officially selected. Phase 8 has
not started. Final-holdout access remains prohibited until a separately authorized ADR-015 Phase
13 protocol; no holdout was accessed in this approval sync.

Approval-sync checks passed: full pytest **152 passed** on Python 3.14.5 and **152 passed** on
Python 3.12.15; Ruff lint and format (70 files), Markdown checker (109 local destinations/anchors
across 22 Markdown files), `uv lock --check` and `git diff --check`. No fixture tests or model
pipelines were added or run; the requested existing fixture suites passed. Full documentation diff
was inspected.

## Phase 7 Implementation Checkpoint — 2026-10-06

Phase 7 is **IMPLEMENTED / UNDER REVIEW** on `feat/phase-7-model-selection`, based on `main`
after approved design PR #12 merged at `64dbf2359c34cc06d81ee4fc1640ad7225db3973`. The reusable
selection engine and thin CLI use only the three reviewed candidates and their cached development
forecasts. The fixed ADR-020 policy is unchanged. No candidate-level operational decision was
found, so all three reviews remain `unknown`; the result is `operational_review_required`, with no
official selected model or selected-model artifacts.

The runner verified all 34 original candidate artifact hashes (5 Seasonal Naive, 11 Holt-Winters,
18 LightGBM), preserved all three source manifests and their original artifact metadata, checked
the approved source snapshot and Phase 2 identity, and validated the saved candidate keys, labels,
availability/eligibility masks, origins, windows, configurations and model identities. Each saved
candidate contained 46,830 observed Store-origin-Date targets from 2015-05-23 through 2015-07-03.
All 46,830 raw forecasts were available for each candidate, yielding 38,553 identical eligible
Open=1 observed-Sales rows. All three standalone and the three-way common population had 100%
open-label coverage in every window (11,678 / 11,678; 13,438 / 13,438; and 13,437 / 13,437).

Pooled results use the same 38,553 common eligible rows; values are direct row-pooled metrics:

| Candidate | MAE | RMSE | MAPE | WAPE |
|---|---:|---:|---:|---:|
| Seasonal Naive | 1,681.2703 | 2,416.9677 | 26.2671% | 0.232748 |
| Holt-Winters | 1,281.7446 | 1,708.3073 | 18.3669% | 0.177439 |
| LightGBM | 871.0612 | 1,350.9138 | 11.3531% | 0.120586 |

Window MAE (all candidate comparison populations use identical rows):

| Window | Seasonal Naive | Holt-Winters | LightGBM |
|---|---:|---:|---:|
| validation_1 | 1,101.5940 | 1,195.5661 | 1,051.4335 |
| validation_2 | 2,269.7721 | 1,136.8306 | 790.9941 |
| validation_3 | 1,596.5170 | 1,501.5664 | 794.3741 |

The numeric ladder keeps Seasonal Naive after Holt-Winters improves pooled MAE by 23.7633% and
wins 2/3 windows, because its pooled h8–14 MAE is 1,405.2746 versus 1,235.4154 for Seasonal
Naive (+13.7492%, above the 10% cap). The h1–7 block improves 45.9052%, and every window remains
within its 10% cap. LightGBM is then compared directly with the retained Seasonal Naive: pooled
MAE improves 48.1903%, all three windows win, and both pooled horizon blocks pass their caps
(h1–7 improves 69.8994%; h8–14 improves 11.4110%). LightGBM passes the numeric gates; operational
review still prevents selection.

| Horizon | Eligible rows | Seasonal Naive MAE | Holt-Winters MAE | LightGBM MAE | LightGBM change vs Seasonal Naive |
|---:|---:|---:|---:|---:|---:|
| 2 (Sunday) | 97 | 861.8763 | 879.1219 | 1,572.8966 | +82.50% |
| 9 (Sunday) | 96 | 752.7188 | 903.0457 | 1,707.5285 | +126.85% |
| 10 (Monday) | 3,344 | 1,025.8322 | 2,341.7674 | 2,280.9889 | +122.35% |

These horizon rows are descriptive and do not add a veto. The comparison file includes MAE, RMSE,
MAPE, WAPE, denominators, pairwise/common changes, horizon 1–14, pooled week blocks, Store-level
diagnostics and unavailable-reason counts. The ignored output directory is
`data/processed/model_selection/`: `model_comparison.csv` (190,680 rows),
`selection_decision.json`, and `manifest.json`. No `selected_model_config.json`, refit recipe,
selected forecasts or residual paths were emitted because operational approval is unresolved.

SN/HW legacy lineage limits and LightGBM's original modified-worktree revision/hash remain
disclosed in the new manifest; old manifests were not rewritten and no model was rerun. The
qualitative operational scope is only the offline CPU course demonstration. No production latency,
reliability, memory SLA, measured end-to-end runtime advantage or real business savings are
established. The runner read no raw/interim data or final-holdout outcomes, emitted no July 4–31
forecast or metric, performed no fit/tuning, and did not begin Phase 8. ADR-015 still blocks later
July 3 and July 17 refits until separately authorized.

The fixture-first suite has **179 passing tests** on Python 3.14.5 and **179 passing tests** on
Python 3.12.15. `ruff check .` passed; `ruff format --check .` passed (73 files); the documentation
checker passed (111 local destinations/anchors across 22 documents); `uv lock --check` resolved 84
packages; `python -m pip check` passed on Python 3.14.5; and `uv pip check` passed on the locked
Python 3.12 environment (60 packages). `git diff --check` passed with only expected Windows
LF-to-CRLF notices on the three new Python files. [Implementation PR #13](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/13)
is open for review and records these checks. Its [Quality workflow run #19](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/actions/runs/37429992491)
passed both Python 3.12 and Python 3.14 jobs, including dependency checks, fixture tests, lint,
formatting and Markdown links, on implementation commit `f95fa9d`. Later PR-head commits only
updated review documentation; the documentation checker and diff check passed locally, and no new
workflow run was created for those doc-only updates. Phase 7 remains under review; this checkpoint
is not a phase closeout.
