"""Unit tests for dev_ready.verify (no network, filesystem confined to tmp_path)."""

from pathlib import Path
import shutil

import pytest

from dev_ready.errors import VerificationError
from dev_ready.verify import FORBIDDEN_PATHS, REQUIRED_UPSTREAM_PATHS, verify_project


from dev_ready.manifest import load_default_manifest
from dev_ready.overlay import apply_overlay
from dev_ready.prompts import Answers, ProjectSelection
from project_factory import materialize_project_structure

CATALOG = load_default_manifest().components
MANIFEST = load_default_manifest()
PIN = MANIFEST.upstream["base_template"]


def _answers(
    tmp_path: Path,
    *,
    skills_items: frozenset[str] = frozenset({"project-orientation"}),
    mcp_items: frozenset[str] = frozenset({"mcp-config"}),
) -> Answers:
    return Answers(
        project_name="my-app",
        target_dir=tmp_path / "my-app",
        selection=ProjectSelection.from_items(
            CATALOG,
            skills=skills_items,
            mcp=mcp_items,
        ),
    )


def _make_complete_project(root: Path, answers: Answers | None = None) -> None:
    ans = answers or _answers(root)
    materialize_project_structure(root, CATALOG, ans.selection)


def test_verify_passes_when_all_required_paths_present(tmp_path: Path) -> None:
    ans = _answers(tmp_path)
    _make_complete_project(tmp_path, ans)
    verify_project(tmp_path, ans, CATALOG)  # must not raise


@pytest.mark.parametrize("missing_path", REQUIRED_UPSTREAM_PATHS)
def test_verify_raises_when_one_required_path_is_missing(
    tmp_path: Path, missing_path: str
) -> None:
    ans = _answers(tmp_path)
    _make_complete_project(tmp_path, ans)
    target = tmp_path / missing_path
    if target.is_dir():
        target.rmdir()
    else:
        target.unlink()

    with pytest.raises(VerificationError) as excinfo:
        verify_project(tmp_path, ans, CATALOG)

    message = str(excinfo.value)
    assert missing_path in message


def test_verify_error_message_contains_actionable_guidance(tmp_path: Path) -> None:
    # Empty project dir: the first path in REQUIRED_UPSTREAM_PATHS is missing.
    tmp_path_missing = tmp_path / "empty"
    tmp_path_missing.mkdir()

    ans = _answers(tmp_path)
    with pytest.raises(VerificationError) as excinfo:
        verify_project(tmp_path_missing, ans, CATALOG)

    message = str(excinfo.value)
    assert "upstream layout changed" in message
    assert "file an issue" in message


@pytest.mark.parametrize("forbidden_path", FORBIDDEN_PATHS)
def test_verify_raises_when_forbidden_path_is_present(
    tmp_path: Path, forbidden_path: str
) -> None:
    ans = _answers(tmp_path)
    _make_complete_project(tmp_path, ans)
    target = tmp_path / forbidden_path
    if forbidden_path in (".git", ".copier"):
        target.mkdir(parents=True, exist_ok=True)
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("stub", encoding="utf-8")

    with pytest.raises(VerificationError) as excinfo:
        verify_project(tmp_path, ans, CATALOG)

    message = str(excinfo.value)
    assert forbidden_path in message
    assert "file an issue" in message


def test_verify_raises_when_stamp_file_is_missing(tmp_path: Path) -> None:
    ans = _answers(tmp_path)
    _make_complete_project(tmp_path, ans)
    (tmp_path / ".dev-ready.json").unlink()

    with pytest.raises(VerificationError, match="missing required overlay path '.dev-ready.json'"):
        verify_project(tmp_path, ans, CATALOG)


def test_verify_raises_when_selected_item_path_is_missing(tmp_path: Path) -> None:
    ans = _answers(tmp_path, skills_items=frozenset({"project-orientation"}))
    _make_complete_project(tmp_path, ans)
    shutil.rmtree(tmp_path / ".claude" / "skills" / "project-orientation")

    with pytest.raises(VerificationError, match="selected skills item 'project-orientation' is missing"):
        verify_project(tmp_path, ans, CATALOG)


def test_verify_raises_when_unselected_item_path_is_present(tmp_path: Path) -> None:
    ans = _answers(tmp_path, mcp_items=frozenset())
    _make_complete_project(tmp_path, ans)
    # create .mcp.json which should not be present when mcp_items is empty
    (tmp_path / ".mcp.json").write_text("stub", encoding="utf-8")

    with pytest.raises(VerificationError, match="unselected mcp item 'mcp-config' left path"):
        verify_project(tmp_path, ans, CATALOG)


