"""Unit tests for dev_ready.verify (no network, filesystem confined to tmp_path)."""

from pathlib import Path

import pytest

from dev_ready.errors import VerificationError
from dev_ready.verify import FORBIDDEN_PATHS, REQUIRED_UPSTREAM_PATHS, verify_project


from dev_ready.manifest import load_default_manifest
from dev_ready.prompts import Answers

CATALOG = load_default_manifest().components
_DIRECTORY_ENTRIES = {"backend", "frontend"}


def _answers(tmp_path: Path, **overrides: object) -> Answers:
    defaults: dict[str, object] = {
        "project_name": "my-app",
        "target_dir": tmp_path / "my-app",
        "include_skills": True,
        "include_mcp": True,
        "include_docs": True,
        "include_agents": True,
        "skills_items": frozenset({"project-orientation"}),
        "mcp_items": frozenset({"mcp-config"}),
    }
    defaults.update(overrides)
    return Answers(**defaults)  # type: ignore[arg-type]


def _make_complete_project(root: Path, answers: Answers | None = None) -> None:
    for rel_path in REQUIRED_UPSTREAM_PATHS:
        path = root / rel_path
        if rel_path in _DIRECTORY_ENTRIES:
            path.mkdir(parents=True, exist_ok=True)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("stub", encoding="utf-8")

    (root / ".dev-ready.json").write_text("{}", encoding="utf-8")

    ans = answers or _answers(root)
    for component, selected in (("skills", ans.skills_items), ("mcp", ans.mcp_items)):
        for item in CATALOG.get(component, ()):
            if item.id in selected:
                for item_path in item.paths:
                    dest = root / item_path.dest
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_text("stub", encoding="utf-8")


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
    (tmp_path / ".claude" / "skills" / "project-orientation").unlink()

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


