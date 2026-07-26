"""Interactive/non-interactive collection of Answers, and pre-write confirmation.

`prompts` performs no I/O other than the terminal (docs/architecture.md).
questionary is imported lazily, only from `_default_asker`, so a caller that
always supplies its own `asker` (tests, or the `--yes` flag path in cli.py,
which never calls into this module at all) never triggers the import.
"""

import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

from dev_ready.errors import AbortedError, InvalidArgumentsError
from dev_ready.manifest import CatalogItem, UpstreamPin
from dev_ready.prompts.answers import Answers, PartialAnswers, ProjectSelection, validate_project_name
from dev_ready.prompts.asker import Asker

__all__ = ["collect_answers", "confirm_generation"]

_COMPONENT_CHOICES = ("skills", "mcp", "docs", "handoff")


def _is_interactive() -> bool:
    return sys.stdin.isatty()


def _default_asker() -> Asker:
    from dev_ready.prompts._questionary_asker import QuestionaryAsker

    return QuestionaryAsker()


def collect_answers(
    partial: PartialAnswers,
    *,
    catalog: Mapping[str, tuple[CatalogItem, ...]] | None = None,
    asker: Asker | None = None,
) -> Answers:
    """Fill in whatever `partial` left unanswered, via `asker` (or a real
    terminal prompt by default), and return a complete `Answers`.

    Never blocks on a terminal that cannot answer: raises
    `InvalidArgumentsError` up front if a prompt would be needed but stdin
    is not a TTY (and no `asker` was injected).
    """
    needs_name = partial.project_name is None
    needs_components = partial.selection is None

    if needs_name and asker is None and not _is_interactive():
        raise InvalidArgumentsError(
            "project name is required: dev-ready init <project-name> "
            "(or run in an interactive terminal to be prompted, or pass --yes)"
        )
    if needs_components and asker is None and not _is_interactive():
        raise InvalidArgumentsError(
            "component selection requires an interactive terminal — pass "
            "--no-skills/--no-mcp/--no-docs/--no-handoff explicitly, or use --yes"
        )

    resolved_asker = asker
    if (needs_name or needs_components) and resolved_asker is None:
        resolved_asker = _default_asker()

    project_name = partial.project_name
    if needs_name:
        assert resolved_asker is not None
        project_name = _prompt_project_name(resolved_asker)

    if needs_components:
        assert resolved_asker is not None
        skills_on, mcp_on, include_docs, include_handoff = _prompt_components(resolved_asker)
        if catalog is not None:
            if skills_on and "skills" in catalog and catalog["skills"]:
                skills_items = _prompt_items(
                    resolved_asker, "skills", [item.id for item in catalog["skills"]]
                )
            else:
                skills_items = frozenset()

            if mcp_on and "mcp" in catalog and catalog["mcp"]:
                mcp_items = _prompt_items(
                    resolved_asker, "mcp", [item.id for item in catalog["mcp"]]
                )
            else:
                mcp_items = frozenset()

        else:
            skills_items = frozenset()
            mcp_items = frozenset()
        if catalog is None and (skills_on or mcp_on):
            raise InvalidArgumentsError("catalog is required to validate selected items")
        agent_targets = _prompt_agent_targets(resolved_asker, catalog or {})
        selection = ProjectSelection.from_items(
            catalog or {},
            skills=skills_items if skills_on else frozenset(),
            mcp=mcp_items if mcp_on else frozenset(),
            agent_targets=agent_targets,
            docs=include_docs,
            handoff=include_handoff,
        )
    else:
        assert partial.selection is not None
        selection = partial.selection

    target_dir = (
        partial.target_dir if partial.target_dir is not None else Path.cwd() / project_name
    )

    return Answers(
        project_name=project_name,
        target_dir=target_dir,
        selection=selection,
        assume_yes=partial.assume_yes,
    )


def confirm_generation(
    answers: Answers, pin: UpstreamPin, *, asker: Asker | None = None
) -> bool:
    """Print a summary of what will be written and ask the user to confirm.

    Returns `False` for both an explicit decline and a cancelled prompt
    (Ctrl-C, or the asker returning `None`) — callers only need to check
    truthiness, never distinguish the two.
    """
    if asker is None and not _is_interactive():
        raise InvalidArgumentsError(
            "confirmation requires an interactive terminal — pass --yes to skip prompts"
        )

    resolved_asker = asker if asker is not None else _default_asker()
    print(_render_confirmation_summary(answers, pin))
    try:
        confirmed = resolved_asker.confirm("Proceed?", default=True)
    except KeyboardInterrupt:
        confirmed = None
    return bool(confirmed)


def _render_confirmation_summary(answers: Answers, pin: UpstreamPin) -> str:
    comp_parts = []
    if answers.includes("skills"):
        skills = answers.items("skills")
        skills_str = ", ".join(sorted(skills)) if skills else "(none)"
        comp_parts.append(f"skills ({skills_str})")
    if answers.includes("mcp"):
        mcp = answers.items("mcp")
        mcp_str = ", ".join(sorted(mcp)) if mcp else "(none)"
        comp_parts.append(f"mcp ({mcp_str})")
    if answers.includes("docs"):
        comp_parts.append("docs")
    if answers.includes("handoff"):
        comp_parts.append("handoff")

    components_line = ", ".join(comp_parts) if comp_parts else "(none)"
    targets_line = ", ".join(sorted(answers.agent_targets)) or "(none)"
    return "\n".join(
        [
            "Ready to generate:",
            f"  project name: {answers.project_name}",
            f"  target dir:   {answers.target_dir}",
            f"  upstream:     {pin.repo}@{pin.commit[:12]}",
            f"  components:   {components_line}",
            f"  agent targets: {targets_line}",
        ]
    )


def _prompt_project_name(asker: Asker) -> str:
    message = "Project name:"
    while True:
        try:
            name = asker.text(message)
        except KeyboardInterrupt:
            name = None
        if name is None:
            raise AbortedError("project name prompt cancelled")
        try:
            validate_project_name(name)
        except InvalidArgumentsError:
            pass
        else:
            return name
        message = (
            f"invalid project name {name!r}: use letters, digits, '.', '_', '-', "
            "starting with a letter or digit. Project name:"
        )


def _prompt_components(asker: Asker) -> tuple[bool, bool, bool, bool]:
    try:
        selected = asker.checkbox("Select components to include:", _COMPONENT_CHOICES)
    except KeyboardInterrupt:
        selected = None
    if selected is None:
        raise AbortedError("component selection prompt cancelled")
    selected_set = set(selected)
    return (
        "skills" in selected_set,
        "mcp" in selected_set,
        "docs" in selected_set,
        "handoff" in selected_set,
    )


def _prompt_items(asker: Asker, component: str, item_ids: Sequence[str]) -> frozenset[str]:
    try:
        selected = asker.checkbox(f"Select {component} items to include:", item_ids)
    except KeyboardInterrupt:
        selected = None
    if selected is None:
        raise AbortedError(f"{component} item selection cancelled")
    return frozenset(selected)


def _prompt_agent_targets(
    asker: Asker,
    catalog: Mapping[str, tuple[CatalogItem, ...]],
) -> frozenset[str]:
    targets = getattr(catalog, "agent_targets", {})
    if not targets:
        return frozenset()
    labels = {
        f"{target_id}: {target.description}": target_id
        for target_id, target in targets.items()
    }
    try:
        selected = asker.checkbox("Select Agent Targets:", tuple(labels))
    except KeyboardInterrupt:
        selected = None
    if selected is None:
        raise AbortedError("Agent Target selection cancelled")
    return frozenset(labels[label] for label in selected)
