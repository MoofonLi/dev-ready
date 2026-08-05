#!/usr/bin/env python3
"""Fail when upstream's root ignore file drifts from the copy dev-ready adopted.

Maintainer tooling outside src/: FR-38 made dev-ready the owner of the generated
project's root `.gitignore`, so upstream additions no longer arrive for free.
Pruning is applied as a Copier exclude at fetch time, which means upstream's file
never reaches a generated project and nothing downstream can notice the
difference — the comparison has to reach the pinned commit itself.

The check resolves the base-template pin from manifest.json, reads upstream's
root ignore file at that commit, and compares it against the upstream-derived
portion of `templates/gitignore/gitignore`. dev-ready's own two `.env` entries
are excluded from the comparison by construction, so they never fail it.

Exits 0 on match, 1 on drift.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "src"))

from dev_ready.manifest.loader import load_manifest  # noqa: E402

# The path upstream keeps its root ignore file at, and the path dev-ready keeps
# its replacement at. The replacement is dotless in the package tree — see the
# comment beside its write in `dev_ready.overlay`.
UPSTREAM_IGNORE_PATH = ".gitignore"
ADOPTED_IGNORE_PATH = Path("src", "dev_ready", "templates", "gitignore", "gitignore")

# The entries dev-ready adds on top of upstream's. Excluding them here is what
# lets the rest of the file be compared verbatim; it also means an upstream that
# adopts `.env` itself still shows up as drift, which is the correct outcome —
# the maintainer decides what to do about it.
DEV_READY_ADDITIONS: tuple[str, ...] = (".env", ".env*")


def ignore_entries(text: str) -> tuple[str, ...]:
    """Return the patterns a git implementation would act on, in file order.

    Comments and blank lines carry no matching behaviour, so they are not
    drift. A trailing carriage return is stripped for the same reason: git
    strips it too, and a CRLF checkout must not read as a changed file.
    """
    entries = []
    for raw in text.splitlines():
        line = raw.rstrip("\r")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        entries.append(line)
    return tuple(entries)


def upstream_derived_entries(adopted_text: str) -> tuple[str, ...]:
    """Return the adopted file's entries with dev-ready's own additions removed."""
    additions = set(DEV_READY_ADDITIONS)
    return tuple(entry for entry in ignore_entries(adopted_text) if entry not in additions)


def compare_ignore_files(upstream_text: str | None, adopted_text: str) -> list[str]:
    """Return one message per difference, naming what changed.

    `upstream_text` is None when the file is absent at the pinned commit. Pure
    function: no filesystem and no network.
    """
    if upstream_text is None:
        return [
            f"upstream's root {UPSTREAM_IGNORE_PATH} is missing at the pinned commit; "
            f"the adopted copy at {ADOPTED_IGNORE_PATH.as_posix()} has nothing to track"
        ]

    upstream = ignore_entries(upstream_text)
    adopted = upstream_derived_entries(adopted_text)
    if upstream == adopted:
        return []

    failures = [
        f"upstream added an entry the adopted copy lacks: {entry!r}"
        for entry in upstream
        if entry not in adopted
    ]
    failures.extend(
        f"upstream no longer carries an entry the adopted copy has: {entry!r}"
        for entry in adopted
        if entry not in upstream
    )
    if not failures:
        failures.append(
            f"upstream changed the order of its entries: {list(upstream)} "
            f"against the adopted {list(adopted)}"
        )
    return failures


def adopted_ignore_text(repo_root: Path | None = None) -> str:
    """Read the replacement dev-ready writes into every generated project."""
    root = _REPO_ROOT if repo_root is None else repo_root
    return (root / ADOPTED_IGNORE_PATH).read_text(encoding="utf-8")


def read_upstream_ignore(repo: str, commit: str, clone_dir: Path) -> str | None:
    """Clone `repo` blobless and return its root ignore file at `commit`.

    Returns None when the file does not exist at that commit — that is drift to
    report, not an error to crash on.
    """
    clone = subprocess.run(
        [
            "git",
            "clone",
            "--filter=blob:none",
            "--no-checkout",
            f"https://github.com/{repo}.git",
            str(clone_dir),
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if clone.returncode != 0:
        raise RuntimeError(f"git clone failed for {repo}: {clone.stderr}")
    shown = subprocess.run(
        ["git", "show", f"{commit}:{UPSTREAM_IGNORE_PATH}"],
        cwd=clone_dir,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if shown.returncode != 0:
        if "does not exist" in shown.stderr or "exists on disk, but not in" in shown.stderr:
            return None
        raise RuntimeError(f"git show failed for {repo} at {commit}: {shown.stderr}")
    return shown.stdout


def check_ignore_drift(repo_root: Path | None = None) -> list[str]:
    """Resolve the pin, fetch upstream's file, and return its differences."""
    root = _REPO_ROOT if repo_root is None else repo_root
    manifest = load_manifest(root / "src" / "dev_ready" / "manifest.json")
    pin = manifest.upstream["base_template"]
    with tempfile.TemporaryDirectory(prefix="dev-ready-ignore-drift-") as workspace:
        upstream_text = read_upstream_ignore(
            pin.repo, pin.commit, Path(workspace) / "upstream"
        )
    return compare_ignore_files(upstream_text, adopted_ignore_text(root))


def main() -> int:
    failures = check_ignore_drift()
    if failures:
        print("Root ignore file drift detected:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        print(
            f"Adopt or reject the change in {ADOPTED_IGNORE_PATH.as_posix()}, "
            "then re-run this check.",
            file=sys.stderr,
        )
        return 1

    print("Root ignore file check: the adopted copy matches upstream at the pinned commit")
    return 0


if __name__ == "__main__":
    sys.exit(main())
