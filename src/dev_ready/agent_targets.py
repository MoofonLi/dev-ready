"""Project the selected Agent Targets onto their native paths (ADR-015, ADR-028).

Canonical Content is written once, at the open-standard location. This module
owns the pure mapping: each target's rules pointer, MCP file, Skill Link path,
nested ignore-anchor path, and the skill names derived from desired content.
It performs no filesystem I/O. The overlay writer, inspector, upgrade planner
and lifecycle fixtures all read the mapping here instead of restating it.

Does not import `intent`: callers hand over the selected target ids, not a
`ProjectSelection`, so nothing in the dependency graph has to invert.
"""

from __future__ import annotations

from collections.abc import Callable, Collection
from dataclasses import dataclass, replace
from pathlib import Path

from dev_ready.manifest import AgentTarget, CatalogItem, ComponentCatalog

__all__ = [
    "CANONICAL_SKILLS_ROOT",
    "TargetProjection",
    "canonical_skill_names",
    "project_targets",
    "skill_names_from_content",
]

# Where Canonical Content for a skill lives, regardless of Agent Target.
CANONICAL_SKILLS_ROOT: tuple[str, ...] = (".agents", "skills")

# The manifest-declared target of an MCP effect before it is retargeted onto an
# Agent Target's own MCP file.
_BASE_MCP_CONFIG = ".mcp.json"


@dataclass(frozen=True)
class TargetProjection:
    """The native surface a set of Agent Targets adds to a generated project."""

    selected_targets: tuple[AgentTarget, ...] = ()

    @property
    def skill_targets(self) -> tuple[AgentTarget, ...]:
        """One representative target for each native skills destination."""
        return _unique_targets_by_path(
            self.selected_targets, lambda target: target.skills_dir
        )

    @property
    def mcp_targets(self) -> tuple[AgentTarget, ...]:
        """One representative target for each declared native MCP destination."""
        return _unique_targets_by_path(
            self.selected_targets, lambda target: target.mcp_file
        )

    @property
    def rules_files(self) -> tuple[str, ...]:
        """Native rules-file paths that need a pointer to `AGENTS.md`."""
        return tuple(
            target.rules_file
            for target in _unique_targets_by_path(
                self.selected_targets, lambda target: target.rules_file
            )
            if target.rules_file is not None
        )

    @property
    def mcp_files(self) -> tuple[str, ...]:
        """Native MCP configuration paths, for targets that declare one."""
        return tuple(
            target.mcp_file for target in self.mcp_targets
            if target.mcp_file is not None
        )

    def retarget_mcp(
        self, item: CatalogItem
    ) -> tuple[tuple[AgentTarget, CatalogItem], ...]:
        """Rewrite one MCP item onto each target that declares an MCP file.

        Both the item's destination paths and its injected effect move to the
        target's native file — an MCP item is only ever materialized there.
        """
        return tuple(
            (
                target,
                replace(
                    item,
                    paths=tuple(
                        replace(item_path, dest=target.mcp_file)
                        for item_path in item.paths
                    ),
                    effect=(
                        replace(item.effect, target=target.mcp_file)
                        if item.effect is not None
                        else None
                    ),
                ),
            )
            for target in self.mcp_targets
            if target.mcp_file is not None
        )

    def stub_path(self, target: AgentTarget, skill_name: str) -> Path:
        """Where one target's Pointer Stub for a canonical skill is written."""
        return Path(target.skills_dir) / skill_name / "SKILL.md"

    def link_path(self, target: AgentTarget, skill_name: str) -> Path:
        """Where one target's Skill Link for a canonical skill is written."""
        return Path(target.skills_dir) / skill_name

    def ignore_anchor_path(self, target: AgentTarget) -> Path:
        """Where one target's nested Git safety-anchor file is written."""
        return Path(target.skills_dir) / ".gitignore"

    def base_mcp_config_paths(
        self, catalog: ComponentCatalog, selected_mcp_items: Collection[str]
    ) -> tuple[Path, ...]:
        """Native MCP paths needing the base config file a selected effect injects into."""
        needs_base_config = any(
            item.id in selected_mcp_items
            and item.effect is not None
            and item.effect.target == _BASE_MCP_CONFIG
            for item in catalog.get("mcp", ())
        )
        if not needs_base_config:
            return ()
        return tuple(Path(mcp_file) for mcp_file in self.mcp_files)


def _unique_targets_by_path(
    targets: tuple[AgentTarget, ...],
    path_for: Callable[[AgentTarget], str | None],
) -> tuple[AgentTarget, ...]:
    seen: set[str] = set()
    unique: list[AgentTarget] = []
    for target in targets:
        path = path_for(target)
        if path is None or path in seen:
            continue
        seen.add(path)
        unique.append(target)
    return tuple(unique)


def project_targets(
    catalog: ComponentCatalog, target_ids: Collection[str]
) -> TargetProjection:
    """Project the named Agent Targets, in the catalog's declaration order.

    Pass `catalog.agent_target_ids` to reason about every declared target (as
    structural inspection does when checking that unselected targets left
    nothing behind); pass the selection's ids to reason about one project.
    """
    wanted = frozenset(target_ids)
    return TargetProjection(
        tuple(
            target
            for target_id, target in catalog.agent_targets.items()
            if target_id in wanted
        )
    )


def skill_names_from_content(paths: Collection[str]) -> tuple[str, ...]:
    """Skill names from every direct `.agents/skills/<name>/SKILL.md` path."""
    names = {
        parts[2]
        for path in paths
        if len(parts := Path(path).parts) == 4
        and parts[:2] == CANONICAL_SKILLS_ROOT
        and parts[3] == "SKILL.md"
        and parts[2]
    }
    return tuple(sorted(names))


def canonical_skill_names(
    catalog: ComponentCatalog, skill_ids: Collection[str]
) -> tuple[str, ...]:
    """Skill directory names the given skills write as Canonical Content.

    A skill earns a Skill Link in every selected Agent Target exactly when it
    writes a `.agents/skills/<name>/` directory. Prefer ``skill_names_from_content``
    for desired overlay paths so non-catalog infrastructure participates.
    """
    selected = frozenset(skill_ids)
    names = {
        Path(item_path.dest).parts[2]
        for item in catalog.get("skills", ())
        if item.id in selected
        for item_path in item.paths
        if len(Path(item_path.dest).parts) >= 3
        and Path(item_path.dest).parts[:2] == CANONICAL_SKILLS_ROOT
    }
    return tuple(sorted(names))
