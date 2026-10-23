# Public Course Demonstration

**Current state (2026-10-23):** Milestone A is **REVIEWED / INTEGRATED** through PR #52 at
`086c59183e237279a21139a62265e7450890fa63`; B1 is **REVIEWED / INTEGRATED** through PR #53 at
`a31f9d610ea7922629d24c4b134cd986f634bcb4`. B2-A is **REVIEWED / INTEGRATED** through PR #54 at
`232c7307f75d1ae7906af621853a8753ebe81795`. WP2-S16 authorizes local B2-B synthetic Streamlit
dashboard implementation and offline AppTest validation on `feat/public-demo-synthetic-streamlit-dashboard`.
B2-B is **IMPLEMENTED / UNDER REVIEW — AWAITING SOL 6.1**. Milestone B remains incomplete; Milestone C,
release, hosting and deployment remain unauthorized under ADR-024 and ADR-030.

**Current task branch and base:** `feat/public-demo-synthetic-streamlit-dashboard`, from
`origin/main` at `232c7307f75d1ae7906af621853a8753ebe81795`. The earlier Milestone A, B1 and B2-A
branches and review checkpoints below are preserved as history.

## Accepted objective and fixed boundaries

The future course demonstration may provide two separately reachable public URLs: a read-only
FastAPI service and a Streamlit dashboard. Both may consume the same versioned immutable approved
bundle using a typed provider; Streamlit continues direct Python calls and does not need HTTP
loopback. Controlled synthetic content comes first. Render is the preferred candidate for later
assessment only.

Milestone A produces a small deterministic bundle and manifest offline under the ignored
`artifacts/public_demo/` convention. It packages no Rossmann-derived data, canonical runs, model
identities, source hashes, credentials, authorization records or protected outcomes. Fixed fixture
arithmetic demonstrates the existing six service categories and five screens. No training,
prediction generation, calibration, inventory simulation, source discovery, network access, public
listener, publication or host provisioning is permitted.

Scientific meaning remains monetary Store × Date Sales, a 14-day horizon, development dates through
2015-07-03 and all existing forecast, metric, uncertainty, inventory and holdout contracts. Synthetic
fixtures cannot substantiate empirical or operational claims. A missing bundle must not fall back to
canonical local artifacts in any later explicit public profile. Bundle readiness, process health and
per-view availability are separate concepts.

## Milestones

| Milestone | Scope and exit evidence | State |
|---|---|---|
| A — Offline controlled-synthetic release candidate | Release contract; exact versioned schema; deterministic builder; bounded canonical JSON manifest and payload; standalone verifier with integrity and semantic checks; focused corruption, content and side-effect tests; ignored local candidate only; independent Sol 6.1 review | **REVIEWED / INTEGRATED through WP2-S8/S9 and PR #52** |
| B - Explicit public-compatible application profile | B1 typed offline provider and services; B2-A synthetic FastAPI adapter; B2-B separate direct-service Streamlit dashboard; no change to local defaults, canonical reader pins or scientific methods | **B1 and B2-A REVIEWED / INTEGRATED through PR #53 and PR #54. B2-B IMPLEMENTED / UNDER REVIEW awaiting Sol 6.1 under WP2-S16. Overall Milestone B INCOMPLETE.** |
| C — Staging and public release | Exact-content/rights approval, independent security review, resource/rollback plan and explicit hosting/audience/window authorization; owner-approved bundle hash; staged external checks; release and shutdown record | NOT AUTHORIZED |

## Milestone A design and acceptance

The release identity is `rossmann-course-demo-synthetic-v1`, schema `1.0.0`, evidence kind
`controlled_synthetic_demo`, and fixed seed `4063`. The finite synthetic population contains Stores
101, 202 and 303; origins 2015-05-22, 2015-06-05 and 2015-06-19; H14 forecasts; synthetic Fit A
and Fit B display pairings for the two June origins; a 56-day history window ending 2015-07-03;
an illustrative comparison panel; and reference/adverse inventory examples with one explicit
unavailable case. These identifiers and values are fixture identities, not Rossmann Store mapping,
canonical model runs or historical evaluations.

