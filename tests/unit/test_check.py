"""Unit tests for dev-ready check command and verification logic."""

import hashlib
import json
from pathlib import Path

import pytest

from dev_ready.cli import main
from dev_ready.manifest import load_default_manifest



def _create_minimal_valid_project(project_dir: Path, stamp_version: int = 2) -> None:
    manifest = load_default_manifest()
    pin = manifest.upstream["base_template"]
    vendored_map = {v.repo: v.commit for v in manifest.vendored}

    # Upstream required paths
    (project_dir / "backend").mkdir(parents=True, exist_ok=True)
    (project_dir / "frontend").mkdir(parents=True, exist_ok=True)
    (project_dir / "compose.yml").write_text("services: {}\n", encoding="utf-8")
    (project_dir / "compose.override.yml").write_text("services: {}\n", encoding="utf-8")
    (project_dir / ".env").write_text("ENV=test\n", encoding="utf-8")
    (project_dir / "LICENSE").write_text("MIT License\n", encoding="utf-8")

    # Required overlay files
    (project_dir / "CLAUDE.md").write_text("# Project\n", encoding="utf-8")
    (project_dir / "README.md").write_text("# Readme\n", encoding="utf-8")

    # Default items setup
    skill_item = manifest.components["skills"][0]
    skill_pin = vendored_map.get(skill_item.vendored_repo, skill_item.pin) if skill_item.vendored_repo else skill_item.pin

    mcp_item = manifest.components["mcp"][0]
    mcp_pin = mcp_item.pin

    # Create item paths
    for item in (skill_item, mcp_item):
        for item_path in item.paths:
            dest = project_dir / item_path.dest
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text("content\n", encoding="utf-8")

    # Create stamp
    if stamp_version == 1:
        stamp_data = {
            "stamp_version": 1,
            "dev_ready_version": "0.3.0",
            "components": {
                "skills": {"included": True, "items": [skill_item.id]},
                "mcp": {"included": True, "items": [mcp_item.id]},
                "docs": {"included": False},
                "agents": {"included": False},
            },
            "upstream": {"repo": pin.repo, "commit": pin.commit},
        }
    else:
        stamp_data = {
            "stamp_version": 2,
            "dev_ready_version": "0.5.0",
            "components": {
                "skills": {"included": True, "items": [{"id": skill_item.id, "pin": skill_pin}]},
                "mcp": {"included": True, "items": [{"id": mcp_item.id, "pin": mcp_pin}]},
                "docs": {"included": False},
                "agents": {"included": False},
            },
            "upstream": {"repo": pin.repo, "commit": pin.commit},
        }

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
    data["stamp_version"] = 3
    stamp_path.write_text(json.dumps(data), encoding="utf-8")

    exit_code = main(["check", str(tmp_path)])
    assert exit_code == 6
    captured = capsys.readouterr()
    assert "unsupported stamp_version 3" in captured.err


def test_check_upstream_pin_drift(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _create_minimal_valid_project(tmp_path, stamp_version=2)
    stamp_path = tmp_path / ".dev-ready.json"
    data = json.loads(stamp_path.read_text(encoding="utf-8"))
    data["upstream"]["commit"] = "0000000000000000000000000000000000000000"
    stamp_path.write_text(json.dumps(data), encoding="utf-8")

    exit_code = main(["check", str(tmp_path)])
    assert exit_code == 7
    captured = capsys.readouterr()
    assert "upstream pin drift" in captured.err


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
