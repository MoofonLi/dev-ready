"""Project the selected Agent Targets onto their native paths (ADR-015).

Canonical Content is written once, at the open-standard location; every Agent
Target reaches those same bytes through its own native layout. This module owns
that mapping. The overlay writer, the structural inspector, the upgrade planner
and the lifecycle fixtures all read it here instead of restating it, so a change
to an Agent Target's layout — or to where the Agent Target Map comes from
(ADR-019) — is one edit rather than five.

Deliberately below `prompts`: callers hand over the selected target ids, not a
`ProjectSelection`, so nothing in the dependency graph has to invert.
"""

from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass, replace
from pathlib import Path

from dev_ready.manifest import AgentTarget, CatalogItem, ComponentCatalog

__all__ = [
    "CANONICAL_SKILLS_ROOT",
    "TargetProjection",
    "canonical_skill_names",
    "project_targets",
]

# Where Canonical Content for a skill lives, regardless of Agent Target.
CANONICAL_SKILLS_ROOT: tuple[str, ...] = (".agents", "skills")

# The manifest-declared target of an MCP effect before it is retargeted onto an
# Agent Target's own MCP file.
_BASE_MCP_CONFIG = ".mcp.json"


@dataclass(frozen=True)
class TargetProjection:
    """The native surface a set of Agent Targets adds to a generated project."""

    targets: tuple[AgentTarget, ...] = ()

    @property
    def rules_files(self) -> tuple[str, ...]:
        """Native rules-file paths that need a pointer to `AGENTS.md`."""
        return tuple(
            target.rules_file for target in self.targets if target.rules_file is not None
        )

    @property
    def mcp_files(self) -> tuple[str, ...]:
        """Native MCP configuration paths, for targets that declare one."""
        return tuple(
            target.mcp_file for target in self.targets if target.mcp_file is not None
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
            for target in self.targets
            if target.mcp_file is not None
        )

    def stub_path(self, target: AgentTarget, skill_name: str) -> Path:
        """Where one target's Pointer Stub for a canonical skill is written."""
        return Path(target.skills_dir) / skill_name / "SKILL.md"

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


def canonical_skill_names(
    catalog: ComponentCatalog, skill_ids: Collection[str]
) -> tuple[str, ...]:
    """Skill directory names the given skills write as Canonical Content.

    A skill earns a Pointer Stub in every selected Agent Target exactly when it
    writes a `.agents/skills/<name>/` directory, so this is also the list every
    target's stub directory is expected to mirror.
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
