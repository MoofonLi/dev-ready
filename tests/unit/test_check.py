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

    (project_dir / ".dev-ready.json").write_text(json.dumps(stamp_data, indent=2) + "\n", encoding="utf-8")


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
    selected_skill_id = data["components"]["skills"]["items"][0]["id"]
    missing = tmp_path / f".windsurf/skills/{selected_skill_id}/SKILL.md"
    missing.unlink()

    assert main(["check", str(tmp_path)]) == 7
    error = capsys.readouterr().err
    assert "missing agent target artifact" in error
    assert f".windsurf/skills/{selected_skill_id}/SKILL.md" in error


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
