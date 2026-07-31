"""Resolve infrastructure files implied by selected catalog effects."""

from collections.abc import Collection, Mapping
from pathlib import Path

from dev_ready.manifest import AgentTarget, CatalogItem

_DOCUMENTATION_SCAFFOLD_PATHS = (
    (Path("docs", "architecture.md.tmpl"), Path("docs", "architecture.md")),
    (Path("docs", "requirements.md.tmpl"), Path("docs", "requirements.md")),
)


def base_mcp_config_targets(
    catalog: Mapping[str, tuple[CatalogItem, ...]],
    selected_mcp_items: Collection[str],
    agent_targets: Mapping[str, AgentTarget],
) -> tuple[Path, ...]:
    """Return native MCP config paths when a selected effect needs its base file."""
    needs_base_config = any(
        item.id in selected_mcp_items
        and item.effect is not None
        and item.effect.target == ".mcp.json"
        for item in catalog.get("mcp", ())
    )
    if not needs_base_config:
        return ()
    return tuple(
        Path(target.mcp_file)
        for target in agent_targets.values()
        if target.mcp_file is not None
    )


def documentation_scaffold_paths(
    included: bool,
) -> tuple[tuple[Path, Path], ...]:
    """Return documentation scaffold source/destination paths for this selection."""
    return _DOCUMENTATION_SCAFFOLD_PATHS if included else ()
