"""Unit tests for scripts/sync_vendored.py (no network; filesystem confined to tmp_path).

`scripts/` is CI-only tooling, loaded via importlib.util from an explicit file path.
"""

from __future__ import annotations

from dataclasses import replace
import importlib.util
from pathlib import Path
import subprocess

import pytest

from dev_ready.manifest import load_default_manifest
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
            [
                ItemPath(
                    src="SKILL.md", dest="src/dev_ready/templates/claude/skills/caveman/SKILL.md"
                )
            ],
        )
    ]
    mappings = sync_vendored.build_path_mappings(vendored, tmp_path)
    assert len(mappings) == 1
    src, dest = mappings[0]
    assert src == "SKILL.md"
    assert dest == tmp_path / "src/dev_ready/templates/claude/skills/caveman/SKILL.md"


def test_build_path_mappings_multiple_entries(tmp_path: Path) -> None:
    vendored = [
        _pin(
            "JuliusBrussee/caveman",
            "a" * 40,
            "MIT",
            [
                ItemPath(
                    src="SKILL.md", dest="src/dev_ready/templates/claude/skills/caveman/SKILL.md"
                ),
                ItemPath(
                    src="README.md", dest="src/dev_ready/templates/claude/skills/caveman/README.md"
                ),
            ],
        ),
        _pin(
            "owner/other",
            "b" * 40,
            "Apache-2.0",
            [ItemPath(src="foo.txt", dest="src/dev_ready/templates/mcp/foo.txt")],
        ),
    ]
    mappings = sync_vendored.build_path_mappings(vendored, tmp_path)
    assert len(mappings) == 3
    assert mappings[0] == (
        "SKILL.md",
        tmp_path / "src/dev_ready/templates/claude/skills/caveman/SKILL.md",
    )
    assert mappings[1] == (
        "README.md",
        tmp_path / "src/dev_ready/templates/claude/skills/caveman/README.md",
    )
    assert mappings[2] == ("foo.txt", tmp_path / "src/dev_ready/templates/mcp/foo.txt")


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
            [ItemPath(src="SKILL.md", dest="src/dev_ready/templates/../evil.txt")],
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
  "default_set": {"development_loop": "sample-loop", "documentation": ["architecture", "requirements"], "enhancements": []},
  "categories": {"dev": {"description": "Development loop."}},
  "agent_targets": {"claude": {"description": "Claude Code.", "skills_dir": ".claude/skills", "rules_file": "CLAUDE.md", "mcp_file": ".mcp.json"}},
  "upstream": {
    "base_template": {
      "repo": "fastapi/full-stack-fastapi-template",
      "ref": "master",
      "commit": "%s",
      "license": "MIT"
    }
  },
  "vendored": [],
  "components": {"skills": {"items": [{"id": "sample-loop", "kind": "development-loop", "steps": ["sample-step"], "invocation": "user", "chain": ["sample-step"], "roles": {"build": ["sample-step"]}, "category": "dev", "description": "Sample loop.", "mode": "builtin", "license": "MIT", "paths": [{"src": "sample", "dest": ".agents/skills/sample-step"}]}]}, "mcp": {"items": []}, "docs": {"items": []}},
  "overlay_version": "0.1.0"
}"""
        % ("a" * 40),
        encoding="utf-8",
    )
    count = sync_vendored.sync_all(manifest_path, tmp_path, tmp_path / ".sync-cache")
    assert count == 0


def test_pathless_provenance_entry_does_not_require_sync() -> None:
    pathless = _pin(
        "vercel-labs/skills",
        "1164afa5f0e21ebd01e6fc11249759353f494ad1",
        "MIT",
        [],
    )

    assert sync_vendored.entries_requiring_sync([pathless]) == ()


def test_sync_all_rejects_invalid_manifest(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text('{"manifest_version": 99}', encoding="utf-8")

    from dev_ready.errors import ManifestError

    with pytest.raises(ManifestError):
        sync_vendored.sync_all(manifest_path, tmp_path, tmp_path / ".sync-cache")


def test_clone_or_fetch_disables_checkout_line_ending_conversion(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[list[str]] = []

    def successful_run(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, returncode=0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", successful_run)

    sync_vendored.clone_or_fetch("owner/repo", "a" * 40, tmp_path / "cache" / "owner_repo")

    assert calls[0][:5] == [
        "git",
        "-c",
        "core.autocrlf=false",
        "-c",
        "core.eol=lf",
    ]
    assert calls[0][5] == "clone"
    assert calls[-1][:6] == [
        "git",
        "-c",
        "core.autocrlf=false",
        "-c",
        "core.eol=lf",
        "checkout",
    ]
    assert "--force" in calls[-1]


def test_spec_loop_snapshot_declares_every_support_path() -> None:
    manifest = load_default_manifest()
    pin = next(entry for entry in manifest.vendored if entry.repo == "mattpocock/skills")
    skill_directories = {path.dest for path in pin.paths if not path.dest.endswith("/LICENSE")}
    notice_paths = {path.dest for path in pin.paths if path.dest.endswith("/LICENSE")}

    assert skill_directories == {
        "src/dev_ready/templates/claude/skills/tdd",
        "src/dev_ready/templates/claude/skills/diagnosing-bugs",
        "src/dev_ready/templates/claude/skills/code-review",
        "src/dev_ready/templates/claude/skills/grill-with-docs",
        "src/dev_ready/templates/claude/skills/grilling",
        "src/dev_ready/templates/claude/skills/domain-modeling",
        "src/dev_ready/templates/claude/skills/to-spec",
        "src/dev_ready/templates/claude/skills/to-tickets",
        "src/dev_ready/templates/claude/skills/implement",
        "src/dev_ready/templates/claude/skills/improve-codebase-architecture",
        "src/dev_ready/templates/claude/skills/codebase-design",
        "src/dev_ready/templates/claude/skills/setup-matt-pocock-skills",
    }
    assert notice_paths == {f"{directory}/LICENSE" for directory in skill_directories}


def test_superpowers_snapshot_declares_every_support_path() -> None:
    manifest = load_default_manifest()
    pin = next(entry for entry in manifest.vendored if entry.repo == "obra/superpowers")
    skill_directories = {path.dest for path in pin.paths if not path.dest.endswith("/LICENSE")}
    notice_paths = {path.dest for path in pin.paths if path.dest.endswith("/LICENSE")}

    assert skill_directories == {
        "src/dev_ready/templates/claude/skills/brainstorming",
        "src/dev_ready/templates/claude/skills/dispatching-parallel-agents",
        "src/dev_ready/templates/claude/skills/executing-plans",
        "src/dev_ready/templates/claude/skills/finishing-a-development-branch",
        "src/dev_ready/templates/claude/skills/receiving-code-review",
        "src/dev_ready/templates/claude/skills/requesting-code-review",
        "src/dev_ready/templates/claude/skills/subagent-driven-development",
        "src/dev_ready/templates/claude/skills/systematic-debugging",
        "src/dev_ready/templates/claude/skills/test-driven-development",
        "src/dev_ready/templates/claude/skills/using-git-worktrees",
        "src/dev_ready/templates/claude/skills/verification-before-completion",
        "src/dev_ready/templates/claude/skills/writing-plans",
    }
    assert notice_paths == {f"{directory}/LICENSE" for directory in skill_directories}
    assert len(pin.paths) == 24


def test_compare_executable_modes_detects_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    clone_base = tmp_path / "cache"
    repo_dir = clone_base / "owner_repo"
    (repo_dir / ".git").mkdir(parents=True)

    pin = _pin(
        "owner/repo",
        "a" * 40,
        "MIT",
        [ItemPath(src="skills/demo", dest="src/dev_ready/templates/claude/skills/demo")],
    )
    pin = replace(pin, executable=("skills/demo/run.sh", "skills/demo/missing.sh"))

    def mock_run(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        output = (
            "100755 abcdef 0\tskills/demo/run.sh\n"
            "100755 123456 0\tskills/demo/extra.sh\n"
            "100644 789012 0\tskills/demo/missing.sh\n"
        )
        return subprocess.CompletedProcess(cmd, returncode=0, stdout=output, stderr="")

    monkeypatch.setattr(subprocess, "run", mock_run)

    diffs = sync_vendored._compare_executable_modes(clone_base, [pin])
    assert (
        "owner/repo: skills/demo/missing.sh declared executable but upstream mode is not 100755"
        in diffs
    )
    assert (
        "owner/repo: skills/demo/extra.sh upstream mode is 100755 but not declared in executable"
        in diffs
    )


def test_compare_executable_modes_fails_when_clone_metadata_is_missing(
    tmp_path: Path,
) -> None:
    pin = replace(
        _pin(
            "owner/repo",
            "a" * 40,
            "MIT",
            [ItemPath(src="skills/demo", dest="src/dev_ready/templates/claude/skills/demo")],
        ),
        executable=("skills/demo/run.sh",),
    )

    diffs = sync_vendored._compare_executable_modes(tmp_path / "cache", [pin])

    assert diffs == ["owner/repo: clone metadata missing; executable modes were not checked"]


def test_compare_executable_modes_fails_when_git_mode_query_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    clone_base = tmp_path / "cache"
    (clone_base / "owner_repo" / ".git").mkdir(parents=True)
    pin = replace(
        _pin(
            "owner/repo",
            "a" * 40,
            "MIT",
            [ItemPath(src="skills/demo", dest="src/dev_ready/templates/claude/skills/demo")],
        ),
        executable=("skills/demo/run.sh",),
    )

    def failed_run(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(cmd, returncode=1, stdout="", stderr="bad index")

    monkeypatch.setattr(subprocess, "run", failed_run)

    diffs = sync_vendored._compare_executable_modes(clone_base, [pin])

    assert diffs == ["owner/repo: git ls-files failed; executable modes were not checked"]


def test_compare_executable_line_endings_rejects_carriage_returns(tmp_path: Path) -> None:
    executable = (
        tmp_path
        / "src"
        / "dev_ready"
        / "templates"
        / "claude"
        / "skills"
        / "demo"
        / "scripts"
        / "run"
    )
    executable.parent.mkdir(parents=True)
    executable.write_bytes(b"#!/usr/bin/env bash\r\necho demo\r\n")
    pin = replace(
        _pin(
            "owner/repo",
            "a" * 40,
            "MIT",
            [
                ItemPath(
                    src="skills/demo",
                    dest="src/dev_ready/templates/claude/skills/demo",
                )
            ],
        ),
        executable=("skills/demo/scripts/run",),
    )

    diffs = sync_vendored._compare_executable_line_endings(tmp_path, [pin])

    assert diffs == [
        "src/dev_ready/templates/claude/skills/demo/scripts/run: "
        "declared executable contains carriage returns"
    ]
