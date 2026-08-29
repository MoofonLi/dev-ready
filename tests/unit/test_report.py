"""Unit tests for dev_ready.report (pure function; no filesystem, no network)."""

from pathlib import Path
import re

import pytest

from dev_ready.manifest import UpstreamPin, load_default_manifest
from dev_ready.intent import Answers, ProjectSelection
from dev_ready.presentation import PresentationStyle
from dev_ready.report import render
from dev_ready.report import render_report

PIN = UpstreamPin(
    repo="fastapi/full-stack-fastapi-template",
    ref="master",
    commit="4cd0d9e51aebd1af6f82d91ad0df4c9e41f4dea2",
    license="MIT",
)
CATALOG = load_default_manifest().components
_ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*m")


def test_report_summarises_written_paths_with_a_count_and_breakdown() -> None:
    answers = Answers(project_name="my-app", target_dir=Path("/does/not/exist/my-app"))
    written = [
        Path("CLAUDE.md"),
        Path(".agents") / "skills" / "caveman" / "SKILL.md",
        Path(".mcp.json"),
        Path("docs") / "requirements.md",
        Path(".windsurf") / "skills" / "caveman" / "SKILL.md",
    ]

    report = render_report(answers, PIN, written)
    normalized_report = " ".join(report.split())

    assert str(answers.target_dir) in report
    assert f"{PIN.repo}@{PIN.commit[:12]}" in report
    assert "overlay files written: 5" in report
    assert "root files: 2" in report
    assert "canonical agent content: 1" in report
    assert "documentation: 1" in report
    assert "Agent Target artifacts: 1" in normalized_report
    for path in written:
        assert str(path) not in report
    assert '"inventory" entries in .dev-ready.json' in report
    # FR-44 as amended 2026-08-14: the report points at the stamp's inventory,
    # not at `dev-ready check`, which renders a drift verdict and never the paths.
    assert "dev-ready check" not in report


def test_report_contains_runnable_next_steps() -> None:
    answers = Answers(project_name="my-app", target_dir=Path("/does/not/exist/my-app"))

    report = render_report(answers, PIN, [Path("CLAUDE.md")])

    assert "Next Steps" in report
    assert f"cd {answers.target_dir}" in report
    assert "AGENTS.md" in report


def test_report_omits_redundant_cd_and_renumbers_steps_in_current_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    answers = Answers(
        project_name=tmp_path.name,
        target_dir=tmp_path,
        selection=ProjectSelection.default_set(CATALOG),
    )

    report = render_report(answers, PIN, [], CATALOG)

    assert f"cd {tmp_path}" not in report
    assert "  1. ask your coding agent to run `/setup-project`" in report
    assert "  2. docker compose watch" in report
    assert "  3. read AGENTS.md" in report
    assert "  4. after cloning" in report
    assert "  5." not in report


def test_report_colour_is_decoration_and_preserves_a_bracketed_destination() -> None:
    answers = Answers(
        project_name="my-app",
        target_dir=Path("/projects/[draft]/my-app"),
    )

    plain = render_report(answers, PIN, [], style=PresentationStyle())
    coloured = render_report(
        answers,
        PIN,
        [],
        style=PresentationStyle(color=True, width=80),
    )

    assert "\x1b" in coloured
    assert _ANSI_ESCAPE.sub("", coloured) == plain
    # str(), not the literal: on Windows the separator is a backslash. The
    # square brackets are the point — Rich must not read them as markup.
    assert str(answers.target_dir) in coloured
    assert "[draft]" in coloured


@pytest.mark.parametrize(
    "selection",
    [ProjectSelection.default_set(CATALOG), ProjectSelection.all(CATALOG)],
)
def test_report_names_setup_project_before_first_start(
    selection: ProjectSelection,
) -> None:
    answers = Answers(
        project_name="my-app",
        target_dir=Path("/does/not/exist/my-app"),
        selection=selection,
    )

    report = render_report(answers, PIN, [], CATALOG)

    assert report.index("setup-project") < report.index("docker compose watch")
    assert "before the first start" in report


def test_actionable_steps_precede_selection_login_and_overlay_summary() -> None:
    answers = Answers(
        project_name="my-app",
        target_dir=Path("/does/not/exist/my-app"),
        selection=ProjectSelection.default_set(CATALOG),
    )

    report = render_report(answers, PIN, [Path("CLAUDE.md")], CATALOG)

    assert report.index("location:") < report.index("Next Steps:")
    assert report.index("Next Steps:") < report.index("Engineering Flow")
    assert report.index("Engineering Flow") < report.index("standard-compliant agents")
    assert report.index("standard-compliant agents") < report.index("First Login:")
    assert report.index("First Login:") < report.index("Overlay Summary:")


def test_report_separates_title_case_sections_with_blank_lines() -> None:
    answers = Answers(project_name="my-app", target_dir=Path("/does/not/exist/my-app"))

    report = render_report(answers, PIN, [Path("CLAUDE.md")])

    assert "\n\nNext Steps:\n" in report
    assert "\n\nFirst Login:\n" in report
    assert "\n\nOverlay Summary:\n" in report


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


def test_report_names_the_superuser_login_and_where_its_password_is() -> None:
    """FR-38: a user reaches a login form and must know what to type."""
    answers = Answers(project_name="my-app", target_dir=Path("/does/not/exist/my-app"))

    report = render_report(answers, PIN, [Path("CLAUDE.md")])

    assert "admin@example.com" in report
    assert "FIRST_SUPERUSER_PASSWORD" in report
    assert ".env" in report


