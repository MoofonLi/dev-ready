"""Unit tests for scripts/sync_vendored.py (no network; filesystem confined to tmp_path).

`scripts/` is CI-only tooling, loaded via importlib.util from an explicit file path.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from dev_ready.manifest.models import ItemPath, VendoredPin

_SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "sync_vendored.py"
_spec = importlib.util.spec_from_file_location("sync_vendored", _SCRIPT_PATH)
assert _spec is not None and _spec.loader is not None
sync_vendored = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sync_vendored)


def _pin(repo: str, commit: str, license_: str, paths: list[ItemPath]) -> VendoredPin:
    return VendoredPin(repo=repo, commit=commit, license=license_, paths=tuple(paths))


def test_build_path_mappings_empty_vendored(tmp_path: Path) -> None:
    mappings = sync_vendored.build_path_mappings([], tmp_path)
    assert mappings == []


def test_build_path_mappings_single_entry(tmp_path: Path) -> None:
    vendored = [
        _pin(
            "JuliusBrussee/caveman",
            "a" * 40,
            "MIT",
            [ItemPath(src="SKILL.md", dest="templates/claude/skills/caveman/SKILL.md")],
        )
    ]
    mappings = sync_vendored.build_path_mappings(vendored, tmp_path)
    assert len(mappings) == 1
    src, dest = mappings[0]
    assert src == "SKILL.md"
    assert dest == tmp_path / "templates/claude/skills/caveman/SKILL.md"


def test_build_path_mappings_multiple_entries(tmp_path: Path) -> None:
    vendored = [
        _pin(
            "JuliusBrussee/caveman",
            "a" * 40,
            "MIT",
            [
                ItemPath(src="SKILL.md", dest="templates/claude/skills/caveman/SKILL.md"),
                ItemPath(src="README.md", dest="templates/claude/skills/caveman/README.md"),
            ],
        ),
        _pin(
            "owner/other",
            "b" * 40,
            "Apache-2.0",
            [ItemPath(src="foo.txt", dest="templates/mcp/foo.txt")],
        ),
    ]
    mappings = sync_vendored.build_path_mappings(vendored, tmp_path)
    assert len(mappings) == 3
    assert mappings[0] == ("SKILL.md", tmp_path / "templates/claude/skills/caveman/SKILL.md")
    assert mappings[1] == ("README.md", tmp_path / "templates/claude/skills/caveman/README.md")
    assert mappings[2] == ("foo.txt", tmp_path / "templates/mcp/foo.txt")


def test_build_path_mappings_rejects_dest_outside_templates(tmp_path: Path) -> None:
    vendored = [
        _pin(
            "owner/repo",
            "a" * 40,
            "MIT",
            [ItemPath(src="SKILL.md", dest="src/dev_ready/evil.py")],
        )
    ]
    with pytest.raises(RuntimeError, match="escapes templates root"):
        sync_vendored.build_path_mappings(vendored, tmp_path)


def test_build_path_mappings_rejects_dest_traversal(tmp_path: Path) -> None:
    vendored = [
        _pin(
            "owner/repo",
            "a" * 40,
            "MIT",
            [ItemPath(src="SKILL.md", dest="templates/../evil.txt")],
        )
    ]
    with pytest.raises(RuntimeError, match="escapes templates root"):
        sync_vendored.build_path_mappings(vendored, tmp_path)


def test_copy_snapshot_copies_file_to_dest(tmp_path: Path) -> None:
    clone_dir = tmp_path / "clone"
    clone_dir.mkdir()
    (clone_dir / "src_file.txt").write_text("hello world", encoding="utf-8")

    dest_file = tmp_path / "output" / "dest_file.txt"
    mappings = [("src_file.txt", dest_file)]

    sync_vendored.copy_snapshot(clone_dir, mappings)
    assert dest_file.exists()
    assert dest_file.read_text(encoding="utf-8") == "hello world"


def test_copy_snapshot_creates_parent_dirs(tmp_path: Path) -> None:
    clone_dir = tmp_path / "clone"
    clone_dir.mkdir()
    (clone_dir / "deep.txt").write_text("nested content", encoding="utf-8")

    dest_file = tmp_path / "a" / "b" / "c" / "deep.txt"
    mappings = [("deep.txt", dest_file)]

    sync_vendored.copy_snapshot(clone_dir, mappings)
    assert dest_file.exists()
    assert dest_file.read_text(encoding="utf-8") == "nested content"


def test_copy_snapshot_raises_on_missing_src(tmp_path: Path) -> None:
    clone_dir = tmp_path / "clone"
    clone_dir.mkdir()

    dest_file = tmp_path / "dest.txt"
    mappings = [("nonexistent.txt", dest_file)]

    with pytest.raises(RuntimeError, match="source path does not exist"):
        sync_vendored.copy_snapshot(clone_dir, mappings)


def test_copy_snapshot_rejects_src_escaping_clone(tmp_path: Path) -> None:
    clone_dir = tmp_path / "clone"
    clone_dir.mkdir()
    (tmp_path / "secret.txt").write_text("outside", encoding="utf-8")

    dest_file = tmp_path / "dest.txt"
    mappings = [("../secret.txt", dest_file)]

    with pytest.raises(RuntimeError, match="escapes clone directory"):
        sync_vendored.copy_snapshot(clone_dir, mappings)


def test_sync_all_empty_vendored_returns_zero(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        """{
  "manifest_version": 1,
  "upstream": {
    "base_template": {
      "repo": "fastapi/full-stack-fastapi-template",
      "ref": "master",
      "commit": "%s",
      "license": "MIT"
    }
  },
  "vendored": [],
  "components": {"skills": {"items": []}, "mcp": {"items": []}},
  "overlay_version": "0.1.0"
}"""
        % ("a" * 40),
        encoding="utf-8",
    )
    count = sync_vendored.sync_all(manifest_path, tmp_path, tmp_path / ".sync-cache")
    assert count == 0


def test_sync_all_rejects_invalid_manifest(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text('{"manifest_version": 99}', encoding="utf-8")

    from dev_ready.errors import ManifestError

    with pytest.raises(ManifestError):
        sync_vendored.sync_all(manifest_path, tmp_path, tmp_path / ".sync-cache")
