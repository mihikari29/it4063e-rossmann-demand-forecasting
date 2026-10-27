# Local Data and Generated Outputs

Keep sources, derived tables, models, credentials, authorization packets and temporary outputs
local and Git-ignored. Commit reusable code, definitions, reviewed findings and generation
instructions. Raw files are immutable; never use `data/raw/` for transformed output.

## Layout

| Location | Producer and contents |
|---|---|
| `data/raw/rossmann/` | Official immutable `train.csv`, `test.csv`, `store.csv`, `sample_submission.csv` |
| `data/interim/` | `prepare_data.py`: joined `train.parquet`, `test.parquet`, separate `test_open_resolution.parquet` and preparation manifest |
| `data/processed/` | `build_features.py`: historical/inference features and feature manifest |
| `data/processed/seasonal_naive/` | Weekly development forecasts, coverage and metrics |
| `data/processed/holt_winters/` | Statistical forecasts/internal paths, fit/clipping diagnostics and paired metrics |
| `data/processed/lightgbm/` | Bounded tuning, development forecasts, diagnostics and comparisons |
| `artifacts/lightgbm/` | Serialized model state |
| `data/processed/model_selection/` | Frozen recipe/refit instructions, comparisons, selected forecasts/residual paths |
| `data/processed/uncertainty/<run_id>/` | Daily/cumulative quantile tables, assessment outputs and diagnostics |
| `data/processed/synthetic_inventory/<run_id>/` | Scenario config/catalog, anchors, parameters, daily context and upstream bindings |
| `data/processed/inventory_simulation/<run_id>/` | Simulation config, targets, ledger, policy/comparison/validation summaries and manifest |
| `reports/validation/`, `reports/eda/` | Source-quality and historical descriptive exports |
| `reports/generated/seasonal_decomposition/` | Authorized component/status tables, figures and analysis manifest |
| `artifacts/public_demo/` | Offline controlled synthetic two-file release candidate, never automatically published |

## Reproducibility commands

Use the [locked environment](../README.md#installation-and-quick-start). These commands document
supported operations; they do not grant data-access or regeneration permission. Source-wide
validation/preparation/EDA and default feature generation contact protected-period bytes and need
their applicable authorization. Follow [acquisition](../docs/DATA_ACQUISITION.md) first.

```powershell
python scripts/validate_data.py --report reports/validation/rossmann.json
python scripts/prepare_data.py
python scripts/build_features.py
python scripts/run_eda.py
python scripts/run_seasonal_naive.py
python scripts/run_holt_winters.py
python scripts/run_lightgbm.py
python scripts/run_model_selection.py --operational-review configs/phase-7-operational-review-v1.json
python scripts/run_forecast_uncertainty.py
python scripts/generate_inventory_scenarios.py --run-id <unused-id>
python scripts/run_inventory_simulation.py --run-id <unused-id>
```

Development model readers filter Date ≤ July 3, 2015 before labels reach evaluation, and history
stops at each origin. Prepared train contains the protected final period. Default feature inference
uses Kaggle covariates at July 31, not a development-origin input; changing the origin alone does
not supply development target covariates. See [model integration](../docs/FEATURE_CONTRACT.md#model-integration).
The notebooks reproduce historical full-source descriptive analysis, not an approved development gate.

Model selection validates cached candidate evidence without fitting. Its versioned operational
review input approves the scoped offline CPU demonstration, not production runtime. Missing review
produces `operational_review_required` rather than selected-model artifacts. Uncertainty consumes
verified development outputs without source reads or model fits; accepted Fit B values remain frozen.
Scenario generation reads only censored 56-day history through June 5/June 19 and verified safe
upstream lineage. Inventory freezes targets before outcomes and does not regenerate scenarios.
Numerical findings and limitations are in [results](../docs/PROGRESS.md).

## Immutable publication and provenance

Run directories refuse overwrite. Producers stage and reread/validate outputs, recheck authorized
inputs, write `manifest.json` last and publish atomically. An ignored `current.json` pointer advances
only after complete success; earlier artifacts remain immutable after failure or later review.
New manifests record command/configuration, source/output identities, code revision, seed where
applicable, environment and lock identity, schemas/counts and availability. Exact accepted runtime
pins remain in code and structured bindings; do not rewrite historical flags or use a mutable latest
pointer in place of required pins. Do not hash a mixed protected source merely to refresh provenance.

## Development-only STL inputs

The [custodian runbook](../docs/CC-02D_CUSTODIAN_RUNBOOK.md) owns the one-use source-access packet,
independent verification, reference activation and separate provider/STL/publication approvals.
No real bundle, approval binding or Rossmann decomposition is established.

The fixed bundle is `data/interim/cc02_development/<artifact_id>/`, containing only `sales.parquet`
and `partition_manifest.json`. Provider representations are Store int64, timezone-naive midnight
Date timestamp[ns/us] and Sales int64/float64; preserve float null/nonfinite segment breaks and zeros.
Admission limits are 128 MiB data, 64 KiB manifest and 1.2 million rows. The provider verifies the
pinned manifest and exact data snapshot, then returns copy-safe Store/Date/Sales with provenance.
These checks do not authenticate an approver or establish administrator-proof physical isolation.

```powershell
python scripts/prepare_cc02_development.py --describe-input-contract
python scripts/run_seasonal_decomposition.py --describe-input-contract
```

The commands describe requirements without source reads. Preparation requires separately approved
`--execute-once` with the fixed packet `data/authorizations/cc02_custodian_execution.json` and
evidence under `data/authorizations/cc02_custodian/<execution_id>/`. The separate receipt is
`reports/generated/cc02_custodian/<artifact_id>/preparation_record.json`. Source access consumes
a no-replace marker even on later failure. A failed receipt leaves a published bundle unbound;
reconcile explicitly. Interrupted preparation may leave inert `.stage-<artifact_id>-*` output;
there is no startup cleanup sweep. Never substitute combined prepared train or feature artifacts.

Independent verification must precede external exact-hash provider binding. Reserved reference IDs
are pending, without permission. Provider loading, STL and findings release are separate gates.
The operator/custodian and machine owner/admin are trusted; optional Windows identities/ACLs do not
follow from Python checks. Source preparation is distinct from Phase 13 staging/analytical release.