def test_report_states_that_changing_the_password_after_first_start_does_nothing() -> None:
    answers = Answers(project_name="my-app", target_dir=Path("/does/not/exist/my-app"))

    report = render_report(answers, PIN, [Path("CLAUDE.md")])

    assert "first start" in report
    assert "reset" in report


def test_report_names_the_password_key_but_never_a_value() -> None:
    """The property that must survive the next edit to the renderer.

    A secret echoed to a terminal lands in scrollback, in CI logs, and in
    whatever captured the command's output. Naming the key is enough; together
    with `test_report_does_not_touch_the_filesystem` this pins the renderer to
    text it can compose without ever holding a secret.
    """
    answers = Answers(project_name="my-app", target_dir=Path("/does/not/exist/my-app"))

    report = render_report(answers, PIN, [Path("CLAUDE.md")], CATALOG)

    assert "FIRST_SUPERUSER_PASSWORD=" not in report
    # The other two generated secrets have no reason to be mentioned at all.
    assert "SECRET_KEY" not in report
    assert "POSTGRES_PASSWORD" not in report


def test_report_states_selected_target_artifacts_and_manual_windsurf_mcp() -> None:
    answers = Answers(
        project_name="my-app",
        target_dir=Path("/does/not/exist/my-app"),
        selection=ProjectSelection.from_items(
            CATALOG,
            skills=frozenset({"caveman"}),
            mcp=frozenset({"code-memory"}),
            agent_targets=frozenset({"claude", "windsurf"}),
        ),
    )

    report = render_report(answers, PIN, [], CATALOG)

    assert "claude:" in report
    assert "CLAUDE.md" in report
    assert ".claude/skills" in report
    assert ".mcp.json" in report
    assert "windsurf:" in report
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
    assert "setup-project" in report


def test_report_distinguishes_required_loop_from_selected_enhancements() -> None:
    default_answers = Answers(
        project_name="my-app",
        target_dir=Path("/does/not/exist/my-app"),
        selection=ProjectSelection.default_set(CATALOG),
    )

    default_report = render_report(default_answers, PIN, [], CATALOG)

    assert "Engineering Flow (required): mattpocock" in default_report
    assert "documentation skeletons: architecture, requirements" in default_report
    assert "enhancements: (none)" in default_report

    enhanced_answers = Answers(
        project_name="my-app",
        target_dir=Path("/does/not/exist/my-app"),
        selection=ProjectSelection.from_items(
            CATALOG,
            skills=frozenset({"security-audit"}),
            docs_items=frozenset(),
        ),
    )
    enhanced_report = render_report(enhanced_answers, PIN, [], CATALOG)

    assert "Engineering Flow (required): mattpocock" in enhanced_report
    assert "documentation skeletons: architecture, requirements" in enhanced_report
    assert "enhancements: security-audit" in enhanced_report


def test_report_states_standard_compliant_agents_needing_no_target_selection() -> None:
    answers = Answers(
        project_name="my-app",
        target_dir=Path("/does/not/exist/my-app"),
        selection=ProjectSelection.default_set(CATALOG),
    )

    report = render_report(answers, PIN, [], CATALOG)

    assert "standard-compliant agents" in report
    assert "read .agents/skills/ directly" in report
    agent_summary = " ".join(
        report[
            report.index("standard-compliant agents") : report.index("\nagent targets")
        ].split()
    )
    assert f"({len(CATALOG.standard_compliant_agents)};" in agent_summary
    assert "codex, cursor, gemini-cli, …" in agent_summary
    unfeatured_agents = set(CATALOG.standard_compliant_agents) - {
        "codex",
        "cursor",
        "gemini-cli",
    }
    assert all(agent_id not in agent_summary for agent_id in unfeatured_agents)


def test_report_example_agents_exist_in_the_standard_compliant_agent_list() -> None:
    for agent_id in ("codex", "cursor", "gemini-cli"):
        assert agent_id in CATALOG.standard_compliant_agents


@pytest.mark.parametrize(
    "selection",
    [ProjectSelection.default_set(CATALOG), ProjectSelection.all(CATALOG)],
)
def test_report_is_plain_text_for_default_and_whole_catalog(
    selection: ProjectSelection,
) -> None:
    answers = Answers(
        project_name="my-app",
        target_dir=Path("/does/not/exist/my-app"),
        selection=selection,
    )

    report = render_report(
        answers,
        PIN,
        [Path("CLAUDE.md"), Path("docs") / "requirements.md"],
        CATALOG,
    )

    assert "\x1b" not in report
    assert [
        line
        for line in report.splitlines()
        if line in {"Next Steps:", "First Login:", "Overlay Summary:"}
    ] == ["Next Steps:", "First Login:", "Overlay Summary:"]


def test_report_and_readme_template_disclose_the_same_superuser_email() -> None:
    """FR-38 states the login on two dev-ready-owned surfaces; they must agree.

    Neither surface derives the address — it is upstream's own `first_superuser`
    default, which `_template_data` deliberately does not override. This test is
    what stops the two copies drifting apart; `scripts/check_stack_facts.py`
    holds the README's copy to the pinned commit via the generated `.env`, so
    together they keep both surfaces true without either one deriving the value.
    """
    template = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "dev_ready"
        / "templates"
        / "readme"
        / "README.md.tmpl"
    ).read_text(encoding="utf-8")

    assert f"`{render._SUPERUSER_EMAIL}`" in template
