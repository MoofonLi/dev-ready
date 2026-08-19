"""Unit tests for dev-ready check command and verification logic."""

import hashlib
import json
from pathlib import Path

import pytest

from dev_ready.cli import main
from dev_ready import __version__
from dev_ready.errors import StampInvalidError
from dev_ready.manifest import load_default_manifest
from dev_ready.prompts import ProjectSelection
from dev_ready.stamp import load_stamp
from project_factory import materialize_project_structure
from dev_ready.agent_targets import project_targets
from dev_ready.inspection import _desired_skill_names
from dev_ready.overlay import render_ignore_anchor
from dev_ready.recorded import RecordedProject



def _create_minimal_valid_project(project_dir: Path, stamp_version: int = 2) -> None:
    manifest = load_default_manifest()
    pin = manifest.upstream["base_template"]
    vendored_map = {v.repo: v.commit for v in manifest.vendored}

    # Default items setup
    skill_item = manifest.components["skills"][0]
    skill_pin = vendored_map.get(skill_item.vendored_repo, skill_item.pin) if skill_item.vendored_repo else skill_item.pin

    mcp_item = manifest.components["mcp"][0]
    mcp_pin = mcp_item.pin

    selection = ProjectSelection.from_items(
        manifest.components,
        skills=frozenset({skill_item.id}),
        mcp=frozenset({mcp_item.id}),
    )
    materialize_project_structure(project_dir, manifest.components, selection)

    # Create stamp
    if stamp_version == 1:
        stamp_data = {
            "stamp_version": 1,
            "dev_ready_version": __version__,
            "components": {
                "skills": {"included": True, "items": [skill_item.id]},
                "mcp": {"included": True, "items": [mcp_item.id]},
                "docs": {"included": False},
                "agents": {"included": False},
            },
            "upstream": {"repo": pin.repo, "commit": pin.commit},
        }
    elif stamp_version == 2:
        stamp_data = {
            "stamp_version": 2,
            "dev_ready_version": __version__,
            "components": {
                "skills": {"included": True, "items": [{"id": skill_item.id, "pin": skill_pin}]},
                "mcp": {"included": True, "items": [{"id": mcp_item.id, "pin": mcp_pin}]},
                "docs": {"included": False},
                "agents": {"included": False},
            },
            "upstream": {"repo": pin.repo, "commit": pin.commit},
        }
    else:
        component_key = "handoff" if stamp_version >= 4 else "agents"
        stamp_data = {
            "stamp_version": stamp_version,
            "dev_ready_version": __version__,
            "project_name": "test-project",
            "components": {
                "skills": {"included": True, "items": [{"id": skill_item.id, "pin": skill_pin}]},
                "mcp": {"included": True, "items": [{"id": mcp_item.id, "pin": mcp_pin}]},
                "docs": {"included": False},
                component_key: {"included": False},
            },
            "upstream": {"repo": pin.repo, "commit": pin.commit},
            "inventory": [],
        }
        if stamp_version >= 4:
            stamp_data["agent_targets"] = sorted(selection.agent_targets)
        if stamp_version >= 5:
            stamp_data["categories"] = sorted(selection.categories)
            stamp_data["development_loop"] = selection.development_loop
            loop_item = next(
                item
                for item in manifest.components.get("skills", ())
                if item.id == selection.development_loop
            )
            loop_pin = (
                vendored_map.get(loop_item.vendored_repo, loop_item.pin)
                if loop_item.vendored_repo
                else loop_item.pin
            )
            stamp_data["components"]["skills"]["items"].append(
                {"id": loop_item.id, "pin": loop_pin}
            )

    (project_dir / ".dev-ready.json").write_text(json.dumps(stamp_data, indent=2) + "\n", encoding="utf-8")
    if stamp_version < 5:
        _align_fixture_skill_projection(project_dir, manifest.components)


def _align_fixture_skill_projection(project_dir: Path, catalog) -> None:
    recorded = RecordedProject.observed(load_stamp(project_dir), load_default_manifest())
    names = _desired_skill_names(
        catalog, recorded.selection, recorded.selection.development_loop
    )
    projection = project_targets(catalog, recorded.selection.agent_targets)
    for target in projection.skill_targets:
        skills = project_dir / target.skills_dir
        if not skills.is_dir() or skills.is_symlink() or skills.is_junction():
            continue
        for child in list(skills.iterdir()):
            if child.name in names or child.name == ".gitignore":
                continue
            if child.is_symlink() or child.is_junction():
                child.unlink()
        if names:
            (skills / ".gitignore").write_bytes(render_ignore_anchor(names))
    selected_dirs = {target.skills_dir for target in projection.skill_targets}
    declared = project_targets(catalog, catalog.agent_target_ids)
    for target in declared.skill_targets:
        if target.skills_dir in selected_dirs:
            continue
        skills = project_dir / target.skills_dir
        if not skills.is_dir() or skills.is_symlink() or skills.is_junction():
            continue
        anchor = skills / ".gitignore"
        if anchor.is_file():
            anchor.unlink()
        for child in list(skills.iterdir()):
            if child.is_symlink() or child.is_junction():
                child.unlink()


