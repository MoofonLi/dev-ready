"""Interactive/non-interactive collection of Answers, and pre-write confirmation.

`prompts` performs no I/O other than the terminal (docs/architecture.md).
questionary is imported lazily, only from `_default_asker`, so a caller that
never needs an asker does not trigger the import. The `--yes` path passes
complete intent through this module but never constructs an asker.
"""

import sys
from pathlib import Path

from dev_ready.errors import AbortedError, InvalidArgumentsError
from dev_ready.manifest import AgentTarget, CatalogItem, ComponentCatalog, UpstreamPin
from dev_ready.presentation import PresentationStyle, ScreenBlock, ScreenLine, render_screen
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
    style: PresentationStyle = PresentationStyle(),
) -> Answers:
    """Fill in whatever `partial` left unanswered, via `asker` (or a real
    terminal prompt by default), and return a complete `Answers`.

    Never blocks on a terminal that cannot answer: raises
    `InvalidArgumentsError` up front if a prompt would be needed but stdin
    is not a TTY (and no `asker` was injected).
    """
    project_name = partial.project_name
    invalid_destination_name: str | None = None
    if project_name is None and partial.target_dir is not None:
        candidate = partial.target_dir.name
        try:
            validate_project_name(candidate)
        except InvalidArgumentsError:
            invalid_destination_name = candidate
        else:
            project_name = candidate

    needs_name = project_name is None
    needs_selection = partial.selection is None

    if needs_name and partial.assume_yes:
        if invalid_destination_name is not None:
            validate_project_name(invalid_destination_name)
        raise InvalidArgumentsError(
            "project name is required: dev-ready init <project-name> or --dir <path>"
        )
    if needs_name and asker is None and not _is_interactive():
        if invalid_destination_name is not None:
            validate_project_name(invalid_destination_name)
        raise InvalidArgumentsError(
            "project name is required: dev-ready init <project-name> "
            "(or run in an interactive terminal to be prompted, or pass --yes)"
        )
    if needs_selection and asker is None and not _is_interactive():
        raise InvalidArgumentsError(
            "Engineering Flow and Category selection require an interactive terminal — pass "
            "--categories with per-Category item flags, or use --yes"
        )

    resolved_asker = asker
    if (needs_name or needs_selection) and resolved_asker is None:
        resolved_asker = _default_asker()

    if needs_name:
        assert resolved_asker is not None
        project_name = _prompt_project_name(
            resolved_asker,
            invalid_name=invalid_destination_name,
        )

    if needs_selection:
        assert resolved_asker is not None
        if catalog is None:
            raise InvalidArgumentsError("catalog is required for Category selection")
        development_loop = _prompt_development_loop(resolved_asker, catalog, style)
        selected_item_ids = frozenset().union(
            *(
                _prompt_category_items(resolved_asker, catalog, category_id)
                for category_id in catalog.categories
                if category_id != "dev"
            )
        )
        selected_by_component = catalog.by_component(selected_item_ids)
        agent_targets = (
            partial.agent_targets
            if partial.agent_targets is not None
            else _prompt_agent_targets(resolved_asker, catalog)
        )
        selection = ProjectSelection.from_items(
            catalog,
            skills=selected_by_component["skills"] | frozenset({development_loop}),
            mcp=selected_by_component["mcp"],
            docs_items=selected_by_component["docs"],
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
    answers: Answers,
    pin: UpstreamPin,
    *,
    asker: Asker | None = None,
    style: PresentationStyle = PresentationStyle(),
    occupied_entry_count: int = 0,
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
    print(
        _render_confirmation_summary(
            answers,
            pin,
            style=style,
            occupied_entry_count=occupied_entry_count,
        )
    )
    try:
        confirmed = resolved_asker.confirm("Proceed?", default=True)
    except KeyboardInterrupt:
        confirmed = None
    return bool(confirmed)


def _render_confirmation_summary(
    answers: Answers,
    pin: UpstreamPin,
    *,
    style: PresentationStyle = PresentationStyle(),
    occupied_entry_count: int = 0,
) -> str:
    categories_line = ", ".join(sorted(answers.selection.categories)) or "(none)"
    selected_items = set().union(
        answers.items("skills"),
        answers.items("mcp"),
        answers.items("docs"),
    )
    items_line = ", ".join(sorted(selected_items)) or "(none)"
    targets_line = ", ".join(sorted(answers.agent_targets)) or "(none)"
    lines = [
        ScreenLine(f"  project name: {answers.project_name}"),
        ScreenLine(f"  target dir:   {answers.target_dir}", wrap=False),
    ]
    if occupied_entry_count:
        noun = "entry" if occupied_entry_count == 1 else "entries"
        lines.append(
            ScreenLine(
                f"  occupancy:    {answers.target_dir} already contains "
                f"{occupied_entry_count} pre-existing top-level {noun} "
                "that will be left in place",
                wrap=False,
            )
        )
    lines.extend(
        (
            ScreenLine(f"  upstream:     {pin.repo}@{pin.commit[:12]}"),
            ScreenLine(f"  engineering flow: {answers.selection.development_loop}"),
            ScreenLine(f"  categories:   {categories_line}"),
            ScreenLine(f"  selected items: {items_line}"),
            ScreenLine(f"  agent targets: {targets_line}"),
        )
    )
    return render_screen(
        (
            ScreenBlock(
                heading="Ready to generate:",
                lines=tuple(lines),
            ),
        ),
        style=style,
    )


def _flow_caption(item: CatalogItem) -> str:
    return f"{item.display_name} — {item.description}"


def _render_flow_comparison(
    catalog: ComponentCatalog,
    *,
    style: PresentationStyle = PresentationStyle(),
) -> str:
    comparison = tuple(
        ScreenBlock(
            heading=_flow_caption(item),
            lines=tuple(ScreenLine(f"  - {criterion}") for criterion in item.choose_when),
        )
        for item in catalog.loops()
    )
    return render_screen(comparison, style=style)


def _prompt_project_name(asker: Asker, *, invalid_name: str | None = None) -> str:
    message = (
        f"invalid project name {invalid_name!r}: use letters, digits, '.', '_', '-', "
        "starting with a letter or digit. Project name:"
        if invalid_name is not None
        else "Project name:"
    )
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


def _prompt_category_items(
    asker: Asker,
    catalog: ComponentCatalog,
    category_id: str,
) -> frozenset[str]:
    labels = {
        f"{item.id} — {item.description}": item.id
        for item in catalog.all_items()
        if item.category == category_id
    }
    category_name = category_id.replace("-", " ").title()
    try:
        selected = asker.checkbox(
            f"Select {category_name} items:",
            tuple(labels),
            initially_selected=(),
        )
    except KeyboardInterrupt:
        selected = None
    if selected is None:
        raise AbortedError(f"{category_name} item selection prompt cancelled")
    return frozenset(labels[label] for label in selected)


def _prompt_development_loop(
    asker: Asker,
    catalog: ComponentCatalog,
    style: PresentationStyle,
) -> str:
    loop_ids = catalog.development_loop_ids
    if not loop_ids:
        raise InvalidArgumentsError("catalog does not declare a development loop")
    default_loop = catalog.default_development_loop
    ordered_ids = (
        (default_loop, *tuple(loop_id for loop_id in loop_ids if loop_id != default_loop))
        if default_loop in loop_ids
        else loop_ids
    )
    items = {item.id: item for item in catalog.loops()}
    labels = {_flow_caption(items[loop_id]): loop_id for loop_id in ordered_ids}
    announced_labels = tuple(
        f"{item.display_name} — Not yet available"
        for item in catalog.announced_loops
    )
    print(_render_flow_comparison(catalog, style=style))
    try:
        selected = asker.select(
            "Select an Engineering Flow:",
            (*tuple(labels), *announced_labels),
            disabled_choices=announced_labels,
        )
    except KeyboardInterrupt:
        selected = None
    if selected is None:
        raise AbortedError("Engineering Flow prompt cancelled")
    return labels[selected]


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
