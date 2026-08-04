"""Unit tests for dev_ready.prompts (no network, no real TTY, tmp_path only)."""

from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path

import pytest

import dev_ready.prompts.collect as collect_module
import dev_ready.prompts._questionary_asker as questionary_asker_module
from dev_ready.errors import AbortedError, InvalidArgumentsError
from dev_ready.manifest import (
    AgentTarget,
    ComponentCatalog,
    ItemPath,
    UpstreamPin,
    load_default_manifest,
)
from dev_ready.prompts import (
    Answers,
    PartialAnswers,
    ProjectSelection,
    collect_answers,
    confirm_generation,
)

PIN = UpstreamPin(
    repo="fastapi/full-stack-fastapi-template",
    ref="master",
    commit="4cd0d9e51aebd1af6f82d91ad0df4c9e41f4dea2",
    license="MIT",
)
CATALOG = load_default_manifest().components


def _agent_target_label(target: AgentTarget) -> str:
    paths = [f"skills {target.skills_dir}"]
    if target.rules_file is not None:
        paths.append(f"rules {target.rules_file}")
    if target.mcp_file is not None:
        paths.append(f"MCP {target.mcp_file}")
    return f"{target.id}: {'; '.join(paths)}"


ALL_AGENT_LABELS = [
    _agent_target_label(target) for target in CATALOG.agent_targets.values()
]
CLAUDE_AGENT_LABELS = [_agent_target_label(CATALOG.agent_targets["claude"])]
ALL_CATEGORY_LABELS = [
    f"{category.id}: {category.description}"
    for category in CATALOG.categories.values()
]
ALL_ITEM_LABELS = [
    f"{item.category}: {item.id} — {item.description}"
    for items in CATALOG.values()
    for item in items
    if item.id not in CATALOG.development_loop_ids
]


def _catalog_with_second_loop() -> ComponentCatalog:
    current = next(
        item for item in CATALOG["skills"] if item.kind == "development-loop"
    )
    alternate = replace(
        current,
        id="alternate-loop",
        description="Alternate development method.",
        steps=("alternate-step",),
        paths=(
            ItemPath(
                src="claude/skills/alternate-loop",
                dest=".agents/skills/alternate-loop",
            ),
        ),
    )
    components = dict(CATALOG)
    components["skills"] = (*CATALOG["skills"], alternate)
    return ComponentCatalog(
        components,
        CATALOG.agent_targets,
        CATALOG.categories,
        CATALOG.default_set,
    )


def _item_labels(*item_ids: str) -> list[str]:
    requested = set(item_ids)
    return [
        label
        for label in ALL_ITEM_LABELS
        if label.split(": ", 1)[1].split(" — ", 1)[0] in requested
    ]


def _category_labels(*category_ids: str) -> list[str]:
    requested = set(category_ids)
    return [
        label for label in ALL_CATEGORY_LABELS if label.split(":", 1)[0] in requested
    ]


class FakeAsker:
    """Scripted Asker: pops one canned response per call, in call order."""

    def __init__(
        self,
        *,
        texts: list[str | None] | None = None,
        selects: list[str | None] | None = None,
        checkboxes: list[list[str] | None] | None = None,
        confirms: list[bool | None] | None = None,
    ) -> None:
        self._texts = list(texts or [])
        self._selects = list(selects or [])
        self._checkboxes = list(checkboxes or [])
        self._confirms = list(confirms or [])
        self.text_calls: list[str] = []
        self.select_calls: list[str] = []
        self.select_choices: list[list[str]] = []
        self.checkbox_calls: list[str] = []
        self.checkbox_choices: list[list[str]] = []
        self.checkbox_initially_selected: list[list[str]] = []
        self.confirm_calls: list[str] = []

    def text(self, message: str) -> str | None:
        self.text_calls.append(message)
        return self._texts.pop(0)

    def select(self, message: str, choices: Sequence[str]) -> str | None:
        self.select_calls.append(message)
        self.select_choices.append(list(choices))
        return self._selects.pop(0)

    def checkbox(
        self,
        message: str,
        choices: Sequence[str],
        *,
        initially_selected: Sequence[str],
    ) -> list[str] | None:
        self.checkbox_calls.append(message)
        self.checkbox_choices.append(list(choices))
        self.checkbox_initially_selected.append(list(initially_selected))
        return self._checkboxes.pop(0)

    def confirm(self, message: str, *, default: bool = True) -> bool | None:
        self.confirm_calls.append(message)
        return self._confirms.pop(0)


