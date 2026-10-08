# Phase 11 — Application Services & Thin API

**Status:** M1 REVIEWED / formally accepted on the feature branch; M2 IMPLEMENTED / UNDER REVIEW; Phase 11 is not complete. M3–M4 remain planned and unauthorized.
**Base:** `main` / `origin/main` at `d437269b9f0cf36a842cdfd496ad50a310804768`.
**Approved architecture:** A read-only cached-development-results application with reusable Python services, a thin local/demo FastAPI adapter, and Streamlit calling the shared services directly. API hosting remains optional (ADR-017 and the accepted Phase 11 architecture review).

## Milestones and authorization

| Milestone | Scope | Status |
|---|---|---|
| M1 — Typed contracts and safe canonical artifact readers | Pin accepted Phase 7–10 identities; validate manifests, lineage and requested output hashes; expose fixed, read-only artifact readers and a cutoff-safe historical Sales reader; fixture tests only. | **Reviewed / formally accepted** on 2026-10-08; PR remains open and draft. |
| M2 — Shared application services | Compose verified cached results into forecast, uncertainty and inventory views; preserve explicit null/unavailable values and methodological caveats. | **Implemented / under review** on 2026-10-08; implementation authorized, acceptance pending independent review. |
| M3 — Thin local/demo API | Add the approved HTTP adapter and request/error tests over the shared services. | Planned; separate implementation authorization required. |
| M4 — Integration, documentation and handoff | Complete cross-layer fixtures, startup/use documentation and integration review for the approved scope. | Planned; separate implementation authorization required. |

The technical lead formally accepted M1 after the final independent targeted review returned ACCEPT on exact head `1fef9c7f27cb27068f8fcb415378771b878d4aed`. The technical lead separately authorized **M2 only** for implementation on the same feature branch and PR. M2 is implemented and remains under independent review. This authorization does not extend to M3–M4, UI or API implementation, deployment, inference, publication of new artifacts, or Phase 13 evaluation. Keep PR #26 draft and unmerged; do not mark Phase 11 complete.

## Frozen methodology and information boundaries

- Treat `Sales` as monetary turnover, not physical demand or SKU quantity; synthetic inventory values remain conditional simulations, not observed stock or proven savings.
- Read only the pinned accepted Phase 7–10 development artifacts. Verify the exact accepted manifest bytes, run identities, upstream lineage and the particular output identity needed by a read. `current.json` is an informational pointer, never a selector or trust anchor; do not fall back to another run.
- Phase 8's historical manifest flags predate its later accepted freeze. Respect the documented accepted run and frozen hashes; do not mutate or reject that run because those historical flags are false.
- Keep unknown and unavailable results null or explicitly unavailable. Do not substitute zeros, treat absent dates as zero Sales, or reinterpret synthetic scenario values as observations.
- Historical Sales access is restricted to `Date <= 2015-07-03` and the `Store`, `Date`, `Sales`, `Open` projection. Reject an out-of-range request before opening the dataset; push the cutoff predicate into the Parquet scan before materializing rows. Never load `Customers` or protected July 4–31 labels/Open values.
- Do not fit, forecast, calibrate, simulate, change accepted algorithms/metrics/policies, or access/release final-holdout outcomes. Do not read or hash the Phase 10 simulation ledger for readiness or unrelated artifact reads.

## M1 acceptance criteria

- Internal repository-root resolution and a fixed artifact allowlist; no request-controlled paths, run IDs, filenames, column expressions or fallback selection.
- Typed contracts and sanitized, stable errors for unavailable, malformed, unsafe or integrity-failing resources.
- Exact manifest SHA-256 and schema/run/lineage checks for the pinned Phase 7–10 runs, plus required output hash/schema checks only for files actually read.
- Safe symlink/path-traversal rejection, bounded CSV/JSON parsing, fixed-projection Parquet reads, Arrow-filtered historical reads, and primary-key uniqueness checks where the producer contract defines keys.
- Explicit null preservation; a historical reader that rejects invalid/cross-cutoff dates before opening data and proves storage-side filtering with synthetic fixtures.
- Fixture coverage for integrity, lineage, schemas, keys, unavailable resources, selectors, path safety, nulls, history firewall, projections, no fallback, and canonical immutability. No Rossmann downloads or holdout fixtures.
- Standard repository checks pass in the existing locked environment; no dependency/lock update and no canonical output mutation. Self-review confirms Phase 7–10 producer code/methods remain unchanged and Phase 11 is not complete.

