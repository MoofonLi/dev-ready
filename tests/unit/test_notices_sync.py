"""Unit tests for scripts/check_notices_sync.py (no network; filesystem confined to tmp_path)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

_SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "check_notices_sync.py"
_spec = importlib.util.spec_from_file_location("check_notices_sync", _SCRIPT_PATH)
assert _spec is not None and _spec.loader is not None
check_notices_sync_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check_notices_sync_mod)

_CURRENT_CATALOG_JSON = """"default_set": {
    "development_loop": "sample-loop",
    "documentation": ["architecture", "requirements"],
    "enhancements": []
  },
  "categories": {"dev": {"description": "Development loop."}},
  "components": {
    "skills": {"items": [{
      "id": "sample-loop",
      "kind": "development-loop",
      "steps": ["sample-step"],
      "choose_when": ["Use `steps`.", "Follow `chain`.", "Prefer `invocation`."],
      "invocation": "user",
      "chain": ["sample-step"],
      "roles": {"build": ["sample-step"]},
      "category": "dev",
      "description": "Sample loop.",
      "mode": "builtin",
      "license": "MIT",
      "paths": [{
        "src": "claude/skills/sample-loop",
        "dest": ".agents/skills/sample-step"
      }]
    }]},
    "mcp": {"items": []},
    "docs": {"items": []}
  }"""


def _write_vendored_fixture(
    tmp_path: Path,
    *,
    repo: str,
    license_name: str,
    paths: list[dict[str, str]],
) -> tuple[Path, Path]:
    manifest_path = tmp_path / "src" / "dev_ready" / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    notices_path = tmp_path / "THIRD_PARTY_NOTICES.md"
    commit = "a" * 40
    manifest_path.write_text(
        f"""{{
  "manifest_version": 1,
  "agent_targets": {{"claude": {{"description": "Claude Code.", "skills_dir": ".claude/skills", "rules_file": "CLAUDE.md", "mcp_file": ".mcp.json"}}}},
  "upstream": {{
    "base_template": {{
      "repo": "fastapi/full-stack-fastapi-template",
      "ref": "master",
      "commit": "{commit}",
      "license": "MIT"
    }}
  }},
  "vendored": [
    {{
      "repo": "{repo}",
      "commit": "{commit}",
      "license": "{license_name}",
      "paths": {json.dumps(paths)}
    }}
  ],
  {_CURRENT_CATALOG_JSON},
  "overlay_version": "0.1.0"
}}""",
        encoding="utf-8",
    )
    notices_path.write_text(
        f"""# Notices
## {repo}
- License: {license_name}
- Pinned Commit: {commit}
""",
        encoding="utf-8",
    )
    return manifest_path, notices_path


def test_parse_notices_content_extracts_vendored_entries() -> None:
    content = """# Third-Party Notices

## fastapi/full-stack-fastapi-template
- License: MIT
- Source: https://github.com/fastapi/full-stack-fastapi-template

## owner/repo-a
- License: MIT
- Pinned Commit: 0123456789abcdef0123456789abcdef01234567

