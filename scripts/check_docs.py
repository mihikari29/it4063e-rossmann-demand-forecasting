"""Check local Markdown destinations and heading anchors without reading datasets.

Scope: inline links/images and reference-definition destinations outside fenced/inline code and
HTML comments. Check relative files/directories and GitHub-style Markdown heading/explicit HTML
anchors; skip external URLs and fragments in non-Markdown files. This is not a full Markdown
parser or an external-link availability check. Git repositories include tracked and non-ignored
new Markdown; the fallback scan excludes environment and generated-output directories.
"""

from __future__ import annotations

import argparse
import html
import os
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote, urlsplit

_FENCE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")
_INLINE_CODE = re.compile(r"(`+).*?\1")
_DESTINATION = r"(?:<(?P<angle>[^>]+)>|(?P<plain>(?:\\.|[^\s)])+))"
_INLINE_LINK = re.compile(r"!?\[[^\]\n]*\]\(\s*" + _DESTINATION + r"(?:\s+['\"][^\n]*?['\"])?\s*\)")
_REFERENCE = re.compile(r"^\s{0,3}\[[^\]\n]+\]:\s*" + _DESTINATION, re.MULTILINE)
_EXCLUDED_NAMES = {".git", ".venv", "venv", "env", "__pycache__", "node_modules"}
_EXCLUDED_PATHS = {
    "artifacts",
    "outputs",
    "mlruns",
    "data/raw",
    "data/interim",
    "data/processed",
    "data/external",
    "reports/generated",
    "reports/validation",
    "reports/eda",
}


def markdown_files(root: Path) -> list[Path]:
    """Discover repository docs, including non-ignored files added in the current task."""

    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "ls-files",
                "-z",
                "--cached",
                "--others",
                "--exclude-standard",
            ],
            capture_output=True,
            check=False,
        )
    except OSError:
        result = None
    if result is not None and result.returncode == 0:
        names = result.stdout.decode("utf-8").split("\0")
        return sorted(
            {root / name for name in names if Path(name).suffix.lower() == ".md"}, key=str
        )

    files: list[Path] = []
    for directory, children, names in os.walk(root):
        current = Path(directory)
        children[:] = [
            name
            for name in children
            if name not in _EXCLUDED_NAMES
            and (current / name).relative_to(root).as_posix() not in _EXCLUDED_PATHS
        ]
        files.extend(current / name for name in names if Path(name).suffix.lower() == ".md")
    return sorted(files, key=str)


def prose_only(text: str) -> str:
    """Remove code fences/comments while preserving source line numbers."""

    text = re.sub(r"<!--.*?-->", lambda match: "\n" * match[0].count("\n"), text, flags=re.DOTALL)
    lines: list[str] = []
    fence: str | None = None
    for line in text.splitlines(keepends=True):
        match = _FENCE.match(line)
        if fence is None and match:
            fence = match[1]
            lines.append("\n")
        elif fence is not None:
            if match and match[1][0] == fence[0] and len(match[1]) >= len(fence):
                if not line[match.end() :].strip():
                    fence = None
            lines.append("\n")
        else:
            lines.append(line)
    return "".join(lines)


def heading_anchors(text: str) -> set[str]:
    """Recognize common GitHub heading slugs, duplicate headings, and explicit HTML anchors."""

    prose = prose_only(text)
    headings: list[str] = []
    lines = prose.splitlines()
    for index, line in enumerate(lines):
        atx = re.match(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$", line)
        if atx:
            headings.append(atx[1])
        elif index and re.fullmatch(r"\s{0,3}(?:=+|-+)\s*", line) and lines[index - 1].strip():
            headings.append(lines[index - 1].strip())

    anchors = set(re.findall(r"<(?:a|span)\b[^>]*\b(?:id|name)=['\"]([^'\"]+)['\"]", prose))
    occurrences: dict[str, int] = {}
    for heading in headings:
        visible = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", heading)
        visible = html.unescape(re.sub(r"<[^>]*>", "", visible))
        visible = re.sub(r"[^\w\s-]", "", visible.lower().strip())
        slug = re.sub(r"\s", "-", visible)
        count = occurrences.get(slug, 0)
        anchors.add(f"{slug}-{count}" if count else slug)
        occurrences[slug] = count + 1
    return anchors


def check_markdown(root: Path) -> tuple[int, int, list[str]]:
    """Return scanned file/destination counts and actionable local-link errors."""

    files = markdown_files(root)
    errors: list[str] = []
    checked = 0
    anchor_cache: dict[Path, set[str]] = {}
    for source in files:
        if not source.is_file():
            continue
        text = source.read_text(encoding="utf-8")
        prose = _INLINE_CODE.sub("", prose_only(text))
        matches = list(_INLINE_LINK.finditer(prose)) + list(_REFERENCE.finditer(prose))
        for match in matches:
            destination = match["angle"] or match["plain"]
            destination = re.sub(r"\\([\\ ()])", r"\1", destination)
            parsed = urlsplit(destination)
            if parsed.scheme or parsed.netloc:
                continue
            checked += 1
            line = prose.count("\n", 0, match.start()) + 1
            location = f"{source.relative_to(root).as_posix()}:{line}"
            path_text = unquote(parsed.path)
            if not path_text:
                target = source
            elif path_text.startswith("/"):
                target = root / path_text.lstrip("/")
            else:
                target = source.parent / path_text
            target = target.resolve()
            if not target.exists():
                errors.append(f"{location}: missing local destination {destination!r}")
                continue
            if parsed.fragment and target.is_file() and target.suffix.lower() == ".md":
                if target not in anchor_cache:
                    anchor_cache[target] = heading_anchors(target.read_text(encoding="utf-8"))
                if unquote(parsed.fragment) not in anchor_cache[target]:
                    errors.append(f"{location}: missing Markdown anchor {destination!r}")
    return len(files), checked, errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()
    if not root.is_dir():
        parser.error("--root must be an existing directory")
    count, checked, errors = check_markdown(root)
    for error in errors:
        print(error)
    if errors:
        print(f"FAIL: {len(errors)} local-link errors across {count} Markdown files.")
        return 1
    print(f"PASS: {checked} local destinations/anchors across {count} Markdown files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
