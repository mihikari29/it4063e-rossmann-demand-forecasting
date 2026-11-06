"""Metadata-only checks before reading trusted local source/generated artifact files."""

import stat
from pathlib import Path


def require_plain_file(path: Path, root: Path) -> None:
    """Reject outside/aliased paths before content access; not a hostile-race security boundary."""
    base, selected = root.absolute(), path.absolute()
    if not selected.is_relative_to(base):
        raise ValueError("File must remain inside the intended root.")
    for component in (selected, *selected.parents):
        info = component.lstat()
        if (
            stat.S_ISLNK(info.st_mode)
            or component.is_junction()
            or getattr(info, "st_file_attributes", 0) & 0x400
        ):
            raise ValueError("Aliased source/artifact paths are unsupported.")
        if component == base:
            break
    if not selected.resolve(strict=True).is_relative_to(base.resolve(strict=True)):
        raise ValueError("Resolved file must remain inside the intended root.")
    if not stat.S_ISREG(selected.lstat().st_mode):
        raise ValueError("A regular source/artifact file is required.")