The bundle records field meanings, monetary units, synthetic source/licensing declarations, query
allowlists, exact date/Store bounds, availability and null semantics, label provenance, limitations,
and exclusions. The manifest records code/config/lock/environment identity, SHA-256 and byte counts,
row counts, populations, supported queries and the same exclusions. Canonical JSON rejects duplicate
keys and nonfinite values. A verifier accepts only the two exact filenames, enforces the 5 MiB bundle
and 64 KiB manifest encoded-size targets before decoding, validates exact schemas/counts/identities,
and supports an out-of-band manifest hash pin plus deterministic regeneration.

The builder writes only to a new fixed release-ID directory below ignored
`artifacts/public_demo/`; it refuses an existing directory and publishes both files as one atomic
directory rename. Generated bytes remain untracked and offline. This directory convention and the
application checks do not prove hard memory containment, source rights or publication authority.

## WP2-S2 independent review and WP2-S3 correction checkpoint — 2026-10-21

WP2-S2 returned **REQUEST_CHANGES** for three findings: Windows junctions could redirect builder
output and verifier input; ordinary verification did not bind the manifest's configuration digest
or require complete, well-formed provenance; and an integral float could pass as a manifest byte
count. WP2-S3 corrected those issues without changing the accepted synthetic content or application
contracts.

The builder and directory verifier now reject symlinks and Windows reparse-point aliases in every
existing path component and check resolved containment under the trusted checkout root. The
manifest validator recomputes the fixed configuration digest; requires module, builder-script,
project and lock SHA-256 identities; validates nonempty required distribution versions and an
optional exact-length Git revision; and requires a bounded integer bundle byte count. Regeneration
continues to check the current source and environment identities, while ordinary verification
checks intrinsic manifest consistency.

The regressions cover actual CLI rejection of an `artifacts` junction, output and verifier aliases
at multiple path levels, traversal and outside paths, no-overwrite, injected write/rename cleanup,
resealed manifest mutations, and strict byte-count types. The confirmed WP2-S2 cases were reproduced
in a disposable checkout of the original snapshot before applying the fixes.

Milestone A remains **IMPLEMENTED / UNDER REVIEW — AWAITING INDEPENDENT SOL 6.1 REREVIEW**. This
checkpoint records no bundle release, Milestone B/C authorization, deployment, public exposure, or
real-source permission.

Milestone B must adapt this reviewed schema to the existing typed service views where their
provenance and semantics fit. It must distinguish synthetic evidence from canonical phase/run
identity, keep Streamlit on direct Python calls, require an explicit demo profile, preserve localhost
defaults, and never substitute canonical files when the bundle is missing. If an existing DTO cannot
represent that distinction honestly, a profile-specific typed wrapper requires separate review.

Milestone A completes only after the scoped locked-environment tests and quality checks pass, the
full diff and untracked-output isolation are checked, and the exact snapshot is handed to independent
Sol 6.1 review. Review acceptance does not authorize Milestone B, any publication or a public release.

## WP2-S5 correction of WP2-S4 version-grammar finding - 2026-10-21

WP2-S4 showed that ordinary verification accepted malformed installed-dependency versions `1+.`
and `1a1b1` even with a canonically resealed manifest and matching manifest hash pin. WP2-S5 adds a
bounded local PEP 440-compatible normalized grammar for required installed versions. The verifier
supports numeric releases, optional epochs and `a`/`b`/`rc`, `.post`, `.dev`, and local-version
segments. The bound is 128 characters; no production `packaging` import, dependency, or lock change
is needed. Ordinary verification still checks intrinsic manifest syntax and identity; deterministic
regeneration checks equality with the current installed environment.

Permanent regressions apply malformed and valid version representatives to every required
dependency, canonicalize each changed manifest, and supply its matching SHA-256 pin. They also check
that a valid portable version passes ordinary verification but fails deterministic regeneration
when it differs from the host. The initial red-first test run reproduced both WP2-S4 examples.

Milestone A remains **IMPLEMENTED / UNDER REVIEW - AWAITING INDEPENDENT SOL 6.1 REREVIEW**. This
correction does not authorize Milestone B/C, publication, deployment, a public listener, or use of
real-source content.

## WP2-S6 independent rereview and WP2-S7 correction — 2026-10-22

