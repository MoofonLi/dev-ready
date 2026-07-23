"""Unit tests for scripts/check_notices_sync.py (no network; filesystem confined to tmp_path)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

_SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "check_notices_sync.py"
_spec = importlib.util.spec_from_file_location("check_notices_sync", _SCRIPT_PATH)
assert _spec is not None and _spec.loader is not None
check_notices_sync_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check_notices_sync_mod)


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


def test_check_notices_sync_success_when_matching(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    notices_path = tmp_path / "THIRD_PARTY_NOTICES.md"

    commit = "a" * 40
    manifest_path.write_text(
        f"""{{
  "manifest_version": 1,
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
  "components": {{"skills": {{"items": []}}, "mcp": {{"items": []}}}},
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
  "components": {{"skills": {{"items": []}}, "mcp": {{"items": []}}}},
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
  "upstream": {{
    "base_template": {{
      "repo": "fastapi/full-stack-fastapi-template",
      "ref": "master",
      "commit": "{commit}",
      "license": "MIT"
    }}
  }},
  "vendored": [],
  "components": {{"skills": {{"items": []}}, "mcp": {{"items": []}}}},
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
  "components": {{"skills": {{"items": []}}, "mcp": {{"items": []}}}},
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
    manifest_path = tmp_path / "src" / "dev_ready" / "manifest.json"
    manifest_path.parent.mkdir(parents=True)
    notices_path = tmp_path / "THIRD_PARTY_NOTICES.md"

    commit = "a" * 40
    dest_dir = "src/dev_ready/templates/claude/skills/apache-skill"
    (tmp_path / dest_dir).mkdir(parents=True)
    (tmp_path / dest_dir / "LICENSE.txt").write_text("Apache License 2.0", encoding="utf-8")

    manifest_path.write_text(
        f"""{{
  "manifest_version": 1,
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
      "repo": "owner/apache-repo",
      "commit": "{commit}",
      "license": "Apache-2.0",
      "paths": [
        {{
          "src": "skills/apache-skill",
          "dest": "{dest_dir}"
        }}
      ]
    }}
  ],
  "components": {{"skills": {{"items": []}}, "mcp": {{"items": []}}}},
  "overlay_version": "0.1.0"
}}""",
        encoding="utf-8",
    )

    notices_path.write_text(
        f"""# Notices
## owner/apache-repo
- License: Apache-2.0
- Pinned Commit: {commit}
""",
        encoding="utf-8",
    )

    diffs = check_notices_sync_mod.check_notices_sync(manifest_path, notices_path, repo_root=tmp_path)
    assert diffs == []


def test_check_notices_sync_apache_license_missing_fails(tmp_path: Path) -> None:
    manifest_path = tmp_path / "src" / "dev_ready" / "manifest.json"
    manifest_path.parent.mkdir(parents=True)
    notices_path = tmp_path / "THIRD_PARTY_NOTICES.md"

    commit = "a" * 40
    dest_dir = "src/dev_ready/templates/claude/skills/apache-skill"
    (tmp_path / dest_dir).mkdir(parents=True)
    # Intentionally omit LICENSE.txt

    manifest_path.write_text(
        f"""{{
  "manifest_version": 1,
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
      "repo": "owner/apache-repo",
      "commit": "{commit}",
      "license": "Apache-2.0",
      "paths": [
        {{
          "src": "skills/apache-skill",
          "dest": "{dest_dir}"
        }}
      ]
    }}
  ],
  "components": {{"skills": {{"items": []}}, "mcp": {{"items": []}}}},
  "overlay_version": "0.1.0"
}}""",
        encoding="utf-8",
    )

    notices_path.write_text(
        f"""# Notices
## owner/apache-repo
- License: Apache-2.0
- Pinned Commit: {commit}
""",
        encoding="utf-8",
    )

    diffs = check_notices_sync_mod.check_notices_sync(manifest_path, notices_path, repo_root=tmp_path)
    assert len(diffs) == 1
    assert "has no LICENSE file in its snapshot" in diffs[0]


def test_check_notices_sync_mit_without_license_does_not_fail(tmp_path: Path) -> None:
    manifest_path = tmp_path / "src" / "dev_ready" / "manifest.json"
    manifest_path.parent.mkdir(parents=True)
    notices_path = tmp_path / "THIRD_PARTY_NOTICES.md"

    commit = "a" * 40
    dest_dir = "src/dev_ready/templates/claude/skills/mit-skill"
    (tmp_path / dest_dir).mkdir(parents=True)
    # No LICENSE file in MIT dest dir

    manifest_path.write_text(
        f"""{{
  "manifest_version": 1,
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
      "repo": "owner/mit-repo",
      "commit": "{commit}",
      "license": "MIT",
      "paths": [
        {{
          "src": "skills/mit-skill",
          "dest": "{dest_dir}"
        }}
      ]
    }}
  ],
  "components": {{"skills": {{"items": []}}, "mcp": {{"items": []}}}},
  "overlay_version": "0.1.0"
}}""",
        encoding="utf-8",
    )

    notices_path.write_text(
        f"""# Notices
## owner/mit-repo
- License: MIT
- Pinned Commit: {commit}
""",
        encoding="utf-8",
    )

    diffs = check_notices_sync_mod.check_notices_sync(manifest_path, notices_path, repo_root=tmp_path)
    assert diffs == []


def test_attribution_only_entry_is_recognized(tmp_path: Path) -> None:
    """An adapted-rewrite (attribution-only) NOTICES entry is NOT an orphan."""
    manifest_path = tmp_path / "manifest.json"
    notices_path = tmp_path / "THIRD_PARTY_NOTICES.md"
    commit = "2c606141936f1eeef17fa3043a72095b4765b9c2"
    manifest_path.write_text(
        f"""{{
  "manifest_version": 1,
  "upstream": {{"base_template": {{"repo": "fastapi/full-stack-fastapi-template", "ref": "master", "commit": "{'a' * 40}", "license": "MIT"}}}},
  "vendored": [],
  "components": {{"skills": {{"items": []}}, "mcp": {{"items": []}}}},
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
  "upstream": {{"base_template": {{"repo": "fastapi/full-stack-fastapi-template", "ref": "master", "commit": "{'a' * 40}", "license": "MIT"}}}},
  "vendored": [],
  "components": {{"skills": {{"items": []}}, "mcp": {{"items": []}}}},
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

