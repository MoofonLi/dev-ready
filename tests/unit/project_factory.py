"""Shared generated-project structure builder for lifecycle tests.

The Agent Target layout is read from `dev_ready.agent_targets`, never restated
here — a fixture that re-derives the projection can agree with itself while
disagreeing with the overlay it is meant to verify.
"""

from pathlib import Path
from importlib import resources
from importlib.resources.abc import Traversable

from dev_ready.agent_targets import canonical_skill_names, project_targets
from dev_ready.inspection import REQUIRED_UPSTREAM_PATHS
from dev_ready.manifest import CATALOG_COMPONENTS, ComponentCatalog
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

    if selection.docs:
        (root / "docs").mkdir(exist_ok=True)

    projection = project_targets(catalog, selection.agent_targets)

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

    skill_names = canonical_skill_names(catalog, selection.skills)
    for target in projection.targets:
        if target.rules_file is not None:
            rules_file = root / target.rules_file
            rules_file.parent.mkdir(parents=True, exist_ok=True)
            rules_file.write_text("@AGENTS.md\n", encoding="utf-8")
        for skill_name in skill_names:
            stub = root / projection.stub_path(target, skill_name)
            stub.parent.mkdir(parents=True, exist_ok=True)
            stub.write_text(
                f"---\nname: {skill_name}\ndescription: stub\n---\n\n"
                f"Read `.agents/skills/{skill_name}/SKILL.md`.\n",
                encoding="utf-8",
            )
