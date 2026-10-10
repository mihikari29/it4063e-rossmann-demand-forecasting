# Phase 12 dashboard deployment runbook

## Current deployment state

Option A, a private LAN demo on the machine that owns the accepted artifacts, is the selected
strategy. The current M4 session is approved for **localhost only**. The operator identified the
allowed audience as localhost only; the host's active Wi-Fi network is classified Public. The
course accepts a session-only URL and the machine will remain powered, but those facts do not
approve LAN exposure. No LAN listener, Windows Firewall rule, independent viewer test or LAN URL
was created. M4 remains blocked pending host/network and independent-viewer acceptance evidence.

The host is Windows 11 Home Single Language (build 10.0.26300), AMD Ryzen 5 5600H (6 cores / 12
threads), with 16 GiB installed memory. The locked runtime used Python 3.14.5, uv 0.12.23 and
Streamlit 1.65.0. A private IPv4 was inspected locally and is intentionally omitted from tracked
documentation. The local-only browser URL is `http://127.0.0.1:8501`.

## Install and start locally

From the repository root, install the committed lock and launch the existing Streamlit entry point:

```powershell
uv sync --locked --extra dev --extra api --extra dashboard --python 3.14
uv run --locked --extra dashboard streamlit run streamlit_app.py
```

Open `http://127.0.0.1:8501`. `.streamlit/config.toml` fixes the bind to `127.0.0.1`, disables
static serving and the file watcher, keeps CORS and XSRF protection enabled, suppresses detailed
error pages and disables usage-stat collection. These settings were read back from the installed
Streamlit runtime. Do not override the bind address for the current localhost-only approval.

If startup reports a port conflict, inspect the listener and stop only a process you own, or choose
an available local port with `--server.port <LOCAL_PORT>` while retaining `--server.address
127.0.0.1`. Confirm the local URL shown by Streamlit. Do not expose a wildcard listener. Stop the
dashboard with **Ctrl+C** in its terminal. After the demo, close the browser and use the normal
Windows shutdown flow if the host may power off.

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

## Conditional LAN procedure for a later approved session

LAN access requires a separate explicit operator approval naming the host interface, allowed
reviewer IP or subnet and port. Confirm the active network is trusted and uses the Windows **Private**
profile; the current observed profile is Public and does not meet this condition. Confirm the
reviewer device and course requirement, then document the actual session URL outside committed
machine-specific allowlists. No LAN command or firewall rule below was executed for M4.

After those gates are met, bind only to the approved private IPv4, for example in PowerShell:

```powershell
uv run --locked --extra dashboard streamlit run streamlit_app.py --server.address <APPROVED_PRIVATE_IPV4> --server.port 8501 --server.headless true
```

If inbound filtering is required, an operator must approve and run an elevated rule restricted to
the approved local address, port, remote IP/subnet and Private profile:

```powershell
New-NetFirewallRule -DisplayName "Rossmann dashboard M4 demo" -Direction Inbound -Action Allow -Protocol TCP -LocalAddress <APPROVED_PRIVATE_IPV4> -LocalPort 8501 -RemoteAddress <APPROVED_REVIEWER_IP_OR_SUBNET> -Profile Private
```

Rollback that named rule after the session with:

```powershell
Remove-NetFirewallRule -DisplayName "Rossmann dashboard M4 demo"
```

Then stop Streamlit with **Ctrl+C** and verify that the listener has closed before host shutdown.
Do not use a tunnel, port forwarding, public DNS, cloud hosting or a public/wildcard listener. If
the session needs to resume, repeat the host/audience checks and use a newly authorized session URL.

## Review boundary

The real-browser checks, two-session state-isolation result, timing samples, memory measurements,
configuration review, canonical service provenance and automated check matrix are in the linked
PROGRESS checkpoint. A local run or successful CI does not establish independent LAN access or
complete M4 acceptance. The active Phase 12 plan remains open for independent review; Phase 13 and
the protected final holdout remain outside this task.
