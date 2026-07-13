"""Unit tests for dev_ready.cli."""

import argparse
from pathlib import Path

import pytest

import dev_ready.cli as cli_module
from dev_ready import __version__
from dev_ready.cli import build_answers, build_parser, main
from dev_ready.errors import FetchError, InvalidArgumentsError, OverlayError, TargetDirectoryError
from dev_ready.prompts import Answers


def _init_args(**overrides) -> argparse.Namespace:
    defaults = {
        "project_name": "my-app",
        "yes": False,
        "target_dir": None,
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
        build_answers(_init_args(project_name=bad_name))


def test_init_unsafe_name_exits_2(capsys) -> None:
    assert main(["init", "../etc"]) == 2
    assert "error:" in capsys.readouterr().err


def test_init_success_exits_0_and_prints_summary(
    tmp_path, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    target_dir = tmp_path / "my-app"

    def _fake_generate(answers: Answers, pin) -> list[Path]:
        assert answers.project_name == "my-app"
        return [Path("CLAUDE.md"), Path(".mcp.json")]

    monkeypatch.setattr(cli_module, "generate", _fake_generate)

    assert main(["init", "my-app", "--yes", "--dir", str(target_dir)]) == 0
    out = capsys.readouterr().out
    assert "my-app" in out
    assert str(target_dir) in out
    assert "fastapi/full-stack-fastapi-template" in out
    assert "next steps" in out


def test_init_success_omits_disabled_components_from_summary(
    tmp_path, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    monkeypatch.setattr(cli_module, "generate", lambda answers, pin: [Path("CLAUDE.md")])

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


@pytest.mark.parametrize(
    ("error", "expected_exit_code"),
    [
        (FetchError("network down"), 3),
        (TargetDirectoryError("dir taken"), 4),
        (OverlayError("collision"), 1),
    ],
)
def test_init_maps_generate_errors_to_exit_codes(
    monkeypatch: pytest.MonkeyPatch, capsys, error: Exception, expected_exit_code: int
) -> None:
    def _raising_generate(answers: Answers, pin) -> list[Path]:
        raise error

    monkeypatch.setattr(cli_module, "generate", _raising_generate)

    assert main(["init", "my-app", "--yes"]) == expected_exit_code
    assert "error:" in capsys.readouterr().err


def test_init_flags_reach_generate_via_answers(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, Answers] = {}

    def _capturing_generate(answers: Answers, pin) -> list[Path]:
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
    answers = build_answers(_init_args())
    assert answers.project_name == "my-app"
    assert answers.target_dir == Path.cwd() / "my-app"
    assert answers.include_skills is True
    assert answers.include_mcp is True
    assert answers.include_docs is True
    assert answers.assume_yes is False


def test_build_answers_respects_flags(tmp_path) -> None:
    answers = build_answers(
        _init_args(yes=True, target_dir=tmp_path / "out", no_skills=True, no_mcp=True)
    )
    assert answers.target_dir == tmp_path / "out"
    assert answers.include_skills is False
    assert answers.include_mcp is False
    assert answers.include_docs is True
    assert answers.assume_yes is True


def test_parser_accepts_all_documented_flags() -> None:
    args = build_parser().parse_args(
        ["init", "my-app", "-y", "--dir", "x", "--no-skills", "--no-mcp", "--no-docs"]
    )
    assert args.command == "init"
    assert args.yes is True
    assert args.target_dir == Path("x")