class _RaisingAsker:
    """An Asker where every method raises KeyboardInterrupt."""

    def text(self, message: str) -> str | None:
        raise KeyboardInterrupt

    def select(self, message: str, choices: Sequence[str]) -> str | None:
        raise KeyboardInterrupt

    def checkbox(
        self,
        message: str,
        choices: Sequence[str],
        *,
        initially_selected: Sequence[str],
    ) -> list[str] | None:
        raise KeyboardInterrupt

    def confirm(self, message: str, *, default: bool = True) -> bool | None:
        raise KeyboardInterrupt


def _partial(
    *,
    project_name: str | None = "my-app",
    target_dir: Path | None = None,
    selection_explicit: bool = True,
    selection: ProjectSelection | None = None,
    assume_yes: bool = False,
) -> PartialAnswers:
    if selection_explicit and selection is None:
        selection = ProjectSelection.from_items(
            CATALOG,
            skills=frozenset({"caveman"}),
            mcp=frozenset({"code-memory"}),
        )
    if not selection_explicit:
        selection = None
    return PartialAnswers(
        project_name=project_name,
        target_dir=target_dir,
        selection=selection,
        assume_yes=assume_yes,
    )



def _answers(
    *,
    project_name: str = "my-app",
    selection: ProjectSelection | None = None,
) -> Answers:
    return Answers(
        project_name=project_name,
        target_dir=Path("/does/not/exist/my-app"),
        selection=selection
        or ProjectSelection.from_items(
            CATALOG,
            skills=frozenset({"caveman"}),
            mcp=frozenset({"code-memory"}),
        ),
    )



# --- name prompt ---


def test_name_prompt_fires_only_when_argument_missing() -> None:
    asker = FakeAsker(texts=["should-not-be-used"])
    answers = collect_answers(_partial(project_name="given-name"), asker=asker)
    assert answers.project_name == "given-name"
    assert asker.text_calls == []


def test_name_prompt_reasks_on_invalid_input() -> None:
    asker = FakeAsker(texts=["bad name!", "good-name"])
    answers = collect_answers(_partial(project_name=None), asker=asker)
    assert answers.project_name == "good-name"
    assert len(asker.text_calls) == 2


def test_name_prompt_result_lands_in_answers() -> None:
    asker = FakeAsker(texts=["prompted-name"])
    answers = collect_answers(_partial(project_name=None), asker=asker)
    assert answers.project_name == "prompted-name"


# --- Category prompt ---


def test_interactive_defaults_produce_default_set_without_enhancement_selection() -> None:
    asker = FakeAsker(confirms=[True], checkboxes=[[], [], CLAUDE_AGENT_LABELS])

    answers = collect_answers(
        _partial(selection_explicit=False), catalog=CATALOG, asker=asker
    )

    assert answers.selection.categories == frozenset({"dev"})
    assert answers.skills_items == frozenset({"spec-loop"})
    assert answers.mcp_items == frozenset()
    assert answers.include_docs is False
    assert answers.items("docs") == frozenset()
    assert asker.confirm_calls == [
        "Use the Default Set (development loop: spec-loop)?",
    ]
    assert asker.checkbox_calls[0] == "Select Categories to include:"
    assert asker.checkbox_calls[1] == "Select items within the chosen Categories:"
    assert asker.checkbox_calls[2].startswith(
        "Select Agent Targets (standard-compliant agents read .agents/skills/ directly"
    )
    assert "cursor" in asker.checkbox_calls[2]
    assert answers.agent_targets == frozenset({"claude"})
    assert answers.selection == ProjectSelection.default_set(CATALOG)
    assert asker.checkbox_initially_selected == [[], [], CLAUDE_AGENT_LABELS]


def test_interactive_custom_branch_preselects_the_same_agent_as_default_set() -> None:
    asker = FakeAsker(confirms=[False], checkboxes=[[], [], CLAUDE_AGENT_LABELS])

    answers = collect_answers(
        _partial(selection_explicit=False), catalog=CATALOG, asker=asker
    )

    assert answers.agent_targets == ProjectSelection.default_set(CATALOG).agent_targets
    assert asker.checkbox_initially_selected[-1] == CLAUDE_AGENT_LABELS


