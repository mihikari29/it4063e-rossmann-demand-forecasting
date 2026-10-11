# CC-02B — Trusted Development-Only Sales Provider

**State:** Fixture-only implementation is **IMPLEMENTED / UNDER REVIEW**. Real-data operation is
not approved.

## Scope and accepted boundary

Implement one bounded loader for an already-created immutable CC-02 development-only partition.
The loader does not discover, prepare, filter, or authorize its input. The existing robust weekly
STL method, Store/segment selection, 2015-07-03 ceiling, forecasting contracts, and Phase 13 gates
remain unchanged. The command-line interface continues to fail closed.

The provider accepts a frozen `DevelopmentInputApproval` supplied by a trusted caller. Its purpose,
artifact ID, exact location, fixed filenames, expected data/manifest SHA-256 values, date ceiling,
source-lineage reference, custodian/preparation authorization reference, provider-loading approval
reference, and preflight reference are validated before either file is opened. The bundle location
is restricted to `data/interim/cc02_development/<artifact_id>/`; there is no globbing or fallback.

The approved manifest is pinned by the external binding and declares the artifact identity/purpose,
approval references, file hash and byte size, ordered fields/dtypes, row/store counts, sort order, and
date bounds. Only the manifest and exact approved Parquet file are read. The loader hashes each byte
snapshot once, decodes the same in-memory Parquet bytes it verified, enforces Store `int64`, Date
`datetime64[ns]` or `datetime64[us]`, and Sales `int64` or `float64`, and returns a copy-safe
`Store`, `Date`, `Sales` projection with accurate `InputProvenance`. The analysis manifest keeps
exact source-file hashes separate from its canonical projection hash.

The local limits are 128 MiB for Parquet, 64 KiB for its manifest, and 1.2 million rows. These
bound the intended small local input; larger provider needs require a separate reviewed change.
Float Sales nulls and non-finite values retain the existing segment-breaking behavior; zero Sales
and sparse dates are preserved. No interpolation, fill, or row removal is introduced.

The approval object is not an authority or proof of custody. Its origin must be a separately
reviewed operator process outside the bundle. Application checks can reject an unapproved path and
detect symlink/reparse aliases where supported, but cannot authenticate the approver or prove the
partition's physical contents and custody. Operating-system isolation and access controls are a
separate operational prerequisite. Real source access to create a partition requires a distinct
written authorization and custodian procedure; analytical release and findings publication remain
separate gates. This task grants none of them and does not modify ADR-027.

## Verification

Use synthetic Parquet bundles in temporary directories only. Test pre-read rejection, binding and
path checks, alias behavior, byte/hash and manifest mismatches, schema/content/cutoff validation,
Sales preservation, copy safety, and the existing STL/provenance integration. Run the focused suite
and the full fixture quality gate in an isolated checkout with no local Rossmann or generated
artifacts. Do not run source preparation, real-data STL, or Phase 13.

## Implementation checkpoint — 2026-10-11

The fixed-path approval loader, strict manifest/Parquet validation, copy-safe frame result, and
CC-02 provenance handoff are implemented. The CLI remains fail-closed and no source partition or
real-data approval is configured.

The focused provider and CC-02 suite passed 61 tests with one Windows symlink-permission skip. The
full suite passed 712 tests with two skips in a detached worktree without local data/artifacts and
one existing Starlette/httpx deprecation warning. Whole-repository Ruff, formatting, 309 Markdown
destinations/anchors, `uv lock --check`, and `git diff --check` passed. Independent review and
integration remain pending; see [PROGRESS](../../docs/PROGRESS.md).
