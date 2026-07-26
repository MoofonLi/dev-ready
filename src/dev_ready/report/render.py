"""Render the post-generation success report.

Pure function of its arguments — no filesystem access, so it stays valid
even if the caller passes paths that were never actually written (as the
unit tests do). See docs/architecture.md, Module Boundary.
"""

from pathlib import Path
from collections.abc import Mapping

from dev_ready.manifest import CatalogItem, ComponentCatalog, UpstreamPin
from dev_ready.prompts import Answers

__all__ = ["render_report"]


def render_report(
    answers: Answers,
    pin: UpstreamPin,
    written: list[Path],
    catalog: Mapping[str, tuple[CatalogItem, ...]] | None = None,
) -> str:
    """Render the full success message `cli.py` prints verbatim after generation."""
    overlay_paths = ", ".join(str(path) for path in written) if written else "(none)"
    lines = [
        f"project generated: {answers.project_name}",
        f"location:  {answers.target_dir}",
        f"upstream:  {pin.repo}@{pin.commit[:12]} ({pin.ref})",
        f"overlay:   {overlay_paths}",
        *_render_agent_targets(answers, catalog),
        "",
        "next steps:",
        f"  1. cd {answers.target_dir}",
        # "docker compose watch" is the dev workflow for
        # fastapi/full-stack-fastapi-template as of the manifest-pinned commit.
        # Update when a manifest bump changes the upstream workflow.
        "  2. docker compose watch   (see AGENTS.md for other commands)",
        "  3. read AGENTS.md for the full picture",
    ]
    return "\n".join(lines)


def _render_agent_targets(
    answers: Answers,
    catalog: Mapping[str, tuple[CatalogItem, ...]] | None,
) -> list[str]:
    if not answers.agent_targets:
        return ["agent targets: (none)"]
    targets = getattr(catalog, "agent_targets", {}) if catalog is not None else {}
    if not isinstance(catalog, ComponentCatalog):
        return [f"agent targets: {', '.join(sorted(answers.agent_targets))}"]

    lines = ["agent targets:"]
    for target_id in sorted(answers.agent_targets):
        target = targets[target_id]
        artifacts: list[str] = []
        if target.rules_file is not None:
            artifacts.append(f"rules pointer {target.rules_file}")
        if answers.include_skills:
            artifacts.append(f"skill stubs in {target.skills_dir}")
        if answers.include_mcp and target.mcp_file is not None:
            artifacts.append(f"MCP configuration {target.mcp_file}")
        received = ", ".join(artifacts) if artifacts else "no target-specific files"
        lines.append(f"  {target.description.rstrip('.')} ({target_id}): {received}")
        if target.mcp_file is None:
            lines.append("    MCP configuration must be set up manually (user-global configuration).")
    return lines
