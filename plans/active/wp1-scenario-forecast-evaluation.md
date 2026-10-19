# WP1 — Scenario-Based Forecast Evaluation

**State:** WP1 direction is owner-approved for fixture-only methodology implementation. L1 was
reviewed and integrated through PR #46 at `291660108da0c3d91b065a7dba47beabe1926fae`; Quality
#149 passed on Python 3.12 and 3.14. L2 fixture-only aggregation and serialization are
IMPLEMENTED / UNDER REVIEW after local correction of all four WP1-S4 findings; independent
rereview is pending. No real-data scenario analysis has run, scenario results are not accepted, and
ADR-028 remains PROPOSED.

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

## Approved L2 scope and execution plan

L2 accepts in-memory output from `build_scenario_population` as its sole population authority. Its
adapter requires the exact 21-column L1 schema, rebuilds the three candidate views, calls the
unchanged L1 builder, and rejects any key, label, availability, reason, or eligibility-mask
mismatch. All summaries use the regenerated canonical population. L2 does not add a second
candidate or forecast validator and does not change Phase 7.

Optional in-memory scenario membership uses the exact observed `(Store, forecast_origin, Date)` key
set and only the approved `Promo`, `StoreType`, `Assortment`, `StateHoliday`, and `SchoolHoliday`
columns. A missing keyed record is an integrity error; a null cell is a missing category. Static
StoreType and Assortment values must remain consistent per Store. Known codes are normalized only as
specified by the accepted design; unknown nonempty text codes remain distinct unrecognized levels.

Reporting includes pooled development and each of the three approved origins. Every scope declares
all rows, H1-H14, H1-H7/H8-H14, and ISO weekday 1-7. Enabled metadata dimensions report all known,
missing, and observed unrecognized levels independently, with no interactions. Empty strata remain
present. Support and coverage preserve observed sparse keys and distinguish target, label, forecast
availability, standalone, and exact common populations.

Primary metrics and all three fixed comparisons use the same three-way common rows. L2 stores
additive sufficient statistics and derives MAE, RMSE, WAPE, and directional summaries from pooled
sums. Undefined values remain null with reasons; no epsilon, MAPE change, winner rule, or selection
policy is introduced. The serializer returns deterministic UTF-8 JSON bytes in memory and performs
no file I/O.

Execution sequence:

1. Add the population adapter, strict membership normalization, fixed stratum generation, additive
   summaries, reconciliation checks, and deterministic fixture serializer to the existing
   `scenario_evaluation.py` module.
2. Extend the existing synthetic tests with independently hand-computed metrics, population and
   metadata integrity cases, deterministic serialization, invalid arithmetic/payload checks, and
   Phase 7 metric reconciliation.
3. Update this plan and PROGRESS with actual implementation and validation state; keep L2
   IMPLEMENTED / UNDER REVIEW until independent review and authorized integration.
4. Run focused fixture tests and repository quality checks. Run the full fixture suite only from a
   clean isolated checkout that has no linked or copied ignored datasets or artifacts; do not
   inspect, read, or hash those artifacts to establish isolation.
5. Self-review the exact four-file diff. This task does not authorize commit, push, PR, merge, real
   input access, L3/L4, Phase 13, or ADR-028 acceptance.

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
| L1 — common population | Fixture-only candidate alignment and auditable eligibility masks | REVIEWED / INTEGRATED by PR #46; main Quality #149 passed |
| L2 — metrics and scenario views | Add approved metrics, summaries, and in-memory JSON serialization to synthetic fixtures | IMPLEMENTED / UNDER REVIEW after this task's implementation and validation |
| L3 — safe-input readiness | Review provenance and feasibility for authorized scenario metadata and any optional history inputs | Requires explicit source/input authorization; no mixed-source shortcut |
| L4 — development analysis | Run frozen scenario analysis on approved cached development evidence and document interpretation | Requires safe inputs, execution authorization, independent review, and disclosure of limitations |

## Deferred decisions

Volume segmentation and cross-model inventory experiments remain deferred; the latter is a separate
bonus design. Do not infer categorical meanings or turn forecast underprediction into observed
stockouts, lost Sales, or realized savings. L3 requires separate source/input authorization before
safe-input assessment; L4 requires safe inputs, a frozen methodology, separate execution
authorization, independent review, and disclosure. This L2 authorization grants neither milestone.

## Academic integrity and review

This is a reviewable development draft. Human ownership review and the course's AI-assistance and
authorship disclosure requirements must be resolved before the code is represented as submitted
coursework. Do not describe AI-assisted code as solely human-authored. Independent review must check
validator reuse, masks, sparse population, scenario membership integrity, metrics, deterministic
serialization, and scope before later milestones build on L1/L2.

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

## L2 acceptance criteria

- The public summary accepts only the exact L1 population schema, regenerates it through the
  unchanged L1 builder, compares the supplied eligibility/availability/reason fields by canonical
  key, and uses only the regenerated sorted population.
- Optional membership requires the exact observed key set, validates the approved metadata domains,
  preserves missing and unrecognized category states separately, and enforces static StoreType and
  Assortment per Store.
- The five stable tables are `support`, `coverage`, `metrics`, `comparisons`, and `unavailability`.
  They retain all 96 default strata, all declared metadata levels, empty groups, sparse observations,
  exact common-population counts, and original unavailability reasons.
- Every candidate metric and the fixed LightGBM/Seasonal Naive, LightGBM/Holt-Winters, and
  Holt-Winters/Seasonal Naive comparison is computed on the same three-way common rows. Additive
  statistics reconcile direction counts and signed/absolute errors. Signed reconciliation permits
  only a component-magnitude ULP rounding bound while retaining the independently accumulated
  signed sum. Pooled metrics derive from pooled sufficient statistics. Undefined values remain null
  with explicit reasons.
- Serialization validates the complete result and returns deterministic fixture-only JSON bytes
  with fixed schema, integer counts, finite full-precision numbers, normalized negative zero, ISO
  dates, compact sorted UTF-8 JSON, and one trailing newline. It performs no file I/O.
- The serializer requires identical actual-Sales denominators across the three candidates for each
  stratum, checks known/missing/unrecognized metadata identities against the fixed domains, and
  bounds missing-Sales and reason-level unavailable diagnostics by their eligible populations.
- Synthetic tests cover the hand-calculated fixture, coverage and missing-label cases, metadata/key
  integrity, large opposing directional sums and corrupted sufficient statistics,
  candidate-denominator agreement, valid/invalid metadata identities, diagnostic subset bounds,
  ordering/nonmutation, arithmetic overflow, serializer integrity, no external side effects, and
  Phase 7 metric consistency. No real input, fit, forecast generation, protected outcome, holdout,
  Phase 13, selection policy, or inventory decision is accessed or executed.
- L2 remains IMPLEMENTED / UNDER REVIEW until independent review and separately authorized
  integration. L3 input authorization and L4 scenario execution remain separate gates.

## WP1-S4 correction checkpoint — 2026-10-19

The independent review requested changes for four bounded defects. Local corrections now use a
component-scaled ULP bound for signed-error reconciliation, require exact common actual-Sales
denominators across candidates, validate metadata level identities against each fixed domain, and
enforce missing-Sales and per-reason unavailability subset bounds. Regression tests cover the
reviewer-provided cancellation fixture, material signed-total corruption, pooled and non-pooled
denominators, known/missing/unrecognized metadata identities, and both diagnostic bounds.

L2 remains IMPLEMENTED / UNDER REVIEW. Independent Sol 6.1 rereview of the exact corrected diff is
pending; this checkpoint does not accept L2 or authorize publication or integration.