## owner/repo-b
- License: Apache-2.0
- Pinned Commit: fedcba9876543210fedcba9876543210fedcba98
"""
    result = check_notices_sync_mod.parse_notices_content(content)
    assert "owner/repo-a" in result
    assert result["owner/repo-a"] == {
        "commit": "0123456789abcdef0123456789abcdef01234567",
        "license": "MIT",
    }
    assert "owner/repo-b" in result
    assert result["owner/repo-b"] == {
        "commit": "fedcba9876543210fedcba9876543210fedcba98",
        "license": "Apache-2.0",
    }
    # Template repo with no Pinned Commit should be ignored
    assert "fastapi/full-stack-fastapi-template" not in result


def test_mattpocock_notice_names_the_complete_spec_loop_subset() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    notices = (repo_root / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")

    for skill_name in (
        "grill-with-docs",
        "grilling",
        "domain-modeling",
        "to-spec",
        "to-tickets",
        "improve-codebase-architecture",
        "codebase-design",
    ):
        assert skill_name in notices

    assert "distributed as derived works under the same MIT license" in notices
    assert "source snapshots in this repository remain byte-checked" in notices
    assert "adapt setup-command references" not in notices
    assert "project-orientation" not in notices
    assert "mounted Enhancement" not in notices
    assert "delimited block" not in notices


def test_superpowers_notice_names_the_complete_curated_subset() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    notices = (repo_root / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")

    assert "## obra/superpowers" in notices
    for skill_name in (
        "brainstorming",
        "dispatching-parallel-agents",
        "executing-plans",
        "finishing-a-development-branch",
        "receiving-code-review",
        "requesting-code-review",
        "subagent-driven-development",
        "systematic-debugging",
        "test-driven-development",
        "using-git-worktrees",
        "verification-before-completion",
        "writing-plans",
    ):
        assert skill_name in notices

    assert "using-superpowers" not in notices
    assert "writing-skills" not in notices
    assert "b36e0829c6d0140e93cfef2ca599b1b07d4a7797" in notices



def test_reference_installer_notice_records_pathless_derived_data() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    notices_path = repo_root / "THIRD_PARTY_NOTICES.md"
    notices = notices_path.read_text(encoding="utf-8")
    parsed = check_notices_sync_mod.parse_notices_content(notices)

    assert parsed["vercel-labs/skills"] == {
        "commit": "1164afa5f0e21ebd01e6fc11249759353f494ad1",
        "license": "MIT",
    }
    assert "derived data" in notices
    assert "no files are copied" in notices
    assert check_notices_sync_mod.check_notices_sync(
        repo_root / "src/dev_ready/manifest.json", notices_path, repo_root
    ) == []


def test_check_notices_sync_success_when_matching(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    notices_path = tmp_path / "THIRD_PARTY_NOTICES.md"

    commit = "a" * 40
    manifest_path.write_text(
        f"""{{
  "manifest_version": 1,
  "agent_targets": {{"claude": {{"description": "Claude Code.", "skills_dir": ".claude/skills", "rules_file": "CLAUDE.md", "mcp_file": ".mcp.json"}}}},
  "upstream": {{
    "base_template": {{
      "repo": "fastapi/full-stack-fastapi-template",
      "ref": "master",
      "commit": "{commit}",
      "license": "MIT"
    }}
  }},
  "vendored": [
    {{
      "repo": "owner/repo-a",
      "commit": "{commit}",
      "license": "MIT",
      "paths": []
    }}
  ],
  {_CURRENT_CATALOG_JSON},
  "overlay_version": "0.1.0"
}}""",
        encoding="utf-8",
    )

    notices_path.write_text(
        f"""# Notices
## owner/repo-a
- License: MIT
- Pinned Commit: {commit}
""",
        encoding="utf-8",
    )

    diffs = check_notices_sync_mod.check_notices_sync(manifest_path, notices_path)
    assert diffs == []


def test_check_notices_sync_detects_missing_in_notices(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    notices_path = tmp_path / "THIRD_PARTY_NOTICES.md"

    commit = "a" * 40
    manifest_path.write_text(
        f"""{{
  "manifest_version": 1,
  "agent_targets": {{"claude": {{"description": "Claude Code.", "skills_dir": ".claude/skills", "rules_file": "CLAUDE.md", "mcp_file": ".mcp.json"}}}},
  "upstream": {{
    "base_template": {{
      "repo": "fastapi/full-stack-fastapi-template",
      "ref": "master",
      "commit": "{commit}",
      "license": "MIT"
    }}
  }},
  "vendored": [
    {{
      "repo": "owner/repo-a",
      "commit": "{commit}",
      "license": "MIT",
      "paths": []
    }}
  ],
  {_CURRENT_CATALOG_JSON},
  "overlay_version": "0.1.0"
}}""",
        encoding="utf-8",
    )

    notices_path.write_text("# Notices\n", encoding="utf-8")

    diffs = check_notices_sync_mod.check_notices_sync(manifest_path, notices_path)
    assert len(diffs) == 1
    assert "owner/repo-a is in manifest.json vendored but missing" in diffs[0]


def test_check_notices_sync_detects_missing_in_manifest(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    notices_path = tmp_path / "THIRD_PARTY_NOTICES.md"

    commit = "a" * 40
    manifest_path.write_text(
        f"""{{
  "manifest_version": 1,
  "agent_targets": {{"claude": {{"description": "Claude Code.", "skills_dir": ".claude/skills", "rules_file": "CLAUDE.md", "mcp_file": ".mcp.json"}}}},
  "upstream": {{
    "base_template": {{
      "repo": "fastapi/full-stack-fastapi-template",
      "ref": "master",
      "commit": "{commit}",
      "license": "MIT"
    }}
  }},
  "vendored": [],
  {_CURRENT_CATALOG_JSON},
  "overlay_version": "0.1.0"
}}""",
        encoding="utf-8",
    )

    notices_path.write_text(
        f"""# Notices