def test_interactive_default_set_can_add_one_enhancement() -> None:
    asker = FakeAsker(
        confirms=[True],
        checkboxes=[
            _category_labels("security"),
            _item_labels("security-audit"),
            ALL_AGENT_LABELS,
        ],
    )

    answers = collect_answers(
        _partial(selection_explicit=False), catalog=CATALOG, asker=asker
    )

    assert answers.selection.development_loop == "spec-loop"
    assert answers.skills_items == frozenset({"security-audit", "spec-loop"})
    assert answers.include_docs is False
    assert asker.confirm_calls == [
        "Use the Default Set (development loop: spec-loop)?",
    ]


def test_interactive_customization_can_choose_an_alternate_loop() -> None:
    catalog = _catalog_with_second_loop()
    asker = FakeAsker(
        confirms=[False],
        selects=["alternate-loop: Alternate development method."],
        checkboxes=[[], [], ALL_AGENT_LABELS],
    )

    answers = collect_answers(
        _partial(selection_explicit=False), catalog=catalog, asker=asker
    )

    assert answers.selection.development_loop == "alternate-loop"
    assert answers.skills_items == frozenset({"alternate-loop"})
    assert asker.select_calls == ["Select one development loop:"]


def test_category_prompt_skipped_when_flags_resolved_selection() -> None:
    asker = FakeAsker(checkboxes=[ALL_CATEGORY_LABELS])
    answers = collect_answers(
        _partial(
            selection=ProjectSelection.from_items(
                CATALOG,
                mcp=frozenset({"code-memory"}),
            ),
        ),
        asker=asker,
    )

    assert answers.selection.development_loop == "spec-loop"
    assert answers.include_skills is True
    assert asker.checkbox_calls == []


def test_category_and_item_choices_resolve_across_components() -> None:
    asker = FakeAsker(
        confirms=[False],
        checkboxes=[
            _category_labels("token-optimize"),
            _item_labels("caveman", "code-memory"),
            ALL_AGENT_LABELS,
        ]
    )

    answers = collect_answers(
        _partial(selection_explicit=False), catalog=CATALOG, asker=asker
    )

    assert answers.skills_items == frozenset(
        {"caveman", "spec-loop"}
    )
    assert answers.mcp_items == frozenset({"code-memory"})
    assert answers.include_docs is False


def test_empty_category_selection_produces_no_catalog_content() -> None:
    asker = FakeAsker(confirms=[False], checkboxes=[[], [], ALL_AGENT_LABELS])

    answers = collect_answers(
        _partial(selection_explicit=False), catalog=CATALOG, asker=asker
    )

    assert answers.skills_items == frozenset(
        {"spec-loop"}
    )
    assert answers.mcp_items == frozenset()
    assert answers.include_docs is False
    assert answers.selection.development_loop == "spec-loop"
    assert answers.selection.categories == frozenset({"dev"})
    assert asker.checkbox_initially_selected == [[], [], CLAUDE_AGENT_LABELS]


def test_interactive_agent_targets_remain_last_and_are_resolved() -> None:
    asker = FakeAsker(
        confirms=[False],
        checkboxes=[
            _category_labels("design"),
            _item_labels("frontend-design"),
            ["windsurf: skills .windsurf/skills"],
        ]
    )

    answers = collect_answers(
        _partial(selection_explicit=False), catalog=CATALOG, asker=asker
    )

    assert answers.agent_targets == frozenset({"windsurf"})
    assert asker.checkbox_calls[-1].startswith(
        "Select Agent Targets (standard-compliant agents read .agents/skills/ directly"
    )
    assert asker.checkbox_choices[-1] == ALL_AGENT_LABELS


def test_questionary_checkboxes_enable_type_to_filter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    class _Question:
        def ask(self) -> list[str]:
            return []

    def _checkbox(message: str, choices: list[object], **kwargs: object) -> _Question:
        captured.update(message=message, choices=choices, **kwargs)
        return _Question()

    monkeypatch.setattr(questionary_asker_module.questionary, "checkbox", _checkbox)

    questionary_asker_module.QuestionaryAsker().checkbox(
        "Select choices:",
        ["alpha", "beta"],
        initially_selected=["alpha"],
    )

    assert captured["use_search_filter"] is True


