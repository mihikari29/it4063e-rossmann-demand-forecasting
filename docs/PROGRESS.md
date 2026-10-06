# Project Progress

## Current implementation and Git state — 2026-10-06

| Scope | State | Integration |
|---|---|---|
| Phases 0–4 | COMPLETE | On `main`; Phase 3 PR #3/#4, Phase 4 PR #5/#6 |
| Phase 5 — additive Holt-Winters | COMPLETE | PR #7 squash-merged into `main` at `76707a03b7d10dbaa79d3ef26b39e31994431d70`; formal closeout recorded here |
| Repository architecture/governance review | COMPLETE | Integrated with Phase 5 by PR #7 at `76707a03b7d10dbaa79d3ef26b39e31994431d70` |
| Phase 6 — Global LightGBM | COMPLETE | [PR #10](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/10) merged into `main` at `dac71d26bd8a9e43eff7d33592460906ae6fee6f`; [completed plan](../plans/completed/phase-6-global-lightgbm.md) |
| Phase 7 — model selection | COMPLETE | [PR #13](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/13) merged at `89bcb861642ee28259e4a402e8e8ee98a999a6e5`; [completed plan](../plans/completed/phase-7-model-selection.md); selected LightGBM identity and ADR-020 remain intact |
| Phase 8 - forecast uncertainty | IMPLEMENTED / UNDER REVIEW | [Active plan](../plans/active/phase-8-forecast-uncertainty.md); ADR-021 integrated by PR #14; [PR #15](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/15) is open and unmerged; fitted values await external review |
| Phase 9 and later | PLANNED; not started | Await their dependencies and separate authorization |

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
snapshots, not separate results to update. Phase 7's development-only selection is integrated and
formally closed. Its result and closeout do not constitute final-holdout evaluation or production
approval. Phase 8 methodology is approved in ADR-021 and PR #14 is integrated. The bounded development implementation and evidence are recorded below; its external implementation/results review remains open.

## Immediate next boundary

Phase 5 is formally COMPLETE following PR #7 integration and PR #8 closeout. Phase 6 is **COMPLETE**:
ADR-019 remains accepted, and [PR #10](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/10)
was merged into `main` at `dac71d26bd8a9e43eff7d33592460906ae6fee6f`; its completed plan is
archived.
The Phase 6 development-only results and coverage evidence remain recorded below. Phase 6 closeout
[PR #11](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/11) merged at
`0b8d55144ace29cb8b5367d11aeedc59cfb33a65`. Phase 7 methodology is approved in ADR-020, and
[PR #13](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/13) merged into
`main` at `89bcb861642ee28259e4a402e8e8ee98a999a6e5`. Phase 7 is **COMPLETE**; the selected
`global_lightgbm_gbdt_regression_l1` recipe remains trial A at exactly 180 rounds.
Phase 8 methodology is approved in ADR-021 and implementation is **UNDER REVIEW**. Final-holdout evaluation remains unreleased. The
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
awaiting approval, and no final model officially selected.** The [active plan](../plans/completed/phase-7-model-selection.md)
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

## Phase 7 External Review Follow-up — 2026-10-06

The PR #13 review follow-up hardens generated-artifact lifecycle handling without changing
ADR-020. Before reading candidate evidence, the runner atomically replaces its prior manifest with
an in-progress marker. It stages the comparison, decision, and—only for a selected decision—all
four selected-model artifacts under one run ID; each output is hashed, and the complete manifest is
published last. An interrupted publication therefore cannot leave a complete manifest pointing at
a partial selection. Unresolved or failed runs publish no selected identity or selected-artifact
references. Cleanup is limited to the four fixed selected-output names and only removes files whose
hashes match prior runner-owned metadata. Modified or unverified paths are preserved and reported as
conflicts. Original candidate manifests and files are read-only.

Synthetic lifecycle coverage now includes successful approvals and all four hashed outputs,
subsequent unknown reviews, integrity failure, selected-artifact generation failure, ownership
conflicts, inability to invalidate the existing manifest, preservation of unrelated files and
original manifests, no fit/tuning calls, and residual path keys/masks/errors/completeness. The full
suite passed **187 tests** on Python 3.14.5 and **187 tests** on Python 3.12.15.

The real cached selection command ran without an operational-review file. It returned
`operational_review_required`, selected candidate `null`, and no selected-model files. On the same
38,553 common eligible rows, pooled MAE remained Seasonal Naive **1,681.2703**, Holt-Winters
**1,281.7446**, and LightGBM **871.0612**. All 12 standalone/common per-window coverage gates
passed. The pre-run verification and post-run checks confirmed every original candidate manifest
and every artifact hash still matches its source manifest. No candidate was fitted or tuned, no
final-holdout outcomes were read or hashed, and Phase 8 did not start. Phase 7 remains
**IMPLEMENTED / UNDER REVIEW**; there is no official final model selection.

Final review-fix checks passed: `ruff check .`; `ruff format --check .` (73 files);
`python scripts/check_docs.py` (112 local destinations/anchors across 22 documents);
`uv lock --check` (84 packages); Python 3.14 `pip check`; Python 3.12 `uv pip check` (60
packages); and `git diff --check` (only expected Windows LF-to-CRLF notices for the two changed
Python files). Implementation commit `dbb1712bdc856a2c9b6787a34493cb429d5b8e3c` was pushed to
PR #13; GitHub Actions [Quality run #22](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/actions/runs/37441277676)
passed both Python 3.12 and Python 3.14 jobs on that commit.

## Phase 7 Offline Operational Acceptance and Selection 2026-10-06

The external technical review supplied for PR #13 records candidate-level operational decisions
for the **offline CPU course demonstration** only. These are project technical-review decisions;
this record does not assert a named human reviewer or signature. The versioned input is
[configs/phase-7-operational-review-v1.json](../configs/phase-7-operational-review-v1.json), and
its reviewer reference points back to this section.

| Candidate | Decision | Rationale |
|---|---|---|
| Seasonal Naive | approved | Minimal computational complexity and deterministic same-weekday recurrence make it suitable as the initial incumbent. It needs no optimization or native model dependency. |
| Holt-Winters additive weekly | unknown | It fails ADR-020's pooled h8–14 regression cap; a candidate-specific operational approval is unnecessary for this selection. The operational decision remains unknown rather than being inferred as a rejection. |
| Global LightGBM GBDT regression L1 | approved | The reviewed global CPU implementation uses frozen trial A at 180 rounds in the reproducible locked environment, has 100% development coverage, improves pooled MAE substantially, and had no observed development fit failure. |

This approval is limited to the existing offline CPU demonstration. It establishes no production
latency SLA, reliability guarantee, end-to-end inference-speed comparison, memory SLA, real
inventory result, business savings, or universal accuracy superiority. The h2, h9 and h10
weaknesses and the original candidate-provenance limitations remain in force. The input does not
change ADR-020 thresholds, authorize fitting or tuning, or authorize access to final-holdout
outcomes. The actual CLI result and output integrity checks are recorded next.

### Selection result and artifact verification

The reviewed command ran with the versioned input:
`python scripts/run_model_selection.py --operational-review configs/phase-7-operational-review-v1.json`.
The runner returned **`selected`**; artifact integrity, record integrity and coverage statuses all
**passed**. The selected candidate is `global_lightgbm_gbdt_regression_l1`, selection run ID
`365f22d4c3f94722a594ab934a22c4f6`, and publication state **`complete`**. This is the Phase 7
offline development selection, **RECORDED / AWAITING EXTERNAL INTEGRATION REVIEW**; Phase 7 remains
**IMPLEMENTED / UNDER REVIEW**.

All original candidate-manifest artifacts were rehashed and passed: 5 Seasonal Naive, 11
Holt-Winters and 18 LightGBM artifacts. Their unchanged manifest SHA-256 identities are:

| Candidate | Original manifest SHA-256 |
|---|---|
| Seasonal Naive | `f5e3a18a0a8bff709cb06b4e6282e22cbe3f84668937d3c3e57245b7c76072e3` |
| Holt-Winters | `37b46babad1d197143bfda2f4f11aa65291c350b6b0687410bc4496b7171903b` |
| LightGBM | `ddd379fe4264dd90f618ba57791b97fcce3fd64199ffe95410c4f0d0695810c1` |

The runner matched 46,830 saved Store-origin target rows across 3,345 H14 paths, all ending on
2015-07-03. All 12 standalone/common 99% coverage gates passed at 100%: denominators were 11,678,
13,438 and 13,437 in `validation_1`, `validation_2` and `validation_3`, respectively. The common
eligible population contains 38,553 observed source Open=1 Sales rows.

| Candidate | Pooled common-row MAE | Policy result versus incumbent |
|---|---:|---|
| Seasonal Naive | 1,681.2703 | Initial incumbent |
| Holt-Winters additive weekly | 1,281.7446 | Improves 23.7633% and wins 2/3 windows, but fails the pooled h8–14 cap at +13.7492%; Seasonal Naive remains incumbent. Operational decision remains `unknown`. |
| Global LightGBM GBDT regression L1 | 871.0612 | Improves 48.1903% against Seasonal Naive, wins all 3 windows, and passes every window and pooled horizon-block cap; approved operationally for the scoped demonstration and selected. |

Actual window MAEs and the 10% caps against the retained Seasonal Naive incumbent:

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

The selection output retains the weaker h2 and h9 Sunday results and h10 Monday result: their
LightGBM MAEs are 1,572.8966 (97 rows), 1,707.5285 (96 rows) and 2,280.9889 (3,344 rows),
versus Seasonal Naive MAEs 861.8763, 752.7188 and 1,025.8322. No per-horizon veto was introduced.

The selected recipe exactly matches the reviewed LightGBM candidate configuration: global CPU
GBDT regression L1, trial A, 180 rounds and the ordered 29 Phase 3 predictors. It is a recipe only;
`fit_performed=false`, `no_tuning_or_refit_performed=true`, and no fitted future July model was
generated. The four selected artifacts share the run ID above. Their SHA-256 hashes, plus the two
comparison outputs and completed manifest, are:

| Generated artifact | SHA-256 |
|---|---|
| `selected_model_config.json` | `de53a477b4bed768a9fbaa459e7f347be28c05063f5c5e379c0dfbb40d21960b` |
| `refit_recipe.json` | `9ef3ee340ac57f14394857203ca3de5445ebae70972ec541a51947f38a49f799` |
| `selected_development_forecasts.parquet` | `72566349b233ef26c8de5b4f9c1623ac66df8676ad0370ad63b192ed4c1b5b09` |
| `development_residual_paths.parquet` | `509bb4a822157850e8fb0309114a4003b98bcbc6b56f4a49244d8b6593e03382` |
| `model_comparison.csv` | `c648e8e407dc367e56f26cb421656dabc8d742a9a3cd3d3b092b746a84b10357` |
| `selection_decision.json` | `02c00b7f0b72e260db03b6f786e443db93844a146f3a93fb8c4c4ea076f2e5de` |
| `manifest.json` | `03a1f26ba5855fd0576667bf280df938664c196a802de0a71e696a600b281cdc` |

The manifest binds the review input at SHA-256
`9ef1c1fa28fc12db318d510a5ae48a29fd2198116a0114e0d5ee866dc66d7516`. Its selection code revision
is reviewed PR #13 head `ca3d51fff53e6e98b55fae2ac84a5cfe1af7324a`, with current source hash
`20028b1133053489f8b3a68b5a38b272e7bf8a9947581395f96e64e5d57be997`; the runner records a
modified worktree because the review input and this record were present. No forecasting source or
runner code differed from that reviewed head. The original cached provenance limitations remain:
legacy SN/HW manifests lack modern source-code/lock identity, and the LightGBM manifest records its
historical modified-worktree run. All seven published files remain Git-ignored.

Residual checks verified the signed definition `actual_sales - forecast`, raw-primary masks,
operational masks and their complete/partial counts. Every Store-origin path has exactly horizons
1–14; 96 raw-primary paths are complete and 3,249 are partial because closed-day labels are not in
the primary population. All 3,345 operational paths are complete under the saved Open routing.
Closed-day raw residuals remain descriptive and excluded from primary metrics; unavailable values
were not filled. The manifest records no July 4–31 read/hash/forecast/evaluation and
`phase_8_started=false`; no Phase 8 work began.

Acceptance quality checks: full pytest passed **187 tests** on Python 3.14.5 (71.21s) and **187
tests** on Python 3.12.15 (69.61s); Ruff lint passed; Ruff format check passed (73 files); the
documentation checker passed (115 local destinations/anchors across 22 Markdown files);
`uv lock --check` resolved 84 packages; Python 3.14 `pip check` and locked Python 3.12 `uv pip
check` (60 packages) passed; `git diff --check` passed. The runner output and all original
candidate hashes were independently reverified after publication. No implementation code, tests,
dependencies or methodology changed. No candidate was fit or tuned and no protected outcome was
read or hashed.

## Phase 7 formal closeout and Phase 8 evidence audit — 2026-10-06

GitHub and fetched `origin/main` verify PR #13 merged at
`89bcb861642ee28259e4a402e8e8ee98a999a6e5`. Its integrated tree matches the reviewed final head
`688d673f3ebaf802cbe47f9fa3236fcb4aaa3dea`; final-head Quality run #25 passed Python 3.12 and
3.14. The accepted external review, verified integration and this explicitly authorized closeout
make Phase 7 **COMPLETE**. The [completed plan](../plans/completed/phase-7-model-selection.md)
preserves historical approval, implementation and selection checkpoints. ADR-020 and the selected
`global_lightgbm_gbdt_regression_l1` identity remain unchanged: frozen trial A, 180 rounds,
29 predictors and the same raw recursive/operational routing behavior.

The clean `docs/phase-8-uncertainty-design` branch started from that latest `origin/main`.
A read-only audit of existing ignored development exports verified the seven selection-file
hashes above and all 34 original candidate artifacts; no source dataset or protected outcomes were
read or hashed. The selected run ID remains `365f22d4c3f94722a594ab934a22c4f6`. Recipe and
manifest still record no refit, tuning or future-origin forecasting. Historical candidate
provenance limitations remain disclosed rather than being repaired by regenerating evidence.

The residual export has 35 fields and 46,830 unique Store-origin-Date rows, ending 2015-07-03:
3,345 paths with exactly h1–14. Masks, signed residuals (`actual_sales - forecast`), path flags
and saved Open routing match the implementation. No target keys are absent, no Open values are
unknown, and all required labels/forecasts are finite in these saved records.

| Audited population | Result and interpretation |
|---|---|
| Complete raw-primary H14 paths | 96, from the same 32 distinct stores in each of three origins; 3,249 paths are partial. Closed labels are outside the raw-primary Open=1 population. |
| Complete operational H14 paths | 3,345, covering all 1,115 stores per origin under saved Open routing. |
| Observed closed-day rows | 8,277, all with actual Sales=0 and routed forecast=0. These are observed turnover outcomes, not imputed missing residuals or uncensored physical demand. |
| Raw-primary counts at sparse h2 / h3 / h9, validation_1 | 32 / 33 / 32. |
| Raw-primary counts at h2 / h9, validation_1 + validation_2 | 65 / 64, reusing only 33 / 32 distinct stores across two origins. |

Operational completeness depends on using saved historical Open. This does not establish that
the schedule was known at origin. The proposed Phase 8 plan explicitly separates that unverified
availability from a newly proposed, conditional offline replay assumption; unknown future Open
must remain operationally unavailable.

### Phase 8 design checkpoint

At the reviewed PR #14 design head, the [active Phase 8 plan](../plans/active/phase-8-forecast-uncertainty.md)
was **PROPOSED / AWAITING APPROVAL** and included a draft ADR-021. The 2026-10-06 approval sync
below supersedes that proposal checkpoint; the accepted methodology is recorded in ADR-021.

No uncertainty runner or tests were added; no intervals, empirical quantile values, inventory
outcomes or new forecasts were calculated. Phase 8 implementation and Phases 9–10 remain
unstarted. Final-holdout outcomes for 2015-07-04 through 2015-07-31 remain protected under ADR-015;
their release requires the separately authorized frozen Phase 13 protocol.

### Phase 8 design delivery validation

Executed on Python 3.14.5 in the development environment with uv 0.12.23; a subsequent
`uv sync --locked --extra dev --python 3.14` verified the same environment (60 managed packages,
no package changes):

| Check | Result |
|---|---|
| Full `python -m pytest` | PASS — 187 tests in 87.93s; existing fixtures only |
| `python -m ruff check .` | PASS |
| `python -m ruff format --check .` | PASS — 74 files already formatted |
| `python scripts/check_docs.py` | PASS — 146 local destinations/anchors across 23 Markdown files |
| `uv lock --check` | PASS — 84 packages resolved; lock unchanged |
| `uv pip check` | PASS — 61 compatible installed packages |
| `git diff --check` | PASS |

Complete diff review confirms changes are limited to Phase 7 lifecycle closeout/archive, the
Phase 8 proposal and mechanical links/current-status synchronization. No code, tests, dependencies,
proposal or selected artifacts
changed. New-PR CI is not yet verified; delivery stops after opening the authorized design PR.

## Phase 8 methodology approval sync — 2026-10-06

The external Phase 8 methodology review is accepted in [ADR-021](DECISIONS.md#adr-021--chronological-empirical-forecast-uncertainty-and-conditional-operational-replay).
Phase 8 is **APPROVED / IMPLEMENTATION NOT STARTED**. PR #14 remains open and unmerged as the
design integration gate; implementation of the approved bounded protocol may begin after it
integrates into `main`.

Approval fixes the daily signed-residual estimator, exact horizon-specific ranks and n>=40 floor,
Fit A/Fit B chronology, and the complete operational-prefix estimator with p={0.90,0.95,0.98},
upper-rank rule and n>=50 floor. The saved historical Open values authorize development-only
conditional course replay and do not prove origin-time schedule availability. For Phase 13, actual
holdout Open must not be read, hashed, loaded or substituted before issuance; operational outputs
requiring future Open remain unavailable without separately reviewed origin-known schedule
provenance or a separately approved synthetic/conditional schedule that is not derived from
protected actual Open.

No uncertainty runner, fixture tests, interval calculations, quantile tables or fitted-table
freeze were produced in this approval sync. Fit B's actual tables, diagnostics, hashes and
availability require separate external implementation/results review before the values are
frozen. No Phase 9/10 implementation, final-holdout access or evaluation occurred; protected
2015-07-04 through 2015-07-31 outcomes remain unreleased.

Approval-sync local validation on Python 3.14.5 with the locked environment:

| Check | Result |
|---|---|
| Full `python -m pytest` | PASS — 187 tests in 92.93s; existing fixtures only |
| `python -m ruff check .` | PASS |
| `python -m ruff format --check .` | PASS — 74 files already formatted |
| `python scripts/check_docs.py` | PASS — 148 local destinations/anchors across 23 Markdown files |
| `uv lock --check` | PASS — 84 packages resolved; lock unchanged |
| `uv pip check` | PASS — 61 installed packages compatible |
| `git diff --check` | PASS |

## Phase 8 development-only implementation checkpoint - 2026-10-06

The approved ADR-021 implementation is **IMPLEMENTED / UNDER REVIEW** on branch
`feat/phase-8-uncertainty-implementation`, based on merged PR #14 commit
`305ddc80a4e3399698f64762ec26da2fc79cfb10`. Implementation PR
[#15](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/15) is open and
unmerged; external implementation/results review is pending. The selected Phase 7 identity remains
`global_lightgbm_gbdt_regression_l1`; this work reads its saved paths only and performs no point
model fit, refit, tuning or selection change.

The canonical development run is `phase8-impl-20261006-final`, under the ignored directory
`data/processed/uncertainty/phase8-impl-20261006-final/`. An earlier implementation-validation run,
`phase8-impl-20261006`, is retained as an immutable prior run; `current.json` points to the canonical
run recorded here. Its manifest status is
`complete_with_unavailable_strata`; dates are 2015-05-23 through 2015-07-03 across the three
approved development windows. The run read 46,830 selected residual-path rows, with 38,553
Open=1 raw-primary errors and 46,830 routed operational errors. The saved Phase 7 outputs,
selected candidate manifest and all three original candidate output sets were SHA-256 verified
before and after the run; every input hash was unchanged. The run did not read or hash source
datasets or protected July 4-31 Open, Sales or Customers values.

Fit A has 22 of 28 daily tail strata available. Its h2 (n=32), h3 (n=33) and h9 (n=32) lower and
upper tails remain unavailable as `insufficient_calibration`; no neighboring-horizon fallback
was used. Fit B has 28 of 28 daily tail strata available. All 42 cumulative `(k,p)` strata are
available for each fit: 1,115 complete calibration Store-origin prefixes for Fit A and 2,230 for
Fit B at every k=1-14. The saved schedule interpretation is explicitly
`saved_source_open_assumed_known_at_origin`, a conditional historical replay. Empirical coverage
and width diagnostics are descriptive and have no approved numeric acceptance threshold or
production/service guarantee. Fit B fitted values remain unfrozen pending external review.

The run manifest records source revision `305ddc80a4e3399698f64762ec26da2fc79cfb10`,
`worktree_modified=true`, implementation source hash
`993e9e687eaa3ec3f662e0851e57a8fd7c93c499642c13c5d0a103cd6f36edce`, and `uv.lock` hash
`584337e365e653d97731b73c6d9e2292c4224bee524f0225ddf3221b0aa0f5d0`. Output row counts and
hashes are recorded in that manifest; primary table identities are:

| Artifact | Rows | SHA-256 |
|---|---:|---|
| `calibration_config.json` | - | `afe563632a2ebff937f1500f568d53cdb93be35d6dc299654464c2615ae64a08` |
| `daily_residual_quantiles.csv` | 56 | `5c985c912d14b502a5d370090353624907e7fddd6d0d8552c102ee3a1ad7eda8` |
| `cumulative_error_quantiles.csv` | 84 | `1a0bba7916b498f2048f080dcd3b24f6cd47472d2f71fca92b94f1b678cb70ff` |
| `daily_intervals.parquet` | 62,440 | `160e68f4dd0237b61e60d20d041e06d0760fd94b006f7e89730e24e96b601fd2` |
| `cumulative_uncertainty.parquet` | 93,660 | `f338ff7189d652e64c8aa27f3d03c205c313185fb205f9f8a50b9776d59c0a0e` |
| `coverage_diagnostics.csv` | 392 | `7517435e7e4dd4bf0d08aa705c3555bb1ea945d6cae3dff8db8dfdf46ca0aaa4` |

| Check | Result |
|---|---|
| Full `python -m pytest` | PASS - 199 tests in 92.05s |
| `python -m ruff check .` | PASS |
| `python -m ruff format --check .` | PASS - 77 files already formatted |
| `python scripts/check_docs.py` | PASS - 149 local destinations/anchors across 23 Markdown files |
| `uv lock --check` | PASS - 84 packages resolved; lock unchanged |
| `git diff --check` | PASS |

The implementation adds `src/rossmann_forecasting/forecasting/uncertainty.py`,
`scripts/run_forecast_uncertainty.py` and fixture coverage in `tests/test_uncertainty.py`. It also
updates this state record, the Phase 8 active plan, README usage/state text, and the ignored-data
layout guide. No ADR-021 methodology, Phase 7 algorithm/artifact, proposal, inventory layer,
Phase 9/10 work or final-holdout protocol changed. Canonical run manifest SHA-256 is
`d32ea0d3de331fc9e61ece091742edd8d23291383a2bb64779a1af945073a2bb`; its canonical policy/config hash is
`49f4811bf7b01ffe6472ea76233eefa50e211207aa0b6246dada934cd4611d93`. Whole-repository checks on
Python 3.14.5 with the locked environment passed:
