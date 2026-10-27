# Store-Level Forecast Scenario Comparison

**Incomplete.** Common-population alignment (L1), metric summaries (L2), restricted fixture
verification (L3-F), fixture preparation/reference verification and the copy-safe fixture provider
are reviewed/integrated. No real-data scenario analysis has run. This plan retains the accepted
comparison/input contracts and remaining approvals, without reopening model selection.

## Objective and scientific boundary

Explain where the three frozen candidates differ on the three approved H14 development windows:
May 22, June 5 and June 19 origins, ending by July 3. Use monetary Sales, primary common-row MAE,
coverage/missingness/support and supplementary metrics. Preserve sparse observed keys, labels,
raw forecasts, masks and original failure reasons. LightGBM need not lead every stratum.

Use `forecasting/model_selection.py` candidate validation and `forecasting/validation.py` origins.
Do not read/hash real sources, cached forecasts or protected July 4–31 outcomes under fixture
approval. Static metadata and historical Promo grouping do not prove origin-time availability or
causal effects. Volume segmentation remains **BLOCKED**; competition bins, interactions, new
origins and cross-model inventory comparisons need their own accepted scope.

## Remaining work and approval gates

| Stage | Required outcome | Gate |
|---|---|---|
| Real preparation | Named custodian, source identities, approved dates/fields/purpose, isolated output and provenance | Separate source-access/preparation/custody authorization before mixed-source reads/hashes |
| Independent real verification | Source-observed roster, exact candidate/label identity, metadata completeness and integrity | Separate reviewed real decoder/process design; existing fixture verifier is unsuitable |
| External binding/provider | Effective exact-input binding issued through trusted operator process | Independent verification and explicit loading authorization; a record alone grants no permission |
| Analysis | Frozen permitted strata/support/availability rules, common-row comparisons and interpretation | Separate L4 execution authorization and independent Sol 6.1 result review |
| Delivery | Reviewed findings, failures, limitations and human ownership/AI disclosure | Required course acceptance and any publication permissions |

Reuse this plan for the next concrete operation. Fixture support is not a real-source path, and
none of these gates authorizes Phase 13, public deployment or a new model-selection experiment.

## Approved L1 scope

Implement a pure in-memory population builder for synthetic fixtures. It must call the public
`validate_candidate_records` Phase 7 validator, use its normalized records, align the exact three
approved candidates on `(Store, forecast_origin, Date)`, and preserve all observed target keys.
Produce label-only eligibility, each candidate's raw forecast, availability/reason and standalone
eligibility, plus exact three-way common eligibility. Derived standalone masks must agree with the
Phase 7 accepted eligibility masks or fail closed. Sort deterministically and leave input frames
unchanged.

Approved origins are 2015-05-22, 2015-06-05, and 2015-06-19, with targets ending no later than
2015-07-03. Sparse observed target keys remain sparse. Open=1 with zero Sales is an eligible label;
closed, unknown-Open, and missing-Sales rows remain in the output but are ineligible. This milestone
adds no scenario fields, joins, metrics, forecast generation, file access, hashes, or publication.

## Approved L2 scope and execution plan

L2 accepts in-memory output from `build_scenario_population` as its sole population authority. Its
adapter requires the exact 21-column L1 schema, rebuilds the three candidate views, calls the
unchanged L1 builder, and rejects any key, label, availability, reason, or eligibility-mask
mismatch. All summaries use the regenerated canonical population. L2 does not add a second
candidate or forecast validator and does not change Phase 7.

Optional in-memory scenario membership uses the exact observed `(Store, forecast_origin, Date)` key
set and only the approved `Promo`, `StoreType`, `Assortment`, `StateHoliday`, and `SchoolHoliday`
columns. A missing keyed record is an integrity error; a null cell is a missing category. Static
StoreType and Assortment values must remain consistent per Store. Known codes are normalized only as
specified by the accepted design; unknown nonempty text codes remain distinct unrecognized levels.

Reporting includes pooled development and each of the three approved origins. Every scope declares
all rows, H1-H14, H1-H7/H8-H14, and ISO weekday 1-7. Enabled metadata dimensions report all known,
missing, and observed unrecognized levels independently, with no interactions. Empty strata remain
present. Support and coverage preserve observed sparse keys and distinguish target, label, forecast
availability, standalone, and exact common populations.

