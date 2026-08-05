"""End-to-end test: one real `init` run against the manifest-pinned upstream commit."""

import json
from pathlib import Path

import pytest

from dev_ready.cli import main

pytestmark = pytest.mark.network


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
    claude_stub = target_dir / ".claude/skills/implement/SKILL.md"
    assert canonical_skill.is_file()
    assert claude_stub.is_file()
    assert canonical_skill.read_bytes() != claude_stub.read_bytes()
    assert not canonical_skill.is_symlink()
    assert not claude_stub.is_symlink()
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
    assert stamp["development_loop"] == "spec-loop"

    captured = capsys.readouterr()
    assert "[1/4] Fetching base template" in captured.err
    assert "[2/4] Applying dev-ready overlay" in captured.err
    assert "[3/4] Verifying generated project" in captured.err
    assert "[4/4] Finalizing project" in captured.err
    assert "next steps" in captured.out