WP2-S6 returned **REQUEST_CHANGES** for WP2-S6-01, a MAJOR Unicode case-folding bypass in the
documented ASCII dependency-version grammar. Python's Unicode case-insensitive matching accepted
five malformed values, including `1+\u212a` and `1.0.po\u017ft1`, through ordinary pinned
verification. WP2-S7 preserves the existing grammar and adds `re.ASCII` to its existing
case-insensitive regular expression. The 128-character bound, strict string checks, plain-verifier
portability, and regeneration identity check remain unchanged. Tests apply five original bypasses
and representative Unicode digits, local letters, combining marks, whitespace, and keyword
lookalikes across all five dependency fields, plus a real CLI rejection with a matching manifest
pin. The full test and quality evidence, generated identities, and final ten-file hashes are
recorded in [PROGRESS](../../docs/PROGRESS.md#wp2-s7-ascii-dependency-version-validation-2026-10-22).

Milestone A remains **IMPLEMENTED / UNDER REVIEW — AWAITING SOL 6.1 REREVIEW**. No public bundle
release, Git publication, deployment, real-source access, or Milestone B/C implementation is
authorized.

## WP2-S10 B1 interface contract and execution plan

WP2-S10 authorizes the offline provider and typed read-only services only. The implementation must
not change the current API, Streamlit dashboard, localhost settings, canonical artifact reader,
scientific methods, or dependency lock. The generated release stays in a temporary fixture for
tests; no manifest pin is approved for public release.

### Provider contract

- Construction requires the explicit `CONTROLLED_SYNTHETIC` profile and an independently supplied,
  lowercase 64-character manifest SHA-256. The release directory is derived internally from the
  trusted repository root and fixed release ID; query objects cannot supply paths or selectors.
- Construction calls the Milestone A `verify_release_directory` validator with that mandatory pin.
  The provider loads the two bounded files once at construction, checks the loaded bytes against the
  verified bundle and manifest digests, decodes only those verified bytes, and stores a recursively
  immutable snapshot. It builds fixed, bounded indexes for history, issuance, uncertainty,
  comparison and inventory rows. Queries perform no filesystem reads.
- Missing, malformed, tampered, mismatched, aliased or extra-file releases fail closed with fixed,
  sanitized typed errors. No unpinned mode, regeneration, download, canonical fallback or service
  readiness is returned on construction failure.
- Every response uses a frozen synthetic provenance wrapper carrying release ID, evidence kind,
  bundle and manifest SHA-256, schema version, source kind, view ID and selected-row count. Synthetic
  DTOs replace canonical provenance fields whose phase/run/artifact semantics would be false.
- Results preserve saved values, order, nulls, zeros, sparse dates, unavailable reasons and evidence
  declarations. Services do no arithmetic, model execution, calibration, selection or simulation.
  The provider has no network or write path.

### Query and service contract

Reuse `HistoryQuery`, `ForecastQuery`, `UncertaintyQuery`, `ModelComparisonQuery`, and
`InventoryComparisonQuery` as request DTOs, with additional strict checks against the embedded
fixed allowlist. `DemoServices` exposes `catalog()`, `sales_history(query)`,
`forecast_issuance(query)`, `forecast_uncertainty(query)`, `model_comparison(query)`, and
`inventory_comparison(query)`. The six result families are frozen synthetic DTOs with machine-readable
provenance and explicit availability.

History is Store 101/202/303 within 2015-05-09 through 2015-07-03 and at most 56 inclusive calendar
days; missing dates stay absent and null Sales is not zero. Issuance accepts the three saved origins
and returns exact H1-H14 rows, both forecast paths, eligibility, trajectory identity and
`model_execution=none`. Uncertainty accepts only `(demo_fit_a, 2015-06-05)` or
`(demo_fit_b, 2015-06-19)` and returns saved daily/cumulative rows, including unavailable values.
Comparison filters are restricted to the fixed candidate, population, window, scope, metric, horizon
and Store dimensions, with no more than 500 saved rows. Inventory accepts only the two fixed cases;
Store filtering applies only to policy-pair detail, while case aggregates retain their all-Store
population and denominator scope.

### B2 adapter handoff and checks

The later adapter task must keep the existing shared-service/thin-API/direct-Streamlit architecture.
It must explicitly select a synthetic profile at runtime, obtain the approved manifest pin from a
trusted deployment configuration rather than from the manifest, serialize the synthetic provenance
as a source label in every API response and dashboard screen, map invalid queries to sanitized 422
responses and unavailable/invalid releases to sanitized 503 responses, and keep `/health` as process
health separate from bundle and view readiness. The five dashboard screens are Overview & Evidence,
Historical Sales, Forecast Explorer (including uncertainty), Model Comparison, and Inventory
Comparison. B2 must replace canonical phase/run provenance assumptions and fixed selectors/wording
(including canonical Store/origin/Fit/candidate/case labels and empirical LightGBM/uncertainty claims)
with profile-aware synthetic selectors and captions. No B2 changes are part of this task.

The existing request DTOs remain reusable for history, issuance, uncertainty, model comparison and
inventory queries. The B1 service-specific result DTOs carry those query values plus a synthetic
provenance object; B2 must not serialize canonical response wrappers that require phase/run IDs,
artifact validation identities or a model-selection run ID. Numerical rows and units can be mapped
directly when their field meaning is unchanged. Each API response body should include a `provenance`
object with `release_id`, `evidence_kind`, `bundle_sha256`, `manifest_sha256`, `schema_version`,
`source_kind`, `view_id` and `selected_rows`, plus a visible controlled-synthetic source label. The
dashboard should show the same source label and relevant limitations on every screen.

Screen mapping: Overview & Evidence shows the synthetic source declaration, release identity,
limitations and per-view availability, removing empirical LightGBM and calibrated-uncertainty
claims. Historical Sales uses only the three synthetic Store IDs and bounded history dates, with
captions that identify authored fixture arithmetic. Forecast Explorer offers the three synthetic
origins and shows raw forecasts separately from operational values; its uncertainty controls offer
only Fit A at June 5 and Fit B at June 19, with incomplete/unavailable prefixes visible. Model
Comparison uses only `demo_path_a/b/c`, the synthetic population/window and saved scopes/metrics;
candidate labels must not imply Phase 7 or LightGBM performance. Inventory Comparison offers the two
synthetic cases and optional Store detail while keeping aggregates case-wide; captions identify
turnover-value cost proxies and explicitly avoid physical stock, observed stockouts or savings
claims. Invalid query DTOs map to sanitized HTTP 422, missing/invalid pinned releases to sanitized
503, and `/health` remains process liveness rather than release readiness.

Implementation and verification remain local and uncommitted: focused provider/service tests, the
existing Milestone A and application/API/dashboard regressions, then the full fixture suite in a
tracked-only isolated workspace with no local ignored data/artifacts; Ruff, documentation, locked
dependency, whitespace and deterministic release checks. Record actual results in PROGRESS. The
handoff after validation is independent Sol 6.1 review of B1 only.

## WP2-S12 B1 Git integration and CI identity clarification — 2026-10-23

The exact seven-file B1 snapshot was accepted in WP2-S11 and integrated by squash PR #53. Its
publication commit `626acf76726a63efe7f264e9669aaab11af90d19` was based on
`086c59183e237279a21139a62265e7450890fa63`; merge commit and `main` are
`a31f9d610ea7922629d24c4b134cd986f634bcb4`. PR Quality run
[#39924005789](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/actions/runs/39924005789)
and post-merge Quality run
[#39924475405](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/actions/runs/39924475405)
passed on Python 3.12 and 3.14. The PR jobs checked out temporary merge ref
`f2dd84f07d1d11c22a55c140397dfe4ab2e85fb1` (publication head into base `086c59183e237279a21139a62265e7450890fa63`);
post-merge jobs checked out squash merge `a31f9d610ea7922629d24c4b134cd986f634bcb4`.

This checkpoint resolves the nonblocking WP2-S11-01 documentation finding without rewriting its
historical checkpoint. Milestone A PR #52 Quality run
[#39904731393](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/actions/runs/39904731393)
was associated with publication head `5e1722220c0a3e2944788a470af68b4c3abc949d`. Its Python 3.12
job actually checked out temporary merge ref `ddae5428714dd9b784d12b91bcc40c00e4635eb7`, combining
that head with then-current base `a747d7799919497dead9b98bc0498c12115adfc2`; the later squash merge
was `086c59183e237279a21139a62265e7450890fa63`. Workflow association, tested merge-ref commit and
final squash merge are distinct identities.

## WP2-S13 B2-A synthetic FastAPI adapter implementation and validation — 2026-10-23

WP2-S13 authorizes only an offline, explicitly constructed FastAPI adapter over integrated B1
`DemoServices`, fixture tests using `TestClient`, and this plan plus `docs/PROGRESS.md`. The task
branch is based on B1 merge `a31f9d610ea7922629d24c4b134cd986f634bcb4`. No commit, push, PR, merge,
bundle publication, server startup, B2-B dashboard, hosting or deployment is authorized.

### Construction and release availability

`create_demo_app(*, profile, expected_manifest_sha256, repository_root=None)` has no defaults for
profile or pin. It requires the exact `DemoProfile.CONTROLLED_SYNTHETIC` enum and a separate
lowercase 64-character hexadecimal manifest SHA-256; missing or malformed configuration fails
factory construction. It calls `DemoServices.open` once with that explicit configuration and uses no
canonical services or fallback. If the configured release is missing, corrupt or mismatched, the
factory retains only the provider's fixed sanitized error code/message: `/health` remains available
as process liveness, all analytical routes return 503, and requests do not retry initialization.
Successful construction uses B1's already verified immutable in-memory snapshot. No import-time
scan, module-level synthetic `app`, query-supplied pin/path or network listener is introduced.

### HTTP and query contract

The application has exactly these GET paths, with FastAPI docs, ReDoc and OpenAPI disabled:

| Route | Accepted query |
|---|---|
| `/health` | None; process liveness only |
| `/api/v1/catalog` | None; B1 catalog, source declaration, six view-availability records and provenance |
| `/api/v1/history` | Required `store_id`, `start_date`, `end_date`; Stores 101/202/303; canonical dates from 2015-05-09 through 2015-07-03; inclusive maximum 56 days |
| `/api/v1/forecasts` | Required `store_id`, `forecast_origin`; the three B1 Stores and origins; saved H1–H14 raw/operational points and trajectory identity |
| `/api/v1/uncertainty` | Required `store_id`, `forecast_origin`, `fit_id`; only `demo_fit_a`/2015-06-05 and `demo_fit_b`/2015-06-19 pairings |
| `/api/v1/model-comparison` | Optional `candidate_id`, `population`, `scope`, `validation_window`, `horizon`, `store_id`, `metric`, `limit`; B1 allowlists, maximum 500 saved rows, default limit 200 |
| `/api/v1/inventory` | Required `case_id`; optional `store_id`; only the two B1 case IDs; store filtering affects policy-pair detail while aggregates remain case-wide |

Each analytical response is `{evidence_label, data, provenance}`. `data` contains the complete
frozen typed B1 result except that its provenance field is moved to the top-level `provenance`
object. The exact label is `CONTROLLED SYNTHETIC DEMONSTRATION — NOT OBSERVED ROSSMANN DATA`.
Provenance retains B1's release, evidence kind, bundle/manifest SHA-256, schema, source kind, view
ID and selected-row count without canonical phase/run identifiers. The serializer accepts only
bounded frozen dataclasses, tuples and JSON primitives, finite numbers and exact date values;
unsupported values fail safely. Output is bounded to 2 MiB, nesting to 12 levels, 20,000 visited
values and 4,096 characters per string. Query strings are bounded to 4,096 bytes and individual
values to 128 characters (dates to exactly 10); numeric fields require canonical ASCII decimal
syntax. Unknown and repeated keys, bodies on GET, invalid bounds and unsupported filters are
rejected before B1 service dispatch. B1 allowlists remain the final query authority.

### Errors, liveness and isolation

Invalid query or request shape returns fixed sanitized HTTP 422. A missing, corrupt or mismatched
verified release returns sanitized HTTP 503. Unexpected request-time failures return sanitized HTTP
500; unknown paths and methods return sanitized 404/405, preserving the framework's `Allow` header
on 405. Error bodies never contain exception text, object representations, paths, environment data
or release contents. `/health` reports only process liveness and makes no bundle/readiness claim.
No unrestricted CORS, writes, uploads, admin routes, arbitrary file access, model execution,
calibration, metric calculation or inventory simulation are allowed.

Tests generate deterministic bundle/manifest bytes into per-test temporary repositories, independently
hash the manifest bytes and supply that pin to the factory. Coverage includes all seven routes,
supported query combinations and edge values, malformed/duplicate/unknown inputs and bodies,
missing/wrong/tampered release handling, sanitized errors, health versus readiness, no canonical
fallback, no post-construction file/network access, no model/simulator calls, route/method
inventory, deterministic output and repeated-request isolation.

The implementation is in `src/rossmann_forecasting/app/demo_api.py`, with fixture-only HTTP
coverage in `tests/test_public_demo_api.py`. Focused regressions, the artifact-free tracked-only
full suite, locked-environment checks, Ruff, Markdown and whitespace checks passed. Detailed
counts and skip reasons are recorded in [PROGRESS](../../docs/PROGRESS.md#wp2-s13-b2-a-offline-synthetic-fastapi-adapter-2026-10-23).
No dependency, canonical API, Streamlit entry point, localhost configuration, generated release
asset, server startup, commit or publication was performed. B2-A is **IMPLEMENTED / UNDER REVIEW — AWAITING SOL 6.1**; B2-B and Milestone B closeout remain outside this authorization.


## WP2-S15 B2-A Git integration and CI - 2026-10-23

The exact four-file WP2-S14-accepted B2-A snapshot was integrated through PR #54. Publication head
`26eaed63f272cb931275b080e66b7eb982fb9790` was based on `a31f9d610ea7922629d24c4b134cd986f634bcb4`.
The PR jobs checked out temporary merge ref `bc547266b964924beab06e3fe732eede16326b26`, whose
parents were the base and publication head and whose tree matched the publication-head tree. The
squash merge and resulting `main` revision are `232c7307f75d1ae7906af621853a8753ebe81795`.

PR Quality run [#39934550249](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/actions/runs/39934550249)
and post-merge Quality run [#39935158003](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/actions/runs/39935158003)
passed on Python 3.12 and 3.14. All four jobs reported 1,548 passed, 8 skipped and one existing
Starlette/httpx deprecation warning. The temporary PR merge ref is distinct from both publication
head and squash merge. WP2-S14 returned ACCEPT; its nonblocking WP2-S14-01 inventory regression gap
was disclosed in PR #54 and carried forward for the B2-B test correction below.


## WP2-S16 B2-B synthetic Streamlit dashboard implementation and validation 2026-10-23

**Status:** B2-B implementation is authorized by WP2-S16 and is implemented locally on
`feat/public-demo-synthetic-streamlit-dashboard`, based directly on `232c7307f75d1ae7906af621853a8753ebe81795`.
This work is local, offline and fixture-backed. It authorizes no commit, push, PR, merge, bundle
publication, listener, hosting, deployment, public release, or Milestone C work.

### Architecture and trusted configuration

The separate renderer is `run_demo_dashboard(services: DemoServices)` in
`src/rossmann_forecasting/app/demo_dashboard.py`. It accepts a B1 verified service instance and calls
its six Python methods directly; it does not use the FastAPI adapter or canonical presenters. The
separate root entrypoint `demo_streamlit_app.py` reads only `ROSSMANN_DEMO_PROFILE` and
`ROSSMANN_DEMO_MANIFEST_SHA256` from trusted process configuration. The profile must exactly equal
`controlled_synthetic_demo`; the independently supplied pin must match lowercase `[0-9a-f]{64}`.
The release root is fixed by the checked-out entrypoint, never user-selected. Missing/malformed
configuration and missing/invalid pinned content render fixed sanitized states without a traceback,
path or secret and never fall back to canonical services.

Verified services and a fixed failure state are retained only in Streamlit's per-session state under
the exact current profile/pin pair. A changed or invalid configuration clears any prior service
before rendering. No process-wide resource cache is used. A service is verified once for the current
session configuration; B1 then serves its immutable in-memory snapshot on widget reruns. Corrected or
new release configuration requires a new verified construction, with no silent old-service reuse.
Importing the entrypoint performs no configuration read, release scan or service construction.

### Five screens and presentation contract

1. **Overview & Evidence** uses `catalog()` to show fixed release/schema/evidence identities, Stores,
   origins, Fit pairings, candidate and inventory-case IDs, all six view-availability rows, source
   declaration, units, limitations and provenance. Bundle readiness, each view's availability and
   this Streamlit page's rendering status remain distinct.
2. **Historical Sales** uses `sales_history(HistoryQuery(...))` with only Stores 101/202/303 and
   dates 2015-05-09 through 2015-07-03, at most 56 inclusive days. Tables contain only saved rows;
   sparse dates stay absent, null Sales stays null, zero remains zero, and synthetic Open is a
   separate Open/Closed/Unknown field. Chart-only NaN coordinates break lines across absent/null
   dates without creating table observations.
3. **Forecast Explorer and Uncertainty** uses `forecast_issuance(ForecastQuery(...))` for the three
   saved origins and H1-H14. Raw and operational forecasts, availability, synthetic eligibility,
   trajectory and `model_execution=none` remain separate. `forecast_uncertainty(UncertaintyQuery(...))`
   is called only for `demo_fit_a`/2015-06-05 or `demo_fit_b`/2015-06-19; May 22 shows an explicit
   unavailable state. Daily intervals and cumulative rows are saved values only, with unavailable
   reasons, incomplete prefixes, schedule flags, units, probabilities and provenance retained.
4. **Model Comparison** uses `model_comparison(ModelComparisonQuery(...))` and only the finite B1
   synthetic allowlists: saved candidates, population, window, scopes, metrics, horizons and Stores.
   It displays saved values/numerators/denominators/reasons and candidate labels; empty intersections
   are empty, limits remain bounded, and no metric or winner is recalculated.
5. **Inventory Comparison** uses `inventory_comparison(InventoryComparisonQuery(...))` for the two
   saved cases. Store selection filters policy-pair detail only; the exact case-wide aggregate DTO
   rows, population counts and denominators are displayed unchanged. Signed values and null reasons
   remain intact, including adverse Store 303 unavailability.

Every screen shows the exact persistent evidence label `CONTROLLED SYNTHETIC DEMONSTRATION - NOT
OBSERVED ROSSMANN DATA` (the UI uses an em dash), relevant limitation text and machine-readable
`SyntheticProvenance` fields. Presentation code may map frozen DTOs to deterministic tables and chart
coordinates, but it does not fit models, recalculate metrics, estimate interval bounds, fill missing
scientific values, reaggregate inventory results, invoke the Phase 10 simulator, or render unsafe
HTML/Markdown. Matplotlib figures are closed after display.

### Errors, tests and compatibility boundary

B1 invalid requests, unavailable/invalid releases and bounded provider errors map to fixed user-facing
messages. Unexpected errors also render a generic message without exception text or traceback. No
failure triggers a retry, download, repair, or canonical fallback. AppTest uses generated temporary
controlled-synthetic bundles and separately computed manifest pins to exercise startup/configuration,
all five screens, filtering, empty/unavailable values, provenance, session changes, and canonical
isolation. The permanent API inventory test compares Store-101-filtered reference detail and
filtered adverse Store-303 detail against separate unfiltered case aggregates, including exact
population counts and denominators; WP2-S14-01 is resolved after this regression passes.

Canonical `dashboard.py`, `dashboard_presenters.py`, `api.py`, `streamlit_app.py`, `.streamlit/config.toml`,
B1 provider/services/bundle, dependencies and scientific modules remain unchanged. ADR-024's localhost
behavior, ADR-028's proposed scope, ADR-030's authorization boundary, WP1 limitations and Phase 13
holdout gates remain intact. The numerical synthetic bundle remains offline and untracked. No visual
human acceptance is inferred from AppTest; independent Sol 6.1 review is the next technical gate.

### WP2-S14-01 permanent API regression correction — 2026-10-23

The reference-case API request now explicitly filters policy-pair detail to Store 101 and asserts
that this is the only returned detail row. It makes a separate unfiltered request for the same case
and compares all case-wide aggregate rows plus metric, requested and matched population counts, and
baseline/forecast numerators and denominators. The adverse-case Store 303 request retains its
unavailable cost and reason assertions and applies the same filtered-versus-unfiltered aggregate
check. `tests/test_public_demo_api.py::test_inventory_route_supports_both_cases_and_preserves_case_aggregates`
passed both parametrized cases. This resolves the deferred WP2-S14-01 test gap without changing the
API or B1 service behavior.

### WP2-S16 implementation and validation evidence — 2026-10-23

The implementation adds the isolated `run_demo_dashboard(services)` renderer in
`src/rossmann_forecasting/app/demo_dashboard.py`, the explicitly invoked root entrypoint
`demo_streamlit_app.py`, and fixture-only AppTest coverage in
`tests/test_public_demo_dashboard.py`. The README documents the local process settings and run
command. The renderer uses only the six direct B1 Python services; it imports neither canonical
`ApplicationServices` nor the synthetic FastAPI adapter. The canonical dashboard, its presenters,
entrypoint, configuration, API, B1 provider/services/bundle, lockfile, dependencies, CI and scientific
modules are unchanged.

The five screens render the saved catalog, sparse Sales history, forecast/uncertainty rows, finite
model comparison results and case-wide inventory aggregates with selected Store detail. Query
selectors stay within the release's Stores, origins, horizons, fit pairings, comparison values and
case IDs. Null, zero, unknown Open, unavailable paths, interval reasons, schedule flags, signed cost
differences and full-population aggregate denominators remain distinct. Charts use display-only
coordinates, and no model, metric, quantile, inventory target or aggregate is recomputed. Each screen
shows the exact synthetic label, a relevant limitation, verified release identity and machine-readable
provenance when a view result is available. Startup errors are fixed and sanitized.

The entrypoint reads `ROSSMANN_DEMO_PROFILE` and `ROSSMANN_DEMO_MANIFEST_SHA256` only when run. The
profile must be exactly `controlled_synthetic_demo`; the independent pin must be lowercase 64-digit
hex. The repository release location is fixed. Verified services or a fixed failure are scoped to
the current Streamlit session and exact profile/pin pair; configuration changes clear the old state.
Imports do not inspect configuration or scan for releases, and widget reruns reuse the verified
immutable B1 snapshot without rereading release files. AppTest covered all five screens, all Stores,
three origins, H1-H14, both approved June Fit pairings, May 22 uncertainty unavailability, unknown
and closed eligibility, incomplete cumulative rows, valid empty queries, over-limit results, both
inventory cases, all Store detail filters, missing/wrong/tampered releases, configuration changes,
no canonical fallback, no release reread and no network connection.

The generated numerical fixture remained **326,074 bytes**, bundle SHA-256
`9b7ee60df204d11a4a993a84ceb236c5885c373168b0d6a767c99654683ecfdb`. The generated manifest was
3,708 bytes with SHA-256
`31d4760e890cbf2f048e7aa7cdd9b33908eacdb627c3a17be3dfea5ca3851bd9` for this source revision and
environment. Bytes were generated in memory and written only to temporary test repositories; no
JSON release was added to Git or published.

Validation used `.venv` Python 3.14.5. The final focused dashboard plus full synthetic API command
passed **87 tests** in 29.88 seconds with one existing Starlette/httpx deprecation warning. The
provider, services, bundle, API and canonical dashboard/API regression command passed **464 tests**,
with one symlink test skipped for Windows WinError 1314 and the same warning, in 52.92 seconds. The
full suite ran in a detached tracked-only worktree at the B2-A base with the exact S16 files copied
in and no ignored artifacts: **1,576 passed, 8 skipped, 1 warning** in 369.12 seconds. Seven skips
were Windows symlink privilege checks; one was the existing optional canonical-artifact test. Ruff
lint passed and all 155 Python files passed the format check. Markdown validation passed for 353
local destinations/anchors across 38 Markdown files. Offline `uv lock --check` resolved 109 locked
packages; offline `uv pip check` found all 93 installed packages compatible; `git diff --check`
passed. The sole warning was the existing Starlette/httpx test-client deprecation. No real Rossmann
or protected holdout data was read. AppTest is not human visual acceptance.

The current branch remains local and uncommitted at base
`232c7307f75d1ae7906af621853a8753ebe81795`; nothing was staged, pushed or published, and no listener
was started. B2-B is **IMPLEMENTED / UNDER REVIEW — AWAITING SOL 6.1**. Milestone B remains incomplete;
Milestone C, public bundle release, external URLs and deployment are not authorized.
