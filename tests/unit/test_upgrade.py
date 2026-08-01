"""Unit tests for the offline, transactional overlay upgrader."""

import hashlib
import json
import shutil
from pathlib import Path

import pytest

import dev_ready.upgrade as upgrade_module
import dev_ready.overlay.stamp_rendering as stamp_rendering_module
from dev_ready.cli import main
from dev_ready.errors import StampInvalidError, UpgradeError, UpgradeNotSupportedError
from dev_ready.inspection import REQUIRED_UPSTREAM_PATHS
from dev_ready.manifest import load_default_manifest
from dev_ready.overlay import apply_overlay
from dev_ready.prompts import Answers, ProjectSelection
from dev_ready.stamp import load_stamp
from dev_ready.upgrade import upgrade_project

MANIFEST = load_default_manifest()
PIN = MANIFEST.upstream["base_template"]
CATALOG = MANIFEST.components

_HANDOFF_PATHS = (
    "docs/handoffs/.gitignore",
    "docs/handoffs/README.md",
    "docs/handoffs/phase-N/03-review.md",
    "docs/handoffs/phase-N/04-qa-review.md",
    "docs/handoffs/phase-N/05-security-review.md",
    "docs/handoffs/phase-N/06-sre-review.md",
    "docs/handoffs/phase-N/reports/execution-report.md",
    "docs/handoffs/phase-N/tickets/README.md",
    "docs/handoffs/protocol.yaml",
)
_PROJECT_ORIENTATION_PATHS = (
    ".agents/skills/project-orientation/SKILL.md",
    ".claude/skills/project-orientation/SKILL.md",
    ".windsurf/skills/project-orientation/SKILL.md",
)
_RETIRED_PATH_CASES = (
    pytest.param("handoff", _HANDOFF_PATHS, id="handoff-protocol"),
    pytest.param(
        "project-orientation",
        _PROJECT_ORIENTATION_PATHS,
        id="project-orientation-and-stubs",
    ),
    pytest.param("mcp-config", (".mcp.json",), id="unused-base-mcp-config"),
)
_REQUIRED_LOOP_STEPS = (
    "grill-with-docs",
    "grilling",
    "domain-modeling",
    "to-spec",
    "to-tickets",
    "implement",
    "tdd",
    "diagnosing-bugs",
    "code-review",
    "improve-codebase-architecture",
    "codebase-design",
)
_LOOP_TARGET_SKILLS_DIRS = (Path(".claude/skills"), Path(".windsurf/skills"))