Primary metrics and all three fixed comparisons use the same three-way common rows. L2 stores
additive sufficient statistics and derives MAE, RMSE, WAPE, and directional summaries from pooled
sums. Undefined values remain null with reasons; no epsilon, MAPE change, winner rule, or selection
policy is introduced. The serializer returns deterministic UTF-8 JSON bytes in memory and performs
no file I/O.

## Fixture preparation and provider

`data/wp1_preparation.py` projects synthetic CSV bytes to approved target windows, validates
original candidate horizons before narrowing and creates complete keyed retrospective Promo
membership. `data/wp1_development.py` constructs deterministic snapshots and checks them against
an independently supplied synthetic source reference. Preserve original numeric labels until
exact source comparison: adjacent integers above 2**53 must remain distinct.

Store accepts only Python/NumPy integer keys in 1..2**63−1 (no Boolean/float/string coercion).
Sales accepts nonnegative int64/finite float64 or missing; Open accepts exact numeric 0/1 or
missing. Exact numeric equality permits 20 and 20.0, without tolerance. Authorization declarations
require actual JSON Booleans. Sparse/null/zero observations remain distinct.

`load_wp1_fixture_provider` requires a separately supplied frozen `WP1FixtureBinding` and exact
fixture context. Each load reruns independent verification, checks all candidate/raw/payload
identities and re-decodes through existing validators. Accessors return deep copies. Only Promo
is enabled; StoreType/Assortment source approval is deferred and H remains disabled. No filesystem,
real-data loader, CLI, authorization issuer, automatic L1/L2 execution or publication path exists.

Provider admission limits are 64 MiB per source reference/payload, 1 MiB manifest, 256 KiB receipt,
128 MiB combined handoff and 50,000 rows. Declared schemas/counts are screened before decode and
actual counts afterward. Inputs already exist in memory; these are practical limits, without hard
process-memory containment or authenticated custody.

## Restricted fixture verifier and unresolved resource requirement

Only `verify_trusted_scenario_fixture_snapshot` is supported, on reviewed project-controlled
synthetic fixture-generator bytes and controlled mutations. The caller precondition cannot be
authenticated by Python. The former generic verifier was removed without alias. Successful
results retain immutable limitations covering fixture-only conformance, unauthenticated
origin/custody, unverified historical availability/real-roster completeness, no real-source
permission, no hard peak-memory guarantee and no analysis authority.

Arrow output checks run **after materialization**; untrusted footer estimates cannot prevent
excessive decoder allocation. Malformed fixtures can exhaust memory or terminate the process.
The original hard-memory requirement is **unresolved**; the owner accepted residual risk only for
restricted fixture testing. Eventual rejection is not allocation prevention. A future isolated
worker needs a separately reviewed architecture/platform/handoff design. A custom Parquet parser
was rejected as disproportionate. Scientific validators and all defensive bounds remain intact.

## L3-F v1 fixture contract

The two public functions are `verify_trusted_scenario_fixture_snapshot(files,
preparation_receipt_bytes) -> ScenarioInputVerification` and
`validate_scenario_input_binding(binding, verification) -> None`. All inputs are immutable caller
bytes or externally supplied records; logical filenames and all archived references are inert.
The output consists of frozen records and tuples, with hashes, population counts/bounds, accepted
candidate/raw identities, original reason-field presence and unavailable-reason counts, enabled
dimensions, lineage/claim declarations, findings and limitations. It contains no approval flag,
source reader, authorization issuer, model binary, aggregation, CLI or execution handoff.

The fixed inventory is `manifest.json`, `M/observed_keys.parquet`, three candidate-named Parquet
projections and three candidate-named JSON originals under `M/original_manifests/`, plus
`M/lightgbm_configuration.json`. `C/membership.parquet` is required exactly when at least one
metadata field is enabled. Separate SN/HW configuration payloads are absent, explicitly represented
by null configuration identities; the original manifests remain required under Phase 7's contract.
No other file is admitted. This synthetic layout does not establish that corresponding verified
real archives or metadata exist.

