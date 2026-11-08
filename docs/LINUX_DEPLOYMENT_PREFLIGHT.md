# Linux portability and resource preflight

**Local Linux smoke PASS; two-Render hosting CONDITIONAL; unchanged hybrid packaging BLOCKED.**
This preflight implements no release, public listener, host selection or purchase. It is stacked
on the course-submission integration candidate. The existing Milestone B, independent security,
content/rights/provenance, human and owner-release gates remain effective.

## Scope and retained evidence

The requested integration base and clean worktree matched before work. A fresh source-allowlisted
candidate was generated under ignored `artifacts/deployment/linux-preflight-v1/`. After the bounded
configuration correction below, a second new candidate was generated under
`artifacts/deployment/linux-preflight-v2/`; the first was not overwritten. Each has 47 files,
including its candidate manifest. Exact revisions, source/output hashes, bundle/manifest pins,
commands, lock identity, seed and environment are in the generated manifests and the local
`outputs/validation/linux-preflight-v1/` evidence directory. These are private local evidence,
not approved publication bundles. Git owns the code/review chronology.

The final inventory has 35 named source files. Both API and dashboard use the same two immutable
synthetic release files and explicit manifest pin. All recorded candidate file digests were checked
before and after Linux execution. The configuration correction did not change either release file
or its pin. Ordinary pinned verification passed on Linux; deterministic regeneration against a
different host environment was not claimed. The separate monitoring fixture remains explicitly
distinct from the saved-service bundle and contains no production observations.

## Environment and build

Ubuntu 26.04.1 x86-64 ran on WSL2 with kernel 6.18.33.2, 12 logical CPUs and approximately 7.46 GiB
visible memory. Docker CLI was available, but its Linux daemon was unavailable; no image build or
container run occurred. An isolated Linux directory received only the checked candidate inventory,
not the repository's ignored data/artifacts, credentials or `.git`. WSL discarded an early `/tmp`
scratch directory on shutdown; the retained experiment used its own Linux home directory.

The official uv 0.12.23 Linux archive passed its published SHA-256 check. A fresh managed Python
3.12.15 environment successfully ran locked `api`/`dashboard` setup and dependency validation
(59 installed distributions). A separate fresh build replay also passed the blueprint's exact
`pip install uv==0.12.23 && uv sync --locked --extra api --extra dashboard` command using an isolated
Python 3.12.15 bootstrap environment. The initial uncached locked setup took about 26 seconds;
subsequent builds reused the download cache. Build resources were not constrained or profiled.

## Configuration correction

The builder previously authored an incomplete `.streamlit/config.toml`, omitting the repository's
reviewed `client.showErrorDetails="none"` and `server.fileWatcherType="none"` controls. A malformed
WebSocket widget-state probe exposed server-path/stack details with that generated configuration;
WSL also selected poll-based watching. The builder now includes the original reviewed config in
its literal source allowlist and copies its exact bytes instead of duplicating settings.
The existing loopback default, CORS/XSRF/static-serving/telemetry settings remain in that file;
the explicit proposed cloud CLI bindings still require separate release approval.

A regression assertion first failed on the old generated file and passed after the correction.
The final live WebSocket error probes confirmed redacted errors without server paths or stack
frames. This restores existing controls; it does not establish a comprehensive security review.
Initial one-use probe trials also required adapting radio state and dataframe names to the locked
Streamlit wire protocol; their failed reports remain separate from the completed runs.

## HTTP, UI and restart checks

Both initial and corrected candidates passed real Linux loopback execution. The final run checked:

- All seven API GET routes: health, catalog, bounded history, forecasts, uncertainty, comparison
  and inventory returned 200. Analytical response pins, bundle hashes and synthetic labels matched.
- Invalid Store and duplicate/unsupported-query requests returned sanitized 422 responses.
- In a separate source-only copy missing the synthetic bundle, health returned 200 and all six
  analytical routes returned 503. A wrong manifest pin also produced catalog 503.
- The supported `scripts/verify_local_demo.py` probe reported synthetic bundle readiness.
- Streamlit root and health returned 200. Real WebSocket sessions rendered all five saved-service
  screens and the separate monitoring workspace, including tables, charts, selectors and truthful
  provenance. Monitoring reported `DESCRIPTIVE_ONLY`. This checks server-generated UI content,
  not browser pixel layout or human visual acceptance.
- Fresh API/dashboard processes repeated readiness and all six UI views with the same pin.
  A missing-bundle dashboard remained live but displayed unavailable content and no result table.
- Both deliberately malformed UI-state probes were redacted; there were no unexpected application
  exceptions in the valid UI flows. The recorded HTTP assertions comprise 19 status-200, two
  status-422 and seven status-503 responses, plus the supported probe and Streamlit checks.

Each service had its own unprivileged user cgroup, a cleared environment containing only runtime
paths and non-secret fixture settings, and loopback binding. No container ports were published.
Every owned unit was stopped; ports 8000, 8001 and 8501 were closed, and the final listener inventory
contained no owned application listener. Environments and evidence remain on disk for inspection.

## Resource observations

