# Course submission readiness

**Local integration candidate; final course delivery incomplete.** Work is on the dedicated
`feat/course-submission-integration` branch, preserving current origin/main and the later HF
demonstration commit. No main merge, push, public upload or protected-data operation is part of
this task. [The integration plan](../plans/active/course-submission-integration.md) owns scope and
design; [progress](PROGRESS.md) owns reviewed scientific findings.

## Eight-module evidence matrix

| Course module | Functionality / evidence | Validation / limitation | Status |
|---|---|---|---|
| Business understanding / data generation | [Proposal](PROPOSAL.md), [dictionary](DATA_DICTIONARY.md), `inventory/scenarios.py`; monetary Store x Date H14 and explicitly synthetic operations | `tests/test_inventory_scenarios.py`; no physical demand, observed inventory or proven savings | COMPLETE |
| EDA | [Historical findings](EDA_FINDINGS.md), notebooks 01/02, `analysis/eda.py`, bounded `analysis/seasonal_decomposition.py` | `tests/test_eda_summaries.py`, `test_seasonal_decomposition.py`; historical exposure disclosed, real STL execution/findings gated | PARTIAL |
| Data cleaning | `data/preparation.py`, `data/validation.py`, [source validation](DATA_VALIDATION.md) | `tests/test_data_preparation.py`, `test_data_validation.py`; sparse/null/zero semantics retained, no new source preparation | COMPLETE |
| Feature engineering | [29-predictor contract](FEATURE_CONTRACT.md), `features/`, origin-safe recursion | `tests/test_feature_engineering.py`; selected schema/future-data boundary unchanged | COMPLETE |
| Model development | `forecasting/`, [development results](PROGRESS.md), frozen uncertainty and `inventory/simulation.py` | `tests/test_seasonal_naive.py`, `test_holt_winters.py`, `test_lightgbm.py`, `test_model_selection.py`, `test_uncertainty.py`, `test_inventory_simulation.py`; real scenario/final evidence blocked | PARTIAL |
| Deployment | Existing typed services/API/five-screen dashboard; [two-service candidate](LOCAL_DEMO_DEPLOYMENT.md) | `tests/test_public_demo_*.py`, `test_demo_runtime.py`, `test_demo_probe.py`; real HTTP smoke, no approved public pair | PARTIAL |
| Monitoring | [Contract](MONITORING.md), `monitoring.py`, `monitoring_report.py`, [notebook](../notebooks/03_model_monitoring.ipynb) | `tests/test_monitoring.py`, executed synthetic notebook; no production labels, Phase 13 M5 integration or approved numeric trigger policy | PARTIAL |
| Report / presentation | [Academic source/export guide](../reports/README.md), report PDF and actual 15-slide editable PPTX with native charts/notes | PowerPoint rendering and PDF/slide QA; final academic/human acceptance pending | PARTIAL |

COMPLETE denotes the retained scoped foundation, not instructor acceptance or full course delivery.
Tests do not authenticate historical artifacts or replace scientific review. The report transcribes
canonical Markdown evidence without loading/hashing source or canonical artifacts.

## Corrections and affected interfaces

The HF builder is now an offline retirement notice, with no upload operation or bundled fake
business results. Real FastAPI/Streamlit services replace JavaScript analytics. The runtime factory
requires explicit synthetic profile/pin; the launcher fixes loopback. The actual HTTP probe has
timeout, connection, HTTP and invalid-response states and distinguishes catalog readiness.

The old monitoring generator/notebook's target-derived pseudo-LightGBM, false KS, fixed Healthy
badge and absent three-day persistence are removed. Strict origin/horizon/label validation precedes
pairing. Shared metric arithmetic, calendar windows, Store/origin/horizon summaries, descriptive
feature changes, explicit availability and report provenance replace those mechanisms. Numeric
alarms remain unactivated under ADR-031. This adapter is separate from Phase 13 M5.

Implemented PDF/PPTX authoring/render tools are optional `reporting` dependencies, with a
generated lock. The existing Python 3.12/3.14 CI gates are retained and install this extra for
the editable-evidence tests. Core forecasting algorithms, selected recipe, uncertainty estimators,
inventory policies and canonical artifacts are unchanged. Documentation explains new emitted
fields, usage, synthetic meaning, actual external inspection and remaining acceptance.

## Prior validation (historical)

Full isolated fixture suites pass **2,576 tests, 10 skipped** on both Python **3.12.15** and
**3.14.5**, using uv **0.12.23** and the locked dev/api/dashboard/reporting extras. Nine skips
reflect Windows symlink privileges; one is the deliberately absent optional canonical-artifact
integration. Each suite has one existing Starlette/httpx deprecation warning and no failures.
The final HTML presentation adjustment was followed by current-source focused checks on both
versions: **42 passed** each, with the same warning. Full suites used the preceding code snapshot;
the final change affects HTML presentation only, not calculations, model or service behavior.
Independent Sol 6.1 corrective review **ACCEPTED**
the bounded code/draft-source candidate after fixes for overwritten horizon identity, closed-date
missing-forecast status and false constant-reference detection. The final derived HTML-table
improvement also received ACCEPT. This is separate from whole Milestone B/human/release acceptance.

