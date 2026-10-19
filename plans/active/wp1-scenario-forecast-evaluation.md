# WP1 — Scenario-Based Forecast Evaluation

**State:** The owner-approved WP1 direction and fixture-only L1 scope are in progress. L1 is
implemented on `feat/wp1-scenario-common-population` and awaits independent review. WP1 analysis has
not run; its results are not accepted. ADR-028 remains PROPOSED.

## Objective

Compare the three existing Phase 7 Store × Date monetary Sales forecasts across approved Store-level
scenarios using development-only evidence, then explain only the business implications supported by
the available evidence. Preserve Phase 7 candidate identities, chronological origins, raw forecast
semantics, and the existing forecast information boundary.

## Approved L1 scope

Implement a pure in-memory population builder for synthetic fixtures. It must call the public
`validate_candidate_records` Phase 7 validator, use its normalized records, align the exact three
approved candidates on `(Store, forecast_origin, Date)`, and preserve all observed target keys.
Produce label-only eligibility, each candidate's raw forecast, availability/reason and standalone
eligibility, plus exact three-way common eligibility. Derived standalone masks must agree with the
Phase 7 accepted eligibility masks or fail closed. Sort deterministically and leave input frames
unchanged.

Approved origins are 2015-05-22, 2015-06-05, and 2015-06-19, with targets ending no later than
2015-07-03. Sparse observed target keys remain sparse. Open=1 with zero Sales is an eligible label;
closed, unknown-Open, and missing-Sales rows remain in the output but are ineligible. This milestone
adds no scenario fields, joins, metrics, forecast generation, file access, hashes, or publication.

## Dependencies and scientific boundaries

- Reuse `CANDIDATE_IDS`, `FORECAST_COLUMNS`, canonical keys, windows, and validation from
  `src/rossmann_forecasting/forecasting/model_selection.py` and
  `src/rossmann_forecasting/forecasting/validation.py`.
- Keep Phase 7 candidates and model selection unchanged. Do not replace accepted raw forecasts with
  operational forecasts or unclipped diagnostics.
- Keep July 4–31 protected. No source, cached real-data forecast, inventory, or holdout artifact may
  be read or hashed for L1.
- Do not treat absent Store × Date keys as zero, unknown Open as closed, unavailable forecasts as
  zero, or forecast error as observed inventory or lost-sales outcomes.
- Preserve Phase 13 as PLANNED / NOT APPROVED and all of its separate authorization gates.

## Milestones

| Milestone | Scope | Boundary |
|---|---|---|
| L1 — common population | Fixture-only candidate alignment and auditable eligibility masks | Implemented; independent review pending |
| L2 — metrics and scenario views | Add the approved development metrics and scenario summaries to synthetic fixtures | Requires a separate bounded task; no real-data operation by default |
| L3 — safe-input readiness | Review provenance and feasibility for authorized scenario metadata and any optional history inputs | Requires explicit source/input authorization; no mixed-source shortcut |
| L4 — development analysis | Run frozen scenario analysis on approved cached development evidence and document interpretation | Requires safe inputs, execution authorization, independent review, and disclosure of limitations |

## Deferred decisions

L1 does not implement or freeze scenario dimensions, interaction rules, minimum support flags,
volume cutpoints, scenario-specific exclusions, business weighting, or inventory-policy comparisons.
These remain bounded design decisions for later milestones. Do not infer categorical meanings or turn
forecast underprediction into observed stockouts, lost Sales, or realized savings. Any cross-model
inventory comparison remains a separate bonus design.

## Academic integrity and review

This is a reviewable development draft. Human ownership review and the course's AI-assistance and
authorship disclosure requirements must be resolved before the code is represented as submitted
coursework. Do not describe AI-assisted code as solely human-authored. Independent review must check
the validator reuse, masks, sparse population, ordering, and scope before later milestones build on
L1.

## L1 acceptance criteria

- The builder exposes the documented stable schema and calls the Phase 7 validator as the sole
  authority for candidate, key, label, origin, horizon, window, and availability integrity.
- It retains every validated observed key and approved metadata, uses only the three accepted raw
  forecast fields, and distinguishes label-only, standalone, and common eligibility.
- Its output is deterministic under row and dictionary-order changes, and caller frames are
  unchanged.
- Synthetic tests cover candidate identity, chronology, key/label integrity, missing forecasts,
  source Open/Sales cases, raw forecast semantics, sparse targets, and absence of external side
  effects.
- Focused tests, repository quality checks, and final diff review are recorded with actual results.
- No commit, push, PR, merge, real-data operation, Phase 13 operation, or L2 implementation occurs
  in this milestone.
