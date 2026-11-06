# Descriptive forecast monitoring

The local adapter in [monitoring.py](../src/rossmann_forecasting/monitoring.py) supports authorized
retrospective development forecasts and controlled synthetic fixtures. It does not read source
files, fit models, implement Phase 13 M5 or demonstrate post-deployment performance. No new real
sales observations exist in this work. The older target-derived pseudo-LightGBM predictions,
mislabeled KS statistic and unimplemented three-day rule have been removed.

## Input and information contract

Supply already-authorized in-memory records to `pair_forecasts` or `build_monitoring_summary`.
The adapter is deliberately not a general filesystem importer. A genuine-artifact caller must
first authenticate immutable issuance/provenance and obtain purpose-specific data permission;
a supplied receipt hash cannot establish either. No real artifact was loaded in this task.

| Record | Required fields and rules |
|---|---|
| Forecast | `Store` integer 1..1115; `forecast_origin`, `issued_on`, `training_through`, `features_available_on`, `target_date` ISO dates; `horizon` integer 1..14; nonnegative finite `prediction` or null; bounded `model_id`, `issuance_id`; lowercase `issuance_sha256`; `evidence_kind`; `features` |
| Issuance chronology | `issued_on == forecast_origin`; training/features available no later than origin; target exactly origin+horizon; issuance no later than as-of; every date ends by July 3, 2015 |
| Label | Unique `Store`, `target_date`; `available_on` between target and as-of; nonnegative finite `actual_sales` or null; `source_open` exactly 0, 1 or null |
| Identity | One model/evidence kind per call; same issuance ID has consistent origin/training/model/hash; unique Store/origin/horizon keys; duplicate or unmatched label keys rejected |
| Evidence kind | `retrospective_development_forecast` or `controlled_synthetic_fixture`; fixtures require a `synthetic_` model ID |
| Feature declarations | Only `DayOfWeek` (1..7), planned `Promo` and `SchoolHoliday` (0/1), or null. Availability is a declared assumption, not proven by the snapshot. No Sales, Customers, source Open, reconstructed actual lag or arbitrary columns |

Issuance validation finishes before label pairing. Labels must already be available as of the
assessment; future supplied labels are rejected. Missing labels remain absent; future target
outcomes never generate predictions. Overlapping origins retain distinct forecast pairs and
may share a subsequently available Store/date label; pooled rows are forecast-label pairs,
not independent observations. Receipt hashes are upstream references, not recomputed row hashes.
The fixture's issuance content digest is created before the separate label stage.

## Populations, windows and interpretation

The adapter reuses [accepted metric arithmetic](../src/rossmann_forecasting/forecasting/metrics.py).
Primary MAE/RMSE use available raw forecasts paired with observed source Open=1. MAPE is a percent
on strictly positive actuals, reports excluded zero rows, and is unavailable without a valid
denominator. WAPE is a ratio of absolute-error total to positive actual-value total. Closed
labels and closed/positive-Sales conflicts are counted separately, never used to route the raw
path or improve raw errors. Unknown Open remains unknown.

Reports include requested forecast keys/availability, observed labels, missing actuals, eligible
rows and observed-target/open-label coverage. Missing forecasts remain in coverage denominators.
Store, origin and horizon summaries accompany pooled daily and trailing 7/14-calendar-day views.
Startup windows are partial; absent labels do not shorten a calendar window or become zero.
Reference dates precede current dates without overlap. Feature populations are issued requested
keys, including keys without labels; reference/current counts and missingness are explicit.
Quartiles, median differences and category frequencies are descriptive, without a KS test,
p-value or drift threshold. Fewer than two nonnull feature values gives `INSUFFICIENT_SAMPLE`;
constant reference values (one distinct nonnull value) are identified without division by zero.
Even larger populations
do not establish statistical reliability.

`DESCRIPTIVE_ONLY`, `PARTIAL_EVIDENCE` and `UNAVAILABLE` describe evidence availability. None means
healthy production. JSON, HTML and the chart share one calculation payload, timestamp and windows.
Human review inspects provenance, quality, coverage and changes, then records a disposition under
a separately approved process. No numeric warning, persistence rule, automatic retraining or
promotion is activated. [The proposed broader policy](PROPOSAL.md#242-proposed-operational-alerts-and-human-retraining-review)
retains its own approval and development-rehearsal gates. It cannot adapt the frozen final replay.

## Reproduction and outputs

```powershell
uv run --locked python scripts/generate_monitoring_artifacts.py --output-dir reports/generated/monitoring/submission-v1
```

Use a new directory for every run. This command authors calendar/store-based predictions before
independently authoring labels, without any LightGBM execution or actual Rossmann records.
Outputs are `issued_forecasts.json`, `available_labels.json`, `monitoring_summary.json`,
`monitoring_report.html`, `rolling_mae.png` and `manifest.json`. The manifest binds input/output
hashes, source code hashes/revision/dirty state, command/configuration, deterministic seed policy,
Python/packages/platform and lock identity. Generated files remain ignored.

[The notebook](../notebooks/03_model_monitoring.ipynb) calls the same reusable API and displays
the same summary, strata and feature comparisons. Evidently is unnecessary for this scope and
is not imported or added to the lock. Final replay monitoring, real observed post-deployment
performance and a validated human trigger policy remain incomplete.
