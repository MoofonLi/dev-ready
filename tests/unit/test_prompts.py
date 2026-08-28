"""Unit tests for dev_ready.prompts (no network, no real TTY, tmp_path only)."""

from collections.abc import Callable, Sequence
from dataclasses import replace
from pathlib import Path
import re
from typing import TypeVar

import pytest
from prompt_toolkit.application import create_app_session
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput

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
from dev_ready.prompts._questionary_asker import QuestionaryAsker
from dev_ready.presentation import PresentationStyle
from dev_ready.overlay import render_stamp

PIN = UpstreamPin(
    repo="fastapi/full-stack-fastapi-template",
    ref="master",
    commit="4cd0d9e51aebd1af6f82d91ad0df4c9e41f4dea2",
    license="MIT",
)
CATALOG = load_default_manifest().components
_ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*m")


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
ALL_ITEM_LABELS = [
    f"{item.id} — {item.description}"
    for items in CATALOG.values()
    for item in items
    if item.id not in CATALOG.development_loop_ids
]
SELECTABLE_FLOW_LABELS = [
    f"{item.display_name} — {item.description}" for item in CATALOG.loops()
]
SELECTABLE_FLOW_LABEL = SELECTABLE_FLOW_LABELS[0]
ANNOUNCED_FLOW_LABELS = [
    f"{item.display_name} — Not yet available"
    for item in CATALOG.announced_loops
]
CATEGORY_PROMPTS = [
    "Select Security items:",
    "Select Quality items:",
    "Select Design items:",
    "Select Token Optimize items:",
]
AGENT_TARGET_PROMPT = (
    "Select Agent Targets (standard-compliant agents read .agents/skills/ directly "
    "— no selection needed: amp, antigravity, antigravity-cli, cline, codex, cursor, "
    "deepagents, dexto, firebender, gemini-cli, github-copilot, kimi-code-cli, loaf, "
    "opencode, promptscript, replit, universal, warp, zed):"
)


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
        if label.split(" — ", 1)[0] in requested
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
        self.select_disabled_choices: list[list[str]] = []
        self.checkbox_calls: list[str] = []
        self.checkbox_choices: list[list[str]] = []
        self.checkbox_initially_selected: list[list[str]] = []
        self.confirm_calls: list[str] = []
        self.events: list[str] = []

    def text(self, message: str) -> str | None:
        self.events.append(message)
        self.text_calls.append(message)
        return self._texts.pop(0)

    def select(
        self,
        message: str,
        choices: Sequence[str],
        *,
        disabled_choices: Sequence[str],
    ) -> str | None:
        self.events.append(message)
        self.select_calls.append(message)
        self.select_choices.append(list(choices))
        self.select_disabled_choices.append(list(disabled_choices))
        return self._selects.pop(0)

    def checkbox(
        self,
        message: str,
        choices: Sequence[str],
        *,
        initially_selected: Sequence[str],
    ) -> list[str] | None:
        self.events.append(message)
        self.checkbox_calls.append(message)
        self.checkbox_choices.append(list(choices))
        self.checkbox_initially_selected.append(list(initially_selected))
        return self._checkboxes.pop(0)

    def confirm(self, message: str, *, default: bool = True) -> bool | None:
        self.events.append(message)
        self.confirm_calls.append(message)
        return self._confirms.pop(0)


class _RaisingAsker:
    """An Asker where every method raises KeyboardInterrupt."""

    def text(self, message: str) -> str | None:
        raise KeyboardInterrupt

    def select(
        self,
        message: str,
        choices: Sequence[str],
        *,
        disabled_choices: Sequence[str],
    ) -> str | None:
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