def test_verify_always_applied_files_with_unselected_item_still_passes(tmp_path: Path) -> None:
    ans = _answers(tmp_path, mcp_items=frozenset())
    _make_complete_project(tmp_path, ans)
    # create always applied file CLAUDE.md
    (tmp_path / "CLAUDE.md").write_text("stub", encoding="utf-8")
    verify_project(tmp_path, ans, CATALOG)


def test_verify_selection_matrix_all_on(tmp_path: Path) -> None:
    ans = _answers(
        tmp_path,
        skills_items=frozenset({"project-orientation", "react-doctor"}),
        mcp_items=frozenset({"mcp-config", "code-memory"}),
    )
    _make_complete_project(tmp_path, ans)
    verify_project(tmp_path, ans, CATALOG)  # must not raise


def test_verify_selection_matrix_all_off(tmp_path: Path) -> None:
    ans = _answers(tmp_path, skills_items=frozenset(), mcp_items=frozenset())
    _make_complete_project(tmp_path, ans)
    verify_project(tmp_path, ans, CATALOG)  # must not raise


def test_verify_selection_matrix_mixed_and_negative(tmp_path: Path) -> None:
    import json

    ans = _answers(
        tmp_path,
        skills_items=frozenset({"react-doctor"}),
        mcp_items=frozenset({"mcp-config"}),
    )
    _make_complete_project(tmp_path, ans)
    verify_project(tmp_path, ans, CATALOG)  # passes

    # Leaked code-memory server entry while code-memory is unselected -> raises
    mcp_json = json.loads((tmp_path / ".mcp.json").read_text(encoding="utf-8"))
    mcp_json.setdefault("mcpServers", {})["codebase-memory"] = {
        "command": "uvx",
        "args": ["codebase-memory-mcp==0.9.0"],
    }
    (tmp_path / ".mcp.json").write_text(json.dumps(mcp_json), encoding="utf-8")
    with pytest.raises(VerificationError, match="unselected mcp item 'code-memory' left inject effect"):
        verify_project(tmp_path, ans, CATALOG)

    # Clean up code-memory from .mcp.json
    del mcp_json["mcpServers"]["codebase-memory"]
    (tmp_path / ".mcp.json").write_text(json.dumps(mcp_json), encoding="utf-8")

    # Missing react-doctor devDependency while selected -> raises
    (tmp_path / "frontend" / "package.json").write_text("{}", encoding="utf-8")
    with pytest.raises(VerificationError, match="selected skills item 'react-doctor' is missing its inject effect"):
        verify_project(tmp_path, ans, CATALOG)


def test_verify_rejects_missing_selected_spec_loop_configuration(tmp_path: Path) -> None:
    ans = _answers(tmp_path, skills_items=frozenset({"spec-loop"}), mcp_items=frozenset())
    _make_complete_project(tmp_path, ans)
    shutil.rmtree(tmp_path / "docs" / "agents")

    with pytest.raises(VerificationError, match="selected skills item 'spec-loop' is missing"):
        verify_project(tmp_path, ans, CATALOG)


def _make_generated_project(root: Path, answers: Answers) -> None:
    for relative in REQUIRED_UPSTREAM_PATHS:
        path = root / relative
        if relative in {"backend", "frontend"}:
            path.mkdir(parents=True, exist_ok=True)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("upstream", encoding="utf-8")
    apply_overlay(answers, root, CATALOG, PIN, MANIFEST.vendored)


def test_verify_detects_a_missing_nested_spec_loop_asset(tmp_path: Path) -> None:
    ans = _answers(tmp_path, skills_items=frozenset({"spec-loop"}), mcp_items=frozenset())
    _make_generated_project(tmp_path, ans)
    (tmp_path / ".claude" / "skills" / "domain-modeling" / "ADR-FORMAT.md").unlink()

    with pytest.raises(
        VerificationError,
        match="selected skills item 'spec-loop'.*ADR-FORMAT.md.*missing",
    ):
        verify_project(tmp_path, ans, CATALOG)


def test_verify_rejects_a_deselected_spec_loop_asset(tmp_path: Path) -> None:
    ans = _answers(tmp_path, skills_items=frozenset(), mcp_items=frozenset())
    _make_generated_project(tmp_path, ans)
    leaked = tmp_path / ".claude" / "skills" / "to-spec"
    leaked.mkdir(parents=True)
    (leaked / "SKILL.md").write_text("leaked", encoding="utf-8")

    with pytest.raises(VerificationError, match="unselected skills item 'spec-loop'"):
        verify_project(tmp_path, ans, CATALOG)


