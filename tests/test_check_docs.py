"""Local Markdown checker fixtures; no Rossmann data or network access."""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
from pathlib import Path

import pytest

_CHECKER_PATH = Path(__file__).resolve().parents[1] / "scripts" / "check_docs.py"
_SPEC = importlib.util.spec_from_file_location("check_docs", _CHECKER_PATH)
assert _SPEC is not None and _SPEC.loader is not None
checker = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(checker)


def test_local_reference_directory_unicode_and_duplicate_anchors(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "guide.md").write_text(
        "# Hello, World!\n\n# Hello, World!\n\n# Café\n\n# Café\n", encoding="utf-8"
    )
    (tmp_path / "README.md").write_text(
        "[Heading](guide.md#hello-world)\n"
        "[Duplicate](guide.md#hello-world-1)\n"
        "[Unicode](guide.md#caf%C3%A9)\n"
        "[Unicode duplicate](guide.md#caf%C3%A9-1)\n"
        "[Directory](docs/)\n"
        "[Reference][guide]\n\n"
        '[guide]: <guide.md#hello-world> "Guide title"\n',
        encoding="utf-8",
    )

    count, checked, errors = checker.check_markdown(tmp_path)

    assert (count, checked, errors) == (2, 6, [])


def test_missing_file_and_anchor_report_source_locations(tmp_path: Path) -> None:
    (tmp_path / "guide.md").write_text("# Existing\n", encoding="utf-8")
    (tmp_path / "README.md").write_text(
        "[File](missing.md)\n[Anchor](guide.md#missing)\n", encoding="utf-8"
    )

    count, checked, errors = checker.check_markdown(tmp_path)

    assert (count, checked) == (2, 2)
    assert errors == [
        "README.md:1: missing local destination 'missing.md'",
        "README.md:2: missing Markdown anchor 'guide.md#missing'",
    ]


def test_code_comments_and_external_links_do_not_require_local_targets(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text(
        "`[Inline example](missing.md)`\n\n"
        "```markdown\n[Example](missing.md#absent)\n```\n\n"
        "~~~markdown\n[Another example](missing.md)\n~~~\n\n"
        "<!-- [Comment](missing.md) -->\n"
        "[External](https://example.invalid/missing)\n"
        "[Email](mailto:review@example.invalid)\n",
        encoding="utf-8",
    )

    assert checker.check_markdown(tmp_path) == (1, 0, [])


def test_git_enumeration_includes_tracked_and_new_docs_but_excludes_ignored(tmp_path: Path) -> None:
    git = shutil.which("git")
    if git is None:
        pytest.skip("Git is required to exercise repository document enumeration.")
    subprocess.run([git, "init", "--quiet", str(tmp_path)], check=True, capture_output=True)
    (tmp_path / ".gitignore").write_text("generated/\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("# Tracked\n", encoding="utf-8")
    subprocess.run(
        [git, "-C", str(tmp_path), "add", ".gitignore", "README.md"],
        check=True,
        capture_output=True,
    )
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "new.md").write_text("# New\n", encoding="utf-8")
    (tmp_path / "generated").mkdir()
    (tmp_path / "generated" / "ignored.md").write_text("# Ignored\n", encoding="utf-8")

    names = {path.relative_to(tmp_path).as_posix() for path in checker.markdown_files(tmp_path)}

    assert names == {"README.md", "docs/new.md"}
