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

    claude_md = (target_dir / "CLAUDE.md").read_text(encoding="utf-8")
    assert "my-app" in claude_md

    mcp_config = json.loads((target_dir / ".mcp.json").read_text(encoding="utf-8"))
    assert isinstance(mcp_config, dict)

    captured = capsys.readouterr()
    assert "[1/4] Fetching base template" in captured.err
    assert "[2/4] Applying dev-ready overlay" in captured.err
    assert "[3/4] Verifying generated project" in captured.err
    assert "[4/4] Finalizing project" in captured.err
    assert "next steps" in captured.out
