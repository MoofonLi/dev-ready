"""Unit tests for dev_ready.cli."""

import argparse
import io
import sys
from pathlib import Path

import pytest

import dev_ready.cli as cli_module
from dev_ready import __version__
from dev_ready.cli import ProgressRenderer, build_answers, build_parser, main
from dev_ready.errors import (
    AbortedError,
    FetchError,
    InvalidArgumentsError,
    OverlayError,
    TargetDirectoryError,
    VerificationError,
)
from dev_ready.generate import (
    CleanupWarningEvent,
    GenerationStage,
    ProgressEvent,
    ProgressStatus,
)
from dev_ready.manifest import load_default_manifest
from dev_ready.prompts import Answers

CATALOG = load_default_manifest().components


class _TTYBuffer(io.StringIO):
    def isatty(self) -> bool:
        return True


def _init_args(**overrides) -> argparse.Namespace:
    defaults = {
        "project_name": "my-app",
        "yes": False,
        "target_dir": None,
        "skills": None,
        "mcp": None,
        "agents": None,
        "no_skills": False,
        "no_mcp": False,
        "no_docs": False,
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
    assert "next steps" in out


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


def test_init_success_omits_disabled_components_from_summary(
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
                "--no-skills",
                "--no-mcp",
                "--no-docs",
            ]
        )
        == 0
    )
    out = capsys.readouterr().out
    assert "skills" not in out
    assert "mcp" not in out
    assert "docs" not in out
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
            "--no-skills",
            "--no-mcp",
        ]
    )

    answers = captured["answers"]
    assert answers.project_name == "my-app"
    assert answers.target_dir == target_dir
    assert answers.include_skills is False
    assert answers.include_mcp is False
    assert answers.include_docs is True
    assert answers.assume_yes is True


def test_build_answers_defaults() -> None:
    answers = build_answers(_init_args(), CATALOG)
    assert answers.project_name == "my-app"
    assert answers.target_dir == Path.cwd() / "my-app"
    assert answers.include_skills is True
    assert answers.include_mcp is True
    assert answers.skills_items == frozenset(
        {
            "react-doctor",
            "caveman",
                "security-audit",
                "spec-loop",
                "tdd",
            "diagnosing-bugs",
            "code-review",
            "webapp-testing",
            "frontend-design",
        }
    )
    assert answers.mcp_items == frozenset({"mcp-config", "code-memory"})
    assert answers.include_docs is True
    assert answers.assume_yes is False


def test_build_answers_respects_flags(tmp_path) -> None:
    answers = build_answers(
        _init_args(yes=True, target_dir=tmp_path / "out", no_skills=True, no_mcp=True),
        CATALOG,
    )
    assert answers.target_dir == tmp_path / "out"
    assert answers.include_skills is False
    assert answers.include_mcp is False
    assert answers.skills_items == frozenset()
    assert answers.mcp_items == frozenset()
    assert answers.include_docs is True
    assert answers.assume_yes is True


def test_parser_accepts_all_documented_flags() -> None:
    args = build_parser().parse_args(
        [
            "init",
            "my-app",
            "-y",
            "--dir",
            "x",
            "--skills",
            "caveman",
            "--mcp",
            "none",
            "--agents",
            "claude,windsurf",
            "--no-docs",
        ]
    )
    assert args.command == "init"
    assert args.yes is True
    assert args.target_dir == Path("x")
    assert args.skills == "caveman"
    assert args.mcp == "none"
    assert args.agents == "claude,windsurf"
    assert args.no_docs is True
    assert not hasattr(args, "no_handoff")
    assert not hasattr(args, "no_agents")


@pytest.mark.parametrize("removed_flag", ["--no-handoff", "--no-agents"])
def test_removed_handoff_flags_exit_2_before_generation(
    removed_flag: str,
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
    assert "Handoff Protocol" in error


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
    assert "claude" in error
    assert "windsurf" in error


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


def test_skills_and_mcp_item_flag_variations() -> None:
    # --skills all / --mcp none
    ans = build_answers(_init_args(skills="all", mcp="none"), CATALOG)
    assert ans.skills_items == frozenset(
        {
            "react-doctor",
            "caveman",
                "security-audit",
                "spec-loop",
                "tdd",
            "diagnosing-bugs",
            "code-review",
            "webapp-testing",
            "frontend-design",
        }
    )
    assert ans.mcp_items == frozenset()
    assert ans.include_skills is True
    assert ans.include_mcp is False

    # --skills caveman / --mcp mcp-config
    ans2 = build_answers(_init_args(skills="caveman", mcp="mcp-config"), CATALOG)
    assert ans2.skills_items == frozenset({"caveman"})
    assert ans2.mcp_items == frozenset({"mcp-config"})


def test_unknown_item_id_exits_2(capsys) -> None:
    assert main(["init", "my-app", "--yes", "--skills", "bogus"]) == 2
    err = capsys.readouterr().err
    assert "unknown skills item ids: ['bogus']" in err
    assert "valid ids: ['caveman', 'code-review', 'diagnosing-bugs', 'frontend-design', 'react-doctor', 'security-audit', 'spec-loop', 'tdd', 'webapp-testing']" in err


def test_removed_project_orientation_id_uses_standard_unknown_item_error(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["init", "my-app", "--yes", "--skills", "project-orientation"]) == 2
    error = capsys.readouterr().err
    assert "unknown skills item ids: ['project-orientation']" in error
    assert (
        "valid ids: ['caveman', 'code-review', 'diagnosing-bugs', "
        "'frontend-design', 'react-doctor', 'security-audit', 'spec-loop', "
        "'tdd', 'webapp-testing']"
    ) in error


def test_conflicting_flags_exits_2(capsys) -> None:
    assert main(["init", "my-app", "--yes", "--no-skills", "--skills", "caveman"]) == 2
    err = capsys.readouterr().err
    assert "--no-skills conflicts with --skills 'caveman'" in err


def test_no_skills_with_skills_none_is_allowed() -> None:
    ans = build_answers(_init_args(no_skills=True, skills="none"), CATALOG)
    assert ans.skills_items == frozenset()
    assert ans.include_skills is False


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