The exact envelope uses integer `schema_version=1`, `purpose=wp1_scenario_fixture_inputs`,
`input_kind=synthetic_fixture`, simple `bundle_id`, cutoff `2015-07-03`, `h_enabled=false`,
`candidates`, `metadata_fields`, the three fixed `windows`, `files`, `field_schemas`, `population`,
`observed_key_sha256`, `payload_sha256`, `source_lineage_references`,
`observed_key_lineage_reference`, `preparation`, and `availability_claims`.

- Each candidate declaration has its exact `raw_column`, `original_evidence_reference`,
  `original_reason_fields` (ordered subset of `unavailable_reason`, `fit_failure_reason`, including
  empty), and nonempty `legacy_provenance_limitations`. Original JSON keeps its variable historical
  field set; it is strict bounded JSON, with minimal candidate/command/development identity checks and a
  LightGBM configuration-byte hash cross-check. Other original fields remain inert and unverified;
  this does not re-run Phase 7 artifact loading or certify model execution/configuration provenance.
- `files` maps every payload name, excluding the manifest itself, to exact integer `bytes` and
  lowercase SHA-256 `sha256`. The payload digest hashes compact sorted UTF-8 JSON of that inventory
  (`ensure_ascii=False`, no newline). Manifest/receipt identities hash their actual supplied bytes.
  There is no circular manifest self-hash.
- `field_schemas` maps each Parquet name to ordered `{name, type}` records checked against Arrow.
  Keys use int64 Store and timezone-free ns/us timestamps at midnight; horizons use int8/int16/int64;
  Sales/Open/raw values use int64 or float64, masks use booleans, and reason/category strings use
  string/large_string/null. Binary metadata also accepts int64/float64/bool; StateHoliday also accepts
  numeric zero. Missing numeric values require nullable numeric storage. Nested/extension fields,
  unexpected columns, duplicate fields and external Parquet column paths are rejected.
- `population` declares exact positive row/Store/date/origin counts and ISO date bounds. The roster
  contains exactly the three keys, unique and sorted by Store/origin/Date. Its digest hashes ASCII
  `Store\tYYYY-MM-DD origin\tYYYY-MM-DD target\n` per row, without a header. Candidate chronology is
  screened before labels reach the unchanged Phase 7/L1 validators. All three candidates and the
  independent roster must agree exactly, preserving sparse and ineligible rows.
- Enabled C fields follow Promo, StoreType, Assortment, StateHoliday, SchoolHoliday order. Their
  keyed population must match the entire roster, with null categories distinct from missing records,
  unknown text codes retained, binary values validated, and static fields consistent per Store.
  Claims require `original_source_identity` in declared lineage, one of the three S6 levels,
  `assumption_or_evidence_reference`, and `permitted_interpretation` fixed to
  `retrospective_conditional_grouping`. Even `documented_known_at_origin` remains an unverified
  declaration and permits no origin-known or causal inference.
- `preparation` declares `execution_id`, `reference`, 40-hex `code_revision`, 64-hex `lock_sha256`,
  `environment_references`, `custodian_label` and `authorization_reference`. The exact receipt
  repeats those fields and schema/purpose/bundle/lineage/payload identity, adding the actual
  `manifest_sha256`. All identities must agree; custodian and authorization labels are untrusted.
- The separate binding must match bundle/purpose/schema/cutoff, candidate/dimension tuples,
  manifest/payload/receipt hashes, preparation execution/reference, and the deterministic verification
  reference (`wp1-v1:` plus SHA-256 of compact JSON `[manifest_hash, receipt_hash]`). A nonempty external
  reference and unique nonempty permitted-use tuple are required. Only
  `synthetic_fixture_verification` and `synthetic_fixture_compatibility` are supported. Missing or
  mismatched records fail closed; matching records confer no real access or L4 authority.

| Fixed v1 fixture limit | Bound |
|---|---:|
| Logical files, including manifest | 10 |
| Manifest / receipt / each archived JSON | 64 KiB each |
| Total supplied bytes, including receipt | 32 MiB |
| Individual Parquet | 8 MiB |
| Rows / columns / row groups per Parquet | 50,000 / 12 / 64 |
| Parquet footer / Thrift string budget | 128 KiB |
| Footer-declared uncompressed bytes / post-read Arrow output threshold per table | 16 MiB each |
| Aggregate footer-declared bytes / cumulative post-read Arrow output threshold | 64 MiB each |
| JSON/string lengths | 1,024 characters |
| JSON depth / nodes; Thrift container budget | 16 / 10,000; 10,000 |
| References per declared list / logical filename length | 32 / 160 characters |

