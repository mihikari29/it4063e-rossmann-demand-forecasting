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
opening the source it checks the fixed packet, current username and host, exact clean commit and
lock hash, expiry, exact documented source identity, and three matching evidence-file hashes. It
then creates a no-replace execution marker. That marker consumes the authorization even if the
source read or preparation later fails; do not delete it or retry under the same authorization.
The only source snapshot passed to preparation is the bytes read from the fixed path. The existing
preparation code verifies byte count and SHA-256, classifies dates before parsing Store or Sales,
and emits only Store/Date/Sales rows through 2015-07-03.

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
is not an OS-enforced security boundary.

## GO / NO-GO authorization checklist

Proceed only when every GO item is true and documented. Any missing, stale, mismatched, or
unverifiable item is **NO-GO**; stop before opening or hashing the Rossmann file.

| Gate | GO evidence required |
|---|---|
| Named custodian | Owner names one human, Windows account, and approved host; the operator confirms the current identity matches. |
| Fixed source snapshot | Owner approves `data/raw/rossmann/train.csv` and the recorded 38,057,952-byte / `f6e4597c142d7d909a13d53b68a8e85c00b9a4c7b5ff40adbb37d6829cc1f4cc` identity. No alternate file or snapshot is substituted. |
| Mechanical source access | Owner explicitly authorizes the custodian to open and hash the entire mixed raw CSV, including protected-period bytes, solely to prepare the eligible development projection. This is not permission to inspect, summarize, model, or disclose protected values. |
| Accepted procedure | Owner approves the exact integrated execution commit, clean worktree, `uv.lock` hash, fixed CLI, one-use packet, and accepted CC-02C preparation behavior. |
| Custody evidence | Custodian documents source provenance and handling; trusted operator verifies the signed owner and custodian records and hashes them into the fixed packet. |
| Preparation permission | Owner separately approves this one-time preparation, output artifact ID, and cutoff/schema contract. No retry follows a consumed marker without a new authorization. |
| Independent partition verification | After preparation, owner names and separately authorizes an independent verifier to inspect only the generated development bundle and receipt. Verifier records immutable Parquet and manifest byte hashes, exact 17-field manifest, exact schema, row/store counts, sorting/uniqueness, and `date_max <= 2015-07-03`. |
| Provider binding and loading | Only after the verification record passes, a delegated approver binds the exact immutable Parquet and manifest hashes and activates provider-loading/preflight references. Loading authority names the exact fixed bundle and does not include STL authority. |
| Real STL execution | Owner separately authorizes the real CC-02 analysis after the approved development frame is loaded. Use `STL(period=7, robust=True)`, retain source zeros, split at sparse dates and missing/non-finite Sales, require 56 contiguous days, select the latest eligible segment by end date then start date, trim to its latest 112 rows, and choose the first three eligible Store IDs ascending. |
| Findings publication | Owner separately approves release of the verified tables, three eligible Store-level weekly figures when available, Store availability status, manifest, and evidence-based discussion. |

The current task leaves all of these real-data GO items unapproved. In particular, the task does
not name a custodian, authorize mixed-source access, create the fixed packet, produce a real
execution marker, prepare a bundle, verify real partition files, bind the provider, run STL, or
publish findings.

## Handoff after an authorized preparation

On success, preserve the command output and inspect only the immutable bundle at
`data/interim/cc02_development/<artifact_id>/` and its separate receipt at
`reports/generated/cc02_custodian/<artifact_id>/preparation_record.json`. The bundle must contain
only `sales.parquet` and `partition_manifest.json`; the manifest remains the accepted 17-field
CC-02B schema. The receipt and command output report the exact data and manifest hashes. Do not
edit the manifest to activate later approvals.

The independently authorized verifier records both file hashes directly from the immutable
files, compares them with the manifest and preparation receipt, checks Parquet schema and contents,
and confirms the development cutoff. For example, after separate owner authorization to inspect
that generated bundle, the verifier can run this read-only check with the locked environment and
record its printed hashes and counts in the independent verification record:

```powershell
$bundle = 'data/interim/cc02_development/<artifact_id>'
Get-FileHash "$bundle/sales.parquet" -Algorithm SHA256
Get-FileHash "$bundle/partition_manifest.json" -Algorithm SHA256
$env:CC02_BUNDLE = $bundle
@'
import hashlib, json
import os
from pathlib import Path
import pandas as pd
import pyarrow.parquet as pq

root = Path(os.environ["CC02_BUNDLE"])
data_path, manifest_path = root / "sales.parquet", root / "partition_manifest.json"
data_bytes, manifest_bytes = data_path.read_bytes(), manifest_path.read_bytes()
manifest = json.loads(manifest_bytes)
expected = {
    "schema_version", "artifact_id", "purpose", "source_lineage_reference",
    "custodian_preparation_authorization_reference", "provider_loading_approval_reference",
    "preflight_reference", "data_file", "data_sha256", "data_bytes", "row_count",
    "store_count", "columns", "dtypes", "sort_order", "date_min", "date_max",
}
table = pq.read_table(data_path)
frame = table.to_pandas()
assert set(manifest) == expected and manifest["columns"] == ["Store", "Date", "Sales"]
assert manifest["data_file"] == "sales.parquet"
assert manifest["dtypes"] == {"Store": "int64", "Date": "datetime64[us]", "Sales": "int64"}
assert manifest["sort_order"] == ["Store", "Date"]
assert table.schema.names == ["Store", "Date", "Sales"]
assert [str(field.type) for field in table.schema] == ["int64", "timestamp[us]", "int64"]
assert hashlib.sha256(data_bytes).hexdigest() == manifest["data_sha256"]
assert len(data_bytes) == manifest["data_bytes"] == data_path.stat().st_size
assert len(frame) == manifest["row_count"] and frame["Store"].nunique() == manifest["store_count"]
assert frame["Store"].notna().all() and frame["Store"].gt(0).all()
assert not frame.duplicated(["Store", "Date"]).any()
assert frame.equals(frame.sort_values(["Store", "Date"], kind="stable", ignore_index=True))
assert frame["Date"].min().date().isoformat() == manifest["date_min"]
assert frame["Date"].max().date().isoformat() == manifest["date_max"] <= "2015-07-03"
print({"data_sha256": hashlib.sha256(data_bytes).hexdigest(),
       "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
       "rows": len(frame), "stores": frame["Store"].nunique(),
       "date_max": manifest["date_max"]})
'@ | .\.venv\Scripts\python.exe -B -
Remove-Item Env:CC02_BUNDLE
```

The verifier also compares the printed manifest hash and data hash with the separate preparation
receipt and command output. The printed hashes must be exactly the identities in the independent
verification record; do not edit the manifest. A delegated external approver then issues a distinct
`DevelopmentInputApproval` binding for those exact hashes and fixed bundle path. Reserved reference
IDs do not grant provider permission. Do not use the convenience function that combines loading
and STL when the separate STL gate is pending: first call the approved provider loader, stop for
the separate STL authorization, then pass its returned copy-safe frame and provenance to
`decompose_development_sales`. Findings export waits for its own approval.

The analysis process receives only the verified development partition; it never reads or hashes
the mixed source. The academic output is descriptive weekly decomposition of monetary Store-level
Sales. It reports explicit Store selection and unavailable-Store reasons, and includes three
Store-level figures when sufficient histories exist. Discuss trend, weekly seasonality, and
residual behavior from the verified components only. Make no causal promotion claim and no
SKU-demand claim from store-level revenue. No CC-02 step changes Phase 13 or authorizes access to
its protected holdout.
