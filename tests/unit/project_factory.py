"""Shared generated-project structure builder for lifecycle tests."""

from dataclasses import replace
from pathlib import Path
from importlib import resources
from importlib.resources.abc import Traversable

from dev_ready.inspection import REQUIRED_UPSTREAM_PATHS
from dev_ready.manifest import CatalogItem, ComponentCatalog
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

    (root / "AGENTS.md").write_text("# Project\n", encoding="utf-8")
    (root / "README.md").write_text("# Readme\n", encoding="utf-8")
    (root / ".dev-ready.json").write_text("{}", encoding="utf-8")

    if selection.docs:
        (root / "docs").mkdir(exist_ok=True)

    for name in ("skills", "mcp", "docs"):
        selected = selection.items(name)
        for item in catalog.get(name, ()):
            if item.id not in selected:
                continue
            target_files: tuple[str | None, ...] = (None,)
            if name == "mcp":
                target_files = tuple(
                    target.mcp_file
                    for target_id, target in getattr(catalog, "agent_targets", {}).items()
                    if target_id in selection.agent_targets and target.mcp_file is not None
                )
            for target_file in target_files:
                for item_path in item.paths:
                    destination = root / (target_file or item_path.dest)
                    source = resources.files("dev_ready").joinpath(
                        "templates", *item_path.src.split("/")
                    )
                    _materialize_asset(source, destination)
                if item.effect is not None:
                    effect = (
                        replace(item.effect, target=target_file)
                        if target_file is not None
                        else item.effect
                    )
                    target = root / effect.target
                    target.parent.mkdir(parents=True, exist_ok=True)
                    if not target.exists():
                        target.write_text("{}", encoding="utf-8")
                    effect.apply(root)

    if isinstance(catalog, ComponentCatalog):
        skill_names = {
            Path(item_path.dest).parts[2]
            for item in catalog.get("skills", ())
            if item.id in selection.skills
            for item_path in item.paths
            if len(Path(item_path.dest).parts) >= 3
            and Path(item_path.dest).parts[:2] == (".agents", "skills")
        }
        for target_id, target in catalog.agent_targets.items():
            if target_id not in selection.agent_targets:
                continue
            if target.rules_file is not None:
                rules_file = root / target.rules_file
                rules_file.parent.mkdir(parents=True, exist_ok=True)
                rules_file.write_text("@AGENTS.md\n", encoding="utf-8")
            for skill_name in skill_names:
                stub = root / target.skills_dir / skill_name / "SKILL.md"
                stub.parent.mkdir(parents=True, exist_ok=True)
                stub.write_text(
                    f"---\nname: {skill_name}\ndescription: stub\n---\n\n"
                    f"Read `.agents/skills/{skill_name}/SKILL.md`.\n",
                    encoding="utf-8",
                )
