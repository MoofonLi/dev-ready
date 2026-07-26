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
    canonical_skill = target_dir / ".agents/skills/project-orientation/SKILL.md"
    claude_stub = target_dir / ".claude/skills/project-orientation/SKILL.md"
    windsurf_stub = target_dir / ".windsurf/skills/project-orientation/SKILL.md"
    assert canonical_skill.is_file()
    assert claude_stub.is_file()
    assert windsurf_stub.is_file()
    assert canonical_skill.read_bytes() != claude_stub.read_bytes()
    assert canonical_skill.read_bytes() != windsurf_stub.read_bytes()
    assert not canonical_skill.is_symlink()
    assert not claude_stub.is_symlink()
    assert not windsurf_stub.is_symlink()

    mcp_config = json.loads((target_dir / ".mcp.json").read_text(encoding="utf-8"))
    assert isinstance(mcp_config, dict)

    captured = capsys.readouterr()
    assert "[1/4] Fetching base template" in captured.err
    assert "[2/4] Applying dev-ready overlay" in captured.err
    assert "[3/4] Verifying generated project" in captured.err
    assert "[4/4] Finalizing project" in captured.err
    assert "next steps" in captured.out
