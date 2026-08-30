"""Unit tests for dev_ready.cli."""

import argparse
import io
import re
import sys
from pathlib import Path

import pytest

import dev_ready.cli as cli_module
from dev_ready import __version__
from dev_ready.cli import ProgressRenderer, build_answers, build_parser, main
from dev_ready.errors import (
    AbortedError,
    DriftError,
    FetchError,
    InvalidArgumentsError,
    OverlayError,
    TargetDirectoryError,
    UpgradeError,
    VerificationError,
)
from dev_ready.generate import (
    CleanupWarningEvent,
    GenerationStage,
    ProgressEvent,
    ProgressStatus,
)
from dev_ready.manifest import load_default_manifest
from dev_ready.intent import Answers

CATALOG = load_default_manifest().components
_ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*m")


class _TTYBuffer(io.StringIO):
    def isatty(self) -> bool:
        return True


def _init_args(**overrides) -> argparse.Namespace:
    defaults = {
        "project_name": "my-app",
        "yes": False,
        "target_dir": None,
        "categories": None,
        "dev": None,
        "security": None,
        "quality": None,
        "design": None,
        "token_optimize": None,
        "agents": None,
    }
    defaults.update(overrides)
    return argparse.Namespace(**defaults)



def test_version_flag(capsys) -> None:
    with pytest.raises(SystemExit) as excinfo:
        main(["--version"])
    assert excinfo.value.code == 0
    assert __version__ in capsys.readouterr().out


def test_no_command_prints_help_and_succeeds(capsys) -> None:
    assert main([]) == 0
    assert "init" in capsys.readouterr().out


def test_unknown_command_exits_2() -> None:
    with pytest.raises(SystemExit) as excinfo:
        main(["frobnicate"])
    assert excinfo.value.code == 2


def test_init_without_name_exits_2(capsys) -> None:
    assert main(["init"]) == 2
    assert "project name is required" in capsys.readouterr().err


@pytest.mark.parametrize("assume_yes", [False, True])
def test_init_defaults_name_from_explicit_destination_on_both_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    assume_yes: bool,
) -> None:
    target_dir = tmp_path / "app"
    captured: list[Answers] = []

    def _capture_generate(answers: Answers, *args: object, **kwargs: object) -> list[Path]:
        captured.append(answers)
        return []

    monkeypatch.setattr(cli_module, "generate", _capture_generate)
    monkeypatch.setattr(cli_module, "confirm_generation", lambda *args, **kwargs: True)
    argv = ["init", "--dir", str(target_dir)]
    if assume_yes:
        argv.append("--yes")
    else:
        argv.extend(["--categories", "none"])

    assert main(argv) == 0
    assert captured[0].project_name == "app"
    assert captured[0].target_dir == target_dir


def test_init_explicit_name_beats_destination_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: list[Answers] = []
    monkeypatch.setattr(
        cli_module,
        "generate",
        lambda answers, *args, **kwargs: captured.append(answers) or [],
    )

    assert main(["init", "chosen", "--dir", str(tmp_path / "ignored"), "--yes"]) == 0
    assert captured[0].project_name == "chosen"


def test_init_invalid_destination_name_exits_2_non_interactively(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    invalid_target = tmp_path / "My App"

    assert main(["init", "--dir", str(invalid_target), "--yes"]) == 2

    error = capsys.readouterr().err
    assert "invalid project name 'My App'" in error
    assert not invalid_target.exists()


@pytest.mark.parametrize("assume_yes", [False, True])
def test_init_known_collision_fails_before_confirmation_or_generation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    assume_yes: bool,
) -> None:
    target_dir = tmp_path / "app"
    (target_dir / ".claude").mkdir(parents=True)
    confirmed = False
    generated = False

    def _unexpected_confirm(*args: object, **kwargs: object) -> bool:
        nonlocal confirmed
        confirmed = True
        return True

    def _unexpected_generate(*args: object, **kwargs: object) -> list[Path]:
        nonlocal generated
        generated = True
        return []

    monkeypatch.setattr(cli_module, "confirm_generation", _unexpected_confirm)
    monkeypatch.setattr(cli_module, "generate", _unexpected_generate)
    argv = ["init", "--dir", str(target_dir)]
    if assume_yes:
        argv.append("--yes")
    else:
        argv.extend(["--categories", "none"])

    assert main(argv) == 4
    assert ".claude" in capsys.readouterr().err
    assert confirmed is False
    assert generated is False


