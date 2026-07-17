"""Unit tests for dev_ready.prompts (no network, no real TTY, tmp_path only)."""

from collections.abc import Sequence
from pathlib import Path

import pytest

import dev_ready.prompts.collect as collect_module
from dev_ready.errors import AbortedError, InvalidArgumentsError
from dev_ready.manifest import UpstreamPin
from dev_ready.prompts import Answers, PartialAnswers, collect_answers, confirm_generation

PIN = UpstreamPin(
    repo="fastapi/full-stack-fastapi-template",
    ref="master",
    commit="4cd0d9e51aebd1af6f82d91ad0df4c9e41f4dea2",
    license="MIT",
)


class FakeAsker:
    """Scripted Asker: pops one canned response per call, in call order."""

    def __init__(
        self,
        *,
        texts: list[str | None] | None = None,
        checkboxes: list[list[str] | None] | None = None,
        confirms: list[bool | None] | None = None,
    ) -> None:
        self._texts = list(texts or [])
        self._checkboxes = list(checkboxes or [])
        self._confirms = list(confirms or [])
        self.text_calls: list[str] = []
        self.checkbox_calls: list[str] = []
        self.confirm_calls: list[str] = []

    def text(self, message: str) -> str | None:
        self.text_calls.append(message)
        return self._texts.pop(0)

    def checkbox(self, message: str, choices: Sequence[str]) -> list[str] | None:
        self.checkbox_calls.append(message)
        return self._checkboxes.pop(0)

    def confirm(self, message: str, *, default: bool = True) -> bool | None:
        self.confirm_calls.append(message)
        return self._confirms.pop(0)


class _RaisingAsker:
    """An Asker where every method raises KeyboardInterrupt."""

    def text(self, message: str) -> str | None:
        raise KeyboardInterrupt

    def checkbox(self, message: str, choices: Sequence[str]) -> list[str] | None:
        raise KeyboardInterrupt

    def confirm(self, message: str, *, default: bool = True) -> bool | None:
        raise KeyboardInterrupt


def _partial(**overrides: object) -> PartialAnswers:
    defaults: dict[str, object] = {
        "project_name": "my-app",
        "target_dir": None,
        "include_skills": True,
        "include_mcp": True,
        "include_docs": True,
        "include_agents": True,
        "components_explicit": True,
        "assume_yes": False,
    }
    defaults.update(overrides)
    return PartialAnswers(**defaults)  # type: ignore[arg-type]


def _answers(**overrides: object) -> Answers:
    defaults: dict[str, object] = {
        "project_name": "my-app",
        "target_dir": Path("/does/not/exist/my-app"),
    }
    defaults.update(overrides)
    return Answers(**defaults)  # type: ignore[arg-type]


def test_answers_default_has_include_agents() -> None:
    answers = Answers(project_name="my-app", target_dir=Path("/tmp/my-app"))
    assert answers.include_agents is True


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


# --- component prompt ---


def test_component_prompt_fires_only_when_no_explicit_flag() -> None:
    asker = FakeAsker(checkboxes=[["skills", "mcp", "docs", "agents"]])
    answers = collect_answers(_partial(components_explicit=False), asker=asker)
    assert (answers.include_skills, answers.include_mcp, answers.include_docs, answers.include_agents) == (
        True,
        True,
        True,
        True,
    )
    assert len(asker.checkbox_calls) == 1


def test_component_prompt_skipped_when_flag_explicit() -> None:
    asker = FakeAsker(checkboxes=[["skills", "mcp", "docs", "agents"]])
    answers = collect_answers(
        _partial(components_explicit=True, include_skills=False, include_mcp=True, include_docs=True, include_agents=True),
        asker=asker,
    )
    assert answers.include_skills is False
    assert asker.checkbox_calls == []


def test_component_prompt_selection_can_disable_some() -> None:
    asker = FakeAsker(checkboxes=[["mcp"]])
    answers = collect_answers(_partial(components_explicit=False), asker=asker)
    assert (answers.include_skills, answers.include_mcp, answers.include_docs, answers.include_agents) == (
        False,
        True,
        False,
        False,
    )


@pytest.mark.parametrize(
    ("selected", "expected_skills", "expected_mcp", "expected_docs", "expected_agents"),
    [
        (["skills", "mcp", "docs", "agents"], True, True, True, True),
        (["skills", "mcp", "docs"], True, True, True, False),
        (["docs", "agents"], False, False, True, True),
        ([], False, False, False, False),
    ]
)
def test_component_matrix(selected, expected_skills, expected_mcp, expected_docs, expected_agents) -> None:
    asker = FakeAsker(checkboxes=[selected])
    answers = collect_answers(_partial(components_explicit=False), asker=asker)
    assert answers.include_skills is expected_skills
    assert answers.include_mcp is expected_mcp
    assert answers.include_docs is expected_docs
    assert answers.include_agents is expected_agents


# --- cancellation during collect_answers ---


def test_name_prompt_cancel_raises_aborted() -> None:
    asker = FakeAsker(texts=[None])
    with pytest.raises(AbortedError):
        collect_answers(_partial(project_name=None), asker=asker)


def test_component_prompt_cancel_raises_aborted() -> None:
    asker = FakeAsker(checkboxes=[None])
    with pytest.raises(AbortedError):
        collect_answers(_partial(components_explicit=False), asker=asker)


def test_name_prompt_keyboard_interrupt_raises_aborted() -> None:
    with pytest.raises(AbortedError):
        collect_answers(_partial(project_name=None), asker=_RaisingAsker())


# --- non-TTY guard ---


def test_non_tty_missing_name_raises_invalid_arguments(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(collect_module, "_is_interactive", lambda: False)
    with pytest.raises(InvalidArgumentsError) as excinfo:
        collect_answers(_partial(project_name=None))
    assert "project name is required" in str(excinfo.value)


def test_non_tty_missing_components_raises_invalid_arguments(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(collect_module, "_is_interactive", lambda: False)
    with pytest.raises(InvalidArgumentsError) as excinfo:
        collect_answers(_partial(components_explicit=False))
    assert "component selection requires an interactive terminal" in str(excinfo.value)
    assert "--no-agents" in str(excinfo.value)


# --- interactive/flag path convergence (ADR-004) ---


def test_interactive_and_flag_paths_produce_identical_answers(tmp_path: Path) -> None:
    """build_answers (flags) and collect_answers (prompts, answers pre-supplied via
    FakeAsker) must construct an equal Answers for equivalent inputs — the two
    paths share one Answers model by construction (ADR-004)."""
    target_dir = tmp_path / "my-app"

    flag_answers = Answers(
        project_name="my-app",
        target_dir=target_dir,
        include_skills=False,
        include_mcp=True,
        include_docs=True,
        include_agents=True,
        assume_yes=False,
    )

    asker = FakeAsker(texts=["my-app"], checkboxes=[["mcp", "docs", "agents"]])
    prompt_answers = collect_answers(
        _partial(
            project_name=None,
            target_dir=target_dir,
            components_explicit=False,
        ),
        asker=asker,
    )

    assert flag_answers == prompt_answers


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
    collect_answers(_partial(project_name="my-app", components_explicit=True))


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


def test_render_confirmation_summary_includes_agents() -> None:
    from dev_ready.prompts.collect import _render_confirmation_summary
    # when agents is True
    summary_on = _render_confirmation_summary(_answers(include_agents=True), PIN)
    assert "agents" in summary_on
    # when agents is False
    summary_off = _render_confirmation_summary(_answers(include_agents=False), PIN)
    assert "agents" not in summary_off
