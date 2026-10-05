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
| `reports/validation/`, `reports/eda/` | Reproducible source-quality reports and descriptive EDA exports |

These tables, reports, and manifests are local Git-ignored generated outputs, not committed data.
Preserve raw inputs and source nulls; regenerate derived artifacts through scripts. Prepared train
contains the protected final-period labels, so modeling must filter development reads before
evaluation. The default feature inference artifact uses Kaggle future covariates and origin
2015-07-31; see the [feature handoff](../docs/FEATURE_CONTRACT.md#handoff-to-phase-6-modeling) before
using any artifact for modeling.

For later models, use `data/processed/<model>/` for generated tabular evidence and
`artifacts/<model>/` for model binaries; both conventions are ignored. These are directory
conventions, not claims that later-phase outputs already exist. Commit reusable code, concise
verified findings, and generation instructions rather than datasets or binaries.
