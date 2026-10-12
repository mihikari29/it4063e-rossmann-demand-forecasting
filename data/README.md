# Local Data Layout

The official Rossmann Store Sales competition files belong in:

```text
data/raw/rossmann/
|-- train.csv
|-- test.csv
|-- store.csv
`-- sample_submission.csv
```

All files under `data/raw/` are local, ignored, immutable source artifacts. Do not edit them, commit
them, or use this directory for transformed output. The acquisition command creates the complete
directory atomically and refuses to overwrite an existing directory. The validation command reads
the files and verifies that their SHA-256 checksums remain unchanged.

Follow [the acquisition guide](../docs/DATA_ACQUISITION.md). Later implemented stages generate:

| Location | Contents and producer |
|---|---|
| `data/interim/` | Phase 2 `train.parquet`, `test.parquet`, separate `test_open_resolution.parquet`, and preparation manifest; `scripts/prepare_data.py` |
| `data/processed/` | Frozen `features_train.parquet`, `features_inference.parquet`, and feature manifest; `scripts/build_features.py` |
| `data/processed/seasonal_naive/` | Development forecasts, window/pooled/horizon metrics, coverage, and manifest; `scripts/run_seasonal_naive.py` |
| `data/processed/holt_winters/` | Development forecasts, internal paths, diagnostics, standalone/paired metrics, coverage guardrail, and manifest; `scripts/run_holt_winters.py` |
| `data/processed/model_selection/` | Phase 7 comparison, approved operational review decision, selected development forecasts/residual paths, recipe, and manifest; `scripts/run_model_selection.py` |
| `data/processed/uncertainty/<run_id>/` | Immutable Phase 8 daily/cumulative quantile tables, assessment intervals, diagnostics, configuration, and manifest; `scripts/run_forecast_uncertainty.py` |
| `reports/validation/`, `reports/eda/` | Reproducible source-quality reports and descriptive EDA exports |

These tables, reports, and manifests are local Git-ignored generated outputs, not committed data.
Preserve raw inputs and source nulls; regenerate derived artifacts through scripts. Prepared train
contains the protected final-period labels, so modeling must filter development reads before
evaluation. The default feature inference artifact uses Kaggle future covariates and origin
2015-07-31; see the [feature handoff](../docs/FEATURE_CONTRACT.md#handoff-to-phase-6-modeling) before
using any artifact for modeling.

Phase 8 writes a new run directory and its `manifest.json` last. On success, the ignored
`data/processed/uncertainty/current.json` pointer identifies the latest published run. A failed run
does not replace that pointer or modify earlier runs. The uncertainty command consumes verified
Phase 7 development outputs only; it never reads raw/interim source data or the protected holdout.

Phase 9's [completed design and plan](../plans/completed/phase-9-synthetic-inventory.md) is
integrated and formally complete. The accepted canonical run is
`phase9-dev-20261007-config-validation-fix` with manifest SHA-256
`573e36efddef452df781994c43f76006e208ec8c588b4c47e46735530da34761`; it is an existing immutable
local artifact and was not regenerated during closeout. To create a separate run, use a new
unused run ID, for example `phase9-dev-20261007-example`, with
`python scripts/generate_inventory_scenarios.py --run-id phase9-dev-20261007-example`. The command
publishes immutable scenario/config/anchor/parameter/context/binding/validation/manifest artifacts under
`data/processed/synthetic_inventory/<run_id>/`; a successful run updates its ignored
`current.json` pointer. The generator projects and censors the 56-day history at each scenario
origin and hashes only that safe projection; it verifies frozen Phase 7/8 identities and date
boundaries before hashing upstream files. Existing run IDs cannot be overwritten. These outputs
remain ignored local artifacts. Phase 9 introduces no model artifact, inventory ledger, order queue
or policy comparison.

Phase 10's [completed plan](../plans/completed/phase-10-inventory-simulation.md) and ADR-023 record
the accepted method and closeout. PR #23 integrated the implementation at
`15bce83cd63a4edfeed6defb95788da90d0f36d9`; PR #24 integrated the B1-B3 corrections at
`fcbf6b7de79d57bb7db8a965d5a2b78e9376a3a9`. The final independent external/model-assisted review
accepted the corrective implementation and numerical evidence; details and canonical results are in
[PROGRESS](../docs/PROGRESS.md). The accepted run is `phase10-dev-20261008-validator-fix` with
manifest SHA-256 `1c914b8a0fc7582c192f24fb8286e8521669cc079162cf832a58f2d8a1569f16`. Its seven ignored
files are `simulation_config.json`, `policy_targets.parquet`, `simulation_ledger.parquet`,
`policy_summary.parquet`, `comparison_summary.csv`, `validation_summary.json` and `manifest.json`.
It contains 383,560 targets and summaries, 5,753,400 ledger rows, 172 cases and 1,720 comparisons.
These are conditional simulated monetary-turnover values, not observed inventory, physical demand or
savings. Phase 10 formal completion takes effect when this closeout PR is integrated into `main`.

The implementation records explicit ordered schemas/keys/nulls, byte and logical hashes, pinned
Phase 7/8/9 identities, staged reread/validation, upstream recheck, manifest-last and atomic
publication. Existing run IDs are immutable; `current.json` advances only on complete success.
Failure preserves prior runs/pointer. Development date boundaries are checked before outcome hashing;
protected dates and the full raw source file are not accessed/hashed. Targets exclude evaluation
outcomes, and approved upstream scenario/forecast artifacts are not modified or regenerated. No final
holdout evaluation occurred. Phase 11 remains NOT STARTED / NOT AUTHORIZED.

For later models, use `data/processed/<model>/` for generated tabular evidence and
`artifacts/<model>/` for model binaries; both conventions are ignored. These are directory
conventions, not claims that later-phase outputs already exist. Commit reusable code, concise
verified findings, and generation instructions rather than datasets or binaries.

The CC-02 seasonal-decomposition exporter uses ignored
`reports/generated/seasonal_decomposition/` for component/status CSVs, four-panel Store figures,
and a manifest. The manifest identifies direct Python API execution or preserves an explicitly
caller-supplied invocation, while recording the exporter entry point and output hashes. Figures
label their source as a synthetic fixture or development-only input according to caller provenance.
Each export requires a new or empty destination and refuses to overwrite an existing run.
The fixture-tested provider API is implemented in
`src/rossmann_forecasting/data/cc02_development.py`. It accepts only a trusted, externally issued
approval binding for one exact bundle under `data/interim/cc02_development/<artifact_id>/`, with the
fixed files `sales.parquet` and `partition_manifest.json`. It hashes the pinned manifest before the
partition, checks the exact approved Parquet bytes, strict three-column schema, row/store counts,
date bounds and provenance references, then decodes the same in-memory byte snapshot it hashed.
Supported representations are Store `int64`, timezone-naive Date `datetime64[ns]` or
`datetime64[us]`, and Sales `int64` or `float64`; null/non-finite float Sales and observed zeros are
preserved. The 128 MiB partition, 64 KiB manifest and 1.2 million row limits bound local memory.
The returned frame is copy-safe and its exact partition/manifest byte hashes remain separate from
the CC-02 canonical in-memory projection hash.

These Python checks enforce an application-level allowlist and detect path aliases where the
operating system exposes them. They do not authenticate an approver, prove custody or guarantee
physical isolation against a privileged process. CC-02D adds a default-deny one-use preparation
path. Its ignored fixed packet is `data/authorizations/cc02_custodian_execution.json`; three
hash-matched evidence records belong under
`data/authorizations/cc02_custodian/<execution_id>/`. The packet is checked against the documented
source identity, named Windows account/host, exact clean code commit and lock hash, expiry, and a
no-replace run marker before the fixed source can be opened. The external trusted process must
authenticate the approver and verify the signed records; Python does not. This task created no
packet, real partition or real-data approval. The command remains fail-closed unless explicitly
invoked with `--execute-once` and a complete, externally approved packet. Mechanical source access
and analytical release are distinct approval gates.
Never create the partition by reading/filtering `data/interim/train.parquet`; do not fall back to
raw or feature artifacts.

CC-02C adds fixture-tested preparation helpers in
`src/rossmann_forecasting/data/cc02_preparation.py`. CC-02D connects them to the fixed-source
custodian command `python scripts/prepare_cc02_development.py --execute-once`, which is opt-in and
requires the packet described above. No real bundle currently exists. A future custodian read of
the mixed `train.csv` mechanically accesses bytes from the protected period, including when
chunked, and requires a distinct written authorization. Preparation, independent bundle
verification, provider loading, STL execution and findings publication are separate gates. The
output manifest keeps the exact CC-02B provider schema; additional command, code, lock and
environment provenance belongs in ignored
`reports/generated/cc02_custodian/<artifact_id>/preparation_record.json`.

Provider and preflight reference IDs may be reserved before preparation, but pending records grant
no permission. After preparation, an independently authorized verifier checks the bundle and an
external delegated approver binds its exact data and manifest hashes. The bundle's separate path,
application checks and date ceiling do not establish OS-enforced isolation. The local claim trusts
the custodian/operator and machine owner/administrator; Windows identity and ACL separation is
optional hardening. No Phase 13 or final-holdout access is authorized by the CC-02 workflow.
