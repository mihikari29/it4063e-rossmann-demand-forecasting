# Project Progress

## Current Phase

Phase 3 — Feature Engineering.

## Status

**IMPLEMENTED / UNDER REVIEW — PHASE NOT CLOSED.** Phase 2 preparation, warning
investigations, and EDA are complete. The Phase 3 feature contract is approved and checkpointed;
implementation, fixture tests, and the real-data integrity audit have been run on
`feat/feature-engineering`. The active Phase 3 plan remains unarchived. No forecasting model,
forecast metrics, or model-selection work is in scope.

## Completed

- Phase 0 — repository foundation.
- Phase 1 — official Rossmann acquisition and validation; see the completed Phase 1 plan and
  verified source findings.
- Phase 2 — prepared immutable-source train/test data, recorded audit-only Store 622 Open
  consensus candidates, investigated all four Phase 1 warnings and metadata missingness, generated
  descriptive reports and 14 figures, and documented findings in [EDA Findings](EDA_FINDINGS.md).
- Added fixture tests for source preservation, joins, key uniqueness, explicit Open resolution,
  deterministic representatives, denominators, and Parquet round trips.
- Archived the completed Phase 2 execution plan at
  `plans/completed/phase-2-data-preparation-eda.md`.

## In Progress

Awaiting external code review of the Phase 3 implementation on branch `feat/feature-engineering`.
Keep the active plan open until review and any requested changes are resolved.

## Next

After review, address requested changes and obtain explicit direction before closing Phase 3 or
starting any later modeling phase. Do not train models, compute forecast metrics, or inspect
holdout outcomes as feature-design feedback.

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

## Phase 3 Implementation Evidence (Review Pending)

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
  [Feature Contract](FEATURE_CONTRACT.md); the active execution plan remains in
  `plans/active/phase-3-feature-engineering.md` pending review.

## Quality Gates

- `python scripts/validate_data.py --report reports/validation/rossmann.json`: PASS — 0 errors,
  4 reviewed warnings, 12 informational findings.
- `python scripts/build_features.py`: PASS — raw/interim provenance checks, key preservation,
  matching predictor schemas/dtypes, holdout mechanical audit, and output generation.
- `python -m pytest -q --tb=short`: 45 passed.
- `ruff check .`: passed; `ruff format --check .`: 44 files already formatted.
- `git diff --check`: passed. Relative Markdown links in changed user-facing documentation: passed.
- Preparation and EDA commands completed against the official data; both notebooks validated and
  executed successfully with cleared committed outputs.

## Scope Confirmation

No forecasting model, model selection, random split, inventory simulation, synthetic supply-chain
data, API, or dashboard has been added. Sales remains monetary turnover at Store × Date; future
Customers remains unavailable to production forecasts. Primary forecast evaluation on actual
Open=1 observations and the proposal's known-closed operational rule remain later-phase constraints.
