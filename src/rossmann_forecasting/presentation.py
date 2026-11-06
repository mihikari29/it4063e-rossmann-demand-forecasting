"""Editable 15-slide academic export from the reviewed Markdown source."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import platform
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass(frozen=True)
class SlideSource:
    title: str
    body: tuple[str, ...]
    notes: str


def read_slide_source(source: str) -> tuple[dict[str, str], tuple[SlideSource, ...]]:
    """Read this repository's small, explicit Markdown/notes format without executing it."""
    metadata_text, content = source.removeprefix("---\n").split("\n---\n", 1)
    metadata = dict(line.split(": ", 1) for line in metadata_text.splitlines() if ": " in line)
    slides = []
    for section in re.split(r"(?m)^# ", content)[1:]:
        title, remainder = section.split("\n", 1)
        body, note_text = remainder.split("::: notes", 1)
        notes, trailing = note_text.split(":::", 1)
        if trailing.strip():
            raise ValueError("Unexpected content after speaker notes.")
        slides.append(
            SlideSource(
                title.strip(),
                tuple(line.strip() for line in body.splitlines() if line.strip()),
                notes.strip(),
            )
        )
    if len(slides) != 14 or any(not slide.notes for slide in slides):
        raise ValueError("The source must contain 14 content slides with notes, plus the title.")
    return metadata, tuple(slides)


def _table_values(slide: SlideSource) -> tuple[list[str], list[float]]:
    rows = [
        line for line in slide.body if line.startswith("|") and not re.fullmatch(r"[| :\-]+", line)
    ]
    labels, values = [], []
    for row in rows[1:]:
        label, number = [part.strip() for part in row.strip("|").split("|")]
        labels.append(label)
        values.append(float(number.replace(" million", "")))
    if len(values) not in (2, 3):
        raise ValueError("Expected the reviewed two/three-row evidence table.")
    return labels, values


