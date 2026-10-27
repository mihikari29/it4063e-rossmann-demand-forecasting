# Public Demo Release Contract — Controlled Synthetic v1

**Status:** Milestone A implementation contract under the
[approved public-demo scope](DECISIONS.md#adr-030--narrow-public-course-demonstration-objective-and-synthetic-first-milestone-a).
This document describes an offline
release candidate. It grants no permission to publish its files or expose an application.

## Purpose and evidence label

The bundle demonstrates the shapes and interactions needed by the read-only catalog, history,
forecast, uncertainty, model-comparison and inventory-comparison services, covering the five
Streamlit screens. It uses the existing Store × Date monetary Sales interpretation and H14 calendar
horizon. It contains controlled synthetic fixture arithmetic only. Every release has
`evidence_kind = controlled_synthetic_demo`, release ID
`rossmann-course-demo-synthetic-v1`, schema version `1.0.0`, and fixed seed `4063`.

No value is an observed Rossmann Sales value, a Rossmann forecast, or a result from an executed
historical model. These examples do not claim observed forecasting performance, actual Rossmann
history, genuine empirical uncertainty calibration, real inventory quantities, actual stockouts,
realized savings, production deployment, or validated service-level guarantees. Monetary values are
synthetic retail-equivalent turnover values; no currency code is implied. Inventory cost proxies use
synthetic cost-proxy units. No SKU or physical unit is represented.

## Population and supported queries

The fixed illustrative population is Store IDs **101, 202 and 303**, with no mapping to actual
Rossmann stores. Forecast origins are **2015-05-22, 2015-06-05 and 2015-06-19**. Each origin has
horizons **1–14**, ending no later than the development cutoff **2015-07-03**. History is bounded to
**2015-05-09 through 2015-07-03** (56 calendar days maximum). It contains 165 rows: one date per
Store is intentionally absent, null Sales and zero Sales are retained as separate states, and one
synthetic Open eligibility value is null.

The query allowlist is closed and is duplicated in the manifest for identity checking:

| Service category | Supported query identities |
|---|---|
| Catalog and resource availability | `catalog()` with no arguments |
| Sales history | Stores 101/202/303; dates from 2015-05-09 through 2015-07-03; start on or before end; at most 56 inclusive calendar days |
| Forecast issuance | Full Store × origin × horizon product: 3 Stores × 3 origins × H1–H14 (126 rows) |
| Forecast uncertainty | Stores 101/202/303 paired with `demo_fit_a` at 2015-06-05 or `demo_fit_b` at 2015-06-19; H1–H14; display probabilities 0.90, 0.95 and 0.98 |
| Model comparison | Candidates `demo_path_a`, `demo_path_b`, `demo_path_c`; population `synthetic_open_label_rows`; window `synthetic_display_panel`; scopes `pooled`, `horizon`, `week_block`, `store`; metrics `mae`, `rmse`, `mape`, `wape`; maximum 500 rows |
| Inventory comparison | Cases `synthetic_demo_reference_20150605` and `synthetic_demo_adverse_20150605`; optional Store 101/202/303 |

May 22 has no uncertainty fit pairing and no uncertainty data is implied for that origin. Sparse
history dates are omitted rather than converted to zero. A returned row with `sales_value: null` is
different from an omitted date, and an observed synthetic zero is retained as numeric zero. Missing
or unavailable forecast inputs remain null with an explicit reason where the service view supports
one. An unavailable view is not an empty-but-successful result.

## Exact bundle content

`demo_bundle.json` is a canonical UTF-8 JSON object with these top-level fields only:

| Field | Meaning |
|---|---|
| `schema_version`, `release_id`, `evidence_kind` | Fixed version and synthetic evidence identity |
| `title` | `Controlled synthetic course demonstration` |
| `sales_unit`, `inventory_cost_unit` | `synthetic_retail_equivalent_turnover_value`; `synthetic_cost_proxy_units` |
| `source_declaration` | Authored fixture arithmetic, no Rossmann/source files/external datasets or model runs, no model execution, and no claim to redistribution rights for any source |
| `limitations` | Fixed scientific, source and service-claim exclusions |
| `populations`, `query_allowlist` | Exact Stores, origins, horizons, date bounds, pairings and query filters |
| `catalog` | Scenario labels, per-view availability, bounded record counts and a health/readiness distinction |
| `history_rows` | Synthetic history rows with Store, ISO date, nullable monetary `sales_value`, nullable Boolean `synthetic_open`, and `observation_state` (`value`, `zero_sales`, `null_sales`) |
| `forecast_rows` | Forecast rows with Store, origin, ISO target date, integer horizon, nonnegative raw forecast value/availability, `synthetic_open_eligibility` (`known_open`, `known_closed`, `unknown`), nullable operational forecast value/availability, fixed trajectory label and `model_execution: none` |
| `uncertainty_views` | Store, supported June origin/Fit label, view state and reason; 28 daily rows per view (raw and operational H1–H14) plus 42 cumulative rows (H1–H14 × three display probabilities) |
| `comparison_panel` | Three explicitly untrained fixed-arithmetic candidate labels; 126 synthetic comparison-basis rows; metric definitions; 69 pooled, horizon, week-block and Store comparison rows |
| `inventory_views` | Two fixed illustrative cases, each with three Store pair rows, ten aggregate metric rows, monetary inputs/outputs and per-policy measurement numerators/denominators; one adverse case has a genuinely unavailable Store 303 forecast-policy result |

History, forecast and comparison values are generated from fixed formulae and SHA-256 keyed
deterministic variation. The manifest records the fixed seed and configuration digest. Synthetic
forecast paths never use future labels. A known synthetic closure leaves the raw path intact and
routes the operational value to zero. Unknown future eligibility leaves the raw forecast available
and the operational forecast null/unavailable. One Store 303 / June 19 / H4 example demonstrates
unknown eligibility and makes that uncertainty interval unavailable; cumulative prefixes from H4
onward remain incomplete and null.

Daily display bands use fixed ±15% arithmetic around each available point (lower bound floored at
zero). Cumulative display buffers use fixed synthetic constants 80, 120 or 180 multiplied by prefix
days for the three probability labels. These are interface examples, not fitted or calibrated
quantiles. Synthetic comparison predictions are fixed arithmetic paths. Metrics use eligible
synthetic Open=1 rows: MAE is mean absolute error; RMSE is the square root of mean squared error;
MAPE is the mean absolute percentage error × 100 on positive synthetic Sales only; WAPE is total
absolute error divided by total synthetic Sales. Zero Sales remains eligible for MAE/RMSE/WAPE and
is excluded from MAPE. None of these rows is a Phase 7 model-selection result or a Rossmann
performance estimate.

Inventory policy names and values are fixture examples, not execution of Phase 10. Monetary
demand/fulfillment/unmet/target and inventory-state values use the synthetic retail-equivalent
turnover basis. Cost fields use synthetic cost-proxy units. `ValueFillRate`, stockout rate and
receipt-cycle service rate are dimensionless fixture ratios. Fixed case values are authored
arithmetic, not outputs of the inventory simulator. The adverse case includes positive
forecast-minus-baseline cost for available Store pairs; Store 303's missing input remains unavailable
and makes the case-level matched difference null because coverage is incomplete. No physical stock,
order quantities, ledger or equivalent SKU units are present.

The complete row counts are recorded in the manifest: 165 history rows, 126 forecasts, 6 supported
uncertainty views, 168 daily intervals, 252 cumulative rows, 126 comparison basis rows, 69 model
comparison rows, 2 inventory views, 6 inventory policy pairs and 20 inventory aggregate rows.

## Provenance, files and verification

`demo_manifest.json` records schema/release/evidence identities; generator module and script hashes;
configuration digest; Git revision when available; Python version; `pyproject.toml` and `uv.lock`
hashes; installed direct-dependency identities; fixed seed; bundle SHA-256 and byte count; row
counts; supported queries; population/origin/horizon definitions; source declaration; and
limitations. No canonical run ID, real source hash, model hash or protected content is included.

Only these two filenames are valid: `demo_bundle.json` and `demo_manifest.json`. Both use sorted-key,
compact canonical JSON with no trailing newline. The bundle is limited to 5 MiB and the manifest to
64 KiB encoded bytes before JSON decoding; decoded schemas, row counts, scalar types, finite numbers,
Store/date/horizon combinations, metrics, availability/null relationships and inventory arithmetic
are then checked. Duplicate object keys, additional fields, noncanonical encodings, symlinks, extra
files and unsafe output paths are rejected. Deterministic regeneration compares both complete files
under the recorded code/configuration/environment identity.

The ordinary verifier also recomputes the digest of the fixed generator configuration and validates
required source, lockfile, and installed-dependency identities as well as the optional Git revision
shape. It does not require those declared environment identities to equal the current verifier host;
deterministic regeneration performs that stronger comparison. Manifest byte counts must be bounded
JSON integers, not merely values that compare equal to an integer in Python.

Each required installed dependency version is limited to 128 ASCII characters and must
match this normalized PEP 440-compatible subset: an optional numeric epoch, a dotted numeric release,
at most one `aN`, `bN` or `rcN` pre-release, an optional `.postN`, an optional `.devN`, and an optional
`+` local version made of nonempty alphanumeric segments separated by `.`, `_` or `-`. Syntax is
checked locally without importing or adding `packaging` at runtime. Ordinary verification validates
the declared version syntax and manifest integrity; deterministic regeneration checks exact current
environment identity.

The manifest contains the bundle hash but cannot contain its own hash. An eventual release approval
must pin the exact manifest SHA-256 out of band and pass it to the verifier. A matching hash proves
byte identity only; it does not authenticate an approver, establish custody or grant publication
rights. The 5 MiB/64 KiB limits are encoded-size targets, not proof of a hard peak-memory limit.
Bundle readiness means these files passed offline verification; process health means only that a
future application process responds; and each analytical view has its own availability state. A
successful verifier returns `bundle_ready: true`; the manifest by itself does not claim readiness.
A future `/health` route must describe process health only, while catalog `view_availability` reports
the content state per view. These must remain separate in any later API/UI adapter.

## Exclusions and rights boundary

The bundle contains no raw or prepared Rossmann data, feature matrices, source-derived Sales,
Customers or Store characteristics, canonical forecasts/quantiles/comparison results, fitted models,
inventory ledgers, protected July 4–31 outcomes, authorization packets, credentials, file paths or
external downloads. The official competition materials inspected for the prior architecture review
did not establish redistribution permission. This synthetic bundle makes no license claim and does
not resolve rights for any later real-data excerpt. Any such excerpt would require separate source
access, content, rights and exact-hash approvals.

## Output isolation and later adaptation

The builder accepts only a new `artifacts/public_demo/rossmann-course-demo-synthetic-v1/` directory,
which is covered by the repository's ignored `artifacts/` convention. It rejects tracked collisions,
unsafe parents and existing releases. Before creating output, it checks existing path components for
symbolic links and Windows reparse-point aliases, and verifies resolved containment under the trusted
checkout root. The directory verifier applies the same checks before reading files. It writes to a
temporary sibling and renames the complete two-file directory atomically. It never overwrites an
existing candidate. These checks address static aliases in the controlled local workflow; they do
not claim protection against privileged concurrent filesystem replacement. Generated files stay
offline and untracked; the repository stores the schema, builder, verifier, tests and this contract.

Milestone B must adapt the approved bundle to the existing six typed service categories and five
screens. It may reuse DTOs where their meaning remains truthful. Existing `ArtifactProvenance` and
`ResourceStatus` encode canonical Phase/run identities; those fields must not be filled with synthetic
IDs as though they were canonical. Use a separately typed synthetic profile wrapper if the existing
DTO cannot preserve the evidence and availability distinctions. Streamlit must keep direct Python
service calls; the API and UI may share one immutable bundle/provider without making HTTP a required
path. The public profile must be explicit, keep localhost defaults unchanged, and have no fallback
to local canonical artifacts when its bundle is missing.

## Authorization boundary

The [public-demo scope decision](DECISIONS.md#adr-030--narrow-public-course-demonstration-objective-and-synthetic-first-milestone-a)
accepts the future two-URL objective and authorizes only offline synthetic Milestone A work.
The bundle is a private local release candidate, not `PUBLIC`, `RELEASED` or `COMPLETE`. Public
content approval, redistribution-rights review, Milestone B, independent staging/security review,
host selection/provisioning, purchases, deployment, public listeners and URL publication each remain
outside this authorization. The [localhost restrictions](DECISIONS.md#adr-024---phase-12-localhost-only-demonstration-boundary)
and the scientific, development-cutoff,
holdout, Phase 13, WP1-L4, monitoring and scenario-analysis boundaries remain in force.
