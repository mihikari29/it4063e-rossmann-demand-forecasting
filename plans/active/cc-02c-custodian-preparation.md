# CC-02C — Fixture-Only Custodian Preparation

**State:** **IMPLEMENTED / UNDER REVIEW** under the explicit 2026-10-12 fixture-only owner task.
Real source access and preparation are not authorized.

## Scope and boundary

Implement a bounded transformation over an already supplied immutable byte snapshot. Synthetic
tests exercise source identity validation, strict CSV extraction through 2015-07-03, int64
preservation, deterministic Parquet, the exact CC-02B provider manifest, staged publication, a
separate preparation receipt, and the existing provider-to-STL path. The public command describes
the contract or fails closed without opening a data file. The private byte-snapshot seam exists for
artificial fixtures and grants no permission.

The documented future source is `data/raw/rossmann/train.csv`, with recorded identity
38,057,952 bytes and SHA-256
`f6e4597c142d7d909a13d53b68a8e85c00b9a4c7b5ff40adbb37d6829cc1f4cc`. Those historical values are
not checked against local files in this task. Any future custodian read mechanically includes
protected bytes in the mixed source and requires separate explicit authorization.

The bundle contains exactly `sales.parquet` and `partition_manifest.json` under
`data/interim/cc02_development/<artifact_id>/`. Parquet contains Store int64, timezone-naive
Date timestamp[us], and Sales int64. Retain every row through the date ceiling, preserve source
zeros/gaps/values, reject duplicate keys and invalid eligible values, and sort Store then Date.
Never impute, aggregate, smooth, clip, choose Stores, or filter on Open/Sales positivity.

## Authorization and trust

Preparation configuration carries reference identities, not effective permissions. Fixture
references say `synthetic-only`. Production CLI execution remains disabled. Stable real source,
custodian, and preparation references must be genuine before a separately authorized preparation;
provider-loading and preflight references can be reserved as PENDING. An independently authorized
verifier validates the isolated bundle. Only a delegated external approver may then bind exact data
and manifest hashes and activate loading/preflight references. The manifest never changes when
external approval state changes. Preparation, provider loading, STL execution and publication of
findings are separate gates.

The output directory is a distinct artifact location, not OS-enforced isolation. The accepted
minimum claim is operator-enforced with a trusted custodian/operator and trusted machine owner and
administrator. Separate Windows identities and restrictive NTFS ACLs are optional hardening; do
not claim protection from the operator, owner or administrator.

## Verification

Use synthetic CSV bytes and temporary destinations only. Test exact cutoff inclusion/exclusion,
retention, source fidelity, strict parsing, output types/hashes/limits, repeatability, manifest
compatibility, safe publication and cleanup, protected canaries, CLI fail-closed behavior, and
synthetic end-to-end CC-02B provider/STL provenance. Run the focused tests, CC-02/CC-02B regressions,
isolated full fixture suite, Ruff, documentation checks, lock check and whitespace check. No test may
open repository data or canonical analytical artifacts.

Publication stages only under the bundle root and removes only the current invocation's staging
directory after an ordinary failure. If the process is interrupted or that cleanup fails, its hidden
`.stage-<artifact_id>-*` directory is inert and requires reviewed manual cleanup; there is no
startup sweep. Final directory publication uses a no-replace rename on supported Windows/Linux
platforms. If the separate receipt cannot be written after the completed bundle is published, the
bundle remains unbound and requires explicit reconciliation; the error does not issue permission.

## Documentation closeout

Record PR #41/#42 integration and Quality #135 success. Preserve historical checkpoints. Close
CC-02 and CC-02B fixture implementation status while keeping real Rossmann decomposition pending.
Clarify ADR-027 source-mechanical access, reference reservation/activation, downstream analytical
approval and the operator-enforced isolation claim. Phase 13 methods and gates are unchanged.

## Execution checkpoint — 2026-10-12

Implementation and validation evidence will be appended after the scoped checks. The active plan
remains open until independent review and integration. Do not create a real bundle, activate a real
binding, run real STL, or enter Phase 13.