def test_category_item_selection_can_be_narrowed_to_one_item() -> None:
    asker = FakeAsker(
        confirms=[False],
        checkboxes=[
            _category_labels("quality"),
            _item_labels("react-doctor"),
            ALL_AGENT_LABELS,
        ]
    )

    answers = collect_answers(
        _partial(selection_explicit=False), catalog=CATALOG, asker=asker
    )

    assert answers.skills_items == frozenset(
        {"react-doctor", "spec-loop"}
    )
    assert answers.mcp_items == frozenset()


def test_category_prompt_cancel_raises_aborted() -> None:
    with pytest.raises(AbortedError, match="Category selection prompt cancelled"):
        collect_answers(
            _partial(selection_explicit=False),
            catalog=CATALOG,
            asker=FakeAsker(confirms=[False], checkboxes=[None]),
        )


def test_category_item_prompt_cancel_raises_aborted() -> None:
    asker = FakeAsker(
        confirms=[False], checkboxes=[_category_labels("dev"), None]
    )

    with pytest.raises(AbortedError, match="Category item selection cancelled"):
        collect_answers(
            _partial(selection_explicit=False), catalog=CATALOG, asker=asker
        )


def test_flags_explicit_path_no_prompts() -> None:
    partial = _partial(
        selection=ProjectSelection.from_items(
            CATALOG,
            skills=frozenset({"caveman"}),
        ),
    )
    asker = FakeAsker()

    answers = collect_answers(partial, catalog=CATALOG, asker=asker)

    assert answers.skills_items == frozenset(
        {"caveman", "spec-loop"}
    )
    assert answers.mcp_items == frozenset()
    assert len(asker.checkbox_calls) == 0


# --- cancellation during collect_answers ---


def test_name_prompt_cancel_raises_aborted() -> None:
    asker = FakeAsker(texts=[None])
    with pytest.raises(AbortedError):
        collect_answers(_partial(project_name=None), asker=asker)


def test_category_prompt_keyboard_interrupt_raises_aborted() -> None:
    with pytest.raises(AbortedError):
        collect_answers(
            _partial(selection_explicit=False),
            catalog=CATALOG,
            asker=_RaisingAsker(),
        )


def test_name_prompt_keyboard_interrupt_raises_aborted() -> None:
    with pytest.raises(AbortedError):
        collect_answers(_partial(project_name=None), asker=_RaisingAsker())


# --- non-TTY guard ---


