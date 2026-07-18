"""Interactive/non-interactive collection of Answers, and pre-write confirmation.

`prompts` performs no I/O other than the terminal (docs/architecture.md).
questionary is imported lazily, only from `_default_asker`, so a caller that
always supplies its own `asker` (tests, or the `--yes` flag path in cli.py,
which never calls into this module at all) never triggers the import.
"""

import re
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

from dev_ready.errors import AbortedError, InvalidArgumentsError
from dev_ready.manifest import CatalogItem, UpstreamPin
from dev_ready.prompts.answers import Answers, PartialAnswers
from dev_ready.prompts.asker import Asker

__all__ = ["collect_answers", "confirm_generation"]

_PROJECT_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]*$")
_COMPONENT_CHOICES = ("skills", "mcp", "docs", "agents")


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
    needs_components = not partial.components_explicit

    if needs_name and asker is None and not _is_interactive():
        raise InvalidArgumentsError(
            "project name is required: dev-ready init <project-name> "
            "(or run in an interactive terminal to be prompted, or pass --yes)"
        )
    if needs_components and asker is None and not _is_interactive():
        raise InvalidArgumentsError(
            "component selection requires an interactive terminal — pass "
            "--no-skills/--no-mcp/--no-docs/--no-agents explicitly, or use --yes"
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
        skills_on, mcp_on, include_docs, include_agents = _prompt_components(resolved_asker)
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

            include_skills = bool(skills_items)
            include_mcp = bool(mcp_items)
        else:
            skills_items = frozenset()
            mcp_items = frozenset()
            include_skills = skills_on
            include_mcp = mcp_on
    else:
        skills_items = (
            partial.skills_selection if partial.skills_selection is not None else frozenset()
        )
        mcp_items = (
            partial.mcp_selection if partial.mcp_selection is not None else frozenset()
        )
        include_skills = (
            bool(skills_items)
            if partial.skills_selection is not None
            else partial.include_skills
        )
        include_mcp = (
            bool(mcp_items) if partial.mcp_selection is not None else partial.include_mcp
        )
        include_docs = partial.include_docs
        include_agents = partial.include_agents

    target_dir = (
        partial.target_dir if partial.target_dir is not None else Path.cwd() / project_name
    )

    return Answers(
        project_name=project_name,
        target_dir=target_dir,
        include_skills=include_skills,
        include_mcp=include_mcp,
        include_docs=include_docs,
        include_agents=include_agents,
        skills_items=skills_items,
        mcp_items=mcp_items,
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
    if answers.include_skills:
        skills_str = ", ".join(sorted(answers.skills_items)) if answers.skills_items else "(none)"
        comp_parts.append(f"skills ({skills_str})")
    if answers.include_mcp:
        mcp_str = ", ".join(sorted(answers.mcp_items)) if answers.mcp_items else "(none)"
        comp_parts.append(f"mcp ({mcp_str})")
    if answers.include_docs:
        comp_parts.append("docs")
    if answers.include_agents:
        comp_parts.append("agents")

    components_line = ", ".join(comp_parts) if comp_parts else "(none)"
    return "\n".join(
        [
            "Ready to generate:",
            f"  project name: {answers.project_name}",
            f"  target dir:   {answers.target_dir}",
            f"  upstream:     {pin.repo}@{pin.commit[:12]}",
            f"  components:   {components_line}",
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
        if _PROJECT_NAME_PATTERN.fullmatch(name):
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
        "agents" in selected_set,
    )


def _prompt_items(asker: Asker, component: str, item_ids: Sequence[str]) -> frozenset[str]:
    try:
        selected = asker.checkbox(f"Select {component} items to include:", item_ids)
    except KeyboardInterrupt:
        selected = None
    if selected is None:
        raise AbortedError(f"{component} item selection cancelled")
    return frozenset(selected)