def _get_tree_snapshot(root: Path) -> dict[str, str]:
    snapshot: dict[str, str] = {}
    for p in sorted(root.rglob("*")):
        if p.is_file():
            rel = str(p.relative_to(root))
            snapshot[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    return snapshot


def test_check_fresh_v2_project(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _create_minimal_valid_project(tmp_path, stamp_version=2)
    exit_code = main(["check", str(tmp_path)])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Status: CLEAN" in captured.out


def test_check_fresh_v1_project(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _create_minimal_valid_project(tmp_path, stamp_version=1)
    exit_code = main(["check", str(tmp_path)])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Status: CLEAN" in captured.out


def test_check_fresh_v5_project(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _create_minimal_valid_project(tmp_path, stamp_version=5)

    assert main(["check", str(tmp_path)]) == 0
    assert "Status: CLEAN" in capsys.readouterr().out


def test_check_resolves_a_retired_recorded_item_id_before_comparing_pins(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _create_minimal_valid_project(tmp_path, stamp_version=5)
    manifest = load_default_manifest()
    loop = next(item for item in manifest.components.loops() if item.id == "mattpocock")
    vendored_pins = {vendor.repo: vendor.commit for vendor in manifest.vendored}
    stamp_path = tmp_path / ".dev-ready.json"
    data = json.loads(stamp_path.read_text(encoding="utf-8"))
    data["development_loop"] = "spec-loop"
    data["components"]["skills"]["items"].append(
        {"id": "spec-loop", "pin": vendored_pins[loop.vendored_repo]}
    )
    stamp_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    assert main(["check", str(tmp_path)]) == 0
    output = capsys.readouterr()
    assert "Status: CLEAN" in output.out
    assert "removed catalog item" not in output.err


def test_check_still_reports_a_genuinely_removed_recorded_item(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _create_minimal_valid_project(tmp_path, stamp_version=5)
    stamp_path = tmp_path / ".dev-ready.json"
    data = json.loads(stamp_path.read_text(encoding="utf-8"))
    data["components"]["skills"]["items"].append(
        {"id": "missing-forever", "pin": None}
    )
    stamp_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    assert main(["check", str(tmp_path)]) == 7
    error = capsys.readouterr().err
    assert "removed catalog item" in error
    assert "missing-forever" in error


@pytest.mark.parametrize(
    ("stamp_version", "component_key"),
    [(3, "agents"), (4, "handoff")],
)
def test_check_legacy_stamp_with_handoff_state_stays_clean(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    stamp_version: int,
    component_key: str,
) -> None:
    _create_minimal_valid_project(tmp_path, stamp_version=stamp_version)
    stamp_path = tmp_path / ".dev-ready.json"
    data = json.loads(stamp_path.read_text(encoding="utf-8"))
    data["components"][component_key]["included"] = True
    stamp_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    assert load_stamp(tmp_path).handoff_included is True
    assert main(["check", str(tmp_path)]) == 0
    assert "Status: CLEAN" in capsys.readouterr().out


def test_check_reports_missing_selected_agent_target_artifact(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _create_minimal_valid_project(tmp_path, stamp_version=4)
    stamp_path = tmp_path / ".dev-ready.json"
    data = json.loads(stamp_path.read_text(encoding="utf-8"))
    data["agent_targets"] = ["windsurf"]
    stamp_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    missing = tmp_path / ".windsurf" / "skills" / "setup-project"
    assert missing.is_symlink() or missing.is_junction()
    missing.unlink()

    assert main(["check", str(tmp_path)]) == 7
    error = capsys.readouterr().err
    assert "missing agent target artifact" in error
    assert missing.relative_to(tmp_path).as_posix() in error


def test_check_reports_removed_recorded_agent_target(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _create_minimal_valid_project(tmp_path, stamp_version=4)
    stamp_path = tmp_path / ".dev-ready.json"
    data = json.loads(stamp_path.read_text(encoding="utf-8"))
    data["agent_targets"] = ["retired-agent"]
    stamp_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    assert main(["check", str(tmp_path)]) == 7
    error = capsys.readouterr().err
    assert "removed agent target" in error
    assert "retired-agent" in error


def test_check_json_output(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _create_minimal_valid_project(tmp_path, stamp_version=2)
    exit_code = main(["check", str(tmp_path), "--json"])
    assert exit_code == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["clean"] is True
    assert data["drift_count"] == 0


def test_check_missing_stamp(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # Empty directory
    exit_code = main(["check", str(tmp_path)])
    assert exit_code == 6
    captured = capsys.readouterr()
    assert "missing .dev-ready.json" in captured.err
    assert "projects generated before dev-ready v0.3 have no stamp" in captured.err


def test_check_corrupt_stamp(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (tmp_path / ".dev-ready.json").write_text("{corrupt json", encoding="utf-8")
    exit_code = main(["check", str(tmp_path)])
    assert exit_code == 6
    captured = capsys.readouterr()
    assert "failed to read or parse .dev-ready.json" in captured.err


def test_check_future_stamp_version(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _create_minimal_valid_project(tmp_path, stamp_version=2)
    stamp_path = tmp_path / ".dev-ready.json"
    data = json.loads(stamp_path.read_text(encoding="utf-8"))
    data["stamp_version"] = 6
    stamp_path.write_text(json.dumps(data), encoding="utf-8")

    exit_code = main(["check", str(tmp_path)])
    assert exit_code == 6
    captured = capsys.readouterr()
    assert "unsupported stamp_version 6" in captured.err


def test_malformed_v5_categories_raise_typed_stamp_error(tmp_path: Path) -> None:
    _create_minimal_valid_project(tmp_path, stamp_version=5)
    stamp_path = tmp_path / ".dev-ready.json"
    data = json.loads(stamp_path.read_text(encoding="utf-8"))
    data["categories"] = "design"
    stamp_path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(StampInvalidError, match="categories.*list of identifiers"):
        load_stamp(tmp_path)


def test_v5_stamp_requires_a_development_loop(tmp_path: Path) -> None:
    _create_minimal_valid_project(tmp_path, stamp_version=5)
    stamp_path = tmp_path / ".dev-ready.json"
    data = json.loads(stamp_path.read_text(encoding="utf-8"))
    data.pop("development_loop")
    stamp_path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(StampInvalidError, match="development_loop"):
        load_stamp(tmp_path)


def test_v5_stamp_loads_selected_docs_items(tmp_path: Path) -> None:
    _create_minimal_valid_project(tmp_path, stamp_version=5)
    stamp_path = tmp_path / ".dev-ready.json"
    data = json.loads(stamp_path.read_text(encoding="utf-8"))
    data["components"]["docs"] = {
        "included": True,
        "items": [{"id": "design-stripe", "pin": "a" * 40}],
    }
    stamp_path.write_text(json.dumps(data), encoding="utf-8")

    stamp = load_stamp(tmp_path)

    assert [(item.id, item.pin) for item in stamp.docs_items] == [
        ("design-stripe", "a" * 40)
    ]


def test_check_v5_uses_the_recorded_docs_item_selection(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    manifest = load_default_manifest()
    selection = ProjectSelection.from_items(
        manifest.components,
        docs_items=frozenset({"design-stripe"}),
    )
    materialize_project_structure(tmp_path, manifest.components, selection)
    _create_minimal_valid_project(tmp_path, stamp_version=5)
    stamp_path = tmp_path / ".dev-ready.json"
    data = json.loads(stamp_path.read_text(encoding="utf-8"))
    data["categories"] = ["design"]
    data["components"]["docs"] = {
        "included": True,
        "items": [{"id": "design-stripe", "pin": None}],
    }
    stamp_path.write_text(json.dumps(data), encoding="utf-8")

    assert main(["check", str(tmp_path)]) == 0
    assert "Status: CLEAN" in capsys.readouterr().out


def test_v4_stamp_requires_agent_target_state(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _create_minimal_valid_project(tmp_path, stamp_version=4)
    stamp_path = tmp_path / ".dev-ready.json"
    data = json.loads(stamp_path.read_text(encoding="utf-8"))
    data.pop("agent_targets", None)
    stamp_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    assert main(["check", str(tmp_path)]) == 6
    assert "agent_targets" in capsys.readouterr().err


def test_check_newer_upstream_pin_is_a_non_blocking_advisory(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _create_minimal_valid_project(tmp_path, stamp_version=2)
    stamp_path = tmp_path / ".dev-ready.json"
    data = json.loads(stamp_path.read_text(encoding="utf-8"))
    data["upstream"]["commit"] = "0000000000000000000000000000000000000000"
    stamp_path.write_text(json.dumps(data), encoding="utf-8")

    exit_code = main(["check", str(tmp_path)])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "base update advisory" in captured.out
    assert "Status: CLEAN" in captured.out


def test_check_json_separates_base_advisories_from_actionable_drift(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _create_minimal_valid_project(tmp_path, stamp_version=3)
    stamp_path = tmp_path / ".dev-ready.json"
    data = json.loads(stamp_path.read_text(encoding="utf-8"))
    data["upstream"]["commit"] = "0" * 40
    stamp_path.write_text(json.dumps(data), encoding="utf-8")

    assert main(["check", str(tmp_path), "--json"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["clean"] is True
    assert report["drift_count"] == 0
    assert report["advisory_count"] == 1
    assert "base update advisory" in report["advisories"][0]


def test_check_stale_dev_ready_version_is_overlay_currency_drift(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _create_minimal_valid_project(tmp_path, stamp_version=3)
    stamp_path = tmp_path / ".dev-ready.json"
    data = json.loads(stamp_path.read_text(encoding="utf-8"))
    data["dev_ready_version"] = "0.6.0"
    stamp_path.write_text(json.dumps(data), encoding="utf-8")

    assert main(["check", str(tmp_path)]) == 7
    assert "overlay version drift" in capsys.readouterr().err


def test_check_item_pin_drift(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _create_minimal_valid_project(tmp_path, stamp_version=2)
    stamp_path = tmp_path / ".dev-ready.json"
    data = json.loads(stamp_path.read_text(encoding="utf-8"))
    data["components"]["skills"]["items"][0]["pin"] = "0.0.0-outdated"
    stamp_path.write_text(json.dumps(data), encoding="utf-8")

    exit_code = main(["check", str(tmp_path)])
    assert exit_code == 7
    captured = capsys.readouterr()
    assert "skills pin drift" in captured.err


def test_check_missing_required_path(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _create_minimal_valid_project(tmp_path, stamp_version=2)
    # Remove required backend dir
    for file in (tmp_path / "backend").iterdir():
        file.unlink()
    (tmp_path / "backend").rmdir()

    exit_code = main(["check", str(tmp_path)])
    assert exit_code == 7
    captured = capsys.readouterr()
    assert "required path 'backend' is missing" in captured.err


def test_check_forbidden_path_present(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _create_minimal_valid_project(tmp_path, stamp_version=2)
    (tmp_path / ".git").mkdir()

    exit_code = main(["check", str(tmp_path)])
    assert exit_code == 7
    captured = capsys.readouterr()
    assert "forbidden path '.git'" in captured.err


def test_check_read_only_assertion(tmp_path: Path) -> None:
    _create_minimal_valid_project(tmp_path, stamp_version=2)
    before_snapshot = _get_tree_snapshot(tmp_path)

    # Run check multiple times (clean and failing)
    main(["check", str(tmp_path)])
    main(["check", str(tmp_path), "--json"])

    # Introduce drift and check again
    (tmp_path / ".git").mkdir()
    main(["check", str(tmp_path)])

    (tmp_path / ".git").rmdir()

    after_snapshot = _get_tree_snapshot(tmp_path)
    assert before_snapshot == after_snapshot


def test_check_reports_incomplete_nested_gitignore_as_drift(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _create_minimal_valid_project(tmp_path, stamp_version=5)
    from dev_ready.overlay import render_ignore_anchor

    anchor = tmp_path / ".claude" / "skills" / ".gitignore"
    assert anchor.is_file()
    anchor.write_bytes(render_ignore_anchor(["setup-project"]))

    assert main(["check", str(tmp_path)]) == 7
    error = capsys.readouterr().err
    assert ".claude/skills/.gitignore" in error


def test_check_reports_stale_skill_link_as_drift(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _create_minimal_valid_project(tmp_path, stamp_version=5)
    from dev_ready.skill_links import create_skill_link

    canonical = tmp_path / ".agents" / "skills" / "setup-project"
    stale = tmp_path / ".claude" / "skills" / "retired-skill"
    create_skill_link(stale, canonical)

    assert main(["check", str(tmp_path)]) == 7
    error = capsys.readouterr().err
    assert "retired-skill" in error
    assert "stale" in error


def test_check_reports_an_obsolete_nested_anchor_as_drift(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _create_minimal_valid_project(tmp_path, stamp_version=5)
    stamp_path = tmp_path / ".dev-ready.json"
    data = json.loads(stamp_path.read_text(encoding="utf-8"))
    data["agent_targets"] = ["claude"]
    stamp_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    leftover = tmp_path / ".windsurf" / "skills" / ".gitignore"
    leftover.parent.mkdir(parents=True, exist_ok=True)
    leftover.write_text("# leftover\n", encoding="utf-8")

    assert main(["check", str(tmp_path)]) == 7
    error = capsys.readouterr().err
    assert ".windsurf/skills/.gitignore" in error
    assert "obsolete" in error