def test_non_tty_missing_name_raises_invalid_arguments(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(collect_module, "_is_interactive", lambda: False)
    with pytest.raises(InvalidArgumentsError) as excinfo:
        collect_answers(_partial(project_name=None))
    assert "project name is required" in str(excinfo.value)


def test_non_tty_missing_category_selection_raises_invalid_arguments(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(collect_module, "_is_interactive", lambda: False)
    with pytest.raises(InvalidArgumentsError) as excinfo:
        collect_answers(_partial(selection_explicit=False))
    assert "Category selection requires an interactive terminal" in str(excinfo.value)
    assert "--categories" in str(excinfo.value)


# --- interactive/flag path convergence (ADR-004) ---


def test_interactive_and_flag_paths_produce_identical_answers(tmp_path: Path) -> None:
    """build_answers (flags) and collect_answers (prompts, answers pre-supplied via
    FakeAsker) must construct an equal Answers for equivalent inputs — the two
    paths share one Answers model by construction (ADR-004)."""
    target_dir = tmp_path / "my-app"

    flag_answers = Answers(
        project_name="my-app",
        target_dir=target_dir,
            selection=ProjectSelection.from_items(
                CATALOG,
                mcp=frozenset({"code-memory"}),
                categories=frozenset({"token-optimize"}),
                agent_targets=frozenset({"claude"}),
            ),
        assume_yes=False,
    )

    asker = FakeAsker(
        texts=["my-app"],
        confirms=[False],
        checkboxes=[
                _category_labels("token-optimize"),
                _item_labels("code-memory"),
                CLAUDE_AGENT_LABELS,
        ],
    )
    prompt_answers = collect_answers(
        _partial(
            project_name=None,
            target_dir=target_dir,
            selection_explicit=False,
        ),
        catalog=CATALOG,
        asker=asker,
    )

    assert flag_answers == prompt_answers


def test_design_skill_only_is_identical_through_flags_and_prompts(tmp_path: Path) -> None:
    target_dir = tmp_path / "design-app"
    flag_selection = ProjectSelection.from_flags(
        catalog=CATALOG,
        categories="design",
        category_items={"design": "frontend-design"},
    )
    assert flag_selection is not None
    flag_answers = Answers(
        project_name="design-app",
        target_dir=target_dir,
        selection=flag_selection,
    )

    prompt_answers = collect_answers(
        _partial(
            project_name="design-app",
            target_dir=target_dir,
            selection_explicit=False,
        ),
        catalog=CATALOG,
        asker=FakeAsker(
            confirms=[False],
            checkboxes=[
                _category_labels("design"),
                _item_labels("frontend-design"),
                CLAUDE_AGENT_LABELS,
            ]
        ),
    )

    assert flag_answers == prompt_answers
    assert flag_answers.includes("docs") is False


def test_non_tty_with_asker_injected_still_prompts(monkeypatch: pytest.MonkeyPatch) -> None:
    """An injected asker (as tests use) means a real TTY isn't required."""
    monkeypatch.setattr(collect_module, "_is_interactive", lambda: False)
    asker = FakeAsker(texts=["given-name"])
    answers = collect_answers(_partial(project_name=None), asker=asker)
    assert answers.project_name == "given-name"


# --- target_dir resolution ---


def test_target_dir_defaults_to_cwd_over_project_name(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    answers = collect_answers(_partial(project_name="my-app", target_dir=None))
    assert answers.target_dir == tmp_path / "my-app"


def test_target_dir_uses_partial_value_when_given(tmp_path: Path) -> None:
    target = tmp_path / "custom"
    answers = collect_answers(_partial(project_name="my-app", target_dir=target))
    assert answers.target_dir == target


# --- collect_answers avoids the default asker (and questionary) when unneeded ---


def test_collect_answers_never_constructs_default_asker_when_nothing_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _boom() -> None:
        raise AssertionError("_default_asker should not be called")

    monkeypatch.setattr(collect_module, "_default_asker", _boom)
    collect_answers(_partial(project_name="my-app", selection_explicit=True))


# --- confirmation ---


def test_confirm_accept_returns_true() -> None:
    asker = FakeAsker(confirms=[True])
    assert confirm_generation(_answers(), PIN, asker=asker) is True


def test_confirm_decline_returns_false() -> None:
    asker = FakeAsker(confirms=[False])
    assert confirm_generation(_answers(), PIN, asker=asker) is False


def test_confirm_cancel_via_none_returns_false() -> None:
    asker = FakeAsker(confirms=[None])
    assert confirm_generation(_answers(), PIN, asker=asker) is False


def test_confirm_keyboard_interrupt_returns_false() -> None:
    assert confirm_generation(_answers(), PIN, asker=_RaisingAsker()) is False


def test_confirm_prints_summary_with_project_name_and_pin(capsys: pytest.CaptureFixture) -> None:
    asker = FakeAsker(confirms=[True])
    confirm_generation(_answers(project_name="my-app"), PIN, asker=asker)
    out = capsys.readouterr().out
    assert "my-app" in out
    assert PIN.repo in out


def test_confirm_non_tty_without_injected_asker_raises_invalid_arguments(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(collect_module, "_is_interactive", lambda: False)
    with pytest.raises(InvalidArgumentsError):
        confirm_generation(_answers(), PIN)


def test_render_confirmation_summary_omits_removed_handoff() -> None:
    from dev_ready.prompts.collect import _render_confirmation_summary

    summary = _render_confirmation_summary(_answers(), PIN)

    assert "handoff" not in summary


def test_render_confirmation_summary_names_categories_and_items() -> None:
    from dev_ready.prompts.collect import _render_confirmation_summary

    summary = _render_confirmation_summary(_answers(), PIN)

    assert "categories:" in summary
    assert "token-optimize" in summary
    assert "selected items:" in summary
    assert "caveman" in summary
    assert "code-memory" in summary
    assert "components:" not in summary


def test_render_confirmation_summary_includes_resolved_agent_targets() -> None:
    from dev_ready.prompts.collect import _render_confirmation_summary

    summary = _render_confirmation_summary(
        _answers(
            selection=ProjectSelection.from_items(
                CATALOG,
                agent_targets=frozenset({"windsurf"}),
            )
        ),
        PIN,
    )

    assert "agent targets: windsurf" in summary
