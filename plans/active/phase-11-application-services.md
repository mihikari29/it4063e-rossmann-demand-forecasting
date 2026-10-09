# Phase 11 — Application Services & Thin API

**Status:** M1, M2 and M3 ACCEPTED; M3-01 RESOLVED; M4 ACCEPTED WITH MINOR CHANGES (M4-01 RESOLVED). Final PR integration and merge-readiness review and formal Phase 11 closeout remain pending; Phase 11 is not complete.
**Base:** `main` / `origin/main` at `d437269b9f0cf36a842cdfd496ad50a310804768`.
**Approved architecture:** A read-only cached-development-results application with reusable Python services, a thin local/demo FastAPI adapter, and Streamlit calling the shared services directly. API hosting remains optional (ADR-017 and the accepted Phase 11 architecture review).

## Milestones and authorization

| Milestone | Scope | Status |
|---|---|---|
| M1 — Typed contracts and safe canonical artifact readers | Pin accepted Phase 7–10 identities; validate manifests, lineage and requested output hashes; expose fixed, read-only artifact readers and a cutoff-safe historical Sales reader; fixture tests only. | **Reviewed / formally accepted** on 2026-10-08; PR remains open and draft. |
| M2 — Shared application services | Compose verified cached results into forecast, uncertainty and inventory views; preserve explicit null/unavailable values and methodological caveats. | **Reviewed / formally accepted** on exact PR #26 head `cd7d3319760379716244e4db6c0cf0cb96ec6cbd` after independent ACCEPT, 2026-10-09. |
| M3 — Thin local/demo API | Add the approved HTTP adapter and request/error tests over the shared services. | **Formally accepted** by the Technical Lead on 2026-10-09; its M3-01 follow-up was resolved in M4. |
| M4 — Integration, documentation and handoff | Close M3-01; add focused HTTP-to-reader fixture integration evidence; document clean-checkout startup and direct shared-service handoff. | **Formally accepted with minor changes** by the Technical Lead after independent review; M4-01 was resolved in this documentation update. |

The Technical Lead formally accepted M1 after independent review on exact head `1fef9c7f27cb27068f8fcb415378771b878d4aed`, M2 after independent ACCEPT on exact head `cd7d3319760379716244e4db6c0cf0cb96ec6cbd`, and M3 with minor follow-up M3-01 after independent `ACCEPT_WITH_MINOR_CHANGES` review on exact head `6169e850d824e3f6eccc1faa57b3d4a311646bd6`. The Technical Lead later formally accepted M4 with minor changes after independent review of exact head `db2d8ce47e7704e7beb11f7c7b08fd846ac1619c`; M3-01 was resolved in M4 and M4-01 is resolved by this documentation-only correction. The implementation milestones are accepted; separate final PR integration/merge-readiness review and formal Phase 11 closeout remain pending. Keep PR #26 open, draft and unmerged. Streamlit, hosting/deployment, inference and Phase 13 evaluation remain outside scope.

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

## M3 authorization and frozen HTTP contract — 2026-10-09

The Technical Lead formally accepted M2 after independent ACCEPT on PR #26 head
`cd7d3319760379716244e4db6c0cf0cb96ec6cbd` and authorized M3 implementation on the same draft PR.
M3 remains IMPLEMENTED / UNDER REVIEW until separate independent review. M4 is not authorized.

M3 is a thin adapter over the existing `ApplicationServices`; successful responses return the
existing JSON-safe DTO fields directly at the top level. There is no business-route request body,
artifact selector, path, run ID, model option, or file name. Query names must match the table exactly,
and repeated or unknown query parameters return the fixed 422 request error. Dates use `YYYY-MM-DD`.

