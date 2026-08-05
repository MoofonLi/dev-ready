"""Render the post-generation success report.

Pure function of its arguments — no filesystem access, so it stays valid
even if the caller passes paths that were never actually written (as the
unit tests do). See docs/architecture.md, Module Boundary.
"""

from pathlib import Path

from dev_ready.manifest import CATALOG_COMPONENTS, ComponentCatalog, UpstreamPin
from dev_ready.prompts import Answers

__all__ = ["render_report"]

# FR-38. `admin@example.com` is upstream's own `first_superuser` default and
# dev-ready does not override it, so it is a value this renderer knows without
# reading anything. The password is generated per project and is named by key
# only: a secret echoed to a terminal lands in scrollback, in CI logs, and in
# whatever captured the command's output, and the file is already the right
# place for it.
_SUPERUSER_EMAIL = "admin@example.com"
_CREDENTIAL_DISCLOSURE = (
    "first login:",
    f"  email:    {_SUPERUSER_EMAIL}",
    "  password: generated per project; it is the FIRST_SUPERUSER_PASSWORD value in .env",
    "  note:     the superuser is created on first start and is looked up by email,",
    "            so editing FIRST_SUPERUSER_PASSWORD afterwards has no effect until",
    "            the database is reset (docker compose down -v).",
)


def render_report(
    answers: Answers,
    pin: UpstreamPin,
    written: list[Path],
    catalog: ComponentCatalog | None = None,
) -> str:
    """Render the full success message `cli.py` prints verbatim after generation."""
    overlay_paths = ", ".join(str(path) for path in written) if written else "(none)"
    lines = [
        f"project generated: {answers.project_name}",
        f"location:  {answers.target_dir}",
        f"upstream:  {pin.repo}@{pin.commit[:12]} ({pin.ref})",
        f"overlay:   {overlay_paths}",
        *_render_selection(answers, catalog),
        *_render_agent_targets(answers, catalog),
        "",
        "next steps:",
        f"  1. cd {answers.target_dir}",
        # "docker compose watch" is the dev workflow for
        # fastapi/full-stack-fastapi-template as of the manifest-pinned commit.
        # Update when a manifest bump changes the upstream workflow.
        "  2. docker compose watch   (see AGENTS.md for other commands)",
        "  3. read AGENTS.md for the full picture",
        "",
        *_CREDENTIAL_DISCLOSURE,
    ]
    return "\n".join(lines)


def _render_selection(
    answers: Answers,
    catalog: ComponentCatalog | None,
) -> list[str]:
    if catalog is None:
        return []
    selected_ids = frozenset().union(
        *(answers.items(component) for component in CATALOG_COMPONENTS)
    )
    selected_enhancements = sorted(
        item.id
        for item in catalog.all_items()
        if item.kind == "enhancement" and item.id in selected_ids
    )
    return [
        f"development loop (required): {answers.selection.development_loop}",
        "documentation skeletons: architecture, requirements",
        "enhancements: " + (", ".join(selected_enhancements) or "(none)"),
    ]


def _render_agent_targets(
    answers: Answers,
    catalog: ComponentCatalog | None,
) -> list[str]:
    lines: list[str] = []
    if catalog is not None and catalog.standard_compliant_agents:
        agents_str = ", ".join(sorted(catalog.standard_compliant_agents))
        lines.append(
            f"standard-compliant agents (read .agents/skills/ directly — no target selection needed): {agents_str}"
        )
    if not answers.agent_targets:
        lines.append("agent targets: (none)")
        return lines
    if catalog is None:
        lines.append(f"agent targets: {', '.join(sorted(answers.agent_targets))}")
        return lines
    targets = catalog.agent_targets

    lines.append("agent targets:")
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
        lines.append(f"  {target_id}: {received}")
        if target.mcp_file is None:
            lines.append("    MCP configuration must be set up manually (user-global configuration).")
    return lines
