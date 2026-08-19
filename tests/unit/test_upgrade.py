"""Unit tests for the offline, transactional overlay upgrader."""

import hashlib
import json
import os
import shutil
import sys
from dataclasses import replace
from pathlib import Path

import pytest

import dev_ready.upgrade as upgrade_module
import dev_ready.overlay.stamp_rendering as stamp_rendering_module
from dev_ready.cli import main
from dev_ready.errors import StampInvalidError, UpgradeError, UpgradeNotSupportedError
from dev_ready.inspection import REQUIRED_UPSTREAM_PATHS
from dev_ready.manifest import ComponentCatalog, load_default_manifest
from dev_ready.overlay import (
    apply_overlay,
    build_overlay_content,
    projected_skill_link_pairs,
    render_ignore_anchor,
)
from dev_ready.prompts import Answers, ProjectSelection
from dev_ready.stamp import load_stamp
from dev_ready.skill_links import PathKind, classify_path, create_skill_link
from dev_ready.upgrade import upgrade_project

_WINDOWS = sys.platform == "win32"

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
    "setup-matt-pocock-skills",
)
_LOOP_TARGET_SKILLS_DIRS = (Path(".claude/skills"), Path(".windsurf/skills"))


def _snapshot(root: Path) -> dict[str, str]:
    snapshot: dict[str, str] = {}
    stack = [root]
    while stack:
        current = stack.pop()
        for path in current.iterdir():
            relative = path.relative_to(root).as_posix()
            if path.is_symlink() or path.is_junction():
                snapshot[relative] = f"link:{os.readlink(path)}"
                continue
            if path.is_dir():
                stack.append(path)
                continue
            if path.is_file():
                snapshot[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return snapshot


def _remove_windsurf_tree(project: Path) -> None:
    skills = project / ".windsurf" / "skills"
    if skills.is_dir() and not skills.is_symlink() and not skills.is_junction():
        for child in list(skills.iterdir()):
            if child.is_symlink() or child.is_junction():
                child.unlink()
    windsurf = project / ".windsurf"
    if windsurf.exists():
        shutil.rmtree(windsurf)
    stamp_path = project / ".dev-ready.json"
    data = json.loads(stamp_path.read_text(encoding="utf-8"))
    data["inventory"] = [
        entry
        for entry in data["inventory"]
        if not str(entry["path"]).startswith(".windsurf/")
    ]
    stamp_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _apply_current_project(answers: Answers, project: Path) -> Path:
    apply_overlay(answers, project, CATALOG, PIN, MANIFEST.vendored)
    for link_rel, canonical_rel in projected_skill_link_pairs(answers, CATALOG):
        create_skill_link(project / link_rel, project / canonical_rel)
    return project


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
                agent_targets=frozenset({"claude", "windsurf"}),
        ),
    )
    return _apply_current_project(answers, project)


