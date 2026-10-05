# Project Progress

## Current Phase

Phase 4 — PLANNING / DESIGN REVIEW (Seasonal Naive Baseline NOT IMPLEMENTED).

## Status

**PHASE 1 COMPLETE — PHASE 2 COMPLETE — PHASE 3 COMPLETE.** Phase 3 was externally reviewed;
the canonical Store × Date key finding was resolved, and PR #3 was merged into `main` at
`ef2c23ca79bb239b6c143572b6b4dc545d1de0b5`. Its completed execution plan is archived at
`plans/completed/phase-3-feature-engineering.md`. The shared `phase-3-v1` contract has 29
predictors. No final-holdout outcomes were used for feature selection or design feedback. Phase 4
is in design review; the methodology is proposed and awaits explicit approval. No forecasting
model, baseline forecast, or forecast metric has been produced.

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
- Phase 3 — completed forecast-origin-safe feature engineering; externally reviewed, canonical-key
  finding resolved, and merged through PR #3. The completed plan is under
  `plans/completed/phase-3-feature-engineering.md`.

## In Progress

Phase 4 — Seasonal Naive Baseline design review is in progress. Its proposed methodology is
documented in [the active Phase 4 plan](../plans/active/phase-4-seasonal-naive.md); implementation
has not been approved or started.

## Next

Wait for explicit approval of the Phase 4 design before implementation. No baseline, forecast, or
forecast metric exists yet. Keep the final holdout untouched during future feature and model
selection.

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

## Quality Gates

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

## Scope Confirmation

No forecasting model, model selection, random split, inventory simulation, synthetic supply-chain
data, API, or dashboard has been added. Sales remains monetary turnover at Store × Date; future
Customers remains unavailable to production forecasts. Primary forecast evaluation on actual
Open=1 observations and the proposal's known-closed operational rule remain later-phase constraints.

## Phase 4 Design Checkpoint

- Planning branch is based on `main` at `c016c4e3a2c33da278ebdbbe074b3e1d4f13fe70`, which includes
  the Phase 3 documentation closeout. The active execution/design plan is
  `plans/active/phase-4-seasonal-naive.md` and is awaiting explicit user approval.
- The exact three proposed 14-day development windows were mechanically checked using only the
  historical `Date` column. The final holdout (2015-07-04 through 2015-07-31) was not evaluated or
  summarized.
- No proposed Phase 4 methodology has been added as an accepted ADR. No Seasonal Naive
  implementation, forecast output, forecast metric, or holdout evaluation has been produced.