def test_interactive_sequence_discloses_flow_then_walks_every_category() -> None:
    asker = FakeAsker(
        texts=["my-app"],
        selects=[SELECTABLE_FLOW_LABEL],
        checkboxes=[[], [], [], [], CLAUDE_AGENT_LABELS],
        confirms=[True],
    )

    answers = collect_answers(
        _partial(project_name=None, selection_explicit=False),
        catalog=CATALOG,
        asker=asker,
    )
    assert confirm_generation(answers, PIN, asker=asker) is True

    assert asker.events == [
        "Project name:",
        "Select an Engineering Flow:",
        *CATEGORY_PROMPTS,
        AGENT_TARGET_PROMPT,
        "Proceed?",
    ]
    assert answers.selection == ProjectSelection.default_set(CATALOG)
    assert asker.checkbox_initially_selected[:4] == [[], [], [], []]


def test_flow_prompt_lists_announced_flows_as_disabled_choices() -> None:
    asker = FakeAsker(
        selects=[SELECTABLE_FLOW_LABEL],
        checkboxes=[[], [], [], [], CLAUDE_AGENT_LABELS],
    )

    answers = collect_answers(
        _partial(selection_explicit=False), catalog=CATALOG, asker=asker
    )

    assert asker.select_choices == [
        [*SELECTABLE_FLOW_LABELS, *ANNOUNCED_FLOW_LABELS]
    ]
    assert asker.select_disabled_choices == [ANNOUNCED_FLOW_LABELS]
    reasons = [label.rsplit(" — ", 1)[1] for label in ANNOUNCED_FLOW_LABELS]
    assert reasons == ["Not yet available"] * len(ANNOUNCED_FLOW_LABELS)
    assert all(not any(character.isdigit() for character in reason) for reason in reasons)
    assert answers.selection.development_loop == "mattpocock"
    assert answers.selection.development_loop not in {
        item.id for item in CATALOG.announced_loops
    }


def test_flow_prompt_prints_declared_criteria_but_no_announced_flow(
    capsys: pytest.CaptureFixture[str],
) -> None:
    collect_answers(
        _partial(selection_explicit=False),
        catalog=CATALOG,
        asker=FakeAsker(
            selects=[SELECTABLE_FLOW_LABEL],
            checkboxes=[[], [], [], [], CLAUDE_AGENT_LABELS],
        ),
        style=PresentationStyle(),
    )
    comparison = capsys.readouterr().out
    collect_answers(
        _partial(selection_explicit=False),
        catalog=CATALOG,
        asker=FakeAsker(
            selects=[SELECTABLE_FLOW_LABEL],
            checkboxes=[[], [], [], [], CLAUDE_AGENT_LABELS],
        ),
        style=PresentationStyle(color=True, width=80),
    )
    coloured_comparison = capsys.readouterr().out
    normalized_comparison = " ".join(comparison.split())

    assert "\x1b" not in comparison
    assert "\x1b" in coloured_comparison
    assert _ANSI_ESCAPE.sub("", coloured_comparison) == comparison
    for flow in CATALOG.loops():
        assert flow.display_name in normalized_comparison
        assert all(
            " ".join(criterion.split()) in normalized_comparison
            for criterion in flow.choose_when
        )
    assert all(
        flow.display_name not in normalized_comparison
        for flow in CATALOG.announced_loops
    )


def test_flow_comparison_is_absent_when_selection_was_resolved_by_flags(
    capsys: pytest.CaptureFixture[str],
) -> None:
    collect_answers(
        _partial(selection=ProjectSelection.default_set(CATALOG)),
        catalog=CATALOG,
        asker=FakeAsker(),
        style=PresentationStyle(color=True, width=80),
    )

    assert capsys.readouterr().out == ""


def test_interactive_selects_superpowers_flow() -> None:
    superpowers_label = next(
        f"{item.display_name} — {item.description}"
        for item in CATALOG.loops()
        if item.id == "superpowers"
    )
    asker = FakeAsker(
        selects=[superpowers_label],
        checkboxes=[[], [], [], [], CLAUDE_AGENT_LABELS],
    )

    answers = collect_answers(
        _partial(selection_explicit=False), catalog=CATALOG, asker=asker
    )

    assert answers.selection.development_loop == "superpowers"
    assert "superpowers" in answers.skills_items
    assert "mattpocock" not in answers.skills_items