| Method and path | Query contract | Success response |
|---|---|---|
| `GET /health` | None | `{"status":"ok","mode":"local_read_only"}`; does not touch artifacts. |
| `GET /api/v1/catalog` | None | Existing catalog DTO, preserving its resource validation levels. |
| `GET /api/v1/forecasts` | Required `store_id` (1–1115), `forecast_origin` (one accepted Phase 7 date). | Existing forecast issuance DTO; at most 14 rows and no retrospective assessment fields. |
| `GET /api/v1/uncertainty` | Required `store_id` (1–1115), `forecast_origin`, `fit_id` (`A`/`B` with its matching origin). | Existing uncertainty DTO with separate daily/cumulative results, provenance and interpretation. |
| `GET /api/v1/model-comparison` | Optional exact filters `candidate_id`, `population`, `scope`, `validation_window`, `horizon` (1–14), `store_id` (1–1115), `metric`; `limit` defaults to 200 and is 1–500. At least one data filter is required. | Existing comparison DTO; saved producer metrics and denominators remain unchanged. |
| `GET /api/v1/inventory` | Required `case_id` matching `[A-Za-z0-9._-]{1,128}`; optional `store_id` (1–1115). | Existing case aggregates, policy pairs, provenance and state. Case aggregates retain whole-case scope under Store filtering. |
| `GET /api/v1/history` | Required `store_id` (1–1115), `start_date`, `end_date`; inclusive range at most 366 days within 2013-01-01–2015-07-03. | Existing history DTO with only Store/Date/Sales/Open and the July 3 cutoff. |

Request parsing failures, invalid M1/M2 query bounds and unsupported/extra query parameters return
HTTP 422 with a fixed JSON error envelope. `invalid_artifact_request` and
`unsupported_artifact_selector` remain 422. Missing required canonical outputs, unsafe paths,
duplicate keys, integrity failures and schema failures return HTTP 503 with their stable
`ArtifactErrorCode` and sanitized message. Unexpected failures return HTTP 500 with fixed
`internal_error`; unknown paths/methods return fixed 404/405 envelopes. Error responses never expose
input values, stack traces, local paths, raw exception text or manifest data. Successful empty
selection results remain normal 200 DTOs.

Only these six API paths plus `/health` are exposed; FastAPI's generated docs/OpenAPI routes are
disabled. The local serving example binds Uvicorn to `127.0.0.1`. This is a local/demo adapter, not
public hosting or production hardening. Phase 10 ledger, protected holdout and unneeded historical
source data remain outside M3.

## Deferred matters for later authorized milestones

- The M3 route names, request/response mapping and error translation are frozen above; changing them requires a written clarification and renewed authorization. M2's selectors, query bounds, history wrapper and case-level versus Store-level inventory views are frozen below.
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
| Inventory comparison | Phase 10 comparison CSV by known `case_id`, plus policy summary and targets by `case_id` and optional Store. | Store 1–1115 when supplied; at most 2,230 policy rows per case when omitted (two fixed policy IDs across at most 1,115 stores). Return producer case-level aggregates unchanged and pair baseline/forecast by `(case_id, Store)` after key, policy-ID and provenance checks. Evaluate each policy's episode completeness, target availability/value, and matched-comparison validity independently; do not require equal policy states. The only derived arithmetic is the signed per-Store forecast-policy minus baseline-policy simulated holding-plus-shortfall cost for eligible pairs. Do not average ratios or hide adverse values. |
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

For inventory pair eligibility, both policies must have complete episodes, available targets with
non-null saved values, valid matched-comparison flags, and saved costs. Preserve each policy's
episode status/reason, target status/reason, validity and cost even when the pair is not comparable.
The pair-level unavailable-reason priority is deterministic: first incomplete episode (use the first
incomplete policy's summary reason), then unavailable target (use the first unavailable policy's
target reason), then `not_valid_matched_comparison`, then `cost_unavailable`. This priority does not
replace or discard individual policy states. A target is structurally inconsistent when its
availability flag disagrees with its reason or when an available target has no saved value / an
unavailable target has a saved value.

## Phase 11 M4 integration handoff

At this M4 implementation handoff checkpoint, M3 had been accepted with minor follow-up M3-01
and M4 was authorized on this branch and draft PR. The independent review and later Technical Lead
acceptance are recorded in the M4 acceptance checkpoint below. M1, M2 and M3 acceptance checkpoints
remain intact; Phase 11 remains incomplete and PR #26 remains draft and unmerged.

M3-01: the centralized Starlette HTTP exception handler must preserve only the framework's
`Allow` response header on 405 responses. Keep the fixed sanitized JSON body and status, do not
echo exception text or forward arbitrary headers, and use the methods Starlette reports for each
route. Tests must cover `POST /health`, another GET route, no service dispatch, and stable 404.