Supplied byte/JSON sizes and footer parsing have pre-parse bounds. Footer-declared uncompressed
totals are untrusted and serve only as defense-in-depth checks; they can understate decoded output.
PyArrow `ParquetFile.read()` materializes decoded pages and dictionary-expanded values before the
returned table can be measured. The per-table Arrow output and aggregate output thresholds therefore
reject only after allocation, and do not bound peak process memory. Text-length checks run before
pandas conversion but also after Parquet materialization. Python, Arrow, pandas and native temporary
allocations have no hard process-memory budget; malformed or erroneous fixtures may exhaust memory
or terminate the process. WP1-S7-01 is **UNRESOLVED UNDER ORIGINAL CONTRACT — RESTRICTED FIXTURE
CONTRACT APPROVED**. These limits do not certify a hardened parser or production memory budget.

## L1 acceptance criteria

- The builder exposes the documented stable schema and calls the Phase 7 validator as the sole
  authority for candidate, key, label, origin, horizon, window, and availability integrity.
- It retains every validated observed key and approved metadata, uses only the three accepted raw
  forecast fields, and distinguishes label-only, standalone, and common eligibility.
- Its output is deterministic under row and dictionary-order changes, and caller frames are
  unchanged.
- Synthetic tests cover candidate identity, chronology, key/label integrity, missing forecasts,
  source Open/Sales cases, raw forecast semantics, sparse targets, and absence of external side
  effects.
- Focused tests, repository quality checks, and final diff review are recorded with actual results.

## L2 acceptance criteria

- The public summary accepts only the exact L1 population schema, regenerates it through the
  unchanged L1 builder, compares the supplied eligibility/availability/reason fields by canonical
  key, and uses only the regenerated sorted population.
- Optional membership requires the exact observed key set, validates the approved metadata domains,
  preserves missing and unrecognized category states separately, and enforces static StoreType and
  Assortment per Store.
- The five stable tables are `support`, `coverage`, `metrics`, `comparisons`, and `unavailability`.
  They retain all 96 default strata, all declared metadata levels, empty groups, sparse observations,
  exact common-population counts, and original unavailability reasons.
- Every candidate metric and the fixed LightGBM/Seasonal Naive, LightGBM/Holt-Winters, and
  Holt-Winters/Seasonal Naive comparison is computed on the same three-way common rows. Additive
  statistics reconcile direction counts and signed/absolute errors. Signed reconciliation permits
  only a component-magnitude ULP rounding bound while retaining the independently accumulated
  signed sum. Pooled metrics derive from pooled sufficient statistics. Undefined values remain null
  with explicit reasons.
- Serialization validates the complete result and returns deterministic fixture-only JSON bytes
  with fixed schema, integer counts, finite full-precision numbers, normalized negative zero, ISO
  dates, compact sorted UTF-8 JSON, and one trailing newline. It performs no file I/O.
- The serializer requires identical actual-Sales denominators across the three candidates for each
  stratum, checks known/missing/unrecognized metadata identities against the fixed domains, and
  bounds missing-Sales and reason-level unavailable diagnostics by their eligible populations.
- Synthetic tests cover the hand-calculated fixture, coverage and missing-label cases, metadata/key
  integrity, large opposing directional sums and corrupted sufficient statistics,
  candidate-denominator agreement, valid/invalid metadata identities, diagnostic subset bounds,
  ordering/nonmutation, arithmetic overflow, serializer integrity, no external side effects, and
  Phase 7 metric consistency. No real input, fit, forecast generation, protected outcome, holdout,
  Phase 13, selection policy, or inventory decision is accessed or executed.
- Independent L1/L2 review and integration are complete; real-input operations and analysis remain separate gates.

## Validation and completion

Retain hand-calculated population/metric fixtures, source-reference/large-integer checks,
canonical serialization, invalid counts/denominators, no-I/O spies, copy safety and Phase 7
compatibility. Validate from a tracked-files-only checkout without ignored Rossmann artifacts.
Existing named independent Sol 6.1 gates remain mandatory for later work; passing tests or
integrating fixture support does not complete real analysis, project delivery or human approval.
