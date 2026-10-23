# Project Progress

## Current implementation and Git state — 2026-10-23

| Scope | State | Integration |
|---|---|---|
| Phases 0–4 | COMPLETE | On `main`; Phase 3 PR #3/#4, Phase 4 PR #5/#6 |
| Phase 5 — additive Holt-Winters | COMPLETE | PR #7 squash-merged into `main` at `76707a03b7d10dbaa79d3ef26b39e31994431d70`; formal closeout recorded here |
| Repository architecture/governance review | COMPLETE | Integrated with Phase 5 by PR #7 at `76707a03b7d10dbaa79d3ef26b39e31994431d70` |
| Phase 6 — Global LightGBM | COMPLETE | [PR #10](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/10) merged into `main` at `dac71d26bd8a9e43eff7d33592460906ae6fee6f`; [completed plan](../plans/completed/phase-6-global-lightgbm.md) |
| Phase 7 — model selection | COMPLETE | [PR #13](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/13) merged at `89bcb861642ee28259e4a402e8e8ee98a999a6e5`; [completed plan](../plans/completed/phase-7-model-selection.md); selected LightGBM identity and ADR-020 remain intact |
| Phase 8 - forecast uncertainty | COMPLETE | PR #15 merged at `c694f5922a1c1e58ffaf9c2437fd9698ca3e5821`; PR #16 merged at `4dd7717fed57ff3b1f14789b980772c1968f3cba`; accepted Fit B freeze; [completed plan](../plans/completed/phase-8-forecast-uncertainty.md) |
| Phase 9 — synthetic inventory layer | **COMPLETE** | [Completed plan](../plans/completed/phase-9-synthetic-inventory.md); [PR #19](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/19) squash-merged at `7451c50ff685d92e8e74b5014d07b3bbfaca0a22` |
| Phase 10 - inventory simulation | **COMPLETE** | PR #23 `15bce83cd63a4edfeed6defb95788da90d0f36d9`; PR #24 `fcbf6b7de79d57bb7db8a965d5a2b78e9376a3a9`; closeout PR #25 merged at `d437269b9f0cf36a842cdfd496ad50a310804768`; [completed plan](../plans/completed/phase-10-inventory-simulation.md) |
| Phase 11 — Application Services & Thin API | **COMPLETE** | PR #26 squash-merged into `main` at `725d30a59d7c8e04e44f3bcbcce9186f8a1183be`; [completed plan](../plans/completed/phase-11-application-services.md) |
| Phase 12 - Streamlit Dashboard | **COMPLETE** — M1-M4 ACCEPTED / INTEGRATED under ADR-024's localhost-only contract | M3 PR #31 merged at `28aa42fdb2186dbbc340bef72917ce2e2ec06425`; main Quality #96 passed on Python 3.12/3.14. M4 PR #32 squash-merged at `5527e780d1a59108c041bb4ca33a32dbb3bc3aca`; main Quality #103 passed on Python 3.12/3.14. The Technical Lead independently accepted reviewed M4 head `8b4275a24030f4ceb21b2f3d5f88b2c23016aae1`; the user's five-screen visual PASS is user-attested. Approved URL `http://127.0.0.1:8501`; LAN, network, tunnel, firewall, cloud and public exposure remain out of scope under ADR-024. ADR-030 accepts a future public-demo objective, but no public runtime or deployment exists. See the [completed plan](../plans/completed/phase-12-streamlit-dashboard.md), [localhost runbook](DEPLOYMENT_LAN.md) and [M4 evidence](#phase-12-m4-integration-browser-and-local-performance-2026-10-10). |
| Phase 13 — Sequential final evaluation | **M1–M3 INTEGRATED; Phase PLANNED / NOT APPROVED** | M1 PR #38 integrated at `6e7d11a29a593c5eddee640f7c44ca1b3b9cd923`; M2 PR #39 merged at `2a935aea30ab22110153d33d3a55dac44e67a1c8`, with main Quality #125 passing on Python 3.12/3.14. PR #40 integrated M3 and P40 corrections at `1426f29878fd8d7aaa920482310c02842498198b`. Independent M3 review, source preparation, rehearsal, staging, release, M4 and later milestones remain open and separately gated; final evaluation has not run. See the [active plan](../plans/active/phase-13-sequential-final-evaluation.md). |
| CC-02 — weekly STL diagnostic | **REVIEWED / INTEGRATED; real-data evidence pending** | Accepted PR #41 merged at `1c83bb4e629b9b8726ea6613a0888e75deb3fbcc`; Quality #132 passed on Python 3.12 and 3.14. No Rossmann decomposition has been run. |
| CC-02B — development-only Sales provider | **REVIEWED / INTEGRATED; real-data operation pending** | Owner-accepted PR #42 merged at `3efbda248af09231f69a6e461bf5246b2fbb3e3a`; post-merge Quality #135 passed on Python 3.12 and 3.14. Fixture-only implementation is complete; no real bundle or approval binding exists. See the [completed plan](../plans/completed/cc-02b-trusted-development-provider.md). |
| CC-02C — custodian preparation | **REVIEWED / INTEGRATED; real-data operation pending** | PR #43 merged at `13d762c0c622164ebf6a804ab0a1887c738bdbe8`; post-merge Quality #141 passed on Python 3.12 and 3.14. No real source access or preparation was authorized. See the [completed plan](../plans/completed/cc-02c-custodian-preparation.md). |
| CC-02D — minimal custodian execution readiness | **INTEGRATED; real-data operation pending** | PR #44 merged into `main` at `8ad97f8a4d19318b31bba280ee14766c37493a23`; post-merge Quality #145 passed on Python 3.12 and 3.14. The integrated code provides a gated preparation path; no real source access, preparation, binding, STL execution, or findings publication has occurred. See the [runbook](CC-02D_CUSTODIAN_RUNBOOK.md) and [completed task plan](../plans/completed/cc-02d-custodian-execution-readiness.md). |
| WP0-L1 — instructor feedback alignment | **DOCUMENTATION IMPLEMENTED / INTEGRATED** | PR #45 squash-merged into `main` at `2e57a2e96ea6f01a3d47be192124500011defa91`; Quality #147 passed on Python 3.12/3.14. ADR-028 remains proposed; ADR-024 remains authoritative. See the [completed task plan](../plans/completed/wp0-l1-synchronize-project-state.md). |
| WP1 — scenario-based forecast evaluation | **L1/L2/L3-F REVIEWED / INTEGRATED; S11 M1 AND S16 M2 REVIEWED / INTEGRATED; WP1 INCOMPLETE** | L1 integrated through PR #46; independently accepted L2 through PR #47 at `29bfd0e0dbf0d42ef94ba5136d25981652921930`; L3-F integrated through PR #48 at `ed2f37cee5a1e7b3901437acf5e643c612868e55`. Milestone 1 was independently accepted and integrated through PR #50 at `8d4f1fb0b6369cf8501c6f87f5c69d88eb566b10`; PR Quality #156 and main Quality #157 passed on Python 3.12 and 3.14. Fixture-only Milestone 2 was accepted in WP1-S17 and integrated through PR #51 at `a747d7799919497dead9b98bc0498c12115adfc2`; PR Quality #158 and post-merge Quality #159 passed on Python 3.12 and 3.14. No real-source operation or scenario analysis has run. ADR-029 remains fixture-only, and WP1-S7-01 remains unresolved under its original contract. See the [active plan](../plans/active/wp1-scenario-forecast-evaluation.md). |
| Public course demonstration | **Milestone A REVIEWED / INTEGRATED; B1 REVIEWED / INTEGRATED; B2-A IMPLEMENTED / UNDER REVIEW — AWAITING SOL 6.1** | WP2-S9 integrated Milestone A through PR #52; WP2-S12 integrated B1 through PR #53; WP2-S13 implements the offline synthetic FastAPI adapter on its local task branch. Milestone B remains incomplete; B2-B, publication, hosting and deployment are not authorized. See the [active plan](../plans/active/public-course-demo.md), [release contract](PUBLIC_DEMO_RELEASE_CONTRACT.md), [WP2-S9 evidence](#wp2-s9-milestone-a-integration-2026-10-23), [WP2-S12 B1 integration](#wp2-s12-b1-git-integration-and-ci-identity-clarification-2026-10-23), and [WP2-S13 evidence](#wp2-s13-b2-a-offline-synthetic-fastapi-adapter-2026-10-23). |

### WP1-S15 / S15-R1 Milestone 1 integration — 2026-10-21

The corrected six-file Milestone 1 snapshot was independently accepted by Sol 6.1 in WP1-S14,
including resolution of WP1-S12-01 (original Sales precision), WP1-S12-02 (exact Store/Open scalar
validation), and WP1-S12-03 (strict Boolean manifest fields). PR #50 was squash-merged into `main`
at `8d4f1fb0b6369cf8501c6f87f5c69d88eb566b10`. PR Quality run [#156](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/actions/runs/39540940582)
and post-merge main Quality run [#157](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/actions/runs/39541341549)
passed both Python 3.12 and 3.14 jobs on their respective exact revisions. The AI review was not a
human GitHub review. The S11/S12/S13 entries below remain historical implementation and review
checkpoints. Milestone 2 is separately authorized as fixture-only work; WP1 remains incomplete and
no real-source operation or later analytical milestone is authorized here.

### WP1-S18 Milestone 2 integration — 2026-10-21

The fixture-only in-memory Milestone 2 handoff from WP1-S16 was independently accepted by Sol 6.1
in WP1-S17. PR #51 was squash-merged into `main` at
`a747d7799919497dead9b98bc0498c12115adfc2`. PR Quality run [#158](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/actions/runs/39600298597)
and post-merge main Quality run [#159](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/actions/runs/39600899559)
passed on Python 3.12 and 3.14 at their respective exact revisions. This integrates only the
controlled-synthetic provider handoff; it does not perform real-source access, scenario analysis,
WP1-L4, Phase 13, publication or deployment. WP1 remains incomplete and WP1-S7-01 remains unresolved
under its original contract.

### WP1-S16 fixture-only Milestone 2 — 2026-10-21

WP1-S16 extends the integrated Milestone 1 verifier with a controlled-synthetic provider on branch
`feat/wp1-fixture-operational-bridge`, based on `origin/main` at
`8d4f1fb0b6369cf8501c6f87f5c69d88eb566b10`. The in-memory sequence uses the existing
`create_wp1_fixture_snapshot` preparation and `verify_wp1_fixture_snapshot` independent-reference
verification, then requires a separately supplied immutable `WP1FixtureBinding` and the exact
`FIXTURE_USE_CONTEXT` before `load_wp1_fixture_provider` returns defensive-copy candidate and Promo
frames. Verification identity now includes the candidate ID, raw forecast column and candidate
payload digest for all three accepted Phase 7 candidates. The provider re-verifies the snapshot and
separate source reference on every load, validates bound purpose/schema/digests/windows/cutoff/
dimension/H state, reconstructs frames through the existing validators, and exposes fixture-only
provenance and limitations. L1/L2 calls remain explicit caller actions.

Provider preflight limits the in-memory reference to 64 MiB, each payload to 64 MiB, the manifest to
1 MiB, the receipt to 256 KiB, the combined serialized handoff to 128 MiB, and declared/decoded
populations to 50,000 rows. Declared counts and schemas are checked before payload decoding; actual
decoded population counts are checked after decoding. These ordinary encoded-size/schema/row
checks do not establish hard peak-memory containment; inputs have already been allocated before
the provider receives them, and WP1-S7-01 remains unresolved under its original contract. No
filesystem rehearsal or one-use execution intent was implemented, so path-alias/symlink, partial
write, and stale single-use-intent cases do not apply. No CC-02 grant, real input path, real source,
candidate archive, July 4–31 outcome, L4, fit, forecast generation, automatic L2 aggregation,
inventory analysis, publication or dependency change was introduced.

The locked local Python 3.14.5 environment was synchronized with `uv 0.12.23` using
`uv sync --locked --extra dev --extra api --extra dashboard --python 3.14` (109 packages resolved;
`uv.lock` unchanged). The focused synthetic regression command
`python -m pytest tests/test_wp1_preparation.py tests/test_wp1_development.py tests/test_wp1_inputs.py tests/test_model_selection.py tests/test_scenario_evaluation.py -q` passed (**457 passed**, no skips or warnings). Repository Ruff lint passed, Ruff formatting reported 141 files already formatted, documentation validation passed for 338 local destinations/anchors across 36 Markdown files, `pip check` reported no broken requirements, and `git diff --check` passed. The full repository suite was not run because an artifact-free isolated full-suite environment was not established without probing ignored data/artifact locations; complete Linux matrix evidence remains for a later authorized PR/CI gate. No new dependencies were added.

The exact local implementation remains **IMPLEMENTED / UNDER REVIEW — AWAITING SOL 6.1**. WP1 remains **INCOMPLETE**; no real-source preparation or binding is complete, and the next boundary is independent review only.

### WP1-L3-F-R3 original horizon range guard — 2026-10-20

The independent WP1-S9-I review returned REQUEST_CHANGES for WP1-S9-I-01. An `int64` horizon such
as 65537 or -65535 passed the supported physical schema and was silently narrowed to `int16` by
the unchanged Phase 7 validator before its range check, becoming 1 and matching a one-day target.
The defect let invalid original candidate metadata pass the fixture verifier.

The R3 correction checks candidate horizons on the decoded PyArrow integer column, after the
existing output-size check and before pandas conversion or either Phase 7/L1 validator. It requires
an integer type, no nulls, and exact Arrow minimum/maximum values within 1–14 inclusive. Arrow
integer scalar conversion yields Python integers, so the guard does not narrow the values, convert
them to floating point, or change the accepted physical schema. The existing Phase 7 validator
remains authoritative for agreement between every valid horizon and its origin/target dates.
Metadata schema, all three candidates, caller frames, trust/binding semantics, and memory limits
are unchanged. WP1-S7-01 remains **UNRESOLVED UNDER ORIGINAL CONTRACT — RESTRICTED FIXTURE
CONTRACT APPROVED**.

Regressions exercise 65537, -65535, 32769, 0 and 15 against each of the three candidates. They
confirm that hashes and receipts are validly resealed and caller DataFrames remain unchanged before
the expected original-horizon error. Date-consistent horizons 1 and 14 remain accepted; an in-range
horizon that disagrees with the date remains rejected by Phase 7. Null and non-integer physical
horizons are also rejected. The final focused input suite passed **218 tests**; the compatibility
suite passed **305 tests** across L3-F, L1/L2 scenario evaluation and Phase 7 model selection. The
full synthetic fixture suite passed **1,075 tests**, with **7 skips** and **1 existing warning** in
**249.89 seconds**. Six skips require unavailable Windows symlink privileges, and the optional
canonical-artifact test skips because ignored upstream artifacts are absent. The warning is the
existing Starlette/httpx TestClient deprecation.

Validation used the existing artifact-free detached sibling worktree at
`29bfd0e0dbf0d42ef94ba5136d25981652921930`, with the exact corrected source, tests and progress
record synchronized by SHA-256. The locked Windows x64 environment is Python 3.14.5, NumPy 2.5.3,
pandas 3.0.6, PyArrow 24.0.0, pytest 9.1.1 and Ruff 0.16.10; `uv.lock` remains unchanged. Final
Ruff lint, formatting (**137 files**), Markdown link validation, offline lock check (**109
packages**), installed-package check (**91 packages**) and whitespace checks passed. No ignored
datasets, forecasts, authorization records or protected outcomes were accessed. No fit, forecast
generation, L2 aggregation, source operation, or production path was introduced.

At the end of this R3 implementation checkpoint, R3 was **IMPLEMENTED / UNDER REVIEW — AWAITING
INDEPENDENT REREVIEW**; L3-F and WP1 were not complete at that point. ADR-029 remained accepted,
ADR-028 remained PROPOSED and ADR-024 remained authoritative. Real M/C/H operations were NO-GO,
H segmentation was BLOCKED, and L3-C/V/B and L4 were separately gated. Phase 13 was PLANNED / NOT
APPROVED and the July 4–31 holdout was protected and unreleased. At that checkpoint, no commit,
push, PR, merge or publication had occurred. The later integration status is recorded below.

### WP1-L3-F post-merge integration closeout — 2026-10-21

The exact six-file L3-F snapshot received independent Sol 6.1 **ACCEPT** review and was squash-merged
through [PR #48](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/48) at
`ed2f37cee5a1e7b3901437acf5e643c612868e55`. The independent review evidence records the corrected
original Arrow horizon-range validation and focused input/compatibility testing. The R3 record above
reports 218 passing focused input tests and 305 passing compatibility tests across L3-F, L1/L2 and
Phase 7. The developer-reported full synthetic fixture suite passed 1,075 tests, with 7 skips and 1
existing warning; this full-suite run is developer evidence and is not attributed to Sol 6.1.

PR Quality [#152](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/actions/runs/39516884014)
passed on Python 3.12 and 3.14. Post-merge main Quality
[#153](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/actions/runs/39517296266)
also passed on Python 3.12 and 3.14 at the merge revision above. No human GitHub review was recorded
or is claimed. This closeout records L3-F as **REVIEWED / INTEGRATED**; WP1 remains incomplete.

ADR-029 restricts inputs to project-controlled synthetic fixtures and controlled test mutations;
the verifier cannot authenticate fixture origin or custody. Hashes, manifests, receipts and bindings
establish consistency, not real-data authorization. Arrow output thresholds apply after
materialization and do not enforce peak process-memory limits. **WP1-S7-01 remains unresolved under
the original contract**; restricted-fixture risk acceptance does not authorize a real-data decoder.

Rossmann Sales remains monetary turnover, not physical demand or SKU quantities, and the approved
three-model comparison is unchanged. No WP1 scenario analysis or real-data M/C/H source operation
has run or is authorized. The July 4–31, 2015 outcomes remain sealed; H segmentation remains
blocked, and L3-C/V/B and L4 remain unauthorized. ADR-028 remains PROPOSED; ADR-024 remains
authoritative for localhost-only deployment. Phase 13 remains PLANNED / NOT APPROVED, Phase 14
remains incomplete, and no public cloud deployment is claimed. Independent AI review does not
establish human authorship or academic compliance; ownership and AI-assistance disclosure
obligations remain. This documentation closeout does not satisfy the complete instructor
assignment.

### WP1-S11 fixture-only Milestone 1 — 2026-10-21

The owner's corrective task confirms prior approval of `RECOMMEND_BOUNDED_HYBRID` and local
synthetic-only Milestone 1 implementation, tests, documentation and handoff for independent Sol
6.1 review. Work is on `feat/wp1-real-input-fixture-core`, based on `origin/main` at
`8069f518734b6b83b1cf78090b9fbd82dcb45eb5`. The worktree contains only the two new fixture
modules, their two new test files and this active WP1 plan/PROGRESS update. Nothing was committed,
published, merged or deleted.

`data/wp1_preparation.py` provides `prepare_target_observations(source_csv_bytes)`, which projects
only Store, Date, Sales, Open and Promo for the three approved target windows;
`prepare_candidate_records(records_by_candidate)`, which range-checks original integer horizons
before calling the unchanged Phase 7 validator; and `build_promo_membership(observations)`, which
creates complete keyed retrospective Promo membership. `data/wp1_development.py` provides
`create_wp1_fixture_snapshot(source_csv_bytes, candidate_records)`, producing deterministic
canonical JSON payloads, a strict preparation manifest and a separate consistency receipt; and
`verify_wp1_fixture_snapshot(snapshot, independent_source_reference)`, which scans a separately
supplied synthetic CSV reference with its own parser, derives the source roster, compares every
candidate's keys/Sales/Open and validates Promo coverage. Its frozen result carries identities,
counts and limitations only. Candidate Sales labels retain their original integer-or-float JSON
type so the independent source comparison catches adjacent large-integer mismatches before Phase
7's accepted float64 normalization can collapse them.

The regressions cover shared omissions, extra keys, changed labels, horizon overflow and boundary
values, protected-date canaries, sparse/missing/zero Sales, large-integer precision collisions,
raw-field and mask semantics, reason preservation, Promo null versus missing membership, canonical
and duplicate-key JSON, tampered identities/declarations, deterministic ordering, input
nonmutation, no external I/O and no fitting, forecasting or L2/publication calls from the new
verifier. A separate synthetic compatibility test passes the prepared records through Phase 7, L1
and the existing in-memory L2 summarizer. These fixtures do not establish real source custody or
candidate-artifact authenticity.

Focused WP1 tests passed **45/45**. The selected WP1/Phase 7/L1/L2 compatibility command passed
**350 tests** in **104.40 seconds**, with no skips, warnings or failures. Validation used the
existing Windows x64 Python **3.14.5**, pytest **9.1.1** and Ruff **0.16.10** environment. Whole-repo
Ruff lint passed; format check passed (**141 files**); `scripts/check_docs.py` passed (**336 local
destinations/anchors across 36 Markdown files**); and `git diff --check` passed. The full fixture
suite was not run because this checkout was not established as an isolated artifact-free
environment; no ignored datasets, cached forecasts, authorization packets or protected outcomes
were read, enumerated or hashed.

The implementation remains **IMPLEMENTED / UNDER REVIEW — AWAITING INDEPENDENT SOL 6.1 REVIEW**.
ADR-029 still limits use to caller-supplied controlled synthetic fixtures, and WP1-S7-01 remains
unresolved under its original contract. This work adds no real-source access, custody, binding,
loader, L4, Phase 13, H segmentation, publication or deployment permission. WP1 remains incomplete;
L3-C/V/B and L4 remain separately gated, July 4–31 outcomes remain protected, and no commit or
publication was authorized.

### WP1-S12 independent implementation rereview — 2026-10-21

The independent Sol 6.1 review verified the exact six-file S11 worktree snapshot on
`feat/wp1-real-input-fixture-core`, based at `8069f518734b6b83b1cf78090b9fbd82dcb45eb5`, and
returned **REQUEST_CHANGES** with two MAJOR findings and one MINOR finding. It independently passed
45 focused tests and 305 Phase 7/L1/L2/L3-F compatibility tests. Of 73 additional synthetic
adversarial probes, 68 passed and five assertions reproduced the reported defects. Ruff, formatting,
Markdown links, and whitespace checks passed; the full suite was not run.

The findings were loss of large integer Sales precision in public candidate preparation; Store and
Open values rounding or truncating into valid keys/labels before snapshot serialization; and
authorization manifest flags accepting numeric values that compare equal to Python Booleans. The
S12 review made no repository changes. S11's implementation evidence above remains its original
checkpoint; the corrective implementation and its results are recorded separately below.

### WP1-S13 correction of S12 findings — 2026-10-21

The independent WP1-S12 review returned **REQUEST_CHANGES** with two MAJOR findings and one MINOR
finding. The correction preserves original candidate labels before Phase 7's unchanged numeric
normalization. `prepare_candidate_records` validates and saves labels by canonical Store, origin,
and target keys; after Phase 7 validation it restores Sales and Open into object-typed columns. It
accepts its own prepared output as snapshot input, verifies the prepared derived columns, and
rebuilds the normalized candidate records without relying on row positions. Exact numeric equality
allows an integer and equal-valued float (for example `20` and `20.0`); it applies no tolerance, so
`9007199254740992` and `9007199254740993` remain distinct.

The supported candidate scalar contract is explicit: Store is a Python/NumPy integer from 1 through
`2**63 - 1` (Booleans, floats, strings, Decimal values, nulls, fractions and out-of-range values
are rejected); Sales is a non-negative int64 integer, finite non-negative float64 value, or missing;
Open is exact integer/float `0` or `1`, or missing. Booleans, strings, Decimal values, fractional or
non-finite Open values are rejected before Phase 7 coercion. Snapshot serialization rechecks the
original Store/Sales/Open values and writes the checked Open semantics. Every authorization flag in
the manifest is type-checked as a JSON Boolean before its required false value is compared; the
H-disabled declaration remains strictly Boolean.

Synthetic regressions cover both adjacent integers above `2**53`, raw and prepared-output snapshot
creation, exact integer/float equivalence, null labels, all three candidate Store/Open paths,
positive int64 Store boundaries, invalid discrete values, and resealed Boolean mutations. The
corrections leave the independent source roster, forecasts, masks, Promo membership, and accepted
Phase 7/L1/L2/L3-F methods unchanged. No real source, authorization packet, cached artifact, or
protected outcome was accessed. The S13 implementation remains **IMPLEMENTED / UNDER REVIEW —
AWAITING SOL 6.1 REREVIEW**; WP1-S7-01 remains unresolved under its original contract.

Final validation on Windows x64 with the locked Python **3.14.5**, pytest **9.1.1**, and Ruff
**0.16.10** environment passed **125 focused WP1 preparation/development tests** in **16.98
seconds** and **305 Phase 7/L1/L2/L3-F compatibility tests** in **141.47 seconds**, with no
failures, skips, or warnings. `ruff check --no-cache .` passed; `ruff format --check --no-cache .`
passed (**141 files**); `scripts/check_docs.py` passed (**339 local destinations/anchors across
36 Markdown files**); and both `git diff --check` and a trailing-whitespace scan of the six
authorized files passed. The full fixture suite was not run because this checkout was not
established as safely isolated from ignored artifacts; no ignored Rossmann data or protected
artifacts were inspected to establish isolation.

### WP1-L3-F-R2 restricted trusted-fixture implementation — 2026-10-20

The owner's R2 task records WP1-S8's **RECOMMEND_RESTRICTED_FIXTURE_CONTRACT** and explicit approval
of that revision. This follows WP1-S7 **REQUEST_CHANGES** and R1 **DESIGN_REVIEW_REQUIRED** for
WP1-S7-01. Accepted [ADR-029](DECISIONS.md#adr-029--wp1-l3-f-restricted-trusted-fixture-contract)
supersedes only L3-F's trust/resource acceptance conditions. The earlier four-file implementation
and R1 entries below remain historical evidence; their counts and interfaces describe those
snapshots. No original failure evidence is erased or reclassified as a technical repair.

The public decoder is now `verify_trusted_scenario_fixture_snapshot`; the generic old API is
removed without an alias. Only reviewed project-controlled synthetic fixture-generator bytes and
controlled synthetic test mutations meet its caller precondition. The implementation cannot
authenticate that precondition. Hashes, manifests, receipts, claimed custody/authorization,
`input_kind`, environment assertions and matching bindings convey no trust or authority. This
verifier is not designed for untrusted or real Rossmann input decoding and must not prepare,
verify, bind or load actual WP1 development datasets or enter production ingestion.

All successful frozen verification results carry explicit fixture-only, unauthenticated
origin/custody, unverified historical availability and real observed-roster completeness,
no-real-source-permission, no-hard-peak-memory and no-L4-approval limitations in their existing
immutable tuple. No trust/approval Boolean or new framework is added. Bindings retain identity
consistency semantics and the two synthetic-only uses; even two mutually matching fabricated
records with a real-data purpose are rejected. Public Phase 7 and L1 validation, exact candidates,
raw fields, masks/reasons, sparse roster, complete C membership, static/null/unrecognized categories,
availability classifications and the development ceiling remain unchanged. The decoder never
invokes L2 aggregation.

WP1-S7-01 is **UNRESOLVED UNDER ORIGINAL CONTRACT — RESTRICTED FIXTURE CONTRACT APPROVED**.
All original input/schema/JSON/footer/logical-output bounds remain. Byte limits precede decoding;
footer estimates are untrusted admission/rejection hints; Arrow output checks follow
materialization. PyArrow may allocate more than accepted output. Python, Arrow, pandas and native
temporary allocations have no hard process-memory budget. Erroneous fixtures can exhaust memory
or terminate the process; the owner accepts this residual risk only for restricted fixture testing.
The R2 regressions demonstrate retained eventual rejection after allocation, not prevention.

Exactly six local files are authorized and changed: `src/rossmann_forecasting/data/wp1_inputs.py`,
`tests/test_wp1_inputs.py`, the active WP1 plan, PROGRESS, DECISIONS and README. Source, script,
test and application/CLI entry-point inspection found no production decoder integration; an
architectural regression checks tracked Python/TOML files only, allowing references solely in the
fixture module and its tests. Existing no-I/O/execution/authorization spies remain. No real source
path, artifact loader, filesystem reader, CLI, dependency or lockfile change is introduced.

Validation uses the existing detached sibling worktree
`C:/Users/Minh/Desktop/hust/introba/project/it4063e-rossmann-demand-forecasting-validation-wp1l3f`
at `29bfd0e0dbf0d42ef94ba5136d25981652921930`, copying only the six authorized files. Known
raw/interim/processed/generated-report/artifact/model directories are absent. No ignored dataset,
forecast, inventory output, authorization packet or protected outcome was copied, linked, scanned,
read or hashed. Its existing locked Windows x64 environment uses Python 3.14.5, NumPy 2.5.3,
pandas 3.0.6, PyArrow 24.0.0, pytest 9.1.1 and Ruff 0.16.10. Python 3.12 and new remote CI remain
pending until a separately authorized post-review publication step.

The original 174 scientific/integrity/side-effect tests are retained with the renamed API. The
24 added cases cover removal of the generic API, immutable result limitations, all prohibited
purposes/uses, mutually matching forged real-purpose records, fabricated provenance/environment
assertions, absence of tracked production callers, and the two controlled expansion mechanisms.
The archived S7 byte counts below remain the original review evidence. R2 uses bounded
reconstructions rather than the reviewer's original encoded blobs; an instrumented invocation
of each exact test measured these final-generator values:

| Synthetic reconstruction | Rows | Encoded bytes | Footer-declared bytes | Materialized Arrow bytes | Outcome |
|---|---:|---:|---:|---:|---|
| Honest dictionary expansion; 1,024-character repeated reason | 20,000 | 125,510 | 206,543 | 21,880,000 | Rejected after materialization |
| Forged-low row-group total; 32,768-character repeated reason | 1,024 | 6,312 | 0 | 33,626,112 | Rejected after materialization |

Both pass the small byte/footer admission checks, exceed the unchanged 16 MiB logical-output
threshold, and are rejected before pandas conversion, text-length checks or scientific validation.
The spies explicitly observe the oversized Arrow table. This is evidence of post-allocation output rejection,
not containment or prevention. The fixture-only footer mutation replaces one asserted unique marker
in a generated single-row-group footer; it is not a general Parquet parser or production control.

Commands use the isolated `.venv/Scripts/python.exe` directly (`python` below), with
`PYTHONDONTWRITEBYTECODE=1`. `uv` is the existing pinned 0.12.23 executable at
`C:/Users/Minh/AppData/Roaming/Python/Python314/Scripts/uv.exe`; no new environment or dependency is
introduced. The unchanged lock SHA-256 is
`16d76d6ffca3848e6af5f7ab838bc16c6b88d18b1af0097e5a3c216fe7e36ad0`.

```powershell
python -B -m pytest -p no:cacheprovider tests/test_wp1_inputs.py
python -B -m pytest -p no:cacheprovider tests/test_wp1_inputs.py tests/test_scenario_evaluation.py tests/test_model_selection.py
python -B -m pytest -p no:cacheprovider
python -B -m ruff check --no-cache .
python -B -m ruff format --check --no-cache .
python -B scripts/check_docs.py
uv lock --check --offline
uv pip check
git diff --check
```

The final-code input suite passed **198 tests in 21.42 seconds**. The compatibility suite passed
**285 tests in 106.80 seconds**: 198 input tests, 52 L1/L2 scenario tests and 35 Phase 7 tests;
neither run had skips or warnings. The final complete fixture suite passed **1,055 tests**, with
**7 skips** and **1 warning**, in **273.74 seconds**. Six skips require unavailable Windows symlink
privileges, and the optional canonical-artifact test skips because ignored upstream artifacts are
absent. The warning is the existing Starlette/httpx TestClient deprecation. No new dependency was
added to suppress it. Before the final generator's honest case was switched from Zstandard to
Snappy for closer encoded-size correspondence with S7, preliminary focused/compatibility runs
passed 198/285 tests in 25.41/113.07 seconds; the final counts/times above supersede those runs.

Final repository checks passed Ruff lint, formatting (**137 files**), Markdown validation
(**333** destinations/anchors across **36** files), `uv lock --check --offline` (**109 packages**),
`uv pip check` (**91 compatible installed packages**) and `git diff --check`. Separate no-index
checks of both untracked Python files found no whitespace diagnostics; their status 1 denotes
the expected file difference against NUL, not a failed whitespace check. Final self-review covers
all six files, including the untracked implementation/tests. Byte identities agree with the
isolated validation snapshot; the six final SHA-256 hashes are supplied in the review handoff
outside these files to avoid a self-referential PROGRESS hash. No seventh file, accepted method,
production path, dependency, lockfile, API/dashboard, CC-02 or Phase 13 implementation changed.

L3-F stays **IMPLEMENTED / UNDER REVIEW — AWAITING SOL 6.1**; WP1 is not complete.
Real M/C/H access remains **NO-GO**, H segmentation **BLOCKED**, and L3-C/V/B and L4 separately
gated. ADR-028 remains PROPOSED, ADR-024 authoritative, Phase 13 PLANNED / NOT APPROVED and July
4–31 protected. No commit, push, PR, merge, real-data model fitting/forecasting/scenario execution,
custody approval or deployment is authorized or performed. Synthetic compatibility and repository
tests may exercise existing synthetic analytics/model routines; they do not produce real-data
course evidence. The complete course objectives and human ownership/authorship/AI-assistance
disclosures remain required.

### WP1-L2 integration and WP1-S6 acceptance — 2026-10-20

The owner-supplied handoff records independent acceptance of the corrected L2 implementation.
Live GitHub metadata confirms PR #47 squash-merged at
`29bfd0e0dbf0d42ef94ba5136d25981652921930`, matching clean local main and fetched origin/main.
Post-merge [Quality #151](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/actions/runs/39286696223)
succeeded at that exact SHA, with both Python 3.12 and Python 3.14 jobs successful. L2 is
REVIEWED / INTEGRATED; the earlier implementation and correction entries below remain historical
evidence of their respective checkpoints.

The Technical Lead accepted WP1-S6 for L3-F with four mandatory clarifications: structural and
declared-provenance verification does not prove authorization or authentic historical provenance;
resource limits and Parquet metadata checks precede decoding; a separately declared observed-key
roster must agree with all three candidate populations; and synthetic engineering remains separate
from any real source/preparation/binding/execution operation. The owner authorized only the local
four-file L3-F implementation, synthetic tests and checks, and local review. This acceptance does
not accept ADR-028, enable a real source, or authorize later milestones.

### WP1-L3-F fixture-only scenario input verification — 2026-10-20

L3-F is IMPLEMENTED / UNDER REVIEW on `feat/wp1-scenario-input-verification`, based on
`29bfd0e0dbf0d42ef94ba5136d25981652921930`. Its exact four-file scope is the new
`src/rossmann_forecasting/data/wp1_inputs.py`, new `tests/test_wp1_inputs.py`, the active WP1 plan,
and this progress record. The implementation adds `verify_scenario_bundle_snapshot` and
`validate_scenario_input_binding`, frozen record objects, a strict synthetic v1 envelope/receipt,
fixed nine/ten-file inventory, computed byte/key identities, bounded in-memory Parquet inspection,
and separate external reference consistency checking. Parquet input/footer inspection is bounded,
but Arrow output checks occur after table materialization. It changes no accepted Phase 7, L1 or L2 code,
dependencies, forecast/inventory methods or commands. The [active plan](../plans/active/wp1-scenario-forecast-evaluation.md#l3-f-v1-fixture-contract)
documents the exact schema, digest encodings, physical types and fixed fixture limits.

The verifier calls public Phase 7 validation and the unchanged L1 builder, retains sparse observed
keys, original raw-column identities, Sales/Open labels, forecast and eligibility masks, and original
reason presence/precedence/fallback semantics. It compares all candidate keys with the independent
declared roster, including shared-omission detection. C metadata requires the entire observed
population, including ineligible rows, with null categories distinct from missing records and static
Store fields consistent. It screens development chronology before labels reach the evaluation
layers. Footer metadata and aggregate declared-uncompressed checks precede table materialization,
but these values are untrusted and do not bound decoder allocations; Arrow output-size checks follow
materialization. External column-file paths are rejected. JSON rejects duplicate keys, non-finite constants/numbers,
unsupported fields and structural excess. Archived original JSON retains its variable historical
field set and inert references; only its bounded syntax, minimal candidate/command/development identity and
LightGBM configuration-byte relationship are checked, not authentic historical model execution.

Availability claims retain the three S6 levels as **unverified declarations**, with permitted
interpretation limited to retrospective conditional grouping. The output and binding confer no
authorization, trusted signer identity, real custody or historically available promotion/holiday/
Store/Open schedule. Separate SN/HW configuration payloads are explicitly absent; original manifests
remain required. The synthetic archival layout establishes no availability of verified real inputs.

Real M/C/H access remains **NO-GO**, and H volume segmentation remains **BLOCKED**. L3-C, L3-V,
L3-B and L4 remain separately gated. ADR-028 remains PROPOSED, ADR-024 remains authoritative,
Phase 13 remains PLANNED / NOT APPROVED, and July 4–31 remains protected and unreleased. Human
ownership and course academic-integrity/AI-assistance disclosure remain required before submission.
Independent Sol 6.1 ACCEPT review of this exact local diff and subsequent required CI remain pending.
No commit, push, PR or merge has occurred during L3-F.

Validation uses the fresh detached sibling worktree
`C:/Users/Minh/Desktop/hust/introba/project/it4063e-rossmann-demand-forecasting-validation-wp1l3f`
at the exact L2 integration base, with only the four scoped files copied in. Tracked-path inspection
showed only `data/README.md` under data/artifacts/models/generated reports; known raw, interim,
processed, generated-report, artifact and model directories were absent. No ignored dataset or
forecast/inventory artifact was copied, linked, inspected, read or hashed. The new code and tests
are checked for byte identity between implementation and validation worktrees at final handoff.

The locked environment is Windows x64, Python **3.14.5**, uv **0.12.23**, NumPy **2.5.3**,
pandas **3.0.6**, PyArrow **24.0.0**, pytest **9.1.1**, and Ruff **0.16.10**. uv was absent from
PATH, so commands used its existing executable at
`C:/Users/Minh/AppData/Roaming/Python/Python314/Scripts/uv.exe`; `uv` below denotes that executable.
No local Python 3.12 run or new remote CI run was performed; Python 3.12 validation awaits the
separately gated publication/CI process.
The tracked lockfile SHA-256 is
`16d76d6ffca3848e6af5f7ab838bc16c6b88d18b1af0097e5a3c216fe7e36ad0`.

Executed commands, from the isolated worktree:

```powershell
uv sync --locked --extra dev --extra api --extra dashboard --python 3.14
uv run --locked --extra dev --extra api --extra dashboard python -B -m pytest -p no:cacheprovider tests/test_wp1_inputs.py tests/test_scenario_evaluation.py tests/test_model_selection.py
uv run --locked --extra dev --extra api --extra dashboard python -B -m pytest -p no:cacheprovider
uv run --locked --extra dev --extra api --extra dashboard python -B -m ruff check --no-cache .
uv run --locked --extra dev --extra api --extra dashboard python -B -m ruff format --check --no-cache .
uv run --locked --extra dev --extra api --extra dashboard python -B scripts/check_docs.py
uv lock --check
uv pip check
git diff --check
```

Initial focused validation passed 249 tests. After resource/side-effect regressions were expanded,
one synthetic external-column metadata fixture failed before verifier invocation because PyArrow's
metadata writer needed a readable buffer. Replacing the write-only buffer with in-memory BytesIO
corrected that test; the expanded focused suite then passed 260 tests. The first complete fixture
run passed 1,030 tests, with 7 skips and 1 existing warning in 258.75 seconds. Self-review then added
one bounded regression rejecting a contradictory archived runner command while preserving legitimate
absence of that legacy field. Final-snapshot validation is recorded below.

The final focused command passed **261 tests** in **102.58 seconds**: **174** L3-F input tests,
**52** scenario-evaluation tests and **35** Phase 7 model-selection tests, with no skips or warnings.
Final-code repository checks passed Ruff lint, formatting (**137 files**), Markdown validation
(**328** local destinations/anchors across **36 files**), `uv lock --check` (**109** packages),
`uv pip check` (**91** compatible installed packages), and `git diff --check`. Additional no-index
checks found no whitespace diagnostics in either new file. Git initially printed LF-to-CRLF
normalization notices; a command-local raw-content check passed without changing Git configuration.

The **final complete fixture suite passed 1,031 tests**, with **7 skips** and **1 warning**, in
**254.49 seconds**. Six skips require Windows symlink privileges; the optional canonical-artifact
test skipped because ignored upstream artifacts were absent. The warning is the existing
Starlette/httpx TestClient deprecation notice. All **174** new input-verification tests passed.
Final documentation validation and diff/byte-identity checks passed after recording these results.
Exactly the four scoped files remain uncommitted; the active phase plan is retained for independent
review and later explicitly authorized milestones. WP1 is not complete.

The verifier and binding check perform no source/artifact I/O, authorization issuance, model fitting,
CC-02 preparation/execution, Phase 13 operation or L2 aggregation. Side-effect spies cover valid and
invalid snapshots and bindings. The separately invoked L2 compatibility test and existing repository
suite exercise synthetic fixtures only, including existing synthetic model routines; no real-data
fit, forecast generation, scenario analysis, recalibration, inventory operation or protected-outcome
access/hash has occurred. Real custody/authentication, historical availability, observed-roster
independence/completeness and production resource limits remain unverified and separately gated.

### WP1-L3-F-R1 preallocation memory enforcement blocker — 2026-10-20

Independent WP1-S7 review returned **REQUEST_CHANGES** for WP1-S7-01: the decoded-memory limits are
checked after PyArrow has allocated the table. The prior reviewer reproduced two validly enveloped,
fully synthetic inputs: a 20,000-row, 1,024-character dictionary-encoded table with 127,450 encoded
bytes and 211,407 footer-declared uncompressed bytes materialized 21,812,500 Arrow bytes; a forged-low
footer case with 6,523 encoded bytes and a declared total of zero materialized 33,555,787 Arrow
bytes. Both exceeded the 16 MiB output threshold before rejection. Encoded-page totals alone do not
prevent the honest dictionary expansion.

R1 investigation used the locked PyArrow 24.0.0 environment and the corresponding official API and
implementation references. `ParquetFile.read()` has no memory-pool or allocation-limit parameter;
`iter_batches()` limits rows yielded per batch, not the size of a page or dictionary decoded inside
the reader. `MemoryPool` exposes allocation statistics and `max_memory()`, while `proxy_memory_pool`
tracks a parent pool; neither API rejects allocations at a configured byte limit. PyArrow's Parquet
reader grows a decompression buffer to the page-header uncompressed size when reading compressed
pages. Thus footer totals, output size checks, memory-pool measurements, and small batches are not
preallocation controls. References: [PyArrow 24 ParquetFile API](https://arrow.apache.org/docs/24.0/python/generated/pyarrow.parquet.ParquetFile.html),
[PyArrow 24 MemoryPool API](https://arrow.apache.org/docs/24.0/python/generated/pyarrow.MemoryPool.html),
[PyArrow 24 page reader](https://github.com/apache/arrow/blob/apache-arrow-24.0.0/cpp/src/parquet/column_reader.cc#L3104-L3125).

A footer-level encoding/codec whitelist cannot establish a hard bound while page headers and their
declared expansion sizes are parsed during the Arrow read. Safely admitting a strict Parquet subset
would require a bounded pre-reader that validates every page header and row/value count before Arrow
decoding, or an isolated decoder process with an OS-enforced memory limit and bounded output handoff.
The former adds a custom format parser; the latter changes the in-memory verifier architecture and
needs platform-specific process controls. Both exceed this repair's current interfaces and accepted
dependencies, so no weaker assertion or post-allocation check is presented as a fix. The existing
16 MiB per-table and 64 MiB aggregate thresholds remain useful output rejection checks, while footer
totals remain untrusted defense-in-depth checks; neither is a hard peak-memory budget.

L3-F remains **IMPLEMENTED / UNDER REVIEW**, and WP1-S7-01 is **UNRESOLVED**. No R1 regression test
is claimed as passing because the permitted implementation cannot prove prevention of the allocation;
the two prior synthetic reproductions remain the failure evidence. The existing footer-estimate tests
have been named to describe only their pre-read checks. In the isolated sibling worktree, this
targeted command passed 7 tests (167 deselected, 4.87 seconds), confirming footer-estimate rejection
only:

```powershell
python -B -m pytest -p no:cacheprovider tests/test_wp1_inputs.py -k "footer_metadata_and_size_estimates or aggregate_footer_estimate"
```

`python -B scripts/check_docs.py` passed for 328 local destinations/anchors, and `git diff --check`
passed. No R1 allocation-prevention
regression can pass against the unresolved implementation, so the focused compatibility suite, full
suite, lint, format and lock checks were not rerun. Minimum next decision for independent Sol 6.1
review: approve a design amendment for an isolated, OS-memory-limited decoder with a bounded result
handoff, or approve a separately specified bounded Parquet pre-reader. Until that decision and a
passing allocation-prevention regression exist, the snapshot is not READY_FOR_REREVIEW.
Real M/C/H access remains **NO-GO**; H volume segmentation remains **BLOCKED**; L3-C/V/B and L4 remain
separately gated; ADR-028 remains PROPOSED; Phase 13 remains PLANNED / NOT APPROVED; July 4–31 remains
protected.

### WP0-L1 instructor feedback and current delivery boundary — 2026-10-19

Instructor guidance recorded in proposed ADR-028 accepts the existing Store × Date monetary
`Sales` target and 14-day horizon; prefers public access to both API and dashboard using precomputed
forecasts; makes on-demand inference optional; requests multiple monitoring indicators and a
development-only scenario-based model comparison with business interpretation. A matched
cross-model inventory comparison is a bonus. The project owner has not accepted ADR-028, so ADR-024
remains authoritative and public exposure is not approved or implemented.

PR #44 is merged and its Python 3.12/3.14 checks passed, but real-source access/preparation and STL
evidence remain pending. Phase 13 M1–M3 are integrated through PR #40, but Phase 13 remains PLANNED /
NOT APPROVED; no final evaluation or protected-outcome release has occurred. Phase 14 is incomplete.
The current WP0-L1 work changes documentation only and does not run scenario analysis, source
operations, STL, final evaluation, or deployment.

### WP1-L1 fixture-only common population — 2026-10-19

The project owner authorized the WP1 methodology direction and fixture-only L1 implementation,
subject to reuse of the Phase 7 candidate validator, a separate label-only eligibility mask, and
preservation of the sparse observed-target population. L1 adds a pure in-memory builder and synthetic
tests on `feat/wp1-scenario-common-population`; it uses only the three accepted candidates and the
three approved development windows through 2015-07-03.

The focused suite passed 21 tests on the locked Python 3.14.5 environment. The full fixture suite
passed 827 tests with 6 Windows symlink-privilege skips and one existing Starlette/httpx
deprecation warning. Ruff lint, formatting (135 files), Markdown validation (326
destinations/anchors across 36 files), and `git diff --check` passed. No Python 3.12 local run was
performed.

This authorization does not accept ADR-028, execute the full scenario-analysis protocol, or accept
scenario results. No real Rossmann source or cached forecast artifact, protected outcome, inventory
artifact, fitting, recalibration, or Phase 13 operation was accessed or run. L2 metrics/scenario
summaries, safe-input readiness and any L4 analysis remain outside this milestone and separately
gated. Human ownership and course academic-integrity review are required before submission.

### WP1-L1 integration closeout — 2026-10-19

PR #46 was independently reviewed and merged into `main` at
`291660108da0c3d91b065a7dba47beabe1926fae`. Post-merge Quality #149 completed successfully on
Python 3.12 and 3.14 at that exact SHA ([run 39255134029](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/actions/runs/39255134029)).
The L1 common-population builder is REVIEWED / INTEGRATED. Its local feature branch and history are
preserved. Scenario analysis has not run, and no real or protected data was accessed.

### WP1-L2 fixture-only aggregation and serialization — 2026-10-19

L2 is IMPLEMENTED / UNDER REVIEW on `feat/wp1-scenario-metrics-aggregation`, based on the
integrated L1 SHA `291660108da0c3d91b065a7dba47beabe1926fae`. The exact four changed files are the
active WP1 plan, this progress record, `scenario_evaluation.py`, and
`tests/test_scenario_evaluation.py`. L2 adds `summarize_scenario_population`, the
`ScenarioEvaluationResult` container, and the in-memory `serialize_scenario_fixture` API. It
revalidates the 21-column L1 population through the unchanged L1 builder, optionally joins complete
in-memory synthetic metadata by canonical key, and emits five fixed long-form tables: support,
coverage, metrics, comparisons, and unavailability. Default reporting retains all 96 pooled/origin
core strata; known, missing, and observed unrecognized metadata levels are declared without
interactions.

All candidate metrics and the three fixed pairwise comparisons use the same three-way common rows.
Directional errors are `raw forecast - actual Sales`; additive sums use stable float64 summation,
undefined ratios remain null with explicit reasons, and reconciliation checks cover direction
counts, signed/absolute error totals, MAE, and WAPE. The serializer validates schemas, strata,
counts, metrics and comparisons before returning deterministic UTF-8 JSON bytes. No dependencies,
Phase 7 logic, forecast methods, or inventory methods changed.

Focused validation in the locked Python 3.14.5 environment passed **84 tests** across scenario
evaluation (46), Phase 7 metrics (3), and model selection (35). The complete repository suite ran in
a detached sibling worktree at the L1 integration SHA with only the four proposed files copied in;
`data/README.md` was the only tracked data path, and raw, interim, processed, forecast, and inventory
artifact directories were absent. It passed **851 tests**, with **7 skips** and **1 warning** in
206.22 seconds. Six skips were Windows symlink-privilege cases; one optional canonical-artifact test
skipped because ignored artifacts were absent. The warning was the existing Starlette/httpx
TestClient deprecation notice.

Repository checks in that isolated checkout passed: Ruff lint (with `--no-cache`), Ruff format
(135 files), Markdown validation (326 local destinations/anchors across 36 files), `uv lock
--check` (109 packages), `uv pip check` (91 installed packages), and `git diff --check`. An initial
cached Ruff invocation reported an access-denied cache write warning; the no-cache lint rerun
passed cleanly. The locked environment used uv 0.12.23 and Python 3.14.5; no local Python 3.12 run
was performed.

No real Rossmann source, forecast artifact, inventory artifact, or protected outcome was read or
hashed. The L2 implementation generated no forecasts and performed no fitting. The repository
suite ran existing synthetic fixture tests only; no real-data scenario analysis, recalibration,
real inventory operation, or Phase 13 run occurred. Phase 13 remains PLANNED / NOT APPROVED and
the July 4–31 holdout remains protected. ADR-028 remains PROPOSED; ADR-024 remains effective. L2
awaits an independent Sol 6.1 ACCEPT review of this exact diff and required CI before any separately
authorized publication. L3 metadata/source readiness needs its own input authorization; L4 scenario analysis
needs a separate frozen-method execution authorization, independent review, and disclosure. Human
ownership and course AI-assistance/authorship disclosure remain required before submission. No
commit, push, PR, or merge was performed.

### WP1-L2 independent review corrections — 2026-10-19

Sol 6.1's read-only review returned REQUEST_CHANGES with four bounded findings. The local L2
corrections now reconcile the independently accumulated signed-error sum against directional sums
using an ULP allowance derived from component magnitudes; serializer validation requires exact
candidate agreement for each common-population actual-Sales denominator, checks metadata identities
against fixed known domains and missing/unrecognized rules, and bounds missing-Sales and
reason-level unavailability counts by their eligible populations. Exact error sign and zero-match
classification, the common population, metric formulas, comparison identities, and all declared
strata remain unchanged. New regressions cover the 1,001-row cancellation case and material
corruption, non-pooled denominator corruption, malformed metadata identities, valid missing
categories, and both impossible diagnostic subsets.

Validation ran in the detached isolated sibling checkout at base SHA
`291660108da0c3d91b065a7dba47beabe1926fae`, with corrected implementation and tests byte-identical
to this branch. `data/README.md` was the only tracked data path; raw, interim, processed, forecast,
inventory, generated-report, model, and artifact directories were absent. The focused WP1, Phase 7
metrics, and model-selection suites passed **90 tests**; the complete fixture suite passed **857
tests**, with **7 skips** and **1 existing Starlette/httpx deprecation warning** in 221.71 seconds.
Six skips require Windows symlink privileges; the optional canonical-artifact test skipped because
ignored artifacts were absent. After formatting, all **52** scenario-evaluation tests passed again.

Ruff lint and format checks, Markdown validation (**326** local destinations/anchors across 36
files), `uv lock --check --offline` (**109** resolved packages), `uv pip check` (**91** compatible
packages), and `git diff --check` passed in Python **3.14.5** with uv **0.12.23**. No local
Python 3.12 run was performed. No real Rossmann source, forecast/inventory artifact, or protected
outcome was read or hashed; no fitting, scenario analysis, or Phase 13 run occurred. ADR-028 remains
PROPOSED, ADR-024 remains effective, and Phase 13 remains PLANNED / NOT APPROVED with the holdout
protected. L2 remains IMPLEMENTED / UNDER REVIEW pending independent rereview of this exact diff.
No commit, push, PR, or merge was performed.

### CC-02C independent review corrections (2026-10-12)

Independent Sol 6.1 review returned ACCEPT_WITH_MINOR_CHANGES at reviewed head
073f4e9a850df76c34796c3ad68138f9d58f1873. Required finding CC02C-R01 is fixed in
_parse_signed_int64: the existing ASCII signed-decimal grammar is preserved, leading zeros are
removed, signed magnitude bounds are checked before conversion, only the bounded normalized token
reaches int(), and the exact signed-int64 range check remains. Invalid eligible values raise a
sanitized PreparationError. Date classification still excludes rows after 2015-07-03 before
Store or Sales numeric parsing.

Optional finding CC02C-R02 added two fixture regressions without production changes: a receipt write
failure after bundle publication and a late receipt-directory collision. Both verify that the
published two-file bundle remains hash-valid and unbound, unrelated bytes survive, and no active
staging directory remains. The collision test also verifies the pre-existing receipt marker is
preserved and no receipt overwrites it. These cases add failure coverage; the independent review
found no production defect in receipt handling.

Implementation commit e85e814237bd35240d8f44ff427c7e5d9f7205ac is pushed on the existing branch
and Draft PR #43. Focused preparation/provider/STL tests passed 115 tests with two Windows
symlink-privilege skips. A full fixture suite in a clean detached checkout at this commit, with
no data/raw or data/interim, passed 766 tests with three skips and one existing Starlette/httpx
deprecation warning in 252.27 seconds using Python 3.14.5. The skips were the two Windows symlink
tests and the optional canonical-artifact test. An additional synthetic probe passed 5,000-digit
positive and negative overflow, int64 boundaries, zero-padded values, signed zero, and sanitized
error checks. Ruff lint passed; 126 files passed format checking; Markdown validation found 315
local destinations/anchors across 32 files; uv lock --check resolved 109 packages; pip check and
git diff --check passed.

[Quality run 38195056526](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/actions/runs/38195056526)
passed at the implementation commit on Python 3.12 and 3.14, each with 768 passed, 1 skipped,
and 1 warning. The only CI skip was the optional canonical-artifact test. CC-02C remains
IMPLEMENTED / UNDER REVIEW pending focused independent re-review and authorized integration.
No real Rossmann source, prepared partition, protected outcome, real approval binding, real STL
run, or Phase 13 operation was accessed or executed.

### CC-02C integration closeout (2026-10-12)

PR #43 was subsequently accepted and merged into `main` at
`13d762c0c622164ebf6a804ab0a1887c738bdbe8`. Live GitHub metadata confirmed the merge, and
[Quality #141](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/actions/runs/38197240761)
passed on Python 3.12 and 3.14 at that exact merge SHA. The CC-02C fixture implementation is
reviewed and integrated; no real source, partition, approval binding or STL run was created. Its
ordinary task plan is archived under `plans/completed/`.

### CC-02D minimal custodian execution readiness — 2026-10-12

Verified `origin/main` at `13d762c0c622164ebf6a804ab0a1887c738bdbe8` and live post-merge Quality
#141 success at that exact SHA before creating the focused branch
`feat/cc-02d-stl-custodian-readiness`. The missing connection was the absence of any production
path from the fail-closed CC-02C CLI to its byte-snapshot transformation: the accepted preparation
helper accepts bytes only, while the accepted provider separately requires an externally issued
`DevelopmentInputApproval`. CC-02D adds a fixed-source `--execute-once` gate that checks a structured
external packet, exact documented source identity, named account/host, clean procedure commit and
lock hash, expiry, hash-matched source-access/custody/preparation records, and a no-replace
consumption marker before source open. It passes one in-memory source snapshot to the accepted
preparation helper, then stops. It does not create or activate a provider binding or call STL.

The [operator runbook](CC-02D_CUSTODIAN_RUNBOOK.md) defines the fixed packet and GO/NO-GO checklist,
the independently authorized bundle verification, the later exact-hash provider binding, and
separate provider-loading, STL, and findings gates. Python checks packet structure and evidence
hashes but does not authenticate approvers or prove custody; the ADR-027 trusted operator process
remains the authority. No packet or external approval binding was created.

All new execution tests use independently generated synthetic CSV bytes and temporary paths. The
focused CC-02/preparation/provider/STL regression selection passed 124 tests with two Windows
symlink-privilege skips. Full fixture suite: 776 passed, two symlink-privilege skips, one existing
Starlette/httpx deprecation warning in 189.04 seconds on Python 3.14.5. Full-repository Ruff lint
and format, Markdown validation (322 local destinations/anchors across 34 files),
`python -m uv lock --check`, `python -m uv pip check`, and `git diff --check` passed. No actual
Rossmann source bytes were opened or hashed, no partition was generated, and no real provider/STL
execution or Phase 13 operation occurred. The initial implementation/PR-opening checkpoint was
`6ca830060d53bc182b831747e5f5947e5e71640d`. Independent Sol 6.1 reviewed PR #44 at
`93b29f9d4139ef79916bd23f2e3045b620c038eb` and returned **REQUEST_CHANGES** for CC02D-R01–R04;
the focused corrections below address those findings and clarify optional R05/R06. Draft
[PR #44](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/44) remains
IMPLEMENTED / UNDER REVIEW; no merge or real-data operation is authorized.

### CC-02D independent review corrections — 2026-10-12

This correction pass addresses the review checkpoint at `93b29f9d4139ef79916bd23f2e3045b620c038eb`:
R01 adds a non-mutating output preflight before marker creation and source access while preserving
the preparation helper's no-replace publication checks; R02 verifies bounded byte snapshots and
cross-checks the accepted manifest against the preparation receipt without creating a provider
binding; R03 corrects receipt and contract wording; R04 labels earlier SHAs as historical review
checkpoints. The runbook also clarifies environment-derived username hints and separates pre-source
and post-preparation approvals. The current state remains **IMPLEMENTED / UNDER REVIEW** pending
focused independent re-review. Implementation correction commit
`1e14be1a75a32bb4c3ab4265e88e060328eb2d60` contains the R01–R04 fixes, synthetic regressions, and
R05/R06 documentation clarifications. The focused CC-02D/preparation/provider/STL selection passed
154 tests with six Windows symlink-privilege skips. A full fixture suite in a detached checkout at
that commit, with no real source or canonical interim artifacts, passed 805 tests with seven skips
and one existing Starlette/httpx deprecation warning in 183.94 seconds on Python 3.14.5. Six skips
were Windows symlink-privilege cases; the other was the optional canonical-artifact test. The
runbook verifier example also passed against a temporary synthetic partition. Ruff lint and format,
Markdown validation (323 local destinations/anchors across 34 files), `uv lock --check`, dependency
consistency (93 packages), and whitespace checks passed. All execution evidence is synthetic-only;
real source, partition, binding, STL, findings release and Phase 13 remain unauthorized.

### CC-02/CC-02B closeout and CC-02C implementation — 2026-10-12

PR #41 was accepted and merged at `1c83bb4e629b9b8726ea6613a0888e75deb3fbcc`; PR #42 was
accepted and merged at `3efbda248af09231f69a6e461bf5246b2fbb3e3a`. Live GitHub metadata verified
both merge commits and Quality #135 at the PR #42 merge SHA. Quality #135 succeeded on Python 3.12
and 3.14. CC-02/CC-02B fixture implementations are reviewed and integrated. Their real-data
evidence remains pending.

The current CC-02C branch starts from that accepted main SHA. It adds a byte-snapshot transformation
test seam, explicit Arrow int64/timestamp[us] schema, deterministic Parquet settings, the exact
17-field provider manifest, bounded staged publication, an external receipt, and a CLI that
describes the contract or fails closed. Reference labels are inert; preparation does not create a
provider binding or call STL. Synthetic end-to-end tests exercise the existing provider and weekly
STL method only with artificial CSV rows.

The [ADR-027 custody clarification](DECISIONS.md#adr-027--cc-02-development-only-weekly-stl-diagnostic)
distinguishes the custodian's mechanical mixed-source read from provider loading, STL execution and
findings publication. It documents reference reservation versus permission activation and the
trusted-operator/admin boundary. Separate bundle storage and application checks do not prove
OS-level isolation. Source snapshot/custodian approval, mechanical-source authorization, actual
preparation, independent verification and external binding, real STL execution, and findings
publication remain separate owner gates. No real source, combined prepared artifact, protected
outcome, canonical artifact or real STL run was accessed for CC-02C. Phase 13 and the final holdout
remain protected.

Validation at commit `e589232`: focused CC-02C/provider/STL regression suite, 98 passed and two
Windows symlink-privilege skips. Full fixture suite in a clean detached worktree with no raw or
interim data: 749 passed, 3 skipped, 1 warning in 272.37 seconds. The skips were those two symlink
tests plus the existing optional canonical-artifact test; the warning was Starlette's `httpx`
TestClient deprecation. Whole-repository Ruff lint and formatting, 315 Markdown destinations and
anchors, `python -m uv lock --check`, commit whitespace, and the no-source contract-description
command passed. No forecasting/data pipeline or Rossmann file was used. Draft [PR #43](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/43)
is open and mergeable against `main`. Quality #137, run [#38189361426](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/actions/runs/38189361426),
passed on Python 3.12 and 3.14 at pushed head `e872043a000a05cffc733da90e64ad74bdae2383`.

### CC-02 integration and current data boundary — 2026-10-11

PR #41 was independently accepted and squash-merged into `main` at
`1c83bb4e629b9b8726ea6613a0888e75deb3fbcc`. Live GitHub metadata reports the PR merged, and
[Quality #132](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/actions/runs/38147072575)
completed successfully on Python 3.12 and 3.14 at that exact commit. The reviewed method is
integrated; real Rossmann decomposition and its findings remain pending.

CC-02B implements a narrow fixed-path loader that consumes one externally approved immutable
development-only bundle. Its approval object must come from a trusted operator process outside the
bundle. Python validation checks the exact allowlisted path, identifiers/references, hashes,
manifest, schema, ordering, counts and date ceiling; it does not authenticate the approver or prove
physical custody. A distinct custodian procedure must establish physical separation and authorize
mechanical source access before any real partition is prepared or opened. Analytical release and
findings publication are separate gates. This task uses synthetic fixtures only, creates no real
partition, and does not enable the fail-closed CLI. Phase 13 and the final holdout remain protected.

### CC-02B trusted development-only provider — implementation checkpoint 2026-10-11

The implementation branch starts from verified `origin/main` at the PR #41 integration commit
`1c83bb4e629b9b8726ea6613a0888e75deb3fbcc`. The loader accepts only an external approval binding
for `data/interim/cc02_development/<artifact_id>/sales.parquet` and its fixed manifest. It checks
the binding and exact path before file reads; verifies the manifest hash and approval references;
then verifies data bytes, strict schema, counts, sorting and actual dates before returning a
copy-safe three-column frame. Exact Parquet and manifest byte hashes are recorded separately from
the canonical in-memory projection hash in CC-02 provenance. The existing STL API remains the
execution target, and the CLI still rejects filesystem execution.

Validation results are recorded below. [Draft PR #42](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/42)
was opened against `main` for independent review. No Rossmann source, combined prepared train,
final-holdout outcome or existing analytical artifact was opened or hashed for this provider
implementation.

Focused provider plus CC-02 tests passed **61 tests** with **one skip** because this Windows host
does not grant directory-symlink creation; a separate injected reparse-point test passed. The full
fixture suite passed **712 tests** with **two skips** in a detached worktree without local data or
generated artifacts: the same symlink-permission skip and the existing optional canonical-artifact
skip. One existing Starlette/httpx deprecation warning remains. The full run used Python 3.14.5 and
took about 3 minutes 32 seconds. Whole-repository Ruff lint/format, documentation checking (309
local destinations/anchors), `uv lock --check` (109 resolved packages), and whitespace checking
passed. The synthetic integration exercised an 84-row Parquet partition and temporary STL outputs;
no real-data capacity or resource measurement was made. The active branch remains
IMPLEMENTED / UNDER REVIEW.

### CC-02 course-compliance seasonal decomposition — pre-merge implementation checkpoint 2026-10-11

The focused branch `feat/course-cc02-seasonal-decomposition` starts from verified live
`origin/main` at `1426f29878fd8d7aaa920482310c02842498198b`; the prior local tracking ref was stale.
CC-02 adds robust weekly STL (`period=7`) as a retrospective EDA diagnostic over finite contiguous
Store/Date/Sales segments through 2015-07-03. It requires 56 days, caps the most recent eligible
segment at 112 rows, and chooses the first three eligible Store IDs in ascending order. Missing
calendar dates and missing/non-finite values split segments, observed zeros remain, and the
components are checked to reconstruct observed Sales. The diagnostic is not a forecast, causal
result, feature, model-selection input, or Phase 13 operation. See the [completed CC-02 plan](../plans/completed/cc-02-seasonal-decomposition.md)
and [ADR-027](DECISIONS.md#adr-027--cc-02-development-only-weekly-stl-diagnostic).

The dedicated command only describes the trusted-input contract or fails closed. It has no source
path or bypass option and opens no data; actual API use requires an already-authorized in-memory
frame. Before any real run, a separately approved provider must prove physical separation from the
combined prepared artifact and protected period, establish the cutoff before opening/hashing data,
and carry a reviewable owner-approved preflight reference. No such provider is configured here.

Focused synthetic tests passed **20/20**. The full fixture suite passed **671** tests with **one
skip** for a canonical artifact-dependent test in an isolated clean worktree with no source or
prepared artifacts; one existing Starlette/httpx deprecation warning was reported. Whole-repository
Ruff lint/format, 304 Markdown destinations/anchors, `uv lock --check`, and `git diff --check`
passed. An 84-day synthetic figure was visually inspected; maximum absolute reconstruction error
was approximately `2.3e-13`. Generated synthetic component/figure/manifest outputs stayed in
temporary directories. No Rossmann source, combined prepared artifact, holdout outcome, EDA pipeline,
model, or Phase 13 command was read or run.

The original CC-02 implementation commit is `46cb013506a6b2f35335beb07ba0f22f72af74df`.
[Draft PR #41](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/41) is the
canonical link for its live head and review state; this record does not pin a changing branch head.
**State:** CC-02 is IMPLEMENTED / UNDER REVIEW on the focused branch. Merge and Phase 13 closeout
are not authorized by this task.

### CC-02 independent review and focused corrections — pre-merge checkpoint 2026-10-11

The independent Sol 6.1 review covered PR #41 at head
`d5f27e5981fd4303fdf8318aff7074ce6c3b0d8e` and returned `ACCEPT_WITH_MINOR_CHANGES`. On the same
branch, the exporter now rejects occupied destinations and publishes its manifest by atomic
replacement; manifest metadata distinguishes direct Python API execution from a caller-supplied
invocation; and figures label synthetic or development-only inputs. The original implementation
commit remains identified above. Use [Draft PR #41](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/41)
for the live head; independent follow-up acceptance is pending.

The focused synthetic suite passed **25 tests**. The full fixture suite passed **676 tests** with
**one skip** for an artifact-dependent test in a detached worktree without Rossmann source or
generated artifacts; the existing Starlette/httpx deprecation warning remains. Whole-repository Ruff
lint/format, documentation links, `uv lock --check`, and `git diff --check` were rerun for these
corrections. No Rossmann source, protected outcome, EDA pipeline, model, or Phase 13 operation was
accessed or run. The revised 84-day synthetic figure was rendered and visually inspected; its title
identifies it as a synthetic fixture, its four panels remain legible, and maximum absolute component
reconstruction error was approximately `2.3e-13`.

**State:** CC-02 remains IMPLEMENTED / UNDER REVIEW. Merge and Phase 13 closeout remain unauthorized.

At closeout start, the clean `docs/phase-5-closeout` branch was created from fetched latest
`origin/main`; both resolved to `76707a03b7d10dbaa79d3ef26b39e31994431d70`, the actual PR #7
squash-merge commit reported by GitHub. PR #7 is merged into `main`. The merged tree contains the
reusable Holt-Winters forecaster, development runner, evaluation code, and tests. The closeout
changes lifecycle/documentation only: no forecasting algorithm or historical metric is changed, and
no final-holdout forecast or evaluation was performed. Main protection was reported disabled in
the 2026-10-05 branch-metadata snapshot; no settings were changed.

Completed plans under `plans/completed/` preserve their historical approval/results/checkpoint
records, including the [completed Phase 5 plan](../plans/completed/phase-5-statistical-forecasting.md).
PROGRESS is the canonical maintained numerical-results record; duplicated plan tables are dated
snapshots, not separate results to update. Phase 7's development-only selection is integrated and
formally closed. Its result and closeout do not constitute final-holdout evaluation or production
approval. Phase 8 methodology is approved in ADR-021; implementation PR #15 and results-acceptance
PR #16 are integrated, and the external results review accepted the canonical development run.
Fit B values are frozen for that run. Phase 8 is COMPLETE following the explicit closeout recorded
below and in the completed plan. Phase 9 is COMPLETE after PR #19 integration, accepted independent
implementation and numerical review, and formal closeout. Its accepted canonical run and manifest
are recorded below and were not regenerated. Phase 10 methodology is accepted under ADR-023. PR #23 integrated the implementation at
`15bce83cd63a4edfeed6defb95788da90d0f36d9`; corrective PR #24 integrated the B1-B3 fixes at
`fcbf6b7de79d57bb7db8a965d5a2b78e9376a3a9`. Final focused independent external/model-assisted review
accepted the implementation and numerical evidence. Closeout PR #25 was squash-merged into `main`
at `d437269b9f0cf36a842cdfd496ad50a310804768`; Phase 10 is COMPLETE. Phase 11 is COMPLETE after
PR #26 squash-merged into `main` at `725d30a59d7c8e04e44f3bcbcce9186f8a1183be`; M1-M4 are accepted,
M3-01, M4-01 and FR-01 are resolved, and post-merge Quality #81 passed. The [completed Phase 11
plan](../plans/completed/phase-11-application-services.md) preserves its acceptance and handoff
record. The protected final holdout remains unreleased.

### Phase 11 formal closeout — 2026-10-09

The Technical Lead authorized documentation-only formal closeout after verifying PR #26's squash
merge into `main` at `725d30a59d7c8e04e44f3bcbcce9186f8a1183be`. The original feature branch was
`feat/phase-11-application-services`, and the final reviewed PR head was
`77128a3b589cbe662833962cd20aacb03241dd55`. M1-M4 are accepted; independent reviews returned M1
`ACCEPT`, M2 `ACCEPT`, M3 `ACCEPT_WITH_MINOR_CHANGES`, M4 `ACCEPT_WITH_MINOR_CHANGES`, and the final
full-PR merge-readiness review returned `READY_WITH_MINOR_CHANGES`. Findings M3-01, M4-01 and FR-01
were resolved before merge. All implementation and integration gates are satisfied.

Post-merge GitHub Quality [#81](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/actions/runs/37902479835)
passed at the squash merge SHA on Python 3.12 and 3.14. The previously accepted baselines were 431
full-suite tests and 151 focused application tests. For this closeout, the full suite was rerun and
431 passed; the 151-test focused subset was not rerun. The nonblocking Starlette TestClient
deprecation warning remains. Earlier accepted Quality #80 evidence and milestone checkpoints remain
recorded in the archived plan and historical entries below.

The application serves saved development forecasts without new inference. Historical access ends on
2015-07-03 and projects only Store, Date, Sales and Open; Customers are not exposed. Sales are
monetary turnover; saved uncertainty is empirical without guaranteed coverage; inventory outputs
are conditional synthetic monetary simulations, not observed physical inventory, actual stockouts,
proven savings or validated optimal policies. Positive forecast-minus-baseline simulated cost is
adverse: the accepted reference difference is +1,842,931.0502027555 and `buffer_090` is
+2,657,553.7797287568, both existing results and not new calculations. The protected July 4-31
holdout remains unreleased. The Phase 10 simulation ledger and canonical artifacts were not read,
hashed, regenerated or changed. No real-data forecast fit, final-holdout evaluation, recalibration
or canonical simulation/artifact regeneration was performed; the closeout repository test run used
the fixture suite. Phase 12 and Phase 13 remain outside this authorization.

### Phase 12 architecture audit and design proposal — 2026-10-09

The authorized task is design documentation, commit/push and a draft PR only. The worktree was clean
on the already merged `docs/phase-11-closeout` branch. Fetch and live GitHub metadata verified
`origin/main` at `2a47ae7dd959daac8eacf2b5410f090edbbcd7cb`, the actual PR #27 Phase 11 closeout
merge; all 27 existing PRs were merged and none open. The new `docs/phase-12-streamlit-design`
branch starts directly from that main SHA. Phase 11 remains COMPLETE.

The [Phase 12 plan](../plans/completed/phase-12-streamlit-dashboard.md) audits the existing
reader/service/API contracts and tests, proposes five screens using direct `ApplicationServices`
calls, and separates the seven candidate content sections into implementation-ready specifications.
Four proposed milestones have bounded Luna 6 task/review boundaries. Public service DTO omissions
limit richer EDA, calibration diagnostics, structured case selectors and operational parameters;
the core proposes bounded Sales/Open history and saved-case comparisons. It explicitly records
the narrower scope relative to proposal §22 for Technical Lead review without editing the proposal.

Deployment remains undecided; private course LAN is one candidate, subject to later approval that it
satisfies the course requirement. Private canonical-file cloud
provisioning and a separately reviewed reduced DTO evidence snapshot are alternatives, each requiring
additional distribution/contract approval. A clean checkout or synthetic fixtures cannot substitute
for accepted analytical evidence. No source, API, service, model, simulation, dependency or canonical
artifact changed; no canonical artifact contents, ledger or protected outcomes were read/hashed.
Design-task checks passed on Python 3.14.5 / uv 0.12.23: 151 focused application tests and all
431 fixture tests, Ruff lint/format, 259 local documentation destinations/anchors, lock consistency
and installed dependency compatibility, plus diff/scope self-review. The existing nonblocking
Starlette TestClient deprecation warning remains. Detailed check scope is recorded in the active
plan; no Streamlit implementation, UI test or deployment was performed.

At the end of that original design task, Phase 12 was **PROPOSED / AWAITING REVIEW**. That historical
boundary was superseded by the later M1 authorization recorded below; Phase 13 and Phase 14 remain
future work, and the holdout is unreleased.

### Phase 12 M1 implementation checkpoint — 2026-10-09

Technical Lead authorization followed verification that design PR #28 was merged into `main` at
`9b4ab7f54abff0ca1abfe8b6c547de960c8be8b1`. M1 is limited to the Streamlit shell, static overview
and catalog/readiness presentation, pure display helpers, sanitized UI errors and fixture-backed
tests. The other four screens remain data-free placeholders and make no service queries. The
optional dashboard extra is used only by the dashboard and AppTest suite; pandas/matplotlib remain
the visualization foundation. Deployment is undecided, the proposal's interactive what-if scope is
excluded from M1–M3, and M2–M4 and Phase 13 remain unauthorized. No holdout or ledger access is
authorized.

Implementation branch: `feat/phase-12-streamlit-m1`, based directly on the verified merge SHA above.
M1 is IMPLEMENTED / UNDER REVIEW only; it is not accepted, merged or a Phase 12 closeout. The
focused UI/presenter tests passed (13 before the final empty-checkout test was added); the final
suite includes 14 dashboard tests. Whole-repository pytest passed with 445 tests on Python 3.12 and
445 on Python 3.14, each with one existing Starlette/httpx deprecation warning. The 3.12 run used a
locked isolated uv environment; the 3.14 run used the locked project environment.

Ruff lint and format checks passed (102 files formatted), documentation links passed (259 local
destinations/anchors across 27 Markdown files), `uv lock --check` passed with 109 resolved packages,
and `uv pip check` passed with 93 compatible installed packages. The dashboard extra resolves
Streamlit 1.65.0 under `streamlit>=1.50,<2`. AppTests use temporary fixture roots; the empty-checkout
case renders static content and unavailable statuses without provenance, while the corrupt-catalog
case displays a fixed integrity error without a local path. Navigation tests confirm that only the
overview calls `catalog()` and its reader opens only the Phase 9 scenario catalog and Phase 10
comparison output. No manual browser/performance test, real-data pipeline, deployment, canonical
artifact regeneration, ledger access or protected holdout access was performed.

The feature branch is pushed in [draft PR #29](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/29)
targeting `main`; the final task report records its current head SHA. M2–M4 remain unauthorized;
do not merge or start subsequent work.

### Phase 12 M1 independent review corrections — 2026-10-09

The narrow corrective task addresses review findings M1-01 through M1-03 on the existing PR #29
branch. M1-01 adds an explicit **Refresh resource status** button to Overview. Each click reruns
the existing `catalog()` service under its existing lock and reader validation; no new application
cache or inference/artifact-generation path is introduced. An AppTest removes a fixture scenario
artifact, verifies the unavailable state, restores its original bytes, clicks refresh, and verifies
recovery and provenance. The reader spy confirms each run reads only the Phase 9 scenario catalog
and Phase 10 comparison resources.

M1-02 moves both resource-readiness and provenance conversions inside a sanitized presentation
boundary and completes both before emitting resource tables/status cards. Invalid injected resource
and provenance DTOs each render the fixed `internal_error` notice with no partial table or path.
The existing `ArtifactReadError` mapping is unchanged. M1-03 replaces catalog-specific shared error
copy with resource-neutral language. Table-driven tests preserve all stable error codes and distinct
unavailable, integrity, schema, duplicate-key, unsupported-selector, invalid-request and unsafe-path
messages without raw exception details. Focused dashboard/presenter tests pass (**24 passed**).

Whole-repository pytest passed on Python 3.12 and 3.14 (**455 passed each**) with the existing
Starlette/httpx deprecation warning. Python 3.12 used the locked isolated uv environment with dev,
API and dashboard extras; Python 3.14 used the locked project environment. Ruff lint and format
passed (102 files formatted), documentation links passed (259 local destinations/anchors across 27
Markdown files), `uv lock --check` passed (109 resolved packages), `uv pip check` passed (93
compatible installed packages), and `git diff --check` passed. No dependency or lockfile changed.

GitHub's Python 3.12/3.14 Quality result and PR metadata are verified after the corrective push and
reported in the final task handoff. M1 remains IMPLEMENTED / UNDER REVIEW; PR #29 remains draft and
unmerged. No model inference, canonical artifact generation, real-data pipeline, ledger access,
protected holdout access or deployment occurred.

### Phase 12 M1 integration and M2 implementation checkpoint — 2026-10-09

PR #29 was accepted and squash-merged into `main` at
`cb508a0bbdefe6afeba6e1ea8ebad5a0614a03f6`. The reviewed M1 head
`2460b3d59ef1fce90702719c59501e84dd5f36af` has the same Git tree as the merge. The conditional M2
authorization gate is satisfied. Branch `feat/phase-12-streamlit-m2` starts directly from that main
SHA. M1 is ACCEPTED / INTEGRATED; M2 is IMPLEMENTED / UNDER REVIEW. This does not close Phase 12.

M2 implements the Historical Sales and Forecast Explorer/uncertainty screens from the approved
plan. The UI uses only `catalog()`, `sales_history(HistoryQuery)`,
`forecast_issuance(ForecastQuery)` and `forecast_uncertainty(UncertaintyQuery)` with the existing
DTOs. It adds no service, model inference, analytical producer change, metric, inventory assumption,
dependency or lockfile change. History validates Store/date bounds before dispatch and distinguishes
observed zero, null and missing calendar dates. Forecast output is saved H14; H7 filters display
only. Raw/operational availability stays separate. Fit A/June 5 and Fit B/June 19 map from the
catalog; May 22 sends no uncertainty request. Daily and cumulative saved values, unavailable
reasons and their separate provenance are retained without recalculation or rounding.

The UI labels history as retrospective development evidence, displays source Open separately,
describes operational routing as a conditional historical replay, and exposes empirical/sparse
uncertainty limitations. It does not access Customers, model-comparison results, inventory ledgers,
or July 4–31 protected outcomes. M3/M4 remain NOT AUTHORIZED, deployment remains pending, and the
Phase 13 holdout remains protected.

Focused dashboard/presenter/M2 tests passed (**64 passed**). The full fixture suite passed on Python
3.12 (**495 passed**) and Python 3.14 (**495 passed**); each run reported the existing
Starlette/httpx deprecation warning. Ruff lint/format passed (103 files already formatted),
`uv lock --check` passed with 109 resolved packages, and `uv pip check` passed with 93 compatible
packages. `scripts/check_docs.py` passed with 259 local destinations/anchors across 27 Markdown
files, and `git diff --check` passed. Git emitted configured LF-to-CRLF normalization notices for
modified files.

The optional read-only development smoke used Store 1, history 2015-06-19–2015-07-03, the June 19
H14 forecast and Fit B uncertainty. It returned 15 history rows, 14 forecast rows (14 raw and 14
operational available), 28 daily interval rows and 42 cumulative rows, with the service's saved
provenance. No source values were printed, no artifact was changed or regenerated, and the Phase 10
ledger and protected holdout were not accessed. No manual browser, performance or deployment test
was performed.

## Current boundary

Phases 0–12 are COMPLETE; Phase 13 M1–M3 are integrated, but Phase 13 remains PLANNED / NOT
APPROVED and the protected July 4–31 holdout remains unreleased. The [active Phase 13 plan](../plans/active/phase-13-sequential-final-evaluation.md)
records methods under ADR-026 and the owner's A-bounded scope under ADR-025. Independent M3 review,
source/preparation preflight, development rehearsal, protected-source staging, analytical release,
M4 and later milestones remain separately gated; Phase 14 is incomplete. ADR-028 is proposed only;
ADR-024 remains the approved localhost-only boundary until the owner accepts a superseding decision.

### Phase 13 M0.1 methodology review checkpoint — 2026-10-10

PR #34 merged the initial documentation proposal into `main` at
`4f2f9dc407109efea8401ff3b19894e104ad764e`; this SHA is the verified `origin/main` base for the
current methodology-review branch. The independent Sol 6.1 review covering P13-01–P13-09 is
incorporated into the active M0.1 design proposal. This remains a review checkpoint, not a
methodology acceptance: P13-01–P13-08 remain pending approval, Option B is only a Technical Lead
recommendation with owner approval pending, and no accepted ADR or normative Proposal/Project Plan
change is made. Phase 13 remains PLANNED / NOT AUTHORIZED. This documentation task did not
implement or run Phase 13, stage/extract/hash protected source content, access July 4–31 outcomes,
or perform future-data extraction.

### Phase 13 M0.2 Option A-bounded feasibility checkpoint — 2026-10-10

The owner prefers including simulated inventory evaluation in Phase 13. The independent Sol 6.1
feasibility review recommends Option A-bounded: two independent July H14 origin-frozen standing-
target episodes on the July 3 and July 17 primary origins, retaining the accepted Phase 10 policy
pair and full precommitted scenario/sensitivity panel. This is a recommendation, not methodology
or acceptance approval. Two fixed targets do not provide fresh forecast-supported protection
coverage for every later daily review and do not demonstrate continuous calibrated 28-day inventory
operation. The active plan records the required roadmap acceptance clarification, proposed schedule
and Fit B transport decisions, context provenance, panel volumes/resource gate, fixture oracles,
and separate rehearsal/release gates. No accepted ADR, Proposal, or Project Plan is changed.
Phase 13 remains PLANNED / NOT AUTHORIZED; no implementation, real-data modeling or simulation,
July context generation, protected-source staging, holdout access/hash, or outcome release occurred
in this checkpoint. P35-01/P35-02 corrections remain in the existing PR head; Technical Lead
acceptance is pending.

### Phase 13 M0.3 owner scope approval — 2026-10-10

PR #35 merged into `main` at `2d34e20d5ae9fdb29af610dd28aefd3b80023946`; post-merge Quality
[#111](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/actions/runs/38059767105)
passed on Python 3.12 and 3.14. On 2026-10-10 the owner explicitly approved Option A-bounded
inventory scope and its daily-protection limitation only. New ADR-025 records that scope-only
decision. The M0.3 revision synchronizes the Phase 13 acceptance boundary in PROJECT_PLAN and
PROPOSAL: two independent H14 origin-frozen episodes use the July 3 and July 17 origins; later
daily reviews execute the existing targets without claiming fresh calibrated protection coverage;
the episodes do not establish continuous rolling 28-day inventory operation. The full
precommitted scenario/sensitivity panel remains subject to a resource-feasibility gate.

P13-05 inventory scope is approved by the owner; detailed execution methodology remains pending.
P13-01's detailed issue/release protocol and P13-02/03/04/06/07/08 remain pending Technical Lead
review/approval. Implementation, development rehearsal, protected-source staging, and analytical
release retain separate authorizations. Phase 13 remains PLANNED / NOT IMPLEMENTED; M1 is NOT
AUTHORIZED. No model fit, simulation, July context generation, protected-data access, staging,
holdout release, or canonical artifact operation occurred for M0.3. The scope-only ADR does not
approve remaining Phase 13 methodology.

### Phase 13 M0.4 selected methodology checkpoint — 2026-10-10

M0.4 records the delegated Technical Lead's selected Phase 13 methods in new ADR-026 on branch
`docs/phase-13-m04-methodology-freeze`, created from verified `origin/main` SHA
`66b2019ad19958e414e51bd9c5799d08809f0424` (PR #36 merge;
post-merge Quality #113 passed). The selected protocol retains two complete H14 blocks, the
1,115-store/29-feature input schema, conditional origin-safe covariates and synthetic weekly
planning schedule, A2 logical/operator-enforced custody, unchanged frozen June Fit B transport as
unvalidated, ADR-025 A-bounded inventory, descriptive monitoring with deterministic integrity/data
alerts only, the pinned Windows/Python 3.14 tolerance, and LightGBM with frozen Seasonal Naive
contextual issuance. The M0.4 plan records exact statuses and gates; PROPOSAL and PROJECT_PLAN were
updated where needed to reflect selected monitoring and input/custody methods and remove
contradictions.

Source identity, historical-availability provenance, safe acquisition/preparation, operator and
prior-partition provenance, and full-panel resource approval remain execution preconditions. If
required covariates exist only in a combined source containing protected Sales/Open, a separately
reviewed safe-preparation/custody procedure is required before any source access; column projection
alone is not physical isolation. M1, development rehearsal, mechanical staging, and analytical
release each remain separately authorized gates. Phase 13 remains PLANNED / NOT IMPLEMENTED, M1 is
NOT AUTHORIZED, and the final holdout remains UNRELEASED. No implementation, fit, simulation, July
covariate extraction, protected-source/outcome access or hashing, staging, analytical release, or
canonical artifact regeneration occurred for M0.4. The method-freeze Draft PR is pending Technical
Lead review.

### Phase 13 M1 synthetic input contracts and providers — 2026-10-11

The owner authorized M1 only, using synthetic fixtures, on a fresh branch from the verified PR #37
merge SHA `3bebca61ea8eb8b1eefadbc752e7d278afc0cc35`. The branch is
`feat/phase-13-m1-safe-providers`. PR #37 is merged; post-merge Quality #116 passed on Python 3.12
and 3.14. This does not change the selected ADR-026 method or approve Phase 13; M2 remains
unauthorized.

M1 adds typed contracts for the two origins and H14 grids, origin-censored training rows, sparse
recursive history, exact frozen future covariates, calendar-generated synthetic planned Open, and
one-date outcome projections. The input provider exposes only bound training/history/covariate
sources and the separate synthetic schedule. A distinct outcome provider requires a matching
synthetic date token and chronological access. Block 2 views can include only ordered released
Block 1 fixtures with the matching issued covariates. The in-memory reader accepts only recognized
`memory://phase13/...` fixture references; returned frames are copies and missing keys are not
filled.

Focused M1 tests passed **22 tests**; the repository fixture suite passed **558 tests** on Python
3.14.5 with one existing Starlette/httpx deprecation warning. Ruff lint and format, the documentation
checker (298 local destinations/anchors across 29 Markdown files), `uv lock --check` (109 packages),
and `git diff --check` passed. Draft PR #38 is open and unmerged pending independent review. No
model fit or forecast issuance, July context generation, real-data provider, filesystem source, staging, outcome release, or
canonical artifact operation was implemented or run. No real or protected Rossmann data was read,
loaded, staged, extracted, or hashed. M1 is IMPLEMENTED / UNDER REVIEW; independent review and
acceptance remain pending. Source/preparation provenance, operator, resource, rehearsal, staging,
and analytical release gates remain open. M2 is NOT AUTHORIZED; STOP here pending Technical Lead
review.

### PR #38 Technical Lead corrections P38-01–03 — 2026-10-11

M1 corrections on the existing Draft PR branch harden the synthetic provider boundary. `SyntheticInputProvider._read()` now checks role, capability, typed source binding, safe memory reference, and a fixed role-to-column schema before calling the injected reader; requested columns cannot define their own expected schema. The synthetic Block 1 handoff is now created only by `SyntheticOutcomeProvider` after the exact 14 Block 1 dates have been successfully authorized and read in order. It is registered to that provider's in-memory release state and bound to the matching Block 1 Store grid, covariate identity, and provenance. A handoff rejects forged projection collections and cannot include Block 2 outcomes; projection frames are returned as independent copies. `SyntheticPlannedOpen` validates each supplied non-null value against Monday–Saturday open/Sunday closed while preserving nullable unknowns, missing rows, independent actual Open, and positive observed Sales.

The focused Phase 13 input suite passed **30 tests**; the repository suite passed **566 tests** on Python 3.14.5 with one existing Starlette/httpx deprecation warning. Ruff lint and format, documentation checks, `git diff --check`, and `uv lock --check` passed. These tests exercise logical in-memory behavior with artificial fixtures and do not establish physical isolation. No real or protected Rossmann data was read, loaded, staged, extracted, or hashed; no model fit, protected-source operation, M2 work, or canonical artifact operation occurred. The correction is for Technical Lead re-review on Draft PR #38; Phase 13 remains PLANNED / NOT APPROVED and M2 remains NOT AUTHORIZED.

### Phase 13 M2 synthetic fresh-fit issuer — 2026-10-11

M1 PR #38 merged into `main` at `6e7d11a29a593c5eddee640f7c44ca1b3b9cd923`. GitHub post-merge
Quality #120 passed both Python 3.12 and 3.14 jobs on that exact SHA. This satisfied the explicit
precondition for the owner's M2 authorization. The M2 branch is `feat/phase-13-m2-fresh-fit-issuer`,
created from that SHA; M2 remains IMPLEMENTED / UNDER REVIEW and Phase 13 remains PLANNED / NOT
APPROVED.

`rossmann_forecasting.phase13.issuer.Phase13FreshFitIssuer` accepts only M1's typed synthetic input
provider. It builds historical features from valid observed Sales rows only, preserving exact-date
closed-day zeros and excluding missing-label rows without filling them. It uses the approved Phase
3 feature pipeline and Phase 6 LightGBM interfaces, plus `build_refit_recipe` from Phase 7, for a
fresh exact Trial A fit at each of the two approved origins. Before recursion it checks fit origin,
parameters, eligible row count, category vocabulary, feature schema, and actual tree count.

The M2 input-validation contract reconciles training and recursive-history Sales only on overlapping
canonical `(Store, Date)` keys after the M1 contracts' numeric normalization. It requires exactly
equal observed values and matching observed/missing status; valid zero observations remain intact,
and non-overlapping sparse history is neither required nor filled from training. It does not
substitute values between views and retains separate training and history identities. A mismatch
raises the stable, non-sensitive `Phase13IssuanceError` message before feature construction, dataset
creation, fitting, recursion, or M2 issuance identity construction. Synthetic tests cover
non-zero disagreement (including a `1e-9` difference), closed-day zero disagreement, normalized
matching zero, sparse history, missing training labels, Block 2 handoff inputs, and no new outcome
reads during the check.

The in-memory, label-free `RawForecastIssuance` retains one record per requested Store × Date key,
including raw clipped and unclipped values, recursive state, clipping/category diagnostics,
identities, availability and explicit failure reasons. It accounts for incomplete paths separately
from all-requested-key coverage. Missing predictions remain null; no fallback or numerical
fabrication is used. No planned Open, actual future Open, Customers, future outcomes, or release
provider is read for raw issuance. The result is not a durable or formally published final
issuance.

The focused issuer suite passed **20 tests**. Block 1's synthetic fixture has 1,098 input rows,
1,097 valid labels, one excluded missing label, 156 observed closed-day history rows, and 941
eligible fit rows. Its fresh fit produced 180 trees and 28 available of 28 requested keys. The
verified Block 2 fixture has 1,126 input rows (including only the 28 released Block 1 outcomes),
1,125 valid labels, one excluded missing label, 160 observed closed-day history rows, and 965
eligible fit rows; its fresh fit also produced 180 trees and 28 available of 28 requested keys.
The incomplete-input adversarial fixture accounted for all 28 keys, with 26 available and two
explicitly unavailable for a missing key and required covariate. A fit-failure fixture accounted
for all 28 keys as unavailable with reason `model_fit_failure` and no numeric values. Block 2's
release provider reads the 14 authorized synthetic Block 1 dates to create its verified handoff;
issuance itself makes no additional outcome reads, and changing unreleased Block 2 outcomes does not
change issuance.

The booster save/load test writes only under pytest's temporary directory. It preserves category
vocabulary and order, recipe/origin/schema identity and 180-tree count; same-input predictions pass
the frozen `rtol=1e-12`, `atol=1e-9` comparison. The full fixture suite passed **586 tests in
167.44 seconds** (168.85 seconds measured command wall time), with one existing
`StarletteDeprecationWarning` about `httpx`/`starlette.testclient`. The focused suite passed 20
tests. Ruff check and format, `scripts/check_docs.py` (299 local destinations/anchors across 29
Markdown files), `uv lock --check` (109 locked packages), and `git diff --check` passed.

The measured environment is Windows 11 `10.0.26300-SP0`, AMD64, 12 logical CPUs; Python 3.14.5
(MSC v.1944 64-bit), LightGBM 4.7.0, NumPy 2.5.3, pandas 3.0.6, and uv 0.12.23. `uv.lock` SHA-256
is `151CD5A2A868B219D315D8333D75D54E8C1F7EFA43AFA0869933A5682852DBD`; the LightGBM native DLL
SHA-256 is `7E366D2E49CD061AAC3AB21676B2F99B0C7A758DC3E888D4B23812AF1B7D301C`. Draft PR #39 is open; its GitHub Quality run is tracked on the PR. The base's post-merge Quality #120 on Python 3.12 and
3.14 passed at the verified M1 merge SHA.

No Rossmann source, protected July outcomes, source file, accepted real-data model, or canonical
artifact was read, hashed, loaded, or changed. No July covariate extraction, source preparation,
real-data fit, June Fit B transport, planned-Open routing, inventory work, durable release journal,
M3, or later milestone was implemented. Source/preparation provenance, operator, rehearsal,
staging and analytical-release gates remain open.

### Phase 13 M3 synthetic uncertainty and target adapters — 2026-10-11

M2 PR #39 merged into `main` at `2a935aea30ab22110153d33d3a55dac44e67a1c8`. Post-merge Quality
#125 passed on Python 3.12 and 3.14 at that exact SHA. The M3 branch
`feat/phase-13-m3-frozen-uncertainty-targets` is based on that verified `origin/main`; M3 is
IMPLEMENTED / UNDER REVIEW. Phase 13 remains PLANNED / NOT APPROVED.

`rossmann_forecasting.phase13.adapters` adds a synthetic-only M3 boundary. It accepts an in-memory
M2 `RawForecastIssuance`, M1's typed synthetic planned-Open schedule, independently generated
synthetic Fit B-shaped quantile fixtures, and a synthetic mean anchor. Static, documented Fit B
metadata is retained as calibration identity; hashes generated by the fixtures identify only
artificial table content. The canonical Fit B loader fails closed. Calibration identity and model
fit identity remain separate, and June-to-July Fit B transport is explicitly unvalidated.

Daily intervals apply the exact signed Fit B endpoint errors at 0.025/0.975 for horizons 1–14,
requiring n ≥ 40 and the frozen 1-indexed ranks floor((n+1)/40) and ceil(39(n+1)/40). Cumulative
quantiles use complete planned-open operational prefixes k=1–14 and p={0.90, 0.95, 0.98}, requiring
n ≥ 50 and rank ceil((n+1)p). Quantiles are not refit, interpolated, borrowed across horizons or
prefixes, or replaced with fallback values. Raw points/intervals are preserved; planned closures
route operational point and interval values to zero, and unknown schedule values stay unavailable.

The target adapter applies the frozen Phase 10 equations for both policies and every L=2…7 with
R=1 and P=L+1: baseline target = historical open-day mean × planned-open days; forecast demand D
is the sum of operational point values; upper protection value U=max(0,D+q); safety value
max(0,U−D); target=max(D,U). Baseline anchor and forecast availability remain independent, and
each origin freezes its paired target set across H14.

The focused M3 synthetic suite passed **47 tests in 12.08 seconds**. It covers both July origins,
H14 ordering and M2 identities, schedule closure/unknown/sparse rows, signed daily and cumulative
quantiles, sample floors/ranks and reasons, unsupported-prefix behavior, identity separation,
metadata and hash validation, no-fit/no-borrow behavior, Phase 10 targets, independent availability,
and no future outcome reader calls. The full fixture suite passed **633 tests in 172.41 seconds**
on Python 3.14.5, with one existing Starlette deprecation warning about `httpx` and
`starlette.testclient`. Repository Ruff checks passed (`ruff check .`; 115 files formatted),
`scripts/check_docs.py` passed with 301 local destinations/anchors across 29 Markdown files,
`uv lock --check` resolved 109 locked packages, and `git diff --check` passed.

No real or protected Rossmann data, canonical Phase 8/9 artifact, or future outcome was accessed or
hashed. No source preparation, staging, rehearsal, analytical release, M4 publication/replay, or
later milestone is included. Independent Technical Lead review is the next boundary; the final
holdout remains unreleased.

### Phase 13 P40-01/02/03 synthetic M3 corrections — 2026-10-11

On the existing Draft PR #40 branch, P40-01 replaces the broadcast synthetic historical mean with
a typed collection bound to `(Store, origin)`. Duplicate/cross-origin/out-of-universe anchors are
rejected, the Store universe and issuance origin must match, and sparse missing anchors remain
unavailable without filling or cross-Store borrowing. Per-Store values, status, identity, and
synthetic provenance are captured in the collection identity and target rows. Synthetic golden
coverage checks Store 1 mean 100 and Store 2 mean 500 across two planned open days (baseline targets
200 and 1,000), as well as Store-local unavailable, zero, missing-key, duplicate-key, wrong-origin,
and no-borrow cases.

P40-02 enforces equal daily lower/upper calibration counts at each horizon and equal cumulative
complete-prefix counts across all probabilities at each prefix. Frozen rank equations, n floors,
availability reasons, and independent per-probability quantile values remain unchanged. The
nonfinite-quantile test uses a consistent common-n prefix; an n=49 prefix marks every probability
unavailable with `insufficient_calibration`. Adversarial fixtures with contradictory counts across
tails or probabilities are rejected.

P40-03 makes `OriginFrozenStandingTargets` validate the supported origin, SHA-256 issuance and
anchor-collection identities, exact output schema, forbidden outcome fields, complete unique
`(Store, origin, L, R, P, p, policy)` combinations, per-Store anchor binding/provenance, explicit
Boolean availability, and target value/reason consistency. Forgery tests reject duplicate keys,
missing policy rows, wrong origin, negative/null available targets, reasons on available targets,
numeric unavailable targets, and mismatched row identity. The focused suite now passes **66 tests**
on Python 3.14.5; the prior valid M3 cases remain represented with constructors and sample-count
fixtures updated to the tightened contracts. The full repository suite passes **652 tests** in
178.29 seconds on Python 3.14.5, with one existing Starlette/httpx deprecation warning. Ruff lint
passed; all **115 files** pass Ruff format; documentation validation passed with **302 local
destinations/anchors across 29 Markdown files**; `uv lock --check` resolved 109 packages; and
`git diff --check` passed. The focused suite passed in 18.35 seconds.

No real or protected Rossmann data, canonical quantile artifact, or future outcome was accessed.
The change remains synthetic M3 only; M4, staging, and release remain outside scope. Draft PR #40
remains under Technical Lead re-review.

## Historical implementation checkpoints (preserved)

The following next-boundary notes are historical checkpoints; the current state is recorded at
the top of this file. Phase 5 was formally COMPLETE following PR #7 integration and PR #8
closeout. Phase 6 is **COMPLETE**:
ADR-019 remains accepted, and [PR #10](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/10)
was merged into `main` at `dac71d26bd8a9e43eff7d33592460906ae6fee6f`; its completed plan is
archived.
The Phase 6 development-only results and coverage evidence remain recorded below. Phase 6 closeout
[PR #11](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/11) merged at
`0b8d55144ace29cb8b5367d11aeedc59cfb33a65`. Phase 7 methodology is approved in ADR-020, and
[PR #13](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/13) merged into
`main` at `89bcb861642ee28259e4a402e8e8ee98a999a6e5`. Phase 7 is **COMPLETE**; the selected
`global_lightgbm_gbdt_regression_l1` recipe remains trial A at exactly 180 rounds.
Phase 8 implementation/results were accepted after PR #15 merged at
`c694f5922a1c1e58ffaf9c2437fd9698ca3e5821`; the Fit B freeze was integrated by PR #16 at
`4dd7717fed57ff3b1f14789b980772c1968f3cba`. Phase 8 is **COMPLETE** following the closeout
recorded below. Its completed plan preserves the approved method and review checkpoints.
Final-holdout evaluation remains unreleased. The
[historical Phase 6 implementation handoff](PROJECT_PLAN.md#phase-6-implementation-handoff-historical)
records the interfaces and boundary used.

PR #17 integrated Phase 8's formal closeout at `f08a62aa980d0670186ed25ae1f6e5a018ff3781`.
PR #18 integrated the accepted Phase 9 design and ADR-022 at
`97795ca5d868b512e5c2f6cae59bcec1d6ce19a4`. PR #19 subsequently merged into `main` at
`7451c50ff685d92e8e74b5014d07b3bbfaca0a22`, completing Phase 9 after independent implementation
and numerical review acceptance. PR #20 merged into `main` at
`ff3c11554144e79ee84c627c2bcd3619d23072d0`; that commit is integrated into the current `origin/main`.
The PR #19 branch was synchronized by merging `origin/main`, preserving the uppercase canonical
proposal path and its unchanged content. At the Phase 9 closeout checkpoint, Phase 10's review,
queue, policy and comparison design was outside the accepted scope; the subsequent ADR-023
approval is recorded below. No final-holdout release or access is authorized.

The [completed Phase 10 plan](../plans/completed/phase-10-inventory-simulation.md) and accepted
[ADR-023](DECISIONS.md#adr-023--origin-frozen-daily-inventory-policy-simulation-and-finite-window-accounting)
record the methodology and lifecycle. The current canonical development run is
`phase10-dev-20261008-validator-fix`, manifest SHA-256
`1c914b8a0fc7582c192f24fb8286e8521669cc079162cf832a58f2d8a1569f16`. PR #23 and corrective PR #24
are integrated at the SHAs in the current-state table. Phase 10's final closeout is recorded in the
completed plan; Phase 10 is COMPLETE after closeout PR #25 merged into `main` at
`d437269b9f0cf36a842cdfd496ad50a310804768`. Phase 11 M1, M2 and M3 are formally accepted;
M3-01 is resolved; M4 is accepted with minor changes; and M4-01 is resolved by this correction.
Phase 11 is COMPLETE following PR #26 squash merge at
`725d30a59d7c8e04e44f3bcbcce9186f8a1183be`; its [completed plan](../plans/completed/phase-11-application-services.md)
records formal acceptance. Phase 12 M1 is IMPLEMENTED / UNDER REVIEW on the feature branch, as
recorded in the [Phase 12 plan](../plans/completed/phase-12-streamlit-dashboard.md); the current
checkpoint below supersedes that earlier M1-only state: M1 is ACCEPTED / INTEGRATED and M2 is
IMPLEMENTED / UNDER REVIEW. M3/M4 remain unauthorized. Phase 13 still requires a
separate frozen protocol and explicit authorization to release holdout outcomes. The holdout remains
unreleased.

The current forecasting firewall excludes July 4–31 from tuning/selection/calibration and has
produced no final-holdout forecasts/metrics; final-holdout evaluation remains unreleased. Earlier
full-source validation and descriptive EDA
did include those labels; [EDA_FINDINGS](EDA_FINDINGS.md) records that exposure. Do not claim an
entirely never-inspected test set or reuse those full-period cohorts for modeling. ADR-015 defers
the single authorized sequential final evaluation until model, intervals and policies are frozen.

### Phase 11 M1 implementation and review-fix checkpoint — 2026-10-08

M1 provides typed contracts and fixed, read-only readers for the accepted Phase 7–10 canonical
outputs, plus a bounded historical Sales reader. Phase 7/8 projected Parquet fields are checked
against their accepted Arrow types; Phase 9/10 artifacts are checked against producer schemas and
mandatory manifest descriptors, including field nullability. CSV fields are read with nullable
string, integer, float and boolean types; malformed numeric/boolean values and missing required
identifiers are rejected while documented unavailable values remain null. Model-comparison nulls
are allowed only in optional grouping-key fields. Output hash memoization remains process-local under
the immutable, locally trusted artifact assumption: fingerprint changes trigger rehashing, while
matching metadata does not prove byte immutability. There is no selector for the Phase 10 ledger and
no `current.json` fallback.

The history reader accepts one Store and at most 366 days from 2013-01-01 through 2015-07-03. It
rejects unsupported query dates before opening the dataset and accepts only the prepared source's
timezone-naive `timestamp[ns]` Date schema. The fixed `Store`, `Date`, `Sales`, `Open` projection and
Store/date predicate are applied in Arrow before materialization. Fixtures cover extreme dates,
timezone-aware schemas/requests, sanitized conversion errors, and the protected cutoff. Selection-
driven case/Store reads from Phase 10 summaries remain an M2 prerequisite; M1 retains fixed
projections. A read-only smoke read passed for all ten registered outputs (including Phase 10 summary
and target tables); the simulation ledger was not read. No forecast or inventory output was
regenerated, and no protected July 4–31 outcome rows were inspected.

Validation on the existing Python 3.14.5 environment: the full pytest suite passed (332 tests),
including the focused app-reader suite; Ruff lint and format, documentation links, `git diff --check`,
`uv lock --check` (84 resolved packages), and `uv pip check` (62 compatible installed packages)
passed. No dependency or lockfile changed. M1 remains **IMPLEMENTED / UNDER REVIEW** pending
independent acceptance; Phase 11 is not complete, and M2–M4, final-holdout access and merge remain
outside this authorization.

The targeted M1 correctness fix rejects any CSV source containing an embedded NUL before pandas
tokenization. The bounded 1 MiB byte scan runs in the same pass as output SHA-256 verification;
matching verified fingerprints reuse that result under the documented immutable local-artifact
assumption, and changed fingerprints trigger a fresh hash and scan. Public-reader fixtures cover
all three reproduced integer-token bypasses, NUL bytes in string columns across all four CSV
selectors, a NUL outside field data, and unchanged values, UTF-8, nullable `Int64`, row counts and
source bytes for valid CSVs. Focused reader tests passed (80 tests), and the full suite passed (360
tests). Ruff, formatting, documentation links, `git diff --check`, lock consistency (84 packages)
and installed dependency compatibility (62 packages) passed. Read-only smoke reads passed for all
ten registered canonical development outputs; output, manifest and binding sizes and modification
times were unchanged. The Phase 10 ledger and final holdout were not read. M1 remains
**IMPLEMENTED / UNDER REVIEW**; M2–M4 remained unauthorized at that checkpoint.

### Phase 11 M1 acceptance and M2 implementation checkpoint — 2026-10-08

The Technical Lead formally accepted M1 after the final independent targeted review returned
`ACCEPT` on exact PR #26 head `1fef9c7f27cb27068f8fcb415378771b878d4aed`. The PR remains open,
draft and unmerged; `main` remains at Phase 10 closeout commit
`d437269b9f0cf36a842cdfd496ad50a310804768`. This records M1 review acceptance, not phase completion
or integration.

The Technical Lead authorized M2 on the same branch and PR. M2 is in implementation and remains
pending independent review. Before code changes, the active plan froze supported selectors, query
bounds, service response whitelists, selective-read integrity behavior and comparison semantics
against the producer contracts. M2 is limited to shared read-only services and fixture tests;
M3–M4 remain unauthorized, PR #26 must stay draft/unmerged, and no final-holdout outcome, inference,
or Phase 10 ledger artifact is part of this work.

### Phase 11 M2 initial implementation checkpoint — 2026-10-08

M2 adds closed typed queries and bounded shared services for readiness/catalog, forecast issuance,
saved uncertainty, model comparisons, policy comparisons and the existing cutoff-safe history reader.
Parquet selection uses Arrow predicates after full-file hash, footer schema and global manifest-row
verification; selected rows have independent bounds. Large CSV comparisons stream exact matches and
never materialize the complete Phase 7 comparison frame. Service DTOs whitelist response fields,
preserve unavailable values and provenance, reject non-finite JSON numbers, and do not expose artifact
paths. The corrective checkpoint below fixes the initial `pd.NaT` serialization edge case. Policy
cost differences are shown only for valid complete matched pairs; producer case-level comparisons,
denominators and signed adverse results remain unchanged.

Initial implementation validation on Python 3.14.5: focused app-reader/service tests passed (**98**);
full pytest passed (**379**). Ruff lint and format, documentation links (**229** local destinations/anchors),
`git diff --check`, and the environment's `pip check` passed. The `uv` executable was not available
in this shell, so `uv lock --check` could not run; no dependency or lockfile changed. A read-only
canonical service smoke covered 10 registered non-ledger resources, 82 scenario entries, 172 case
IDs, all service views, and 1,115 matched Store pairs. Responses were JSON-safe and cutoff-safe;
canonical output and manifest sizes/modification times were unchanged. No final-holdout outcomes,
Phase 10 ledger, or raw historical source data were read; no artifact was generated or mutated.

M2 is **IMPLEMENTED / UNDER REVIEW** pending independent review. M1 remains reviewed/accepted on the
unmerged feature branch. PR #26 stays draft and unmerged; M3–M4 remain unauthorized and Phase 11 is
not complete.

### Phase 11 M2 corrective review-fix checkpoint — 2026-10-09

The targeted correction separates target unavailability from episode failure in each policy DTO and
allows baseline and forecast validity/availability to differ. A pair is comparable only when both
episodes are complete, both targets are available with saved values, both matched-comparison flags
are true, and both saved costs exist. For a non-comparable pair, the stable reason priority is:
first incomplete episode (using that policy's summary reason), then unavailable target (using that
policy's target reason), then invalid matched comparison, then unavailable saved cost. Available
targets with null values and unavailable targets with non-null values are rejected as integrity
failures. `json_safe` now converts `pd.NaT` and `pd.NA` to JSON null before date handling.

The earlier test counts above are the initial implementation checkpoint. Corrective validation on
Python 3.14.5: focused app-reader/service tests passed (**107**); full pytest passed (**387**).
Ruff lint and format, documentation links (**229** local destinations/anchors), `git diff --check`,
`uv lock --check` (**84** resolved packages) and installed dependency compatibility (`pip check`)
passed. A read-only canonical service smoke opened all ten registered non-ledger outputs and
confirmed their output hashes, schemas and manifest identities. The base reference and buffer-090
sensitivity case-level forecast-minus-baseline cost differences remained positive (+1,842,931.05
and +2,657,553.78 respectively); all 1,115 Store pairs were comparable for each case. These are
synthetic simulated monetary costs, not observed inventory or proven savings. No Phase 10 ledger,
final-holdout outcome or raw historical source data was read; no producer, canonical artifact or
manifest was changed.

M2 is formally accepted as recorded in the 2026-10-09 review/authorization checkpoint below. M1
remains accepted on the unmerged feature branch; PR #26 stays open, draft and unmerged. M3–M4 were
unauthorized at this historical checkpoint, and Phase 11 was not complete.

### Phase 11 M2 formal acceptance and M3 authorization — 2026-10-09

The Technical Lead formally accepted M2 following the independent `ACCEPT` review of exact PR #26
head `cd7d3319760379716244e4db6c0cf0cb96ec6cbd`. This records the project acceptance checkpoint;
the PR remains draft and unmerged. M1 and M2 are REVIEWED / ACCEPTED on the feature branch.

The Technical Lead separately authorized M3 implementation on the same branch and PR. M3 is
AUTHORIZED / IN IMPLEMENTATION pending independent review. The HTTP route, query, response and
sanitized error contract was frozen in the [completed Phase 11 plan](../plans/completed/phase-11-application-services.md)
before adapter implementation. M4, merge and Phase 11 closeout remain outside this authorization.
The Phase 10 ledger and protected final holdout remain excluded.

### Phase 11 M3 implementation checkpoint — 2026-10-09

Implemented the frozen seven-route, read-only FastAPI adapter in `src/rossmann_forecasting/app/api.py`
over the accepted M2 services. Added fixture-backed endpoint, selector, bound, error-sanitization,
serialization and mutation-method tests in `tests/test_app_api.py`; added optional API dependencies,
locked them, enabled that extra in CI and documented local use. The routes expose only accepted
development artifacts and the M1 bounded Sales history view. No inference, simulation, producer
changes, ledger access or holdout access was added.

The full fixture suite passed: 424 tests on Python 3.14.5 in 119.56 seconds. The M1/M2/M3 focused
suite passed 144 tests. Ruff lint and formatting, Markdown-link validation (230 destinations across
26 files), `uv lock --check`, `pip check` and `git diff --check` passed. The full test run emitted one
upstream Starlette deprecation warning because its TestClient currently uses `httpx`; no test failed.

A canonical-data API smoke returned 200 for all seven routes, including forecast, uncertainty,
comparison, inventory and history. The 82 scenario entries, 172 cases and 1,115 policy pairs were
available as expected. Before/after snapshots confirmed 15 registered non-ledger canonical files
were unchanged. The smoke did not read the simulation ledger, protected holdout or raw historical
source beyond the authorized bounded-history route.

M3 is **IMPLEMENTED / UNDER REVIEW**, pending independent review. GitHub Quality run [#75 /
37882356772](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/actions/runs/37882356772)
passed on exact implementation head `8ee9c0639b8598dfe7f79ad6175f4f87a1b030f1` for Python 3.12
and 3.14. PR #26 remains draft and unmerged. M4 remains unauthorized; Phase 11 is not complete.


### Phase 11 M3 formal acceptance and M4 authorization — 2026-10-09

The Technical Lead formally accepted M3 with the single minor follow-up M3-01 after the independent
`ACCEPT_WITH_MINOR_CHANGES` review of exact PR #26 head
`6169e850d824e3f6eccc1faa57b3d4a311646bd6`. M3-01 is the omitted framework-provided `Allow`
header on HTTP 405 responses. The Technical Lead authorized M4 implementation on the same branch
and draft PR. M4 is limited to that correction, cross-layer fixture integration evidence, and
reproducible startup/use guidance and handoff. M1 and M2 remain accepted; Phase 11 remains
incomplete; PR #26 remains draft and unmerged.


### Phase 11 M4 implementation and local verification — 2026-10-09

M4 resolves M3-01 by preserving only Starlette's framework-provided `Allow` header on sanitized
HTTP 405 responses. New fixture-backed HTTP-to-reader tests exercise the shared service chain,
validated artifact provenance, null/unavailable results, Store versus case-level inventory views,
the history cutoff, and process-only health. The tests use synthetic fixtures and do not require
canonical artifacts or Kaggle credentials.

The locked full repository suite passed **431 tests** with one existing Starlette TestClient
deprecation warning. GitHub Quality run #77 passed on exact pushed M4 head
`6f5eaccd7b0f5f11574c4c60e278dc72c0819980` for Python 3.12 and 3.14. The focused
application suites passed **151 tests**; the locked API and integration invocation passed **44 tests**. Ruff, repository formatting (96 Python files), the docs
link/anchor check (232 local targets across 26 documents), locked dependency sync, lock check, and
installed dependency compatibility check passed. The documented local Uvicorn command was started
on `127.0.0.1`; health, catalog, forecast, and inventory reference requests returned 200.

A read-only canonical API smoke made seven successful requests across health, catalog, forecast,
uncertainty, model comparison, and both inventory cases. It returned the pinned 14-point forecast,
28 daily intervals, 42 cumulative prefixes, four comparison rows, and 1,115 policy pairs per case.
Reference and `buffer_090` signed differences remained respectively +1,842,931.0502027555 and
+2,657,553.7797287568. All 15 registered canonical file snapshots were unchanged; the smoke read
no ledger, history source, or holdout. No inference, simulation, or canonical artifact generation
was performed. M4 remains implemented / under independent review; PR #26 remains draft and
unmerged, and Phase 11 remains incomplete.


### Phase 11 M4 acceptance and M4-01 correction - 2026-10-09

The independent M4 review of expected PR #26 head
`db2d8ce47e7704e7beb11f7c7b08fd846ac1619c` returned `ACCEPT_WITH_MINOR_CHANGES`. It confirmed
M3-01 is resolved and identified M4-01 as the sole remaining finding: the current "Immediate next
boundary" paragraph still described M3 as under review and M4 as unauthorized. This documentation-
only correction updates that status; no product finding remains. The Technical Lead formally
accepted M4 with minor changes.

M1, M2 and M3 are formally accepted; M3-01 and M4-01 are resolved; M4 is accepted with minor
changes. The implementation milestones are accepted, but the separate final PR integration and
merge-readiness review and formal Phase 11 closeout remain pending. PR #26 remains open, draft and
unmerged. No final-holdout release is authorized. Prior implementation test totals and canonical
results remain recorded in the preceding M4 checkpoint.


## Branch cleanup inventory

GitHub snapshot, 2026-10-05; cleanup is recommended only after checking unique commits and working
changes. No local or remote branches were deleted in this review.

| Candidate branch | Merged work | Disposition |
|---|---|---|
| `feat/data-preparation-eda` | [PR #2](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/2) | Retire after unique-change check |
| `feat/feature-engineering` | [PR #3](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/3) | Retire after unique-change check |
| `docs/phase-3-closeout` | [PR #4](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/4) | Retire after unique-change check |
| `feat/seasonal-naive` | [PR #5](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/5) | Retire after unique-change check |
| `docs/phase-4-closeout` | [PR #6](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/6) | Retire after unique-change check |

`feat/holt-winters` is active, not a cleanup candidate. The old
`origin/feat/data-acquisition-validation` exists only as a stale local tracking ref: that branch
is absent from GitHub's current branch list. Prune it during authorized maintenance. Main and this
review branch are retained; fresh work should not continue on merged branches.

## Source and Preparation Evidence

- Official raw CSVs remain unchanged and Git-ignored; their four SHA-256 hashes matched the
  documented source snapshot before and after preparation.
- Historical train: 1,017,209 rows, 1,115 stores, 2013-01-01 through 2015-07-31. Test: 41,088
  future-covariate rows, 856 stores, 2015-08-01 through 2015-09-17. Both metadata joins preserve
  row counts and unique Store × Date keys.
- The sparse historical output retains all source rows, including closed and open/zero-Sales days.
  No synthetic calendar rows or zero fills were added. Test remains separate and has no Sales or
  Customers.
- The 180-store 184-day gap, 54 open/zero-Sales rows, 11 missing test Open statuses, and 259
  metadata stores unused by test have documented evidence and dispositions. Store 622's original
  missing Open statuses remain null in `test.parquet`; the separate audit output contains 11
  uncertain unanimous historical-context candidates.
- Promo2 details retain structural nulls for all 544 nonparticipants. The 354 paired missing
  competition-open dates remain unexplained and unfilled; three missing CompetitionDistance
  values remain missing.
- Ignored Parquet outputs are reproducible through PyArrow 24.0.0. EDA tables, manifests, and
  figures are local generated artifacts under `reports/eda/`.

## Phase 3 Implementation and Closeout Evidence

- `python scripts/build_features.py` completed with contract `phase-3-v1`: 1,017,209 training
  rows and 41,088 inference rows, preserving input Store × Date keys and the shared ordered
  29-predictor schema. The outputs and manifest are ignored under `data/processed/`.
- Development feature-coverage diagnostics end on 2015-07-03. They record 313,436 nulls each for
  `competition_has_opened` and `competition_age_months` (the 354 jointly missing competition
  metadata stores), 2,558 missing `competition_distance` values, and expected exact-history warm-up
  and sparse-gap nulls. No imputations were introduced. Promo2 produced no invalid/incomplete
  schedule findings in the prepared snapshot; nonparticipants remain inactive despite structural
  schedule nulls.
- For a gap-affected store, all dynamic history fields are unavailable on 2015-01-01; lag 1 resumes
  on Jan 2; lag 7 and the 7-day window resume Jan 8; lag 14 and the 14-day windows resume Jan 15;
  all ten dynamic fields resume Jan 29 after the complete 28-day window exists. No absent dates
  were bridged or synthesized.
- The final holdout remains 2015-07-04 through 2015-07-31 (31,220 store-days). Its audit is
  mechanical only: predictor schema/order, unique keys, and dtype compatibility. No holdout
  distribution or forecast metric was summarized. Development coverage stops July 3.
- The feature runner verified all four raw-source hashes and the three prepared Parquet hashes
  against the approved source snapshot and Phase 2 manifest before and after the build. The raw
  validator also passed without errors. Store 622 Open candidates remain audit fields; inference
  contains no Sales, Customers, or Customers-derived fields.
- Future-known/static inference predictors are materialized for all test rows. Without recursive
  predictions, dynamic values needing exact dates after the forecast origin remain null; later
  recursive steps can supply predictions through the origin-censored history API.
- Repeated deterministic builds produced the same SHA-256 for each corresponding artifact:
  `features_train.parquet` matched its prior build, and `features_inference.parquet` matched its
  prior build. These two distinct artifacts do not share a hash. No holdout distributions were
  summarized.
- Detailed field semantics, roles, dtypes, null behavior, and point-in-time rules are in
  [Feature Contract](FEATURE_CONTRACT.md); the completed execution plan is archived at
  `plans/completed/phase-3-feature-engineering.md`.
- External review follow-up canonicalizes history keys before duplicate/overlap checks, grouping,
  or exact-date lookup: Store IDs are validated positive exact integers representable as int64;
  Dates are parsed as midnight calendar values and stored as datetime64[ns]. The shared key path
  copies inputs and is also used by static predictor assembly. Focused regression coverage now
  includes fractional/out-of-range IDs, canonical Store/Date collisions, valid coercion, and input
  non-mutation.

## Phase 3 Quality Checkpoint (Historical)

- `python scripts/validate_data.py --report reports/validation/rossmann.json`: PASS — 0 errors,
  4 reviewed warnings, 12 informational findings.
- `python scripts/build_features.py`: PASS — raw/interim provenance checks, key preservation,
  matching predictor schemas/dtypes, holdout mechanical audit, and output generation.
- Full suite chronology: 45 passed before the external-review key-canonicalization fix; 56 passed
  after the fix and again at PR readiness, including the key-canonicalization regression cases.
- `ruff check .`: passed; `ruff format --check .`: 45 files already formatted.
- `git diff --check`: passed. Relative Markdown links in changed user-facing documentation: passed.
- Preparation and EDA commands completed against the official data; both notebooks validated and
  executed successfully with cleared committed outputs.

## Phase 4 Scope Confirmation at Closeout

At the Phase 4 closeout checkpoint, only the explicitly approved Seasonal Naive baseline was
implemented; Holt-Winters and later-phase work had not begun. Sales remains monetary turnover at
Store × Date; future Customers remain unavailable to forecasts. Primary evaluation uses actual
source Open=1 observations, while the known-closed zero rule is applied only to the separate
operational forecast after raw generation.

## Phase 4 Implementation and Development Results

- The approved methodology is recorded in accepted ADR-013, which remains unchanged. External
  review found no blocking issue; PR #5 received final approval and merged into `main` at
  `12f80b5fe8a8580b3d8367cd473766decd3ebf31`. The completed execution plan is archived at
  [`plans/completed/phase-4-seasonal-naive.md`](../plans/completed/phase-4-seasonal-naive.md).
- `python scripts/run_seasonal_naive.py` completed successfully against the existing prepared
  Rossmann historical table. The runner read only `Store`, `Date`, `Sales`, and source `Open`, and
  applied the Parquet Date filter through 2015-07-03 before evaluation. It ran exactly the three
  approved development windows and emitted 46,830 observed target records. Generated outputs are
  ignored under `data/processed/seasonal_naive/`; the manifest records the methodology, windows,
  source hashes, and artifact hashes.
- Coverage and primary metrics by window (coverage is available raw forecasts / denominator):

  | Window | Observed targets | Eligible open labels | All-target coverage | Open-label coverage | MAE | RMSE | MAPE | MAPE rows / eligible | Zero rows excluded from MAPE | WAPE |
  |---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
  | validation_1 | 15,610 | 11,678 | 15,610 / 15,610 (100%) | 11,678 / 11,678 (100%) | 1,101.5940 | 1,444.9870 | 15.0088% | 11,678 / 11,678 (100%) | 0 | 0.143224 |
  | validation_2 | 15,610 | 13,438 | 15,610 / 15,610 (100%) | 13,438 / 13,438 (100%) | 2,269.7721 | 3,141.3506 | 36.1046% | 13,438 / 13,438 (100%) | 0 | 0.324782 |
  | validation_3 | 15,610 | 13,437 | 15,610 / 15,610 (100%) | 13,437 / 13,437 (100%) | 1,596.5170 | 2,253.3165 | 26.2135% | 13,437 / 13,437 (100%) | 0 | 0.226393 |

- Pooled eligible development rows: 38,553. Pooled MAE **1,681.2703**, RMSE **2,416.9677**,
  MAPE **26.2671%** (38,553 MAPE rows, 0 zero-actual rows excluded, 100% MAPE coverage), and
  WAPE **0.232748**. These are computed over pooled eligible observations, not averaged window
  metrics.
- Horizon-level eligible counts and metrics (WAPE is a ratio; MAPE is a percent):

  | Horizon | Eligible | MAE | RMSE | MAPE | WAPE |
  |---:|---:|---:|---:|---:|---:|
  | 1 | 3,344 | 672.2425 | 981.3211 | 11.9931% | 0.114442 |
  | 2 | 97 | 861.8763 | 1,187.4567 | 14.7578% | 0.108050 |
  | 3 | 2,262 | 4,259.5504 | 4,747.9555 | 72.8666% | 0.677632 |
  | 4 | 3,344 | 2,307.4554 | 2,739.8971 | 39.9556% | 0.368580 |
  | 5 | 3,344 | 2,131.9731 | 2,459.9699 | 38.2207% | 0.362656 |
  | 6 | 3,344 | 2,405.0329 | 3,161.1523 | 42.6760% | 0.407425 |
  | 7 | 3,344 | 1,765.8403 | 2,232.6592 | 30.0997% | 0.273202 |
  | 8 | 3,344 | 832.9013 | 1,125.0257 | 14.0842% | 0.135236 |
  | 9 | 96 | 752.7188 | 1,039.2468 | 10.4863% | 0.089113 |
  | 10 | 3,344 | 1,025.8322 | 1,418.5733 | 9.7639% | 0.097370 |
  | 11 | 3,344 | 1,141.4202 | 1,587.1030 | 11.6617% | 0.122944 |
  | 12 | 3,343 | 1,124.9399 | 1,441.6304 | 13.9331% | 0.137552 |
  | 13 | 2,660 | 2,460.7320 | 3,971.0272 | 33.6384% | 0.324489 |
  | 14 | 3,343 | 1,091.0808 | 1,453.2243 | 13.6778% | 0.136541 |

- All 46,830 observed target records had an available raw forecast (46,830 / 46,830); therefore
  there were no unavailable weekly baseline forecasts, no affected Store × Date rows, and no
  unavailable-store cases to report. Open-labelled forecast coverage was also 100% in each window.
- No final-holdout forecast, score, metric, or target summary was produced. Phase 4 reads are
  restricted to dates through 2015-07-03 before the evaluation layer; only development outputs
  appear in the generated artifact directory.
- Raw Rossmann inputs and Phase 2 `train.parquet` hashes matched their recorded provenance before
  and after the run. The runner wrote only Git-ignored generated files; no raw, interim, or Phase 3
  files were modified, and generated results remain ignored and untracked. `docs/PROPOSAL.md` is
  unchanged.
- Validation at Phase 4 completion: full pytest suite **73 passed**; `ruff check .`,
  `ruff format --check .`, and `git diff --check` passed. The Seasonal Naive CLI completed
  successfully with unchanged input provenance. Phase 4 is formally COMPLETE. At the Phase 4
  closeout checkpoint, Phase 5 implementation had not begun; no final-holdout result was produced.

## Phase 5 Statistical Forecasting Approval and Implementation

- Status at approval checkpoint: **APPROVED / IMPLEMENTATION IN PROGRESS**. The user explicitly
  approved the fixed Holt-Winters methodology and its 99% coverage guardrail on 2026-10-05. Phase 5
  implementation and real-data results are recorded below as they are produced.
- The archived design plan is [`plans/completed/phase-5-statistical-forecasting.md`](../plans/completed/phase-5-statistical-forecasting.md).
- A mechanical history-availability audit projected only `Store` and `Date` from the existing
  training feature Parquet and filtered dates to `<= 2015-07-03`. It used no Sales, Open,
  Customers, forecast, metric, or holdout field/value. All 1,115 target Stores in each approved
  development window had at least 28 consecutive observed dates ending at the origin:

  | Window | Target Stores | Origin-row Stores | ≥28 days | 14–27 days | 7–13 days | 2–6 days | 0–1 day | Eligible |
  |---|---:|---:|---:|---:|---:|---:|---:|---:|
  | validation_1 | 1,115 | 1,115 | 1,115 | 0 | 0 | 0 | 0 | 1,115 / 1,115 (100.00%) |
  | validation_2 | 1,115 | 1,115 | 1,115 | 0 | 0 | 0 | 0 | 1,115 / 1,115 (100.00%) |
  | validation_3 | 1,115 | 1,115 | 1,115 | 0 | 0 | 0 | 0 | 1,115 / 1,115 (100.00%) |

- At the approval checkpoint, this date-only result suggested no date-availability coverage loss
  under the minimum-history rule. It did not establish Sales validity or model-fit success;
  numerical failures were then unmeasured. The implementation evidence below records the later
  successful fits. The approved policy has no fallback.
- The audit stopped at 2015-07-03 and did not read holdout Sales. It produced no holdout forecast
  or evaluation; the earlier descriptive exposure is disclosed above.

### Phase 5 Implementation and Development Results

- The approved design is implemented on `feat/holt-winters` under accepted ADR-014. The package
  provides origin-censored, per-Store additive Holt-Winters fitting, latest-contiguous-history
  eligibility, a single internal 14-step forecast operation, clipped raw forecasts with retained
  unclipped values, explicit unavailable reasons, and post-forecast Open routing. There is no
  fallback model. The dependency resolved to statsmodels 0.15.0.
- `python scripts/run_holt_winters.py` completed successfully against the existing Phase 2
  `train.parquet`. Its Parquet projection includes only Store, Date, Sales, and Open, and the Date
  predicate is applied at read time through 2015-07-03. It evaluated the three approved development
  windows and recomputed Seasonal Naive from the reviewed Phase 4 implementation. Raw Rossmann and
  Phase 2 hashes matched before and after the run. No final-holdout forecast, score, or metric was
  produced.
- The run generated 46,830 observed target forecasts and 46,830 internal 14-step path records
  across 3,345 Store-origin fits. All 3,345 fits succeeded; there were no unavailable forecasts,
  fit/forecast failures, warnings, or optimizer non-convergence flags. All three windows achieved
  100% raw and Open-label forecast coverage, above the precommitted 99% coverage guardrail.
- Standalone Holt-Winters metrics (primary population: observed source Open=1 and Sales, with
  available clipped raw forecast):

  | Window | Observed targets | Eligible open labels | Open-label coverage | MAE | RMSE | MAPE | WAPE |
  |---|---:|---:|---:|---:|---:|---:|---:|
  | validation_1 | 15,610 | 11,678 | 11,678 / 11,678 (100%) | 1,195.5661 | 1,617.4146 | 15.2155% | 0.155442 |
  | validation_2 | 15,610 | 13,438 | 13,438 / 13,438 (100%) | 1,136.8306 | 1,483.1660 | 16.9474% | 0.162669 |
  | validation_3 | 15,610 | 13,437 | 13,437 / 13,437 (100%) | 1,501.5664 | 1,974.7435 | 22.5253% | 0.212929 |

- Pooled over 38,553 eligible rows, Holt-Winters MAE was **1,281.7446**, RMSE **1,708.3073**,
  MAPE **18.3669%**, and WAPE **0.177439**. MAPE included 38,553 positive-actual rows, excluded
  zero rows: 0, and had 100% MAPE coverage. Pooled values are calculated over rows, not averaged
  from window metrics.
- Paired comparison uses the identical 38,553 eligible Store-origin-Date rows where both
  recomputed Seasonal Naive and Holt-Winters forecasts were available. A negative MAE difference
  means Holt-Winters MAE is lower; this fixed-candidate development comparison is not final model
  selection:

  | Window | Paired rows | Holt-Winters MAE | Seasonal Naive MAE | Difference (HW - SN) | Relative change | Lower paired MAE |
  |---|---:|---:|---:|---:|---:|---|
  | validation_1 | 11,678 | 1,195.5661 | 1,101.5940 | +93.9721 | +8.5306% | Seasonal Naive |
  | validation_2 | 13,438 | 1,136.8306 | 2,269.7721 | -1,132.9415 | -49.9143% | Holt-Winters |
  | validation_3 | 13,437 | 1,501.5664 | 1,596.5170 | -94.9506 | -5.9474% | Holt-Winters |
  | pooled | 38,553 | 1,281.7446 | 1,681.2703 | -399.5257 | -23.7633% | Holt-Winters |

- Additive forecasts below zero were clipped only for the raw metric forecast; unclipped values
  remain in the audit output. In the full internal paths, 1,085 of 46,830 forecasts (2.3169%)
  were clipped. The minimum unclipped forecast was -4,175.2857. By window, clipping was
  354 / 15,610 (2.2678%), 408 / 15,610 (2.6137%), and 323 / 15,610 (2.0692%), respectively.
- Ignored artifacts and a manifest are under `data/processed/holt_winters/`: observed-key
  forecasts, internal 14-step paths, per-fit and aggregated diagnostics, window/pooled/horizon
  metrics, coverage guardrail, identical-row paired forecasts and metrics, and clipping
  diagnostics. All emitted dates are 2015-05-23 through 2015-07-03; all 46,830 composite keys are
  unique. The generated forecast table does not expose the protected holdout.
- Initial executions exposed two post-fit reporting defects (strict JSON serialization of a
  missing pooled label, and a clipping-rate denominator reference); both were corrected and covered
  by tests. The final real-data runner completed with exit code 0 and regenerated all artifacts.
- Initial Phase 5 implementation checks: full pytest suite **95 passed**;
  `ruff check src tests scripts` and `ruff format --check src tests scripts` passed. Artifact paths
  were verified Git-ignored;
  provenance checks passed before and after evaluation. At this implementation checkpoint, Phase 5
  was **IMPLEMENTED / UNDER REVIEW**, not formally closed. `docs/PROPOSAL.md`, reviewed Phase 4 model code/artifacts, raw data,
  and Phase 2 prepared data were not modified.
- External review found that the reusable Holt-Winters API validated horizons from 1–14 but still
  generated a fixed 14-step path. The forecaster now consistently uses the validated
  horizon for model forecasts, output-length validation, and internal path rows, records
  `forecast_horizon` for successful and failed fits, and computes clipping rates over successful
  requested forecast steps. Regression tests cover 7- and 14-step behavior, target bounds, output
  lengths, failed-fit paths, and horizon-aware clipping rates. The approved Phase 5 runner continues
  to request 14 days. Its post-fix rerun reproduced the recorded metrics unchanged: 46,830 forecasts,
  3,345 successful Store-origin fits, 100% availability in every window, and a passed 99% coverage
  guardrail. The ignored fit-diagnostics artifact now includes `forecast_horizon`; artifact hashes
  were regenerated for the updated output schema. Full-repository validation passed: pytest **102
  passed**, `ruff check .`, `ruff format --check .`, `git diff --check`, and relative Markdown-link
  validation across 19 files. No holdout forecast or evaluation occurred; at that review checkpoint,
  Phase 5 was **IMPLEMENTED / UNDER REVIEW**.

## Repository Architecture/Governance Review — 2026-10-05

The [completed review task plan](../plans/completed/repository-architecture-governance-review.md)
records scope and cross-review. Verdict: **READY for the next authorized design task**, not an
authorization to implement Phase 6 or a declaration that Phase 5 is closed.

- Reviewed all listed governance/data docs, active/completed plans, source/script/test/notebook
  structure, and public branch/merged-PR metadata. Current-state, branch, phase, artifact-path,
  terminology and local Markdown references were cross-checked; archived evidence was preserved.
- ADR-015–018 trace the fixes: final evaluation after all choices freeze, disclosed descriptive
  exposure, consistent simulated inventory values/cumulative uncertainty, simpler application and
  work-package boundaries, portable locked environments and fixture CI. AGENTS/WORKFLOW now own
  approval/lifecycle rules; this document owns maintained results, not duplicated plan tables.
- The Phase 6 handoff specifies origin-censored fitting/history, future-known covariates,
  categorical/null adapter design, raw recursion versus Open routing, metric/coverage interfaces,
  outputs, tests and approval. No LightGBM or later-phase module/dependency was implemented.
- Forecast algorithms/configurations and existing numerical evidence were unchanged. Three
  exception clauses gained tuple parentheses for Python 3.12 compatibility. Source hash-only
  verification matched all four documented raw hashes; no data/model pipeline or holdout
  forecasting/evaluation was run for this review.

The continuation recovered the existing dirty review branch at HEAD `3d4fbfd`: 18 modified and
five new files, nothing staged. Full-file rereads, diff/history inspection and a fresh repository-
only Phase 6 handoff audit preserved that work. Two residual ambiguities were corrected: LightGBM
feeds predictions, never unrevealed target actuals; final scheduled preprocessing/model refits may
update fitted state only under the frozen recipe using already revealed training rows. No new
phase scope or methodology search was introduced. The quality gate was rerun after these fixes.

Final checks actually executed:

| Check | Result |
|---|---|
| `python -m pytest` in the original Python 3.14.5 environment | 106 passed; includes four new Markdown-checker fixtures |
| Complete fixture suite in isolated locked Python 3.12.15 / 3.14.5 | 106 passed in each environment |
| `python -m ruff check .` | PASS |
| `python -m ruff format --check .` | PASS; 63 files already formatted |
| `python scripts/check_docs.py` | PASS; local files/directories/common heading anchors across 20 Markdown files |
| `git diff --check` | PASS |
| `uv lock --check` / `uv pip check` | PASS; current lock and compatible installed packages |
| Numbering and math checks | Phase 0–14, proposal 1–30, ADR-001–018 and paired proposal dollar delimiters PASS |

Remaining non-blocking limits: only 42 development target days and prior descriptive holdout
exposure; pooled empirical intervals/simulated policies require their later reviewed designs.
At the review checkpoint recorded here, main protection was not enabled, and stale branch cleanup
needed separate authorization/unique-change checks. PR #7 integration followed by Phase 5 explicit
closeout remained the immediate project gate. Phase 6 had not started.

## Phase 5 Formal Closeout — 2026-10-05

PR #7 was squash-merged into `main` at `76707a03b7d10dbaa79d3ef26b39e31994431d70`. The GitHub
PR metadata's `merge_commit_sha` matches the fetched `origin/main` and the closeout branch base.
Phase 5 is **COMPLETE**; its fixed additive Holt-Winters implementation and development-only
evaluation are integrated. The completed execution plan is archived at
[`plans/completed/phase-5-statistical-forecasting.md`](../plans/completed/phase-5-statistical-forecasting.md).
No final-holdout forecasting or evaluation was performed, and Phase 6 implementation began only
after the separate authorization recorded in its active plan. The historical metric tables and
methodology above are unchanged.

## Phase 6 Global LightGBM Implementation — 2026-10-06

At the implementation checkpoint, Phase 6 was **IMPLEMENTED / UNDER REVIEW** on
`feat/phase-6-global-lightgbm`. The candidate follows
ADR-019 and the [completed Phase 6 plan](../plans/completed/phase-6-global-lightgbm.md). It is a
development candidate only; Phase 7 has not started, and no final project model has been selected.

- `lightgbm>=4.7,<4.8` resolved to LightGBM 4.7.0 in the locked Python 3.14.5 / Windows 11
  environment. The runner writes ignored outputs only under `data/processed/lightgbm/` and
  `artifacts/lightgbm/`; `git check-ignore` confirmed the generated outputs are ignored.
- The exact 29-predictor phase-3-v1 matrix and four frozen trial recipes were used. Inner tuning
  ran 109 recursive checkpoints: A 23, B 6, C 40, and D 40. It selected trial A at 180 rounds
  (learning rate 0.05, 15 leaves, max depth 4, min_data_in_leaf 200), with inner open-label MAE
  **1,305.1707** and **100%** open-label coverage. Trials C and D reached the 400-round cap; A and
  B stopped after five checkpoints without strict improvement. Every fit succeeded.
- The predeclared outer refits completed for all three origins. Each 14-day window emitted 15,610
  target rows; the 46,830 pooled target rows include 38,553 eligible observed source Open=1 labels.
  Open-label coverage was 100% in every window (11,678/11,678; 13,438/13,438; and
  13,437/13,437), exceeding the frozen 99% guardrail. There were no unavailable forecasts and no
  negative-output clipping events.

Standalone development metrics use the primary population of observed source Open=1 and Sales with
an available clipped raw forecast. MAPE is reported as a percentage; WAPE is a ratio.

| Scope | Eligible rows | Open-label coverage | MAE | RMSE | MAPE | WAPE |
|---|---:|---:|---:|---:|---:|---:|
| validation_1 | 11,678 | 100% | 1,051.4335 | 1,512.2577 | 12.5686% | 0.136702 |
| validation_2 | 13,438 | 100% | 790.9941 | 1,193.4810 | 10.9700% | 0.113184 |
| validation_3 | 13,437 | 100% | 794.3741 | 1,350.5876 | 10.6797% | 0.112646 |
| pooled | 38,553 | 100% | **871.0612** | 1,350.9138 | 11.3531% | 0.120586 |

The pooled values are recomputed over eligible rows. Paired baseline summaries use the identical
38,553 eligible Store × Date rows with both forecasts available; these are descriptive Phase 6
development comparisons, not final model selection.

| Scope | Paired rows | LightGBM MAE | Seasonal Naive MAE | Holt-Winters MAE | LightGBM MAE change vs SN | vs Holt-Winters |
|---|---:|---:|---:|---:|---:|---:|
| validation_1 | 11,678 | 1,051.4335 | 1,101.5940 | 1,195.5661 | -4.55% | -12.06% |
| validation_2 | 13,438 | 790.9941 | 2,269.7721 | 1,136.8306 | -65.15% | -30.42% |
| validation_3 | 13,437 | 794.3741 | 1,596.5170 | 1,501.5664 | -50.24% | -47.10% |
| pooled | 38,553 | **871.0612** | 1,681.2703 | 1,281.7446 | -48.19% | -32.04% |

The final manifest records `development_only_through=2015-07-03`,
`final_holdout_forecast_or_evaluation=false`, and that Phase 6 neither read nor hashed final-holdout
outcomes. Emitted inner forecasts end on 2015-05-08; outer forecasts end on 2015-07-03. Phase 7
and the protected 2015-07-04 through 2015-07-31 holdout remain outside this implementation.

Implementation tuning exposed a repeated history-index build across recursive steps; a reusable
origin-censored history cache now matches the reviewed builder exactly across fixture horizons and
preserves missing-date behavior. LightGBM also required `feature_pre_filter=false` on the shared
Dataset because the frozen trial grid varies `min_data_in_leaf`; the four recipes and objective
were unchanged. The final real-data run completed without fit failures.

Final quality checks after the documentation update:

| Check | Result |
|---|---|
| Full fixture suite (`python -m pytest`, Python 3.14.5) | PASS — 151 passed in 22.39s |
| PR #10 GitHub Quality workflow | PASS — Python 3.12 and 3.14 jobs; tests, dependency check, Ruff, formatting, and Markdown links |
| `python -m ruff check .` | PASS |
| `python -m ruff format --check .` | PASS — 69 files already formatted |
| `python scripts/check_docs.py` | PASS — 85 local destinations/anchors across 21 Markdown files |
| `uv lock --check` | PASS — 84 packages resolved |
| `python -m pip check` | PASS — no broken requirements |
| `git diff --check` | PASS — Git reported only the existing uv.lock LF-to-CRLF working-copy warning |

At the implementation checkpoint, the runner completed successfully and its manifest hashed the
ignored development outputs and date-censored input projections. External review, authorized
integration, and formal closeout were then pending; the closeout is recorded below.

### External-review follow-up — 2026-10-06

- Recursive feature/history construction now has its own failure boundary; prediction API errors
  use the approved `model_fit_failure` reason, while explicit schema and categorical-adapter
  failures keep their approved reasons. The fake-booster regression and feature-construction
  failure fixture pass.
- Removed the `narwhals!=2.27.0` resolver exclusion after the LightGBM fixtures passed with
  LightGBM 4.7.0 and Narwhals 2.27.0 on Python 3.12.15 and 3.14.5 (46 passed in each
  environment). PyPI marks 2.27.0 yanked for Pointblank breakage; no incompatibility relevant to
  this repository or LightGBM was reproduced. The normal resolver therefore keeps the yanked
  release out and `uv.lock` remains at Narwhals 2.26.0; the effective locked runtime is unchanged.
- The review fixes do not alter the successful Phase 6 forecasts or recorded metrics. The
  approved real-data development command was not rerun because the locked runtime did not change.
  At this follow-up checkpoint Phase 6 remained **IMPLEMENTED / UNDER REVIEW**; Phase 7 and the
  final holdout remained untouched.
- Follow-up validation passed: full suite **152 passed** on Python 3.12.15 and **152 passed** on
  Python 3.14.5; Ruff lint and formatting, documentation links, `uv lock --check`, dependency
  consistency in both environments, and `git diff --check` passed.

## Phase 6 Formal Closeout — 2026-10-06

Phase 6 is **COMPLETE**. PR #10 merged into `main` at
`dac71d26bd8a9e43eff7d33592460906ae6fee6f`; its completed execution plan is
[archived](../plans/completed/phase-6-global-lightgbm.md). The external-review fixes are in final
commit `9a33e8f673ec438fe4a5546011d06219d66e6a92`, and final-head
[Quality workflow run #12](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/actions/runs/37419362812)
passed on Python 3.12 and 3.14. Review did not change the approved development results documented
above: trial A at 180 rounds, 100% open-label coverage, pooled MAE 871.0612, and the 99% coverage
guardrail passed. The full
fixture suite finished with 152 passing tests. No final-holdout forecast or evaluation occurred.
Phase 7 has not started and requires a separate approved design and authorization.

## Phase 7 Design and Development Evidence Audit — 2026-10-06

**At the evidence-audit checkpoint: design started, implementation not started, methodology
awaiting approval, and no final model officially selected.** The [active plan](../plans/completed/phase-7-model-selection.md)
was PROPOSED / AWAITING APPROVAL on `docs/phase-7-model-selection-design`, based on verified PR #11
integration. Its thresholds were proposed after observing the existing results, not
preregistered. Historical Phase 4–6 result records above remain unchanged.

Read-only audit of ignored development outputs: SHA-256 checks match the original manifests for
all three candidates' forecast, pooled/window/horizon metric files and saved HW/LightGBM fit
diagnostics. Exact label/key joining reproduces 46,830 targets and 38,553 common eligible rows
(11,678 / 13,438 / 13,437 per window); recomputed pooled MAEs match the reported values above.
No model/tuning runner or source-data read was needed. Newly verified horizon block MAEs,
pooled over the same common eligible rows rather than averaged daily metrics:

| Horizon block | Seasonal Naive | Holt-Winters | LightGBM |
|---|---:|---:|---:|
| 1–7 | 2,136.3558 | 1,155.6570 | 643.0551 |
| 8–14 | 1,235.4154 | 1,405.2746 | 1,094.4426 |

LightGBM beats each baseline on 11 of 14 pooled horizons, but Sunday h2/h9 MAEs are
1,572.8966 / 1,707.5285 versus SN 861.8763 / 752.7188 and HW 879.1219 / 903.0457;
these strata contain only 97 / 96 eligible rows. At h10 LightGBM MAE 2,280.9889 is worse
than SN 1,025.8322, though below HW 2,341.7674. At h8 it is slightly worse than HW
(733.6691 versus 716.2542). Friday origins confound horizon/weekday; these are descriptive
tradeoffs, not independent replication or confidence evidence.

Saved LightGBM outer `training_seconds` are 6.0427 / 6.1840 / 6.2647 on the recorded
Python 3.14.5, LightGBM 4.7.0 Windows CPU environment with four model threads. Runner inspection
confirms the timer surrounds fitting only. No comparable SN/HW times, end-to-end inference
timings or peak-memory measurements are available; none are fabricated here.

Cached provenance limits remain visible: SN/HW manifests lack modern code/lock identity;
LightGBM records revision `79ddb510e94fe5695c4bc17814153fd47695e16f` with modified worktree and
working-tree source hash, preceding the committed review fixes. The plan requires explicit
acceptance of that lineage and unchanged reviewed specifications, not a claim that these outputs
were regenerated from current main. This audit accessed only saved development evidence ending
July 3; no final-holdout read, hashing, fit, forecast or evaluation, nor Phase 8 work, occurred.

Design quality gate passed: full pytest **152 passed** on each of Python 3.14.5 and 3.12.15,
Ruff lint/format (70 files), Markdown links (107 local destinations/anchors, 22 documents),
`uv lock --check` and `git diff --check`. Only documentation changes; no new tests, models,
dependencies, selection artifacts or interval calculations. Full diff reviewed before publication.

## Phase 7 Methodology Approval Sync — 2026-10-06

External methodology approval was synchronized for reviewed PR #12 head
`1c15ab0b6ee94f3ecccb8f04c84da97d58bbb225`. Phase 7 is **APPROVED / IMPLEMENTATION NOT
STARTED**, and [ADR-020](DECISIONS.md#adr-020--development-only-model-selection-and-frozen-refit-policy)
records the accepted policy. PR #12 remains the open design integration gate; implementation may
begin only after it merges into `main`.

The approved phase-7-v1 rule is unchanged: SN → HW → LightGBM; same three-way eligible/available
open-label population; ≥5% pooled MAE improvement, lower MAE in at least 2/3 windows, and ≤10%
regression in each window and pooled horizon block 1–7/8–14; ties or failed gates retain the
simpler incumbent. Each standalone candidate and the common population must meet 99% coverage in
every approved window, with integrity checks passing. Thresholds remain disclosed as introduced
after observing results, not preregistered; there is no significance or generalization claim.
Keep individual-horizon weaknesses visible, including sparse Sundays and horizon 10; no horizon
veto or forecast mixing is added.

Qualitative operational assessment is accepted for the existing offline CPU course demonstration
without a new benchmark. This grants no API, production, end-to-end runtime, measured-memory or
savings claims. The existing artifact lineage is accepted only for this development selection,
subject to rechecking hashes, keys, labels, masks and configurations; original metadata remains
unchanged. Later operational inputs must be explicit, versioned and auditable.

The selection runner remains unimplemented; no final model is officially selected. Phase 8 has
not started. Final-holdout access remains prohibited until a separately authorized ADR-015 Phase
13 protocol; no holdout was accessed in this approval sync.

Approval-sync checks passed: full pytest **152 passed** on Python 3.14.5 and **152 passed** on
Python 3.12.15; Ruff lint and format (70 files), Markdown checker (109 local destinations/anchors
across 22 Markdown files), `uv lock --check` and `git diff --check`. No fixture tests or model
pipelines were added or run; the requested existing fixture suites passed. Full documentation diff
was inspected.

## Phase 7 Implementation Checkpoint — 2026-10-06

Phase 7 is **IMPLEMENTED / UNDER REVIEW** on `feat/phase-7-model-selection`, based on `main`
after approved design PR #12 merged at `64dbf2359c34cc06d81ee4fc1640ad7225db3973`. The reusable
selection engine and thin CLI use only the three reviewed candidates and their cached development
forecasts. The fixed ADR-020 policy is unchanged. No candidate-level operational decision was
found, so all three reviews remain `unknown`; the result is `operational_review_required`, with no
official selected model or selected-model artifacts.

The runner verified all 34 original candidate artifact hashes (5 Seasonal Naive, 11 Holt-Winters,
18 LightGBM), preserved all three source manifests and their original artifact metadata, checked
the approved source snapshot and Phase 2 identity, and validated the saved candidate keys, labels,
availability/eligibility masks, origins, windows, configurations and model identities. Each saved
candidate contained 46,830 observed Store-origin-Date targets from 2015-05-23 through 2015-07-03.
All 46,830 raw forecasts were available for each candidate, yielding 38,553 identical eligible
Open=1 observed-Sales rows. All three standalone and the three-way common population had 100%
open-label coverage in every window (11,678 / 11,678; 13,438 / 13,438; and 13,437 / 13,437).

Pooled results use the same 38,553 common eligible rows; values are direct row-pooled metrics:

| Candidate | MAE | RMSE | MAPE | WAPE |
|---|---:|---:|---:|---:|
| Seasonal Naive | 1,681.2703 | 2,416.9677 | 26.2671% | 0.232748 |
| Holt-Winters | 1,281.7446 | 1,708.3073 | 18.3669% | 0.177439 |
| LightGBM | 871.0612 | 1,350.9138 | 11.3531% | 0.120586 |

Window MAE (all candidate comparison populations use identical rows):

| Window | Seasonal Naive | Holt-Winters | LightGBM |
|---|---:|---:|---:|
| validation_1 | 1,101.5940 | 1,195.5661 | 1,051.4335 |
| validation_2 | 2,269.7721 | 1,136.8306 | 790.9941 |
| validation_3 | 1,596.5170 | 1,501.5664 | 794.3741 |

The numeric ladder keeps Seasonal Naive after Holt-Winters improves pooled MAE by 23.7633% and
wins 2/3 windows, because its pooled h8–14 MAE is 1,405.2746 versus 1,235.4154 for Seasonal
Naive (+13.7492%, above the 10% cap). The h1–7 block improves 45.9052%, and every window remains
within its 10% cap. LightGBM is then compared directly with the retained Seasonal Naive: pooled
MAE improves 48.1903%, all three windows win, and both pooled horizon blocks pass their caps
(h1–7 improves 69.8994%; h8–14 improves 11.4110%). LightGBM passes the numeric gates; operational
review still prevents selection.

| Horizon | Eligible rows | Seasonal Naive MAE | Holt-Winters MAE | LightGBM MAE | LightGBM change vs Seasonal Naive |
|---:|---:|---:|---:|---:|---:|
| 2 (Sunday) | 97 | 861.8763 | 879.1219 | 1,572.8966 | +82.50% |
| 9 (Sunday) | 96 | 752.7188 | 903.0457 | 1,707.5285 | +126.85% |
| 10 (Monday) | 3,344 | 1,025.8322 | 2,341.7674 | 2,280.9889 | +122.35% |

These horizon rows are descriptive and do not add a veto. The comparison file includes MAE, RMSE,
MAPE, WAPE, denominators, pairwise/common changes, horizon 1–14, pooled week blocks, Store-level
diagnostics and unavailable-reason counts. The ignored output directory is
`data/processed/model_selection/`: `model_comparison.csv` (190,680 rows),
`selection_decision.json`, and `manifest.json`. No `selected_model_config.json`, refit recipe,
selected forecasts or residual paths were emitted because operational approval is unresolved.

SN/HW legacy lineage limits and LightGBM's original modified-worktree revision/hash remain
disclosed in the new manifest; old manifests were not rewritten and no model was rerun. The
qualitative operational scope is only the offline CPU course demonstration. No production latency,
reliability, memory SLA, measured end-to-end runtime advantage or real business savings are
established. The runner read no raw/interim data or final-holdout outcomes, emitted no July 4–31
forecast or metric, performed no fit/tuning, and did not begin Phase 8. ADR-015 still blocks later
July 3 and July 17 refits until separately authorized.

The fixture-first suite has **179 passing tests** on Python 3.14.5 and **179 passing tests** on
Python 3.12.15. `ruff check .` passed; `ruff format --check .` passed (73 files); the documentation
checker passed (111 local destinations/anchors across 22 documents); `uv lock --check` resolved 84
packages; `python -m pip check` passed on Python 3.14.5; and `uv pip check` passed on the locked
Python 3.12 environment (60 packages). `git diff --check` passed with only expected Windows
LF-to-CRLF notices on the three new Python files. [Implementation PR #13](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/13)
is open for review and records these checks. Its [Quality workflow run #19](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/actions/runs/37429992491)
passed both Python 3.12 and Python 3.14 jobs, including dependency checks, fixture tests, lint,
formatting and Markdown links, on implementation commit `f95fa9d`. Later PR-head commits only
updated review documentation; the documentation checker and diff check passed locally, and no new
workflow run was created for those doc-only updates. Phase 7 remains under review; this checkpoint
is not a phase closeout.

## Phase 7 External Review Follow-up — 2026-10-06

The PR #13 review follow-up hardens generated-artifact lifecycle handling without changing
ADR-020. Before reading candidate evidence, the runner atomically replaces its prior manifest with
an in-progress marker. It stages the comparison, decision, and—only for a selected decision—all
four selected-model artifacts under one run ID; each output is hashed, and the complete manifest is
published last. An interrupted publication therefore cannot leave a complete manifest pointing at
a partial selection. Unresolved or failed runs publish no selected identity or selected-artifact
references. Cleanup is limited to the four fixed selected-output names and only removes files whose
hashes match prior runner-owned metadata. Modified or unverified paths are preserved and reported as
conflicts. Original candidate manifests and files are read-only.

Synthetic lifecycle coverage now includes successful approvals and all four hashed outputs,
subsequent unknown reviews, integrity failure, selected-artifact generation failure, ownership
conflicts, inability to invalidate the existing manifest, preservation of unrelated files and
original manifests, no fit/tuning calls, and residual path keys/masks/errors/completeness. The full
suite passed **187 tests** on Python 3.14.5 and **187 tests** on Python 3.12.15.

The real cached selection command ran without an operational-review file. It returned
`operational_review_required`, selected candidate `null`, and no selected-model files. On the same
38,553 common eligible rows, pooled MAE remained Seasonal Naive **1,681.2703**, Holt-Winters
**1,281.7446**, and LightGBM **871.0612**. All 12 standalone/common per-window coverage gates
passed. The pre-run verification and post-run checks confirmed every original candidate manifest
and every artifact hash still matches its source manifest. No candidate was fitted or tuned, no
final-holdout outcomes were read or hashed, and Phase 8 did not start. Phase 7 remains
**IMPLEMENTED / UNDER REVIEW**; there is no official final model selection.

Final review-fix checks passed: `ruff check .`; `ruff format --check .` (73 files);
`python scripts/check_docs.py` (112 local destinations/anchors across 22 documents);
`uv lock --check` (84 packages); Python 3.14 `pip check`; Python 3.12 `uv pip check` (60
packages); and `git diff --check` (only expected Windows LF-to-CRLF notices for the two changed
Python files). Implementation commit `dbb1712bdc856a2c9b6787a34493cb429d5b8e3c` was pushed to
PR #13; GitHub Actions [Quality run #22](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/actions/runs/37441277676)
passed both Python 3.12 and Python 3.14 jobs on that commit.

## Phase 7 Offline Operational Acceptance and Selection 2026-10-06

The external technical review supplied for PR #13 records candidate-level operational decisions
for the **offline CPU course demonstration** only. These are project technical-review decisions;
this record does not assert a named human reviewer or signature. The versioned input is
[configs/phase-7-operational-review-v1.json](../configs/phase-7-operational-review-v1.json), and
its reviewer reference points back to this section.

| Candidate | Decision | Rationale |
|---|---|---|
| Seasonal Naive | approved | Minimal computational complexity and deterministic same-weekday recurrence make it suitable as the initial incumbent. It needs no optimization or native model dependency. |
| Holt-Winters additive weekly | unknown | It fails ADR-020's pooled h8–14 regression cap; a candidate-specific operational approval is unnecessary for this selection. The operational decision remains unknown rather than being inferred as a rejection. |
| Global LightGBM GBDT regression L1 | approved | The reviewed global CPU implementation uses frozen trial A at 180 rounds in the reproducible locked environment, has 100% development coverage, improves pooled MAE substantially, and had no observed development fit failure. |

This approval is limited to the existing offline CPU demonstration. It establishes no production
latency SLA, reliability guarantee, end-to-end inference-speed comparison, memory SLA, real
inventory result, business savings, or universal accuracy superiority. The h2, h9 and h10
weaknesses and the original candidate-provenance limitations remain in force. The input does not
change ADR-020 thresholds, authorize fitting or tuning, or authorize access to final-holdout
outcomes. The actual CLI result and output integrity checks are recorded next.

### Selection result and artifact verification

The reviewed command ran with the versioned input:
`python scripts/run_model_selection.py --operational-review configs/phase-7-operational-review-v1.json`.
The runner returned **`selected`**; artifact integrity, record integrity and coverage statuses all
**passed**. The selected candidate is `global_lightgbm_gbdt_regression_l1`, selection run ID
`365f22d4c3f94722a594ab934a22c4f6`, and publication state **`complete`**. This is the Phase 7
offline development selection, **RECORDED / AWAITING EXTERNAL INTEGRATION REVIEW**; Phase 7 remains
**IMPLEMENTED / UNDER REVIEW**.

All original candidate-manifest artifacts were rehashed and passed: 5 Seasonal Naive, 11
Holt-Winters and 18 LightGBM artifacts. Their unchanged manifest SHA-256 identities are:

| Candidate | Original manifest SHA-256 |
|---|---|
| Seasonal Naive | `f5e3a18a0a8bff709cb06b4e6282e22cbe3f84668937d3c3e57245b7c76072e3` |
| Holt-Winters | `37b46babad1d197143bfda2f4f11aa65291c350b6b0687410bc4496b7171903b` |
| LightGBM | `ddd379fe4264dd90f618ba57791b97fcce3fd64199ffe95410c4f0d0695810c1` |

The runner matched 46,830 saved Store-origin target rows across 3,345 H14 paths, all ending on
2015-07-03. All 12 standalone/common 99% coverage gates passed at 100%: denominators were 11,678,
13,438 and 13,437 in `validation_1`, `validation_2` and `validation_3`, respectively. The common
eligible population contains 38,553 observed source Open=1 Sales rows.

| Candidate | Pooled common-row MAE | Policy result versus incumbent |
|---|---:|---|
| Seasonal Naive | 1,681.2703 | Initial incumbent |
| Holt-Winters additive weekly | 1,281.7446 | Improves 23.7633% and wins 2/3 windows, but fails the pooled h8–14 cap at +13.7492%; Seasonal Naive remains incumbent. Operational decision remains `unknown`. |
| Global LightGBM GBDT regression L1 | 871.0612 | Improves 48.1903% against Seasonal Naive, wins all 3 windows, and passes every window and pooled horizon-block cap; approved operationally for the scoped demonstration and selected. |

Actual window MAEs and the 10% caps against the retained Seasonal Naive incumbent:

| Window | Seasonal Naive MAE | Holt-Winters MAE (change; cap) | LightGBM MAE (change; cap) |
|---|---:|---:|---:|
| validation_1 | 1,101.5940 | 1,195.5661 (+8.5306%; pass) | 1,051.4335 (-4.5534%; pass) |
| validation_2 | 2,269.7721 | 1,136.8306 (-49.9143%; pass) | 790.9941 (-65.1509%; pass) |
| validation_3 | 1,596.5170 | 1,501.5664 (-5.9474%; pass) | 794.3741 (-50.2433%; pass) |

The pooled horizon-block comparisons also pass for LightGBM and fail only for Holt-Winters h8–14:

| Horizon block | Seasonal Naive MAE | Holt-Winters MAE (change; cap) | LightGBM MAE (change; cap) |
|---|---:|---:|---:|
| h1–7 | 2,136.3558 | 1,155.6570 (-45.9052%; pass) | 643.0551 (-69.8994%; pass) |
| h8–14 | 1,235.4154 | 1,405.2746 (+13.7492%; fail) | 1,094.4426 (-11.4110%; pass) |

The selection output retains the weaker h2 and h9 Sunday results and h10 Monday result: their
LightGBM MAEs are 1,572.8966 (97 rows), 1,707.5285 (96 rows) and 2,280.9889 (3,344 rows),
versus Seasonal Naive MAEs 861.8763, 752.7188 and 1,025.8322. No per-horizon veto was introduced.

The selected recipe exactly matches the reviewed LightGBM candidate configuration: global CPU
GBDT regression L1, trial A, 180 rounds and the ordered 29 Phase 3 predictors. It is a recipe only;
`fit_performed=false`, `no_tuning_or_refit_performed=true`, and no fitted future July model was
generated. The four selected artifacts share the run ID above. Their SHA-256 hashes, plus the two
comparison outputs and completed manifest, are:

| Generated artifact | SHA-256 |
|---|---|
| `selected_model_config.json` | `de53a477b4bed768a9fbaa459e7f347be28c05063f5c5e379c0dfbb40d21960b` |
| `refit_recipe.json` | `9ef3ee340ac57f14394857203ca3de5445ebae70972ec541a51947f38a49f799` |
| `selected_development_forecasts.parquet` | `72566349b233ef26c8de5b4f9c1623ac66df8676ad0370ad63b192ed4c1b5b09` |
| `development_residual_paths.parquet` | `509bb4a822157850e8fb0309114a4003b98bcbc6b56f4a49244d8b6593e03382` |
| `model_comparison.csv` | `c648e8e407dc367e56f26cb421656dabc8d742a9a3cd3d3b092b746a84b10357` |
| `selection_decision.json` | `02c00b7f0b72e260db03b6f786e443db93844a146f3a93fb8c4c4ea076f2e5de` |
| `manifest.json` | `03a1f26ba5855fd0576667bf280df938664c196a802de0a71e696a600b281cdc` |

The manifest binds the review input at SHA-256
`9ef1c1fa28fc12db318d510a5ae48a29fd2198116a0114e0d5ee866dc66d7516`. Its selection code revision
is reviewed PR #13 head `ca3d51fff53e6e98b55fae2ac84a5cfe1af7324a`, with current source hash
`20028b1133053489f8b3a68b5a38b272e7bf8a9947581395f96e64e5d57be997`; the runner records a
modified worktree because the review input and this record were present. No forecasting source or
runner code differed from that reviewed head. The original cached provenance limitations remain:
legacy SN/HW manifests lack modern source-code/lock identity, and the LightGBM manifest records its
historical modified-worktree run. All seven published files remain Git-ignored.

Residual checks verified the signed definition `actual_sales - forecast`, raw-primary masks,
operational masks and their complete/partial counts. Every Store-origin path has exactly horizons
1–14; 96 raw-primary paths are complete and 3,249 are partial because closed-day labels are not in
the primary population. All 3,345 operational paths are complete under the saved Open routing.
Closed-day raw residuals remain descriptive and excluded from primary metrics; unavailable values
were not filled. The manifest records no July 4–31 read/hash/forecast/evaluation and
`phase_8_started=false`; no Phase 8 work began.

Acceptance quality checks: full pytest passed **187 tests** on Python 3.14.5 (71.21s) and **187
tests** on Python 3.12.15 (69.61s); Ruff lint passed; Ruff format check passed (73 files); the
documentation checker passed (115 local destinations/anchors across 22 Markdown files);
`uv lock --check` resolved 84 packages; Python 3.14 `pip check` and locked Python 3.12 `uv pip
check` (60 packages) passed; `git diff --check` passed. The runner output and all original
candidate hashes were independently reverified after publication. No implementation code, tests,
dependencies or methodology changed. No candidate was fit or tuned and no protected outcome was
read or hashed.

## Phase 7 formal closeout and Phase 8 evidence audit — 2026-10-06

GitHub and fetched `origin/main` verify PR #13 merged at
`89bcb861642ee28259e4a402e8e8ee98a999a6e5`. Its integrated tree matches the reviewed final head
`688d673f3ebaf802cbe47f9fa3236fcb4aaa3dea`; final-head Quality run #25 passed Python 3.12 and
3.14. The accepted external review, verified integration and this explicitly authorized closeout
make Phase 7 **COMPLETE**. The [completed plan](../plans/completed/phase-7-model-selection.md)
preserves historical approval, implementation and selection checkpoints. ADR-020 and the selected
`global_lightgbm_gbdt_regression_l1` identity remain unchanged: frozen trial A, 180 rounds,
29 predictors and the same raw recursive/operational routing behavior.

The clean `docs/phase-8-uncertainty-design` branch started from that latest `origin/main`.
A read-only audit of existing ignored development exports verified the seven selection-file
hashes above and all 34 original candidate artifacts; no source dataset or protected outcomes were
read or hashed. The selected run ID remains `365f22d4c3f94722a594ab934a22c4f6`. Recipe and
manifest still record no refit, tuning or future-origin forecasting. Historical candidate
provenance limitations remain disclosed rather than being repaired by regenerating evidence.

The residual export has 35 fields and 46,830 unique Store-origin-Date rows, ending 2015-07-03:
3,345 paths with exactly h1–14. Masks, signed residuals (`actual_sales - forecast`), path flags
and saved Open routing match the implementation. No target keys are absent, no Open values are
unknown, and all required labels/forecasts are finite in these saved records.

| Audited population | Result and interpretation |
|---|---|
| Complete raw-primary H14 paths | 96, from the same 32 distinct stores in each of three origins; 3,249 paths are partial. Closed labels are outside the raw-primary Open=1 population. |
| Complete operational H14 paths | 3,345, covering all 1,115 stores per origin under saved Open routing. |
| Observed closed-day rows | 8,277, all with actual Sales=0 and routed forecast=0. These are observed turnover outcomes, not imputed missing residuals or uncensored physical demand. |
| Raw-primary counts at sparse h2 / h3 / h9, validation_1 | 32 / 33 / 32. |
| Raw-primary counts at h2 / h9, validation_1 + validation_2 | 65 / 64, reusing only 33 / 32 distinct stores across two origins. |

Operational completeness depends on using saved historical Open. This does not establish that
the schedule was known at origin. The proposed Phase 8 plan explicitly separates that unverified
availability from a newly proposed, conditional offline replay assumption; unknown future Open
must remain operationally unavailable.

### Phase 8 design checkpoint

At the reviewed PR #14 design head, the [Phase 8 plan active at that checkpoint](../plans/completed/phase-8-forecast-uncertainty.md)
was **PROPOSED / AWAITING APPROVAL** and included a draft ADR-021. The 2026-10-06 approval sync
below supersedes that proposal checkpoint; the accepted methodology is recorded in ADR-021.

No uncertainty runner or tests were added; no intervals, empirical quantile values, inventory
outcomes or new forecasts were calculated. Phase 8 implementation and Phases 9–10 remain
unstarted. Final-holdout outcomes for 2015-07-04 through 2015-07-31 remain protected under ADR-015;
their release requires the separately authorized frozen Phase 13 protocol.

### Phase 8 design delivery validation

Executed on Python 3.14.5 in the development environment with uv 0.12.23; a subsequent
`uv sync --locked --extra dev --python 3.14` verified the same environment (60 managed packages,
no package changes):

| Check | Result |
|---|---|
| Full `python -m pytest` | PASS — 187 tests in 87.93s; existing fixtures only |
| `python -m ruff check .` | PASS |
| `python -m ruff format --check .` | PASS — 74 files already formatted |
| `python scripts/check_docs.py` | PASS — 146 local destinations/anchors across 23 Markdown files |
| `uv lock --check` | PASS — 84 packages resolved; lock unchanged |
| `uv pip check` | PASS — 61 compatible installed packages |
| `git diff --check` | PASS |

Complete diff review confirms changes are limited to Phase 7 lifecycle closeout/archive, the
Phase 8 proposal and mechanical links/current-status synchronization. No code, tests, dependencies,
proposal or selected artifacts
changed. New-PR CI is not yet verified; delivery stops after opening the authorized design PR.

## Phase 8 methodology approval sync — 2026-10-06

The external Phase 8 methodology review is accepted in [ADR-021](DECISIONS.md#adr-021--chronological-empirical-forecast-uncertainty-and-conditional-operational-replay).
Phase 8 is **APPROVED / IMPLEMENTATION NOT STARTED**. PR #14 remains open and unmerged as the
design integration gate; implementation of the approved bounded protocol may begin after it
integrates into `main`.

Approval fixes the daily signed-residual estimator, exact horizon-specific ranks and n>=40 floor,
Fit A/Fit B chronology, and the complete operational-prefix estimator with p={0.90,0.95,0.98},
upper-rank rule and n>=50 floor. The saved historical Open values authorize development-only
conditional course replay and do not prove origin-time schedule availability. For Phase 13, actual
holdout Open must not be read, hashed, loaded or substituted before issuance; operational outputs
requiring future Open remain unavailable without separately reviewed origin-known schedule
provenance or a separately approved synthetic/conditional schedule that is not derived from
protected actual Open.

No uncertainty runner, fixture tests, interval calculations, quantile tables or fitted-table
freeze were produced in this approval sync. Fit B's actual tables, diagnostics, hashes and
availability require separate external implementation/results review before the values are
frozen. No Phase 9/10 implementation, final-holdout access or evaluation occurred; protected
2015-07-04 through 2015-07-31 outcomes remain unreleased.

Approval-sync local validation on Python 3.14.5 with the locked environment:

| Check | Result |
|---|---|
| Full `python -m pytest` | PASS — 187 tests in 92.93s; existing fixtures only |
| `python -m ruff check .` | PASS |
| `python -m ruff format --check .` | PASS — 74 files already formatted |
| `python scripts/check_docs.py` | PASS — 148 local destinations/anchors across 23 Markdown files |
| `uv lock --check` | PASS — 84 packages resolved; lock unchanged |
| `uv pip check` | PASS — 61 installed packages compatible |
| `git diff --check` | PASS |

## Phase 8 development-only implementation checkpoint - 2026-10-06

The approved ADR-021 implementation is **IMPLEMENTED / UNDER REVIEW** on branch
`feat/phase-8-uncertainty-implementation`, based on merged PR #14 commit
`305ddc80a4e3399698f64762ec26da2fc79cfb10`. Implementation PR
[#15](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/15) is open and
unmerged; external implementation/results review is pending. The selected Phase 7 identity remains
`global_lightgbm_gbdt_regression_l1`; this work reads its saved paths only and performs no point
model fit, refit, tuning or selection change.

The canonical development run is `phase8-impl-20261006-final`, under the ignored directory
`data/processed/uncertainty/phase8-impl-20261006-final/`. An earlier implementation-validation run,
`phase8-impl-20261006`, is retained as an immutable prior run; `current.json` points to the canonical
run recorded here. Its manifest status is
`complete_with_unavailable_strata`; dates are 2015-05-23 through 2015-07-03 across the three
approved development windows. The run read 46,830 selected residual-path rows, with 38,553
Open=1 raw-primary errors and 46,830 routed operational errors. The saved Phase 7 outputs,
selected candidate manifest and all three original candidate output sets were SHA-256 verified
before and after the run; every input hash was unchanged. The run did not read or hash source
datasets or protected July 4-31 Open, Sales or Customers values.

Fit A has 22 of 28 daily tail strata available. Its h2 (n=32), h3 (n=33) and h9 (n=32) lower and
upper tails remain unavailable as `insufficient_calibration`; no neighboring-horizon fallback
was used. Fit B has 28 of 28 daily tail strata available. All 42 cumulative `(k,p)` strata are
available for each fit: 1,115 complete calibration Store-origin prefixes for Fit A and 2,230 for
Fit B at every k=1-14. The saved schedule interpretation is explicitly
`saved_source_open_assumed_known_at_origin`, a conditional historical replay. Empirical coverage
and width diagnostics are descriptive and have no approved numeric acceptance threshold or
production/service guarantee. Fit B fitted values remain unfrozen pending external review.

The run manifest records source revision `305ddc80a4e3399698f64762ec26da2fc79cfb10`,
`worktree_modified=true`, implementation source hash
`993e9e687eaa3ec3f662e0851e57a8fd7c93c499642c13c5d0a103cd6f36edce`, and `uv.lock` hash
`584337e365e653d97731b73c6d9e2292c4224bee524f0225ddf3221b0aa0f5d0`. Output row counts and
hashes are recorded in that manifest; primary table identities are:

| Artifact | Rows | SHA-256 |
|---|---:|---|
| `calibration_config.json` | - | `afe563632a2ebff937f1500f568d53cdb93be35d6dc299654464c2615ae64a08` |
| `daily_residual_quantiles.csv` | 56 | `5c985c912d14b502a5d370090353624907e7fddd6d0d8552c102ee3a1ad7eda8` |
| `cumulative_error_quantiles.csv` | 84 | `1a0bba7916b498f2048f080dcd3b24f6cd47472d2f71fca92b94f1b678cb70ff` |
| `daily_intervals.parquet` | 62,440 | `160e68f4dd0237b61e60d20d041e06d0760fd94b006f7e89730e24e96b601fd2` |
| `cumulative_uncertainty.parquet` | 93,660 | `f338ff7189d652e64c8aa27f3d03c205c313185fb205f9f8a50b9776d59c0a0e` |
| `coverage_diagnostics.csv` | 392 | `7517435e7e4dd4bf0d08aa705c3555bb1ea945d6cae3dff8db8dfdf46ca0aaa4` |

| Check | Result |
|---|---|
| Full `python -m pytest` | PASS - 199 tests in 92.05s |
| `python -m ruff check .` | PASS |
| `python -m ruff format --check .` | PASS - 77 files already formatted |
| `python scripts/check_docs.py` | PASS - 149 local destinations/anchors across 23 Markdown files |
| `uv lock --check` | PASS - 84 packages resolved; lock unchanged |
| `git diff --check` | PASS |

The implementation adds `src/rossmann_forecasting/forecasting/uncertainty.py`,
`scripts/run_forecast_uncertainty.py` and fixture coverage in `tests/test_uncertainty.py`. It also
updates this state record, the Phase 8 active plan, README usage/state text, and the ignored-data
layout guide. No ADR-021 methodology, Phase 7 algorithm/artifact, proposal, inventory layer,
Phase 9/10 work or final-holdout protocol changed. Canonical run manifest SHA-256 is
`d32ea0d3de331fc9e61ece091742edd8d23291383a2bb64779a1af945073a2bb`; its canonical policy/config hash is
`49f4811bf7b01ffe6472ea76233eefa50e211207aa0b6246dada934cd4611d93`. Whole-repository checks on
Python 3.14.5 with the locked environment passed as listed above.

## Phase 8 targeted provenance and results review (2026-10-06)

PR #15 remains **OPEN / UNMERGED**; Phase 8 remains **IMPLEMENTED / UNDER REVIEW**, and Fit B is
**UNFROZEN**. The focused follow-up did not change ADR-021, quantile ranks/sample floors, Fit A/B
chronology, the selected LightGBM recipe, conditional saved-Open replay, or the final-holdout
firewall.

### Post-computation input-integrity gate

After estimation and staged-output verification, the runner now reruns the same allowlisted Phase 7
integrity verifier and compares the complete canonical input-lineage snapshot with the identities
verified before computation. The second pass rechecks the Phase 7 selection manifest and all six
manifest-listed selection outputs, then the three original candidate manifests and all 34
manifest-listed candidate artifacts. Candidate paths must still match the reviewed allowlist and
Parquet Date metadata must still stop by 2015-07-03 before file hashing. A failed recheck occurs
before the run manifest, official run-directory rename, or `current.json` update; staging is
removed, and earlier runs/current pointer remain unchanged. No raw/interim or unexpected source
path is opened or hashed.

A targeted fixture mutates the previously verified residual-path artifact during uncertainty
calculation. The post-computation identity comparison rejects publication; the fixture confirms
that an existing run and pointer retain their exact bytes and no failed run/staging directory is
left behind.

### New canonical development run and provenance

After the code fix, the runner published `phase8-impl-20261006-provenance-review` and atomically
advanced `current.json` to it. Both earlier immutable runs, `phase8-impl-20261006` and
`phase8-impl-20261006-final`, and every listed output hash in those runs were checked before and
after and remained unchanged. The runner's post-computation pass and an independent post-run
verification matched the initial Phase 7 input identities. The new manifest records all six Phase
7 selection outputs, all three original candidate manifests, and all 34 candidate-artifact hashes.

The new run manifest SHA-256 is
`63a00fc8c50ccff99360cd8790498e977e08ec6a9846780a4e1a8ab3498d71c2`. Its current implementation
source SHA-256 is `b89e3a9f16e5395632b2de55be90327aad6e546ead4251812606a878cabad04b`, matching the
source bytes measured for the new run; `uv.lock` remains
`584337e365e653d97731b73c6d9e2292c4224bee524f0225ddf3221b0aa0f5d0`. The prior canonical run
recorded source hash `993e9e687eaa3ec3f662e0851e57a8fd7c93c499642c13c5d0a103cd6f36edce`; direct
source-byte hashing confirmed that it matched the then-current implementation before this fix. It
does not match the implementation after adding the integrity gate. The new run's recorded Git
revision is `95d988abb0e381ed3c4b0aab58218435b494ee39` with `worktree_modified=true`; its source
hash, rather than Git revision alone, identifies the code bytes used.

The selected Phase 7 lineage remains unchanged: selection manifest
`03a1f26ba5855fd0576667bf280df938664c196a802de0a71e696a600b281cdc`; selected residual paths
`509bb4a822157850e8fb0309114a4003b98bcbc6b56f4a49244d8b6593e03382`; selected forecasts
`72566349b233ef26c8de5b4f9c1623ac66df8676ad0370ad63b192ed4c1b5b09`; recipe
`9ef3ee340ac57f14394857203ca3de5445ebae70972ec541a51947f38a49f799`; and original candidate
manifest hashes remain SN `f5e3a18a0a8bff709cb06b4e6282e22cbe3f84668937d3c3e57245b7c76072e3`, HW
`37b46babad1d197143bfda2f4f11aa65291c350b6b0687410bc4496b7171903b`, LightGBM
`ddd379fe4264dd90f618ba57791b97fcce3fd64199ffe95410c4f0d0695810c1`. The new output artifact
hashes match the prior canonical output hashes byte-for-byte; the new run ID and manifest bind this
publication to the post-fix code.

### Chronological assessment results

The run covers 46,830 selected residual-path rows from 2015-05-23 through 2015-07-03, with 38,553
raw-primary Open=1 errors and 46,830 conditional operational errors. Fit A assesses validation_2
(origin 2015-06-05); Fit B assesses validation_3 (origin 2015-06-19). Daily widths below use only
available raw-primary intervals; coverage denominators are the usable assessed interval rows.

| Fit | Open=1 labels | Daily intervals available | Availability | Hits / usable denominator | Empirical coverage | Width n | Mean width | Median width |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A | 13,438 | 12,258 | 91.22% | 10,344 / 12,258 | 84.39% | 12,258 | 4,128.75 | 4,203.37 |
| B | 13,437 | 13,437 | 100.00% | 12,263 / 13,437 | 91.26% | 13,437 | 4,116.49 | 4,152.12 |

Individual horizon diagnostics retain the approved sparse-stratum reasons and expose calibration
sample sizes separately from assessment denominators:

| Fit / horizon | Calibration n (distinct stores) | Assessment Open=1 eligible | Available / usable | Hits / usable | Coverage | Mean / median width |
|---|---:|---:|---:|---:|---:|---:|
| A / h2 | 32 (32) | 33 | 0 / 0 | - | unavailable | - |
| A / h3 | 33 (33) | 1,115 | 0 / 0 | - | unavailable | - |
| A / h9 | 32 (32) | 32 | 0 / 0 | - | unavailable | - |
| A / h10 | 1,115 | 1,114 | 1,114 / 1,114 | 1,084 / 1,114 | 97.31% | 7,382.53 / 7,382.53 |
| B / h2 | 65 (33) | 32 | 32 / 32 | 32 / 32 | 100.00% | 13,870.23 / 13,870.23 |
| B / h9 | 64 (32) | 32 | 32 / 32 | 32 / 32 | 100.00% | 15,183.32 / 15,212.95 |
| B / h10 | 2,229 | 1,115 | 1,115 / 1,115 | 1,069 / 1,115 | 95.87% | 6,873.54 / 6,873.54 |

Both tails at Fit A h2, h3, and h9 remain unavailable as `insufficient_calibration`; their
assessment populations include 33, 1,115, and 32 Open=1 labels respectively, with zero usable
intervals. No coverage value is reported where the issued interval is unavailable. Fit B h2/h9
results use only 33/32 distinct calibration stores across two origins and remain fragile despite
valid support.

| Fit | Operational population | Label-eligible rows | Available / eligible | Hits / usable denominator | Coverage |
|---|---|---:|---:|---:|---:|
| A | Open=1 | 13,438 | 12,258 / 13,438 (91.22%) | 10,344 / 12,258 | 84.39% |
| A | Open=0 | 2,172 | 2,172 / 2,172 (100.00%) | 2,172 / 2,172 | 100.00% |
| A | Pooled | 15,610 | 14,430 / 15,610 (92.44%) | 12,516 / 14,430 | 86.74% |
| B | Open=1 | 13,437 | 13,437 / 13,437 (100.00%) | 12,263 / 13,437 | 91.26% |
| B | Open=0 | 2,173 | 2,173 / 2,173 (100.00%) | 2,173 / 2,173 | 100.00% |
| B | Pooled | 15,610 | 15,610 / 15,610 (100.00%) | 14,436 / 15,610 | 92.48% |

Deterministic closed `[0,0]` routes account for 15.05% of Fit A's pooled usable denominator and
13.92% of Fit B's. Pooled coverage is respectively 2.35 and 1.22 percentage points above the
Open=1 branch. The diagnostics record zero Open=0 / positive-Sales violations for both fits.
This closure-driven increase is conditional-replay coverage inflation, not raw-model accuracy.

Cumulative upper-bound results are coverage of assessed actual operational prefixes `actual_total
<= U_k`. Every cell has 1,115 complete assessment prefixes and 1,115 available bounds; calibration
support is 1,115 prefixes for Fit A and 2,230 for Fit B. There are no unavailable reasons for
k=3..8.

| k | Fit A p=.90 | Fit A p=.95 | Fit A p=.98 | Fit B p=.90 | Fit B p=.95 | Fit B p=.98 |
|---:|---:|---:|---:|---:|---:|---:|
| 3 | 861/1,115 (77.22%) | 970/1,115 (87.00%) | 1,075/1,115 (96.41%) | 1,040/1,115 (93.27%) | 1,079/1,115 (96.77%) | 1,101/1,115 (98.74%) |
| 4 | 1,044/1,115 (93.63%) | 1,070/1,115 (95.96%) | 1,101/1,115 (98.74%) | 1,095/1,115 (98.21%) | 1,102/1,115 (98.83%) | 1,107/1,115 (99.28%) |
| 5 | 1,044/1,115 (93.63%) | 1,084/1,115 (97.22%) | 1,100/1,115 (98.65%) | 1,096/1,115 (98.30%) | 1,101/1,115 (98.74%) | 1,107/1,115 (99.28%) |
| 6 | 1,047/1,115 (93.90%) | 1,091/1,115 (97.85%) | 1,100/1,115 (98.65%) | 1,098/1,115 (98.48%) | 1,107/1,115 (99.28%) | 1,110/1,115 (99.55%) |
| 7 | 1,100/1,115 (98.65%) | 1,105/1,115 (99.10%) | 1,107/1,115 (99.28%) | 1,106/1,115 (99.19%) | 1,110/1,115 (99.55%) | 1,111/1,115 (99.64%) |
| 8 | 1,103/1,115 (98.92%) | 1,106/1,115 (99.19%) | 1,111/1,115 (99.64%) | 1,106/1,115 (99.19%) | 1,110/1,115 (99.55%) | 1,110/1,115 (99.55%) |

Across k=1..14 pooled by the 15,610 assessed prefixes per level, Fit A coverage is 15,009/15,610
(96.15%) at p=.90, 15,271/15,610 (97.83%) at p=.95, and 15,467/15,610 (99.08%) at p=.98.
Fit B coverage is 15,058/15,610 (96.46%), 15,317/15,610 (98.12%), and 15,477/15,610 (99.15%),
respectively. These repeated, dependent prefixes are descriptive, not independent replications or
service guarantees.

New run output hashes (byte-identical to the earlier canonical run's six outputs):

| Artifact | Rows | SHA-256 |
|---|---:|---|
| `calibration_config.json` | - | `afe563632a2ebff937f1500f568d53cdb93be35d6dc299654464c2615ae64a08` |
| `daily_residual_quantiles.csv` | 56 | `5c985c912d14b502a5d370090353624907e7fddd6d0d8552c102ee3a1ad7eda8` |
| `cumulative_error_quantiles.csv` | 84 | `1a0bba7916b498f2048f080dcd3b24f6cd47472d2f71fca92b94f1b678cb70ff` |
| `daily_intervals.parquet` | 62,440 | `160e68f4dd0237b61e60d20d041e06d0760fd94b006f7e89730e24e96b601fd2` |
| `cumulative_uncertainty.parquet` | 93,660 | `f338ff7189d652e64c8aa27f3d03c205c313185fb205f9f8a50b9776d59c0a0e` |
| `coverage_diagnostics.csv` | 392 | `7517435e7e4dd4bf0d08aa705c3555bb1ea945d6cae3dff8db8dfdf46ca0aaa4` |

| Follow-up check | Result |
|---|---|
| Focused Phase 8 fixtures | PASS - 13 tests in 28.98s |
| Full `python -m pytest` | PASS - 200 tests in 95.14s |
| `python -m ruff check .` | PASS |
| `python -m ruff format --check .` | PASS - 77 files already formatted |
| `python scripts/check_docs.py` | PASS - 149 local destinations/anchors across 23 Markdown files |
| `uv lock --check` | PASS - 84 packages resolved; lock unchanged |
| Python 3.14 `pip check` | PASS - no broken requirements |
| `git diff --check` | PASS - only Git's expected LF-to-CRLF notices for the two edited Python files |

The implementation adds no model fit/refit/tuning or methodology change; the selected identity
remains `global_lightgbm_gbdt_regression_l1`. No raw/interim data or protected July 4-31 Open, Sales
or Customers were read, loaded or hashed. Fit B stays unfrozen pending external results review;
Phase 8 remains under review and Phases 9-10 remain unstarted.

## Phase 8 external results acceptance and Fit B freeze — 2026-10-07 (historical pre-closeout checkpoint)

GitHub confirms PR #15 was squash-merged into `main` at
`c694f5922a1c1e58ffaf9c2437fd9698ca3e5821`. The external reviewer decision supplied for the
canonical Phase 8 results is **ACCEPT**: all 56 daily quantiles, 84 cumulative quantiles, 62,440
issued daily interval records, 93,660 cumulative records, and all 392 diagnostics passed independent
numerical review. This acceptance freezes the Fit B fitted quantile values only for the exact
canonical run `phase8-impl-20261006-provenance-review` below. It does not change ADR-021, the Phase 7
selected recipe, or any saved artifact.

| Frozen Fit B identity | SHA-256 |
|---|---|
| Canonical run manifest | `63a00fc8c50ccff99360cd8790498e977e08ec6a9846780a4e1a8ab3498d71c2` |
| `daily_residual_quantiles.csv` | `5c985c912d14b502a5d370090353624907e7fddd6d0d8552c102ee3a1ad7eda8` |
| `cumulative_error_quantiles.csv` | `1a0bba7916b498f2048f080dcd3b24f6cd47472d2f71fca92b94f1b678cb70ff` |
| Canonical policy/config identity | `49f4811bf7b01ffe6472ea76233eefa50e211207aa0b6246dada934cd4611d93` |
| `calibration_config.json` file SHA-256 (separate file identity) | `afe563632a2ebff937f1500f568d53cdb93be35d6dc299654464c2615ae64a08` |

The immutable run was published before this review and its manifest/config retain their recorded
publication-time state (`external_fit_b_results_review_pending=true`,
`fit_b_quantiles_frozen=false`). The later dated acceptance above is the governance record that
freezes Fit B for those exact table/config identities; no canonical run, quantile, source artifact,
or pointer was rewritten or regenerated.

The review accepted the numerical record without establishing nominal coverage as a pass threshold.
Fit B raw-primary daily assessment coverage is **12,263/13,437 (91.26%)**, below nominal 95%, with
100% interval availability. Fit B h2/h9 calibration uses 65/64 rows but only 33/32 distinct stores
across two origins; the 32/32 assessment hits at each Sunday horizon remain fragile evidence. Fit A
h2/h3/h9 remain unavailable under the approved sample floor.

Under the conditional `saved_source_open_assumed_known_at_origin` replay, Fit B operational coverage
is 12,263/13,437 (91.26%) for Open=1, 2,173/2,173 (100%) for Open=0, and 14,436/15,610 (92.48%)
pooled. The deterministic closed `[0,0]` branch contributes 13.92% of the pooled usable denominator
and raises pooled coverage by 1.22 percentage points over Open=1. This is closure-driven inflation,
not raw-model accuracy or evidence that source Open was known prospectively. The saved schedule is
conditional; the dataset does not establish origin-time schedule availability.

The three Friday origins share stores and calendar shocks, and observations are dependent across
stores and origins. Accepted empirical coverage remains descriptive: there is no conformal validity,
per-store guarantee, or production/service guarantee. Cumulative values apply only to the approved
origin-anchored prefixes; no daily-review suffix calibration is authorized for Phase 10. The
2015-07-04 through 2015-07-31 final holdout remains protected under ADR-015 and was not accessed.
The selected identity remains `global_lightgbm_gbdt_regression_l1` (trial A, 180 rounds). No Phase
9/10 work has started.

### Documentation integration validation — 2026-10-07 (historical pre-closeout checkpoint)

| Check | Result |
|---|---|
| Full `python -m pytest` (Python 3.14.5) | PASS — 200 tests in 96.50s |
| `python -m ruff check .` | PASS |
| `python -m ruff format --check .` | PASS — 77 files already formatted |
| `python scripts/check_docs.py` | PASS — 150 local destinations/anchors across 23 Markdown files |
| `uv lock --check` (uv 0.12.23) | PASS — 84 packages resolved; lock unchanged |
| Python 3.14 `pip check` | PASS — no broken requirements |
| `git diff --check` | PASS |

The pinned uv executable was isolated in a temporary directory for the lock check; the project
environment and `uv.lock` were not changed.

**Lifecycle:** Phase 8 is **REVIEWED / FORMAL CLOSEOUT PENDING**, not COMPLETE. Keep the active plan
in place. This documentation/governance change must first be reviewed and integrated; afterward,
perform a separate explicit closeout verification against the merged PR, accepted review, frozen
artifact identities, and holdout firewall. Only that authorized closeout may mark Phase 8 COMPLETE
and archive the plan.

## Phase 8 formal closeout — 2026-10-07

The closeout branch started from fetched `origin/main` at
`4dd7717fed57ff3b1f14789b980772c1968f3cba`. GitHub reports PR #15 and PR #16 as merged; the
verified squash-merge commits are `c694f5922a1c1e58ffaf9c2437fd9698ca3e5821` and
`4dd7717fed57ff3b1f14789b980772c1968f3cba`, respectively. Both commits are ancestors of
`origin/main`, and PR #16's merge commit directly follows PR #15's merge commit.

The independent external results review ACCEPTED the canonical development results: all 56 daily
quantiles, 84 cumulative quantiles, 62,440 daily interval records, 93,660 cumulative records, and
392 diagnostics. The Fit B freeze record is present on merged `main`. The canonical run is
`phase8-impl-20261006-provenance-review`; its immutable local artifacts were available and checked
without regeneration:

| Frozen identity | SHA-256 | Local artifact verification |
|---|---|---|
| Run manifest | `63a00fc8c50ccff99360cd8790498e977e08ec6a9846780a4e1a8ab3498d71c2` | Match |
| Daily quantiles | `5c985c912d14b502a5d370090353624907e7fddd6d0d8552c102ee3a1ad7eda8` | Match |
| Cumulative quantiles | `1a0bba7916b498f2048f080dcd3b24f6cd47472d2f71fca92b94f1b678cb70ff` | Match |
| Canonical policy/config identity | `49f4811bf7b01ffe6472ea76233eefa50e211207aa0b6246dada934cd4611d93` | Match to the config's self-excluding canonical identity |
| `calibration_config.json` file | `afe563632a2ebff937f1500f568d53cdb93be35d6dc299654464c2615ae64a08` | Match |

The immutable run manifest retains its original publication-time flags:
`external_fit_b_results_review_pending=true` and `fit_b_quantiles_frozen=false`. The later
governance freeze does not rewrite the manifest, config, quantile tables, other run artifacts, or
current pointer. ADR-021 and the selected LightGBM recipe are unchanged.

**Closeout decision:** Phase 8 is **COMPLETE** as of 2026-10-07 based on verified PR #15/#16
integration, independent results acceptance, frozen identity checks, and confirmation of the
holdout firewall. The explicit acceptance limitations remain:

- Fit B raw-primary coverage is 12,263/13,437 (91.26%), below nominal 95%.
- Sunday h2/h9 calibration is sparse: 65/64 rows from 33/32 distinct stores across two origins.
- Forecast errors are dependent across stores and forecast origins.
- Operational results are a conditional historical replay assuming saved source Open was known at
  origin. Fit B's 14,436/15,610 (92.48%) pooled coverage is closure-inflated relative to its
  12,263/13,437 (91.26%) Open=1 coverage; deterministic closed routes contribute 13.92% of the
  pooled usable denominator.
- No conformal, per-store, production, or service-level guarantee is established.
- Cumulative quantiles apply only to approved origin-anchored prefixes. No later daily-review
  suffix calibration is authorized.
- The protected 2015-07-04 through 2015-07-31 final holdout remains unreleased.
- The target is monetary Sales turnover, not SKU-level physical demand.

At this Phase 8 closeout checkpoint, Phase 9 was PLANNED and Phase 10 had not started. The closeout
changed documentation only and did not change implementation, calibration results, quantile tables,
model artifacts, or dependencies.

### Formal closeout quality gates — 2026-10-07

| Check | Result |
|---|---|
| Full `python -m pytest` (Python 3.14.5) | PASS — 200 tests |
| Ruff lint | PASS — `ruff check .` |
| Ruff format | PASS — 77 files already formatted |
| Documentation link checker | PASS — 154 local destinations/anchors across 23 Markdown files |
| `uv lock --check` (uv 0.12.23) | PASS — 84 packages resolved; lock unchanged |
| Python 3.14 `pip check` | PASS — no broken requirements |
| `git diff --check` | PASS — no whitespace errors |

The project virtual environment was used for Python/Ruff checks. Pinned uv 0.12.23 was run from
a temporary directory because no uv executable was installed on PATH; `uv.lock` and project
dependencies remain unchanged.

## Phase 9 design proposal — 2026-10-07 (historical proposal checkpoint)

**State at this historical proposal checkpoint:** Design **PROPOSED / AWAITING APPROVAL**. Phase 9
implementation had not started, and Phase 10 remained PLANNED / NOT STARTED. External methodology
acceptance and implementation authorization were the next boundary.

Fetched `origin/main` and verified
[PR #17](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/17) merged at
`f08a62aa980d0670186ed25ae1f6e5a018ff3781`. That commit is the clean base of
`docs/phase-9-inventory-design` and contains PR #15/#16 and the accepted Phase 8 closeout.
Unrelated worktree changes were absent at branch creation.

The [Phase 9 plan, now completed](../plans/completed/phase-9-synthetic-inventory.md) and
[proposal-stage ADR-022, now accepted](DECISIONS.md#adr-022--synthetic-monetary-scenario-contract) specify:

- Two development origins, June 5/June 19, H14 ending by July 3; 56-day Open=1 turnover anchors
  with a 28-row minimum, preserved missingness and cold-start retail-equivalent stock.
- Fixed seed 4209, exact keyed draws, five paired replicates, eight synthetic stress families,
  synthetic schedules/promotions/trend/seasonality and shared-shock dependencies.
- Explicit procurement conversion, carrying/unmet-value costs, display-only equivalent units,
  schema/keys/nullability, immutable artifacts/manifest hashes, failure behavior and planned
  fixture/numerical acceptance criteria.
- Separate observed Sales, frozen point forecasts/uncertainty and synthetic quantities.
  No synthetic feature enters LightGBM. No inferred physical/latent demand or real stockout.
- Phase 10 receives exogenous paths/parameters and provenance only; event order, queue,
  policies, KPIs and cost aggregation require its own design.

Open Phase 9 approval choices are the anchor/initial state, cost assumptions, deterministic
scenario/schedule specification and lineage/availability contract. The plan supplies concrete
recommended defaults for each. Phase 10's later daily-review suffix method is unresolved;
Phase 8 q values remain origin-prefix-only and do not automatically transport to synthetic
stress. Fit A is bound to June 5, Fit B to June 19; frozen artifacts are not altered.

This checkpoint adds no generated results. It references the previously accepted Phase 8
identities without new local artifact verification. Fit B raw-primary coverage remains
12,263/13,437 (91.26%), below nominal 95%; sparse Sunday h2/h9, store/origin dependence,
conditional saved-source-Open replay and closure-inflated pooled coverage remain disclosed.
No conformal, per-store, production or service-level guarantee is introduced.
The protected 2015-07-04 through 2015-07-31 holdout remains unreleased.

## Phase 9 methodology approval — 2026-10-07 (historical approval checkpoint)

**Decision:** External methodology review **ACCEPTED** the Phase 9 design at PR #18's reviewed
head `3820c2c34749b3baa4df954afc3daa0636cff271`. The decision was supplied for this
synchronization; the reviewer identity was not specified. The current design state is
**APPROVED / IMPLEMENTATION NOT STARTED**. The historical proposal checkpoint above retains its
original PROPOSED / AWAITING APPROVAL state.

The approval covers the four choices recorded in [ADR-022](DECISIONS.md#adr-022--synthetic-monetary-scenario-contract)
and the [Phase 9 plan, now completed](../plans/completed/phase-9-synthetic-inventory.md): origin-safe
56-day/Open=1 initialization with a 28-record floor, no imputation/fallback, zero anchors and
an empty initial order pipeline; illustrative c/a/g cost ranges and approved formulas; seed
4209's exact SHA-256 draw contract and paired synthetic scenario families; and the two-origin
development chronology, frozen Phase 7/8 bindings and immutable fail-closed artifacts.

**Required weekday-factor clarification:** Monday–Sunday factors sum to 7 and average 1 over
the calendar week. The default Monday–Saturday open-day factors sum to 6.20 and average
1.033333... . They are illustrative synthetic multipliers, not open-day-normalized factors
preserving the historical anchor's mean. The accepted factor values and generation formula
were not changed.

This is design approval only; no Phase 9 implementation or scenario generation occurred.
Phase 10 remains PLANNED and unstarted. Its rolling suffix calibration, event timing, queue,
replenishment policy and KPI methodology remain separately unapproved. Phase 8 q is restricted
to approved origin-anchored prefixes and does not transport to synthetic stress. Fit B raw-primary
coverage remains 12,263/13,437 (91.26%), below nominal 95%; Sunday h2/h9 evidence is sparse;
stores/origins are dependent; saved-source-Open replay is conditional and closure-inflated; no
conformal, per-store, production or service-level guarantee follows. The final holdout
2015-07-04 through 2015-07-31 remains unreleased and was not accessed.

### Executed design-proposal validation

| Check | Result |
|---|---|
| Full existing fixture suite, Python 3.14.5 | PASS — 200 tests in 95.93s; no Phase 9 tests or implementation added |
| Ruff lint | PASS |
| Ruff format check | PASS — 78 files already formatted |
| Documentation link checker | PASS — no broken local destinations/anchors |
| `uv lock --check`, uv 0.12.23 | PASS — 84 packages; lock unchanged |
| Python 3.14 `pip check` | PASS — no broken requirements |
| `git diff --check` | PASS |

Self-review checked the full documentation diff, schema/factor/count arithmetic, unavailable
anchor precedence, Monday reopening pulse, frozen-input metadata-before-hash ordering,
conditional quantile transport and phase boundaries.
Only Markdown files are changed; no Python implementation/test, dependency, real-data scenario,
calibration table, quantile or model artifact was changed or regenerated. No real-data pipeline
or final-holdout read was run. Accepted ADR-015 through ADR-021 methodology and completed
Phase 8 historical checkpoints are preserved. Local checks validate repository consistency,
not Phase 9's future numerical implementation or external methodology acceptance.

### Approval synchronization validation — 2026-10-07

| Check | Result |
|---|---|
| Full existing fixture suite, Python 3.14.5 | PASS — 200 tests in 97.11s |
| Ruff lint | PASS |
| Ruff format check | PASS — 78 files already formatted |
| Documentation link checker | PASS — 181 local destinations/anchors across 24 Markdown files |
| `uv lock --check`, uv 0.12.23 | PASS — 84 packages; lock unchanged |
| Python 3.14 `pip check` | PASS — no broken requirements |
| `git diff --check` | PASS |

Self-review confirms only the seven listed Markdown files changed; the approved weekday-factor
values and demand formula are unchanged. ADR-015/016/020/021, Phase 7/8 plans, code, tests,
dependencies, model and quantile artifacts remain unchanged. No scenario was generated and the
protected final holdout was not accessed. These checks validate documentation and repository
consistency; they do not implement or numerically validate Phase 9.

## Phase 9 implementation checkpoint — 2026-10-07 (historical pre-closeout checkpoint)

**State:** Design APPROVED by ADR-022; implementation **IMPLEMENTED / UNDER REVIEW** on
`feat/phase-9-synthetic-inventory`. Source commit is
`8dae4e43e06d815746456a1786acfc264b77093b`. [PR #19](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/19)
is open for implementation review. PR #18 is the merged design synchronization at
`97795ca5d868b512e5c2f6cae59bcec1d6ce19a4`; the implementation PR is pending. Phase 9 is not
closed, no Phase 10 work is authorized, and the final holdout remains protected.

### Canonical development run

Run `phase9-dev-20261007-canonical2` completed at `2026-10-07T00:59:31Z` with manifest
SHA-256 `cc148d3670c0b20c769f245488ddd7f535f4333e6b0cf759c60e544e9c6c8a82`. The manifest records
source revision `8dae4e43e06d815746456a1786acfc264b77093b`, source-file digest
`fbeaaea4623360ea41e631346e770090b3875cc40b20e9d07b4353e1e6eee49b`, `worktree_modified=false`,
and lock digest `584337e365e653d97731b73c6d9e2292c4224bee524f0225ddf3221b0aa0f5d0`. It binds
Phase 7 selection manifest `03a1f26ba5855fd0576667bf280df938664c196a802de0a71e696a600b281cdc`
and Phase 8 manifest `63a00fc8c50ccff99360cd8790498e977e08ec6a9846780a4e1a8ab3498d71c2`.
The canonical config hash is `8ded15545911738c9b6551a8af00627e65a231a2d89fea8687cd8c4d6e6b52d7`;
its serialized byte hash is `08fe01cf94866913388312ad30be81b2a831c0abc2524f50185b31980417820b`.

| Output | Rows | Bytes | Byte SHA-256 | Logical SHA-256 |
|---|---:|---:|---|---|
| `scenario_catalog.parquet` | 82 | 4,236 | `7c521c8b2956e2f4de30c70a903216b4a0e2727aee3f5b29947ac25876548e83` | `502c03238a1bf0f8932160199ab4e9c76d0583dd9b70516ee1d98d993e762b04` |
| `origin_anchors.parquet` | 2,230 | 112,699 | `e9bec421447771cae277b437e9e15eff14b0ac4e3c7b009120de70f9be69b131` | `6daee5caeaf50d33c7472a4bbf49e9daf72f62834743fe7409537942561d1bd3` |
| `store_parameters.parquet` | 91,430 | 2,498,919 | `c75aab0c9e54eb3ffe8519c53569ec68db9a2199df0674fd75e4bfc777400427` | `73d4e57d0792e0df529908db52bda242d19a8fabd3a7664db9aa835169bdd315` |
| `scenario_daily.parquet` | 1,280,020 | 41,921,287 | `f43920eed64fb83ebeb7d82effd345f54744994949e637735622d927dfb2203b` | `967b091a28887326c9024fe191722a3a95f887c7da5a873dd1200a28589a642d` |
| `scenario_config.json` | — | 32,991 | `08fe01cf94866913388312ad30be81b2a831c0abc2524f50185b31980417820b` | canonical hash above |
| `upstream_bindings.json` | — | 16,184 | `f1312ef684ab4b2335d8a3b194764f7aac81d6d35b21700e43b602644e1da357` | canonical hash recorded in the manifest |
| `validation_summary.json` | — | 26,521 | `09378b79139dd508ee911dc2a9d442165ec577e362ba15e4ca60bf553b69d0ce` | canonical hash recorded in the manifest |

The four output Parquet byte hashes were independently recomputed after publication. The output
logical hashes all match a reversed-input-order determinism run. The manifest records status
`complete`, all expected row counts, empty structural failures, and output reread/hash validation.
Scenario grid is 2 origins × (1 historical reference + 8 synthetic families × 5 replicates), with
all 1,115 configured stores and 14 target dates per scenario-store.

### Availability, ranges and arithmetic

| Origin | Stores | Available anchors | Unavailable | Zero anchors | Missing calendar dates | Closed-positive Sales rows |
|---|---:|---:|---:|---:|---:|---:|
| 2015-06-05 | 1,115 | 1,115 | 0 | 0 | 0 | 0 |
| 2015-06-19 | 1,115 | 1,115 | 0 | 0 | 0 | 0 |

The initializer read only `Store, Date, Sales, Open` from `data/interim/train.parquet` under
`origin-55 <= Date <= origin` and configured Store membership, then rechecked the input snapshot
before publication. It did not rehash the full prepared train file. Protected 2015-07-04 through
2015-07-31 values were neither read nor hashed. The run records `model_refit_or_tuning=false`,
`phase8_residuals_recomputed=false`, `forecast_or_uncertainty_used_as_synthetic_truth=false` and
`inventory_simulation_performed=false`.

Observed parameter ranges across the synthetic scenarios:

| Field | Minimum | Maximum |
|---|---:|---:|
| Supplier lead time (days) | 2 | 7 |
| Review period (days) | 1 | 1 |
| Protection period (days) | 3 | 8 |
| Initial coverage (open-day equivalents) | 1 | 11 |
| Initial stock value | 2,717.911111 | 254,647.8 |
| Procurement cost ratio | 0.5500066 | 0.8499613 |
| Annual holding rate | 0.1000006 | 0.2999871 |
| Holding-cost rate per calendar day | 0.00015436 | 0.00069392 |
| Goodwill penalty rate | 0.1000259 | 0.7499823 |
| Total stockout penalty | 0.2577159 | 1.1938692 |
| Average equivalent-unit value | 5 | 50 |
| Trend end change | -0.0999815 | 0.30 |
| Promotion response slope | 0.5000557 | 1.4996728 |
| Planned discount depth | 0.0500242 | 0.2999961 |

Observed daily factor ranges:

| Field | Minimum | Maximum |
|---|---:|---:|
| Weekday factor | 0.80 | 1.15 |
| Trend factor | 0.9000185 | 1.30 |
| Promotion factor | 1.0 | 1.5998691 |
| Common shock | -0.0984010 | 0.0995949 |
| Store-date noise | -0.1499999 | 0.1499960 |
| Combined noise factor | 0.7517842 | 1.2482753 |
| Demand stress factor | 0 | 2.0 |
| Discount depth | 0 | 0.40 |
| Synthetic turnover proxy | 0 | 106,054.2063 |

Holding-cost and stockout-penalty arithmetic maximum absolute error is 0. Combined-factor maximum
is 4.9650810021, below the approved 6.0 ceiling. No unavailable store or zero anchor was excluded;
zero synthetic turnover includes the declared zero-turnover scenario and closure routing, not a
claim about lost demand. Historical reference rows have future outcome fields unloaded.

### Checks and boundary

| Check | Result |
|---|---|
| Full fixture suite, Python 3.14.5 | PASS — 218 tests in 113.01s |
| Ruff lint, whole repository | PASS |
| Ruff format, whole repository | PASS — 82 files already formatted |
| Markdown checker | PASS — 182 destinations/anchors across 24 Markdown files |
| `uv lock --check`, pinned uv 0.12.23 | PASS — 84 packages resolved; lock unchanged |
| Python 3.14.5 `pip check` | PASS — no broken requirements |
| `git diff --check` | PASS |
| GitHub Actions PR matrix | PASS — run [#45](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/actions/runs/37555928596) on head `f9c41f0`; Python 3.12 and 3.14 jobs succeeded |

The real-data artifacts are ignored local outputs, not part of the PR. Sales, demand, inventory,
costs and equivalent units retain the approved monetary proxy semantics; no physical quantity,
actual inventory, true lost demand, policy winner, service result or savings is inferred. Do not
merge this implementation PR, start Phase 10, or mark Phase 9 complete at this checkpoint.

## Phase 9 external review fix — 2026-10-07 (historical review checkpoint)

The approved-configuration validation finding from PR #19 was fixed in source commit
`2ec2488adf065e692141eceb8e3f979df4679f45`. `_validate_config()` now reconstructs the accepted
contract through `default_config()` for the supplied normalized fixture store subset, preserves
run-specific upstream bindings and publication fields, and compares the full JSON-compatible
configuration. Changes to nested assumptions, omitted settings or unexpected configuration fields
fail before generation. No ADR, RNG, equation, schema or scenario-generation formula changed.

Because the source digest changed, a new immutable canonical development run
`phase9-dev-20261007-config-validation-fix` completed at `2026-10-07T01:26:56+00:00`. Its manifest
SHA-256 is `573e36efddef452df781994c43f76006e208ec8c588b4c47e46735530da34761`. It records source
revision `2ec2488adf065e692141eceb8e3f979df4679f45`, source digest
`9b753cae8efdaca718f1f93dce6f4eb22c426abef24f48953b9b6f5eadbbcc0f`,
`worktree_modified=false`, and the unchanged lock digest
`584337e365e653d97731b73c6d9e2292c4224bee524f0225ddf3221b0aa0f5d0`. The approved semantic
config hash remains `8ded15545911738c9b6551a8af00627e65a231a2d89fea8687cd8c4d6e6b52d7`; the new
serialized config byte hash is `40a150dfa8e8aa734bf3a7a1ca9b917b7eca7b3b8386721ea4b35fcd66d86421`.

| Parquet output | Rows in both runs | Logical SHA-256 in both runs | Byte SHA-256 in both runs | Comparison |
|---|---:|---|---|---|
| `scenario_catalog.parquet` | 82 | `502c03238a1bf0f8932160199ab4e9c76d0583dd9b70516ee1d98d993e762b04` | `7c521c8b2956e2f4de30c70a903216b4a0e2727aee3f5b29947ac25876548e83` | Identical |
| `origin_anchors.parquet` | 2,230 | `6daee5caeaf50d33c7472a4bbf49e9daf72f62834743fe7409537942561d1bd3` | `e9bec421447771cae277b437e9e15eff14b0ac4e3c7b009120de70f9be69b131` | Identical |
| `store_parameters.parquet` | 91,430 | `73d4e57d0792e0df529908db52bda242d19a8fabd3a7664db9aa835169bdd315` | `c75aab0c9e54eb3ffe8519c53569ec68db9a2199df0674fd75e4bfc777400427` | Identical |
| `scenario_daily.parquet` | 1,280,020 | `967b091a28887326c9024fe191722a3a95f887c7da5a873dd1200a28589a642d` | `f43920eed64fb83ebeb7d82effd345f54744994949e637735622d927dfb2203b` | Identical |

The run validation status is `complete` with no structural failures. It reconfirmed 1,115 stores at
each of the two approved origins, the H14 development cutoff of 2015-07-03, and that protected
holdout values were neither read nor hashed. The previous `canonical2` directory and manifest
remain untouched; its manifest SHA-256 is still
`cc148d3670c0b20c769f245488ddd7f535f4333e6b0cf759c60e544e9c6c8a82`.

| Check | Result |
|---|---|
| Inventory scenario fixtures | PASS — 30 tests |
| Full fixture suite, Python 3.14.5 | PASS — 230 tests in 96.11s |
| Ruff lint, whole repository | PASS |
| Ruff format, whole repository | PASS — 82 files already formatted |
| Documentation link checker | PASS — 183 destinations/anchors across 24 Markdown files |
| `uv lock --check`, uv 0.12.23 | PASS — 84 packages resolved; lock unchanged |
| Python 3.14.5 `pip check` | PASS — no broken requirements |
| `git diff --check` | PASS |

The review fix is committed on the existing PR #19 branch. Phase 9 remains
**IMPLEMENTED / UNDER REVIEW**. The protected holdout remains unreleased, Phase 10 remains
unstarted, and this checkpoint does not authorize merge or closeout.

## Phase 9 independent implementation and numerical review — 2026-10-07 (historical pre-integration acceptance checkpoint)

**Decision: ACCEPTED.** The independent external code and numerical review accepted the final
Phase 9 implementation at source revision `2ec2488adf065e692141eceb8e3f979df4679f45` and the
canonical run `phase9-dev-20261007-config-validation-fix`, manifest SHA-256
`573e36efddef452df781994c43f76006e208ec8c588b4c47e46735530da34761`. The reviewer identity was
not supplied. This acceptance is implementation and numerical evidence; Phase 9 remains
**IMPLEMENTED / UNDER REVIEW** until PR #19 is merged and formally closed.

The audit accepted 82 scenario catalog rows, 2,230 origin anchors, 91,430 store-parameter rows,
and 1,280,020 scenario-daily rows. All four Parquet output byte hashes exactly match `canonical2`.
The review confirmed monetary initialization and cost arithmetic, deterministic keyed sampling and
stress overrides, synthetic turnover calculations, and preservation of historical-reference
missingness. These results do not introduce any policy simulation or inventory-performance claim.

The accepted run and manifest were not regenerated or rewritten for this documentation-only
integration. It remains development-only: origin H14 ends on 2015-07-03, protected
2015-07-04 through 2015-07-31 outcomes were not accessed, and Phase 10 had not started at this
pre-integration checkpoint. PR #19
remains open and unmerged pending this synchronized head's external integration review and CI.

### PR #19 integration quality gates — 2026-10-07 (historical pre-merge checkpoint)

These checks were run after merging PR #20's `origin/main` into the existing PR #19 branch. They
are new integration evidence, separate from the earlier 230-test checkpoint above.

| Check | Result |
|---|---|
| Full `python -m pytest` (Python 3.14.5) | PASS — 230 tests in 144.03s |
| Ruff lint | PASS — `ruff check .` |
| Ruff format | PASS — 82 files already formatted |
| Markdown link checker | PASS — 184 local destinations/anchors across 24 Markdown files |
| `uv lock --check` (uv 0.12.23) | PASS — 84 packages resolved; lock unchanged |
| Python 3.14.5 `pip check` | PASS — no broken requirements |
| `git diff --check` | PASS |
| GitHub Actions Quality matrix | PASS — [run #50](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/actions/runs/37562153977) on integration head `a82d080`; Python 3.12 and 3.14 jobs succeeded |

These fixture and repository checks do not read final-holdout outcomes or regenerate the accepted
Phase 9 run. Run #50's result is recorded here; the latest PR-head CI status is recorded in the
PR #19 description for final external integration review.

## Phase 9 formal closeout — 2026-10-07

**Decision: COMPLETE.** PR #19 is verified merged into `main` by squash merge
`7451c50ff685d92e8e74b5014d07b3bbfaca0a22`, which is present in fetched `origin/main`. GitHub
identifies that commit as the PR #19 merge commit; the reviewed integration head was
`46788db3f5b81af37cda78bf44f054be2bc0098b`. PR #20's proposal rename remains integrated at
`ff3c11554144e79ee84c627c2bcd3619d23072d0`, and `docs/PROPOSAL.md` remains the canonical proposal
path. The accepted Phase 9 methodology remains ADR-022.

The external independent implementation and numerical review accepted source revision
`2ec2488adf065e692141eceb8e3f979df4679f45` and canonical run
`phase9-dev-20261007-config-validation-fix`, manifest SHA-256
`573e36efddef452df781994c43f76006e208ec8c588b4c47e46735530da34761`. Accepted counts are 82
scenario catalog rows, 2,230 origin anchors, 91,430 store-parameter rows and 1,280,020
scenario-daily rows. Review confirmed approved synthetic generation, deterministic sampling,
monetary cost calculations, historical-reference missingness and artifact integrity. This
documentation closeout did not regenerate or rewrite the run or manifest.

The complete plan, including historical proposal, approval, implementation and review checkpoints,
is archived at [plans/completed/phase-9-synthetic-inventory.md](../plans/completed/phase-9-synthetic-inventory.md).
The closeout branch was started from fetched `origin/main` at
`7451c50ff685d92e8e74b5014d07b3bbfaca0a22`. No Phase 9 generator, CLI, test, frozen Phase 7/8
model, quantile or artifact was changed. The protected final-holdout outcomes were not accessed
or hashed. The completed scope is synthetic monetary scenario generation only; it does not claim
physical inventory, observed stockouts, actual savings or policy performance. Phase 10 remains
PLANNED and not started, and no Phase 10 methodology is approved.

### Phase 9 closeout quality gates — 2026-10-07

| Check | Result |
|---|---|
| Full `python -m pytest` (Python 3.14.5) | PASS — 230 passed in 131.42s |
| Ruff lint | PASS — `ruff check .` |
| Ruff format | PASS — 82 files already formatted |
| Markdown link checker | PASS — 189 local destinations/anchors across 24 Markdown files |
| `uv lock --check` | PASS — uv 0.12.23; 84 packages resolved; lock unchanged |
| Python 3.14.5 `pip check` | PASS — no broken requirements |
| `git diff --check` | PASS |

The approved link-maintenance change updates only ADR-022's plan pointer to the completed plan.
Its accepted status, methodology and substantive content remain unchanged. The relocated plan's
internal links and all repository-local Markdown destinations pass validation.

## Phase 10 methodology approval and integration — 2026-10-07

**State: APPROVED; IMPLEMENTATION NOT STARTED.** Human approval of the Phase 10 methodology and
ADR-023 was given on 2026-10-07. The initial technical methodology review and fresh independent
review both returned ACCEPT; the independent verdict is
`INDEPENDENT_PHASE10_DESIGN_REVIEW=ACCEPT`, with no blocking findings or required methodology
changes. This is model-assisted review evidence plus explicit human approval, not a claim of
GitHub-native reviewer approval. Phase 10 implementation is authorized as the next separate task.
This approval/integration task changes documentation only. Phase 9 remains COMPLETE; Phase 11 has
not started and is not authorized. The protected holdout remains unreleased.

The original design branch, `docs/phase-10-inventory-simulation-design`, was created from fetched
`origin/main` at `8234ab2170b7c76b00623c0f4e11a82dd8f2d4b2`, the Phase 9 closeout PR #21 commit.

The then-active Phase 10 plan, now at `plans/completed/phase-10-inventory-simulation.md`, and accepted
ADR-023 record the two approved origin/fit relationships, origin-frozen baseline/LightGBM-buffer
targets, daily review,
L full intervening demand days and EOD-t to BO-day t+L+1 receipts. They define lost-sales balances,
ending-stock holding-plus-shortfall costs, exact KPI denominators, the project-specific completed
positive-demand receipt-cycle service rate, finite-window terminal exposures and nine paired
sensitivity overlays. Synthetic q transport is explicitly uncalibrated. Future interfaces,
immutable artifact schemas/publication and fixture/numerical acceptance are design requirements,
not implemented capabilities or simulated results.

Self-review inspected the entire seven-file documentation diff. No source, scripts, tests,
dependencies, lock, accepted Phase 0–9 method or approved proposal content changed. Current status
and terminology agree across the active plan, ADR, roadmap, dictionary and READMEs. No contradiction
requires editing `docs/PROPOSAL.md`. Upstream manifest identities were copied from existing
governance records, not freshly verified by artifact access or hashing. No real-data pipeline,
model/scenario regeneration or simulation was run. Protected July 4–31 outcomes were not accessed,
inspected, hashed, summarized or evaluated.

### Documentation proposal quality gates

Commands use `.venv/Scripts/python.exe` (Python 3.14.5) and `.venv/Scripts/uv.exe` (uv 0.12.23).
The locked sync used `--inexact` to retain installed environment tooling; project dependencies and
`uv.lock` remain unchanged. These are existing fixtures/repository checks, not Phase 10 tests.

| Check | Actual result |
|---|---|
| `uv lock --check` | PASS — 84 packages resolved; lock unchanged |
| `uv sync --locked --extra dev --inexact --python C:\Users\Minh\AppData\Local\Programs\Python\Python314\python.exe` | PASS — 84 packages resolved; existing project package rebuilt; no dependency/lock change |
| `uv pip check` | PASS — 62 packages checked; all installed packages compatible |
| `python -m pytest` | PASS — 230 passed in 107.94s |
| `python -m ruff check .` | PASS — all checks passed; nonfatal cache-write access warning |
| `python -m ruff check --no-cache .` | PASS — all checks passed without the cache warning |
| `python -m ruff format --check .` | PASS — 83 files already formatted |
| `python scripts/check_docs.py` | PASS — 213 local destinations/anchors across 25 Markdown files |
| `git diff --check` | PASS |

The approval changes no method or accepted Phase 0–9 contract, starts no simulator, and produces
no results or artifacts. The active plan remains in `plans/active/` during implementation and
review. The next authorized boundary is Phase 10 implementation under the accepted plan; Phase 11
and protected holdout access remain outside this approval.

### Approval integration quality gates

The following required checks ran after the approval documentation update using the locked
`.venv` environment. No Phase 10 implementation test or model/scenario pipeline was run.

| Check | Actual result |
|---|---|
| `uv lock --check` | PASS — 84 packages resolved; lock unchanged |
| `uv pip check` | PASS — 62 packages checked; all installed packages compatible |
| `python -m pytest` | PASS — 230 passed in 130.21s |
| `python -m ruff check --no-cache .` | PASS — all checks passed |
| `python -m ruff format --check .` | PASS — 83 files already formatted |
| `python scripts/check_docs.py` | PASS — 214 local destinations/anchors across 25 Markdown files |
| `git diff --check` | PASS |

## Phase 10 implementation and development validation — 2026-10-07 (pre-review merge checkpoint)

**State at the merge checkpoint: IMPLEMENTED / UNDER REVIEW.** Implementation branch:
`feat/phase-10-inventory-simulation`; source/test correction commit:
`4aefc8c1f21a392270150d46aae610a5dea428e0`. PR #23 merged into `main` as
`15bce83cd63a4edfeed6defb95788da90d0f36d9` on 2026-10-07 before the external implementation review
was resolved. The later review returned REQUEST CHANGES with B1–B3; this historical section records
pre-review implementation evidence only. Phase 10 is not COMPLETE. Phase 11 remains NOT STARTED /
NOT AUTHORIZED, and the protected holdout remains unreleased.

The pre-review canonical development run was
`phase10-dev-20261007-implementation-v2`, with manifest SHA-256
`889e8e513c68791dae3c547e9df531ed9ed0c98ce257518c0c011b2a9fe6056e`. Its code revision is
`4aefc8c1f21a392270150d46aae610a5dea428e0`, source SHA-256
`347d6021923b7a82ddd4746335e8cfc7e827c338027c215b605efe7a9c572337`, and recorded worktree state
is clean. It verified these frozen development inputs:

| Phase | Run | Manifest SHA-256 |
|---|---|---|
| 7 | `365f22d4c3f94722a594ab934a22c4f6` | `03a1f26ba5855fd0576667bf280df938664c196a802de0a71e696a600b281cdc` |
| 8 | `phase8-impl-20261006-provenance-review` | `63a00fc8c50ccff99360cd8790498e977e08ec6a9846780a4e1a8ab3498d71c2` |
| 9 | `phase9-dev-20261007-config-validation-fix` | `573e36efddef452df781994c43f76006e208ec8c588b4c47e46735530da34761` |

The seven ignored artifacts are `simulation_config.json`, `policy_targets.parquet`,
`simulation_ledger.parquet`, `policy_summary.parquet`, `comparison_summary.csv`,
`validation_summary.json`, and `manifest.json`. Actual counts match the approved design: 383,560
target rows, 383,560 summary rows, 5,753,400 ledger rows, 172 cases, and 1,720 comparison rows;
the reference grid has 182,860 tracks and 2,742,900 ledger rows. There are 191,780 matched
case/Store pairs. Every requested track is complete: unavailable/incomplete tracks, exclusions,
and historical Open-assumption violations are zero. Both target and ledger artifacts contain the
valid `synthetic_stress` and `historical_replay` mode labels. The ledger spans June 5 through July 3,
2015, with zero post-cutoff rows.

All staged checks pass: zero invalid foreign keys, queue identity and daily/terminal balance
validation, target arithmetic, paired exogenous-input identity, cost-only trajectory identity,
exact nine-variant grid, and pinned upstream identities. `holdout_access`,
`protected_outcome_dates_read_or_hashed`, and `raw_train_file_hashed` are false; the target allowlist,
freeze-before-outcomes rule, unsupported-origin rejection, and terminal-day order suppression are
confirmed. Phase 9 was not regenerated, and no refit or recalibration occurred.

At the `synthetic_base` reference, pooled simulated holding-plus-shortfall cost is 90.787 million
for the historical-mean policy and 113.929 million for the LightGBM-buffer policy, a
forecast-minus-baseline difference of +23.143 million across 11,150 Store tracks. Conditional
historical replay is 15.101 million versus 19.377 million (+4.276 million across 2,230 tracks).
Across the remaining reference cases, the forecast policy is lower by 6,758 in demand-slump and
higher by about 70 in zero-turnover; the other reference cases are higher by 3.749–25.076 million.
These results describe the approved simulated assumptions and do not claim savings or superiority.

For the synthetic-base sensitivity cases, forecast-minus-baseline cost is +32.403 million at
p=.90, +9.034 million at p=.98, +22.349 million at L=2, +14.593 million at L=7, and +25.857
million at one-day initial coverage. Holding-rate overlays retain physical trajectories (+23.147
million at .10; +23.138 million at .30). The goodwill overlays are +12.759 million at .10 and
+33.473 million at .75.

For the synthetic-base reference, terminal on-hand/pipeline values are 8.830/292.443 million for
the baseline and 7.551/274.097 million for the forecast policy. Terminal stock-cost diagnostics
are 6.155/5.259 million, and terminal procurement commitments are 204.447/191.629 million.
These exposures are not included in the primary objective and are not savings.

At that checkpoint, the corrected v2 run was the current-pointer target. It followed an earlier
immutable publication whose target builder had serialized a Pandas `Series.mode` method
representation into the `mode` metadata. The source then used explicit column indexing, with a
regression assertion for both targets. The first run remains ignored and immutable under
`phase10-dev-20261007-implementation`; it is superseded and is not canonical evidence.

No second full run was performed after the corrected canonical run at that checkpoint. Fixture
determinism and ordering-invariance tests pass. A deterministic representative replay covered 18
June-5 Store-1 cases:
historical reference, all eight Phase 9 families at reference, and all nine synthetic-base OFAT
variants, both policies, 36 tracks and 540 ledger rows. Replayed ledger rows and summaries matched
the published subset exactly after explicit-schema casting; source/replay subset logical SHA-256
was `05da21fb002b14772c1eacb3aeb50b1f362d196170851075e26f787851b4a002`.

Quality gates after the correction: 34 focused Phase 10 tests passed; the full repository suite
passed (264 tests in 104.61 seconds); Ruff check and format, docs validation, `uv lock --check`,
`uv pip check`, and `git diff --check` passed. The data outputs remain ignored; no dependency, lock,
Phase 9 source/artifact, accepted methodology, or proposal text changed.

## Phase 10 external implementation review and corrective follow-up — 2026-10-08

The independent implementation review returned **REQUEST CHANGES** after PR #23 had merged. It
identified three implementation blockers, with no change to accepted ADR-023 methodology:

- **B1:** Phase 9's semantic date/schema preflight could be bypassed by a timestamp field and did
  not prove rejection occurred before Parquet byte hashing.
- **B2:** the first missing-demand row could retain dependent post-demand values, and the streaming
  validator did not validate an incomplete track's available prefix and unavailable suffix.
- **B3:** a positive receipt on terminal day T incorrectly removed the terminal right-censored
  receipt interval.

The fixes and regression tests were recovered onto `fix/phase-10-review-findings`, based on
`origin/main` at `15bce83cd63a4edfeed6defb95788da90d0f36d9`. Recovery matched the external binary patch
backup exactly. Source/test commit `296feac19cd69f94a74f7d3322044377f1f1413f` passed 48 focused
tests and 278 full-suite tests. Ruff check/format, documentation validation, `uv lock --check`,
`uv pip check`, and `git diff --check` passed. No Phase 7, 8, or 9 code, artifacts, or methods
changed.

A fresh full canonical run, `phase10-dev-20261008-review-fixes`, completed with manifest SHA-256
`0716fc92623b66f4d8a6024eecb608aa992596809458fa1b7c40595b66cbdd91`, code revision
`296feac19cd69f94a74f7d3322044377f1f1413f`, source SHA-256
`bb0e0f6f52e3d744da7d17a4a094e2e3ddbded19e9e69bc6fd2a1d9ccec8df7d`, clean-worktree provenance,
and `uv.lock` SHA-256 `584337e365e653d97731b73c6d9e2292c4224bee524f0225ddf3221b0aa0f5d0`. It pins the
existing Phase 7/8/9 runs and identities, records ADR-023, and states that protected holdout values
were not read or hashed, no refit/recalibration was performed, and Phase 9 was not regenerated.
`data/processed/inventory_simulation/current.json` points to this run. The v1 and v2 run directories
remain present with their original manifest hashes: v1
`4e5e992760836b93b44fffaff3baa497b79a6a24f6587694cece1a2891a45921`; v2
`889e8e513c68791dae3c547e9df531ed9ed0c98ce257518c0c011b2a9fe6056e`. V2 remains immutable
pre-review evidence and is superseded as the current canonical run.

The output has 383,560 target rows, 383,560 summary rows, 5,753,400 ledger rows, 172 cases, and
1,720 comparison rows. All 383,560 tracks are complete; incomplete/unavailable tracks and
historical Open-assumption violations are zero. Independent reconstruction from ledger receipt
dates found exactly 383,560 right-censored terminal intervals and zero summary mismatches. The
final positive receipt was before T for 108,556 tracks, on T for 236,743, and absent for 38,261.
The corrected summary counts the unfinished final interval for every track, including a receipt on
T and episodes with no positive receipts.

Headline primary costs are unchanged from v2. For synthetic-base reference, baseline is
90,786,517.967853, LightGBM-buffer is 113,929,065.505821, and forecast-minus-baseline is
+23,142,547.537968. Historical conditional replay is 15,100,677.170801 vs 19,376,775.902140,
difference +4,276,098.731339. The nine paired sensitivity differences are +32.403m (p=.90),
+9.034m (p=.98), +22.349m (L=2), +14.593m (L=7), +25.857m (C=1), +23.147m (a=.10), +23.138m
(a=.30), +12.759m (g=.10), and +33.473m (g=.75). Synthetic-base terminal stock is 8.830303m /
7.551179m, terminal pipeline 292.442932m / 274.096540m, terminal stock cost 6.155105m /
5.259219m, and outstanding procurement commitment 204.447440m / 191.629078m, respectively.
These are simulated monetary-turnover exposures, not realized inventory or savings.

Validation reports zero invalid foreign keys and post-cutoff rows and passes queue identity, daily
and terminal balances, target arithmetic, common policy input identity, and cost-only sensitivity
trajectory identity. Complete-track validation passed; incomplete-prefix and dependent-null checks
were not applicable because the canonical grid has no incomplete tracks. A representative
deterministic replay of historical reference, synthetic base, `promo_peak`, both origins, both
policies, and `holding_010` matched exactly: 16 tracks and 240 ledger rows. Published/replay logical
hashes match for ledger (`5277ff63e999658e5264cf207f5e1bed56674ddcd28b333a8b279adbfb1962bc`) and
summaries (`dd752db39d28c0913fbeb8fa14668acd8de296e0f5ea00ee1481b29a58f4e233`). A two-policy
terminal-receipt fixture replay verified a completed cycle plus a censored terminal interval and
has logical SHA-256 `7db6fe4f292dda065bc384cfe574819d3be8364111a2bd04ad33b1033c1406ee`.

The external backup remains at
`C:\Users\Minh\Desktop\hust\introba\project\phase10-review-fixes-local-backup.patch`; stash
`stash@{0}` remains applied and retained through safe push. The new [follow-up PR #24](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/24)
is open and unmerged. Focused re-review #1 returned REQUEST CHANGES: B1 pre-hash firewall, B3
terminal censoring, and B2 missing-demand simulation semantics passed; the sole remaining blocker was
incomplete-track validator coverage. The correction and refreshed evidence follow.

### Phase 10 focused re-review validator correction — 2026-10-08

The focused external re-review of PR #24 returned `PHASE10_FOCUSED_REREVIEW=REQUEST_CHANGES`.
B1 pre-hash firewall, B3 terminal censoring, B2 simulation semantics, and their prior regression
coverage passed. The only blocker was incomplete-track validator coverage. Commit
`5504d855fd60b8a038a4d6574e35b579ed0f439d` hardens the validator without changing simulation
semantics or ADR-023: it validates all available origin-row invariants and origin order arithmetic;
checks fixed policy/cost metadata and holding/penalty rate equations on every incomplete-track row;
and rejects receipt IDs after the first unavailable suffix row while allowing actual receipts on the
first missing-demand boundary. New fixtures reject each reviewer mutation independently, including
a valid L=2 prefix with an origin order and a receipt before missing demand. The fixture also checks
corrupt receipt amount/IDs, post-receipt pipeline, prefix stock, and prefix rate. Focused Phase 10 tests
pass (**50 passed**); the full suite passes (**280 passed**). Ruff, format, docs, locked dependency,
environment, and diff checks also pass.

The fresh immutable canonical run `phase10-dev-20261008-validator-fix` has manifest SHA-256
`1c914b8a0fc7582c192f24fb8286e8521669cc079162cf832a58f2d8a1569f16`, source revision
`5504d855fd60b8a038a4d6574e35b579ed0f439d`, source digest
`a4c1ec83d4211c45d75afe4db9845b359ddb41f88f04f3611a0c3cda872096db`, a clean worktree record, and
the unchanged lock digest `584337e365e653d97731b73c6d9e2292c4224bee524f0225ddf3221b0aa0f5d0`.
It uses the same pinned Phase 7/8/9 inputs. Independent content-hash comparison confirms identical
logical results to `phase10-dev-20261008-review-fixes` for targets
(`25d127258800c584edbb72685ff11c8043e464d88ed7539967b109c8923413f9`), ledger
(`0d58757f8b9cb099537f57d4a79b2f89be698dbf7704f93a67a1aa7db9a9ccbe`), policy summary
(`b9610f414bfd38a363cafe25afe7821eb3ed79a241423920bafa35126b9374c2`), and comparison
(`0133e439a6e6644fb565cbe317440a02e5617b7c668769b974dbbf29bb426bfd`).

The run again has 383,560 targets/summaries, 5,753,400 ledger rows, 172 cases, 1,720 comparisons,
383,560 complete tracks, and zero incomplete/unavailable tracks, Open-assumption violations,
invalid foreign keys, or post-cutoff rows. Incomplete-prefix and unavailable-dependent-null
validation fields are `not_applicable` because this canonical grid contains no incomplete tracks;
the new fixtures exercise those branches. An independent receipt-date reconstruction gives 108,556
final receipts before T, 236,743 on T, 38,261 with no positive receipt, 383,560 right-censored
terminal intervals, and zero summary mismatches. Headline costs, nine sensitivity differences,
terminal exposures, and representative replay results match the prior canonical run; their numerical
record remains above. No Phase 7/8 refit, Phase 8 recalibration, Phase 9 regeneration, or protected
holdout read/hash occurred. `current.json` now points to this run; v1, v2, and
`phase10-dev-20261008-review-fixes` remain immutable, with the latter superseded as current evidence.

At this validator-correction checkpoint, Phase 10 remained IMPLEMENTED / UNDER REVIEW pending final
focused external re-review. The accepted review and formal closeout are recorded below. Phase 11
remains NOT STARTED / NOT AUTHORIZED, and the protected holdout remains unreleased.

## Phase 10 formal closeout - 2026-10-08

PR #23 integrated the Phase 10 implementation at `15bce83cd63a4edfeed6defb95788da90d0f36d9`.
PR #24 integrated the B1/B2/B3 corrective implementation at
`fcbf6b7de79d57bb7db8a965d5a2b78e9376a3a9`. Both PRs are closed and merged. The final focused
independent external/model-assisted technical review returned
`PHASE10_FINAL_FOCUSED_REREVIEW=ACCEPT_WITH_MINOR_CHANGES`. It was not a GitHub-native APPROVE review.

Review chronology and outcome:

- Initial implementation review: `PHASE10_IMPLEMENTATION_REVIEW=REQUEST_CHANGES`, identifying B1,
  B2 and B3 findings.
- Focused re-review #1: `PHASE10_FOCUSED_REREVIEW=REQUEST_CHANGES`; B1 PASS, B3 PASS, B2 simulation
  semantics PASS; the remaining B2 validator coverage blocker was subsequently fixed.
- Final focused review: B1 PASS, B2 PASS, B3 PASS; no blocking findings. Holdout firewall, canonical
  provenance, numerical regression, sensitivity, terminal accounting, reproducibility evidence and
  repository quality gates PASS.
- Sole minor issue: stale PR #24 metadata. The PR description was corrected with the accepted current
  canonical evidence before/around integration.

Accepted canonical run: `phase10-dev-20261008-validator-fix`; manifest SHA-256
`1c914b8a0fc7582c192f24fb8286e8521669cc079162cf832a58f2d8a1569f16`. Source revision
`5504d855fd60b8a038a4d6574e35b579ed0f439d`; source digest
`a4c1ec83d4211c45d75afe4db9845b359ddb41f88f04f3611a0c3cda872096db`; `uv.lock` SHA-256
`584337e365e653d97731b73c6d9e2292c4224bee524f0225ddf3221b0aa0f5d0`. The canonical current pointer
continues to identify this run. Prior immutable runs remain preserved:
`phase10-dev-20261007-implementation`, `phase10-dev-20261007-implementation-v2`,
`phase10-dev-20261008-review-fixes`, and `phase10-dev-20261008-validator-fix`.

Canonical counts: 383,560 targets, 383,560 policy summaries, 5,753,400 ledger rows, 172 cases and
1,720 comparison rows. All 383,560 tracks are complete; incomplete tracks, unavailable tracks,
historical Open-assumption violations and post-cutoff outcome rows are zero.

Receipt accounting: final positive receipt before T for 108,556 tracks, on T for 236,743, and no
positive receipt for 38,261; total 383,560. The 383,560 terminal right-censored intervals and zero
summary mismatches preserve the rule that a final positive receipt begins an unfinished interval,
even when it occurs on T.

At the synthetic-base reference, baseline cost is 90,786,517.967853 and forecast-policy cost is
113,929,065.505821 (forecast minus baseline +23,142,547.537968). Historical conditional replay is
15,100,677.170801 versus 19,376,775.902140 (+4,276,098.731339). These are higher simulated
holding-plus-shortfall costs under the stated assumptions, not realized losses or universal model
performance claims.

Forecast-minus-baseline sensitivity differences remain +32.403m (p=.90), +9.034m (p=.98), +22.349m
(L=2), +14.593m (L=7), +25.857m (C=1), +23.147m (a=.10), +23.138m (a=.30), +12.759m (g=.10) and
+33.473m (g=.75). Cost-only overlays retain identical physical trajectories. Synthetic-base terminal
stock is 8.830303m / 7.551179m, terminal pipeline 292.442932m / 274.096540m, terminal stock cost
6.155105m / 5.259219m, and outstanding procurement commitment 204.447440m / 191.629078m for baseline /
forecast. These exposures remain outside the primary cost.

Representative replay covered 16 tracks and 240 ledger rows; the accepted replay ledger logical
SHA-256 is `5277ff63e999658e5264cf207f5e1bed56674ddcd28b333a8b279adbfb1962bc`. The accepted results are
reproducibility evidence for conditional simulated policy comparisons, not evidence of actual
Rossmann inventory or savings. Focused tests passed (50); the full suite passed (280). GitHub Quality
run [#64 / 37718032966](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/actions/runs/37718032966)
passed on Python 3.12 and 3.14 for the reviewed implementation head.

**Phase 10 is COMPLETE once this closeout PR is integrated into `main`.** The implementation and
numerical evidence are accepted, corrective review findings are resolved, and formal closeout is
recorded in the completed plan. No Phase 11 work is part of this PR. Phase 11 remains PLANNED / NOT
STARTED / NOT AUTHORIZED. No final holdout evaluation occurred; the holdout remains unreleased.

### Phase 12 M2 independent review corrections — 2026-10-09

M2 remains IMPLEMENTED / UNDER REVIEW on `feat/phase-12-streamlit-m2`; existing Draft PR #30 remains
open and unmerged. This corrective task resolves findings M2-01 and M2-02 without starting M3/M4,
deployment or Phase 13.

M2-01 moves all Historical Sales, forecast and uncertainty DTO conversion ahead of their analytical
tables and charts. Safe typed provenance conversion rejects arbitrary objects and path-like values.
Malformed result data now produces a fixed `internal_error` for its panel, with no partial saved
rows or chart. Forecast and uncertainty remain independent: an uncertainty conversion error keeps
the successfully converted forecast visible.

M2-02 keeps `fill_between()` for contiguous intervals with multiple horizons and draws singleton
intervals as vertical saved lower-to-upper ranges with endpoint markers. The saved point remains
separate from its interval and can appear outside it. Missing and unavailable horizons split chart
segments, and saved table bounds, widths, reasons, points and nulls remain unchanged.

Validation: 71 focused dashboard/presenter/M2 tests passed. Whole-repository pytest passed 502 tests
on Python 3.12 and 502 on Python 3.14, with one existing Starlette/httpx deprecation warning per run.
Ruff lint and format passed. `uv lock --check` resolved 109 packages. `uv pip check` passed with 91
packages in the Python 3.12 environment and 93 in Python 3.14. The docs checker passed with 259
local destinations/anchors across 27 Markdown files; `git diff --check` passed. Git reported only
the configured LF-to-CRLF normalization notices for the modified files.

Tests used fixtures; no producer, saved artifact, model, metric, dependency or lockfile changed.
No real-data rerun, model fitting, ledger access, protected July outcome access, manual browser,
performance or deployment check was performed. PR #30 requires final external review; Phase 12 is
not complete.

## Phase 12 M3 implementation checkpoint - 2026-10-09

M2 is accepted and integrated by PR #30 at `327a274bfdad0bb97cdd614a36dc04cbbf8291a2`. Main-branch Quality [run #37955545881](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/actions/runs/37955545881) passed for Python 3.12 and 3.14, satisfying the M3 authorization gate. M3 is IMPLEMENTED / UNDER REVIEW on `feat/phase-12-streamlit-m3`, based directly on that main SHA, in [draft PR #31](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/31), open and unmerged at that checkpoint. Its model/inventory behavior, exact read-only smoke queries, row counts and service provenance are preserved in the [Phase 12 plan](../plans/completed/phase-12-streamlit-dashboard.md).

The focused dashboard/M2/presenter suite passed 98 tests. The full fixture suite passed 529 tests on each of Python 3.12 and 3.14, each with one existing Starlette/httpx deprecation warning. Ruff lint/format, Markdown links, lock consistency, the locked Python 3.14 dependency check and `git diff --check` passed. M3 smoke used only public application services and confirmed the adverse whole-case reference and `buffer_090` cost differences already recorded above remain visible. Store 1 policy pairs were comparable in that smoke; no noncomparable canonical pair was observed. No Phase 10 daily ledger, protected July outcome, producer, simulation, fit, or canonical artifact mutation was part of the work.

M3 remains under review; no merge or Phase 12 closeout is authorized. M4 is NOT AUTHORIZED, deployment remains undecided, Phase 13 is not authorized, and the final holdout remains protected.

### Phase 12 M3-01 corrective review - 2026-10-10

M3-01 is resolved on the existing `feat/phase-12-streamlit-m3` branch and Draft PR #31. `_render_model_comparison_error()` now handles presenter `ModelComparisonTooLargeError` separately from `ArtifactReadError`, shows the fixed "Narrow the selection." message with UI identifier `comparison_too_large`, and never reads a nonexistent `.code` attribute. Genuine `InvalidArtifactRequestError` continues to show its `invalid_artifact_request` code. No raw exception, path, traceback or partial result is displayed; service contracts and query limits are unchanged.

The presenter overflow test verifies a view above the explicit query limit returns `ModelComparisonTooLargeError`. The AppTest injects oversized views after a successful screen render and verifies the sanitized message/identifier, no uncaught error, and no result table, chart, provenance or stale result. The existing invalid-request test pins its original stable code. Focused dashboard/M2/presenter tests passed 100; full pytest passed 531 tests on Python 3.12 and 531 on Python 3.14, each with one existing Starlette/httpx deprecation warning. Ruff, format, link, lock, dependency and whitespace checks passed. M3 remains IMPLEMENTED / UNDER REVIEW; PR #31 remains draft and unmerged. No ledger or protected holdout access occurred; M4 and Phase 13 remain unauthorized.

## Phase 12 M4 integration browser and local performance 2026-10-10

This records the pre-scope-change implementation checkpoint; the later localhost-only decision and
formal closeout below supersede its then-current deployment and lifecycle status.

**State:** M4 is IMPLEMENTED / UNDER REVIEW. M1–M3 were independently accepted and integrated at
`28aa42fdb2186dbbc340bef72917ce2e2ec06425`; main Quality run #37966506688 passed both supported
Python jobs. M4 branch `feat/phase-12-streamlit-m4` starts directly from that base. The attached
task authorizes a commit, push and one Draft PR to `main`, but no merge or formal Phase 12 closeout.
The deployment strategy is Option A (private LAN on the artifact-owning Windows host). The actual
authorized audience for this session is localhost only. The active Wi-Fi network profile is Public,
so the app stays bound to loopback. No firewall rule or LAN URL was created. The machine remains
powered and the course accepts a temporary session-only URL; neither fact grants LAN exposure.

The five screens use the existing `ApplicationServices` and verified `_ArtifactReader`; no service
contract, API, inference, simulation, result cache, dependency or lockfile change was introduced.
The Model Comparison evidence selector issues one bounded query per view: a common comparison,
saved MAE by horizon, or standalone coverage. AppTest and actual Edge interactions cover those views
and two independent browser session states. The inventory view preserves all ten saved whole-case
metrics separately from an optional Store pair and retains the accepted adverse whole-case results.

The read-only canonical service smoke found 82 scenario entries and 172 registered case IDs. All
required Phase 7–10 runtime outputs were present and validated through public services. Optional
Phase 8 daily/cumulative quantile resources were present and manifest-validated; their output hashes
were not needed by the dashboard and were not verified. The selected historical query returned 14
Store 1 rows for 2015-06-01 through 2015-06-14; the screen's default selection displayed 56 source
rows ending no later than 2015-07-03. The 2015-06-19 Store 1 issuance returned 14 saved raw and 14
operational points. Fit B returned 28 daily and 42 cumulative rows. No Phase 10 ledger, protected
July 4–31 outcome, full prepared-source hash, model fit, simulation or artifact generation was
performed. Canonical values and files were unchanged.

**Service-returned provenance** (SHA-256 values come from service DTOs; this is not an independent
full-file audit):

| View / selector | Run and manifest | Output and selected rows |
|---|---|---|
| Forecast issuance, `phase7_selected_forecasts` | Run `365f22d4c3f94722a594ab934a22c4f6`; manifest `03a1f26ba5855fd0576667bf280df938664c196a802de0a71e696a600b281cdc` | `72566349b233ef26c8de5b4f9c1623ac66df8676ad0370ad63b192ed4c1b5b09`; 14 selected / 46,830 manifest rows |
| Model comparison, `phase7_model_comparison` | Same Phase 7 run and manifest above | `c648e8e407dc367e56f26cb421656dabc8d742a9a3cd3d3b092b746a84b10357`; model views selected 42 horizon rows and 9 standalone coverage rows / 190,680 manifest rows |
| Daily uncertainty | Run `phase8-impl-20261006-provenance-review`; manifest `63a00fc8c50ccff99360cd8790498e977e08ec6a9846780a4e1a8ab3498d71c2` | `160e68f4dd0237b61e60d20d041e06d0760fd94b006f7e89730e24e96b601fd2`; 28 selected / 62,440 manifest rows |
| Cumulative uncertainty | Same Phase 8 run and manifest above | `f338ff7189d652e64c8aa27f3d03c205c313185fb205f9f8a50b9776d59c0a0e`; 42 selected / 93,660 manifest rows |
| Inventory comparison, `phase10_comparison` | Run `phase10-dev-20261008-validator-fix`; manifest `1c914b8a0fc7582c192f24fb8286e8521669cc079162cf832a58f2d8a1569f16` | `8d4b519e87677e04ff0f5e75404c37671c22c9b7ed0b229728bf17444a61e7be`; 10 selected / 1,720 manifest rows |
| Inventory policy summary, `phase10_policy_summary` | Same Phase 10 run and manifest above | `93d2e36e286be7c36c33c383b07d73569637f70de5d96378a0a72e85f60f9cb0`; 2 / 383,560 manifest rows |
| Inventory policy targets, `phase10_policy_targets` | Same Phase 10 run and manifest above | `e8ba96d12ecd307df8d8c21368f448ff3a45dca1ed6f21be6bba22b2c66a95ba`; 2 / 383,560 manifest rows |

The registered output sizes were inspected with filesystem metadata, without hashing the history
source or ledger: selected forecasts 3,036,226 bytes; model comparison 20,955,918; daily
uncertainty 2,434,227; cumulative uncertainty 3,687,518; optional quantile outputs 21,434 and
25,838; scenario catalog 4,236; Phase 10 comparison 427,485; policy summary 44,481,689; and
policy targets 17,329,746 bytes. Optional quantile outputs are not in the service provenance table
because the dashboard does not query them.

**Browser and concurrency evidence:** Microsoft Edge on the host was driven with Playwright at
1365×900 and 390×844. This is actual browser interaction, but automated rather than a human manual
review. All five screens, navigation, refresh/apply, saved origins and metrics, forecast/uncertainty
labels, inventory case selectors and model evidence views rendered from local accepted evidence;
the browser reported no page or console errors. Five mobile screens retained 390-pixel document
width after collapsing the sidebar. Inventory grids expose internal horizontal scrolling (measured
content widths up to 3,319 pixels inside 356-pixel viewports); data remain individually scrollable.
Keyboard Tab traversal reached controls and headings, and an interactive control showed a visible
focus box-shadow. A nonexistent benign private-resource URL returned only the generic app shell.
Screenshots stayed in the local temporary directory and were not committed.

Screen results: Overview showed the project purpose, saved-resource readiness and Refresh control.
Historical Sales rendered Store 1's default 2015-05-09 through 2015-07-03 selection (56 source
rows), displayed the development cutoff, kept source Open distinct from monetary Sales and did not
show the protected period. Forecast Explorer offered only the three accepted origins; the selected
issuance remained H14 while H7 changed only the display, and raw and operational values stayed
separate. The 2015-06-19 Fit B panel showed saved daily/cumulative evidence and provenance with
empirical-coverage caveats. Model Comparison rendered all three evidence views; saved MAE retained
the weak h10 row, common-population WAPE/MAPE labels preserved saved denominators and units, and
standalone coverage stayed separate. Inventory Comparison rendered the reference and
`synthetic_base-20150605-r00--buffer_090` cases, all ten saved case aggregates and the optional
Store 1 pair; choosing a Store did not replace whole-case values, and positive cost difference was
labeled adverse. Monetary and synthetic-assumption caveats remained visible.

Two independent browser contexts submitted the common model view and standalone coverage view
concurrently; both completed, then context A changed to saved horizon MAE while context B retained
standalone coverage. Measured concurrent completion was 2.45 seconds. Session state passed and the
browser reported no page/console errors. This verifies two sessions on one host process, not an
independent LAN device or external concurrency beyond the existing service lock.

**Performance method and results:** Windows 11 build 10.0.26300 x64; Ryzen 5 5600H, 6 cores / 12
threads; 16 GiB installed RAM; Python 3.14.5; Streamlit 1.65.0; uv 0.12.23. Lock SHA-256 is
`151cd5a2a868b219d315d8333d75d54e8c1f7efa43afa0869933a5682852dbd5`. A cold visit was timed from
navigation to the Overview readiness content after starting a fresh process and browser. Warm
latency was measured from each button click until the Streamlit websocket reported the submitted
script run complete; each analytical screen used its representative bounded query. Twenty samples
per screen; p95 uses nearest-rank ordering. All 20 samples for every screen were at or below 3
seconds. Cold visit was 2.114 seconds. Peak process working set was 323.3 MiB for one session and
328.2 MiB for two sessions, below the 1 GiB budget.

| Screen | 20 warm click-to-complete samples (seconds) | p50 | p95 | ≤3s |
|---|---|---:|---:|---:|
| Overview & Evidence | 0.242, 0.214, 0.212, 0.207, 0.211, 0.208, 0.190, 0.206, 0.205, 0.215, 0.198, 0.219, 0.204, 0.202, 0.216, 0.210, 0.216, 0.209, 0.217, 0.225 | 0.210 | 0.225 | 20/20 |
| Historical Sales | 0.618, 0.561, 0.655, 0.556, 0.629, 0.598, 0.532, 0.527, 0.518, 0.538, 0.546, 0.569, 0.645, 0.528, 0.552, 0.518, 0.505, 0.517, 0.484, 0.505 | 0.542 | 0.645 | 20/20 |
| Forecast Explorer | 0.569, 0.539, 0.533, 0.515, 0.546, 0.550, 0.573, 0.545, 0.592, 0.552, 0.557, 0.575, 0.587, 0.571, 0.587, 0.559, 0.567, 0.584, 0.545, 0.597 | 0.563 | 0.592 | 20/20 |
| Model Comparison | 1.273, 1.219, 1.162, 1.267, 1.232, 1.371, 1.562, 1.524, 1.351, 1.278, 1.282, 1.197, 1.157, 1.286, 1.349, 1.308, 1.231, 1.294, 1.343, 1.244 | 1.280 | 1.524 | 20/20 |
| Inventory Comparison | 0.703, 0.729, 0.728, 0.719, 0.702, 0.799, 0.915, 0.885, 0.932, 0.943, 0.880, 0.983, 1.112, 1.083, 1.157, 1.029, 1.195, 1.059, 1.173, 1.025 | 0.938 | 1.173 | 20/20 |

**Historical acceptance assessment before the user scope change:** The earlier private-LAN draft
required an independent viewer and trusted network. At that time the audience was localhost only,
the observed Wi-Fi profile was Public, and no LAN URL, listener, firewall rule or separate reviewer
device test existed. These facts remain historical and no LAN test is claimed. The user's later
localhost-only decision supersedes the LAN gate; see the current M4 scope addendum below.

Validation on the locked Windows environments passed: the focused dashboard/M2/M3/config suite
passed 79 tests on Python 3.12 and 79 on Python 3.14; the full fixture suite passed 536 tests on
each interpreter, with one existing Starlette/httpx deprecation warning per run. Ruff lint and
format passed (106 Python files); `uv lock --check` resolved 109 packages; `uv pip check` found 91
compatible packages on Python 3.12 and 93 on Python 3.14; the Markdown checker passed with 268
local destinations/anchors across 28 Markdown files; and `git diff --check` passed. The locked
environment uses Python 3.14.5 / uv 0.12.23, Streamlit 1.65.0 and `uv.lock` SHA-256
`151cd5a2a868b219d315d8333d75d54e8c1f7efa43afa0869933a5682852dbd5`. No package or lockfile
changed. The M4 implementation commit is `32df3ba4a48530bce556659d856991e134813e47` in [draft
PR #32](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/pull/32). GitHub Quality
[run #98](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/actions/runs/38024243400)
passed both Python 3.12 and 3.14 jobs on published PR head `5f095c12f9b0ad9dec9ffc877457915f62ff0985`.
The final head is rechecked after this documentation-only update. No Phase 10 daily ledger or
protected July 4–31 outcomes were accessed; no artifact was regenerated or changed.

### Phase 12 M4-01 corrective review - 2026-10-10

This is the pre-closeout review checkpoint; its pending-review status is superseded by the formal
closeout below.

M4-01 on the existing Draft PR #32 is corrected in the dashboard source: the saved MAE heading
renders `Saved MAE by horizon · h1–h14`, and standalone coverage renders
`Standalone forecast coverage · separate population`. AppTests assert each exact rendered
subheader. A scan of dashboard application Python files found no additional common mojibake
markers. The correction changes no service, query, metric, saved result, dependency or security
configuration.

The focused dashboard/M2/M3/config suite passed 79 tests on Python 3.14; the full fixture suite
passed 536 tests on both Python 3.12 and 3.14, with the existing Starlette/httpx deprecation warning.
Ruff lint/format, lock consistency, both installed-environment dependency checks, documentation
links, and whitespace checks passed. GitHub Quality run #100 passed both Python 3.12 and 3.14 jobs
on corrected head `4477ff69951f863a1a0eb4441d4cc15db3615d78`. Deployment remains bound to
`127.0.0.1` under the localhost-only scope decision. No LAN acceptance is required or claimed;
LAN/network/cloud exposure is out of scope. Phase 12 remains open pending human visual review and
independent final review. No Phase 10 ledger or Phase 13 holdout was accessed.

### Phase 12 M4 localhost-only acceptance scope - pre-merge checkpoint 2026-10-10

The user explicitly selected local development, analysis and live demonstration on the user's own
Windows computer. This decision is recorded in ADR-024 in [DECISIONS](DECISIONS.md) and supersedes
the earlier private-LAN option and independent-LAN-viewer acceptance gate. The
historical LAN assessment above remains a record of what was not performed; it is not a current
blocker. The approved target is `http://127.0.0.1:8501`. LAN access, network-profile changes,
firewall rules, tunnels, cloud deployment and public hosting are outside scope. No LAN tests are
claimed or required.

M4 remains IMPLEMENTED / UNDER REVIEW. Exact rendered-heading AppTests passed in the focused
dashboard/M2/M3/config suite (79 tests on Python 3.14). The full fixture suite passed 536 tests on
both Python 3.12 and 3.14, each with the existing Starlette/httpx deprecation warning. Ruff lint and
format passed; `uv lock --check` resolved 109 packages; `uv pip check` passed for 91 packages on
Python 3.12 and 93 on Python 3.14; Markdown validation passed with 275 local destinations/anchors
across 28 files; `git diff --check` passed. The existing browser, security and performance evidence
remains recorded. The current configuration still binds to `127.0.0.1`, disables static serving,
and keeps CORS and XSRF protection enabled. Human visual review of all five screens in a real
localhost browser and independent final review of Draft PR #32 remain pending. Keep the PR Draft and
unmerged; do not close Phase 12. Analytical services and accepted artifacts are unchanged, and no
Phase 10 ledger or Phase 13 holdout was accessed.

### Phase 12 formal closeout - 2026-10-10

**Phase 12 is COMPLETE.** M1-M4 are ACCEPTED / INTEGRATED. M3 PR #31 is merged at
`28aa42fdb2186dbbc340bef72917ce2e2ec06425`; main Quality [run #96](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/actions/runs/37966506688)
passed on Python 3.12 and 3.14 at that merge SHA. M4 PR #32 was squash-merged at
`5527e780d1a59108c041bb4ca33a32dbb3bc3aca`, containing the independently accepted reviewed head
`8b4275a24030f4ceb21b2f3d5f88b2c23016aae1`; main Quality [run #103](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/actions/runs/38031584298)
passed both Python jobs at the exact merge SHA. Findings M3-01 and M4-01 are resolved.

M3-01 added a dedicated sanitized overflow-exception path for `ModelComparisonTooLargeError`.
M4-01 corrected the headings to `Saved MAE by horizon · h1–h14` and
`Standalone forecast coverage · separate population`; AppTests assert each exact subheader.

For precision, PR-head Quality [run #102](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/actions/runs/38030547822)
reported **535 passed, 1 skipped, 1 warning per Python job** on the reviewed M4 head. The distinct
post-merge main run #103 also reported 535 passed, 1 skipped and 1 warning per job. The separate
local full pytest result recorded for the M4 finalization task was 536 passed per interpreter.
Existing automated functional, browser, security and performance evidence remains in the M4
checkpoint above; no new measurements were made for closeout.

The user personally reported PASS after visually reviewing all five screens at
`http://127.0.0.1:8501`, including layout, interactions and data boundaries. This is user-attested
human acceptance, not an agent-run manual test. The localhost-only boundary remains in force under
ADR-024; no LAN test is claimed or required, and LAN, network, firewall, tunnel, cloud and public
exposure remain out of scope.

Known scientific and operational limits remain: Sales is monetary turnover, not physical demand or
SKU quantities;
development model selection is not final-holdout evaluation; raw and operational forecast paths
remain distinct and future Open is unknown; empirical uncertainty intervals do not guarantee
nominal coverage; and inventory results are conditional synthetic monetary simulations, not
observed stock or actual stockouts. Positive forecast-minus-baseline simulated cost is adverse;
negative is favorable only under the assumptions. Neither proves savings or optimal policies. Saved
artifact provenance and existing analytical service contracts are unchanged.

No Phase 10 daily ledger was accessed. No protected July 4-31 outcome was read, hashed or evaluated;
no accepted artifact or manifest was modified or regenerated, and no model was fitted or
recalibrated. Phase 13 remains PLANNED / NOT AUTHORIZED and the holdout remains protected.

Closeout validation used the locked Python environments: full pytest passed 536 tests on Python
3.12 and 536 on Python 3.14, each with one existing Starlette/httpx deprecation warning; Ruff lint
and format passed; `scripts/check_docs.py` passed with 277 local destinations/anchors across 28
Markdown files; `uv lock --check` resolved 109 packages; `uv pip check` passed with 91 compatible
packages on Python 3.12 and 93 on Python 3.14; `git diff --check` passed. These local counts are
separate from the GitHub CI run counts recorded above.

### WP2-S1 offline controlled-synthetic release candidate - 2026-10-21

WP2-S1 accepts the narrow future public-course objective and authorizes Milestone A only under
ADR-030. The new branch `feat/public-demo-offline-synthetic-bundle` is based on current
`origin/main` at `a747d7799919497dead9b98bc0498c12115adfc2`. Milestone A is
**IMPLEMENTED / UNDER REVIEW - AWAITING INDEPENDENT SOL 6.1 REVIEW**. Milestones B and C remain
NOT AUTHORIZED. ADR-024 localhost behavior and all forecasting, scientific, and protected-holdout
contracts remain in force.

The versioned release contract, deterministic standard-library builder, standalone verifier, CLI,
and fixture tests are recorded in [the release contract](PUBLIC_DEMO_RELEASE_CONTRACT.md) and
[the active plan](../plans/active/public-course-demo.md). The only generated candidate is the
ignored and untracked directory `artifacts/public_demo/rossmann-course-demo-synthetic-v1/`. Its
`demo_bundle.json` is 326,074 bytes with SHA-256
`9b7ee60df204d11a4a993a84ceb236c5885c373168b0d6a767c99654683ecfdb`; `demo_manifest.json` is
3,708 bytes with SHA-256
`75a5ac794fffd01883bdf8b76b1ad669fbf2effb92d2d65a64fb1ae1288a56d4`. The manifest pin and
deterministic regeneration both verified. The bundle contains 165 synthetic history rows, 126
forecast rows, 6 uncertainty views, 168 daily interval rows, 252 cumulative rows, 126 comparison
basis rows, 69 comparison rows, 2 inventory views, 6 policy-pair rows, and 20 aggregate rows.
No source, canonical result, model, protected outcome, credential, or real-data-derived content was
read or packaged; no network, model fitting, prediction generation, calibration, or simulation was
performed.

The 21 focused bundle tests passed. The full fixture suite passed 1,248 tests with 7 skips and 1
existing Starlette/httpx deprecation warning in a clean isolated tracked-only worktree at the same
base plus the scoped changes. Six skips require unavailable Windows symlink privilege; one optional
canonical-upstream-artifact test has no fixture artifact. Ruff check and format passed; the Markdown
checker passed with 347 local destinations/anchors across 38 files; locked dependency consistency
resolved 109 packages and the installed environment reported 93 compatible packages; CLI build,
verification, regeneration, and `git diff --check` passed. No dependency or lockfile changed.
Python was 3.14.5. A standalone `uv` executable was not on this shell's PATH at closeout; the earlier
offline lock and dependency commands completed successfully. The generated candidate remains local
and ignored. The next authorized boundary is independent Sol 6.1 review of this exact branch; this
entry does not authorize a public-compatible runtime, hosting, publication, or integration.

### WP2-S3 correction of independent review findings — 2026-10-21

The WP2-S2 red-first regression run was performed against the original snapshot in a disposable
checkout. It produced **13 failed, 12 passed, 25 deselected**; the failures reproduced the Windows
junction escape, incomplete or inconsistent manifest provenance, and float-valued byte-count
acceptance. No run used real Rossmann data or canonical artifacts.

The builder and directory verifier now reject symbolic links and Windows reparse-point aliases in
existing path components, and check resolved containment under the checkout before file operations.
Manifest validation now recomputes the configured generator digest, requires valid module/script/
project/lock hashes and complete installed-distribution versions, validates optional Git revision
shape, and accepts only a bounded JSON integer byte count matching the encoded bundle size. The
tests exercise actual CLI rejection through a Windows junction, verifier and builder aliases,
resealed provenance mutations, strict byte-count scalar types, and cleanup after failed writes or
renames. The release contract and active plan record these controls and their race-condition limit.

Post-fix `tests/test_public_demo_bundle.py -q` passed **49 tests**, with one skip because this Windows
host does not grant directory-symlink creation. The full tracked-only fixture suite passed **1,276
tests, 8 skipped**, with one existing Starlette/httpx deprecation warning, in an isolated checkout
overlaid with exactly the ten scoped files. Seven skips require unavailable symlink privileges; one
existing optional test requires canonical artifacts intentionally absent from the checkout. Ruff
lint and format passed; `scripts/check_docs.py` passed with 347 local destinations/anchors across 38
Markdown files; offline `uv lock --check` resolved 109 packages; both `uv pip check` (93 packages)
and `pip check` passed; `git diff --check` passed. No dependency or lockfile changed.

Independent builds in two isolated checkouts produced identical bytes. The bundle remains 326,074
bytes with SHA-256 `9b7ee60df204d11a4a993a84ceb236c5885c373168b0d6a767c99654683ecfdb`; ordinary
verification and out-of-band-pinned deterministic regeneration passed. The regenerated manifest is
3,708 bytes with SHA-256
`6244c73cd0954fdf121209497a0425d509c687cb5c9a274b27c5f4250cefcf9c`, reflecting the corrected
builder/source identity while preserving the synthetic bundle content. Milestone A remains
**IMPLEMENTED / UNDER REVIEW — AWAITING SOL 6.1 REREVIEW**; the corrected local outcome is
`CORRECTED_AWAITING_SOL_REREVIEW`. The exact local snapshot is ready for independent rereview. No
commit, push, PR, publication, deployment, host provisioning, or Milestone B/C work occurred;
ADR-024 and all data, scientific, and holdout boundaries remain in force.

### WP2-S5 correction of WP2-S4 dependency-version finding - 2026-10-21

WP2-S4 independent rereview returned **REQUEST_CHANGES** because the plain verifier accepted
malformed dependency versions `1+.` and `1a1b1` after canonical manifest resealing and with a
matching SHA-256 pin. A test-first run reproduced both cases (**2 failed, 50 deselected**).

The verifier now bounds each required installed version to 128 ASCII characters and accepts a
normalized PEP 440-compatible subset: optional numeric epoch, dotted numeric release, at most one
`aN`/`bN`/`rcN` pre-release, optional `.postN`, optional `.devN`, and optional local identifiers
with nonempty alphanumeric segments. It uses local regular-expression validation; production code
does not import `packaging`, and neither project dependencies nor `uv.lock` changed. A local
`packaging.version.Version` oracle was used to confirm the specified valid and malformed examples.
Ordinary verification accepts syntactically valid portable versions with a matching manifest pin;
deterministic regeneration still requires exact current environment identity.

Permanent tests apply 17 malformed values and 10 supported valid forms to all five required
dependencies, reseal manifests canonically, and supply matching pins. They cover overlong versions,
empty or repeated segments, punctuation, and Boolean/integer/float/null/array/object values. The
portable-version test passes ordinary verification and is rejected by deterministic regeneration;
the generated manifest using the actual installed versions also passes. The focused version cases
passed **136 tests**. Existing junction containment, complete provenance, bounded integer byte
count, and bundle identity checks remain covered.

The full fixture suite passed **1,412 tests, 8 skipped**, with one existing Starlette/httpx
deprecation warning, in the isolated tracked-only checkout (267.84 seconds). Seven skips need
unavailable Windows symlink privilege; one optional test needs canonical upstream artifacts absent
from the checkout. Ruff check and format passed; the Markdown checker passed with 347 local
destinations/anchors across 38 Markdown files; `uv lock --check --offline` resolved 109 packages;
`uv pip check` and `pip check` passed with 93 compatible packages; `git diff --check` passed.

Two isolated deterministic builds produced byte-identical bundles and manifests. The unchanged
bundle is 326,074 bytes, SHA-256
`9b7ee60df204d11a4a993a84ceb236c5885c373168b0d6a767c99654683ecfdb`, with 165 history rows, 126
forecasts, 6 uncertainty views, 168 daily intervals, 252 cumulative rows, 126 comparison basis
rows, 69 model comparison rows, 2 inventory views, 6 inventory policy pairs, and 20 aggregate
rows. The new 3,708-byte manifest SHA-256 is
`3ca3d770f813fbca6dac5b9ad594ac5cf75ab12b9ec908a3d308d0ccac8389cb`. Ordinary pin verification
and pinned deterministic regeneration passed in both checkouts. The versioned synthetic release
remains offline and uncommitted. Milestone A stays **IMPLEMENTED / UNDER REVIEW - AWAITING
INDEPENDENT SOL 6.1 REREVIEW**; the local outcome is `CORRECTED_AWAITING_SOL_REREVIEW`. No commit,
push, PR, publication, deployment, real-data access, or Milestone B/C work occurred.

### WP2-S7: ASCII dependency version validation (2026-10-22)

WP2-S6 returned **REQUEST_CHANGES** for WP2-S6-01 (MAJOR): `re.IGNORECASE` allowed Unicode
case-fold equivalents to match the documented ASCII dependency-version grammar. Before changing
the production validator, the new pinned regressions were run against the S6 implementation. The
test-first command `python -m pytest tests/test_public_demo_bundle.py -q -k unicode --tb=no`
reported **26 failed, 25 passed, 186 deselected** in 6.29 seconds: 25 dependency-field API
mutations and the matching-pin CLI case reproduced the bypass; Unicode digits, non-ASCII local
letters, combining marks, whitespace and a Unicode keyword lookalike were already rejected.

The focused correction adds `re.ASCII` alongside `re.IGNORECASE` in
`src/rossmann_forecasting/app/demo_bundle.py`. It preserves the existing version grammar, ASCII
case-insensitive forms, 128-character bound, type checks, portable ordinary-verification behavior,
and exact-environment deterministic-regeneration check. Permanent tests cover all five confirmed
case-fold values and representative Unicode categories across all five required dependency fields,
plus an actual CLI rejection with a matching manifest SHA-256 pin. The post-fix Unicode command
reported **51 passed, 186 deselected** in 6.97 seconds. The independent `packaging.version.Version`
26.3 oracle rejected all five original case-fold values; it is not a production dependency.

The complete fixture suite ran in the locked Python 3.14.5 environment in a disposable tracked-only
workspace: **1,463 passed, 8 skipped, 1 warning** in **390.45 seconds**. It included 236 passing
public-demo tests with one unavailable directory-symlink skip and 256 application/API/dashboard
compatibility tests. Seven skips require Windows symlink privileges; one optional test requires
canonical artifacts absent from the isolated checkout. The sole warning is the existing
Starlette/httpx TestClient deprecation. Ruff lint passed; Ruff format confirmed **146 files**;
documentation validation passed with **349 local destinations/anchors across 38 Markdown files**;
offline lock checking resolved 109 packages; `uv pip check` found 91 compatible packages;
`git diff --check` passed. The temporary checkout printed Git LF-to-CRLF advisory messages for four
unrelated WP1 fixture files, with no whitespace-check failures.

Two independent tracked-only workspaces on Python 3.14.5 and the same locked dependency set
produced byte-identical releases. `demo_bundle.json` remains **326,074 bytes**, SHA-256
`9b7ee60df204d11a4a993a84ceb236c5885c373168b0d6a767c99654683ecfdb`. Its counts remain **165 / 126
/ 6 / 168 / 252 / 126 / 69 / 2 / 6 / 20**. Ordinary verification, out-of-band-pinned ordinary
verification, and pinned deterministic regeneration passed in both workspaces. The corrected
3,708-byte manifest SHA-256 is
`6bccb0c1e19a166e34cca4fe293d1d8ee100e85db4ad4a194eb54c8eace2d462`; its generator module SHA-256
is `ac3910f382d61296d5229048441d793383858d41ef437d859c9f264e2a35a704`. The manifest records the
unchanged builder script, configuration, project and lock identities, Python 3.14.5, and installed
versions FastAPI 0.143.0, NumPy 2.5.3, pandas 3.0.6, PyArrow 24.0.0, and Streamlit 1.65.0. The
synthetic numerical bundle is byte-identical to the accepted S5 content.

The final implementation, documentation and test snapshot remains **IMPLEMENTED / UNDER REVIEW —
AWAITING SOL 6.1 REREVIEW**. No commit, push, PR, public release, deployment, real-source access,
protected-holdout access, or Milestone B/C work. The final rereview handoff reports raw-byte SHA-256
identities for all ten Milestone A files; the five pre-existing documentation identities match their
WP2-S6 pre-fix values.

### WP2-S9 Milestone A integration (2026-10-23)

The exact ten-file WP2-S8-accepted Milestone A snapshot was published in PR #52 and squash-merged
into `main`. Publication commit `5e1722220c0a3e2944788a470af68b4c3abc949d` has parent
`a747d7799919497dead9b98bc0498c12115adfc2`; squash merge and `main` are
`086c59183e237279a21139a62265e7450890fa63`. The AI WP2-S8 ACCEPT was technical review evidence,
not human GitHub approval. The ten committed paths and permitted Markdown CRLF-to-LF normalization
were verified against the reviewed snapshot. No generated JSON assets entered Git.

PR Quality [run](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/actions/runs/39904731393)
on the exact publication SHA and post-merge main Quality [run](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/actions/runs/39905208913)
on the exact merge SHA each passed Python 3.12 and 3.14. Each job ran locked dependency installation
and consistency, full fixture tests, Ruff lint/format and Markdown validation. Both PR jobs reported
1,464 passed, 7 skipped and 1 existing Starlette/httpx deprecation warning. Post-merge Python 3.12
reported 1,464 passed, 7 skipped and 1 warning in 251.89 seconds; Python 3.14 reported 1,464 passed,
7 skipped and 1 warning in 236.38 seconds. Seven skips comprise six Windows-only junction tests
and one optional test requiring ignored canonical artifacts absent from CI. GitHub also emitted the
informational `ubuntu-latest` runner-image migration annotation; no job steps failed.

The generated controlled-synthetic bundle and manifest remain ignored and unpublished. ADR-024
continues to govern localhost behavior; ADR-028's remaining proposals are not accepted, and ADR-030
does not authorize publication or hosting. WP1 remains incomplete and Phase 13 remains separately
gated.

### WP2-S10 offline verified synthetic provider and services 2026-10-23

WP2-S10 implements Milestone B1 on `feat/public-demo-verified-service-provider`, based directly on
`origin/main` at `086c59183e237279a21139a62265e7450890fa63`. `DemoProvider.open` requires the explicit
controlled-synthetic profile and a separate lowercase manifest SHA-256, validates the fixed release
through the integrated Milestone A verifier, checks a bounded in-memory snapshot against the
verifier's bundle and manifest digests, recursively freezes it and creates fixed lookup indexes.
Only the explicit `.open()` factories can construct providers or services; their ordinary public
constructors are disabled. The six `DemoServices` methods return frozen synthetic-specific DTOs with
release/evidence/hash/schema provenance and no canonical phase, run or artifact identities. Queries
only filter the snapshot; they do not read or write files, call the network, load the canonical
artifact reader, or execute models, calibration or inventory simulation. Missing/invalid releases
fail closed without rebuild or fallback.

The tests generate fixtures only with `demo_bundle.generate_release_bytes(Path.cwd())` and use the
resulting bytes under a temporary repository. The fixed seed is 4063; the generated bundle is
326,074 bytes with SHA-256
`9b7ee60df204d11a4a993a84ceb236c5885c373168b0d6a767c99654683ecfdb`, and the 3,708-byte manifest
in the tracked-only verification worktree has SHA-256
`294b3f1fbe2f6ca66a498209561f713c31291db949bbc1f837f7603fd25d9bd3`. Its recorded inputs are
Python 3.14.5, `uv.lock` SHA-256
`16d76d6ffca3848e6af5f7ab838bc16c6b88d18b1af0097e5a3c216fe7e36ad0`, `pyproject.toml` SHA-256
`2180751e965612c20a53ef194073d68d0d55eb6325fa5e28a9d41beca294f6a7`, current base revision
`086c59183e237279a21139a62265e7450890fa63`, builder module SHA-256
`a0910f65dc67903a5c37a17f54267c849560e05977956c5b39f2e04dcf4b1532`, and build-script SHA-256
`c4fdcfa0e2409001601b8d17846011c17ac4b983474a211f45301c553d471a9c`. Tests derive the manifest
pin independently from those bytes and pass it explicitly; this temporary identity is not a
production setting or publication approval.

The focused Milestone A, provider/service and application/API/dashboard regression command passed
**518 passed, 1 skipped, 1 existing Starlette/httpx deprecation warning in 87.93 seconds**. The
artifact-free tracked-only worktree's full suite passed **1,489 passed, 8 skipped and the same one
warning** in 269.28 seconds. The skips were six Windows symlink
creation checks unavailable without the required privilege, one public-demo bundle symlink check
with the same restriction, and one optional inventory test requiring absent ignored canonical
artifacts. The isolated checkout contained no ignored `artifacts/` directory; no Rossmann data,
canonical artifact, model binary or protected outcome was opened or enumerated.

Ruff lint passed; formatting reported 150 files already formatted; Markdown validation passed for
350 local destinations/anchors across 38 Markdown files; offline `uv lock --check` resolved 109
packages without a lock change; `uv pip check` found all 91 installed packages compatible; and
`git diff --check` passed. The isolated environment used Python 3.14.5 and `uv 0.12.23` with locked
`dev`, `api` and `dashboard` extras installed offline. The deterministic release-byte test passed.
No dependency, FastAPI HTTP adapter, dashboard, Streamlit entry point, localhost configuration,
generated release asset or scientific method changed.

The exact B1 snapshot is **IMPLEMENTED / UNDER REVIEW — AWAITING SOL 6.1**. The work remains local
and uncommitted. Milestone B is incomplete; B2, WP2 closeout, Git publication, hosting, public
content release and deployment remain unauthorized. The only next boundary is independent Sol 6.1
review of B1.

### WP2-S12 B1 Git integration and CI identity clarification (2026-10-23)

B1 was independently accepted in WP2-S11 and squash-integrated through PR #53 at
`a31f9d610ea7922629d24c4b134cd986f634bcb4`. Publication head
`626acf76726a63efe7f264e9669aaab11af90d19` was based on
`086c59183e237279a21139a62265e7450890fa63`. The PR Quality run
[#39924005789](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/actions/runs/39924005789)
and post-merge Quality run
[#39924475405](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/actions/runs/39924475405)
passed on Python 3.12 and 3.14. The PR's actual temporary merge-ref checkout was
`f2dd84f07d1d11c22a55c140397dfe4ab2e85fb1`; the final squash merge is
`a31f9d610ea7922629d24c4b134cd986f634bcb4`.

This appended clarification closes nonblocking finding WP2-S11-01 without rewriting its historical
checkpoint. Milestone A PR #52 publication head was
`5e1722220c0a3e2944788a470af68b4c3abc949d`; its actual temporary PR checkout was
`ddae5428714dd9b784d12b91bcc40c00e4635eb7`, combining it with then-current base
`a747d7799919497dead9b98bc0498c12115adfc2`; its squash merge was
`086c59183e237279a21139a62265e7450890fa63`. Workflow association, tested merge-ref commit and final
squash merge are distinct identities. PR #52 Quality run
[#39904731393](https://github.com/mihikari29/it4063e-rossmann-demand-forecasting/actions/runs/39904731393)
and the post-merge Quality run passed on Python 3.12 and 3.14.

### WP2-S13 B2-A offline synthetic FastAPI adapter (2026-10-23)

WP2-S13 implements the offline B2-A adapter on `feat/public-demo-synthetic-api-adapter`, based on
integrated B1 merge `a31f9d610ea7922629d24c4b134cd986f634bcb4`. New files are
`src/rossmann_forecasting/app/demo_api.py` and `tests/test_public_demo_api.py`. The adapter exposes
`create_demo_app` only; there is no module-global `app`. Construction requires the exact
`DemoProfile.CONTROLLED_SYNTHETIC` enum and a separate lowercase manifest SHA-256, accepts an
optional trusted `Path`, and calls `DemoServices.open` once. A missing, corrupt or mismatched release
leaves `/health` available for process liveness and returns sanitized 503 responses from analytical
routes without retry or canonical fallback. Invalid configuration fails factory construction.

The app exposes exactly seven GET routes: `/health`, `/api/v1/catalog`, `/api/v1/history`,
`/api/v1/forecasts`, `/api/v1/uncertainty`, `/api/v1/model-comparison`, and `/api/v1/inventory`.
FastAPI docs, ReDoc and OpenAPI are disabled. Successful analytical responses use the exact visible
label `CONTROLLED SYNTHETIC DEMONSTRATION — NOT OBSERVED ROSSMANN DATA`, with the frozen B1
result data and one top-level `SyntheticProvenance`. Query/body and serialization bounds are
implemented; invalid input maps to sanitized 422, unavailable/invalid releases to sanitized 503,
unexpected errors to sanitized 500, and missing paths/methods to sanitized 404/405 with the `Allow`
header preserved. No CORS, write/upload/admin routes, arbitrary paths, model execution, calibration,
metric recalculation, inventory simulation or listener was added. The existing canonical API,
Streamlit app, dependency declarations and lockfile are unchanged.

The fixture test generates its synthetic bytes in memory and writes them only under a per-test
temporary repository. The bundle is **326,074 bytes**, SHA-256
`9b7ee60df204d11a4a993a84ceb236c5885c373168b0d6a767c99654683ecfdb`; each test independently
hashes the generated manifest bytes and supplies that pin. The ignored bundle was not written or
published. The tracked-only review worktree had no ignored `artifacts/` directory and did not read
Rossmann, canonical, model or protected-outcome files.

Validation passed on the locked Python 3.14.5 environment. The adapter suite passed **59 tests** with
one existing Starlette/httpx deprecation warning. Focused adapter, B1 provider/services, Milestone A,
canonical API and dashboard regressions passed **464 tests**, with one Windows symlink test skipped
and the same warning. The artifact-free tracked-only full suite passed **1,548 tests**, with **8
skipped** and the same warning in 289.63 seconds. Seven symlink tests skipped because Windows denied
symlink creation with WinError 1314; one optional inventory test skipped because ignored canonical
artifacts were absent.

Ruff lint passed; formatting found **152 files already formatted**; Markdown validation passed for
**352 local destinations/anchors across 38 Markdown files**; offline `uv lock --check` resolved 109
packages without a lock change; offline `uv pip check` found all **93** packages in the Python 3.14.5
environment compatible; and whitespace checks passed. No dependencies or generated repository
assets changed.

B2-A is **IMPLEMENTED / UNDER REVIEW — AWAITING SOL 6.1**. The work remains local and
uncommitted. B2-B, Milestone B closeout, Git publication, bundle publication, server startup, hosting,
public exposure and deployment remain unauthorized. The next boundary is independent Sol 6.1 review
of B2-A only.