def _make_mounted_project(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    (project / "frontend").mkdir(parents=True)
    (project / "frontend" / "package.json").write_text(
        json.dumps({"scripts": {}, "devDependencies": {}}),
        encoding="utf-8",
    )
    answers = Answers(
        project_name="upgrade-app",
        target_dir=project,
        selection=ProjectSelection.from_items(
            CATALOG,
            skills=frozenset({"react-doctor"}),
            mcp=frozenset(),
            docs_items=frozenset(),
            agent_targets=frozenset({"claude", "windsurf"}),
        ),
    )
    return _apply_current_project(answers, project)


def _make_design_reference_project(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    project.mkdir()
    answers = Answers(
        project_name="upgrade-app",
        target_dir=project,
        selection=ProjectSelection.from_items(
            CATALOG,
            skills=frozenset(),
            mcp=frozenset(),
            docs_items=frozenset({"design-vercel"}),
            agent_targets=frozenset(),
        ),
    )
    return _apply_current_project(answers, project)


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
    for skills_dir in (project / ".claude" / "skills", project / ".windsurf" / "skills"):
        if skills_dir.is_dir() and not skills_dir.is_symlink() and not skills_dir.is_junction():
            for child in list(skills_dir.iterdir()):
                if child.is_symlink() or child.is_junction():
                    child.unlink()
    canonical_skill = project / ".agents/skills/caveman/SKILL.md"
    legacy_skill = project / ".claude/skills/caveman/SKILL.md"
    legacy_skill.parent.mkdir(parents=True, exist_ok=True)
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


def test_derived_design_reference_stays_managed_and_preserves_user_edits(
    tmp_path: Path,
) -> None:
    project = _make_design_reference_project(tmp_path)
    design_reference = project / "docs" / "design-vercel.md"
    original = design_reference.read_bytes()

    clean_report = upgrade_project(project)
    assert design_reference.read_bytes() == original
    assert "docs/design-vercel.md" not in clean_report

    design_reference.write_bytes(b"user-edited design reference")
    modified_report = upgrade_project(project)
    assert design_reference.read_bytes() == b"user-edited design reference"
    assert "Skipped (user-modified) (1):" in modified_report
    assert "docs/design-vercel.md" in modified_report


def test_shipped_design_reference_pair_upgrades_to_collapsed_mount_without_conflict(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    answers = Answers(
        project_name="upgrade-app",
        target_dir=project,
        selection=ProjectSelection.from_items(
            CATALOG,
            skills=frozenset(),
            mcp=frozenset(),
            docs_items=frozenset({"design-stripe", "design-linear"}),
            agent_targets=frozenset(),
        ),
    )
    apply_overlay(answers, project, CATALOG, PIN, MANIFEST.vendored)
    mounted_path = ".agents/skills/implement/SKILL.md"
    implement_path = project / mounted_path
    old_mount = (
        implement_path.read_text(encoding="utf-8").replace(
            "- **Documentation references** — `design-linear`, `design-stripe`. "
            "See `docs/`.",
            "- **design-linear** — Linear-inspired DESIGN.md reference for a "
            "polished dark product interface system; omit it if that visual "
            "direction is not useful. See `docs/design-linear.md`.\n"
            "- **design-stripe** — Stripe-inspired DESIGN.md reference for a "
            "polished light interface system; omit it if that visual direction "
            "is not useful. See `docs/design-stripe.md`.",
        )
    ).encode("utf-8")
    implement_path.write_bytes(old_mount)
    _set_inventory_hash(project, mounted_path, old_mount)

    report = upgrade_project(project)

    upgraded = implement_path.read_text(encoding="utf-8")
    assert "- **Documentation references** — `design-linear`, `design-stripe`." in upgraded
    assert "Skipped (user-modified) (0):" in report
    assert (project / "docs/design-stripe.md").is_file()
    assert (project / "docs/design-linear.md").is_file()


def test_missing_unrecorded_file_is_added(tmp_path: Path) -> None:
    project = _make_project(tmp_path)
    anchor = project / ".claude" / "skills" / ".gitignore"
    anchor.unlink()
    stamp_path = project / ".dev-ready.json"
    data = json.loads(stamp_path.read_text(encoding="utf-8"))
    data["inventory"] = [
        entry
        for entry in data["inventory"]
        if entry["path"] != ".claude/skills/.gitignore"
    ]
    stamp_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    report = upgrade_project(project)
    assert anchor.exists()
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
    _remove_windsurf_tree(project)
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
    assert migrated["development_loop"] == "mattpocock"
    assert [item["id"] for item in migrated["components"]["skills"]["items"]] == [
        "mattpocock"
    ]
    assert migrated["categories"] == ["dev"]


def test_upgrade_migrates_a_v5_record_naming_retired_setup_all(
    tmp_path: Path,
) -> None:
    project = _make_project(tmp_path)
    stamp_path = project / ".dev-ready.json"
    data = json.loads(stamp_path.read_text(encoding="utf-8"))
    data["components"]["skills"]["items"].append(
        {"id": "setup-all", "pin": None}
    )
    stamp_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    upgrade_project(project)

    migrated = load_stamp(project)
    assert {item.id for item in migrated.skills_items} == {"caveman", "mattpocock"}
    assert (
        project
        / ".agents"
        / "skills"
        / "setup-matt-pocock-skills"
        / "SKILL.md"
    ).is_file()


def test_v4_project_that_declined_the_loop_gains_the_complete_loop_tree(
    tmp_path: Path,
) -> None:
    project = _make_project(tmp_path)
    _remove_loop_from_v4_project(project)
    assert not (project / ".agents/skills/implement/SKILL.md").exists()

    upgrade_project(project)

    _assert_complete_loop_tree(project)
    migrated = load_stamp(project)
    assert migrated.development_loop == "mattpocock"
    assert "mattpocock" in {item.id for item in migrated.skills_items}


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
    assert migrated.development_loop == "mattpocock"
    assert "mattpocock" in {item.id for item in migrated.skills_items}


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
    assert {item.id for item in upgraded.skills_items} == {"caveman", "mattpocock"}


def _drop_from_inventory(project: Path, path: str) -> None:
    stamp_path = project / ".dev-ready.json"
    data = json.loads(stamp_path.read_text(encoding="utf-8"))
    data["inventory"] = [entry for entry in data["inventory"] if entry["path"] != path]
    stamp_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def test_project_without_any_root_ignore_file_receives_it_on_upgrade(tmp_path: Path) -> None:
    """FR-38: nothing at the managed path means the ordinary add rule applies."""
    project = _make_project(tmp_path)
    (project / ".gitignore").unlink()
    _drop_from_inventory(project, ".gitignore")

    report = upgrade_project(project)

    assert ".env" in (project / ".gitignore").read_text(encoding="utf-8")
    assert "Added (1):" in report
    assert "  - .gitignore" in report


def test_v09_projects_unmanaged_ignore_file_is_reported_as_a_conflict(tmp_path: Path) -> None:
    """A v0.9 project carries upstream's own root ignore file, unmanaged and unrecorded.

    ADR-014 forbids `upgrade` from overwriting a file dev-ready never wrote, and
    FR-38 puts this path under the ordinary rules with no special case — so the
    honest outcome is a reported conflict the user resolves, not a silent
    replacement of a file that may hold their own rules.
    """
    project = _make_project(tmp_path)
    upstream_ignore = b"node_modules/\n/test-results/\n"
    (project / ".gitignore").write_bytes(upstream_ignore)
    _drop_from_inventory(project, ".gitignore")

    report = upgrade_project(project)

    assert (project / ".gitignore").read_bytes() == upstream_ignore
    assert "Conflict (1):" in report
    assert "  - .gitignore" in report


def test_untouched_ignore_file_is_replaced_on_upgrade(tmp_path: Path) -> None:
    project = _make_project(tmp_path)
    stale = b"node_modules/\n"
    (project / ".gitignore").write_bytes(stale)
    _set_inventory_hash(project, ".gitignore", stale)

    report = upgrade_project(project)

    assert (project / ".gitignore").read_bytes() != stale
    assert ".env*" in (project / ".gitignore").read_text(encoding="utf-8")
    assert "  - .gitignore" in report


def test_edited_ignore_file_is_preserved_and_reported(tmp_path: Path) -> None:
    project = _make_project(tmp_path)
    edited = b"node_modules/\n.env\nmy-own-rule/\n"
    (project / ".gitignore").write_bytes(edited)

    report = upgrade_project(project)

    assert (project / ".gitignore").read_bytes() == edited
    assert "Skipped (user-modified) (1):" in report
    assert "  - .gitignore" in report


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


def test_upgrade_reports_no_change_for_an_untouched_mounted_skill(
    tmp_path: Path,
) -> None:
    project = _make_mounted_project(tmp_path)
    mounted_path = ".agents/skills/code-review/SKILL.md"

    report = upgrade_project(project)

    assert mounted_path not in report
    assert "No changes were needed." in report


def test_upgrade_preserves_an_edited_mounted_skill_and_reports_divergence(
    tmp_path: Path,
) -> None:
    project = _make_mounted_project(tmp_path)
    mounted_path = ".agents/skills/code-review/SKILL.md"
    mounted_skill = project / mounted_path
    edited = mounted_skill.read_bytes() + b"\nUser edit.\n"
    mounted_skill.write_bytes(edited)

    report = upgrade_project(project)

    assert mounted_skill.read_bytes() == edited
    assert "Skipped (user-modified) (1):" in report
    assert mounted_path in report
    assert "Divergence (1):" in report
    assert (
        f"{mounted_path}: preserved; mounted guidance was not updated because "
        "the file is user-modified"
    ) in report


def test_upgrade_adds_mount_block_to_an_untouched_pre_mount_skill(
    tmp_path: Path,
) -> None:
    project = _make_mounted_project(tmp_path)
    mounted_path = ".agents/skills/code-review/SKILL.md"
    mounted_skill = project / mounted_path
    pre_mount_catalog = ComponentCatalog(
        {
            component: tuple(
                replace(item, mount=None) if item.id == "react-doctor" else item
                for item in items
            )
            for component, items in CATALOG.items()
        },
        CATALOG.agent_targets,
        CATALOG.categories,
        CATALOG.default_set,
    )
    previous_answers = Answers(
        project_name="upgrade-app",
        target_dir=project,
        selection=ProjectSelection.from_items(
            pre_mount_catalog,
            skills=frozenset({"react-doctor"}),
            agent_targets=frozenset(),
        ),
    )
    previous_bytes = build_overlay_content(
        previous_answers, pre_mount_catalog
    )[mounted_path]
    mounted_skill.write_bytes(previous_bytes)
    _set_inventory_hash(project, mounted_path, previous_bytes)

    report = upgrade_project(project)

    assert mounted_path in report
    assert "<!-- dev-ready:mounted-enhancements:start -->" in mounted_skill.read_text(
        encoding="utf-8"
    )


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
    link = project / ".claude/skills/caveman"
    assert (project / "AGENTS.md").is_file()
    assert (project / "CLAUDE.md").read_text(encoding="utf-8") == "@AGENTS.md\n"
    assert canonical.is_file()
    assert link.is_symlink() or link.is_junction()
    assert link.resolve() == canonical.parent.resolve()
    assert not canonical.is_symlink()
    assert not (project / ".windsurf").exists()
    migrated = load_stamp(project)
    assert migrated.stamp_version == 5
    assert migrated.categories == ("dev", "token-optimize")
    assert migrated.development_loop == "mattpocock"
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


def _tree_snapshot(root: Path) -> dict[str, tuple[str, bytes]]:
    snapshot: dict[str, tuple[str, bytes]] = {}
    stack = [root]
    while stack:
        current = stack.pop()
        for child in current.iterdir():
            relative = child.relative_to(root).as_posix()
            if child.is_symlink() or child.is_junction():
                snapshot[relative] = ("link", os.readlink(child).encode("utf-8"))
                continue
            if child.is_dir():
                snapshot[relative] = ("directory", b"")
                stack.append(child)
                continue
            snapshot[relative] = ("file", child.read_bytes())
    return snapshot


def test_wrong_skill_link_is_repaired_without_following_its_target(
    tmp_path: Path,
) -> None:
    project = _make_project(tmp_path)
    decoy = project / "decoy"
    decoy.mkdir()
    (decoy / "SKILL.md").write_text("other\n", encoding="utf-8")
    link = project / ".claude" / "skills" / "caveman"
    if link.is_symlink() or link.is_junction():
        link.unlink()
    create_skill_link(link, decoy)

    report = upgrade_project(project)

    assert "Skill Links repaired" in report
    assert (decoy / "SKILL.md").read_text(encoding="utf-8") == "other\n"
    assert (link / "SKILL.md").read_text(encoding="utf-8") != "other\n"
    assert link.resolve() == (project / ".agents" / "skills" / "caveman").resolve()


def test_clone_without_links_is_bootstrapped_by_upgrade(tmp_path: Path) -> None:
    project = _make_project(tmp_path)
    for skills_dir in (project / ".claude" / "skills", project / ".windsurf" / "skills"):
        if not skills_dir.is_dir():
            continue
        for child in list(skills_dir.iterdir()):
            if child.is_symlink() or child.is_junction():
                child.unlink()

    report = upgrade_project(project)

    assert "Skill Links created" in report
    assert "No changes were needed." not in report
    caveman = project / ".claude" / "skills" / "caveman"
    assert caveman.is_symlink() or caveman.is_junction()
    repeat = upgrade_project(project, dry_run=True)
    assert "would create" not in repeat
    assert "would repair" not in repeat


def test_relocate_moves_a_native_link_without_touching_its_target(tmp_path: Path) -> None:
    canonical = tmp_path / "canon"
    canonical.mkdir()
    marker = canonical / "SKILL.md"
    marker.write_text("keep\n", encoding="utf-8")
    link = tmp_path / "link"
    parked = tmp_path / "parked"
    create_skill_link(link, canonical)

    upgrade_module._relocate_path(link, parked)

    assert classify_path(link) == PathKind.ABSENT
    assert classify_path(parked) in {PathKind.JUNCTION, PathKind.SYMBOLIC_LINK}
    assert marker.read_text(encoding="utf-8") == "keep\n"

    upgrade_module._relocate_path(parked, link)

    assert classify_path(link) in {PathKind.JUNCTION, PathKind.SYMBOLIC_LINK}
    assert classify_path(parked) == PathKind.ABSENT
    assert marker.read_text(encoding="utf-8") == "keep\n"
    assert (link / "SKILL.md").read_text(encoding="utf-8") == "keep\n"


@pytest.mark.skipif(not _WINDOWS, reason="junction detection is the Windows hole")
def test_has_symlink_component_sees_a_junction(tmp_path: Path) -> None:
    real = tmp_path / "real"
    real.mkdir()
    junction = tmp_path / "skills"
    create_skill_link(junction, real)

    assert upgrade_module._has_symlink_component(tmp_path, junction / "to-spec" / "SKILL.md")
    assert (real / "to-spec").exists() is False


def test_backup_failure_restores_already_relocated_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = _make_project(tmp_path)
    old = b"OLD"
    (project / "CLAUDE.md").write_bytes(old)
    _set_inventory_hash(project, "CLAUDE.md", old)
    _add_obsolete_managed_file(
        project, "docs/handoffs/phase-N/01-plan.md", recorded_content=b"legacy"
    )
    before = _tree_snapshot(project)
    original = upgrade_module._relocate_path
    calls = 0

    def fail_second(source: Path, destination: Path) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("injected backup failure")
        original(source, destination)

    monkeypatch.setattr(upgrade_module, "_relocate_path", fail_second)
    with pytest.raises(UpgradeError, match="rolled back"):
        upgrade_project(project)
    assert _tree_snapshot(project) == before


def test_stamp_write_failure_restores_empty_directory_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = _make_project(tmp_path)
    _remove_windsurf_tree(project)
    before = _tree_snapshot(project)
    original = upgrade_module._write_target

    def fail_stamp(path: Path, data: bytes) -> None:
        if path.name == ".dev-ready.json":
            raise OSError("injected stamp failure")
        original(path, data)

    monkeypatch.setattr(upgrade_module, "_write_target", fail_stamp)
    with pytest.raises(UpgradeError, match="rolled back"):
        upgrade_project(project)
    assert _tree_snapshot(project) == before
    assert not (project / ".windsurf").exists()


def test_rollback_leaves_an_unrelated_native_link_untouched(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = _make_project(tmp_path)
    old = b"OLD"
    (project / "CLAUDE.md").write_bytes(old)
    _set_inventory_hash(project, "CLAUDE.md", old)
    canonical = project / "user-skill"
    canonical.mkdir()
    (canonical / "SKILL.md").write_text("user\n", encoding="utf-8")
    user_link = project / "user-link"
    create_skill_link(user_link, canonical)
    before = _tree_snapshot(project)

    def fail_first(path: Path, data: bytes) -> None:
        raise OSError("injected write failure")

    monkeypatch.setattr(upgrade_module, "_write_target", fail_first)
    with pytest.raises(UpgradeError, match="rolled back"):
        upgrade_project(project)
    assert _tree_snapshot(project) == before
    assert classify_path(user_link) in {PathKind.JUNCTION, PathKind.SYMBOLIC_LINK}
    assert (canonical / "SKILL.md").read_text(encoding="utf-8") == "user\n"


def _anchor_entries(project: Path, skills_dir: str) -> list[str]:
    text = (project / skills_dir / ".gitignore").read_text(encoding="utf-8")
    return [line for line in text.splitlines() if line and not line.startswith("#")]


def _remove_native_link(path: Path) -> None:
    if path.is_symlink() or path.is_junction():
        path.unlink()


def _inventory_hash(project: Path, path: str) -> str:
    stamp = load_stamp(project)
    for entry in stamp.inventory:
        if entry.path == path:
            return entry.sha256
    raise AssertionError(f"inventory has no {path}")


def test_differing_nested_gitignore_blocks_every_link_change_in_that_target(
    tmp_path: Path,
) -> None:
    project = _make_project(tmp_path)
    edited = b"# mine\ncustom-rule\n"
    (project / ".claude" / "skills" / ".gitignore").write_bytes(edited)
    claude_link = project / ".claude" / "skills" / "caveman"
    windsurf_link = project / ".windsurf" / "skills" / "caveman"
    _remove_native_link(claude_link)
    _remove_native_link(windsurf_link)
    before_claude = _tree_snapshot(project / ".claude" / "skills")

    report = upgrade_project(project)

    assert (project / ".claude" / "skills" / ".gitignore").read_bytes() == edited
    assert classify_path(claude_link) == PathKind.ABSENT
    assert _tree_snapshot(project / ".claude" / "skills") == before_claude
    assert classify_path(windsurf_link) in {PathKind.JUNCTION, PathKind.SYMBOLIC_LINK}
    assert "Skipped (user-modified)" in report
    assert "  - .claude/skills/.gitignore" in report
    assert "  - .claude/skills\n" in report or "  - .claude/skills\r\n" in report
    assert "  - .windsurf/skills/caveman" in report


def test_recorded_missing_nested_gitignore_is_restored_and_ordinary_missing_is_not(
    tmp_path: Path,
) -> None:
    project = _make_project(tmp_path)
    anchor = project / ".claude" / "skills" / ".gitignore"
    names = _anchor_entries(project, ".claude/skills")
    expected = render_ignore_anchor(names)
    anchor.unlink()
    agents = project / "AGENTS.md"
    agents.unlink()

    report = upgrade_project(project)

    assert anchor.read_bytes() == expected
    assert not agents.exists()
    assert "would restore" not in report
    assert "Restored" in report
    assert ".claude/skills/.gitignore" in report
    assert "Skipped (missing)" in report
    assert "AGENTS.md" in report
    assert _inventory_hash(project, ".claude/skills/.gitignore") == hashlib.sha256(
        expected
    ).hexdigest()


def test_dry_run_reports_would_restore_missing_anchor_without_mutation(
    tmp_path: Path,
) -> None:
    project = _make_project(tmp_path)
    anchor = project / ".claude" / "skills" / ".gitignore"
    anchor.unlink()
    before = _tree_snapshot(project)

    report = upgrade_project(project, dry_run=True)

    assert _tree_snapshot(project) == before
    assert "would restore .claude/skills/.gitignore" in report
    assert not anchor.exists()


def test_identical_unrecorded_nested_gitignore_is_adopted(tmp_path: Path) -> None:
    project = _make_project(tmp_path)
    expected = (project / ".claude" / "skills" / ".gitignore").read_bytes()
    _drop_from_inventory(project, ".claude/skills/.gitignore")
    link = project / ".claude" / "skills" / "caveman"
    _remove_native_link(link)

    report = upgrade_project(project)

    assert (project / ".claude" / "skills" / ".gitignore").read_bytes() == expected
    assert classify_path(link) in {PathKind.JUNCTION, PathKind.SYMBOLIC_LINK}
    assert "  - .claude/skills/.gitignore" not in report
    assert _inventory_hash(project, ".claude/skills/.gitignore") == hashlib.sha256(
        expected
    ).hexdigest()


def test_partial_conversion_inventories_only_post_transaction_links(
    tmp_path: Path,
) -> None:
    project = _make_project(tmp_path)
    _materialize_required_upstream_paths(project)
    occupant = project / ".claude" / "skills" / "caveman"
    _remove_native_link(occupant)
    occupant.mkdir()
    (occupant / "notes.md").write_text("mine\n", encoding="utf-8")
    setup = project / ".claude" / "skills" / "setup-project"
    _remove_native_link(setup)

    report = upgrade_project(project)

    assert (occupant / "notes.md").read_text(encoding="utf-8") == "mine\n"
    assert classify_path(occupant) == PathKind.DIRECTORY
    assert classify_path(setup) in {PathKind.JUNCTION, PathKind.SYMBOLIC_LINK}
    names = _anchor_entries(project, ".claude/skills")
    assert "caveman" not in names
    assert "setup-project" in names
    assert _inventory_hash(project, ".claude/skills/.gitignore") == hashlib.sha256(
        render_ignore_anchor(names)
    ).hexdigest()
    assert "Conflict" in report
    assert ".claude/skills/caveman" in report
    assert main(["check", str(project)]) == 7

    shutil.rmtree(occupant)
    second = upgrade_project(project)

    assert classify_path(occupant) in {PathKind.JUNCTION, PathKind.SYMBOLIC_LINK}
    assert "caveman" in _anchor_entries(project, ".claude/skills")
    assert "Skill Links created" in second
    repeat = upgrade_project(project, dry_run=True)
    assert "would create" not in repeat
    assert "would repair" not in repeat
    assert "No changes were needed." in repeat
    assert main(["check", str(project)]) == 0


def test_user_modified_canonical_content_is_ready_for_its_link(
    tmp_path: Path,
) -> None:
    project = _make_project(tmp_path)
    canonical = project / ".agents" / "skills" / "caveman" / "SKILL.md"
    canonical.write_bytes(b"edited skill\n")
    link = project / ".claude" / "skills" / "caveman"
    _remove_native_link(link)

    report = upgrade_project(project)

    assert canonical.read_bytes() == b"edited skill\n"
    assert classify_path(link) in {PathKind.JUNCTION, PathKind.SYMBOLIC_LINK}
    assert "Skill Links created" in report
    assert ".claude/skills/caveman" in report


def test_missing_recorded_canonical_file_blocks_only_that_skill_link(
    tmp_path: Path,
) -> None:
    project = _make_project(tmp_path)
    (project / ".agents" / "skills" / "caveman" / "SKILL.md").unlink()
    caveman = project / ".claude" / "skills" / "caveman"
    setup = project / ".claude" / "skills" / "setup-project"
    _remove_native_link(caveman)
    _remove_native_link(setup)

    report = upgrade_project(project)

    assert classify_path(caveman) == PathKind.ABSENT
    assert classify_path(setup) in {PathKind.JUNCTION, PathKind.SYMBOLIC_LINK}
    assert "caveman" not in _anchor_entries(project, ".claude/skills")
    assert "setup-project" in _anchor_entries(project, ".claude/skills")
    assert "Skipped (missing)" in report
    assert ".agents/skills/caveman/SKILL.md" in report


def test_redirected_agent_target_container_blocks_the_whole_target(
    tmp_path: Path,
) -> None:
    project = _make_project(tmp_path)
    skills = project / ".claude" / "skills"
    real = project / ".claude" / "skills-real"
    skills.rename(real)
    create_skill_link(skills, real)
    before = _tree_snapshot(real)
    windsurf = project / ".windsurf" / "skills" / "caveman"
    _remove_native_link(windsurf)

    report = upgrade_project(project)

    assert classify_path(skills) in {PathKind.JUNCTION, PathKind.SYMBOLIC_LINK}
    assert _tree_snapshot(real) == before
    assert "Conflict" in report
    assert report.count(".claude/skills") >= 1
    assert classify_path(windsurf) in {PathKind.JUNCTION, PathKind.SYMBOLIC_LINK}


def test_restored_anchor_rolls_back_when_a_later_write_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = _make_project(tmp_path)
    (project / ".claude" / "skills" / ".gitignore").unlink()
    before = _tree_snapshot(project)
    original = upgrade_module._write_target

    def fail_stamp(path: Path, data: bytes) -> None:
        if path.name == ".dev-ready.json":
            raise OSError("injected stamp failure")
        original(path, data)

    monkeypatch.setattr(upgrade_module, "_write_target", fail_stamp)
    with pytest.raises(UpgradeError, match="rolled back"):
        upgrade_project(project)

    assert _tree_snapshot(project) == before
    assert not (project / ".claude" / "skills" / ".gitignore").exists()


def _replace_link_with_recorded_stub(
    project: Path,
    skills_dir: str,
    skill_name: str,
    content: bytes = b"pointer stub\n",
) -> Path:
    link = project / skills_dir / skill_name
    _remove_native_link(link)
    stub = link / "SKILL.md"
    stub.parent.mkdir(parents=True, exist_ok=True)
    stub.write_bytes(content)
    _add_obsolete_managed_file(
        project,
        f"{skills_dir}/{skill_name}/SKILL.md",
        recorded_content=content,
    )
    return stub


def test_untouched_pointer_stub_directory_is_retired_and_replaced_by_a_link(
    tmp_path: Path,
) -> None:
    project = _make_project(tmp_path)
    _replace_link_with_recorded_stub(project, ".claude/skills", "caveman")

    report = upgrade_project(project)

    link = project / ".claude" / "skills" / "caveman"
    assert classify_path(link) in {PathKind.JUNCTION, PathKind.SYMBOLIC_LINK}
    assert link.resolve() == (project / ".agents" / "skills" / "caveman").resolve()
    assert "Deleted (obsolete)" in report
    assert ".claude/skills/caveman/SKILL.md" in report
    stamp = load_stamp(project)
    assert stamp.stamp_version == 5
    assert not any(
        entry.path.endswith("/SKILL.md") and entry.path.startswith(".claude/")
        for entry in stamp.inventory
    )
    repeat = upgrade_project(project, dry_run=True)
    assert "would delete" not in repeat
    assert "would create" not in repeat
    assert "No changes were needed." in repeat


def test_missing_recorded_stub_in_empty_scaffold_still_converts(
    tmp_path: Path,
) -> None:
    project = _make_project(tmp_path)
    stub = _replace_link_with_recorded_stub(project, ".claude/skills", "caveman")
    stub.unlink()
    assert stub.parent.is_dir()

    upgrade_project(project)

    link = project / ".claude" / "skills" / "caveman"
    assert classify_path(link) in {PathKind.JUNCTION, PathKind.SYMBOLIC_LINK}
    assert classify_path(stub.parent) != PathKind.DIRECTORY or link == stub.parent


def test_untouched_stub_with_siblings_loses_only_the_managed_file(
    tmp_path: Path,
) -> None:
    project = _make_project(tmp_path)
    stub = _replace_link_with_recorded_stub(project, ".claude/skills", "caveman")
    sibling = stub.parent / "notes.md"
    sibling.write_text("mine\n", encoding="utf-8")

    report = upgrade_project(project)

    assert not stub.exists()
    assert sibling.read_text(encoding="utf-8") == "mine\n"
    assert classify_path(stub.parent) == PathKind.DIRECTORY
    assert "caveman" not in _anchor_entries(project, ".claude/skills")
    assert ".claude/skills/caveman" in report


def test_modified_pointer_stub_is_preserved_and_blocks_its_link(
    tmp_path: Path,
) -> None:
    project = _make_project(tmp_path)
    stub = _replace_link_with_recorded_stub(project, ".claude/skills", "caveman")
    stub.write_bytes(b"user-edited stub\n")

    report = upgrade_project(project)

    assert stub.read_bytes() == b"user-edited stub\n"
    assert classify_path(stub.parent) == PathKind.DIRECTORY
    assert "Preserved (obsolete, user-modified)" in report
    assert "Divergence" in report
    assert ".claude/skills/caveman/SKILL.md" in report
    assert classify_path(project / ".claude" / "skills" / "caveman") == PathKind.DIRECTORY


def test_correct_link_at_obsolete_stub_path_is_completed_conversion(
    tmp_path: Path,
) -> None:
    project = _make_project(tmp_path)
    canonical = (project / ".agents" / "skills" / "caveman" / "SKILL.md").read_bytes()
    stamp_path = project / ".dev-ready.json"
    data = json.loads(stamp_path.read_text(encoding="utf-8"))
    data["inventory"].append(
        {
            "path": ".claude/skills/caveman/SKILL.md",
            "sha256": hashlib.sha256(b"pointer stub\n").hexdigest(),
        }
    )
    stamp_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    report = upgrade_project(project)

    link = project / ".claude" / "skills" / "caveman"
    assert classify_path(link) in {PathKind.JUNCTION, PathKind.SYMBOLIC_LINK}
    assert (project / ".agents" / "skills" / "caveman" / "SKILL.md").read_bytes() == canonical
    assert "  - .claude/skills/caveman/SKILL.md" not in report


def test_v3_full_copy_directory_retires_as_one_clean_cohort(
    tmp_path: Path,
) -> None:
    project = _make_pre_agent_target_project(tmp_path)
    _materialize_required_upstream_paths(project)
    skill_dir = project / ".claude" / "skills" / "caveman"
    script = skill_dir / "scripts" / "run.py"
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_bytes(b"print('hi')\n")
    _add_obsolete_managed_file(
        project,
        ".claude/skills/caveman/scripts/run.py",
        recorded_content=b"print('hi')\n",
    )

    report = upgrade_project(project)

    link = project / ".claude" / "skills" / "caveman"
    assert classify_path(link) in {PathKind.JUNCTION, PathKind.SYMBOLIC_LINK}
    assert not script.exists()
    assert load_stamp(project).stamp_version == 5
    assert ".claude/skills/caveman/SKILL.md" in report
    assert ".claude/skills/caveman/scripts/run.py" in report


def test_v3_missing_recorded_cohort_file_does_not_block_retirement(
    tmp_path: Path,
) -> None:
    project = _make_pre_agent_target_project(tmp_path)
    skill_dir = project / ".claude" / "skills" / "caveman"
    _add_obsolete_managed_file(
        project,
        ".claude/skills/caveman/LICENSE",
        recorded_content=b"MIT\n",
    )
    (skill_dir / "LICENSE").unlink()

    upgrade_project(project)

    link = project / ".claude" / "skills" / "caveman"
    assert classify_path(link) in {PathKind.JUNCTION, PathKind.SYMBOLIC_LINK}


def test_v3_modified_or_extra_entry_preserves_the_whole_cohort(
    tmp_path: Path,
) -> None:
    project = _make_pre_agent_target_project(tmp_path)
    skill_dir = project / ".claude" / "skills" / "caveman"
    script = skill_dir / "scripts" / "run.py"
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_bytes(b"print('hi')\n")
    _add_obsolete_managed_file(
        project,
        ".claude/skills/caveman/scripts/run.py",
        recorded_content=b"print('hi')\n",
    )
    script.write_bytes(b"print('edited')\n")
    extra = skill_dir / "notes.md"
    extra.write_text("mine\n", encoding="utf-8")
    original_skill = (skill_dir / "SKILL.md").read_bytes()

    report = upgrade_project(project)

    assert (skill_dir / "SKILL.md").read_bytes() == original_skill
    assert script.read_bytes() == b"print('edited')\n"
    assert extra.read_text(encoding="utf-8") == "mine\n"
    assert classify_path(skill_dir) == PathKind.DIRECTORY
    assert ".claude/skills/caveman/scripts/run.py" in report
    assert ".claude/skills/caveman/notes.md" in report or "notes.md" in report


def test_legacy_directory_retirement_rolls_back_the_complete_cohort(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = _make_pre_agent_target_project(tmp_path)
    skill_dir = project / ".claude" / "skills" / "caveman"
    script = skill_dir / "scripts" / "run.py"
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_bytes(b"print('hi')\n")
    _add_obsolete_managed_file(
        project,
        ".claude/skills/caveman/scripts/run.py",
        recorded_content=b"print('hi')\n",
    )
    before = _tree_snapshot(project)
    original = upgrade_module._write_target

    def fail_stamp(path: Path, data: bytes) -> None:
        if path.name == ".dev-ready.json":
            raise OSError("injected stamp failure")
        original(path, data)

    monkeypatch.setattr(upgrade_module, "_write_target", fail_stamp)
    with pytest.raises(UpgradeError, match="rolled back"):
        upgrade_project(project)

    assert _tree_snapshot(project) == before
    assert script.read_bytes() == b"print('hi')\n"


def _record_anchor_with_extra_name(
    project: Path, skills_dir: str, extra_name: str
) -> bytes:
    names = [*_anchor_entries(project, skills_dir), extra_name]
    data = render_ignore_anchor(names)
    anchor = project / skills_dir / ".gitignore"
    anchor.write_bytes(data)
    _set_inventory_hash(project, f"{skills_dir}/.gitignore", data)
    return data


def test_unmodified_anchor_retires_a_stale_link_when_a_skill_disappears(
    tmp_path: Path,
) -> None:
    project = _make_project(tmp_path)
    canonical = project / ".agents" / "skills" / "caveman"
    stale = project / ".claude" / "skills" / "retired-skill"
    create_skill_link(stale, canonical)
    _record_anchor_with_extra_name(project, ".claude/skills", "retired-skill")

    report = upgrade_project(project)

    assert classify_path(stale) == PathKind.ABSENT
    assert "retired-skill" not in _anchor_entries(project, ".claude/skills")
    assert "retired-skill" in report
    assert ".claude/skills/retired-skill" in report
    stamp = load_stamp(project)
    assert not any(entry.path.endswith("/retired-skill") for entry in stamp.inventory)
    repeat = upgrade_project(project, dry_run=True)
    assert "retired-skill" not in repeat or "would remove" not in repeat
    assert "No changes were needed." in repeat


def test_real_occupant_at_a_stale_name_is_preserved_and_reported(
    tmp_path: Path,
) -> None:
    project = _make_project(tmp_path)
    occupant = project / ".claude" / "skills" / "retired-skill"
    occupant.mkdir()
    (occupant / "notes.md").write_text("mine\n", encoding="utf-8")
    _record_anchor_with_extra_name(project, ".claude/skills", "retired-skill")

    report = upgrade_project(project)

    assert (occupant / "notes.md").read_text(encoding="utf-8") == "mine\n"
    assert classify_path(occupant) == PathKind.DIRECTORY
    assert "retired-skill" not in _anchor_entries(project, ".claude/skills")
    assert ".claude/skills/retired-skill" in report


def test_modified_anchor_preserves_stale_links_for_manual_reconciliation(
    tmp_path: Path,
) -> None:
    project = _make_project(tmp_path)
    canonical = project / ".agents" / "skills" / "caveman"
    stale = project / ".claude" / "skills" / "retired-skill"
    create_skill_link(stale, canonical)
    names = [*_anchor_entries(project, ".claude/skills"), "retired-skill"]
    (project / ".claude" / "skills" / ".gitignore").write_bytes(
        render_ignore_anchor(names) + b"# user note\n"
    )

    report = upgrade_project(project)

    assert classify_path(stale) in {PathKind.JUNCTION, PathKind.SYMBOLIC_LINK}
    assert "Skipped (user-modified)" in report
    assert ".claude/skills/.gitignore" in report
    assert ".claude/skills" in report


def test_obsolete_unmodified_anchor_retires_its_trusted_links(
    tmp_path: Path,
) -> None:
    project = _make_project(tmp_path)
    windsurf_link = project / ".windsurf" / "skills" / "caveman"
    assert classify_path(windsurf_link) in {PathKind.JUNCTION, PathKind.SYMBOLIC_LINK}
    stamp_path = project / ".dev-ready.json"
    data = json.loads(stamp_path.read_text(encoding="utf-8"))
    data["agent_targets"] = ["claude"]
    stamp_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    report = upgrade_project(project)

    assert classify_path(windsurf_link) == PathKind.ABSENT
    assert not (project / ".windsurf" / "skills" / ".gitignore").exists()
    assert ".windsurf/skills" in report or ".windsurf/skills/caveman" in report
    assert not any(
        entry.path.startswith(".windsurf/skills/")
        for entry in load_stamp(project).inventory
    )


def test_stale_link_retirement_rolls_back_on_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = _make_project(tmp_path)
    canonical = project / ".agents" / "skills" / "caveman"
    stale = project / ".claude" / "skills" / "retired-skill"
    create_skill_link(stale, canonical)
    _record_anchor_with_extra_name(project, ".claude/skills", "retired-skill")
    before = _tree_snapshot(project)
    original = upgrade_module._write_target

    def fail_stamp(path: Path, data: bytes) -> None:
        if path.name == ".dev-ready.json":
            raise OSError("injected stamp failure")
        original(path, data)

    monkeypatch.setattr(upgrade_module, "_write_target", fail_stamp)
    with pytest.raises(UpgradeError, match="rolled back"):
        upgrade_project(project)

    assert _tree_snapshot(project) == before
    assert classify_path(stale) in {PathKind.JUNCTION, PathKind.SYMBOLIC_LINK}