## owner/unwanted-repo
- License: MIT
- Pinned Commit: {commit}
""",
        encoding="utf-8",
    )

    diffs = check_notices_sync_mod.check_notices_sync(manifest_path, notices_path)
    assert len(diffs) == 1
    assert "owner/unwanted-repo is in THIRD_PARTY_NOTICES.md but missing" in diffs[0]


def test_check_notices_sync_detects_commit_or_license_mismatch(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    notices_path = tmp_path / "THIRD_PARTY_NOTICES.md"

    commit = "a" * 40
    wrong_commit = "b" * 40
    manifest_path.write_text(
        f"""{{
  "manifest_version": 1,
  "agent_targets": {{"claude": {{"description": "Claude Code.", "skills_dir": ".claude/skills", "rules_file": "CLAUDE.md", "mcp_file": ".mcp.json"}}}},
  "upstream": {{
    "base_template": {{
      "repo": "fastapi/full-stack-fastapi-template",
      "ref": "master",
      "commit": "{commit}",
      "license": "MIT"
    }}
  }},
  "vendored": [
    {{
      "repo": "owner/repo-a",
      "commit": "{commit}",
      "license": "MIT",
      "paths": []
    }}
  ],
  {_CURRENT_CATALOG_JSON},
  "overlay_version": "0.1.0"
}}""",
        encoding="utf-8",
    )

    notices_path.write_text(
        f"""# Notices
## owner/repo-a
- License: MIT
- Pinned Commit: {wrong_commit}
""",
        encoding="utf-8",
    )

    diffs = check_notices_sync_mod.check_notices_sync(manifest_path, notices_path)
    assert len(diffs) == 1
    assert "commit mismatch" in diffs[0]


def test_check_notices_sync_apache_license_presence(tmp_path: Path) -> None:
    dest_dir = "src/dev_ready/templates/claude/skills/apache-skill"
    (tmp_path / dest_dir).mkdir(parents=True)
    (tmp_path / dest_dir / "LICENSE.txt").write_text("Apache License 2.0", encoding="utf-8")
    manifest_path, notices_path = _write_vendored_fixture(
        tmp_path,
        repo="owner/apache-repo",
        license_name="Apache-2.0",
        paths=[{"src": "skills/apache-skill", "dest": dest_dir}],
    )

    diffs = check_notices_sync_mod.check_notices_sync(manifest_path, notices_path, repo_root=tmp_path)
    assert diffs == []


def test_check_notices_sync_apache_license_missing_fails(tmp_path: Path) -> None:
    dest_dir = "src/dev_ready/templates/claude/skills/apache-skill"
    (tmp_path / dest_dir).mkdir(parents=True)
    manifest_path, notices_path = _write_vendored_fixture(
        tmp_path,
        repo="owner/apache-repo",
        license_name="Apache-2.0",
        paths=[{"src": "skills/apache-skill", "dest": dest_dir}],
    )

    diffs = check_notices_sync_mod.check_notices_sync(manifest_path, notices_path, repo_root=tmp_path)
    assert len(diffs) == 1
    assert "has no notice file in its snapshot" in diffs[0]


def test_check_notices_sync_mit_without_notice_fails(tmp_path: Path) -> None:
    dest_dir = "src/dev_ready/templates/claude/skills/mit-skill"
    (tmp_path / dest_dir).mkdir(parents=True)
    manifest_path, notices_path = _write_vendored_fixture(
        tmp_path,
        repo="owner/mit-repo",
        license_name="MIT",
        paths=[{"src": "skills/mit-skill", "dest": dest_dir}],
    )

    diffs = check_notices_sync_mod.check_notices_sync(
        manifest_path, notices_path, repo_root=tmp_path
    )
    assert len(diffs) == 1
    assert "owner/mit-repo" in diffs[0]
    assert "has no notice file" in diffs[0]


def test_loose_file_source_is_checked_once_per_repository(tmp_path: Path) -> None:
    docs_dir = tmp_path / "src" / "dev_ready" / "templates" / "docs"
    docs_dir.mkdir(parents=True)
    for name in ("design-a.md", "design-b.md", "design-source-LICENSE.md"):
        (docs_dir / name).write_text(name, encoding="utf-8")
    manifest_path, notices_path = _write_vendored_fixture(
        tmp_path,
        repo="owner/design-source",
        license_name="MIT",
        paths=[
            {
                "src": "design/a.md",
                "dest": "src/dev_ready/templates/docs/design-a.md",
            },
            {
                "src": "design/b.md",
                "dest": "src/dev_ready/templates/docs/design-b.md",
            },
            {
                "src": "LICENSE",
                "dest": "src/dev_ready/templates/docs/design-source-LICENSE.md",
            },
        ],
    )

    assert check_notices_sync_mod.check_notices_sync(
        manifest_path, notices_path, repo_root=tmp_path
    ) == []


def test_attribution_only_entry_is_recognized(tmp_path: Path) -> None:
    """An adapted-rewrite (attribution-only) NOTICES entry is NOT an orphan."""
    manifest_path = tmp_path / "manifest.json"
    notices_path = tmp_path / "THIRD_PARTY_NOTICES.md"
    commit = "2c606141936f1eeef17fa3043a72095b4765b9c2"
    manifest_path.write_text(
        f"""{{
  "manifest_version": 1,
  "agent_targets": {{"claude": {{"description": "Claude Code.", "skills_dir": ".claude/skills", "rules_file": "CLAUDE.md", "mcp_file": ".mcp.json"}}}},
  "upstream": {{"base_template": {{"repo": "fastapi/full-stack-fastapi-template", "ref": "master", "commit": "{'a' * 40}", "license": "MIT"}}}},
  "vendored": [],
  {_CURRENT_CATALOG_JSON},
  "overlay_version": "0.1.0"
}}""",
        encoding="utf-8",
    )
    notices_path.write_text(
        f"""# Notices
