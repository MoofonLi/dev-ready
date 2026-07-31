"""Unit tests for the offline, transactional overlay upgrader."""

import hashlib
import json
import shutil
from pathlib import Path

import pytest

import dev_ready.upgrade as upgrade_module
import dev_ready.overlay as overlay_module
from dev_ready.cli import main
from dev_ready.errors import UpgradeError, UpgradeNotSupportedError
from dev_ready.inspection import REQUIRED_UPSTREAM_PATHS
from dev_ready.manifest import load_default_manifest
from dev_ready.overlay import apply_overlay
from dev_ready.prompts import Answers, ProjectSelection
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
        selection=ProjectSelection.from_items(
            CATALOG,
            skills=frozenset({"caveman"}),
            mcp=mcp_items,
            docs=False,
        ),
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


def _add_obsolete_managed_file(
    project: Path,
    path: str,
    *,
    recorded_content: bytes,
    current_content: bytes | None = None,
) -> Path:
    target = project / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(current_content if current_content is not None else recorded_content)
    stamp_path = project / ".dev-ready.json"
    data = json.loads(stamp_path.read_text(encoding="utf-8"))
    data["inventory"].append(
        {"path": path, "sha256": hashlib.sha256(recorded_content).hexdigest()}
    )
    stamp_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return target


