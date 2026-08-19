"""End-to-end test: one real `init` run against the manifest-pinned upstream commit."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from dev_ready.cli import main

pytestmark = pytest.mark.network
_WINDOWS = sys.platform == "win32"


def _assert_native_skill_link(link: Path, canonical_dir: Path) -> None:
    if _WINDOWS:
        assert link.is_junction(), f"{link} is not a Windows junction"
        assert not link.is_symlink()
        stored = os.readlink(link).removeprefix("\\\\?\\")
        assert Path(stored).resolve() == canonical_dir.resolve()
    else:
        assert link.is_symlink(), f"{link} is not a POSIX symbolic link"
        assert not link.is_junction()
        assert os.readlink(link) == os.path.relpath(canonical_dir, start=link.parent)
    assert link.resolve() == canonical_dir.resolve()
    assert (canonical_dir / "SKILL.md").is_file()
    assert not canonical_dir.is_symlink()
    assert not canonical_dir.is_junction()


def test_init_real_end_to_end(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    target_dir = tmp_path / "my-app"

    exit_code = main(["init", "my-app", "--yes", "--dir", str(target_dir)])

    assert exit_code == 0
    assert (target_dir / "README.md").exists()
    assert (target_dir / "backend").is_dir()

    agents_md = (target_dir / "AGENTS.md").read_text(encoding="utf-8")
    assert "my-app" in agents_md
    assert (target_dir / "CLAUDE.md").read_text(encoding="utf-8") == "@AGENTS.md\n"
    canonical_skill = target_dir / ".agents/skills/implement/SKILL.md"
    claude_link = target_dir / ".claude/skills/implement"
    assert canonical_skill.is_file()
    _assert_native_skill_link(claude_link, canonical_skill.parent)
    assert (target_dir / ".claude/skills/.gitignore").is_file()
    # FR-33 changed the `--yes` Agent Target default from every declared target
    # to `claude` alone: at 57 targets the old default wrote 684 Pointer Stub
    # files. An unselected target gets no directory at all. A second target's
    # own-path projection is covered by the N-1 gate, which selects one by name.
    assert not (target_dir / ".windsurf").exists()

    assert (target_dir / "docs/architecture.md").is_file()
    assert (target_dir / "docs/requirements.md").is_file()
    assert not (target_dir / ".agents/skills/caveman").exists()
    assert not (target_dir / ".mcp.json").exists()
    stamp = json.loads((target_dir / ".dev-ready.json").read_text(encoding="utf-8"))
    assert stamp["development_loop"] == "mattpocock"
    assert not any(
        str(entry["path"]).endswith("/SKILL.md")
        and str(entry["path"]).startswith(".claude/")
        for entry in stamp.get("inventory", [])
    )

    captured = capsys.readouterr()
    assert "[1/4] Fetching base template" in captured.err
    assert "[2/4] Applying dev-ready overlay" in captured.err
    assert "[3/4] Verifying generated project" in captured.err
    assert "[4/4] Finalizing project" in captured.err
    assert "[5/4]" not in captured.err
    assert "\x1b" not in captured.err
    assert "\r" not in captured.err
    assert "next steps" in captured.out
    git = shutil.which("git")
    if git is not None:
        subprocess.run(
            [git, "init"],
            cwd=target_dir,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            [git, "add", "-A"],
            cwd=target_dir,
            check=True,
            capture_output=True,
        )
        listed = subprocess.run(
            [git, "diff", "--cached", "--name-only"],
            cwd=target_dir,
            check=True,
            capture_output=True,
            text=True,
        )
        staged = {
            line.replace("\\", "/")
            for line in listed.stdout.splitlines()
            if line.strip()
        }
        implement_copies = [
            path for path in staged if path.endswith("implement/SKILL.md")
        ]
        assert implement_copies == [".agents/skills/implement/SKILL.md"]
        assert ".claude/skills/.gitignore" in staged
        assert ".claude/skills/implement/SKILL.md" not in staged
        assert not any(
            path.startswith(".claude/skills/implement/") for path in staged
        )


@pytest.mark.skipif(not _WINDOWS, reason="junctions store absolute paths")
def test_moved_windows_project_is_repaired_by_one_upgrade(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    original = tmp_path / "original"
    assert main(["init", "original", "--yes", "--dir", str(original)]) == 0
    capsys.readouterr()
    moved = tmp_path / "moved"
    original.rename(moved)
    link = moved / ".claude" / "skills" / "implement"
    canonical = moved / ".agents" / "skills" / "implement"

    assert main(["check", str(moved)]) == 7
    assert main(["upgrade", str(moved)]) == 0
    assert main(["check", str(moved)]) == 0
    assert main(["upgrade", str(moved)]) == 0
    _assert_native_skill_link(link, canonical)
