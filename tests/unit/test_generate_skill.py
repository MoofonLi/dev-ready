"""Contract tests for the repository-distributed dev-ready Agent Skill."""

from __future__ import annotations

import json
import re
import shlex
from pathlib import Path

import pytest

from dev_ready.cli import build_answers, build_parser
from dev_ready.errors import InvalidArgumentsError
from dev_ready.manifest import load_default_manifest
from dev_ready.overlay import build_overlay_content, render_stamp
from dev_ready.prompts import Answers, ProjectSelection

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_PATH = REPO_ROOT / "skills" / "dev-ready" / "SKILL.md"
README_PATHS = (REPO_ROOT / "README.md", REPO_ROOT / "README-pypi.md")
INSTALL_COMMAND = "npx skills add MoofonLi/dev-ready --skill dev-ready"
ISSUES_URL = "https://github.com/MoofonLi/dev-ready/issues"
MANIFEST = load_default_manifest()
CATALOG = MANIFEST.components
EXPECTED_RETIRED_DEV_IDS = {
    "spec-loop",
    "tdd",
    "diagnosing-bugs",
    "code-review",
    "setup-all",
}


def _skill_text() -> str:
    return SKILL_PATH.read_text(encoding="utf-8")


def _frontmatter(text: str) -> dict[str, str]:
    opening, body, _rest = text.split("---", 2)
    assert opening == ""
    entries: dict[str, str] = {}
    for line in body.strip().splitlines():
        key, value = line.split(":", 1)
        entries[key.strip()] = value.strip()
    return entries


def _init_examples(text: str) -> list[str]:
    return re.findall(r"^uvx dev-ready init .+$", text, flags=re.MULTILINE)


def _documented_ids(text: str, label: str) -> set[str]:
    if label == "Category":
        heading = "Categories"
    elif label == "development loop":
        heading = "Development loops"
    elif label == "Agent Target":
        heading = "Agent Targets"
    elif label == "standard-compliant agent":
        heading = "Standard-compliant agents"
    else:
        assert label.endswith(" item")
        heading = f"{label.removesuffix(' item')} items"

    section = _mapping_section(text, heading)
    if re.fullmatch(r"\s*- \(none\)\s*", section):
        return set()
    entries = re.findall(
        r"^- `([^`]+)`:\s*(\S.*)$",
        section,
        flags=re.MULTILINE,
    )
    assert entries
    assert len(entries) == len({identifier for identifier, _trigger in entries})
    return {identifier for identifier, _trigger in entries}


