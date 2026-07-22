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
