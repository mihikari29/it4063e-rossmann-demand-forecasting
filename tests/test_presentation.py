"""Editable evidence must retain the exact reviewed source values and fifteen-slide scope."""

from pathlib import Path

import pytest

from rossmann_forecasting.presentation import export_presentation, read_slide_source


def test_deck_preserves_editable_chart_values_notes_and_geometry(tmp_path):
    from pptx import Presentation

    source = Path("reports/presentation.md")
    metadata, slides = read_slide_source(source.read_text(encoding="utf-8"))
    assert metadata["title"] == "Rossmann Sales Forecasting"
    assert len(slides) == 14
    output = tmp_path / "presentation.pptx"
    export_presentation(source, output)
    deck = Presentation(output)
    assert len(deck.slides) == 15
    charts = [shape.chart for slide in deck.slides for shape in slide.shapes if shape.has_chart]
    assert len(charts) == 2
    assert list(charts[0].series[0].values) == [1681.2703, 1281.7446, 871.0612]
    assert list(charts[1].series[0].values) == [90.787, 113.929]
    for slide in deck.slides:
        assert "Source" in slide.notes_slide.notes_text_frame.text
        for shape in slide.shapes:
            assert 0 <= shape.left and 0 <= shape.top
            assert shape.left + shape.width <= deck.slide_width
            assert shape.top + shape.height <= deck.slide_height
    with pytest.raises(FileExistsError):
        export_presentation(source, output)


def test_missing_slide_or_notes_fails_explicitly():
    source = Path("reports/presentation.md").read_text(encoding="utf-8")
    with pytest.raises(ValueError):
        read_slide_source(source.replace("# Conclusions", "Conclusions"))