## Pending decisions for later authorized milestones

- M3 must freeze route names, HTTP request/response mapping and error translation before adding the adapter. M2's service selectors, query bounds, history wrapper and case-level versus Store-level inventory views are frozen below.
- M2 exposes the saved historical replay alongside synthetic case entries with the producer's mode, schedule assumption, calibration-transport flag, availability and signed cost comparison. Keep the conditional replay and adverse simulated costs explicit; do not describe them as observed inventory or savings.
- Resolve how ignored local artifacts are distributed to any future hosted demo; cloud deployment is not implied by this plan.
- A service-level cache is out of M2 scope. M1 output-hash memoization remains process-local: device/inode/size/mtime changes trigger rehashing, but matching metadata does not prove the bytes are unchanged. The accepted trust model assumes immutable, locally trusted canonical outputs.

## M2 authorization and frozen query/view contract — 2026-10-08

Producer schemas are pinned by the existing Phase 7–10 contracts in `app/artifacts.py`,
`forecasting/validation.py`, `inventory/scenarios.py`, and the Phase 10 policy summary/target and
comparison schemas. M2 supports only these typed, closed requests:

| View | Canonical input and selectors | Bounds and response boundary |
|---|---|---|
| Catalog/readiness | Pinned Phase 7–10 run identities and registered non-ledger selectors; Phase 9 scenario catalog; Phase 10 comparison case IDs. | Store IDs 1–1115; Phase 7 origins 2015-05-22, 2015-06-05, 2015-06-19; Phase 8 Fit A / 2015-06-05 and Fit B / 2015-06-19. Report resource state as present, manifest-validated, or output-verified only when that level was actually checked. Never inspect or hash the Phase 10 ledger. |
| Forecast issuance | Phase 7 selected forecasts filtered by one Store and one accepted forecast origin. | At most 14 rows; date, horizon, raw/operational values and availability, candidate and model-selection provenance only. Exclude `actual_sales`, `source_open`, and retrospective assessment fields. |
| Forecast uncertainty | Phase 8 daily intervals and cumulative uncertainty filtered by one Store, origin, and matching Fit A/B ID. Small frozen quantile tables may be read whole. | At most 56 daily interval rows and 42 cumulative rows; preserve missing strata and nulls. Exclude `actual_sales` and `assessment_source_open`; state that nominal empirical quantiles are not a 95% performance guarantee, recalibration, or coverage claim. |
| Model comparison | Phase 7 comparison rows filtered by one or more exact producer dimensions: candidate, population, scope, validation window, horizon, Store, or metric. | Require at least one filter; Store 1–1115, horizon 1–14, bounded text values, and result limit 1–500. Preserve producer values, denominators, population, and unavailable reasons; do not recompute or combine metrics. |
| Inventory comparison | Phase 10 comparison CSV by known `case_id`, plus policy summary and targets by `case_id` and optional Store. | Store 1–1115 when supplied; at most 2,230 policy rows per case when omitted (two fixed policy IDs across at most 1,115 stores). Return producer case-level aggregates unchanged and pair baseline/forecast by `(case_id, Store)` only after key, policy-ID, completion, target-availability, and valid-matched-comparison checks. The only derived arithmetic is the signed per-Store forecast-policy minus baseline-policy simulated holding-plus-shortfall cost for valid pairs. Do not average ratios or hide adverse values. |
| Historical Sales | Existing M1 `HistoryQuery` and `read_history_sales`. | Retain the exact M1 date/store bounds, `Store, Date, Sales, Open` projection, and pre-open July 3, 2015 cutoff. |

All selection inputs are validated before opening selected outcome-bearing Parquet data. Parquet
predicates are pushed into Arrow scanners before materialization. For every filtered Parquet view,
validate the full-file SHA-256, Parquet footer schema and global row count against the pinned
manifest before applying the selection; enforce a separate selected-view row cap and never compare
selected rows with the manifest's global row count. Stream bounded CSV comparisons without
materializing their complete source frame. Selectors, fields, predicates and paths are never
request-controlled expressions. Service DTOs contain JSON-safe scalars only, preserve nulls, expose
artifact provenance, and distinguish empty results from unavailable artifacts and sanitized
reader errors. No service cache, inference, new metrics, API routes, or UI belongs to M2.

Detailed canonical result evidence remains in [PROGRESS](../../docs/PROGRESS.md); this plan does not duplicate numerical results.
