#!/usr/bin/env python3
"""Resolve the latest upstream commit and update the manifest pin.

CI-only maintainer tooling: not part of the dev-ready wheel, and not
subject to the src/dev_ready `fetch/`-only network-call rule (see
docs/architecture.md, Dependency Rules). stdlib only (urllib, json) so it
needs nothing beyond a bare Python interpreter to run in CI.

Verification of the bumped pin is not done here: `upstream-bump.yml` opens
a PR, and ci.yml's `generate-and-verify` job is the gate (ADR-002).
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

_COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")
_REQUEST_TIMEOUT = 30.0
_SHORT_LENGTH = 12

_MANIFEST_PATH = Path(__file__).resolve().parent.parent / "src" / "dev_ready" / "manifest.json"


def resolve_latest_commit(repo: str, ref: str) -> str:
    """Resolve `ref` on `repo` to a full commit sha via the GitHub API.

    Unauthenticated: public repo, weekly cadence is far under rate limits.
    Raises `RuntimeError` if the response is not a valid 40-char hex sha.
    """
    url = f"https://api.github.com/repos/{repo}/commits/{ref}"
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "dev-ready-bump-script",
            "Accept": "application/vnd.github+json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=_REQUEST_TIMEOUT) as response:  # noqa: S310
            payload = json.load(response)
    except urllib.error.HTTPError as error:
        raise RuntimeError(f"GitHub API request failed with HTTP {error.code}: {url}") from error
    except (urllib.error.URLError, OSError) as error:
        raise RuntimeError(f"GitHub API request failed ({url}): {error}") from error

    sha = payload.get("sha") if isinstance(payload, dict) else None
    if not isinstance(sha, str) or not _COMMIT_PATTERN.fullmatch(sha):
        raise RuntimeError(f"unexpected commit sha from GitHub API: {sha!r}")
    return sha


def update_manifest(manifest_path: Path, commit: str, verified_at: str) -> bool:
    """Rewrite the `base_template` pin in `manifest_path`.

    Preserves all other manifest structure and formatting
    (`json.dump(..., indent=2)` plus a trailing newline). Returns False
    without writing when the pin is already at `commit`.
    """
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    pin = data["upstream"]["base_template"]
    if pin["commit"] == commit:
        return False

    pin["commit"] = commit
    pin["verified_at"] = verified_at
    manifest_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return True


def _write_github_output(*, changed: bool, old_commit: str, new_commit: str) -> None:
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        return
    with open(output_path, "a", encoding="utf-8") as handle:
        handle.write(f"changed={'true' if changed else 'false'}\n")
        handle.write(f"old_commit={old_commit}\n")
        handle.write(f"new_commit={new_commit}\n")
        handle.write(f"old_commit_short={old_commit[:_SHORT_LENGTH]}\n")
        handle.write(f"new_commit_short={new_commit[:_SHORT_LENGTH]}\n")


def main() -> int:
    manifest_data = json.loads(_MANIFEST_PATH.read_text(encoding="utf-8"))
    pin = manifest_data["upstream"]["base_template"]
    old_commit = pin["commit"]
    if not _COMMIT_PATTERN.fullmatch(old_commit):
        raise RuntimeError(f"manifest.json has an invalid existing commit: {old_commit!r}")

    new_commit = resolve_latest_commit(pin["repo"], pin["ref"])
    verified_at = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    changed = update_manifest(_MANIFEST_PATH, new_commit, verified_at)
    _write_github_output(
        changed=changed,
        old_commit=old_commit,
        new_commit=new_commit if changed else old_commit,
    )

    if not changed:
        print("unchanged")
        return 0

    print(f"updated {old_commit[:_SHORT_LENGTH]} -> {new_commit[:_SHORT_LENGTH]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