Each service was capped at **512 MiB**, zero swap and **0.1 CPU** (`cpu.max=10000 100000`). A separate
observer sampled `/proc` RSS and cgroup memory/CPU counters every 100 ms. RSS high-water values and
kernel `memory.peak` counters supplement the samples. CPU seconds below cover the whole recorded
workload, including UI interactions, error probes and the ten-second post-session idle interval.

| Final candidate process | Readiness, seconds | Peak RSS, MiB | Cgroup memory peak, MiB | CPU seconds / observed wall seconds |
|---|---:|---:|---:|---:|
| API | 22.48 (catalog) | 135.77 | 267.95 | 2.31 / 98.08 |
| Dashboard | 5.43 (health) | 232.29 | 231.05 | 6.55 / 75.41 |
| API fresh-process restart | 6.67 (catalog) | 124.84 | 72.95 | 0.67 / 6.76 |
| Dashboard fresh-process restart | 4.59 (health) | 203.68 | 135.82 | 4.98 / 49.78 |

The first substantive dashboard response arrived about **24.17 seconds** after launch; the
restart's first content took about **13.89 seconds**. Opening monitoring took **31.11 seconds**
initially and **25.69 seconds** after process restart. Valid saved-screen switches took roughly
0.7–4.2 seconds. Ten-second post-session idle CPU use was about 0.13% of one core for the API and
0.33% for the dashboard. All observed cgroups had zero OOM/max/kill events; CPU throttling occurred.

These are small sequential synthetic workloads with one UI session, not capacity, concurrency,
latency-SLO or production estimates. RSS includes shared resident mappings; cgroup charges depend
on page-cache ownership, so the two memory measures need not agree. OS/download caches and host
contention differ across trials. No speed or memory improvement is attributed to the config fix.
Local 512 MiB enforcement approximates Render's documented 512 MB; host CPU hardware, startup
supervision, TLS/proxy/WebSocket behavior and cold-instance provisioning were not reproduced.

## Hosting assessment and next gate

| Option | Assessment | Remaining condition |
|---|---|---|
| Local clean Linux candidate | PASS for this bounded smoke | No cloud or public acceptance follows |
| Two Render Free services | CONDITIONAL | Single-session memory fit was observed, but CPU-limited first use/monitoring is slow. Accept the actual host's cold-start/interaction latency, quotas, request/concurrency budget and restart behavior before release |
| Streamlit Community Cloud + Render | BLOCKED for the unchanged packaging recipe | Community Cloud's actual extra-selection/build and environment-setting behavior is unverified. A clean plain `uv sync --locked --python 3.12.15` without extras installed neither Streamlit nor FastAPI. Establish a reproducible host-compatible locked dashboard-extra setup and the same trusted pin before claiming hybrid portability |

Render currently documents 512 MB/0.1 CPU for Free web services, idle shutdown after 15 minutes,
roughly one-minute platform wake-up and 750 shared workspace service-hours per month.
See [compute plans](https://render.com/docs/compute-plans) and
[Free limitations](https://render.com/docs/free), checked November 7, 2026.
Two continuously running services would consume 1,440 hours in a 30-day month; an approved bounded
window and remaining quota are necessary. The existing deprecated `autoDeploy: false` remains
supported by the [blueprint reference](https://render.com/docs/blueprint-spec); it was not activated.

Community Cloud recognizes `uv.lock` before other dependency files, but that does not establish
which optional extras it selects for this project. See its
[dependency documentation](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies).
No account, host settings, additional requirements list, dependency change or hybrid adaptation was
made. Neither platform's actual account/resource limits or deployment has been tested here.

Prefer the existing two-Render proposal for the next separately authorized staging review, subject
to acceptance of the observed slow CPU-bound interactions. Retain public-content/pin/rights approval,
independent security and human review, host/account/audience/window/quota/spend decisions, and a
rollback/shutdown owner before any publication or deployment. Broader analytical and Phase 13 gates
are unchanged.

## Repeating the local setup

In a new Linux directory containing only a freshly verified candidate, with uv 0.12.23 available:

```sh
uv sync --locked --python 3.12.15 --extra api --extra dashboard
uv pip check
export ROSSMANN_DEMO_PROFILE=controlled_synthetic_demo
export ROSSMANN_DEMO_MANIFEST_SHA256='<independently checked candidate pin>'
```

Run one loopback service per terminal, then stop each with Ctrl+C:

```sh
.venv/bin/python scripts/run_demo.py api
.venv/bin/python scripts/run_demo.py course-dashboard
```

From a third terminal, run `.venv/bin/python scripts/verify_local_demo.py`. Never execute the
blueprint's public bind locally. To reproduce this experiment's quotas, use an existing delegated
user cgroup (`systemd-run --user -p MemoryMax=512M -p MemorySwapMax=0 -p CPUQuota=10%`) around each
explicit loopback command; inspect `memory.peak`, `memory.events` and `cpu.stat` before stopping it.
The retained one-use probe scripts, complete responses' hashes, UI evidence, samples, build logs and
test XML are indexed by the ignored preflight manifest. Do not infer clean startup from health alone.