def _snapshot(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _make_project(tmp_path: Path, *, code_memory: bool = False) -> Path:
    project = tmp_path / "project"
    project.mkdir()
    mcp_items = frozenset({"code-memory"} if code_memory else set())
    answers = Answers(
        project_name="upgrade-app",
        target_dir=project,
        selection=ProjectSelection.from_items(
                CATALOG,
                skills=frozenset({"caveman"}),
                mcp=mcp_items,
                docs_items=frozenset(),
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


def _materialize_required_upstream_paths(project: Path) -> None:
    for relative in REQUIRED_UPSTREAM_PATHS:
        path = project / relative
        if relative in {"backend", "frontend"}:
            path.mkdir(parents=True, exist_ok=True)
        else:
            path.write_text("upstream", encoding="utf-8")


def _make_pre_agent_target_project(tmp_path: Path) -> Path:
    """Rewrite a current fixture into the v3 Claude-only layout."""
    project = _make_project(tmp_path)
    _materialize_required_upstream_paths(project)
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


def _loop_roots() -> tuple[Path, ...]:
    roots = [Path(".agents/skills") / step for step in _REQUIRED_LOOP_STEPS]
    roots.append(Path("docs/agents"))
    roots.extend(
        skills_dir / step
        for skills_dir in _LOOP_TARGET_SKILLS_DIRS
        for step in _REQUIRED_LOOP_STEPS
    )
    return tuple(roots)


def _remove_loop_from_v4_project(project: Path) -> None:
    _rewrite_stamp_as_v4(project)
    roots = _loop_roots()
    stamp_path = project / ".dev-ready.json"
    data = json.loads(stamp_path.read_text(encoding="utf-8"))
    data["components"]["skills"]["items"] = [
        item
        for item in data["components"]["skills"]["items"]
        if item["id"] != MANIFEST.default_set.development_loop
    ]
    data["inventory"] = [
        entry
        for entry in data["inventory"]
        if not any(
            Path(entry["path"]) == root or root in Path(entry["path"]).parents
            for root in roots
        )
    ]
    stamp_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    for root in roots:
        target = project / root
        if target.is_dir():
            shutil.rmtree(target)
        elif target.exists():
            target.unlink()


def _assert_complete_loop_tree(project: Path) -> None:
    for step in _REQUIRED_LOOP_STEPS:
        assert (project / ".agents" / "skills" / step / "SKILL.md").is_file()
        for skills_dir in _LOOP_TARGET_SKILLS_DIRS:
            assert (project / skills_dir / step / "SKILL.md").is_file()
    assert (project / "docs" / "agents" / "issue-tracker.md").is_file()


def test_fresh_project_is_a_byte_identical_noop(tmp_path: Path) -> None:
    project = _make_project(tmp_path)
    before = _snapshot(project)
    report = upgrade_project(project)
    assert _snapshot(project) == before
    assert "Upgraded (0):" in report


def test_malformed_v5_record_fails_before_upgrade_mutates_the_project(
    tmp_path: Path,
) -> None:
    project = _make_project(tmp_path)
    stamp_path = project / ".dev-ready.json"
    data = json.loads(stamp_path.read_text(encoding="utf-8"))
    data.pop("development_loop")
    stamp_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    before = _snapshot(project)

    with pytest.raises(StampInvalidError, match="development_loop"):
        upgrade_project(project)

    assert _snapshot(project) == before


def _rewrite_stamp_as_v4(project: Path) -> None:
    stamp_path = project / ".dev-ready.json"
    data = json.loads(stamp_path.read_text(encoding="utf-8"))
    data["stamp_version"] = 4
    data.pop("categories")
    data.pop("development_loop")
    data["components"]["docs"].pop("items", None)
    stamp_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _record_retired_selection(project: Path, retirement: str) -> None:
    stamp_path = project / ".dev-ready.json"
    data = json.loads(stamp_path.read_text(encoding="utf-8"))
    if retirement == "handoff":
        data["components"]["handoff"] = {"included": True}
    elif retirement == "project-orientation":
        data["components"]["skills"]["items"].append(
            {"id": "project-orientation", "pin": None}
        )
    elif retirement == "mcp-config":
        data["components"]["mcp"] = {
            "included": True,
            "items": [{"id": "mcp-config", "pin": None}],
        }
    else:
        raise AssertionError(f"unknown retirement fixture {retirement!r}")
    stamp_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def test_unknown_v5_development_loop_fails_before_upgrade_mutates_the_project(
    tmp_path: Path,
) -> None:
    project = _make_project(tmp_path)
    stamp_path = project / ".dev-ready.json"
    data = json.loads(stamp_path.read_text(encoding="utf-8"))
    data["development_loop"] = "unknown-loop"
    stamp_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    before = _snapshot(project)

    with pytest.raises(StampInvalidError, match="unknown development_loop"):
        upgrade_project(project)

    assert _snapshot(project) == before


def test_v5_development_loop_missing_from_items_fails_before_mutation(
    tmp_path: Path,
) -> None:
    project = _make_project(tmp_path)
    stamp_path = project / ".dev-ready.json"
    data = json.loads(stamp_path.read_text(encoding="utf-8"))
    data["components"]["skills"]["items"] = [
        item
        for item in data["components"]["skills"]["items"]
        if item["id"] != data["development_loop"]
    ]
    stamp_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    before = _snapshot(project)

    with pytest.raises(StampInvalidError, match="development_loop.*skills"):
        upgrade_project(project)

    assert _snapshot(project) == before


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


def test_symlinked_obsolete_path_is_refused_instead_of_followed(tmp_path: Path) -> None:
    project = _make_project(tmp_path)
    obsolete = _add_obsolete_managed_file(
        project,
        "docs/handoffs/protocol.yaml",
        recorded_content=b"released protocol",
    )
    non_overlay = project / "application-note.txt"
    non_overlay.write_bytes(b"user application content")
    obsolete.unlink()
    obsolete.symlink_to(Path("../..") / non_overlay.name, target_is_directory=False)

    report = upgrade_project(project)

    assert non_overlay.read_bytes() == b"user application content"
    assert obsolete.is_symlink()
    assert "Conflict (1):" in report
    assert "docs/handoffs/protocol.yaml" in report


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
    assert stamp.stamp_version == 5
    inventory = {entry.path: entry.sha256 for entry in stamp.inventory}
    assert inventory["CLAUDE.md"] == hashlib.sha256((project / "CLAUDE.md").read_bytes()).hexdigest()


def test_upgrade_migrates_a_v4_record_to_v5_with_derived_categories(
    tmp_path: Path,
) -> None:
    project = _make_project(tmp_path)
    stamp_path = project / ".dev-ready.json"
    data = json.loads(stamp_path.read_text(encoding="utf-8"))
    data["stamp_version"] = 4
    data.pop("categories")
    data["components"]["docs"].pop("items", None)
    stamp_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    upgrade_project(project)

    migrated = load_stamp(project)
    assert migrated.stamp_version == 5
    assert migrated.categories == ("dev", "token-optimize")


@pytest.mark.parametrize(
    "retired_id",
    ["spec-loop", "tdd", "diagnosing-bugs", "code-review"],
)
def test_upgrade_maps_each_retired_loop_item_to_the_development_loop(
    tmp_path: Path,
    retired_id: str,
) -> None:
    project = _make_project(tmp_path)
    stamp_path = project / ".dev-ready.json"
    data = json.loads(stamp_path.read_text(encoding="utf-8"))
    data["stamp_version"] = 4
    data.pop("categories")
    data.pop("development_loop")
    data["components"]["skills"]["items"] = [{"id": retired_id, "pin": None}]
    data["components"]["docs"].pop("items", None)
    stamp_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    upgrade_project(project)

    migrated = json.loads(stamp_path.read_text(encoding="utf-8"))
    assert migrated["development_loop"] == "spec-loop"
    assert [item["id"] for item in migrated["components"]["skills"]["items"]] == [
        "spec-loop"
    ]
    assert migrated["categories"] == ["dev"]


def test_v4_project_that_declined_the_loop_gains_the_complete_loop_tree(
    tmp_path: Path,
) -> None:
    project = _make_project(tmp_path)
    _remove_loop_from_v4_project(project)
    assert not (project / ".agents/skills/implement/SKILL.md").exists()

    upgrade_project(project)

    _assert_complete_loop_tree(project)
    migrated = load_stamp(project)
    assert migrated.development_loop == "spec-loop"
    assert "spec-loop" in {item.id for item in migrated.skills_items}


def test_v4_project_that_selected_the_loop_keeps_the_complete_loop_tree(
    tmp_path: Path,
) -> None:
    project = _make_project(tmp_path)
    _rewrite_stamp_as_v4(project)
    implement = project / ".agents/skills/implement/SKILL.md"
    before_implement = implement.read_bytes()

    upgrade_project(project)

    _assert_complete_loop_tree(project)
    assert implement.read_bytes() == before_implement
    migrated = load_stamp(project)
    assert migrated.development_loop == "spec-loop"
    assert "spec-loop" in {item.id for item in migrated.skills_items}


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


def test_upgrade_advances_overlay_currency_without_adding_new_enhancements(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = _make_project(tmp_path)
    monkeypatch.setattr(stamp_rendering_module, "__version__", "0.7.0")

    upgrade_project(project)

    upgraded = load_stamp(project)
    assert upgraded.dev_ready_version == "0.7.0"
    assert {item.id for item in upgraded.skills_items} == {"caveman", "spec-loop"}


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
    assert (
        "  - docs/handoffs/phase-N/02-implementation.md: preserved; "
        "review it and remove it manually if it is no longer needed"
    ) in report
    assert "Divergence (1):" in report
    assert "remove it manually" in report


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


@pytest.mark.parametrize(("retirement", "paths"), _RETIRED_PATH_CASES)
def test_each_selected_untouched_retirement_is_deleted_from_recorded_inventory(
    tmp_path: Path,
    retirement: str,
    paths: tuple[str, ...],
) -> None:
    project = _make_project(tmp_path)
    _rewrite_stamp_as_v4(project)
    _record_retired_selection(project, retirement)
    for path in paths:
        _add_obsolete_managed_file(project, path, recorded_content=b"released bytes")

    report = upgrade_project(project)

    for path in paths:
        assert not (project / path).exists()
        assert path in report


@pytest.mark.parametrize(("retirement", "paths"), _RETIRED_PATH_CASES)
def test_each_selected_edited_retirement_is_preserved_with_divergence(
    tmp_path: Path,
    retirement: str,
    paths: tuple[str, ...],
) -> None:
    project = _make_project(tmp_path)
    _rewrite_stamp_as_v4(project)
    _record_retired_selection(project, retirement)
    edited_path = paths[0]
    for path in paths:
        _add_obsolete_managed_file(
            project,
            path,
            recorded_content=b"released bytes",
            current_content=b"user edit" if path == edited_path else None,
        )

    report = upgrade_project(project)

    assert (project / edited_path).read_bytes() == b"user edit"
    assert f"{edited_path}: retained outside the current managed inventory" in report
    for path in paths[1:]:
        assert not (project / path).exists()


@pytest.mark.parametrize(("retirement", "paths"), _RETIRED_PATH_CASES)
def test_each_never_selected_retirement_is_not_reported(
    tmp_path: Path,
    retirement: str,
    paths: tuple[str, ...],
) -> None:
    _ = retirement
    project = _make_project(tmp_path)
    _rewrite_stamp_as_v4(project)

    report = upgrade_project(project)

    for path in paths:
        assert path not in report


def test_dry_run_reports_obsolete_deletion_without_mutating(tmp_path: Path) -> None:
    project = _make_project(tmp_path)
    _add_obsolete_managed_file(project, "obsolete.md", recorded_content=b"old")
    before = _snapshot(project)

    report = upgrade_project(project, dry_run=True)

    assert _snapshot(project) == before
    assert "would delete obsolete.md" in report


def test_v4_dry_run_reports_replacement_addition_and_deletion_without_mutation(
    tmp_path: Path,
) -> None:
    project = _make_project(tmp_path)
    _remove_loop_from_v4_project(project)
    old_rules = b"released v0.8 rules"
    (project / "CLAUDE.md").write_bytes(old_rules)
    _set_inventory_hash(project, "CLAUDE.md", old_rules)
    _add_obsolete_managed_file(
        project,
        "docs/handoffs/protocol.yaml",
        recorded_content=b"released protocol",
    )
    before = _snapshot(project)

    report = upgrade_project(project, dry_run=True)

    assert _snapshot(project) == before
    assert "would CLAUDE.md" in report
    assert "would .agents/skills/implement/SKILL.md" in report
    assert "would delete docs/handoffs/protocol.yaml" in report


def test_v4_stamp_only_dry_run_reports_the_record_replacement(
    tmp_path: Path,
) -> None:
    project = _make_project(tmp_path)
    _rewrite_stamp_as_v4(project)
    before = _snapshot(project)

    report = upgrade_project(project, dry_run=True)

    assert _snapshot(project) == before
    assert "would .dev-ready.json" in report
    assert "No changes were needed." not in report


def test_migrated_v4_project_passes_check_cleanly(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    project = _make_project(tmp_path)
    _materialize_required_upstream_paths(project)
    _remove_loop_from_v4_project(project)
    _add_obsolete_managed_file(
        project,
        "docs/handoffs/protocol.yaml",
        recorded_content=b"released protocol",
    )

    upgrade_project(project)

    assert main(["check", str(project)]) == 0
    assert "clean" in capsys.readouterr().out.lower()


def test_failure_after_obsolete_deletion_rolls_it_back(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    project = _make_project(tmp_path)
    obsolete = _add_obsolete_managed_file(
        project, "docs/handoffs/phase-N/01-plan.md", recorded_content=b"legacy"
    )
    old_rules = b"old rules"
    (project / "CLAUDE.md").write_bytes(old_rules)
    _set_inventory_hash(project, "CLAUDE.md", old_rules)
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
    exit_code = main(["upgrade", str(project)])

    captured = capsys.readouterr()
    assert exit_code == 9
    assert "injected failure after deletion" in captured.err
    assert "rolled back" in captured.err
    assert "original project was restored" in captured.err
    assert "retry the upgrade" in captured.err.lower()
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
    assert "No changes were needed." in report


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
    assert migrated.stamp_version == 5
    assert migrated.categories == ("dev", "token-optimize")
    assert migrated.development_loop == "spec-loop"
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
