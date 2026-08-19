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
    skills_items: frozenset[str] = frozenset({"caveman"}),
    mcp_items: frozenset[str] = frozenset({"code-memory"}),
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
    ans = _answers(tmp_path, skills_items=frozenset({"caveman"}))
    _make_complete_project(tmp_path, ans)
    shutil.rmtree(tmp_path / ".agents" / "skills" / "caveman")

    with pytest.raises(VerificationError, match="selected skills item 'caveman' is missing"):
        verify_project(tmp_path, ans, CATALOG)


def test_verify_rejects_a_real_occupant_at_a_skill_link_path(tmp_path: Path) -> None:
    ans = _answers(tmp_path, skills_items=frozenset({"caveman"}))
    _make_complete_project(tmp_path, ans)
    link = tmp_path / ".claude" / "skills" / "caveman"
    if link.is_symlink() or link.is_junction():
        link.unlink()
    elif link.exists():
        shutil.rmtree(link)
    link.write_text("not a link\n", encoding="utf-8")

    with pytest.raises(VerificationError, match="invalid Skill Link structure"):
        verify_project(tmp_path, ans, CATALOG)


def test_verify_rejects_missing_canonical_rules(tmp_path: Path) -> None:
    ans = _answers(tmp_path)
    _make_complete_project(tmp_path, ans)
    (tmp_path / "AGENTS.md").unlink()

    with pytest.raises(VerificationError, match="required file 'AGENTS.md' is missing"):
        verify_project(tmp_path, ans, CATALOG)


def test_verify_raises_when_unselected_mcp_effect_is_present(tmp_path: Path) -> None:
    ans = _answers(tmp_path, mcp_items=frozenset())
    _make_complete_project(tmp_path, ans)
    (tmp_path / ".mcp.json").write_text(
        '{"mcpServers":{"codebase-memory":{"command":"uvx",'
        '"args":["codebase-memory-mcp==0.9.0"]}}}',
        encoding="utf-8",
    )

    with pytest.raises(
        VerificationError,
        match="unselected mcp item 'code-memory' left inject effect",
    ):
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
        skills_items=frozenset({"caveman", "react-doctor"}),
        mcp_items=frozenset({"code-memory"}),
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
        mcp_items=frozenset(),
    )
    _make_complete_project(tmp_path, ans)
    verify_project(tmp_path, ans, CATALOG)  # passes

    # Leaked code-memory server entry while code-memory is unselected -> raises
    mcp_json: dict[str, object] = {}
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
    ans = _answers(tmp_path, skills_items=frozenset({"mattpocock"}), mcp_items=frozenset())
    _make_complete_project(tmp_path, ans)
    shutil.rmtree(tmp_path / "docs" / "agents")

    with pytest.raises(
        VerificationError,
        match="selected development loop item 'mattpocock' is missing",
    ):
        verify_project(tmp_path, ans, CATALOG)


def test_verify_rejects_a_project_record_missing_the_mandatory_loop(
    tmp_path: Path,
) -> None:
    selection = ProjectSelection.empty()
    materialize_project_structure(tmp_path, CATALOG, selection)
    answers = Answers("my-app", tmp_path, selection)

    with pytest.raises(
        VerificationError,
        match="development loop item 'mattpocock'.*missing",
    ):
        verify_project(tmp_path, answers, CATALOG)


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
    ans = _answers(tmp_path, skills_items=frozenset({"mattpocock"}), mcp_items=frozenset())
    _make_generated_project(tmp_path, ans)
    (tmp_path / ".agents" / "skills" / "domain-modeling" / "ADR-FORMAT.md").unlink()

    with pytest.raises(
        VerificationError,
        match="selected development loop item 'mattpocock'.*ADR-FORMAT.md.*missing",
    ):
        verify_project(tmp_path, ans, CATALOG)


def test_verify_rejects_a_partial_loop_for_a_malformed_empty_selection(
    tmp_path: Path,
) -> None:
    selection = ProjectSelection.empty()
    ans = Answers("my-app", tmp_path, selection)
    _make_complete_project(tmp_path, ans)
    leaked = tmp_path / ".agents" / "skills" / "to-spec"
    leaked.mkdir(parents=True)
    (leaked / "SKILL.md").write_text("leaked", encoding="utf-8")

    with pytest.raises(
        VerificationError,
        match="development loop item 'mattpocock'.*missing",
    ):
        verify_project(tmp_path, ans, CATALOG)


