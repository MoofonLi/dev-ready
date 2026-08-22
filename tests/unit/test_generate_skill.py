"""Contract tests for the repository-distributed dev-ready Agent Skill."""

from __future__ import annotations

import json
import re
import shlex
from pathlib import Path

import pytest

from dev_ready import __version__
from dev_ready.cli import build_answers, build_parser
from dev_ready.errors import InvalidArgumentsError
from dev_ready.manifest import load_default_manifest
from dev_ready.overlay import build_overlay_content, render_stamp
from dev_ready.prompts import Answers, ProjectSelection

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_PATH = REPO_ROOT / "skills" / "dev-ready" / "SKILL.md"
SUBMISSION_PATH = REPO_ROOT / "docs" / "plugin-directory-submission.md"
CLAUDE_PLUGIN_MANIFEST = REPO_ROOT / ".claude-plugin" / "plugin.json"
CLAUDE_MARKETPLACE = REPO_ROOT / ".claude-plugin" / "marketplace.json"
CODEX_PLUGIN_MANIFEST = REPO_ROOT / ".codex-plugin" / "plugin.json"
CODEX_MARKETPLACE = REPO_ROOT / ".agents" / "plugins" / "marketplace.json"
PLUGIN_COMPONENT_NAMES = frozenset(
    {
        "agents",
        "commands",
        "hooks",
        "bin",
        "monitors",
        ".mcp.json",
        ".lsp.json",
        "settings.json",
    }
)
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
    elif label == "Engineering Flow":
        heading = "Engineering Flows"
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
        and "--flow mattpocock" in command
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
    assert _documented_ids(text, "Engineering Flow") == set(
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
        with pytest.raises(InvalidArgumentsError, match="mandatory Engineering Flow"):
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
    original = _skill_text()
    text = original.casefold()
    for required in (
        "--yes",
        "--dir",
        "--categories",
        "--flow",
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
        "superpowers",
        "addyosmani",
    ):
        assert required in text
    assert "--development-loop" not in original
    assert "Engineering Flow id 'spec-loop' was renamed to 'mattpocock'" in original
    assert "Engineering Flow 'addyosmani' is not yet available" in original
    assert "unknown Engineering Flow id" in original
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
        "--flow",
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


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _declared_skill_paths(declared: str | list[str]) -> list[str]:
    if isinstance(declared, str):
        return [declared]
    return list(declared)


def _contains_distributed_skill(location: Path) -> bool:
    return (location / "SKILL.md").is_file() or (
        location / "dev-ready" / "SKILL.md"
    ).is_file()


def _catalog_source_path(source: str | dict) -> str:
    if isinstance(source, str):
        return source
    return source["path"]


def test_plugin_distribution_files_resolve_to_the_distributed_skill() -> None:
    claude_plugin = _load_json(CLAUDE_PLUGIN_MANIFEST)
    claude_marketplace = _load_json(CLAUDE_MARKETPLACE)
    codex_plugin = _load_json(CODEX_PLUGIN_MANIFEST)
    codex_marketplace = _load_json(CODEX_MARKETPLACE)

    assert claude_plugin["name"] == "dev-ready"
    assert claude_plugin["skills"] == ["./skills/dev-ready"]
    assert claude_marketplace["name"] == "dev-ready"
    assert claude_marketplace["owner"]["name"]
    assert codex_plugin["name"] == "dev-ready"
    assert codex_plugin["description"]
    assert codex_marketplace["name"] == "dev-ready"
    assert codex_marketplace["interface"]["displayName"]

    assert len(claude_marketplace["plugins"]) == 1
    claude_entry = claude_marketplace["plugins"][0]
    assert claude_entry["name"] == "dev-ready"
    assert claude_entry["skills"] == ["./skills/dev-ready"]
    assert (REPO_ROOT / _catalog_source_path(claude_entry["source"])).resolve() == (
        REPO_ROOT.resolve()
    )

    assert len(codex_marketplace["plugins"]) == 1
    codex_entry = codex_marketplace["plugins"][0]
    assert codex_entry["name"] == "dev-ready"
    assert codex_entry["policy"]["installation"]
    assert codex_entry["policy"]["authentication"]
    assert codex_entry["category"]
    assert (REPO_ROOT / _catalog_source_path(codex_entry["source"])).resolve() == (
        REPO_ROOT.resolve()
    )

    for declared in (
        claude_plugin["skills"],
        claude_entry["skills"],
        codex_plugin["skills"],
    ):
        for relative in _declared_skill_paths(declared):
            assert _contains_distributed_skill(REPO_ROOT / relative)


def test_plugin_manifest_versions_match_the_package() -> None:
    for path in (CLAUDE_PLUGIN_MANIFEST, CODEX_PLUGIN_MANIFEST):
        assert _load_json(path)["version"] == __version__


def test_repository_root_ships_only_the_distributed_skill() -> None:
    root_names = {path.name for path in REPO_ROOT.iterdir()}
    assert root_names & PLUGIN_COMPONENT_NAMES == set()
    skill_entries = sorted(
        path.name
        for path in (REPO_ROOT / "skills").iterdir()
        if not path.name.startswith(".")
    )
    assert skill_entries == ["dev-ready"]
    assert SKILL_PATH.is_file()


def test_submission_positive_cases_parse_through_the_real_cli() -> None:
    submission = SUBMISSION_PATH.read_text(encoding="utf-8")
    commands = _init_examples(submission)
    assert len(commands) == 6
    assert any("--flow superpowers" in command for command in commands)
    assert (
        "The agent starts each step on its own, and implementation can be split "
        "across fresh subagents."
    ) in submission
    for command in commands:
        tokens = shlex.split(command)
        assert tokens[:2] == ["uvx", "dev-ready"]
        args = build_parser().parse_args(tokens[2:])
        build_answers(args, CATALOG)
