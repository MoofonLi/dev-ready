#!/usr/bin/env python3
"""Check bidirectional synchronization between manifest.json and THIRD_PARTY_NOTICES.md.

Maintainer tooling outside src/: reads manifest.json and THIRD_PARTY_NOTICES.md,
verifying that:
1. Every manifest `vendored` entry is listed in THIRD_PARTY_NOTICES.md (with matching repo, commit, and license).
2. Every vendored repo listed in THIRD_PARTY_NOTICES.md is declared in manifest `vendored`.
Exits 0 on match, 1 on mismatch.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "src"))

from dev_ready.manifest.loader import load_manifest  # noqa: E402

_SECTION_PATTERN = re.compile(r"^##\s+([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)", re.MULTILINE)
_COMMIT_PATTERN = re.compile(r"^\s*-\s*Pinned Commit:\s*([a-fA-F0-9]{40})", re.MULTILINE)
_LICENSE_PATTERN = re.compile(r"^\s*-\s*License:\s*([^\r\n]+)", re.MULTILINE)
_ATTRIBUTION_ONLY_PATTERN = re.compile(
    r"^\s*-\s*Integration:\s*adapted", re.IGNORECASE | re.MULTILINE
)


def parse_notices_content(content: str) -> dict[str, dict[str, str]]:
    """Parse THIRD_PARTY_NOTICES.md content into a repo -> {commit, license} dict.

    Ignores non-vendored sections (e.g. template downloads without pinned commit).
    Pure function: no filesystem/network side effects.
    """
    results: dict[str, dict[str, str]] = {}
    sections = re.split(r"(?=^##\s+)", content, flags=re.MULTILINE)

    for section in sections:
        sec_match = _SECTION_PATTERN.search(section)
        if not sec_match:
            continue
        repo = sec_match.group(1)
        # Skip template section if it has no Pinned Commit
        commit_match = _COMMIT_PATTERN.search(section)
        if not commit_match:
            continue
        commit = commit_match.group(1).lower()

        license_match = _LICENSE_PATTERN.search(section)
        license_str = license_match.group(1).strip() if license_match else ""

        entry = {"commit": commit, "license": license_str}
        if _ATTRIBUTION_ONLY_PATTERN.search(section):
            entry["attribution_only"] = "true"
        results[repo] = entry

    return results


def check_notices_sync(
    manifest_path: Path, notices_path: Path, repo_root: Path | None = None
) -> list[str]:
    """Return a list of drift error messages between manifest and NOTICES file."""
    if not manifest_path.exists():
        return [f"manifest file missing: {manifest_path}"]
    if not notices_path.exists():
        return [f"NOTICES file missing: {notices_path}"]

    if repo_root is None:
        repo_root = manifest_path.resolve().parents[2]

    manifest = load_manifest(manifest_path)
    manifest_map = {
        entry.repo: {"commit": entry.commit.lower(), "license": entry.license}
        for entry in manifest.vendored
    }

    notices_text = notices_path.read_text(encoding="utf-8")
    notices_map = parse_notices_content(notices_text)

    diffs: list[str] = []

    # Check direction 1: manifest -> NOTICES & Apache LICENSE presence
    for entry in manifest.vendored:
        repo = entry.repo
        info = {"commit": entry.commit.lower(), "license": entry.license}
        if repo not in notices_map:
            diffs.append(f"NOTICES mismatch: {repo} is in manifest.json vendored but missing from THIRD_PARTY_NOTICES.md")
        else:
            notice_info = notices_map[repo]
            if notice_info["commit"] != info["commit"]:
                diffs.append(
                    f"NOTICES mismatch: {repo} commit mismatch (manifest: {info['commit']}, NOTICES: {notice_info['commit']})"
                )
            if notice_info["license"] != info["license"]:
                diffs.append(
                    f"NOTICES mismatch: {repo} license mismatch (manifest: {info['license']}, NOTICES: {notice_info['license']})"
                )

        if entry.license == "Apache-2.0":
            for path_map in entry.paths:
                committed = repo_root / path_map.dest
                has_license = False
                if committed.is_dir():
                    for file_path in committed.rglob("*"):
                        if file_path.is_file() and file_path.name.lower().startswith("license"):
                            has_license = True
                            break
                elif committed.is_file() and committed.name.lower().startswith("license"):
                    has_license = True

                if not has_license:
                    diffs.append(
                        f"NOTICES mismatch: Apache-2.0 entry {repo} path '{path_map.dest}' has no LICENSE file in its snapshot"
                    )

    # Check direction 2: NOTICES -> manifest
    for repo, info in notices_map.items():
        if info.get("attribution_only"):
            continue
        if repo not in manifest_map:
            diffs.append(f"NOTICES mismatch: {repo} is in THIRD_PARTY_NOTICES.md but missing from manifest.json vendored")

    return sorted(diffs)


def main() -> int:
    manifest_path = _REPO_ROOT / "src" / "dev_ready" / "manifest.json"
    notices_path = _REPO_ROOT / "THIRD_PARTY_NOTICES.md"

    diffs = check_notices_sync(manifest_path, notices_path)
    if diffs:
        for err in diffs:
            print(f"NOTICES SYNC ERROR: {err}", file=sys.stderr)
        return 1

    print("NOTICES sync check: THIRD_PARTY_NOTICES.md matches manifest.json vendored list")
    return 0


if __name__ == "__main__":
    sys.exit(main())
