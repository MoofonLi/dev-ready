"""Shared generated-project structure builder for lifecycle tests."""

from pathlib import Path
from importlib import resources
from importlib.resources.abc import Traversable

from dev_ready.inspection import REQUIRED_UPSTREAM_PATHS
from dev_ready.manifest import CatalogItem
from dev_ready.prompts import ProjectSelection

_DIRECTORY_ENTRIES = {"backend", "frontend"}


def _materialize_asset(source: Traversable, destination: Path) -> None:
    if source.is_dir():
        destination.mkdir(parents=True, exist_ok=True)
        for entry in source.iterdir():
            _materialize_asset(entry, destination / entry.name.removesuffix(".tmpl"))
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    content = "{}" if destination.suffix == ".json" else "stub"
    destination.write_text(content, encoding="utf-8")


def materialize_project_structure(
    root: Path,
    catalog: dict[str, tuple[CatalogItem, ...]],
    selection: ProjectSelection,
) -> None:
    """Create one structurally valid local project for the given selection."""
    for relative in REQUIRED_UPSTREAM_PATHS:
        path = root / relative
        if relative in _DIRECTORY_ENTRIES:
            path.mkdir(parents=True, exist_ok=True)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("stub", encoding="utf-8")

    (root / "CLAUDE.md").write_text("# Project\n", encoding="utf-8")
    (root / "README.md").write_text("# Readme\n", encoding="utf-8")
    (root / ".dev-ready.json").write_text("{}", encoding="utf-8")

    if selection.docs:
        (root / "docs").mkdir(exist_ok=True)
    if selection.agents:
        (root / "docs" / "handoffs").mkdir(parents=True, exist_ok=True)

    for name in ("skills", "mcp"):
        selected = selection.items(name)
        for item in catalog.get(name, ()):
            if item.id not in selected:
                continue
            for item_path in item.paths:
                destination = root / item_path.dest
                source = resources.files("dev_ready").joinpath(
                    "templates", *item_path.src.split("/")
                )
                _materialize_asset(source, destination)
            if item.effect is not None:
                target = root / item.effect.target
                target.parent.mkdir(parents=True, exist_ok=True)
                if not target.exists():
                    target.write_text("{}", encoding="utf-8")
                item.effect.apply(root)
