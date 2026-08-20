"""Resolve and inspect manifest-declared executable paths.

This neutral, read-only module is shared by overlay application and
generation verification so those two policy modules remain independent.
"""

from __future__ import annotations

import stat
import sys
from collections.abc import Collection
from pathlib import Path

from dev_ready.manifest import CATALOG_COMPONENTS, ComponentCatalog, VendoredPin
from dev_ready.prompts import Answers


def declared_executable_paths(
    catalog: ComponentCatalog,
    answers: Answers,
    vendored: Collection[VendoredPin],
) -> tuple[Path, ...]:
    """Map selected vendored executable source paths into project paths."""
    executable_paths: set[Path] = set()
    for pin in vendored:
        if not pin.executable:
            continue
        selected_items = (
            item
            for component in CATALOG_COMPONENTS
            for item in catalog.get(component, ())
            if item.id in answers.items(component) and item.vendored_repo == pin.repo
        )
        for item in selected_items:
            for item_path in item.paths:
                template_source = f"src/dev_ready/templates/{item_path.src}"
                for pin_path in pin.paths:
                    if pin_path.dest not in {template_source, item_path.src}:
                        continue
                    source_root = pin_path.src.rstrip("/")
                    for executable in pin.executable:
                        if executable == source_root:
                            relative = ""
                        elif executable.startswith(f"{source_root}/"):
                            relative = executable[len(source_root) + 1 :]
                        else:
                            continue
                        destination = Path(item_path.dest)
                        if relative:
                            destination /= relative
                        executable_paths.add(destination)
    return tuple(sorted(executable_paths))


def executable_mode_issues(
    project_dir: Path, paths: Collection[Path]
) -> tuple[str, ...]:
    """Return verification issues for declared executable files on POSIX."""
    if sys.platform == "win32":
        return ()
    issues: list[str] = []
    for dest_rel in paths:
        dest = project_dir / dest_rel
        if not dest.is_file():
            issues.append(f"declared executable path {dest_rel} is missing or not a file")
            continue
        try:
            mode = dest.stat().st_mode
        except OSError as error:
            issues.append(f"could not inspect declared executable path {dest_rel}: {error}")
            continue
        if not mode & stat.S_IXUSR:
            issues.append(f"declared executable path {dest_rel} is not executable")
    return tuple(issues)
