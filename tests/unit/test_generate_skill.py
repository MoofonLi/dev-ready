"""Contract tests for the repository-distributed dev-ready Agent Skill."""

from __future__ import annotations

import json
import re
import shlex
from pathlib import Path

from dev_ready.cli import build_answers, build_parser
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


def _documented_ids(text: str, component: str) -> set[str]:
    label = "MCP" if component == "mcp" else component
    match = re.search(rf"^Current {label} ids: (.+)$", text, flags=re.MULTILINE)
    assert match is not None
    return set(re.findall(r"`([^`]+)`", match.group(1)))


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
    assert any("--skills all" in command and "--mcp all" in command for command in examples)
    assert any("--skills none" in command and "--mcp none" in command for command in examples)
    assert any(
        "--skills spec-loop,frontend-design" in command
        and "--mcp code-memory" in command
        for command in examples
    )

    for command in examples:
        tokens = shlex.split(command)
        assert tokens[:2] == ["uvx", "dev-ready"]
        args = build_parser().parse_args(tokens[2:])
        build_answers(args, CATALOG)


def test_skill_catalog_ids_match_the_current_manifest() -> None:
    text = _skill_text()
    for component in ("skills", "mcp"):
        assert _documented_ids(text, component) == {
            item.id for item in CATALOG[component]
        }


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
        "--no-skills",
        "--no-mcp",
        "--no-docs",
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
    assert "--no-handoff" not in text
    assert "--no-agents" not in text
    assert "handoff protocol" not in text


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
