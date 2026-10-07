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

Phase 10's [active design proposal](../plans/active/phase-10-inventory-simulation.md) is
**PROPOSED / AWAITING APPROVAL; IMPLEMENTATION NOT STARTED**. Future ignored immutable runs would
use `data/processed/inventory_simulation/<run_id>/` with `simulation_config.json`,
`policy_targets.parquet`, `simulation_ledger.parquet`, `policy_summary.parquet`,
`comparison_summary.csv`, `validation_summary.json` and `manifest.json`. No such artifact or
simulator command is generated/implemented by this documentation proposal.

The future contract requires explicit ordered schemas/keys/nulls, byte and logical hashes, pinned
Phase 7/8/9 identities, staged reread/validation, upstream recheck, manifest-last and atomic
publication. Existing run IDs remain immutable; current.json advances only on complete success.
Failure preserves prior runs/pointer. Verify development date boundaries before whole-file
hashing; never hash full protected source data. Targets exclude evaluation outcomes, and the
approved upstream scenario/forecast artifacts are not modified or regenerated. Full schema,
availability and terminal-exposure requirements are in the proposed plan, not an implemented output.

For later models, use `data/processed/<model>/` for generated tabular evidence and
`artifacts/<model>/` for model binaries; both conventions are ignored. These are directory
conventions, not claims that later-phase outputs already exist. Commit reusable code, concise
verified findings, and generation instructions rather than datasets or binaries.
