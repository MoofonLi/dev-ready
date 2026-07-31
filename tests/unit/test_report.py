"""Unit tests for dev_ready.report (pure function; no filesystem, no network)."""

from pathlib import Path

from dev_ready.manifest import UpstreamPin, load_default_manifest
from dev_ready.prompts import Answers, ProjectSelection
from dev_ready.report import render_report

PIN = UpstreamPin(
    repo="fastapi/full-stack-fastapi-template",
    ref="master",
    commit="4cd0d9e51aebd1af6f82d91ad0df4c9e41f4dea2",
    license="MIT",
)
CATALOG = load_default_manifest().components


def test_report_contains_target_path_pin_and_written_paths() -> None:
    answers = Answers(project_name="my-app", target_dir=Path("/does/not/exist/my-app"))
    written = [
        Path("CLAUDE.md"),
        Path(".claude") / "skills" / "caveman" / "SKILL.md",
        Path(".mcp.json"),
    ]

    report = render_report(answers, PIN, written)

    assert str(answers.target_dir) in report
    assert f"{PIN.repo}@{PIN.commit[:12]}" in report
    for path in written:
        assert str(path) in report


def test_report_contains_runnable_next_steps() -> None:
    answers = Answers(project_name="my-app", target_dir=Path("/does/not/exist/my-app"))

    report = render_report(answers, PIN, [Path("CLAUDE.md")])

    assert "next steps" in report
    assert f"cd {answers.target_dir}" in report
    assert "CLAUDE.md" in report


def test_report_omits_flag_names_when_component_disabled() -> None:
    """Regression for SRE-D: only real written paths appear, not flag shortnames."""
    answers = Answers(
        project_name="my-app",
        target_dir=Path("/does/not/exist/my-app"),
        selection=ProjectSelection.empty(),
    )

    report = render_report(answers, PIN, [Path("CLAUDE.md")])

    assert "skills" not in report
    assert "mcp" not in report
    assert "docs" not in report


def test_report_does_not_touch_the_filesystem(tmp_path: Path) -> None:
    ghost_dir = tmp_path / "ghost"  # deliberately never created
    answers = Answers(project_name="ghost", target_dir=ghost_dir)

    report = render_report(answers, PIN, [Path("CLAUDE.md"), Path("docs") / "architecture.md"])

    assert not ghost_dir.exists()
    assert str(ghost_dir) in report


def test_report_states_selected_target_artifacts_and_manual_windsurf_mcp() -> None:
    answers = Answers(
        project_name="my-app",
        target_dir=Path("/does/not/exist/my-app"),
        selection=ProjectSelection.from_items(
            CATALOG,
            skills=frozenset({"caveman"}),
            mcp=frozenset({"mcp-config"}),
            agent_targets=frozenset({"claude", "windsurf"}),
        ),
    )

    report = render_report(answers, PIN, [], CATALOG)

    assert "Claude Code" in report
    assert "CLAUDE.md" in report
    assert ".claude/skills" in report
    assert ".mcp.json" in report
    assert "Windsurf" in report
    assert ".windsurf/skills" in report
    assert "MCP configuration must be set up manually" in report


def test_report_states_when_no_agent_targets_were_selected() -> None:
    answers = Answers(
        project_name="my-app",
        target_dir=Path("/does/not/exist/my-app"),
        selection=ProjectSelection.from_items(
            CATALOG,
            agent_targets=frozenset(),
        ),
    )

    report = render_report(answers, PIN, [], CATALOG)

    assert "agent targets: (none)" in report
    assert "AGENTS.md" in report
