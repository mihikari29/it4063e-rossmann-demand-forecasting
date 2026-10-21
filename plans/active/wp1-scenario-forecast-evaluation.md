# WP1 — Scenario-Based Forecast Evaluation

**Current state (2026-10-21):** WP1 remains incomplete. Milestone 1 is REVIEWED / INTEGRATED
through PR #50 at `8d4f1fb0b6369cf8501c6f87f5c69d88eb566b10`; WP1-S16 fixture-only Milestone 2
is **IMPLEMENTED / UNDER REVIEW — AWAITING SOL 6.1** on `feat/wp1-fixture-operational-bridge`.
L1 was reviewed and integrated through
PR #46 at `291660108da0c3d91b065a7dba47beabe1926fae`; Quality #149 passed on Python 3.12 and
3.14. L2 was independently accepted and integrated through PR #47 at
`29bfd0e0dbf0d42ef94ba5136d25981652921930`; post-merge Quality #151 succeeded on Python 3.12
and 3.14. The exact six-file L3-F implementation was independently accepted and integrated through
PR #48 at `ed2f37cee5a1e7b3901437acf5e643c612868e55`; PR Quality #152 and main Quality #153 passed
on Python 3.12 and 3.14. See the canonical [L3-F integration closeout](../../docs/PROGRESS.md#wp1-l3-f-post-merge-integration-closeout--2026-10-21).
ADR-029 and the owner-approved WP1-S8 restricted fixture contract below govern L3-F. No real-data
scenario analysis has run, scenario results are not accepted, and ADR-028 remains PROPOSED.
The WP1-S11 implementation, WP1-S13 corrections, WP1-S14 independent acceptance and WP1-S15
integration evidence are preserved in the corresponding [PROGRESS checkpoints](../../docs/PROGRESS.md#wp1-s15--s15-r1-milestone-1-integration--2026-10-21).

## WP1-S15 / S15-R1 Milestone 1 integration closeout — 2026-10-21

The exact corrected six-file Milestone 1 snapshot was independently accepted by Sol 6.1 in
WP1-S14. WP1-S12-01 (Sales precision), WP1-S12-02 (exact Store/Open scalar validation), and
WP1-S12-03 (strict Boolean manifest fields) were resolved in WP1-S13. PR #50 was squash-merged
into `main` at `8d4f1fb0b6369cf8501c6f87f5c69d88eb566b10`. PR Quality [run #156](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/actions/runs/39540940582)
and post-merge Quality [run #157](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/actions/runs/39541341549)
passed Python 3.12 and 3.14. The independent review was by an AI reviewer, not a human GitHub
reviewer. Milestone 1 is REVIEWED / INTEGRATED; WP1 remains INCOMPLETE.

## WP1-S16 fixture-only Milestone 2 implementation — 2026-10-21

The owner-authorized S16 scope implements only the synthetic in-memory C → V → B handoff. It
extends `src/rossmann_forecasting/data/wp1_development.py` and adds provider regressions to
`tests/test_wp1_development.py`; it does not modify the accepted preparation, Phase 7, L1, L2,
CC-02, or L3-F implementation. The branch is based on `origin/main` at
`8d4f1fb0b6369cf8501c6f87f5c69d88eb566b10`.

The handoff composes `create_wp1_fixture_snapshot` and the separate-reference
`verify_wp1_fixture_snapshot`, then requires an externally supplied frozen `WP1FixtureBinding` and
the exact fixture-specific context before `load_wp1_fixture_provider` returns
`WP1BoundFixtureData`. The binding checks exact purpose/schema, manifest/inventory/receipt hashes,
verification identity, all three candidate/raw-column/payload-digest identities, the approved
development cutoff/windows, Promo-only scope and disabled H. Verification identity is a canonical
digest of the entire verification finding. Every provider load reruns independent verification and
re-decodes the immutable payload bytes through the existing candidate, observation and Promo
validators. Candidate and Promo accessors return deep copies with fixture-only provenance and
limitations. Creating the binding record does not authenticate its reference or grant permission;
the output identifies only caller-asserted project-controlled synthetic fixture use.

Before payload decoding, the provider checks exact logical payload names and encoded-size limits:
64 MiB per reference and payload, 1 MiB for the manifest, 256 KiB for the receipt, and 128 MiB for
the combined serialized handoff. It also checks declared population/schema limits before payload
tables are decoded and enforces a 50,000-row ceiling. Inputs are allocated before receipt by the
provider. Declared counts and schemas are checked before payload decoding; actual decoded counts are
checked afterward. These are practical input limits, not hard process-memory containment. WP1-S7-01
remains unresolved. No filesystem rehearsal was needed or implemented, and no single-use execution intent
exists; path alias/symlink, partial-write, and reused-intent tests are therefore not applicable.
The provider does not fit or forecast models, call L1/L2 automatically, simulate inventory, or
publish results. No real input, protected holdout outcome, real binding, L4 analysis, or dependency
was used or added.

Validation ran under local Python 3.14.5:

```text
uv 0.12.23 sync --locked --extra dev --extra api --extra dashboard --python 3.14
Resolved 109 packages; uv.lock unchanged
python -m pytest tests/test_wp1_preparation.py tests/test_wp1_development.py tests/test_wp1_inputs.py tests/test_model_selection.py tests/test_scenario_evaluation.py -q
457 passed; no skips or warnings
python -m ruff check .
All checks passed
python -m ruff format --check .
141 files already formatted
python scripts/check_docs.py
PASS: 338 local destinations/anchors across 36 Markdown files
python -m pip check
No broken requirements found
git diff --check
Passed
```

The full repository suite was not run because a safe artifact-free isolated environment was not
established without probing ignored data/artifact locations. Complete Linux matrix evidence is
deferred to the later authorized PR/CI gate. The implementation is **IMPLEMENTED / UNDER REVIEW —
AWAITING SOL 6.1**; WP1 remains **INCOMPLETE**. The next boundary is independent review only.

## WP1-L3-F integration closeout — 2026-10-21

L3-F is **REVIEWED / INTEGRATED through PR #48** at merge revision
`ed2f37cee5a1e7b3901437acf5e643c612868e55`; main Quality #153 passed on Python 3.12 and 3.14.
The independent Sol 6.1 review accepted the exact six-file snapshot and its original Arrow horizon
range correction. Focused and compatibility test evidence is recorded in the canonical
[PROGRESS closeout](../../docs/PROGRESS.md#wp1-l3-f-post-merge-integration-closeout--2026-10-21).
No human GitHub review was recorded or is claimed. The prior R2/R3 handoff statements that review
and publication were pending describe their historical checkpoints and are superseded by this
closeout.

ADR-029 permits only project-controlled synthetic fixtures and controlled test mutations. The
verifier cannot authenticate fixture origin or custody; hashes, manifests, receipts and bindings
establish consistency, not authorization. Arrow thresholds apply after materialization and do not
enforce peak process-memory limits. WP1-S7-01 remains **UNRESOLVED UNDER THE ORIGINAL CONTRACT**;
restricted-fixture risk acceptance does not authorize a real-data decoder.

Rossmann Sales is monetary turnover, not physical demand or SKU-level quantity, and the approved
three-model comparison is unchanged. Protected July 4–31, 2015 outcomes remain sealed; no WP1
scenario analysis or real-data M/C/H operation has run or is authorized. H segmentation remains
blocked, and WP1-L3-C/V/B and L4 remain unauthorized. ADR-028 remains PROPOSED; ADR-024 remains
authoritative for localhost-only deployment. Phase 13 remains PLANNED / NOT APPROVED, Phase 14
remains incomplete, and no public cloud deployment is claimed. Independent AI review does not
establish human authorship or academic compliance; ownership and AI-assistance disclosure remain
obligations. This closeout does not satisfy the complete instructor assignment.

## WP1-S10 / S11 approved bounded-hybrid Milestone 1 — 2026-10-21

The owner approved `RECOMMEND_BOUNDED_HYBRID` and fixture-only implementation of Milestone 1.
This is a new local implementation branch from `origin/main` at
`8069f518734b6b83b1cf78090b9fbd82dcb45eb5`; no source access or publication is included.

Milestone 1 adds only pure in-memory fixture interfaces in
`src/rossmann_forecasting/data/wp1_preparation.py` and
`src/rossmann_forecasting/data/wp1_development.py`, with focused tests in
`tests/test_wp1_preparation.py` and `tests/test_wp1_development.py`. The preparation module
screens synthetic Rossmann-style CSV rows to the three approved target windows, validates the
exact three Phase 7 candidate records before horizon narrowing, and builds complete keyed
retrospective Promo membership. A separate fixture verifier derives the expected target roster
from independently supplied synthetic source bytes, checks every candidate against that roster,
and validates deterministic canonical manifest, payload and separate receipt identities. The
receipt and all references are consistency evidence only; they grant no permission.

The implementation preserves observed sparse keys, nullable source Sales/Open/Promo, zero Sales,
candidate raw-column identities, labels, masks and original reason fields. It checks dates before
interpreting retained fields and skips post-2015-07-03 synthetic canaries without emitting their
values. Candidate Sales labels retain their original JSON numeric type for exact comparison against
source integers before Phase 7's accepted float normalization. Only Promo is enabled; H remains
disabled. It reuses Phase 7 candidate validation and tests
L1/L2 compatibility without changing those accepted modules or methods. It does not read or hash
real source/artifact paths and does not add a loader, CLI, authorization issuer, bound provider,
L4 runner or publication interface. StoreType and Assortment remain deferred to a separate source
approval. ADR-029's fixture-only caller precondition and post-materialization/no-hard-memory limit
remain in force; WP1-S7-01 remains unresolved under its original contract.

Acceptance is limited to synthetic regressions, focused and Phase 7/L1/L2 compatibility tests,
requested repository checks, complete diff review and final file hashes. At handoff the code remains
**IMPLEMENTED / UNDER REVIEW — AWAITING INDEPENDENT SOL 6.1 REVIEW**. No Milestone 2, real-data
operation, L3-C/V/B, L4, Phase 13, commit, push, PR or merge is authorized by this task.

### WP1-S12 independent implementation rereview — 2026-10-21

Sol 6.1 verified the exact six-file S11 worktree snapshot on the approved branch and returned
REQUEST_CHANGES with two MAJOR findings and one MINOR finding. The public preparation interface
lost large integer Sales precision; Store/Open normalization could round or truncate invalid values
into valid evidence; and numeric values could compare equal to Boolean authorization declarations.
The review and its 45 focused tests, 305 compatibility tests, and 73 synthetic adversarial probes
are recorded in the [WP1-S12 PROGRESS checkpoint](../../docs/PROGRESS.md#wp1-s12-independent-implementation-rereview--2026-10-21).
No code or documentation was changed by that read-only review.

### WP1-S13 correction checkpoint — 2026-10-21

The independent S12 review returned REQUEST_CHANGES for two MAJOR and one MINOR findings. This
correction preserves and validates original candidate Store, Sales, and Open scalars before Phase 7
coercion, restores Sales/Open by validated canonical keys after unchanged Phase 7 validation, and
allows snapshot creation from the prepared output after checking its derived fields. Store accepts
only Python/NumPy integer keys in 1..`2**63 - 1`; Sales accepts non-negative int64 integers, finite
non-negative float64 values or missing; Open accepts exact integer/float 0 or 1 or missing.
Integer/float labels compare by exact numeric equality without tolerance. Manifest authorization
flags require JSON Boolean scalar types. The exact six-file correction, regressions, validation and
remaining fixture-only limitations are recorded in the [WP1-S13 PROGRESS checkpoint](../../docs/PROGRESS.md#wp1-s13-correction-of-s12-findings--2026-10-21).
Status remains **IMPLEMENTED / UNDER REVIEW — AWAITING SOL 6.1 REREVIEW**; this does not authorize
Milestone 2 or any real-source operation.

## WP1-S8 / L3-F-R2 approved revision — 2026-10-20

The owner approved `RECOMMEND_RESTRICTED_FIXTURE_CONTRACT` after S7 REQUEST_CHANGES and R1
DESIGN_REVIEW_REQUIRED. [ADR-029](../../docs/DECISIONS.md#adr-029--wp1-l3-f-restricted-trusted-fixture-contract)
supersedes the generic/untrusted decoder claim and the original hard-memory acceptance condition
for this fixture-support component only. WP1-S7-01 remains
**UNRESOLVED UNDER ORIGINAL CONTRACT — RESTRICTED FIXTURE CONTRACT APPROVED**. The historical S6/R1
checkpoints below remain evidence of their earlier scope, not the current acceptance conditions.

The caller must supply only reviewed, project-controlled synthetic fixture-generator bytes or
controlled synthetic test mutations. This precondition cannot be authenticated by the verifier.
Hashes, manifests, receipts, provenance/custodian/authorization labels, `input_kind`, environment
variables and bindings convey no trust or permission. This verifier is not designed for untrusted
or real Rossmann input decoding; it must not prepare, verify, bind or load actual WP1 development
datasets or be called by production ingestion.

R2's exact six-file scope adds DECISIONS and README to the original four files; branch/base remain
`feat/wp1-scenario-input-verification` / `29bfd0e0dbf0d42ef94ba5136d25981652921930`.
Execution sequence and fixture-only acceptance criteria:

1. Record the owner-approved design before code; preserve the existing scientific validators,
   candidate/raw identities, sparse roster, source Sales/Open, masks/reasons, complete C membership,
   static/null/unrecognized metadata semantics, availability claims and development windows.
2. Rename to `verify_trusted_scenario_fixture_snapshot` and remove the generic alias. Retain frozen
   records and the binding API; every successful result must expose the trust, availability,
   real-roster, real-source, memory and L4 limitations through its existing immutable tuple.
3. Keep purpose and binding uses synthetic-only, including rejection of mutually matching forged
   real-purpose records. Audit tracked source, scripts, tests and entry points; add an architectural
   regression against production imports/callers. Add no loader, filesystem access or command.
4. Preserve every v1 defensive limit. Input byte checks precede decoding; footer estimates remain
   untrusted hints. Arrow logical-output checks occur after materialization. Python, Arrow, pandas
   and native temporary allocations have no hard process-memory budget; decoding may allocate more
   than accepted output. Erroneous fixture bytes can exhaust memory or terminate the process. The
   owner accepts this residual risk only for the restricted fixture context.
5. Retain all scientific/side-effect tests and add trust-boundary checks and bounded synthetic
   dictionary-expansion/forged-low-footer cases. Assert eventual output rejection and demonstrate
   that materialization already occurred; never claim allocation prevention. Run the requested
   focused, compatibility and full suites and repository checks in the existing isolated sibling
   worktree using locked Python 3.14. Record actual results only in PROGRESS.
6. Review the complete six-file change set, including untracked files, and hash the final bytes for
   independent Sol 6.1 review. At this R2 implementation handoff, L3-F was IMPLEMENTED / UNDER
   REVIEW — AWAITING SOL 6.1; Python 3.12 publication/CI, commit, push, PR and merge were not yet
   authorized. Those pending gates were later addressed under separate authorization; see the
   post-merge closeout above.

R2 implementation and validation evidence belongs in the
[R2 PROGRESS checkpoint](../../docs/PROGRESS.md#wp1-l3-f-r2-restricted-trusted-fixture-implementation--2026-10-20),
including the controlled post-allocation measurements. At the R2 checkpoint, independent review of
the final six-file snapshot was still required; that review and integration were later completed as
recorded above. The phase plan stays active because WP1 is incomplete.

Real M/C/H access stays NO-GO; H segmentation stays BLOCKED. L3-C/V/B and L4 require their separate
real-input and execution gates; Phase 13 remains PLANNED / NOT APPROVED and July 4–31 protected.
This test-support revision does not reduce L4 or the complete course deliverables, establish
end-to-end course compliance, accept ADR-028 or replace human ownership/AI-assistance disclosure.

## WP1-S6 accepted design and L3-F execution plan — 2026-10-20 (historical)

The Technical Lead accepted S6 with four mandatory guardrails: structural and declared-provenance
checks do not authenticate authorization or historical provenance; byte and Parquet metadata limits
precede decoding; an independently declared observed-key roster must match all three candidates;
and fixture engineering must remain separate from every real source/preparation/binding/execution
operation. Real M/C/H access is **NO-GO**; H volume segmentation is **BLOCKED**.

L3-F adds only `data/wp1_inputs.py` and `tests/test_wp1_inputs.py`, and updates this plan and
PROGRESS. It supplies a strict in-memory v1 snapshot verifier and a separate immutable external
binding consistency check. It reuses public Phase 7 candidate validation and the L1 population
builder; it does not call L2 aggregation. Ordinary hashes and reference labels convey no approval.

Execution sequence:

1. Verify current main and L2 integration/CI, create `feat/wp1-scenario-input-verification` from
   `29bfd0e0dbf0d42ef94ba5136d25981652921930`, and create a clean detached sibling worktree.
2. Implement fixed inventory/schema/receipt/claim checks, bounded input/footer inspection,
   post-read Arrow output checks, independent roster checks, exact metadata coverage, and fail-closed
   binding consistency. R1 later found the output checks do not enforce a hard allocation cap.
3. Add independently constructed fixtures and failure/side-effect regressions; validate public
   L1/L2 compatibility separately from the verifier.
4. Run focused and full fixture suites plus repository checks only in the isolated worktree with
   pinned uv 0.12.23 and locked Python 3.14 dependencies. Record actual evidence in PROGRESS.
5. Review exactly four local changed files and hand off for independent Sol 6.1 review. No commit,
   push, PR or merge is authorized during this task. L3-C (real preparation), L3-V (real independent
   verification), L3-B (external binding), and L4 execution remain separately gated.

ADR-024 remains authoritative, ADR-028 remains PROPOSED, Phase 13 remains PLANNED / NOT APPROVED,
and the July 4–31 holdout remains protected and unreleased. Human ownership and academic-integrity
review remain required before submission. S6 does not approve a production format/resource budget,
establish custody, or prove independence/completeness of a later real observed-key roster.

At this original S6/R1 checkpoint, L3-F implementation, synthetic validation and local self-review
were finished, but the exact four-file diff remained **IMPLEMENTED / UNDER REVIEW** awaiting
independent Sol 6.1 ACCEPT review and subsequent CI. Canonical commands, environment, test counts,
skips, warning and limitations are recorded in
[PROGRESS](../../docs/PROGRESS.md#wp1-l3-f-fixture-only-scenario-input-verification--2026-10-20).
The plan and its authorization boundary describe that historical checkpoint; current L3-F state is
recorded in the closeout above.

WP1-S7 returned REQUEST_CHANGES for finding WP1-S7-01. The current PyArrow path does not enforce
the advertised decoded-memory cap before allocation; see the R1 checkpoint in PROGRESS. This
finding remains unresolved. The owner subsequently selected the S8 restricted fixture design above;
R2 rereview assesses that narrowed contract and does not close the original finding.

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

## Objective

Compare the three existing Phase 7 Store × Date monetary Sales forecasts across approved Store-level
scenarios using development-only evidence, then explain only the business implications supported by
the available evidence. Preserve Phase 7 candidate identities, chronological origins, raw forecast
semantics, and the existing forecast information boundary.

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

Execution sequence:

1. Add the population adapter, strict membership normalization, fixed stratum generation, additive
   summaries, reconciliation checks, and deterministic fixture serializer to the existing
   `scenario_evaluation.py` module.
2. Extend the existing synthetic tests with independently hand-computed metrics, population and
   metadata integrity cases, deterministic serialization, invalid arithmetic/payload checks, and
   Phase 7 metric reconciliation.
3. Update this plan and PROGRESS with actual implementation and validation state; keep L2
   IMPLEMENTED / UNDER REVIEW until independent review and authorized integration.
4. Run focused fixture tests and repository quality checks. Run the full fixture suite only from a
   clean isolated checkout that has no linked or copied ignored datasets or artifacts; do not
   inspect, read, or hash those artifacts to establish isolation.
5. Self-review the exact four-file diff. This task does not authorize commit, push, PR, merge, real
   input access, L3/L4, Phase 13, or ADR-028 acceptance.

## Dependencies and scientific boundaries

- Reuse `CANDIDATE_IDS`, `FORECAST_COLUMNS`, canonical keys, windows, and validation from
  `src/rossmann_forecasting/forecasting/model_selection.py` and
  `src/rossmann_forecasting/forecasting/validation.py`.
- Keep Phase 7 candidates and model selection unchanged. Do not replace accepted raw forecasts with
  operational forecasts or unclipped diagnostics.
- Keep July 4–31 protected. No source, cached real-data forecast, inventory, or holdout artifact may
  be read or hashed for L1.
- Do not treat absent Store × Date keys as zero, unknown Open as closed, unavailable forecasts as
  zero, or forecast error as observed inventory or lost-sales outcomes.
- Preserve Phase 13 as PLANNED / NOT APPROVED and all of its separate authorization gates.

## Milestones

| Milestone | Scope | Boundary |
|---|---|---|
| L1 — common population | Fixture-only candidate alignment and auditable eligibility masks | REVIEWED / INTEGRATED by PR #46; main Quality #149 passed |
| L2 — metrics and scenario views | Approved metrics, summaries, and in-memory JSON serialization for synthetic fixtures | REVIEWED / INTEGRATED by PR #47; main Quality #151 passed |
| L3-F — fixture input verification | Restricted trusted synthetic M/C snapshots and reference consistency under ADR-029 | REVIEWED / INTEGRATED through PR #48; main Quality #153 passed on Python 3.12/3.14; no hard memory containment |
| WP1-S11 Milestone 1 — fixture preparation and verification core | Synthetic-only source projection, candidate validation, independent source-reference check and deterministic manifest/receipt | **REVIEWED / INTEGRATED through PR #50**; S14 Sol 6.1 ACCEPT; PR Quality #156 and main Quality #157 passed on Python 3.12/3.14 |
| WP1-S16 Milestone 2 — operational fixture bridge and verified provider | In-memory synthetic C → V → B handoff, exact binding consistency and copy-safe L1/L2 inputs | **IMPLEMENTED / UNDER REVIEW — AWAITING SOL 6.1**; synthetic fixtures only; no filesystem or real-source operation |
| L3-C/V/B — real input operations | Custodian preparation, independent real verification, and external binding | Separately gated; real M/C/H access is NO-GO |
| L4 — development analysis | Run frozen scenario analysis on approved cached development evidence and document interpretation | Requires safe inputs, execution authorization, independent review, and disclosure of limitations |

## Deferred decisions

H volume segmentation remains BLOCKED; cross-model inventory experiments remain deferred under a separate
bonus design. Do not infer categorical meanings or turn forecast underprediction into observed
stockouts, lost Sales, or realized savings. L3 requires separate source/input authorization before
safe-input assessment; L4 requires safe inputs, a frozen methodology, separate execution
authorization, independent review, and disclosure. L3-F grants none of those real operations.

## Academic integrity and review

This is a reviewable development draft. Human ownership review and the course's AI-assistance and
authorship disclosure requirements must be resolved before the code is represented as submitted
coursework. Do not describe AI-assisted code as solely human-authored. Independent review must check
validator reuse, masks, sparse population, scenario membership integrity, metrics, deterministic
serialization, and scope before later milestones build on L1/L2.

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
- No commit, push, PR, merge, real-data operation, Phase 13 operation, or L2 implementation occurs
  in this milestone.

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
- L2's independent review and integration gate was subsequently satisfied by PR #47. L3 real-input
  authorization and L4 scenario execution remain separate gates.

## WP1-S4 correction checkpoint — 2026-10-19

The independent review requested changes for four bounded defects. Local corrections now use a
component-scaled ULP bound for signed-error reconciliation, require exact common actual-Sales
denominators across candidates, validate metadata level identities against each fixed domain, and
enforce missing-Sales and per-reason unavailability subset bounds. Regression tests cover the
reviewer-provided cancellation fixture, material signed-total corruption, pooled and non-pooled
denominators, known/missing/unrecognized metadata identities, and both diagnostic bounds.

L2 remains IMPLEMENTED / UNDER REVIEW. Independent Sol 6.1 rereview of the exact corrected diff is
pending; this checkpoint does not accept L2 or authorize publication or integration.
