# Phase 11 — Application Services & Thin API

**Status:** M1 IMPLEMENTED / UNDER REVIEW; Phase 11 is not complete. M2–M4 remain planned and are not authorized by the current task.
**Base:** `main` / `origin/main` at `d437269b9f0cf36a842cdfd496ad50a310804768`.
**Approved architecture:** A read-only cached-development-results application with reusable Python services, a thin local/demo FastAPI adapter, and Streamlit calling the shared services directly. API hosting remains optional (ADR-017 and the accepted Phase 11 architecture review).

## Milestones and authorization

| Milestone | Scope | Status |
|---|---|---|
| M1 — Typed contracts and safe canonical artifact readers | Pin accepted Phase 7–10 identities; validate manifests, lineage and requested output hashes; expose fixed, read-only artifact readers and a cutoff-safe historical Sales reader; fixture tests only. | **Implemented / under review.** |
| M2 — Shared application services | Compose verified cached results into forecast, uncertainty and inventory views; preserve explicit null/unavailable values and methodological caveats. | Planned; separate implementation authorization required. |
| M3 — Thin local/demo API | Add the approved HTTP adapter and request/error tests over the shared services. | Planned; separate implementation authorization required. |
| M4 — Integration, documentation and handoff | Complete cross-layer fixtures, startup/use documentation and integration review for the approved scope. | Planned; separate implementation authorization required. |

The technical lead explicitly authorizes **M1 only**. This authorization does not extend to M2–M4, UI or API implementation, deployment, inference, publication of new artifacts, or Phase 13 evaluation. Do not mark Phase 11 complete in this plan or elsewhere.

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

- M2/M3 must freeze the supported view selectors, query bounds and which historical/simulated views are exposed before implementing services or routes. Case/Store selection-driven reads from large Phase 10 summaries remain an M2 prerequisite; M1 retains its fixed projections.
- Decide whether conditional historical replay is shown in the application and how its assumptions and adverse cost comparisons appear to users.
- Resolve how ignored local artifacts are distributed to any future hosted demo; cloud deployment is not implied by this plan.
- Define whether a service-level cache is needed and its full canonical identity key before adding one. M1 output-hash memoization is process-local: device/inode/size/mtime changes trigger rehashing, but matching metadata does not prove the bytes are unchanged. The accepted trust model assumes immutable, locally trusted canonical outputs.

Detailed canonical result evidence remains in [PROGRESS](../../docs/PROGRESS.md); this plan does not duplicate numerical results.
