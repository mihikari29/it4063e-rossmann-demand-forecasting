# Academic deliverables

[Report source](submission_report.md) is an English submission draft based on reviewed repository
evidence. [Presentation source](presentation.md) contains a title slide plus 14 content slides,
editable tables and source/explanation notes. The source files explicitly retain pending final
evidence, public release and human academic acceptance. Neither is an instructor-approved final.

Export the report with the optional locked reporting tools:

```powershell
uv run --locked --extra reporting python scripts/export_submission_report.py --output-dir reports/generated/submission/report-v1
```

The exporter writes a PDF, rendered page PNGs and a provenance manifest; it refuses overwrite.
Inspect every page PNG after changing the source. Generated binaries remain ignored.

The continuation explicitly authorizes an available alternative to the unavailable presentation
runtime. The locked `python-pptx` exporter creates an actual editable 15-slide deck directly from
the authoritative Markdown, including native model/inventory charts, pipeline shapes and notes:

```powershell
uv run --locked --extra reporting python scripts/export_presentation.py --output-dir reports/generated/submission/presentation-v3
./scripts/render_presentation.ps1 -PresentationPath reports/generated/submission/presentation-v3/rossmann_presentation.pptx -OutputDirectory reports/generated/submission/presentation-v3-render
```

Use unused directories. Installed Microsoft PowerPoint renders the macro-free deck without a
visible document window, writing a PDF, one PNG per slide and a separate provenance manifest.
Inspect every slide for overflow/legibility and verify native chart values and notes. No Pandoc
or unavailable runtime is required. The original report PDF need not be regenerated when its
Markdown and output hashes still match; verification preserves its historical manifest.

The [submission staging command](../scripts/stage_submission_package.py) copies only named local
report/PPTX/render/monitoring/notebook outputs, checks their manifests and cross-generation/source
bindings before copying, and writes an evidence index, checksum manifest and three-state checklist.
It refuses outside/aliased inputs and overwrite. Overall final submission remains BLOCKED where
mandatory public/analytical/human gates remain. Generated binaries are not committed to Git.

Team members must inspect, understand and accept all AI-assisted contributions, verify course
policy/disclosure, rehearse the methods and retain the adverse inventory result. Final academic
acceptance and public delivery remain pending in [submission readiness](../docs/SUBMISSION_READINESS.md).
