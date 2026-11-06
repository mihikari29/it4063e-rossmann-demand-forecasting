"""Metadata gates reject redirected inputs before callers can read or hash content."""

from types import SimpleNamespace

import pytest

from rossmann_forecasting.artifact_paths import require_plain_file


def test_plain_source_and_outside_root(tmp_path):
    selected = tmp_path / "source.txt"
    selected.write_text("fixture")
    require_plain_file(selected, tmp_path)
    with pytest.raises(ValueError, match="intended root"):
        require_plain_file(tmp_path.parent / "outside.txt", tmp_path)


def test_ancestor_reparse_rejected_with_metadata_only(monkeypatch, tmp_path):
    directory = tmp_path / "source"
    directory.mkdir()
    selected = directory / "module.py"
    selected.write_text("fixture")
    path_type = type(directory)
    original = path_type.lstat

    def lstat(path):
        info = original(path)
        return (
            SimpleNamespace(st_mode=info.st_mode, st_file_attributes=0x400)
            if path == directory
            else info
        )

    monkeypatch.setattr(path_type, "lstat", lstat)
    with pytest.raises(ValueError, match="Aliased"):
        require_plain_file(selected, tmp_path)
