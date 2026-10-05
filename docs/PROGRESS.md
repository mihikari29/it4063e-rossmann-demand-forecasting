# Project Progress

## Current Phase

Phase 3 — Feature Engineering.

## Status

**IMPLEMENTATION IN PROGRESS.** Phase 2 preparation, warning investigations, EDA, documentation,
and quality gates are complete. The Phase 3 feature contract (including Store identity as a
categorical predictor and the approved competition-status amendment) is approved and checkpointed;
Phase 3 implementation and validation are now beginning. No forecasting model is in scope.

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

Phase 3 feature implementation and validation on branch `feat/feature-engineering`, following the
approved active execution plan.

## Next

Complete the approved Phase 3 feature contract, fixture tests, real-data integrity audit, and
holdout-firewall checks. Do not train models, compute forecast metrics, or begin later modeling
phases.

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

## Quality Gates

- Real-data validator: PASS — 0 errors, 4 reviewed warnings, 12 informational findings.
- `python -m pytest`: 23 passed.
- `python -m ruff check .`: passed.
- `python -m ruff format --check .`: passed.
- Preparation and EDA commands completed against the official data; both notebooks validated and
  executed successfully with cleared committed outputs.

## Scope Confirmation

Phase 2 added no lag/rolling model features, forecasting model, model selection, random split,
inventory simulation, synthetic supply-chain data, API, or dashboard. Sales remains monetary
turnover at Store × Date; future Customers remains unavailable to production forecasts. Primary
forecast evaluation on actual Open=1 observations and the proposal's known-closed operational rule
remain Phase 3/later constraints.