## multica-ai/andrej-karpathy-skills
- License: MIT, per README at {commit}
- Pinned Commit: {commit}
- Integration: adapted-rewrite — attribution only; NOT vendored
""",
        encoding="utf-8",
    )
    diffs = check_notices_sync_mod.check_notices_sync(manifest_path, notices_path)
    assert diffs == []


def test_attribution_only_without_marker_is_orphan(tmp_path: Path) -> None:
    """Drop the Integration marker and the same entry is flagged as an orphan again."""
    manifest_path = tmp_path / "manifest.json"
    notices_path = tmp_path / "THIRD_PARTY_NOTICES.md"
    commit = "2c606141936f1eeef17fa3043a72095b4765b9c2"
    manifest_path.write_text(
        f"""{{
  "manifest_version": 1,
  "agent_targets": {{"claude": {{"description": "Claude Code.", "skills_dir": ".claude/skills", "rules_file": "CLAUDE.md", "mcp_file": ".mcp.json"}}}},
  "upstream": {{"base_template": {{"repo": "fastapi/full-stack-fastapi-template", "ref": "master", "commit": "{'a' * 40}", "license": "MIT"}}}},
  "vendored": [],
  {_CURRENT_CATALOG_JSON},
  "overlay_version": "0.1.0"
}}""",
        encoding="utf-8",
    )
    notices_path.write_text(
        f"""# Notices
## multica-ai/andrej-karpathy-skills
- License: MIT, per README at {commit}
- Pinned Commit: {commit}
""",
        encoding="utf-8",
    )
    diffs = check_notices_sync_mod.check_notices_sync(manifest_path, notices_path)
    assert len(diffs) == 1
    assert "missing from manifest.json vendored" in diffs[0]


def test_parse_marks_only_attribution_only_sections(tmp_path: Path) -> None:
    """The attribution_only key is added ONLY to marked sections, never to normal ones."""
    content = """# Notices
## owner/vendored-repo
- License: MIT
- Pinned Commit: 0123456789abcdef0123456789abcdef01234567

## multica-ai/andrej-karpathy-skills
- License: MIT, per README at 2c606141936f1eeef17fa3043a72095b4765b9c2
- Pinned Commit: 2c606141936f1eeef17fa3043a72095b4765b9c2
- Integration: adapted-rewrite — attribution only
"""
    result = check_notices_sync_mod.parse_notices_content(content)
    assert "attribution_only" not in result["owner/vendored-repo"]
    assert result["multica-ai/andrej-karpathy-skills"].get("attribution_only") == "true"