@pytest.mark.parametrize("bad_name", ["../etc", "a b", "-app", "app/x", ""])
def test_unsafe_project_names_rejected(bad_name: str) -> None:
    with pytest.raises(InvalidArgumentsError):
        build_answers(_init_args(project_name=bad_name), CATALOG)


def test_init_unsafe_name_exits_2(capsys) -> None:
    assert main(["init", "../etc"]) == 2
    assert "error:" in capsys.readouterr().err


def test_init_success_exits_0_and_prints_summary(
    tmp_path, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    target_dir = tmp_path / "my-app"

    def _fake_generate(answers: Answers, pin, catalog=None, **kwargs) -> list[Path]:
        assert answers.project_name == "my-app"
        return [Path("CLAUDE.md"), Path(".mcp.json")]

    monkeypatch.setattr(cli_module, "generate", _fake_generate)

    assert main(["init", "my-app", "--yes", "--dir", str(target_dir)]) == 0
    out = capsys.readouterr().out
    assert "my-app" in out
    assert str(target_dir) in out
    assert "fastapi/full-stack-fastapi-template" in out
    assert "Next Steps" in out


def test_init_coloured_and_no_color_reports_have_the_same_facts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target_dir = tmp_path / "my-app"
    coloured_output = _TTYBuffer()

    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.setattr(cli_module, "generate", lambda *args, **kwargs: [])
    monkeypatch.setattr(cli_module.sys, "stdout", coloured_output)

    assert main(["init", "my-app", "--yes", "--dir", str(target_dir)]) == 0
    coloured = coloured_output.getvalue()

    monkeypatch.setenv("NO_COLOR", "1")
    plain_output = _TTYBuffer()
    monkeypatch.setattr(cli_module.sys, "stdout", plain_output)

    assert main(["init", "my-app", "--yes", "--dir", str(target_dir)]) == 0
    plain = plain_output.getvalue()

    assert "\x1b" in coloured
    assert "\x1b" not in plain
    assert _ANSI_ESCAPE.sub("", coloured) == plain


def test_init_renders_stable_non_tty_progress_on_stderr_only(
    tmp_path, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    def _fake_generate(answers: Answers, pin, catalog=None, **kwargs) -> list[Path]:
        progress = kwargs["progress"]
        for index, stage in enumerate(GenerationStage, start=1):
            progress(
                ProgressEvent(
                    stage=stage,
                    status=ProgressStatus.STARTED,
                    commit=pin.commit if stage is GenerationStage.FETCH else None,
                )
            )
            progress(
                ProgressEvent(
                    stage=stage,
                    status=ProgressStatus.COMPLETED,
                    elapsed_seconds=index + 0.234,
                    commit=pin.commit if stage is GenerationStage.FETCH else None,
                )
            )
        return [Path("CLAUDE.md")]

    monkeypatch.setattr(cli_module, "generate", _fake_generate)

    assert main(["init", "my-app", "--yes", "--dir", str(tmp_path / "my-app")]) == 0
    captured = capsys.readouterr()

    assert "[1/4]" not in captured.out
    assert "Next Steps:" in captured.out
    assert "\x1b" not in captured.out
    assert captured.err.splitlines() == [
        f"[1/4] Fetching base template (commit {cli_module.load_default_manifest().upstream['base_template'].commit})…",
        "[1/4] Fetching base template done (1.23s)",
        "[2/4] Applying dev-ready overlay…",
        "[2/4] Applying dev-ready overlay done (2.23s)",
        "[3/4] Verifying generated project…",
        "[3/4] Verifying generated project done (3.23s)",
        "[4/4] Finalizing project…",
        "[4/4] Finalizing project done (4.23s)",
    ]
    assert "\x1b" not in captured.err
    assert "\r" not in captured.err
    assert "%" not in captured.err


def test_tty_progress_animates_active_stage_and_closes_idempotently() -> None:
    stream = _TTYBuffer()
    renderer = ProgressRenderer(stream, is_tty=True, spinner_interval=60.0)

    renderer(
        ProgressEvent(
            stage=GenerationStage.FETCH,
            status=ProgressStatus.STARTED,
            commit="abc123",
        )
    )
    active_output = stream.getvalue()
    renderer(
        ProgressEvent(
            stage=GenerationStage.FETCH,
            status=ProgressStatus.COMPLETED,
            elapsed_seconds=1.5,
            commit="abc123",
        )
    )
    renderer.close()
    renderer.close()

    output = stream.getvalue()
    assert active_output.startswith("\r⠋ [1/4] Fetching base template (commit abc123)…")
    assert "[1/4] Fetching base template done (1.50s)" in output
    assert output.endswith("\n")


def test_progress_renderer_renders_cleanup_warning_outside_stage_count(tmp_path: Path) -> None:
    stream = io.StringIO()
    renderer = ProgressRenderer(stream, is_tty=False)
    staging = tmp_path / ".my-app.dev-ready-abcd"

    renderer(CleanupWarningEvent(staging))

    assert stream.getvalue() == f"warning: failed to remove temp directory {staging}\n"
    assert "[" not in stream.getvalue()


@pytest.mark.parametrize(
    ("stage", "error", "expected_exit_code"),
    [
        (GenerationStage.FETCH, FetchError("network down"), 3),
        (GenerationStage.OVERLAY, OverlayError("collision"), 1),
        (GenerationStage.VERIFY, VerificationError("missing frontend"), 5),
        (GenerationStage.FINALIZE, TargetDirectoryError("target race"), 4),
    ],
)
def test_init_identifies_failed_stage_once_before_typed_error(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    stage: GenerationStage,
    error: Exception,
    expected_exit_code: int,
) -> None:
    def _failing_generate(answers: Answers, pin, catalog=None, **kwargs) -> list[Path]:
        progress = kwargs["progress"]
        progress(ProgressEvent(stage=stage, status=ProgressStatus.STARTED, commit=pin.commit))
        progress(
            ProgressEvent(
                stage=stage,
                status=ProgressStatus.FAILED,
                elapsed_seconds=2.5,
                commit=pin.commit,
            )
        )
        raise error

    monkeypatch.setattr(cli_module, "generate", _failing_generate)

    assert main(["init", "my-app", "--yes"]) == expected_exit_code
    stderr = capsys.readouterr().err

    assert stderr.count("failed (2.50s)") == 1
    assert stderr.index("failed (2.50s)") < stderr.index("error:")


@pytest.mark.parametrize("error", [RuntimeError("boom"), KeyboardInterrupt(), SystemExit(143)])
def test_init_closes_progress_on_unexpected_interrupt_and_termination(
    monkeypatch: pytest.MonkeyPatch, error: BaseException
) -> None:
    closed: list[ProgressRenderer] = []
    original_close = ProgressRenderer.close

    def _recording_close(renderer: ProgressRenderer) -> None:
        closed.append(renderer)
        original_close(renderer)

    def _failing_generate(answers: Answers, pin, catalog=None, **kwargs) -> list[Path]:
        progress = kwargs["progress"]
        progress(
            ProgressEvent(
                stage=GenerationStage.FETCH,
                status=ProgressStatus.STARTED,
                commit=pin.commit,
            )
        )
        raise error

    monkeypatch.setattr(ProgressRenderer, "close", _recording_close)
    monkeypatch.setattr(cli_module, "generate", _failing_generate)

    with pytest.raises(type(error)):
        main(["init", "my-app", "--yes"])

    assert len(closed) == 1


def test_init_success_keeps_only_the_mandatory_loop_in_disabled_summary(
    tmp_path, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    monkeypatch.setattr(cli_module, "generate", lambda answers, pin, *args, **kwargs: [Path("CLAUDE.md")])

    assert (
        main(
            [
                "init",
                "my-app",
                "--yes",
                "--dir",
                str(tmp_path / "my-app"),
                "--categories",
                "none",
            ]
        )
        == 0
    )
    out = capsys.readouterr().out
    assert "react-doctor" not in out
    assert "caveman" not in out
    assert "mcp" not in out
    assert "handoff" not in out


@pytest.mark.parametrize(
    ("error", "expected_exit_code"),
    [
        (FetchError("network down"), 3),
        (TargetDirectoryError("dir taken"), 4),
        (OverlayError("collision"), 1),
        (VerificationError("missing 'frontend'"), 5),
    ],
)
def test_init_maps_generate_errors_to_exit_codes(
    monkeypatch: pytest.MonkeyPatch, capsys, error: Exception, expected_exit_code: int
) -> None:
    def _raising_generate(answers: Answers, pin, catalog=None, **kwargs) -> list[Path]:
        raise error

    monkeypatch.setattr(cli_module, "generate", _raising_generate)

    assert main(["init", "my-app", "--yes"]) == expected_exit_code
    assert "error:" in capsys.readouterr().err


def test_init_flags_reach_generate_via_answers(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, Answers] = {}

    def _capturing_generate(answers: Answers, pin, catalog=None, **kwargs) -> list[Path]:
        captured["answers"] = answers
        return []

    monkeypatch.setattr(cli_module, "generate", _capturing_generate)


    target_dir = tmp_path / "out"
    main(
        [
            "init",
            "my-app",
            "--yes",
            "--dir",
            str(target_dir),
            "--categories",
            "none",
        ]
    )

    answers = captured["answers"]
    assert answers.project_name == "my-app"
    assert answers.target_dir == target_dir
    assert answers.include_skills is True
    assert answers.selection.development_loop == "mattpocock"
    assert answers.include_mcp is False
    assert answers.include_docs is False
    assert answers.assume_yes is True


def test_build_answers_defaults() -> None:
    answers = build_answers(_init_args(), CATALOG)
    assert answers.project_name == "my-app"
    assert answers.target_dir == Path.cwd() / "my-app"
    assert answers.include_skills is True
    assert answers.include_mcp is False
    assert answers.skills_items == frozenset({"mattpocock"})
    assert answers.mcp_items == frozenset()
    assert answers.include_docs is False
    assert answers.selection.docs_items == frozenset()
    assert answers.assume_yes is False


def test_build_answers_respects_flags(tmp_path) -> None:
    answers = build_answers(
        _init_args(yes=True, target_dir=tmp_path / "out", categories="none"),
        CATALOG,
    )
    assert answers.target_dir == tmp_path / "out"
    assert answers.include_skills is True
    assert answers.include_mcp is False
    assert answers.skills_items == frozenset(
        {"mattpocock"}
    )
    assert answers.mcp_items == frozenset()
    assert answers.include_docs is False
    assert answers.assume_yes is True


@pytest.mark.parametrize(("spelling", "relative"), [(".", Path()), ("new/app", Path("new/app"))])
def test_init_parser_resolves_explicit_target_at_the_cli_boundary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    spelling: str,
    relative: Path,
) -> None:
    monkeypatch.chdir(tmp_path)

    args = build_parser().parse_args(["init", "my-app", "--dir", spelling])

    assert args.target_dir == (tmp_path / relative).resolve()
    assert args.target_dir.is_absolute()


def test_parser_accepts_all_documented_flags() -> None:
    args = build_parser().parse_args(
        [
            "init",
            "my-app",
            "-y",
            "--dir",
            "x",
            "--categories",
            "dev,token-optimize",
            "--dev",
            "none",
            "--token-optimize",
            "caveman",
            "--agents",
            "claude,windsurf",
        ]
    )
    assert args.command == "init"
    assert args.yes is True
    assert args.target_dir == Path("x").resolve()
    assert args.categories == "dev,token-optimize"
    assert args.dev == "none"
    assert args.token_optimize == "caveman"
    assert args.agents == "claude,windsurf"
    assert not hasattr(args, "no_handoff")
    assert not hasattr(args, "no_agents")


def test_init_help_names_dot_as_an_explicit_dir_value(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as excinfo:
        build_parser().parse_args(["init", "--help"])

    assert excinfo.value.code == 0
    help_text = capsys.readouterr().out
    assert "--dir" in help_text
    assert "--dir ." in help_text


@pytest.mark.parametrize(
    ("removed_flag", "replacement"),
    [
        ("--no-handoff", "Handoff Protocol"),
        ("--no-agents", "Handoff Protocol"),
        ("--skills", "--categories"),
        ("--mcp", "--token-optimize"),
        ("--no-skills", "--categories"),
        ("--no-mcp", "--token-optimize none"),
        ("--no-docs", "--design none"),
    ],
)
def test_removed_selection_flags_exit_2_before_generation(
    removed_flag: str,
    replacement: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    called = False

    def _capture(*args, **kwargs) -> list[Path]:
        nonlocal called
        called = True
        return []

    monkeypatch.setattr(cli_module, "generate", _capture)

    assert main(["init", "my-app", "--yes", removed_flag]) == 2
    assert called is False
    error = capsys.readouterr().err
    assert removed_flag in error
    assert "removed" in error
    assert replacement in error


def test_agents_flag_reaches_generation_as_resolved_target_selection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, Answers] = {}

    def _capture(answers: Answers, pin, catalog=None, **kwargs) -> list[Path]:
        captured["answers"] = answers
        return []

    monkeypatch.setattr(cli_module, "generate", _capture)

    assert main(
        [
            "init",
            "my-app",
            "--yes",
            "--dir",
            str(tmp_path / "out"),
            "--agents",
            "windsurf",
        ]
    ) == 0
    assert captured["answers"].agent_targets == frozenset({"windsurf"})
    answers = captured["answers"]
    assert answers.skills_items == frozenset({"mattpocock"})
    assert answers.mcp_items == frozenset()
    assert answers.selection.docs_items == frozenset()


def test_agents_only_non_tty_exits_2_with_unanswered_content_question(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["init", "my-app", "--agents", "windsurf"]) == 2

    error = capsys.readouterr().err
    assert "Engineering Flow and Category selection require an interactive terminal" in error


def test_yes_without_selection_flags_generates_for_claude_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, Answers] = {}

    def _capture(answers: Answers, pin, catalog=None, **kwargs) -> list[Path]:
        captured["answers"] = answers
        return []

    monkeypatch.setattr(cli_module, "generate", _capture)

    assert main(["init", "my-app", "--yes", "--dir", str(tmp_path / "out")]) == 0
    assert captured["answers"].agent_targets == frozenset({"claude"})


def test_development_loop_flag_uses_the_structural_selection_axis() -> None:
    args = build_parser().parse_args(
        [
            "init",
            "my-app",
            "--yes",
            "--categories",
            "none",
            "--development-loop",
            "mattpocock",
        ]
    )

    answers = build_answers(args, CATALOG)

    assert answers.selection.development_loop == "mattpocock"
    assert answers.skills_items == frozenset({"mattpocock"})


@pytest.mark.parametrize("flag", ["--flow", "--development-loop"])
def test_flow_flag_spellings_share_one_destination(flag: str) -> None:
    args = build_parser().parse_args(
        ["init", "my-app", "--yes", flag, "mattpocock"]
    )

    assert args.development_loop == "mattpocock"
    assert build_answers(args, CATALOG).selection.development_loop == "mattpocock"


def test_init_help_calls_the_public_concept_engineering_flow(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as excinfo:
        build_parser().parse_args(["init", "--help"])

    assert excinfo.value.code == 0
    help_text = capsys.readouterr().out
    assert "--flow ID" in help_text
    assert "Mandatory Engineering Flow id" in help_text
    assert "development-loop id" not in help_text


@pytest.mark.parametrize(
    ("arguments", "expected"),
    [
        (("--flow", "spec-loop"), "renamed to 'mattpocock'"),
        (("--flow", "nonesuch"), "unknown Engineering Flow id 'nonesuch'; valid ids: ['addyosmani', 'mattpocock', 'superpowers']"),
        (("--dev", "spec-loop"), "retired Dev item id(s) 'spec-loop'"),
    ],
)
def test_flow_selection_failures_are_mutually_distinguishable(
    arguments: tuple[str, str],
    expected: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["init", "my-app", "--yes", *arguments]) == 2

    assert expected in capsys.readouterr().err


@pytest.mark.parametrize("flow", ["superpowers", "addyosmani"])
def test_selectable_non_default_flow_flag(
    monkeypatch: pytest.MonkeyPatch,
    flow: str,
) -> None:
    captured_answers = None

    def _capture(answers, *args, **kwargs) -> list[Path]:
        nonlocal captured_answers
        captured_answers = answers
        return []

    monkeypatch.setattr(cli_module, "generate", _capture)

    assert main(["init", "my-app", "--yes", "--flow", flow]) == 0
    assert captured_answers is not None
    assert captured_answers.development_loop == flow
    assert flow in captured_answers.skills_items
    assert "mattpocock" not in captured_answers.skills_items


def test_unknown_agents_flag_fails_before_generation(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    called = False

    def _capture(*args, **kwargs) -> list[Path]:
        nonlocal called
        called = True
        return []

    monkeypatch.setattr(cli_module, "generate", _capture)

    assert main(["init", "my-app", "--yes", "--agents", "claud"]) == 2
    assert called is False
    error = capsys.readouterr().err
    assert "unknown agent target ids" in error
    assert "valid ids:" not in error


def test_init_rejects_standard_compliant_agent_target_id(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    called = False

    def _capture(*args, **kwargs) -> list[Path]:
        nonlocal called
        called = True
        return []

    monkeypatch.setattr(cli_module, "generate", _capture)

    assert main(["init", "my-app", "--yes", "--agents", "cursor"]) == 2
    assert called is False
    error = capsys.readouterr().err
    assert "cursor" in error
    assert "reads standard '.agents/skills/' directly" in error
    assert "needs no Agent Target" in error


def test_upgrade_parser_accepts_path_and_dry_run() -> None:
    args = build_parser().parse_args(["upgrade", "project", "--dry-run"])
    assert args.command == "upgrade"
    assert args.target_dir == Path("project")
    assert args.dry_run is True


def test_upgrade_success_and_dry_run_are_wiring_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    captured: dict[str, object] = {}

    def fake_upgrade(target: Path, dry_run: bool = False) -> str:
        captured["target"] = target
        captured["dry_run"] = dry_run
        return "upgrade report\n"

    monkeypatch.setattr(cli_module, "upgrade_project", fake_upgrade)
    target = tmp_path / "project"
    assert main(["upgrade", str(target), "--dry-run"]) == 0
    assert captured == {"target": target, "dry_run": True}
    assert capsys.readouterr().out == "upgrade report\n"


def test_upgrade_missing_stamp_exits_6(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["upgrade", str(tmp_path)]) == 6
    assert "missing .dev-ready.json" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("command", "patch_name", "error", "expected_exit_code"),
    [
        (
            ["init", "my-app", "--yes"],
            "generate",
            TargetDirectoryError(
                "failed to create Skill Link at .claude/skills/implement: "
                "the destination was restored"
            ),
            4,
        ),
        (
            ["init", "my-app", "--yes"],
            "generate",
            VerificationError(
                "failed to create Skill Link at .claude/skills/implement: "
                "[Errno 1] Operation not permitted. Choose a different destination "
                "location on a filesystem that supports directory links."
            ),
            5,
        ),
        (
            ["check", "."],
            "check_project",
            DriftError(
                "[invalid agent target artifact] agent target 'claude' artifact "
                "'.claude/skills/implement' must be a Skill Link"
            ),
            7,
        ),
        (
            ["upgrade", "."],
            "upgrade_project",
            UpgradeError(
                "failed to create Skill Link at .dev-ready-link-probe: "
                "[Errno 1] Operation not permitted. Choose a different destination "
                "location on a filesystem that supports directory links."
            ),
            9,
        ),
    ],
)
def test_cli_maps_skill_link_failures_without_a_new_exit_code(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    command: list[str],
    patch_name: str,
    error: Exception,
    expected_exit_code: int,
) -> None:
    def _raise(*args: object, **kwargs: object) -> object:
        raise error

    monkeypatch.setattr(cli_module, patch_name, _raise)

    assert main(command) == expected_exit_code
    assert "error:" in capsys.readouterr().err


def test_category_item_flag_variations() -> None:
    ans = build_answers(
        _init_args(
            categories="dev,token-optimize",
            dev="all",
            token_optimize="none",
        ),
        CATALOG,
    )
    assert ans.skills_items == frozenset(
        {
            "mattpocock",
        }
    )
    assert ans.mcp_items == frozenset()
    assert ans.include_skills is True
    assert ans.include_mcp is False

    ans2 = build_answers(
        _init_args(
            categories="token-optimize",
            token_optimize="caveman,code-memory",
        ),
        CATALOG,
    )
    assert ans2.skills_items == frozenset(
        {"caveman", "mattpocock"}
    )
    assert ans2.mcp_items == frozenset({"code-memory"})

    adhd = build_answers(
        _init_args(
            categories="token-optimize",
            token_optimize="i-have-adhd",
        ),
        CATALOG,
    )
    assert adhd.skills_items == frozenset({"i-have-adhd", "mattpocock"})

    everything = build_answers(
        _init_args(
            categories="token-optimize",
            token_optimize="all",
        ),
        CATALOG,
    )
    assert everything.skills_items == frozenset(
        {"caveman", "i-have-adhd", "mattpocock"}
    )
    assert everything.mcp_items == frozenset({"code-memory"})


def test_unknown_item_id_exits_2(capsys) -> None:
    assert main(["init", "my-app", "--yes", "--security", "bogus"]) == 2
    err = capsys.readouterr().err
    assert "unknown Security item ids: ['bogus']" in err
    assert "valid ids: ['security-audit']" in err


def test_removed_project_orientation_id_uses_standard_unknown_item_error(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["init", "my-app", "--yes", "--dev", "project-orientation"]) == 2
    error = capsys.readouterr().err
    assert "unknown Dev item ids: ['project-orientation']" in error
    assert "valid ids: []" in error


@pytest.mark.parametrize(
    "retired_id",
    ["spec-loop", "tdd", "diagnosing-bugs", "code-review", "setup-all"],
)
@pytest.mark.parametrize("flow", ["mattpocock", "superpowers"])
def test_retired_loop_item_ids_exit_2_naming_the_mandatory_engineering_flow(
    retired_id: str,
    flow: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(cli_module, "generate", lambda *args, **kwargs: [])
    assert main(["init", "my-app", "--yes", "--flow", flow, "--dev", retired_id]) == 2

    error = capsys.readouterr().err
    assert f"retired Dev item id(s) '{retired_id}'" in error
    assert "mandatory Engineering Flow" in error
    assert "mattpocock" not in error
    assert "superpowers" not in error


def test_retired_dev_item_error_is_identical_for_both_flows(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["init", "my-app", "--yes", "--flow", "mattpocock", "--dev", "tdd"]) == 2
    mattpocock_error = capsys.readouterr().err
    assert main(["init", "my-app", "--yes", "--flow", "superpowers", "--dev", "tdd"]) == 2
    superpowers_error = capsys.readouterr().err

    assert mattpocock_error == superpowers_error
    assert "mattpocock" not in superpowers_error
    assert "superpowers" not in superpowers_error


def test_dev_category_accepts_no_enhancement_items() -> None:
    answers = build_answers(
        _init_args(categories="dev", dev="none"),
        CATALOG,
    )

    assert answers.skills_items == frozenset({"mattpocock"})


def test_conflicting_flags_exits_2(capsys) -> None:
    assert (
        main(
            [
                "init",
                "my-app",
                "--yes",
                "--categories",
                "security",
                "--quality",
                "react-doctor",
            ]
        )
        == 2
    )
    err = capsys.readouterr().err
    assert "--quality conflicts with --categories" in err


def test_unknown_category_exits_2_with_valid_ids(capsys) -> None:
    assert main(["init", "my-app", "--yes", "--categories", "performance"]) == 2
    error = capsys.readouterr().err
    assert "unknown Category ids: ['performance']" in error
    assert "['design', 'dev', 'quality', 'security', 'token-optimize']" in error


# --- interactive flow (no --yes): confirm / abort / questionary isolation ---


def test_init_interactive_confirm_accept_calls_generate_once(
    tmp_path, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    target_dir = tmp_path / "my-app"
    generate_calls: list[Answers] = []

    monkeypatch.setattr(
        cli_module,
        "collect_answers",
        lambda partial, **_: Answers(project_name="my-app", target_dir=target_dir),
    )
    monkeypatch.setattr(cli_module, "confirm_generation", lambda answers, pin, **_: True)

    def _spy_generate(answers: Answers, pin, catalog=None, **kwargs) -> list[Path]:
        generate_calls.append(answers)
        return [Path("CLAUDE.md")]

    monkeypatch.setattr(cli_module, "generate", _spy_generate)

    assert main(["init", "my-app", "--dir", str(target_dir)]) == 0
    assert len(generate_calls) == 1
    assert "my-app" in capsys.readouterr().out


def test_init_interactive_confirm_decline_skips_generate(
    tmp_path, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    target_dir = tmp_path / "my-app"
    generate_calls: list[Answers] = []

    monkeypatch.setattr(
        cli_module,
        "collect_answers",
        lambda partial, **_: Answers(project_name="my-app", target_dir=target_dir),
    )
    monkeypatch.setattr(cli_module, "confirm_generation", lambda answers, pin, **_: False)
    monkeypatch.setattr(
        cli_module, "generate", lambda answers, pin, *_: generate_calls.append(answers) or []
    )

    assert main(["init", "my-app", "--dir", str(target_dir)]) == 1
    assert generate_calls == []
    assert "aborted: nothing was written" in capsys.readouterr().err


def test_init_interactive_cancel_aborts_with_exit_1(
    monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    def _raise_aborted(partial, **_):
        raise AbortedError("prompt cancelled")

    monkeypatch.setattr(cli_module, "collect_answers", _raise_aborted)

    assert main(["init", "my-app"]) == 1
    err = capsys.readouterr().err
    assert err.strip() == "aborted: nothing was written"


def test_yes_path_never_imports_questionary(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sys.modules.pop("questionary", None)
    monkeypatch.setattr(cli_module, "generate", lambda answers, pin, *args, **kwargs: [Path("CLAUDE.md")])

    target_dir = tmp_path / "my-app"
    assert main(["init", "my-app", "--yes", "--dir", str(target_dir)]) == 0

    assert "questionary" not in sys.modules
