#!/usr/bin/env python3
"""Sync vendored external repos to local snapshots under templates/.

Maintainer tooling outside src/: reads manifest.json via the validating
dev_ready loader, clones or fetches pinned vendored repositories, and
materializes declared file snapshots into templates/.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "src"))

from dev_ready.errors import ManifestError  # noqa: E402
from dev_ready.manifest.loader import load_manifest  # noqa: E402
from dev_ready.manifest.models import VendoredPin  # noqa: E402


def build_path_mappings(
    vendored: tuple[VendoredPin, ...] | list[VendoredPin],
    repo_root: Path,
) -> list[tuple[str, Path]]:
    """Return a list of (src_in_repo, abs_dest_path) pairs for all vendored entries.

    `vendored` is the validated pin list from the manifest loader. `repo_root`
    is the absolute path to the repository root; manifest `dest` paths are
    relative to it (e.g. "templates/claude/skills/x/SKILL.md"). Every resolved
    dest must stay inside `<repo_root>/templates`.

    Pure function: no network, no filesystem reads/writes.
    """
    templates_root = (repo_root / "src" / "dev_ready" / "templates").resolve()
    mappings: list[tuple[str, Path]] = []
    for entry in vendored:
        for path_pair in entry.paths:
            dest = repo_root / path_pair.dest
            if not dest.resolve().is_relative_to(templates_root):
                raise RuntimeError(f"destination path escapes templates root: {dest}")
            mappings.append((path_pair.src, dest))
    return mappings


def copy_snapshot(
    clone_dir: Path,
    mappings: list[tuple[str, Path]],
) -> None:
    """Copy files from a cloned repo directory to their dest paths.

    `clone_dir` is the local path of the cloned repo. For each (src, dest) pair,
    copies `clone_dir / src` to `dest`, creating parent directories as needed.
    Raises `RuntimeError` if a source path resolves outside the clone or does
    not exist inside it.
    """
    clone_root = clone_dir.resolve()
    for src, dest in mappings:
        src_path = clone_dir / src
        if not src_path.resolve().is_relative_to(clone_root):
            raise RuntimeError(f"source path escapes clone directory: {src_path}")
        if not src_path.exists():
            raise RuntimeError(f"source path does not exist in cloned repo: {src_path}")
        dest.parent.mkdir(parents=True, exist_ok=True)
        if src_path.is_dir():
            shutil.copytree(src_path, dest, dirs_exist_ok=True)
        else:
            shutil.copy2(src_path, dest)


def clone_or_fetch(repo: str, commit: str, target_dir: Path) -> None:
    """Clone `repo` (GitHub HTTPS) into `target_dir` and check out `commit`.

    Uses `git clone --filter=blob:none --no-checkout` + `git checkout <commit>`.
    If `target_dir` already exists and contains a valid git repo, fetch instead
    of re-cloning. Raises `RuntimeError` on non-zero git exit codes.
    """
    url = f"https://github.com/{repo}.git"
    if (target_dir / ".git").is_dir():
        res = subprocess.run(
            ["git", "fetch", "--depth=1", "origin", commit],
            cwd=target_dir,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if res.returncode != 0:
            res = subprocess.run(
                ["git", "fetch", "origin"],
                cwd=target_dir,
                capture_output=True,
                text=True,
                timeout=60,
            )
            if res.returncode != 0:
                raise RuntimeError(f"git fetch failed for {repo}: {res.stderr}")
    else:
        target_dir.parent.mkdir(parents=True, exist_ok=True)
        res = subprocess.run(
            [
                "git",
                "-c",
                "core.autocrlf=false",
                "-c",
                "core.eol=lf",
                "clone",
                "--filter=blob:none",
                "--no-checkout",
                url,
                str(target_dir),
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if res.returncode != 0:
            raise RuntimeError(f"git clone failed for {repo}: {res.stderr}")

    res = subprocess.run(
        [
            "git",
            "-c",
            "core.autocrlf=false",
            "-c",
            "core.eol=lf",
            "checkout",
            "--force",
            commit,
        ],
        cwd=target_dir,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if res.returncode != 0:
        raise RuntimeError(f"git checkout failed for {repo} at commit {commit}: {res.stderr}")


def sync_all(
    manifest_path: Path,
    repo_root: Path,
    clone_base: Path,
) -> int:
    """Main sync logic: load validated manifest, clone/fetch, copy snapshots.

    Returns the number of vendored entries processed (0 for empty list).
    Prints progress to stdout. Raises `RuntimeError` / `ManifestError` on failure.
    """
    manifest = load_manifest(manifest_path)
    vendored = manifest.vendored
    if not vendored:
        print("vendored: nothing to sync")
        return 0

    count = 0
    for entry in entries_requiring_sync(vendored):
        target_dir = clone_base / entry.repo.replace("/", "_")
        print(f"syncing {entry.repo} @ {entry.commit[:12]}...")
        clone_or_fetch(entry.repo, entry.commit, target_dir)
        mappings = build_path_mappings([entry], repo_root)
        copy_snapshot(target_dir, mappings)
        count += 1

    return count


def entries_requiring_sync(
    vendored: tuple[VendoredPin, ...] | list[VendoredPin],
) -> tuple[VendoredPin, ...]:
    """Return only entries that declare copied snapshot paths."""
    return tuple(entry for entry in vendored if entry.paths)


def _compare_trees(
    synced_root: Path,
    repo_root: Path,
    vendored: tuple[VendoredPin, ...] | list[VendoredPin],
) -> list[str]:
    """Return a list of paths that differ (synced vs committed).

    Only checks paths declared in the vendored manifest — does not walk the
    entire templates/ tree. Handles line-ending normalization: compare content
    decoded as UTF-8 with universal newlines (handles LF vs CRLF on checkout).
    Missing files in committed tree are also reported as diffs.
    """
    diffs: list[str] = []
    for entry in vendored:
        for path_pair in entry.paths:
            dest = path_pair.dest
            synced_path = synced_root / dest
            committed_path = repo_root / dest
            if not synced_path.exists():
                diffs.append(f"{dest}: missing in sync output")
                continue
            if not committed_path.exists():
                diffs.append(f"{dest}: missing in committed tree")
                continue

            if synced_path.is_dir():
                synced_files = {p.relative_to(synced_path) for p in synced_path.rglob("*") if p.is_file()}
                committed_files = {p.relative_to(committed_path) for p in committed_path.rglob("*") if p.is_file()}
                all_rel_files = sorted(synced_files | committed_files)
                for rel_f in all_rel_files:
                    s_file = synced_path / rel_f
                    c_file = committed_path / rel_f
                    rel_dest_str = f"{dest}/{rel_f.as_posix()}"
                    if not s_file.exists():
                        diffs.append(f"{rel_dest_str}: missing in sync output")
                        continue
                    if not c_file.exists():
                        diffs.append(f"{rel_dest_str}: missing in committed tree")
                        continue
                    s_text = s_file.read_text(encoding="utf-8", errors="replace")
                    c_text = c_file.read_text(encoding="utf-8", errors="replace")
                    if s_text.replace("\r\n", "\n") != c_text.replace("\r\n", "\n"):
                        diffs.append(f"{rel_dest_str}: content differs")
            else:
                synced_text = synced_path.read_text(encoding="utf-8", errors="replace")
                committed_text = committed_path.read_text(encoding="utf-8", errors="replace")
                if synced_text.replace("\r\n", "\n") != committed_text.replace("\r\n", "\n"):
                    diffs.append(f"{dest}: content differs")
    return diffs


def _compare_executable_modes(
    clone_base: Path,
    vendored: tuple[VendoredPin, ...] | list[VendoredPin],
) -> list[str]:
    """Compare declared executable paths against upstream git file modes."""
    diffs: list[str] = []
    for entry in vendored:
        if not entry.executable:
            continue
        clone_dir = clone_base / entry.repo.replace("/", "_")
        if not (clone_dir / ".git").exists():
            diffs.append(
                f"{entry.repo}: clone metadata missing; executable modes were not checked"
            )
            continue
        res = subprocess.run(
            ["git", "ls-files", "-s"],
            cwd=clone_dir,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if res.returncode != 0:
            diffs.append(
                f"{entry.repo}: git ls-files failed; executable modes were not checked"
            )
            continue
        upstream_executables: set[str] = set()
        for line in res.stdout.splitlines():
            parts = line.split("\t", 1)
            if len(parts) != 2:
                continue
            meta, path = parts
            mode = meta.split()[0]
            if mode == "100755":
                if any(
                    path == p.src or path.startswith(f"{p.src.rstrip('/')}/")
                    for p in entry.paths
                ):
                    upstream_executables.add(path)
        declared_executables = set(entry.executable)
        for missing in sorted(declared_executables - upstream_executables):
            diffs.append(
                f"{entry.repo}: {missing} declared executable but upstream mode is not 100755"
            )
        for extra in sorted(upstream_executables - declared_executables):
            diffs.append(
                f"{entry.repo}: {extra} upstream mode is 100755 but not declared in executable"
            )
    return diffs


def _compare_executable_line_endings(
    repo_root: Path,
    vendored: tuple[VendoredPin, ...] | list[VendoredPin],
) -> list[str]:
    """Reject carriage returns in committed files declared executable."""
    diffs: list[str] = []
    for entry in vendored:
        for executable in entry.executable:
            for path_pair in entry.paths:
                source_root = path_pair.src.rstrip("/")
                if executable == source_root:
                    relative = ""
                elif executable.startswith(f"{source_root}/"):
                    relative = executable[len(source_root) + 1 :]
                else:
                    continue
                destination = Path(path_pair.dest)
                if relative:
                    destination /= relative
                committed_path = repo_root / destination
                if committed_path.is_file() and b"\r" in committed_path.read_bytes():
                    diffs.append(
                        f"{destination.as_posix()}: declared executable contains carriage returns"
                    )
                break
    return diffs


def _check_mode(manifest_path: Path, repo_root: Path, clone_base: Path) -> int:
    """Sync into a temp dir; byte-compare each file against committed snapshot.

    Exits 0 if all files match (or vendored list is empty). Exits 1 and prints
    a diff summary on any mismatch.
    """
    manifest = load_manifest(manifest_path)
    vendored = manifest.vendored
    if not vendored:
        print("vendored drift check: nothing to check (empty list)")
        return 0

    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        (tmp_root / "templates").mkdir()
        sync_all(manifest_path, tmp_root, clone_base)
        diffs = _compare_trees(tmp_root, repo_root, vendored)
        diffs.extend(_compare_executable_modes(clone_base, vendored))
        diffs.extend(_compare_executable_line_endings(repo_root, vendored))

    if diffs:
        for d in diffs:
            print(f"DRIFT: {d}", file=sys.stderr)
        return 1
    print("vendored drift check: all snapshots match")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sync vendored external repos or check for drift."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Dry-run mode: sync into a temp dir and compare against committed snapshots; exit 1 on any diff.",
    )
    args = parser.parse_args()

    manifest_path = _REPO_ROOT / "src" / "dev_ready" / "manifest.json"
    clone_base = _REPO_ROOT / ".sync-cache"

    try:
        if args.check:
            return _check_mode(manifest_path, _REPO_ROOT, clone_base)
        count = sync_all(manifest_path, _REPO_ROOT, clone_base)
        print(f"sync complete: {count} vendored repo(s) processed")
        return 0
    except (RuntimeError, OSError, ManifestError) as error:
        print(f"sync failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