def test_all_enter_interview_and_accept_defaults_render_identical_stamps(
    tmp_path: Path,
) -> None:
    target_dir = tmp_path / "my-app"
    prompted = collect_answers(
        _partial(
            target_dir=target_dir,
            selection_explicit=False,
        ),
        catalog=CATALOG,
        asker=FakeAsker(
            selects=[SELECTABLE_FLOW_LABEL],
            checkboxes=[[], [], [], [], CLAUDE_AGENT_LABELS],
        ),
    )
    defaults = Answers(
        project_name="my-app",
        target_dir=target_dir,
        selection=ProjectSelection.default_set(CATALOG),
        assume_yes=True,
    )

    assert prompted.selection == defaults.selection
    assert render_stamp(prompted, PIN, CATALOG) == render_stamp(
        defaults, PIN, CATALOG
    )


def test_interactive_walk_can_add_one_enhancement() -> None:
    asker = FakeAsker(
        selects=[SELECTABLE_FLOW_LABEL],
        checkboxes=[
            _item_labels("security-audit"),
            [],
            [],
            [],
            CLAUDE_AGENT_LABELS,
        ],
    )

    answers = collect_answers(
        _partial(selection_explicit=False), catalog=CATALOG, asker=asker
    )

    assert answers.selection.development_loop == "mattpocock"
    assert answers.skills_items == frozenset({"security-audit", "mattpocock"})
    assert answers.include_docs is False
    assert answers.selection.categories == frozenset({"dev", "security"})


def test_interactive_customization_can_choose_an_alternate_loop() -> None:
    catalog = _catalog_with_second_loop()
    alternate_label = next(
        f"{item.display_name} — {item.description}"
        for item in catalog.loops()
        if item.id == "alternate-loop"
    )
    asker = FakeAsker(
        selects=[alternate_label],
        checkboxes=[[], [], [], [], ALL_AGENT_LABELS],
    )

    answers = collect_answers(
        _partial(selection_explicit=False), catalog=catalog, asker=asker
    )

    assert answers.selection.development_loop == "alternate-loop"
    assert answers.skills_items == frozenset({"alternate-loop"})
    assert asker.select_calls == ["Select an Engineering Flow:"]


def test_category_prompt_skipped_when_flags_resolved_selection() -> None:
    asker = FakeAsker(checkboxes=[["should-not-be-used"]])
    answers = collect_answers(
        _partial(
            selection=ProjectSelection.from_items(
                CATALOG,
                mcp=frozenset({"code-memory"}),
            ),
        ),
        asker=asker,
    )

    assert answers.selection.development_loop == "mattpocock"
    assert answers.include_skills is True
    assert asker.checkbox_calls == []


def test_category_and_item_choices_resolve_across_components() -> None:
    asker = FakeAsker(
        selects=[SELECTABLE_FLOW_LABEL],
        checkboxes=[
            [],
            [],
            [],
            _item_labels("caveman", "code-memory"),
            CLAUDE_AGENT_LABELS,
        ]
    )

    answers = collect_answers(
        _partial(selection_explicit=False), catalog=CATALOG, asker=asker
    )

    assert answers.skills_items == frozenset(
        {"caveman", "mattpocock"}
    )
    assert answers.mcp_items == frozenset({"code-memory"})
    assert answers.include_docs is False


def test_declining_every_category_produces_no_optional_catalog_content() -> None:
    asker = FakeAsker(
        selects=[SELECTABLE_FLOW_LABEL],
        checkboxes=[[], [], [], [], CLAUDE_AGENT_LABELS],
    )

    answers = collect_answers(
        _partial(selection_explicit=False), catalog=CATALOG, asker=asker
    )

    assert answers.skills_items == frozenset(
        {"mattpocock"}
    )
    assert answers.mcp_items == frozenset()
    assert answers.include_docs is False
    assert answers.selection.development_loop == "mattpocock"
    assert answers.selection.categories == frozenset({"dev"})
    assert asker.checkbox_initially_selected == [
        [],
        [],
        [],
        [],
        CLAUDE_AGENT_LABELS,
    ]


