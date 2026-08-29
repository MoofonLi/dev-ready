"""Render the post-generation success report.

Pure function of its arguments — no filesystem access, so it stays valid
even if the caller passes paths that were never actually written (as the
unit tests do). See docs/architecture.md, Module Boundary.
"""

from pathlib import Path

from dev_ready.manifest import CATALOG_COMPONENTS, ComponentCatalog, UpstreamPin
from dev_ready.presentation import PresentationStyle, ScreenBlock, ScreenLine, render_screen
from dev_ready.intent import Answers

__all__ = ["render_report"]

# FR-38. `admin@example.com` is upstream's own `first_superuser` default and
# dev-ready does not override it, so it is a value this renderer knows without
# reading anything. The password is generated per project and is named by key
# only: a secret echoed to a terminal lands in scrollback, in CI logs, and in
# whatever captured the command's output, and the file is already the right
# place for it.
_SUPERUSER_EMAIL = "admin@example.com"
_STANDARD_AGENT_EXAMPLES = ("codex", "cursor", "gemini-cli")
_CREDENTIAL_DISCLOSURE = ScreenBlock(
    heading="First Login:",
    lines=(
        ScreenLine(f"  email:    {_SUPERUSER_EMAIL}"),
        ScreenLine(
            "  password: generated per project; it is the FIRST_SUPERUSER_PASSWORD value in .env"
        ),
        ScreenLine("  note:     the superuser is created on first start and is looked up by email,"),
        ScreenLine("            so editing FIRST_SUPERUSER_PASSWORD afterwards has no effect until"),
        ScreenLine("            the database is reset (docker compose down -v)."),
    ),
)


def render_report(
    answers: Answers,
    pin: UpstreamPin,
    written: list[Path],
    catalog: ComponentCatalog | None = None,
    *,
    style: PresentationStyle = PresentationStyle(),
) -> str:
    """Render the full success message `cli.py` prints verbatim after generation."""
    blocks = (
        ScreenBlock(
            heading=f"project generated: {answers.project_name}",
            lines=(
                ScreenLine(f"location:  {answers.target_dir}", wrap=False),
                ScreenLine(f"upstream:  {pin.repo}@{pin.commit[:12]} ({pin.ref})"),
            ),
        ),
        _render_next_steps(answers),
        _render_selection_block(answers, catalog),
        _CREDENTIAL_DISCLOSURE,
        _render_overlay_summary(written),
    )
    return render_screen(blocks, style=style)


def _render_next_steps(answers: Answers) -> ScreenBlock:
    actions: list[tuple[str, ...]] = []
    if answers.target_dir != Path.cwd():
        actions.append((f"cd {answers.target_dir}",))
    actions.extend(
        (
            (
                "ask your coding agent to run `/setup-project` before the first start",
                "(the superuser is created on that first start)",
            ),
            # "docker compose watch" is the dev workflow for
            # fastapi/full-stack-fastapi-template as of the manifest-pinned commit.
            # Update when a manifest bump changes the upstream workflow.
            ("docker compose watch   (see AGENTS.md for other commands)",),
            ("read AGENTS.md for the full picture",),
        )
    )
    if answers.agent_targets:
        actions.append(
            (
                "after cloning, run `uvx dev-ready upgrade` to recreate "
                "machine-local skill links",
            )
        )
    steps: list[ScreenLine] = []
    for number, action in enumerate(actions, start=1):
        steps.append(ScreenLine(f"  {number}. {action[0]}", wrap=False))
        steps.extend(ScreenLine(f"     {continuation}") for continuation in action[1:])
    return ScreenBlock(heading="Next Steps:", lines=tuple(steps))


def _render_overlay_summary(written: list[Path]) -> ScreenBlock:
    counts = {
        "root files": 0,
        "canonical agent content": 0,
        "documentation": 0,
        "Agent Target artifacts": 0,
    }
    for path in written:
        if len(path.parts) == 1:
            counts["root files"] += 1
        elif path.parts[0] == ".agents":
            counts["canonical agent content"] += 1
        elif path.parts[0] == "docs":
            counts["documentation"] += 1
        else:
            counts["Agent Target artifacts"] += 1
    breakdown = "; ".join(f"{label}: {count}" for label, count in counts.items())
    # FR-44 as amended 2026-08-14. The stamp's `inventory` is the authoritative
    # managed-file list, so the report names it. `dev-ready check` is a drift
    # verdict, not an inventory query: it does not print the paths, and it exits
    # 7 on drift. Naming it here would promise output that command never gives.
    return ScreenBlock(
        heading="Overlay Summary:",
        lines=(
            ScreenLine(f"  overlay files written: {len(written)}"),
            ScreenLine(f"  breakdown: {breakdown}"),
            ScreenLine('  full managed-file list: the "inventory" entries in .dev-ready.json'),
        ),
    )


def _render_selection_block(
    answers: Answers,
    catalog: ComponentCatalog | None,
) -> ScreenBlock:
    if catalog is None:
        target_ids = ", ".join(sorted(answers.agent_targets)) or "(none)"
        return ScreenBlock(heading=f"agent targets: {target_ids}", lines=())
    selected_ids = frozenset().union(
        *(answers.items(component) for component in CATALOG_COMPONENTS)
    )
    selected_enhancements = sorted(
        item.id
        for item in catalog.all_items()
        if item.kind == "enhancement" and item.id in selected_ids
    )
    lines = [
        ScreenLine("documentation skeletons: architecture, requirements"),
        ScreenLine("enhancements: " + (", ".join(selected_enhancements) or "(none)")),
        *(ScreenLine(line) for line in _render_agent_targets(answers, catalog)),
    ]
    return ScreenBlock(
        heading=f"Engineering Flow (required): {answers.selection.development_loop}",
        lines=tuple(lines),
    )


def _render_agent_targets(
    answers: Answers,
    catalog: ComponentCatalog,
) -> list[str]:
    lines: list[str] = []
    if catalog.standard_compliant_agents:
        agents_str = ", ".join(_STANDARD_AGENT_EXAMPLES)
        lines.append(
            "standard-compliant agents "
            f"({len(catalog.standard_compliant_agents)}; read .agents/skills/ directly — "
            f"no target selection needed): {agents_str}, …"
        )
    if not answers.agent_targets:
        lines.append("agent targets: (none)")
        return lines
    targets = catalog.agent_targets

    lines.append("agent targets:")
    for target_id in sorted(answers.agent_targets):
        target = targets[target_id]
        artifacts: list[str] = []
        if target.rules_file is not None:
            artifacts.append(f"rules pointer {target.rules_file}")
        if answers.include_skills:
            artifacts.append(f"skill links in {target.skills_dir}")
        if answers.include_mcp and target.mcp_file is not None:
            artifacts.append(f"MCP configuration {target.mcp_file}")
        received = ", ".join(artifacts) if artifacts else "no target-specific files"
        lines.append(f"  {target_id}: {received}")
        if target.mcp_file is None:
            lines.append("    MCP configuration must be set up manually (user-global configuration).")
    return lines
