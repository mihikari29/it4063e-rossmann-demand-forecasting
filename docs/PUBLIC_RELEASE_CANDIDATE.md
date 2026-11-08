# Public course release candidate (not deployed)

The continuation authorizes preparation and loopback verification only. This document proposes
hosting; it does not accept a host, purchase, public listener, upload or release. The accepted
two-URL/shared-immutable-bundle architecture in ADR-030 remains unchanged.

## Existing Space: withdraw, then replace after approval

The historical static Space presents an API tester whose JavaScript constructs JSON, fixed Healthy
monitoring/p-values, unsupported completion claims and inventory examples disconnected from the
selected saved case. Its synthetic paths do not establish genuine LightGBM inference. A read-only
inspection distinguishes HTML availability from actual API health; no external mutation is made.
The corrected local application uses typed Python services and explicit synthetic provenance.

Recommendation: the owner should first authorize withdrawal or replacement with the generated
offline retirement notice. After separate release approval, publish the reviewed two-service
candidate and replace stale links. Do not relabel the existing static mock as a working backend.
Neither the old remote deployment nor these recommendations transfer content/security permission.

## Proposed free demonstration architecture

Use **two Render Free web services** from one separately reviewed, allowlisted candidate: FastAPI
and Streamlit, each with its own host-issued URL. Streamlit uses Python services directly, not
an HTTP reimplementation of business logic. Both read the same exact synthetic bundle/pin; the
separate monitoring workspace uses the authored calendar fixture and declares that distinction.
No real Rossmann rows, fitted models, protected outcomes, credentials or canonical loader are staged.

Render documents Free web services, idle shutdown after 15 minutes, restart on requests, ephemeral
filesystems, 750 shared workspace instance-hours/month and possible quota suspension/restarts.
This suits a bounded course demonstration, not production or guaranteed availability. Limit the
approved demonstration window (for example five days needs at most 240 running service-hours for
two continuously active services), verify remaining account quotas and approve a zero-spend policy.
Never upgrade, attach payment or increase budget automatically.
Sources checked November 6, 2026: [Free services](https://render.com/docs/free),
[FastAPI hosting](https://render.com/docs/deploy-fastapi).

Hugging Face's current documentation says creating Docker/Gradio compute Spaces requires a paid
plan even though CPU Basic has no hourly compute cost. It is therefore not assumed to be an
unconditionally free replacement. Streamlit Community Cloud is an alternative dashboard host,
but a second host adds separate packaging/account controls. The two-Render-service proposal
keeps one locked startup/configuration pattern. Sources:
[HF requirements](https://huggingface.co/docs/hub/spaces-overview),
[Streamlit deployment](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app).

## Reproducible candidate

```powershell
uv run --locked --extra api --extra dashboard python scripts/prepare_deployment_candidate.py --output-dir artifacts/deployment/course-v1
```

The builder refuses overwrite. A literal source allowlist copies only the required synthetic
service/monitoring code, lock/project configuration and local entrypoints. It authors fresh
controlled fixture bytes, verifies the bundle, writes its explicit pin into a non-secret example
and generated `render.yaml`, and records all copied/generated hashes. It never scans source data,
copies `.git`/credentials, uploads, builds containers or starts a listener. Build only from a
reviewed trusted checkout; hashes establish consistency, not authorization or hostile-host safety.

The source allowlist also copies the reviewed Streamlit configuration unchanged, including
redacted errors, disabled file watching and loopback defaults. The generated blueprint contains
two Free services with auto-deploy disabled, Python 3.12.15,
uv 0.12.23, locked api/dashboard extras and single-worker/concurrency-bounded API startup.
The cloud start commands use host binding and `$PORT` only as reviewed configuration; never run
them locally before release approval. Use the [loopback launcher](LOCAL_DEMO_DEPLOYMENT.md) locally:

```powershell
uv run --locked --extra api python scripts/run_demo.py api
uv run --locked --extra dashboard python scripts/run_demo.py course-dashboard
```

Set `ROSSMANN_DEMO_PROFILE=controlled_synthetic_demo` and the independently reviewed
`ROSSMANN_DEMO_MANIFEST_SHA256` in host environment configuration. These are non-secret fixture
settings, not evidence of release approval. No service credential is required. Keep any future
host-account tokens in the owner's account/secret store; never in code, logs or a public bundle.

## Verification, recovery and exact release gates

- API `/health` establishes process liveness; `/api/v1/catalog` establishes bundle/readiness and
  view availability. Use catalog for the proposed API host health check.
- Streamlit `/_stcore/health` is liveness only. Verify the actual saved-service screens, synthetic
  banner/pin and separate monitoring controls; a 200 alone does not prove artifact availability.
- Run [the HTTP probe](../scripts/verify_local_demo.py), valid forecast/uncertainty/inventory
  requests, invalid-query/duplicate tests and missing-artifact 503 checks. Stop local processes.
- Treat cold starts, idle restarts and quota shutdown as unavailable states, never Healthy or zero
  forecasts. Rebuilds must ship the same reviewed fixture bytes/pin; no startup regeneration or
  mutable latest pointer. Monitoring is synthetic descriptive evidence, not continuous production.
- Roll back both services together to one previously reviewed candidate manifest and its exact pin.
  If either service cannot be verified, suspend both, display the retirement notice if authorized,
  and investigate without falling back to canonical data. Retain prior immutable candidates locally.
- Before public action, obtain Milestone B/human visual acceptance, exact content/rights/provenance
  and pin approval, independent security review, host/account/audience/window decision, measured
  Linux memory/CPU/build/request limits, quota/spend budget, rollback/shutdown owner and specific
  owner release authorization. A full local Windows smoke is not Linux/cloud verification.
- Then separately authorize source publication/host creation/deployment, run external HTTP/browser
  checks for both host-issued URLs and all failure/provenance states, and record the real URLs.
  At the approved window's end, suspend/remove the services and verify shutdown externally.

The [Linux preflight](LINUX_DEPLOYMENT_PREFLIGHT.md) records actual isolated WSL2 builds,
loopback HTTP/WebSocket/restart checks and constrained resource observations. Docker's Linux
daemon remained unavailable; no container build occurred. Two-Render hosting remains conditional
on host-specific resource/latency and release acceptance; unchanged hybrid packaging is blocked
pending a verified locked-extras setup. No public URL or host acceptance is established.