def test_interactive_agent_targets_remain_last_and_are_resolved() -> None:
    asker = FakeAsker(
        selects=[SELECTABLE_FLOW_LABEL],
        checkboxes=[
            [],
            [],
            _item_labels("frontend-design"),
            [],
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


def test_agent_target_answer_skips_only_its_question() -> None:
    asker = FakeAsker(
        selects=[SELECTABLE_FLOW_LABEL],
        checkboxes=[[], [], [], []],
    )
    partial = PartialAnswers(
        project_name="my-app",
        target_dir=None,
        selection=None,
        agent_targets=frozenset({"windsurf"}),
    )

    answers = collect_answers(partial, catalog=CATALOG, asker=asker)

    assert answers.agent_targets == frozenset({"windsurf"})
    assert asker.select_calls == ["Select an Engineering Flow:"]
    assert asker.checkbox_calls == CATEGORY_PROMPTS


# --- QuestionaryAsker against the real questionary, driven headlessly ---
#
# Every test above this point injects a FakeAsker, so none of them execute the
# one module that talks to questionary. These do: they drive the real
# QuestionaryAsker through real questionary and prompt_toolkit, over a pipe
# instead of a TTY. Nothing here is monkeypatched — an argument combination
# questionary rejects, or an API that drifts under a questionary upgrade, fails
# here rather than on a user's terminal.

ENTER = "\r"
SPACE = " "

_T = TypeVar("_T")


def _drive_asker(keystrokes: str, interaction: Callable[[QuestionaryAsker], _T]) -> _T:
    """Run `interaction` against a real `QuestionaryAsker`, feeding `keystrokes`.

    Headless: prompt_toolkit reads from a pipe and writes to a dummy output, so
    this needs no console. The app session must wrap the whole call — questionary
    builds its prompt_toolkit Application when the question is constructed, not
    when it is asked.
    """
    with create_pipe_input() as pipe_input:
        pipe_input.send_text(keystrokes)
        with create_app_session(input=pipe_input, output=DummyOutput()):
            return interaction(QuestionaryAsker())


def test_questionary_checkbox_returns_the_initially_selected_items() -> None:
    selected = _drive_asker(
        ENTER,
        lambda asker: asker.checkbox(
            "Select choices:",
            ["alpha", "beta"],
            initially_selected=["alpha"],
        ),
    )

    assert selected == ["alpha"]


def test_questionary_checkbox_narrows_choices_by_typing() -> None:
    """Typing filters the list — the reason the Category and item checkboxes,
    which offer the whole catalog, are usable at all."""
    selected = _drive_asker(
        "gamma" + SPACE + ENTER,
        lambda asker: asker.checkbox(
            "Select choices:",
            ["alpha", "beta", "gamma"],
            initially_selected=(),
        ),
    )

    assert selected == ["gamma"]


def test_default_set_survives_pressing_enter_through_every_prompt() -> None:
    prompt_names = (
        "engineering-flow",
        "security",
        "quality",
        "design",
        "token-optimize",
        "agent-targets",
    )

    answers = _drive_asker(
        ENTER * len(prompt_names),
        lambda asker: collect_answers(
            _partial(selection_explicit=False), catalog=CATALOG, asker=asker
        ),
    )

    assert answers.selection == ProjectSelection.default_set(CATALOG)
    assert answers.agent_targets == frozenset({"claude"})


def test_questionary_text_returns_what_was_typed() -> None:
    assert _drive_asker("my-app" + ENTER, lambda asker: asker.text("Project name:")) == "my-app"


def test_questionary_select_returns_the_highlighted_choice() -> None:
    assert (
        _drive_asker(
            ENTER,
            lambda asker: asker.select(
                "Select one:", ["alpha", "beta"], disabled_choices=[]
            ),
        )
        == "alpha"
    )


def test_questionary_select_skips_disabled_choices() -> None:
    assert (
        _drive_asker(
            ENTER,
            lambda asker: asker.select(
                "Select one:", ["announced", "available"], disabled_choices=["announced"]
            ),
        )
        == "available"
    )


def test_questionary_asker_applies_one_style_to_every_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, dict[str, object]]] = []

    class _Question:
        def ask(self) -> object:
            return None

    def _capture(kind: str) -> Callable[..., _Question]:
        def capture(*args: object, **kwargs: object) -> _Question:
            calls.append((kind, kwargs))
            return _Question()

        return capture

    for kind in ("text", "select", "checkbox", "confirm"):
        monkeypatch.setattr(
            questionary_asker_module.questionary,
            kind,
            _capture(kind),
        )

    asker = QuestionaryAsker()
    asker.text("Name:")
    asker.select("Flow:", ["available"], disabled_choices=[])
    asker.checkbox("Items:", ["one"], initially_selected=[])
    asker.confirm("Proceed?")

    assert [kwargs["style"] for _, kwargs in calls] == [
        questionary_asker_module._PROMPT_STYLE
    ] * 4
    assert all(kwargs["qmark"] == questionary_asker_module._QUESTION_MARK for _, kwargs in calls)
    checkbox_kwargs = next(kwargs for kind, kwargs in calls if kind == "checkbox")
    assert "type to filter" in str(checkbox_kwargs["instruction"])


