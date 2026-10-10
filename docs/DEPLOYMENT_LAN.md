# Phase 12 dashboard localhost deployment runbook

The filename is retained for existing links. This runbook now covers the approved localhost-only
demonstration; LAN instructions from the earlier design have been removed from the operational
procedure. The private-LAN proposal remains historical design in the
[completed Phase 12 plan](../plans/completed/phase-12-streamlit-dashboard.md)
and is superseded by ADR-024 in [DECISIONS](DECISIONS.md).

## Current deployment target

Use the dashboard for local development, analysis and live demonstration on the user's Windows
computer. The sole approved browser URL is `http://127.0.0.1:8501`. LAN access, Windows network
profile changes, firewall rules, port forwarding, tunnels, cloud deployment and public hosting are
outside scope. No LAN test has been performed or is required by the current decision.

The reviewed host is Windows 11 Home Single Language (build 10.0.26300), AMD Ryzen 5 5600H (6
cores / 12 threads), with 16 GiB installed memory. The locked runtime used Python 3.14.5, uv
0.12.23 and Streamlit 1.65.0. Host-specific network addresses are not recorded.

## Install and start locally

From the repository root, install the committed lock and launch the existing Streamlit entry point:

```powershell
uv sync --locked --extra dev --extra api --extra dashboard --python 3.14
uv run --locked --extra dashboard streamlit run streamlit_app.py
```

Open `http://127.0.0.1:8501`. The committed `.streamlit/config.toml` sets:

| Setting | Required value | Purpose |
|---|---|---|
| `server.address` | `127.0.0.1` | Loopback-only listener |
| `server.enableStaticServing` | `false` | Do not serve repository static files |
| `server.enableCORS` | `true` | Keep Streamlit CORS protection enabled |
| `server.enableXsrfProtection` | `true` | Keep Streamlit XSRF protection enabled |

Detailed error pages remain disabled, the file watcher stays off, and usage-stat collection is
disabled. Do not override the configured address, port, or security options. Confirm the local URL
shown by Streamlit. Stop the dashboard with **Ctrl+C** in its terminal. If port 8501 is occupied,
inspect the listener and stop only a process you own; do not change the bind target or expose another
interface.

## Accepted local evidence and failure recovery

The dashboard calls the existing `ApplicationServices` and verified `_ArtifactReader` directly; it
does not call the FastAPI adapter, train or infer, simulate inventory, regenerate data, or cache
service results. Its required local runtime closure is the accepted Phase 7 manifest, selected
forecasts and model comparison; Phase 8 manifest and daily/cumulative uncertainty; Phase 9 manifest,
scenario catalog and upstream bindings; Phase 10 manifest, comparison, policy summary and targets;
and the prepared historical source queried only through 2015-07-03. These ignored artifacts are
not included in Git or served as downloads.

Use **Refresh resource status** on Overview after restoring an operator-managed missing file.
Missing resources remain visibly unavailable; a request that requires one shows the fixed,
sanitized error state. Integrity or schema failures are not repaired or bypassed. Restart the local
process after changing its configuration. A clean checkout can run fixture tests but is not a
substitute for this accepted local evidence closure.

The dashboard does not expose file browsing, uploads, source downloads, manifest downloads, paths,
credentials, model binaries or protected outcomes. A benign nonexistent private-resource URL probe
returned only Streamlit's generic app shell and disclosed no source path or directory listing.
Detailed host/browser/performance evidence and service-returned provenance are recorded in
[PROGRESS](PROGRESS.md#phase-12-m4-integration-browser-and-local-performance-2026-10-10).

## Local acceptance and review boundary

Retain the recorded service provenance, full fixture/quality matrix, desktop/mobile browser
interaction, two-session state-isolation evidence, latency/memory measurements and configuration
review. The two browser contexts ran on the same host process; they were not an independent LAN
viewer. No LAN/network/cloud exposure was tested or is required.

The user reported PASS after personally reviewing all five screens in a real local browser at the
approved URL, including layout, interactions and data boundaries. This is user-attested visual
acceptance, not an agent-run manual browser test. The Technical Lead independently accepted M4 on
reviewed head `8b4275a24030f4ceb21b2f3d5f88b2c23016aae1`; PR #32 was squash-merged and Phase 12
was formally closed. The recorded automated Edge checks remain separate evidence and do not replace
the user's visual review. No LAN/network/cloud exposure was tested or is required.
