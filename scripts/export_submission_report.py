"""Export the evidence-based report source to PDF and render every page for visual QA."""

from __future__ import annotations

import argparse
import hashlib
import html
import importlib.metadata
import json
import platform
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path


def main() -> None:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True, help="new local directory")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    source = root / "reports/submission_report.md"
    args.output_dir.mkdir(parents=True, exist_ok=False)
    output = args.output_dir / "submission_report.pdf"
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            "ReportBody",
            fontName="Helvetica",
            fontSize=10.5,
            leading=15,
            spaceAfter=8,
            alignment=TA_LEFT,
        )
    )
    styles.add(
        ParagraphStyle(
            "ReportTitle",
            fontName="Helvetica-Bold",
            fontSize=23,
            leading=28,
            spaceAfter=18,
            textColor=colors.HexColor("#17324d"),
        )
    )
    styles.add(
        ParagraphStyle(
            "ReportSection",
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=19,
            spaceBefore=14,
            spaceAfter=8,
            keepWithNext=True,
            textColor=colors.HexColor("#17324d"),
        )
    )
    styles.add(ParagraphStyle("ReportCell", fontName="Helvetica", fontSize=9, leading=12))
    styles.add(
        ParagraphStyle(
            "ReportReference", fontName="Helvetica", fontSize=9.5, leading=13, spaceAfter=5
        )
    )

    def inline(text: str) -> str:
        text = html.escape(text.replace("`", ""))
        return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)

    body = []
    paragraph = []
    table_rows = []

    def flush() -> None:
        if paragraph:
            text = " ".join(paragraph)
            style = (
                styles["ReportReference"] if re.match(r"\[\d+\]", text) else styles["ReportBody"]
            )
            body.append(Paragraph(inline(text), style))
            paragraph.clear()
        if table_rows:
            cells = [
                [Paragraph(inline(value), styles["ReportCell"]) for value in row]
                for row in table_rows
            ]
            table = Table(
                cells,
                colWidths=[52 * mm, 28 * mm, 30 * mm, 25 * mm, 27 * mm],
                repeatRows=1,
                hAlign="LEFT",
            )
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e4edf5")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                        ("TOPPADDING", (0, 0), (-1, -1), 7),
                        ("LINEBELOW", (0, 0), (-1, 0), 0.8, colors.HexColor("#17324d")),
                        ("LINEBELOW", (0, 1), (-1, -1), 0.3, colors.lightgrey),
                    ]
                )
            )
            body.extend([table, Spacer(1, 10)])
            table_rows.clear()

    for line in source.read_text(encoding="utf-8").splitlines():
        if line.startswith("|"):
            if not re.fullmatch(r"[| :\-]+", line):
                table_rows.append([cell.strip() for cell in line.strip("|").split("|")])
        elif line.startswith("# ") or line.startswith("## "):
            flush()
            style = styles["ReportTitle"] if line.startswith("# ") else styles["ReportSection"]
            body.append(Paragraph(inline(line.lstrip("# ")), style))
        elif not line.strip():
            flush()
        else:
            paragraph.append(line)
    flush()

    def footer(canvas, document):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#475569"))
        canvas.drawString(24 * mm, 15 * mm, "IT4063E | Submission draft | Development evidence")
        canvas.drawRightString(A4[0] - 24 * mm, 15 * mm, str(document.page))
        canvas.restoreState()

    document = SimpleDocTemplate(
        str(output),
        pagesize=A4,
        rightMargin=24 * mm,
        leftMargin=24 * mm,
        topMargin=22 * mm,
        bottomMargin=24 * mm,
        title="Rossmann Sales Forecasting - IT4063E submission draft",
        author="IT4063E project team; AI-assisted draft",
    )
    document.build(body, onFirstPage=footer, onLaterPages=footer)
    import pypdfium2 as pdfium

    with pdfium.PdfDocument(output) as pdf:
        pages = len(pdf)
        extracted = []
        for index, page in enumerate(pdf):
            textpage = page.get_textpage()
            try:
                extracted.append(textpage.get_text_range())
            finally:
                textpage.close()
            page.render(scale=1.3).to_pil().save(args.output_dir / f"page-{index + 1:02}.png")
        if pages < 3 or "Conclusions and recommendations" not in "\n".join(extracted):
            raise ValueError("PDF export is incomplete.")

    def sha(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    manifest = {
        "generated_at": datetime.now(UTC).isoformat(),
        "command": sys.argv,
        "configuration": {"source": "reports/submission_report.md", "pages": pages, "format": "A4"},
        "seed": None,
        "python": platform.python_version(),
        "packages": {name: importlib.metadata.version(name) for name in ("reportlab", "pypdfium2")},
        "code_revision": subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
        ).stdout.strip(),
        "worktree_dirty": bool(
            subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout
        ),
        "lock_sha256": sha(root / "uv.lock"),
        "source_sha256": {"report": sha(source), "exporter": sha(Path(__file__))},
        "output_sha256": {path.name: sha(path) for path in sorted(args.output_dir.iterdir())},
        "limitations": "Transcribed reviewed development documentation; no analytical rerun. "
        "Human academic acceptance and final evidence remain pending.",
    }
    (args.output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Exported {pages} pages to {output}; page PNGs require visual inspection.")


if __name__ == "__main__":
    main()