def _make_pre_agent_target_project(tmp_path: Path) -> Path:
    """Rewrite a current fixture into the v3 Claude-only layout."""
    project = _make_project(tmp_path)
    for relative in REQUIRED_UPSTREAM_PATHS:
        path = project / relative
        if relative in {"backend", "frontend"}:
            path.mkdir(parents=True, exist_ok=True)
        else:
            path.write_text("upstream", encoding="utf-8")
    canonical_skill = project / ".agents/skills/caveman/SKILL.md"
    legacy_skill = project / ".claude/skills/caveman/SKILL.md"
    legacy_skill.write_bytes(canonical_skill.read_bytes())
    legacy_rules = (project / "AGENTS.md").read_bytes()
    (project / "CLAUDE.md").write_bytes(legacy_rules)
    shutil.rmtree(project / ".agents")
    shutil.rmtree(project / ".windsurf")
    (project / "AGENTS.md").unlink()

    stamp_path = project / ".dev-ready.json"
    data = json.loads(stamp_path.read_text(encoding="utf-8"))
    data["stamp_version"] = 3
    data.pop("agent_targets")
    data["components"]["agents"] = {"included": False}
    retired_prefixes = (".agents/", ".windsurf/")
    data["inventory"] = [
        entry
        for entry in data["inventory"]
        if entry["path"] not in {"AGENTS.md", "CLAUDE.md"}
        and not entry["path"].startswith(retired_prefixes)
    ]
    for path in ("CLAUDE.md", ".claude/skills/caveman/SKILL.md"):
        data["inventory"].append(
            {"path": path, "sha256": hashlib.sha256((project / path).read_bytes()).hexdigest()}
        )
    stamp_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return project


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
    skill = project / ".claude" / "skills" / "caveman" / "SKILL.md"
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
    skill_dir = project / ".claude" / "skills" / "caveman"
    for path in sorted(skill_dir.rglob("*"), reverse=True):
        if path.is_file():
            path.unlink()
    skill_dir.rmdir()
    stamp_path = project / ".dev-ready.json"
    data = json.loads(stamp_path.read_text(encoding="utf-8"))
    data["inventory"] = [
        entry
        for entry in data["inventory"]
        if entry["path"] != ".claude/skills/caveman/SKILL.md"
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


def test_removed_catalog_item_in_stamp_does_not_block_upgrade(tmp_path: Path) -> None:
    project = _make_project(tmp_path)
    stamp_path = project / ".dev-ready.json"
    data = json.loads(stamp_path.read_text(encoding="utf-8"))
    data["components"]["skills"]["items"].append(
        {"id": "removed-skill", "pin": "1.0.0"}
    )
    stamp_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    upgrade_project(project)

    rewritten = json.loads(stamp_path.read_text(encoding="utf-8"))
    rewritten_ids = {
        item["id"] for item in rewritten["components"]["skills"]["items"]
    }
    assert "removed-skill" not in rewritten_ids


def test_upgrade_refuses_to_discard_removed_agent_target(tmp_path: Path) -> None:
    project = _make_project(tmp_path)
    stamp_path = project / ".dev-ready.json"
    data = json.loads(stamp_path.read_text(encoding="utf-8"))
    data["agent_targets"] = ["retired-agent"]
    stamp_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    before = _snapshot(project)

    with pytest.raises(UpgradeError, match="removed Agent Target.*retired-agent"):
        upgrade_project(project)

    assert _snapshot(project) == before


def test_upgrade_rewrites_v3_stamp_inventory(tmp_path: Path) -> None:
    project = _make_project(tmp_path)
    old = b"OLD"
    (project / "CLAUDE.md").write_bytes(old)
    _set_inventory_hash(project, "CLAUDE.md", old)
    upgrade_project(project)
    stamp = load_stamp(project)
    assert stamp.stamp_version == 4
    inventory = {entry.path: entry.sha256 for entry in stamp.inventory}
    assert inventory["CLAUDE.md"] == hashlib.sha256((project / "CLAUDE.md").read_bytes()).hexdigest()


def test_upgrade_preserves_recorded_base_provenance(tmp_path: Path) -> None:
    project = _make_project(tmp_path)
    stamp_path = project / ".dev-ready.json"
    data = json.loads(stamp_path.read_text(encoding="utf-8"))
    data["upstream"] = {"repo": "original/base-template", "commit": "0" * 40}
    stamp_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    upgrade_project(project)

    upgraded = load_stamp(project)
    assert upgraded.upstream.repo == "original/base-template"
    assert upgraded.upstream.commit == "0" * 40


def test_upgrade_advances_overlay_currency_without_adding_new_defaults(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = _make_project(tmp_path)
    monkeypatch.setattr(overlay_module, "__version__", "0.7.0")

    upgrade_project(project)

    upgraded = load_stamp(project)
    assert upgraded.dev_ready_version == "0.7.0"
    assert {item.id for item in upgraded.skills_items} == {"caveman"}
    assert not (project / ".claude" / "skills" / "spec-loop").exists()


def test_untouched_obsolete_managed_file_is_deleted(tmp_path: Path) -> None:
    project = _make_project(tmp_path)
    obsolete = _add_obsolete_managed_file(
        project,
        "docs/handoffs/phase-N/01-plan.md",
        recorded_content=b"legacy plan",
    )

    report = upgrade_project(project)

    assert not obsolete.exists()
    assert "Deleted (obsolete) (1):" in report
    assert "docs/handoffs/phase-N/01-plan.md" in report
    assert "docs/handoffs/phase-N/01-plan.md" not in {
        entry.path for entry in load_stamp(project).inventory
    }


def test_modified_obsolete_managed_file_is_preserved_and_reported(tmp_path: Path) -> None:
    project = _make_project(tmp_path)
    obsolete = _add_obsolete_managed_file(
        project,
        "docs/handoffs/phase-N/02-implementation.md",
        recorded_content=b"legacy brief",
        current_content=b"user notes",
    )

    report = upgrade_project(project)

    assert obsolete.read_bytes() == b"user notes"
    assert "Preserved (obsolete, user-modified) (1):" in report
    assert "docs/handoffs/phase-N/02-implementation.md" in report


def test_modified_retired_project_orientation_skill_is_preserved_and_reported(
    tmp_path: Path,
) -> None:
    project = _make_project(tmp_path)
    retired_path = ".agents/skills/project-orientation/SKILL.md"
    retired = _add_obsolete_managed_file(
        project,
        retired_path,
        recorded_content=b"generated project orientation",
        current_content=b"user-edited project orientation",
    )

    report = upgrade_project(project)

    assert retired.read_bytes() == b"user-edited project orientation"
    assert "Preserved (obsolete, user-modified) (1):" in report
    assert retired_path in report


def test_dry_run_reports_obsolete_deletion_without_mutating(tmp_path: Path) -> None:
    project = _make_project(tmp_path)
    _add_obsolete_managed_file(project, "obsolete.md", recorded_content=b"old")
    before = _snapshot(project)

    report = upgrade_project(project, dry_run=True)

    assert _snapshot(project) == before
    assert "would delete obsolete.md" in report


def test_failure_after_obsolete_deletion_rolls_it_back(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = _make_project(tmp_path)
    obsolete = _add_obsolete_managed_file(
        project, "docs/handoffs/phase-N/01-plan.md", recorded_content=b"legacy"
    )
    before = _snapshot(project)
    original = upgrade_module._write_target
    failed = False

    def fail_write(path: Path, data: bytes) -> None:
        nonlocal failed
        if not failed:
            failed = True
            raise OSError("injected failure after deletion")
        original(path, data)

    monkeypatch.setattr(upgrade_module, "_write_target", fail_write)
    with pytest.raises(UpgradeError, match="rolled back"):
        upgrade_project(project)

    assert obsolete.read_bytes() == b"legacy"
    assert _snapshot(project) == before


def test_obsolete_deletion_is_idempotent(tmp_path: Path) -> None:
    project = _make_project(tmp_path)
    _add_obsolete_managed_file(project, "obsolete.md", recorded_content=b"old")
    upgrade_project(project)
    before = _snapshot(project)

    report = upgrade_project(project, dry_run=True)

    assert _snapshot(project) == before
    assert "Deleted (obsolete) (0):" in report
    assert "would delete" not in report


def test_pre_target_stamp_migrates_to_canonical_claude_layout(tmp_path: Path) -> None:
    project = _make_pre_agent_target_project(tmp_path)
    old_stamp = load_stamp(project)
    old_provenance = old_stamp.upstream

    report = upgrade_project(project)

    canonical = project / ".agents/skills/caveman/SKILL.md"
    stub = project / ".claude/skills/caveman/SKILL.md"
    assert (project / "AGENTS.md").is_file()
    assert (project / "CLAUDE.md").read_text(encoding="utf-8") == "@AGENTS.md\n"
    assert canonical.is_file()
    assert stub.is_file()
    assert canonical.read_bytes() != stub.read_bytes()
    assert not canonical.is_symlink()
    assert not stub.is_symlink()
    assert not (project / ".windsurf").exists()
    migrated = load_stamp(project)
    assert migrated.agent_targets == ("claude",)
    assert migrated.upstream == old_provenance
    assert main(["check", str(project)]) == 0
    assert "AGENTS.md" in report

    before_repeat = _snapshot(project)
    repeat = upgrade_project(project)
    assert _snapshot(project) == before_repeat
    assert "Summary: 0 upgraded, 0 added, 0 deleted" in repeat


def test_migration_preserves_edited_skill_and_reports_divergence(tmp_path: Path) -> None:
    project = _make_pre_agent_target_project(tmp_path)
    legacy_skill = project / ".claude/skills/caveman/SKILL.md"
    legacy_skill.write_bytes(b"user-edited skill")

    report = upgrade_project(project)

    assert legacy_skill.read_bytes() == b"user-edited skill"
    assert (project / ".agents/skills/caveman/SKILL.md").is_file()
    assert "Skipped (user-modified)" in report
    assert "Divergence" in report
    assert ".claude/skills/caveman/SKILL.md" in report


def test_migration_preserves_edited_rules_and_reports_reconciliation(tmp_path: Path) -> None:
    project = _make_pre_agent_target_project(tmp_path)
    (project / "CLAUDE.md").write_bytes(b"user-edited rules")

    report = upgrade_project(project)

    assert (project / "CLAUDE.md").read_bytes() == b"user-edited rules"
    assert (project / "AGENTS.md").is_file()
    assert "CLAUDE.md" in report
    assert "reference AGENTS.md manually" in report


def test_migration_dry_run_reports_full_plan_without_mutation(tmp_path: Path) -> None:
    project = _make_pre_agent_target_project(tmp_path)
    before = _snapshot(project)

    report = upgrade_project(project, dry_run=True)

    assert _snapshot(project) == before
    assert "would AGENTS.md" in report
    assert "would .agents/skills/caveman/SKILL.md" in report
    assert "would CLAUDE.md" in report


def test_migration_failure_rolls_back_added_and_replaced_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = _make_pre_agent_target_project(tmp_path)
    before = _snapshot(project)
    original = upgrade_module._write_target
    calls = 0

    def fail_third(path: Path, data: bytes) -> None:
        nonlocal calls
        calls += 1
        if calls == 3:
            raise OSError("injected migration failure")
        original(path, data)

    monkeypatch.setattr(upgrade_module, "_write_target", fail_third)
    with pytest.raises(UpgradeError, match="rolled back"):
        upgrade_project(project)

    assert _snapshot(project) == before
