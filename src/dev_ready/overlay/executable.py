"""Apply manifest-declared executable modes to overlay output."""

from __future__ import annotations

from collections.abc import Collection
from pathlib import Path

from dev_ready.errors import OverlayError


def apply_executable_modes(project_dir: Path, paths: Collection[Path]) -> None:
    """Set the user-executable bit on every declared generated file."""
    for dest_rel in paths:
        dest = project_dir / dest_rel
        if not dest.is_file():
            raise OverlayError(
                f"declared executable overlay path is missing or not a file: {dest_rel}"
            )
        try:
            dest.chmod(dest.stat().st_mode | 0o755)
        except OSError as error:
            raise OverlayError(
                f"failed to set permissions on {dest_rel}: {error}"
            ) from error