def test_questionary_confirm_returns_the_default_on_enter() -> None:
    assert _drive_asker(ENTER, lambda asker: asker.confirm("Proceed?", default=True)) is True
    assert _drive_asker(ENTER, lambda asker: asker.confirm("Proceed?", default=False)) is False


def test_category_item_selection_can_be_narrowed_to_one_item() -> None:
    asker = FakeAsker(
        selects=[SELECTABLE_FLOW_LABEL],
        checkboxes=[
            [],
            _item_labels("react-doctor"),
            [],
            [],
            CLAUDE_AGENT_LABELS,
        ]
    )

    answers = collect_answers(
        _partial(selection_explicit=False), catalog=CATALOG, asker=asker
    )

    assert answers.skills_items == frozenset(
        {"react-doctor", "mattpocock"}
    )
    assert answers.mcp_items == frozenset()


def test_first_category_prompt_cancel_raises_aborted() -> None:
    with pytest.raises(AbortedError, match="Security item selection prompt cancelled"):
        collect_answers(
            _partial(selection_explicit=False),
            catalog=CATALOG,
            asker=FakeAsker(selects=[SELECTABLE_FLOW_LABEL], checkboxes=[None]),
        )


def test_later_category_prompt_cancel_raises_aborted() -> None:
    asker = FakeAsker(
        selects=[SELECTABLE_FLOW_LABEL],
        checkboxes=[[], None],
    )

    with pytest.raises(AbortedError, match="Quality item selection prompt cancelled"):
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
        {"caveman", "mattpocock"}
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
    assert "Engineering Flow and Category selection require an interactive terminal" in str(
        excinfo.value
    )
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
            agent_targets=frozenset({"claude"}),
        ),
        assume_yes=False,
    )

    asker = FakeAsker(
        texts=["my-app"],
        selects=[SELECTABLE_FLOW_LABEL],
        checkboxes=[
            [],
            [],
            [],
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
            selects=[SELECTABLE_FLOW_LABEL],
            checkboxes=[
                [],
                [],
                _item_labels("frontend-design"),
                [],
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


def test_confirmation_colour_is_decoration_only(
    capsys: pytest.CaptureFixture[str],
) -> None:
    confirm_generation(
        _answers(),
        PIN,
        asker=FakeAsker(confirms=[True]),
        style=PresentationStyle(),
    )
    plain = capsys.readouterr().out
    confirm_generation(
        _answers(),
        PIN,
        asker=FakeAsker(confirms=[True]),
        style=PresentationStyle(color=True, width=80),
    )
    coloured = capsys.readouterr().out

    assert "\x1b" not in plain
    assert "\x1b" in coloured
    assert _ANSI_ESCAPE.sub("", coloured) == plain


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
    assert "engineering flow: mattpocock" in summary
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
