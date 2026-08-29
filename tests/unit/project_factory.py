"""Shared generated-project structure builder for lifecycle tests.

The Agent Target layout is read from `dev_ready.agent_targets`, never restated
here — a fixture that re-derives the projection can agree with itself while
disagreeing with the overlay it is meant to verify.
"""

from pathlib import Path
from importlib import resources
from importlib.resources.abc import Traversable

from dev_ready.agent_targets import (
    CANONICAL_SKILLS_ROOT,
    project_targets,
    skill_names_from_content,
)
from dev_ready.overlay.infrastructure import skill_infrastructure_paths
from dev_ready.skill_links import PathKind, classify_path, create_skill_link
from dev_ready.inspection import REQUIRED_UPSTREAM_PATHS
from dev_ready.manifest import CATALOG_COMPONENTS, ComponentCatalog
from dev_ready.intent import ProjectSelection

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
    catalog: ComponentCatalog,
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

    (root / "AGENTS.md").write_text("# Project\n", encoding="utf-8")
    (root / "README.md").write_text("# Readme\n", encoding="utf-8")
    (root / ".dev-ready.json").write_text("{}", encoding="utf-8")

    (root / "docs").mkdir(exist_ok=True)

    projection = project_targets(catalog, selection.agent_targets)
    for source, destination in skill_infrastructure_paths():
        _materialize_asset(
            resources.files("dev_ready").joinpath("templates", *source.parts),
            root / destination,
        )

    for name in CATALOG_COMPONENTS:
        selected = selection.items(name)
        for item in catalog.get(name, ()):
            if item.id not in selected:
                continue
            materialized = (
                tuple(retargeted for _, retargeted in projection.retarget_mcp(item))
                if name == "mcp"
                else (item,)
            )
            for entry in materialized:
                for item_path in entry.paths:
                    source = resources.files("dev_ready").joinpath(
                        "templates", *item_path.src.split("/")
                    )
                    _materialize_asset(source, root / item_path.dest)
                if entry.effect is not None:
                    target = root / entry.effect.target
                    target.parent.mkdir(parents=True, exist_ok=True)
                    if not target.exists():
                        target.write_text("{}", encoding="utf-8")
                    entry.effect.apply(root)

    from dev_ready.overlay import render_ignore_anchor

    skill_root = root.joinpath(*CANONICAL_SKILLS_ROOT)
    skill_names = skill_names_from_content(
        path.relative_to(root).as_posix()
        for path in skill_root.glob("*/SKILL.md")
        if skill_root.is_dir()
    )
    for target in projection.skill_targets:
        if target.rules_file is not None:
            rules_file = root / target.rules_file
            rules_file.parent.mkdir(parents=True, exist_ok=True)
            rules_file.write_text("@AGENTS.md\n", encoding="utf-8")
        if skill_names:
            anchor = root / projection.ignore_anchor_path(target)
            anchor.parent.mkdir(parents=True, exist_ok=True)
            anchor.write_bytes(render_ignore_anchor(skill_names))
        for skill_name in skill_names:
            link = root / projection.link_path(target, skill_name)
            if classify_path(link) in {PathKind.SYMBOLIC_LINK, PathKind.JUNCTION}:
                continue
            create_skill_link(
                link,
                root.joinpath(*CANONICAL_SKILLS_ROOT, skill_name),
            )
