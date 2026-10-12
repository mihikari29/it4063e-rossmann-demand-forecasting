# CC-02D — Minimal Custodian Execution Readiness

**State:** **IMPLEMENTED / UNDER REVIEW** on `feat/cc-02d-stl-custodian-readiness`, based on
`13d762c0c622164ebf6a804ab0a1887c738bdbe8`. Real-data execution is not authorized.

## Scope

Connect the fixed-source custodian command to the accepted CC-02C byte-snapshot preparation
helper. Add a separately gated, single-use packet with exact source/procedure identity, named
operator and host, hash-matched source-access/custody/preparation evidence, expiry, and a no-replace
consumption marker. Keep provider binding, STL execution, and findings release independent. Do not
read or hash real Rossmann data or create an approval binding.

Archive CC-02C's plan now that PR #43 is integrated, update current progress, and provide the
concise operator/GO-NO-GO handoff.

## Design and acceptance

The production CLI accepts only `--execute-once`; packet, source, bundle, and receipt locations
remain fixed. It validates the accepted documented source identity and an exact clean Git commit
and lock hash before reading the mixed source. It consumes the authorization before source open and
delegates all filtering, schema, manifest, provenance, and no-replace publication behavior to the
accepted preparation implementation. Python validates the packet and evidence bytes but does not
authenticate signers; the owner-approved operator process remains the authority under ADR-027.

Tests use independently generated synthetic source bytes and temporary roots only. They cover the
valid one-use bridge, source identity mismatch, absent preparation/custody evidence, missing
provider binding, default/missing-packet behavior, and no provider/STL call during preparation.
Finish the focused tests, repository quality commands, docs checks, whitespace check, and full diff
self-review; archive this ordinary task plan after validation. Open one Draft PR, do not merge.

## Checkpoint

The focused CC-02/preparation/provider/STL regression selection passed 124 tests with two
Windows symlink-privilege skips. The full fixture suite passed 776 tests with two such skips and
one existing Starlette/httpx deprecation warning. Whole-repository Ruff, format, documentation,
lock, dependency-consistency, and whitespace checks passed. New execution tests use independent
synthetic CSV bytes and temporary directories only. No Rossmann source, real partition, external
approval packet/binding, provider loading, or STL run was accessed or created.

Current status and evidence are recorded in [`docs/PROGRESS.md`](../../docs/PROGRESS.md). The
real-source authorization checklist remains in the
[operator runbook](../../docs/CC-02D_CUSTODIAN_RUNBOOK.md). This ordinary task plan is archived
after validation. Commit `6ca830060d53bc182b831747e5f5947e5e71640d` was the initial
implementation/PR-opening checkpoint, not the current PR head. Independent Sol 6.1 reviewed live
Draft [PR #44](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/44) at
`93b29f9d4139ef79916bd23f2e3045b620c038eb` and returned REQUEST_CHANGES for CC02D-R01–R04. The
focused fixes and synthetic verification are in correction commit
`1e14be1a75a32bb4c3ab4265e88e060328eb2d60`; test and quality evidence is recorded in the current
[progress entry](../../docs/PROGRESS.md). CC-02D remains IMPLEMENTED / UNDER REVIEW pending focused
independent re-review and authorized integration. No real-data work is complete or authorized.
