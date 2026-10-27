# Read-Only Application Services

**Complete.**

The application layer is complete locally. `app/contracts.py` defines typed requests/results, `app/artifacts.py` verifies pinned allowlisted immutable outputs, and `app/services.py` exposes catalog, bounded Sales history, forecast issuance, uncertainty, model comparison and inventory comparison. Services perform no fitting, forecasting or simulation. FastAPI is a thin HTTP adapter and Streamlit calls services directly. [Local application usage](../../docs/LOCAL_APPLICATION.md) owns startup, supported resources, sanitized failures and recovery. [Release requirements](../../docs/PUBLIC_DEMO_RELEASE_CONTRACT.md) apply separately to the synthetic profile and future publication.

[Current results and limitations](../../docs/PROGRESS.md)
