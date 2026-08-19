"""Create and classify Skill Link objects on the local filesystem.

POSIX writes a relative directory symbolic link. Windows writes an
elevation-free directory junction via ``_winapi.CreateJunction`` and never
calls ``os.symlink``. Classification inspects the path object itself and
does not follow it.
"""

from __future__ import annotations

import enum
import os
import sys
from pathlib import Path

__all__ = [
    "PathKind",
    "classify_path",
    "create_skill_link",
    "has_link_component",
    "remove_link_object",
]


class PathKind(enum.Enum):
    """What occupies a path, without following a link object."""

    SYMBOLIC_LINK = "symbolic_link"
    JUNCTION = "junction"
    FILE = "file"
    DIRECTORY = "directory"
    ABSENT = "absent"


def classify_path(path: Path) -> PathKind:
    """Name the object at ``path`` without resolving through it."""
    if path.is_symlink():
        return PathKind.SYMBOLIC_LINK
    if path.is_junction():
        return PathKind.JUNCTION
    if path.is_dir():
        return PathKind.DIRECTORY
    if path.is_file():
        return PathKind.FILE
    return PathKind.ABSENT


def create_skill_link(link_path: Path, canonical_dir: Path) -> None:
    """Create the platform-native Skill Link at ``link_path``."""
    parent = link_path.parent
    if not parent.exists():
        parent.mkdir(parents=True, exist_ok=True)
    if sys.platform == "win32":
        _create_junction(link_path, canonical_dir)
        return
    _create_relative_symlink(link_path, canonical_dir)


def has_link_component(root: Path, path: Path) -> bool:
    """Return whether ``path`` traverses a symlink or junction beneath ``root``."""
    try:
        relative = path.relative_to(root)
    except ValueError:
        return True
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink() or current.is_junction():
            return True
    return False


def remove_link_object(path: Path) -> None:
    """Remove a symlink or junction without following it."""
    if path.is_symlink() or path.is_junction():
        path.unlink()


def _create_junction(link_path: Path, canonical_dir: Path) -> None:
    import _winapi

    _winapi.CreateJunction(str(canonical_dir.resolve()), str(link_path))


def _create_relative_symlink(link_path: Path, canonical_dir: Path) -> None:
    relative = os.path.relpath(canonical_dir, start=link_path.parent)
    os.symlink(relative, link_path, target_is_directory=True)
