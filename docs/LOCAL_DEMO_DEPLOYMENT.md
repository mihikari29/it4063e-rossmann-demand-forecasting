# Two-service local deployment candidate

This candidate uses the existing verified synthetic FastAPI and Streamlit services. It is a
local engineering demonstration, not authorization to publish a bundle, start a public listener
or deploy. Both use the same immutable controlled-synthetic bundle and exact manifest pin, with
no fallback to canonical Rossmann data. [Milestone C](../plans/active/public-course-demo.md)
retains its content/rights/security/resource/owner gates.

## Reproduce locally

Use Python 3.12 or 3.14 and uv 0.12.23. Dependency versions come from `uv.lock`, with no second
requirements file. In a clean, tracked-files-only checkout (without real datasets/artifacts):

```powershell
uv sync --locked --extra dev --extra api --extra dashboard --python 3.14
uv run --locked python scripts/build_public_demo_bundle.py build --output-dir artifacts/public_demo/rossmann-course-demo-synthetic-v1
```

Review the generated content and obtain the manifest SHA-256 through a trusted independent
verification process. A locally computed digest is sufficient for a fixture smoke check but
does not establish release rights or owner acceptance. Do not overwrite an existing release.
Set the same explicit configuration in two terminals:

```powershell
$env:ROSSMANN_DEMO_PROFILE = "controlled_synthetic_demo"
$env:ROSSMANN_DEMO_MANIFEST_SHA256 = "<reviewed lowercase 64-character SHA-256>"
```

Run one command per terminal:

```powershell
uv run --locked --extra api python scripts/run_demo.py api
uv run --locked --extra dashboard python scripts/run_demo.py dashboard
```

API: `http://127.0.0.1:8000`; dashboard: `http://127.0.0.1:8501`. The launcher fixes loopback
bindings, disables static-file serving and usage telemetry, and preserves CORS/XSRF protection.
The dashboard uses direct Python services. There is no JavaScript reimplementation or mock REST
tester. Saved Store/origin/case/interval selections affect the matching service response; missing
intervals/forecasts remain unavailable. Lead time/service level are saved-case definitions, not
interactive controls that pretend to refit uncertainty or simulate a new policy.

```powershell
uv run --locked --extra api python scripts/verify_local_demo.py
Invoke-RestMethod 'http://127.0.0.1:8000/api/v1/forecasts?store_id=101&forecast_origin=2015-06-19'
```

`/health` is liveness only. `/api/v1/catalog` returns verified bundle readiness and per-view
availability. The probe makes genuine HTTP requests with five-second timeouts and reports
connection, HTTP, timeout and invalid-response states; readiness is never inferred from a
hardcoded health example. Query errors return 422, absent/invalid release returns 503, and
unexpected failures are sanitized. Unsupported Store/date/case inputs do not silently return zero.
Stop both terminal processes after use. No daemon, firewall rule, forwarding or cloud resource
is created. Keep environment-specific secrets in process/host configuration; none is required
for this loopback fixture and no token is read by the retired HF builder.

For the course entrypoint with an additional descriptive synthetic monitoring workspace, use
`uv run --locked --extra dashboard python scripts/run_demo.py course-dashboard` instead of the
dashboard command. The saved five-screen service profile is unchanged. The monitoring workspace
uses a separately authored fixture, labels its calculation time/windows and evidence state, and
supports Store and trailing-calendar-window selections. It is not live production monitoring or
genuine LightGBM inference. [Cloud candidate preparation](PUBLIC_RELEASE_CANDIDATE.md) remains
separate from all public-release operations.

## Existing external static Space

The owner's historical Space is external evidence, not an approved release of this candidate.
A read-only check on November 6, 2026 returned HTTP 200 from its metadata API with `sdk=static`
and `RUNNING`; the static host's `/health` returned 404. Its root returned HTML/200 and still
contained the mock `executeApiCall` tester and fixed Healthy badge, without a `fetch(` call.
This establishes the stale static demonstration, not FastAPI service availability. No remote
content was changed; withdrawal/replacement requires separately authorized owner action.
The old builder now writes only
an offline retirement notice and has no upload/deployment dependency or operation.
Public metadata source: [Space metadata](https://huggingface.co/api/spaces/hieu-nguyen2208/rossmann-sales-forecasting).

## External-release acceptance checklist (pending)

- Independent named corrective review and Milestone B closeout; human visual acceptance.
- Review exact bundle bytes/pin, rights/provenance, public content and explicit synthetic labels.
- Independent security review: artifact isolation, secret exclusion, bounded queries, access
  controls/rate limits, sanitized failures and no directory or source exposure.
- Select two separately reachable read-only API/dashboard endpoints with approved hosting,
  audience/window, dependency lock, memory/CPU/request limits and measured resource budget.
- Specify host environment configuration, restart/readiness, rollback to the exact prior bundle,
  shutdown owner/window and removal verification. Any host binding change needs release approval.
- Obtain owner release approval, then separately execute deployment and external HTTP/browser
  checks of both URLs, availability/error behavior and synthetic provenance. Record actual URLs
  only after those checks. Local tests cannot establish public delivery.