The approved request path is FastAPI `create_app()` in
`src/rossmann_forecasting/app/api.py` -> typed requests from `app.contracts` ->
`ApplicationServices` in `app.services` -> the fixed M1 `_ArtifactReader` in
`app.artifacts` -> pinned and schema-validated development artifacts -> `json_safe` DTO response.
The public service views are `catalog()`, `forecast_issuance()`, `forecast_uncertainty()`,
`model_comparison()`, `inventory_comparison()`, and `sales_history()`. A future Streamlit UI
calls these same shared services directly; it must not depend on an HTTP loopback to FastAPI.

M4 integration tests use isolated producer-schema fixtures and trusted fixture hashes. Combine the
existing reader, service and API coverage at the HTTP boundary without repeating each layer's full
unit suite. Verify canonical identities and provenance, deterministic JSON-safe success responses,
producer metrics and denominators, case-wide aggregates alongside Store pairs, signed simulated
costs and unavailable nulls, cutoff-safe history, honest empty results, sanitized 503 failures, and
closed routes/queries. No fixture may contain real protected outcomes. Never open or hash the
Phase 10 ledger or protected July outcomes.

Clean-checkout tests install the locked `dev` and optional `api` extras and require no Rossmann
data or Kaggle credentials. Local forecast, uncertainty, comparison and inventory demonstrations
require the ignored, approved canonical artifacts and manifests; missing sources must stay
unavailable or return sanitized 503. `/health` 200 reports process response only, not artifact
integrity. The serving command binds Uvicorn to `127.0.0.1`; no packaging, cloud service or public
hosting is included.

The accepted artifact identities are pinned in `CANONICAL_RUNS` in
`src/rossmann_forecasting/app/artifacts.py`; the Phase 7 selected candidate remains
`global_lightgbm_gbdt_regression_l1`. One supported reference case is
`synthetic_base-20150605-r00--reference`; the Phase 10 buffer-`0.90` sensitivity case is
`synthetic_base-20150605-r00--buffer_090`. See [PROGRESS](../../docs/PROGRESS.md) for accepted run
and manifest digests. Output hash memoization stays process-local under the accepted immutable local
artifact assumption; it is not a durable cache or proof against same-fingerprint mutation.

Historical access remains one Store, at most 366 inclusive days from 2013-01-01 through 2015-07-03,
projecting only `Store`, `Date`, `Sales`, and `Open`. Sales is monetary turnover, not physical
demand. Inventory values, costs, stockouts, equivalent units and policy comparisons are synthetic
conditional monetary simulations, not observed stock or proven savings. A positive forecast-policy
minus baseline-policy cost is adverse. Preserve producer case aggregates, Store pairs, provenance,
nulls and reasons; do not recompute pooled ratios.

The API's optional dependency extra retains the upstream Starlette TestClient deprecation warning
for its HTTPX fallback. It does not occur on application/Uvicorn startup and is nonblocking. Keep
the Python 3.12/3.14 CI matrix and locked environment unchanged unless an implemented correctness
requirement demonstrates otherwise.

The independent M4 review examined the complete fixture-backed HTTP -> M2 -> M1 path, failure
and serialization behavior, startup examples, quality evidence and canonical compatibility. It
returned `ACCEPT_WITH_MINOR_CHANGES`; the Technical Lead formally accepted M4. The separate final
Phase 11 integration review and explicit closeout remain pending.

## Phase 11 M4 independent review and acceptance - 2026-10-09

The independent review of PR #26 head `db2d8ce47e7704e7beb11f7c7b08fd846ac1619c` returned
`ACCEPT_WITH_MINOR_CHANGES`. It confirmed M3-01 is resolved and identified M4-01 as a stale current-
status paragraph in PROGRESS. The documentation-only correction is recorded in the Phase 11 M4
acceptance checkpoint there. The Technical Lead formally accepted M4 with minor changes.

M1-M4 implementation milestones are accepted and M3-01/M4-01 are resolved. A separate final PR
integration and merge-readiness review and explicit Phase 11 closeout remain pending. PR #26 stays
open, draft and unmerged. The protected holdout remains unreleased.
