# CC-02D — Custodian Readiness Runbook

**Status:** Readiness implementation only. This document and its command do not authorize a
Rossmann source read, hash, partition, provider binding, STL run, or findings release.

## Fixed preparation procedure

The only accepted source is the documented snapshot at `data/raw/rossmann/train.csv`, with the
recorded identity **38,057,952 bytes**, SHA-256
`f6e4597c142d7d909a13d53b68a8e85c00b9a4c7b5ff40adbb37d6829cc1f4cc`. These are the accepted
reference identity values; this task has not checked them against local source bytes. Opening or
hashing this mixed CSV mechanically accesses protected-period bytes, including when the parser
later discards dates after 2015-07-03.

After the implementation PR is reviewed and integrated, the owner must approve the exact clean
execution commit and `uv.lock` SHA-256. The named custodian uses that commit, the locked environment,
the approved host and Windows account, and the fixed procedure below. The custodian does not change
the source path, source identity, projection, output root, preparation contract, or STL method.

The command defaults to no source access. Its sole production option is:

```powershell
python scripts/prepare_cc02_development.py --execute-once
```

It has no source-path, authorization-path, approval-reference, or output-path argument. Before
opening the source it checks the fixed packet, runtime and host, exact clean commit and lock hash,
expiry, exact documented source identity, three matching evidence-file hashes, and both immutable
output destinations. The destination preflight does not create output directories or temporary
files; it cannot prevent a filesystem race or prove that a later write will succeed. It then creates
a no-replace execution marker. That marker consumes the authorization even if the source read or
preparation later fails; do not delete it or retry under the same authorization. The only source
snapshot passed to preparation is the bytes read from the fixed path. The existing preparation code
verifies byte count and SHA-256, classifies dates before parsing Store or Sales, and emits only
Store/Date/Sales rows through 2015-07-03.

The fixed packet is ignored local data at
`data/authorizations/cc02_custodian_execution.json`. It has exactly these top-level fields:

| Field | Required contents |
|---|---|
| `schema_version` | Integer `1` |
| `execution_id` | New canonical UUID; never reused |
| `custodian` | `name`, current `windows_user`, and current `host_name` |
| `valid_until_utc` | Unexpired ISO-8601 timestamp with a UTC offset |
| `procedure` | Exact `commit` and `lock_sha256` approved by the owner |
| `source_snapshot` | Exact fixed path, recorded byte count, and recorded SHA-256 above |
| `artifact_id` | New lowercase identifier for the immutable output directory |
| `source_lineage_reference` | Same record ID as `evidence.source_access_approval.record_id` |
| `custodian_preparation_authorization_reference` | Same record ID as `evidence.preparation_approval.record_id` |
| `provider_loading_approval_reference`, `preflight_reference` | Reserved record IDs only; both gates remain separately pending until activated externally |
| `evidence` | `source_access_approval`, `custody_record`, and `preparation_approval`; each has `record_id` and lowercase SHA-256 |

The evidence files must be placed under
`data/authorizations/cc02_custodian/<execution_id>/` as `source_access_approval.json`,
`custody_record.json`, and `preparation_approval.json`. Their bytes must match the packet hashes.
The source-access record must name the custodian, the complete mixed-source snapshot and its
mechanical read/hash, the narrow preparation purpose and exclusions. The custody record must
document the fixed snapshot identity, source provenance, approved host and custody controls. The
preparation approval must name the exact commit, lock hash, one-time execution, 2015-07-03 cutoff,
three-field output, and accepted preparation contract.

The application checks record bytes and identity; it does **not** authenticate signers or prove
custody. Before preparing the packet, the trusted operator must verify the owner/custodian
signatures and confirm that each approval is current and covers this exact operation. Record IDs
or arbitrary approval strings by themselves never satisfy the evidence-file, runtime, identity,
expiry, and one-use checks. The owner and machine administrator remain trusted under ADR-027; this
is not an OS-enforced security boundary. The account comparison uses `getpass.getuser()`, which is
an environment-derived username hint, not authenticated Windows process-principal identity. The
trusted operator must independently verify the actual Windows principal and approved host before
creating the packet.

## GO / NO-GO authorization checklist

Stage A must be complete before opening or hashing the Rossmann file. Any missing, stale,
mismatched, or unverifiable Stage A item is **NO-GO**. Stage B applies only after successful
preparation; its approvals cannot be prerequisites to creating the partition.

### Stage A — Required before opening source

| Gate | GO evidence required |
|---|---|
| Named custodian | Owner names one human, Windows account, and approved host; the operator confirms the current identity matches. |
| Fixed source snapshot | Owner approves `data/raw/rossmann/train.csv` and the recorded 38,057,952-byte / `f6e4597c142d7d909a13d53b68a8e85c00b9a4c7b5ff40adbb37d6829cc1f4cc` identity. No alternate file or snapshot is substituted. |
| Mechanical source access | Owner explicitly authorizes the custodian to open and hash the entire mixed raw CSV, including protected-period bytes, solely to prepare the eligible development projection. This is not permission to inspect, summarize, model, or disclose protected values. |
| Accepted procedure | Owner approves the exact integrated execution commit, clean worktree, `uv.lock` hash, fixed CLI, one-use packet, and accepted CC-02C preparation behavior. |
| Custody evidence | Custodian documents source provenance and handling; trusted operator verifies the signed owner and custodian records and hashes them into the fixed packet. |
| Preparation permission | Owner separately approves this one-time preparation, output artifact ID, and cutoff/schema contract. No retry follows a consumed marker without a new authorization. |
| Runtime and destinations | Runtime matches the approved account/host, clean commit and lock; the execution ID is new and unused; both immutable output destinations are absent and pass the non-mutating preflight. |

