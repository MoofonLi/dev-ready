"""Unit tests for the offline, transactional overlay upgrader."""

import hashlib
import json
from pathlib import Path

import pytest

import dev_ready.upgrade as upgrade_module
from dev_ready.cli import main
from dev_ready.errors import UpgradeError, UpgradeNotSupportedError
from dev_ready.manifest import load_default_manifest
from dev_ready.overlay import apply_overlay
from dev_ready.prompts import Answers
from dev_ready.stamp import load_stamp
from dev_ready.upgrade import upgrade_project

MANIFEST = load_default_manifest()
PIN = MANIFEST.upstream["base_template"]
CATALOG = MANIFEST.components


def _snapshot(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _make_project(tmp_path: Path, *, code_memory: bool = False) -> Path:
    project = tmp_path / "project"
    project.mkdir()
    mcp_items = frozenset({"mcp-config", "code-memory"} if code_memory else {"mcp-config"})
    answers = Answers(
        project_name="upgrade-app",
        target_dir=project,
        include_skills=True,
        include_mcp=True,
        include_docs=False,
        include_agents=False,
        skills_items=frozenset({"project-orientation"}),
        mcp_items=mcp_items,
    )
    apply_overlay(answers, project, CATALOG, PIN, MANIFEST.vendored)
    return project


def _set_inventory_hash(project: Path, path: str, content: bytes) -> None:
    stamp_path = project / ".dev-ready.json"
    data = json.loads(stamp_path.read_text(encoding="utf-8"))
    for entry in data["inventory"]:
        if entry["path"] == path:
            entry["sha256"] = hashlib.sha256(content).hexdigest()
            break
    else:
        raise AssertionError(f"inventory has no {path}")
    stamp_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def test_fresh_project_is_a_byte_identical_noop(tmp_path: Path) -> None:
    project = _make_project(tmp_path)
    before = _snapshot(project)
    report = upgrade_project(project)
    assert _snapshot(project) == before
    assert "Upgraded (0):" in report


def test_hash_matched_old_file_is_upgraded(tmp_path: Path) -> None:
    project = _make_project(tmp_path)
    old = b"OLD"
    (project / "CLAUDE.md").write_bytes(old)
    _set_inventory_hash(project, "CLAUDE.md", old)

    report = upgrade_project(project)
    assert (project / "CLAUDE.md").read_bytes() != old
    assert "  - CLAUDE.md" in report


def test_user_modified_file_is_left_unchanged(tmp_path: Path) -> None:
    project = _make_project(tmp_path)
    (project / "CLAUDE.md").write_bytes(b"USEREDIT")
    report = upgrade_project(project)
    assert (project / "CLAUDE.md").read_bytes() == b"USEREDIT"
    assert "Skipped (user-modified) (1):" in report


def test_missing_unrecorded_file_is_added(tmp_path: Path) -> None:
    project = _make_project(tmp_path)
    skill = project / ".claude" / "skills" / "project-orientation" / "SKILL.md"
    skill.unlink()
    stamp_path = project / ".dev-ready.json"
    data = json.loads(stamp_path.read_text(encoding="utf-8"))
    data["inventory"] = [entry for entry in data["inventory"] if entry["path"] != skill.relative_to(project).as_posix()]
    stamp_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    report = upgrade_project(project)
    assert skill.exists()
    assert "Added (1):" in report


def test_dry_run_never_mutates(tmp_path: Path) -> None:
    project = _make_project(tmp_path)
    old = b"OLD"
    (project / "CLAUDE.md").write_bytes(old)
    _set_inventory_hash(project, "CLAUDE.md", old)
    before = _snapshot(project)
    report = upgrade_project(project, dry_run=True)
    assert _snapshot(project) == before
    assert "would CLAUDE.md" in report


def test_mid_commit_failure_rolls_back_everything(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project = _make_project(tmp_path)
    old = b"OLD"
    (project / "CLAUDE.md").write_bytes(old)
    _set_inventory_hash(project, "CLAUDE.md", old)
    before = _snapshot(project)
    original = upgrade_module._write_target
    calls = 0

    def fail_second(path: Path, data: bytes) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("injected write failure")
        original(path, data)

    monkeypatch.setattr(upgrade_module, "_write_target", fail_second)
    with pytest.raises(UpgradeError, match="rolled back"):
        upgrade_project(project)
    assert _snapshot(project) == before


def test_symlinked_managed_path_is_conflict_and_never_followed(tmp_path: Path) -> None:
    project = _make_project(tmp_path)
    old = b"OLD"
    non_overlay = project / "application-note.txt"
    non_overlay.write_bytes(old)
    claude = project / "CLAUDE.md"
    claude.unlink()
    claude.symlink_to(non_overlay.name)
    _set_inventory_hash(project, "CLAUDE.md", old)

    report = upgrade_project(project)
    assert non_overlay.read_bytes() == old
    assert claude.is_symlink()
    assert "Conflict (1):" in report


def test_parent_mkdir_failure_removes_partial_directories(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = _make_project(tmp_path)
    skill_dir = project / ".claude" / "skills" / "project-orientation"
    for path in sorted(skill_dir.rglob("*"), reverse=True):
        if path.is_file():
            path.unlink()
    skill_dir.rmdir()
    stamp_path = project / ".dev-ready.json"
    data = json.loads(stamp_path.read_text(encoding="utf-8"))
    data["inventory"] = [
        entry
        for entry in data["inventory"]
        if entry["path"] != ".claude/skills/project-orientation/SKILL.md"
    ]
    stamp_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    before = _snapshot(project)
    original_mkdir = Path.mkdir
    calls = 0

    def mkdir_then_fail(path: Path, *args: object, **kwargs: object) -> None:
        nonlocal calls
        calls += 1
        original_mkdir(path, *args, **kwargs)
        if calls == 1:
            raise OSError("injected mkdir failure")

    monkeypatch.setattr(Path, "mkdir", mkdir_then_fail)
    with pytest.raises(UpgradeError, match="rolled back"):
        upgrade_project(project)
    assert _snapshot(project) == before


@pytest.mark.parametrize("version", [1, 2])
def test_pre_v3_stamps_are_refused(tmp_path: Path, version: int, capsys: pytest.CaptureFixture[str]) -> None:
    project = _make_project(tmp_path)
    stamp_path = project / ".dev-ready.json"
    data = json.loads(stamp_path.read_text(encoding="utf-8"))
    data["stamp_version"] = version
    data.pop("inventory")
    data.pop("project_name")
    stamp_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    with pytest.raises(UpgradeNotSupportedError):
        upgrade_project(project)
    assert main(["upgrade", str(project)]) == 8
    assert "v0.3–v0.5" in capsys.readouterr().err


def test_inject_target_is_never_auto_upgraded(tmp_path: Path) -> None:
    project = _make_project(tmp_path, code_memory=True)
    original = (project / ".mcp.json").read_bytes() + b"\nuser note"
    (project / ".mcp.json").write_bytes(original)
    report = upgrade_project(project)
    assert (project / ".mcp.json").read_bytes() == original
    assert "Skipped (shared, not auto-upgraded) (1):" in report


def test_selected_inject_target_without_overlay_file_is_reported(tmp_path: Path) -> None:
    project = _make_project(tmp_path)
    stamp_path = project / ".dev-ready.json"
    data = json.loads(stamp_path.read_text(encoding="utf-8"))
    data["components"]["skills"]["items"].append({"id": "react-doctor", "pin": "0.0.0"})
    data["components"]["skills"]["included"] = True
    stamp_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    report = upgrade_project(project)
    assert "frontend/package.json" in report


def test_upgrade_rewrites_v3_stamp_inventory(tmp_path: Path) -> None:
    project = _make_project(tmp_path)
    old = b"OLD"
    (project / "CLAUDE.md").write_bytes(old)
    _set_inventory_hash(project, "CLAUDE.md", old)
    upgrade_project(project)
    stamp = load_stamp(project)
    assert stamp.stamp_version == 3
    inventory = {entry.path: entry.sha256 for entry in stamp.inventory}
    assert inventory["CLAUDE.md"] == hashlib.sha256((project / "CLAUDE.md").read_bytes()).hexdigest()
