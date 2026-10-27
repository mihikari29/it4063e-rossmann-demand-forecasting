# Local API and Dashboard

Use the canonical read-only applications for development, analysis and live demonstration on the
local computer. They present precomputed development evidence through shared Python services.
Public hosting is a separately gated [future release](../plans/active/public-course-demo.md).

## Install and start

From the repository root, use the locked environment and separate terminals:

```powershell
uv sync --locked --extra dev --extra api --extra dashboard --python 3.14
uv run --locked --extra api python -m uvicorn rossmann_forecasting.app.api:app --host 127.0.0.1 --port 8000
uv run --locked --extra dashboard streamlit run streamlit_app.py
```

Open `http://127.0.0.1:8501`; stop each process with **Ctrl+C**. Keep the API on
`127.0.0.1:8000`. Do not change network profiles, firewall rules, forwarding or listeners to
expose the applications. If a port is occupied, inspect it and stop only a process you own.

The committed [Streamlit configuration](../.streamlit/config.toml) requires loopback binding,
static serving off, CORS and XSRF protection on. Detailed error pages, file watching and usage-stat
collection stay disabled. Restart after configuration changes; do not bypass integrity failures.

## Views and routes

The five dashboard screens show Overview & Evidence, Historical Sales, Forecast Explorer,
Model Comparison and Inventory Comparison. Streamlit calls `ApplicationServices` directly,
without HTTP loopback. It does not train/infer, simulate, regenerate data, cache service results
or access the inventory ledger. No uploads, filesystem browsing, raw/manifest/model downloads,
credentials or protected outcomes are exposed.

| GET route | Required query fields | Optional bounded filters |
|---|---|---|
| `/health` | None | None |
| `/api/v1/catalog` | None | None |
| `/api/v1/history` | `store_id`, `start_date`, `end_date` | None |
| `/api/v1/forecasts` | `store_id`, `forecast_origin` | None |
| `/api/v1/uncertainty` | `store_id`, `forecast_origin`, `fit_id` | None |
| `/api/v1/model-comparison` | None | `candidate_id`, `population`, `scope`, `validation_window`, `horizon`, `store_id`, `metric`, `limit` |
| `/api/v1/inventory` | `case_id` | `store_id` |

Dates use ISO YYYY-MM-DD; use catalog-supported saved origins/Fits/cases. History ends July 3,
2015. The adapters return stable sanitized JSON errors: invalid requests 422, unavailable or
invalid required artifacts 503, unexpected failures 500. Health 200 means liveness, without
establishing artifact integrity, bundle readiness or every analytical view's availability.

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/api/v1/catalog
Invoke-RestMethod "http://127.0.0.1:8000/api/v1/forecasts?store_id=1&forecast_origin=2015-06-19"
Invoke-RestMethod "http://127.0.0.1:8000/api/v1/inventory?case_id=synthetic_base-20150605-r00--reference"
```

## Local evidence requirements and recovery

Canonical artifacts are ignored and absent in a fresh checkout. The reader requires exact pinned
manifests and selected outputs: model-selection forecasts/comparison, uncertainty daily/cumulative
tables, scenario catalog/bindings, inventory targets/policy/comparison summaries, and prepared
history queried only through July 3. [Artifact definitions](../data/README.md) and
[`app/artifacts.py`](../src/rossmann_forecasting/app/artifacts.py) own layout/pins. Do not regenerate
or substitute files merely to make the UI load, or infer access permission from this list.

After an operator restores an approved missing resource, use **Refresh resource status** on
Overview. Missing views remain visibly unavailable and errors stay sanitized. Integrity/schema
failures require reconciliation, without fallback or repair. Fixture tests work without canonical
artifacts and do not establish that this local evidence closure is installed.

Canonical local acceptance included desktop/mobile automated interaction, same-host two-session
state-isolation and security/performance checks, independent review and user-attested human visual
review of all five screens. The same-host contexts were not independent remote viewers.
No LAN/cloud exposure was tested or required; automated UI evidence does not replace human review.

## Controlled synthetic application

`demo_streamlit_app.py` is a separate entrypoint requiring explicit profile and trusted manifest
pin. `app/demo_api.py:create_demo_app` is an explicit factory. Their saved fixture values and
synthetic provenance are distinct from canonical Rossmann evidence. See the
[demo plan](../plans/active/public-course-demo.md) for exact local configuration and pending
independent review/release gates; missing synthetic inputs never fall back to canonical artifacts.
