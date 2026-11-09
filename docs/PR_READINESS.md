# Local integration and proposed Draft PR

Local commits are authorized by the continuation. Push, PR creation, merge and release remain
unauthorized. Git owns commit/file chronology; the ignored release handoff and validation manifests
record the exact tested revision/tree. Historical results in the readiness record are not new runs.

## Proposed title

Correct synthetic demo monitoring and finalize course submission artifacts

## Proposed description

Replace target-derived pseudo-LightGBM monitoring and fabricated static API/UI responses with
chronology-validated development/synthetic label pairing and the existing typed Python services.
Add explicit loopback launch/probe commands, a separate synthetic monitoring workspace, editable
15-slide PPTX export, an allowlisted two-service deployment candidate and checksummed academic
submission staging. Preserve the selected forecasting recipe, accepted uncertainty/inventory
methods and adverse development finding; no real-source/holdout reads or external release occur.

Validation includes a new locked Python 3.12/3.14 fixture matrix, lint/format/links/dependency
checks, actual local HTTP/error/readiness smoke, PowerPoint slide rendering and page-by-page PDF/
slide inspection. Exact results/revision come from the current handoff manifest and must be
copied into the final PR body only after execution. No remote Quality result is claimed locally.
Public API/dashboard release, real scenario/STL/final replay and human academic acceptance remain
separate gates. The package is not labeled overall READY for course submission.

## Commands only after explicit push/PR authorization

Save the final reviewed description with actual test results to an ignored UTF-8 body file, then:

```powershell
git push -u origin feat/course-submission-integration
gh pr create --draft --base main --head feat/course-submission-integration --title "Correct synthetic demo monitoring and finalize course submission artifacts" --body-file <reviewed-body-file>
gh pr checks --watch
```

The Quality workflow runs on `pull_request` and pushes to `main`; pushing this feature branch
alone does not trigger it. Opening the authorized Draft PR triggers the Python 3.12/3.14 matrix
against the actual proposed commit. Review check output and human feedback; never auto-merge.
Do not push/merge main, force-push or change branch protections. Artifact/package generation is
local only and does not authorize uploading its bytes, changing the Space or creating cloud hosts.