Actual smoke checks returned 200 for all seven API routes, 422 for an invalid query, and 200 for
the Streamlit page and health endpoint; processes were then terminated. Notebook execution completed
seven code cells with one Windows zmq selector-thread warning. The seven-page PDF was exported,
text-checked, rendered and visually inspected page by page; the synthetic chart was also inspected.
Ruff lint/format, Markdown links, lock/dependency consistency and whitespace checks passed.
Final lint/format/link checks passed on both Python versions: 171 Python/notebook files formatted
and 248 local destinations/anchors across 38 Markdown files. All five changed/new CLI help checks
passed without starting services. Locked dependency checks passed for both isolated environments.
Initial adapter failures (missing shared metric metadata) and an exporter PDFium API error were
corrected before successful validation; no accepted scientific implementation was changed.

Executed full-suite arguments, from the tracked-files-only snapshot at
`outputs/validation/submission-candidate`, with separate `UV_PROJECT_ENVIRONMENT` directories:

```powershell
uv run --locked --python 3.12 --extra dev --extra api --extra dashboard --extra reporting python -m pytest -q --junitxml=../pytest-312.xml
uv run --locked --python 3.14 --extra dev --extra api --extra dashboard --extra reporting python -m pytest -q --junitxml=../pytest-314.xml
```

The executable was the installed uv 0.12.23 binary, called explicitly when absent from PATH.
The prior final current-source focused commands selected
`tests/test_monitoring.py tests/test_demo_runtime.py tests/test_demo_probe.py -q`, using the locked
3.14 environment and the locked 3.12 interpreter with repository `src` on `PYTHONPATH`.
Additional executed checks: `python -m ruff check .`, `python -m ruff format --check .`,
`python scripts/check_docs.py`, `uv lock --check`, `uv pip check` (including both isolated
interpreters), and `git diff --check`. No remote CI result is claimed for this unpublished diff.
The PDF export command used `--output-dir reports/generated/submission/report-v3`; the monitoring
generator used `--output-dir reports/generated/monitoring/submission-v2`. Both used the locked
environment, with `--extra reporting` for the PDF. Notebook execution used `nbclient.NotebookClient`
with a 120-second cell timeout and repository-root execution directory, then `nbformat.write`.

## Deliverables and external verification

Tracked deliverables are the report and presentation Markdown sources, source notebook, reusable
report/monitoring code and exact export/run instructions. Verified generated outputs remain ignored:

- `reports/generated/submission/report-v3/submission_report.pdf`: seven-page academic draft;
  page PNGs and provenance manifest are adjacent.
- `reports/generated/monitoring/submission-v2/`: readable HTML report, JSON summary, chart,
  independently authored fixture inputs and manifest.
- `reports/generated/monitoring/notebook-v1/executed_monitoring.ipynb`: seven executed code cells,
  with separate execution manifest.
- `reports/generated/submission/presentation-v3/rossmann_presentation.pptx`: actual 15-slide
  editable deck with native charts/diagram shapes and speaker notes, exported using python-pptx.
  PowerPoint PDF/PNGs and rendering provenance are in the adjacent `presentation-v3-render/`.
- `reports/generated/submission/offline-notice.html`: tested local HF-builder replacement;
  no upload or remote update occurred.

Read-only external inspection on November 6, 2026 returned `sdk=static` and `RUNNING` from the
historical Hugging Face Space metadata, while its static `/health` returned 404. This verifies
neither a public FastAPI backend nor approved release. Its HTML root returned 200, contained the
mock tester/fixed Healthy badge and had no `fetch(` call. That stale external content remains
unchanged and needs separately authorized withdrawal/replacement. Local
URLs identify ephemeral smoke-test services while running; no persistent service is promised.

## Pending operations and acceptance

| Gate | Required next evidence / operation |
|---|---|
| Protected / mixed-source access | Named operator and separately authorized preparation/custody before any source read/hash; independent verification and exact bindings for each purpose |
| Real Store-level scenarios / weekly STL | Approved safe input chain, purpose-specific loading/execution, output inspection and reviewed interpretation; no fixture-derived empirical conclusion |
| Frozen final evaluation | Separately authorized M4-B release journal and M4-C recovery, then M5-M8, resource review, development rehearsal, mechanical staging and each chronological analytical release; two unchanged H14 blocks/episodes |
| Public release | Existing corrective/visual acceptance, exact content/rights/pin, independent security/resource/rollback review, owner-approved host/audience/window, then deployment and external checks of two URLs |
| Production monitoring | Genuine immutable issuance and subsequent new observed labels; no such production evidence exists here |
| Numeric retraining-review policy | Separate approved development-only design/rehearsal; no automatic retraining/promotion or final-test adaptation |
| Academic ownership | Team review/understanding, course-compliant AI disclosure, report conclusion/slide acceptance and human demonstration rehearsal |

No credential or owner decision is inferred from an environment variable, existing Space or
branch. Independent work proceeds only within its own gate; pending evidence is not fabricated.
The continuation authorizes **local commits** after staged review and validation, while retaining
the push/PR/merge/release prohibition. [PR preparation](PR_READINESS.md) records the proposed
description and authorized-later remote-CI commands; Git and the ignored handoff manifest identify
the exact commit and new test runs. Do not treat the historical counts above as new execution.
[Public-release preparation](PUBLIC_RELEASE_CANDIDATE.md) and
[analytical readiness](ANALYTICAL_READINESS.md) define concrete remaining operations and acceptance.
The final submission package uses READY / NEEDS HUMAN REVIEW / BLOCKED and remains overall BLOCKED
for course delivery. A locally reviewed committed candidate can be READY FOR PR while remote CI,
human approval, final scientific evidence and public release remain outstanding.