def export_presentation(source: Path, output: Path) -> None:
    """Create an editable deck; native chart values come directly from the Markdown tables."""
    from pptx import Presentation
    from pptx.chart.data import CategoryChartData
    from pptx.dml.color import RGBColor
    from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION
    from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
    from pptx.util import Inches, Pt

    metadata, sources = read_slide_source(source.read_text(encoding="utf-8"))
    if output.exists():
        raise FileExistsError("Presentation output already exists.")
    output.parent.mkdir(parents=True, exist_ok=True)
    deck = Presentation()
    deck.slide_width, deck.slide_height = Inches(13.333333), Inches(7.5)
    navy, teal, grey = (
        RGBColor.from_string("17324D"),
        RGBColor.from_string("087F8C"),
        RGBColor.from_string("475569"),
    )

    def text(slide, value, x, y, w, h, size=22, bold=False, color=navy):
        shape = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        frame = shape.text_frame
        frame.word_wrap = True
        frame.margin_left = frame.margin_right = 0
        frame.margin_top = frame.margin_bottom = 0
        for index, line in enumerate(value.split("\n")):
            paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
            paragraph.text = line
            paragraph.font.name, paragraph.font.size = "Arial", Pt(size)
            paragraph.font.bold, paragraph.font.color.rgb = bold, color
            paragraph.space_after = Pt(15)
        return shape

    def base(title, number):
        slide = deck.slides.add_slide(deck.slide_layouts[6])
        text(slide, title, 0.65, 0.5, 12, 0.85, 32, True)
        text(slide, f"IT4063E | {number:02d} / 15", 0.65, 7.04, 12, 0.22, 10, color=grey)
        return slide

    def bullets(slide, lines, y=1.7, size=23):
        cleaned = [line.removeprefix("- ") for line in lines if not line.startswith("|")]
        text(slide, "\n".join(cleaned), 0.8, y, 11.7, 5.05 if y < 2 else 4.3, size)

    def node(slide, label, x, y, w=2.28, h=0.9):
        box = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h)
        )
        box.fill.solid()
        box.fill.fore_color.rgb = RGBColor.from_string("E9F2F4")
        box.line.color.rgb = teal
        frame = box.text_frame
        frame.word_wrap = True
        paragraph = frame.paragraphs[0]
        paragraph.text = label
        paragraph.font.name, paragraph.font.size = "Arial", Pt(19)
        paragraph.font.color.rgb = navy
        return box

    def arrow(slide, x1, y1, x2, y2):
        connector = slide.shapes.add_connector(
            MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2)
        )
        connector.line.color.rgb, connector.line.width = teal, Pt(2)
        # A native chevron makes flow direction editable without relying on private OOXML APIs.
        chevron = slide.shapes.add_shape(
            MSO_SHAPE.CHEVRON, Inches(x2 - 0.1), Inches(y2 - 0.09), Inches(0.16), Inches(0.18)
        )
        chevron.fill.solid()
        chevron.fill.fore_color.rgb = teal
        chevron.line.fill.background()

    cover = base("", 1)
    text(cover, "Rossmann Sales\nForecasting", 0.8, 1.25, 11.5, 1.8, 44, True)
    text(cover, metadata["subtitle"], 0.8, 3.45, 11.5, 0.7, 28, color=teal)
    text(
        cover,
        "IT4063E - Introduction to Business Analytics\n" + metadata["date"],
        0.8,
        4.55,
        11.5,
        1.1,
        20,
        color=grey,
    )
    text(
        cover,
        "AI-assisted draft | Team review and academic acceptance pending",
        0.8,
        6.35,
        11.5,
        0.35,
        15,
        color=grey,
    )
    cover.notes_slide.notes_text_frame.text = (
        "Source: reports/presentation.md; docs/PROPOSAL.md. "
        + metadata["author"]
        + ". Team members must verify, understand and accept AI-assisted contributions. "
        "No final evaluation or public release is claimed."
    )

    for number, item in enumerate(sources, 2):
        slide = base(item.title, number)
        slide.notes_slide.notes_text_frame.text = item.notes
        source_line = next(
            (line for line in item.notes.splitlines() if line.startswith(("Source:", "Sources:"))),
            "Source: reports/presentation.md",
        )
        source_line = re.split(r"\.(?=\s[A-Z])", source_line, maxsplit=1)[0]
        text(slide, source_line[:165], 0.8, 6.65, 11.7, 0.25, 10, color=grey)
        if item.title in ("Chronological model comparison", "Inventory simulation findings"):
            labels, values = _table_values(item)
            chart_data = CategoryChartData()
            chart_data.categories = labels
            chart_data.add_series(
                "Development MAE" if len(values) == 3 else "Simulated cost proxy (millions)", values
            )
            chart = slide.shapes.add_chart(
                XL_CHART_TYPE.BAR_CLUSTERED,
                Inches(0.8),
                Inches(1.65),
                Inches(11.6),
                Inches(3.65),
                chart_data,
            ).chart
            chart.has_legend = False
            chart.font.name, chart.font.size = "Arial", Pt(17)
            chart.category_axis.tick_labels.font.size = Pt(19)
            chart.value_axis.minimum_scale = 0
            chart.value_axis.maximum_scale = 1900 if len(values) == 3 else 130
            chart.plots[0].has_data_labels = True
            chart.plots[0].data_labels.position = XL_LABEL_POSITION.OUTSIDE_END
            chart.plots[0].data_labels.number_format = "0.00" if len(values) == 3 else "0.000"
            chart.plots[0].data_labels.font.size = Pt(18)
            chart.series[0].format.fill.solid()
            chart.series[0].format.fill.fore_color.rgb = teal
            caption = [line for line in item.body if not line.startswith("|")]
            text(slide, "\n".join(caption), 0.8, 5.55, 11.7, 0.85, 20)
        elif item.title == "Pipeline architecture":
            labels = [
                "Validate and\nprepare data",
                "Origin-safe\n29 predictors",
                "Chronological\nH14 forecasts",
                "Frozen daily /\nprefix uncertainty",
                "Simulated\ninventory policies",
            ]
            for index, label in enumerate(labels):
                x = 0.65 + index * 2.55
                node(slide, label, x, 2.1, h=1.2)
                if index < 4:
                    arrow(slide, x + 2.28, 2.7, x + 2.48, 2.7)
            node(slide, "Saved artifacts", 2, 4.15, 2.7)
            node(slide, "Read-only API / UI", 5.35, 4.15, 2.7)
            node(slide, "Descriptive monitoring", 8.7, 4.15, 3.3)
            arrow(slide, 4.7, 4.6, 5.25, 4.6)
            arrow(slide, 8.05, 4.6, 8.6, 4.6)
            text(
                slide,
                "Actual history stops at origin; synthetic operating assumptions remain explicit",
                0.8,
                5.65,
                11.7,
                0.65,
                21,
            )
        elif item.title == "Corrected monitoring":
            for index, label in enumerate(
                ("Issued forecasts", "Available labels", "Validated pairs", "Descriptive summaries")
            ):
                x = 0.8 + index * 3.15
                node(slide, label, x, 1.65, 2.75)
                if index < 3:
                    arrow(slide, x + 2.75, 2.1, x + 3.02, 2.1)
            bullets(slide, [line for line in item.body if line.startswith("- ")], y=3.1, size=21)
        else:
            bullets(slide, item.body)
    if len(deck.slides) != 15:
        raise ValueError("Expected exactly fifteen slides.")
    deck.core_properties.author = "IT4063E project team; AI-assisted draft"
    deck.core_properties.title = metadata["title"]
    deck.save(output)


def write_presentation(output_dir: Path, root: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=False)
    source, output = root / "reports/presentation.md", output_dir / "rossmann_presentation.pptx"
    export_presentation(source, output)

    def sha(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    manifest = {
        "generated_at": datetime.now(UTC).isoformat(),
        "command": sys.argv,
        "configuration": {
            "source": "reports/presentation.md",
            "slides": 15,
            "size": "16:9",
            "font": "Arial",
        },
        "seed": None,
        "python": platform.python_version(),
        "packages": {
            name: importlib.metadata.version(name) for name in ("python-pptx", "lxml", "xlsxwriter")
        },
        "code_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True
        ).strip(),
        "worktree_dirty": bool(
            subprocess.check_output(["git", "status", "--porcelain"], cwd=root, text=True)
        ),
        "lock_sha256": sha(root / "uv.lock"),
        "source_sha256": {"markdown": sha(source), "exporter": sha(Path(__file__))},
        "output_sha256": {output.name: sha(output)},
        "evidence_kind": "academic_draft_transcribed_reviewed_development_records",
        "limitations": "No new analytical run, final evaluation, human acceptance or release.",
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return output