def _mapping_section(text: str, heading: str) -> str:
    match = re.search(
        rf"^### {re.escape(heading)}\r?\n(?P<section>.*?)(?=^### |^## |\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    assert match is not None
    return match.group("section")


def _backticked_ids(text: str) -> set[str]:
    return set(re.findall(r"`([^`]+)`", text))


def _documented_retired_ids(text: str) -> set[str]:
    match = re.search(
        r"The former selectable\s+ids (?P<ids>.+?) now\s+exit 2",
        text,
        flags=re.DOTALL,
    )
    assert match is not None
    return _backticked_ids(match.group("ids"))


def test_skill_uses_the_minimal_standard_frontmatter_and_layout() -> None:
    assert SKILL_PATH.is_file()
    metadata = _frontmatter(_skill_text())
    assert metadata.keys() == {"name", "description"}
    assert metadata["name"] == "dev-ready"
    assert "FastAPI" in metadata["description"]
    assert "init" in metadata["description"]
    assert len(metadata["description"]) <= 1024


def test_skill_examples_cover_default_none_and_mixed_current_cli_contract() -> None:
    examples = _init_examples(_skill_text())
    assert len(examples) >= 3
    assert any("--categories all" in command and "--agents all" in command for command in examples)
    assert any("--categories none" in command and "--agents none" in command for command in examples)
    assert any(
        "--categories dev,design,token-optimize" in command
        and "--development-loop mattpocock" in command
        and "--dev none" in command
        and "--design frontend-design,design-stripe" in command
        and "--token-optimize code-memory" in command
        for command in examples
    )

    for command in examples:
        tokens = shlex.split(command)
        assert tokens[:2] == ["uvx", "dev-ready"]
        args = build_parser().parse_args(tokens[2:])
        build_answers(args, CATALOG)


def test_skill_examples_pair_user_answers_with_commands() -> None:
    text = _skill_text()
    for command in _init_examples(text):
        before_command = text[: text.index(command)].rstrip().splitlines()
        while before_command and (
            not before_command[-1].strip()
            or before_command[-1].strip().startswith("```")
        ):
            before_command.pop()
        assert before_command
        assert not before_command[-1].lstrip().startswith(("#", "uvx "))
        assert any(
            word in before_command[-1].casefold()
            for word in ("i ", "we ", "you ", "need", "want", "build")
        )


def test_skill_points_existing_projects_to_check_and_upgrade() -> None:
    text = _skill_text().casefold()
    assert "creates new projects only" in text
    assert "check" in text
    assert "upgrade" in text
    assert "init" in text
    assert "must never be aimed at" in text


def test_skill_category_and_item_ids_match_the_current_manifest() -> None:
    text = _skill_text()
    assert _documented_ids(text, "Category") == set(MANIFEST.categories)
    for category in MANIFEST.categories:
        assert _documented_ids(text, f"{category} item") == {
            item.id
            for component_items in CATALOG.values()
            for item in component_items
            if item.category == category and item.kind != "development-loop"
        }
    assert _documented_ids(text, "development loop") == set(
        CATALOG.development_loop_ids
    )
    assert _documented_ids(text, "Agent Target") == set(CATALOG.agent_target_ids)
    assert _documented_ids(text, "standard-compliant agent") == set(
        MANIFEST.standard_compliant_agents
    )
    retired_ids = _documented_retired_ids(text)
    assert retired_ids == EXPECTED_RETIRED_DEV_IDS
    for retired_id in retired_ids:
        args = build_parser().parse_args(
            ["init", "skill-test", "--yes", "--dev", retired_id]
        )
        with pytest.raises(InvalidArgumentsError, match="mandatory Dev development loop"):
            build_answers(args, CATALOG)


def test_skill_installation_and_public_docs_stay_synchronized() -> None:
    documents = (SKILL_PATH, *README_PATHS)
    for path in documents:
        text = path.read_text(encoding="utf-8")
        assert text.count(INSTALL_COMMAND) == 1, path


def test_public_docs_explain_discovery_agent_use_and_support() -> None:
    for path in README_PATHS:
        text = path.read_text(encoding="utf-8")
        assert "skills/dev-ready/SKILL.md" in text, path
        assert "npx skills add MoofonLi/dev-ready --list" in text, path
        assert "Scaffold a FastAPI project with dev-ready" in text, path
        assert ISSUES_URL in text, path


def test_skill_documents_safe_failure_and_verification_behavior() -> None:
    text = _skill_text().casefold()
    for required in (
        "--yes",
        "--dir",
        "--categories",
        "--development-loop",
        "--design",
        "--token-optimize",
        "--agents",
        "unknown category",
        "unknown item",
        "conflicting flags",
        "nonzero",
        "exit 2",
        "exit 3",
        "exit 4",
        "exit 5",
        ".dev-ready.json",
        "non-empty target",
        "do not delete",
    ):
        assert required in text
    for removed in ("--skills", "--mcp", "--no-docs", "--no-handoff", "--no-agents"):
        assert removed in text


def test_skill_leads_with_interview_before_selection_flags() -> None:
    text = _skill_text()
    body = text.split("---", 2)[2]
    sections = re.split(r"^## ", body, flags=re.MULTILINE)
    assert sections[1].startswith("Interview")

    interview_start = body.index("## Interview")
    pre_interview = body[:interview_start]
    selection_flags = (
        "--categories",
        "--dev",
        "--security",
        "--quality",
        "--design",
        "--token-optimize",
        "--agents",
        "--development-loop",
    )
    assert not any(flag in pre_interview for flag in selection_flags)


def test_distribution_skill_is_not_a_catalog_or_generated_overlay_asset(tmp_path: Path) -> None:
    assert "dev-ready" not in {
        item.id for items in CATALOG.values() for item in items
    }
    answers = Answers(
        project_name="skill-test",
        target_dir=tmp_path / "skill-test",
        selection=ProjectSelection.all(CATALOG),
    )
    content = build_overlay_content(answers, CATALOG)
    assert all("skills/dev-ready" not in path for path in content)

    stamp = json.loads(
        render_stamp(
            answers,
            MANIFEST.upstream["base_template"],
            CATALOG,
            MANIFEST.vendored,
            ((path, "0" * 64) for path in content),
        )
    )
    assert all("skills/dev-ready" not in entry["path"] for entry in stamp["inventory"])
    assert "dev-ready" not in {
        item["id"]
        for component in ("skills", "mcp")
        for item in stamp["components"][component]["items"]
    }
