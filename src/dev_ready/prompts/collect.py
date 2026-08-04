"""Interactive/non-interactive collection of Answers, and pre-write confirmation.

`prompts` performs no I/O other than the terminal (docs/architecture.md).
questionary is imported lazily, only from `_default_asker`, so a caller that
always supplies its own `asker` (tests, or the `--yes` flag path in cli.py,
which never calls into this module at all) never triggers the import.
"""

import sys
from pathlib import Path

from dev_ready.errors import AbortedError, InvalidArgumentsError
from dev_ready.manifest import AgentTarget, ComponentCatalog, UpstreamPin
from dev_ready.prompts.answers import Answers, PartialAnswers, ProjectSelection, validate_project_name
from dev_ready.prompts.asker import Asker

__all__ = ["collect_answers", "confirm_generation"]

def _is_interactive() -> bool:
    return sys.stdin.isatty()


def _default_asker() -> Asker:
    from dev_ready.prompts._questionary_asker import QuestionaryAsker

    return QuestionaryAsker()


def collect_answers(
    partial: PartialAnswers,
    *,
    catalog: ComponentCatalog | None = None,
    asker: Asker | None = None,
) -> Answers:
    """Fill in whatever `partial` left unanswered, via `asker` (or a real
    terminal prompt by default), and return a complete `Answers`.

    Never blocks on a terminal that cannot answer: raises
    `InvalidArgumentsError` up front if a prompt would be needed but stdin
    is not a TTY (and no `asker` was injected).
    """
    needs_name = partial.project_name is None
    needs_selection = partial.selection is None

    if needs_name and asker is None and not _is_interactive():
        raise InvalidArgumentsError(
            "project name is required: dev-ready init <project-name> "
            "(or run in an interactive terminal to be prompted, or pass --yes)"
        )
    if needs_selection and asker is None and not _is_interactive():
        raise InvalidArgumentsError(
            "Category selection requires an interactive terminal — pass "
            "--categories with per-Category item flags, or use --yes"
        )

    resolved_asker = asker
    if (needs_name or needs_selection) and resolved_asker is None:
        resolved_asker = _default_asker()

    project_name = partial.project_name
    if needs_name:
        assert resolved_asker is not None
        project_name = _prompt_project_name(resolved_asker)

    if needs_selection:
        assert resolved_asker is not None
        if catalog is None:
            raise InvalidArgumentsError("catalog is required for Category selection")
        if _prompt_use_default_set(resolved_asker, catalog):
            base_selection = ProjectSelection.default_set(catalog)
            enhancements = _prompt_custom_selection(
                resolved_asker,
                catalog,
                development_loop=base_selection.development_loop,
            )
            base_selection = ProjectSelection.from_items(
                catalog,
                skills=base_selection.skills | enhancements.skills,
                mcp=base_selection.mcp | enhancements.mcp,
                docs_items=base_selection.docs_items | enhancements.docs_items,
                categories=base_selection.categories | enhancements.categories,
                agent_targets=frozenset(),
            )
        else:
            base_selection = _prompt_custom_selection(resolved_asker, catalog)
        agent_targets = _prompt_agent_targets(resolved_asker, catalog)
        selection = ProjectSelection.from_items(
            catalog,
            skills=base_selection.skills,
            mcp=base_selection.mcp,
            docs_items=base_selection.docs_items,
            categories=base_selection.categories,
            agent_targets=agent_targets,
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
    categories_line = ", ".join(sorted(answers.selection.categories)) or "(none)"
    selected_items = set().union(
        answers.items("skills"),
        answers.items("mcp"),
        answers.items("docs"),
    )
    items_line = ", ".join(sorted(selected_items)) or "(none)"
    targets_line = ", ".join(sorted(answers.agent_targets)) or "(none)"
    return "\n".join(
        [
            "Ready to generate:",
            f"  project name: {answers.project_name}",
            f"  target dir:   {answers.target_dir}",
            f"  upstream:     {pin.repo}@{pin.commit[:12]}",
            f"  categories:   {categories_line}",
            f"  selected items: {items_line}",
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


def _prompt_categories(
    asker: Asker,
    catalog: ComponentCatalog,
) -> frozenset[str]:
    categories = catalog.categories
    labels = {
        f"{category_id}: {category.description}": category_id
        for category_id, category in categories.items()
    }
    try:
        selected = asker.checkbox(
            "Select Categories to include:",
            tuple(labels),
            initially_selected=(),
        )
    except KeyboardInterrupt:
        selected = None
    if selected is None:
        raise AbortedError("Category selection prompt cancelled")
    selected_ids = frozenset(labels[label] for label in selected)
    return selected_ids | (frozenset({"dev"}) if "dev" in categories else frozenset())


def _prompt_category_items(
    asker: Asker,
    catalog: ComponentCatalog,
    selected_categories: frozenset[str],
) -> frozenset[str]:
    development_loop_ids = frozenset(catalog.development_loop_ids)
    labels = {
        f"{item.category}: {item.id} — {item.description}": item.id
        for item in catalog.all_items()
        if item.category in selected_categories and item.id not in development_loop_ids
    }
    try:
        selected = asker.checkbox(
            "Select items within the chosen Categories:",
            tuple(labels),
            initially_selected=(),
        )
    except KeyboardInterrupt:
        selected = None
    if selected is None:
        raise AbortedError("Category item selection cancelled")
    return frozenset(labels[label] for label in selected)


def _prompt_custom_selection(
    asker: Asker,
    catalog: ComponentCatalog,
    *,
    development_loop: str | None = None,
) -> ProjectSelection:
    resolved_loop = development_loop or _prompt_development_loop(asker, catalog)
    selected_categories = _prompt_categories(asker, catalog)
    selected_item_ids = _prompt_category_items(asker, catalog, selected_categories)
    selected_by_component = catalog.by_component(selected_item_ids)
    return ProjectSelection.from_items(
        catalog,
        skills=selected_by_component["skills"] | frozenset({resolved_loop}),
        mcp=selected_by_component["mcp"],
        docs_items=selected_by_component["docs"],
        categories=selected_categories,
        agent_targets=frozenset(),
    )


def _prompt_development_loop(
    asker: Asker,
    catalog: ComponentCatalog,
) -> str:
    loop_ids = catalog.development_loop_ids
    if not loop_ids:
        raise InvalidArgumentsError("catalog does not declare a development loop")
    if len(loop_ids) == 1:
        return loop_ids[0]
    default_loop = catalog.default_development_loop
    ordered_ids = (
        (default_loop, *tuple(loop_id for loop_id in loop_ids if loop_id != default_loop))
        if default_loop in loop_ids
        else loop_ids
    )
    items = {item.id: item for item in catalog.loops()}
    labels = {f"{loop_id}: {items[loop_id].description}": loop_id for loop_id in ordered_ids}
    try:
        selected = asker.select("Select one development loop:", tuple(labels))
    except KeyboardInterrupt:
        selected = None
    if selected is None:
        raise AbortedError("Development loop prompt cancelled")
    return labels[selected]


def _prompt_use_default_set(
    asker: Asker,
    catalog: ComponentCatalog,
) -> bool:
    default_set = catalog.default_set
    if default_set is None:
        raise InvalidArgumentsError("catalog does not declare a Default Set")
    try:
        selected = asker.confirm(
            f"Use the Default Set (development loop: {default_set.development_loop})?",
            default=True,
        )
    except KeyboardInterrupt:
        selected = None
    if selected is None:
        raise AbortedError("Default Set prompt cancelled")
    return selected


def _prompt_agent_targets(
    asker: Asker,
    catalog: ComponentCatalog,
) -> frozenset[str]:
    targets = catalog.agent_targets
    if not targets:
        return frozenset()
    labels = {_agent_target_label(target): target.id for target in targets.values()}
    message = "Select Agent Targets:"
    if catalog.standard_compliant_agents:
        agents_str = ", ".join(sorted(catalog.standard_compliant_agents))
        message = (
            f"Select Agent Targets (standard-compliant agents read .agents/skills/ directly "
            f"— no selection needed: {agents_str}):"
        )
    try:
        selected = asker.checkbox(
            message,
            tuple(labels),
            initially_selected=tuple(
                label
                for label, target_id in labels.items()
                if target_id in ProjectSelection.default_agent_targets(catalog)
            ),
        )
    except KeyboardInterrupt:
        selected = None
    if selected is None:
        raise AbortedError("Agent Target selection cancelled")
    return frozenset(labels[label] for label in selected)


def _agent_target_label(target: AgentTarget) -> str:
    paths = [f"skills {target.skills_dir}"]
    if target.rules_file is not None:
        paths.append(f"rules {target.rules_file}")
    if target.mcp_file is not None:
        paths.append(f"MCP {target.mcp_file}")
    return f"{target.id}: {'; '.join(paths)}"