### Stage B — Required only after successful preparation

| Gate | GO evidence required |
|---|---|
| Independent partition verification | Owner names and separately authorizes an independent verifier to inspect only the generated development bundle and receipt. The verifier records immutable Parquet, manifest, and receipt byte hashes; exact 17-field manifest; exact schema; row/store counts; sorting/uniqueness; and `date_max <= 2015-07-03`. |
| Exact-hash binding and provider loading | Only after verification passes, a delegated approver binds the exact immutable Parquet and manifest hashes and activates provider-loading/preflight references. Loading authority names the exact fixed bundle and does not include STL authority. |
| Real STL execution | Owner separately authorizes real CC-02 analysis after the approved development frame is loaded. Use `STL(period=7, robust=True)`, retain source zeros, split at sparse dates and missing/non-finite Sales, require 56 contiguous days, select the latest eligible segment by end date then start date, trim to its latest 112 rows, and choose the first three eligible Store IDs ascending. |
| Findings publication | Owner separately approves release of the verified tables, three eligible Store-level weekly figures when available, Store availability status, manifest, and evidence-based discussion. |

The current task leaves all real-data GO items unapproved. In particular, it does not name a
custodian, authorize mixed-source access, create the fixed packet, produce a real execution marker,
prepare a bundle, verify real partition files, bind the provider, run STL, or publish findings.

## Handoff after an authorized preparation

On success, preserve the command output and inspect only the immutable bundle at
`data/interim/cc02_development/<artifact_id>/` and its separate receipt at
`reports/generated/cc02_custodian/<artifact_id>/preparation_record.json`. The bundle must contain
only `sales.parquet` and `partition_manifest.json`; the manifest remains the accepted 17-field
CC-02B schema. The receipt and command output report the exact data and manifest hashes. Do not
edit the manifest to activate later approvals.

After separate owner authorization to inspect the already created development-only bundle and
receipt, the independent verifier runs this read-only content check with the locked environment.
It reads bounded regular-file snapshots, hashes and decodes the same in-memory Parquet bytes, and
cross-checks the manifest against the preparation receipt. It does not create a provider approval
binding or authorize provider loading or STL:

```powershell
@'
from dataclasses import asdict
from pathlib import Path
import re
from rossmann_forecasting.data import cc02_development as verification

artifact_id = "<artifact_id>"
if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", artifact_id):
    raise ValueError("replace artifact_id with the authorized immutable bundle ID")
root = Path("data/interim/cc02_development") / artifact_id
receipt_path = (
    Path("reports/generated/cc02_custodian") / artifact_id / "preparation_record.json"
)


def bounded_snapshot(path: Path, limit: int) -> bytes:
    verification._assert_regular_path_without_aliases(path)
    return verification._read_approved_bytes(path, max_bytes=limit)

data_bytes = bounded_snapshot(
    root / verification.DATA_FILENAME, verification.MAX_DATA_BYTES
)
manifest_bytes = bounded_snapshot(
    root / verification.MANIFEST_FILENAME, verification.MAX_MANIFEST_BYTES
)
receipt_bytes = bounded_snapshot(
    receipt_path, verification.MAX_PREPARATION_RECEIPT_BYTES
)
result = verification.verify_development_bundle_snapshot(
    data_bytes, manifest_bytes, receipt_bytes
)
if result.artifact_id != artifact_id:
    raise ValueError("verified artifact_id differs from the fixed bundle directory")
print(asdict(result))
'@ | .\.venv\Scripts\python.exe -B -
```

The verifier rejects duplicate manifest/receipt keys and nonstandard JSON constants; checks the
exact 17-field manifest, accepted physical and decoded schema, positive Stores, unique sorted
Store/Date keys, non-null midnight Dates through 2015-07-03, exact counts and date bounds; and
records SHA-256 for the Parquet, manifest, and preparation receipt snapshots. The operator compares
these results with the separately recorded preparation output and independently authenticated
owner/custodian evidence, including the fixed source path and recorded source identity in the
receipt, source lineage, custodian and preparation references, and exact procedure scope. The
application validates content relationships; it does not authenticate signers or establish custody.
Do not edit the manifest. Only after the independent verification record passes may a delegated
external approver issue a distinct exact-hash `DevelopmentInputApproval`
binding. Reserved reference IDs do not grant provider permission. Do not use the convenience
function that combines loading and STL while the separate STL gate is pending: first load through
the separately authorized provider, stop for STL authorization, then pass its returned copy-safe
frame and provenance to `decompose_development_sales`. Findings export waits for its own approval.

The analysis process receives only the verified development partition; it never reads or hashes
the mixed source. The academic output is descriptive weekly decomposition of monetary Store-level
Sales. It reports explicit Store selection and unavailable-Store reasons, and includes three
Store-level figures when sufficient histories exist. Discuss trend, weekly seasonality, and
residual behavior from the verified components only. Make no causal promotion claim and no
SKU-demand claim from store-level revenue. No CC-02 step changes Phase 13 or authorizes access to
its protected holdout.
