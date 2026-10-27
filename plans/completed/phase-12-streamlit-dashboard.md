# Local Dashboard

**Complete.**

The five-screen dashboard is complete: Overview & Evidence, Historical Sales, Forecast Explorer, Model Comparison and Inventory Comparison. It displays saved evidence through `ApplicationServices`, with bounded controls, raw/operational distinctions, daily/cumulative uncertainty, explicit unavailable states and simulated monetary costs. `dashboard_presenters.py` holds presentation transformations; `streamlit_app.py` remains the supported entrypoint. It never reads the inventory ledger, trains/infers, runs a simulation or evaluates the protected period. [Local application usage](../../docs/LOCAL_APPLICATION.md) owns runtime/security/recovery. User-attested human visual review is accepted; automated checks are distinct evidence. Future public release remains separately gated.

[Current results and limitations](../../docs/PROGRESS.md)
