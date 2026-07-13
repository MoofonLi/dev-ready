"""Safe extraction of GitHub-style upstream tarballs.

GitHub tarballs wrap all content in a single "{name}-{sha}/" directory; this
module strips that one level and rejects malicious members (absolute paths,
path traversal, symlinks escaping the extraction root, hardlinks, and any
other non-regular-file, non-directory member) before anything is written to
disk. Symlinks that resolve within the extraction root are preserved: the
real upstream template (fastapi/full-stack-fastapi-template) ships at least
one (`.agents/skills/fastapi`), so rejecting all symlinks outright would
break every fetch.
"""

import re
import tarfile
from pathlib import Path, PurePosixPath

from dev_ready.errors import FetchError

_DRIVE_LETTER = re.compile(r"^[A-Za-z]:")


def extract_snapshot(tar_path: Path, staging_dir: Path) -> None:
    """Extract `tar_path` into `staging_dir`, stripping the single top-level dir."""
    try:
        with tarfile.open(tar_path, mode="r:gz") as tar:
            members = tar.getmembers()
            if not members:
                raise FetchError(f"upstream archive is empty: {tar_path}")
            _reject_unsafe_paths(members)
            prefix = _single_top_level_dir(members)

            extractable = []
            for member in members:
                _reject_unsafe_type(member)
                rest = _strip_prefix(member, prefix)
                if rest is None:
                    continue
                if member.issym() and _symlink_escapes_root(rest, member.linkname):
                    raise FetchError(
                        f"archive member is a symlink escaping the extraction root:"
                        f" {member.name!r} -> {member.linkname!r}"
                    )
                member.name = rest
                extractable.append(member)

            tar.extractall(path=staging_dir, members=extractable, filter="data")
    except (tarfile.TarError, OSError, EOFError) as error:
        raise FetchError(f"upstream archive is corrupt or unreadable: {error}") from error


def _reject_unsafe_paths(members: list[tarfile.TarInfo]) -> None:
    for member in members:
        name = member.name.replace("\\", "/")
        if name.startswith("/") or _DRIVE_LETTER.match(name):
            raise FetchError(f"archive member has an absolute path: {member.name!r}")
        if ".." in PurePosixPath(name).parts:
            raise FetchError(f"archive member escapes the archive root: {member.name!r}")


def _reject_unsafe_type(member: tarfile.TarInfo) -> None:
    if member.islnk():
        raise FetchError(f"archive member is a hardlink, which is not allowed: {member.name!r}")
    if not (member.isreg() or member.isdir() or member.issym()):
        raise FetchError(f"archive member has an unsupported type: {member.name!r}")


def _single_top_level_dir(members: list[tarfile.TarInfo]) -> str:
    tops = {member.name.replace("\\", "/").split("/", 1)[0] for member in members}
    tops.discard("")
    if len(tops) != 1:
        raise FetchError(
            "unexpected archive layout: expected exactly one top-level directory,"
            f" found {sorted(tops)!r}"
        )
    return next(iter(tops))


def _strip_prefix(member: tarfile.TarInfo, prefix: str) -> str | None:
    name = member.name.replace("\\", "/")
    if name == prefix:
        if not member.isdir():
            raise FetchError(
                f"unexpected archive layout: top-level entry {member.name!r} is not a directory"
            )
        return None
    rest = name[len(prefix) + 1 :]
    return rest or None


def _symlink_escapes_root(rest: str, linkname: str) -> bool:
    """Lexically resolve a symlink target relative to its (post-strip) location.

    Pure path arithmetic (no filesystem access): the destination tree may not
    exist yet at validation time.
    """
    target = linkname.replace("\\", "/")
    if target.startswith("/") or _DRIVE_LETTER.match(target):
        return True
    resolved: list[str] = []
    for part in (*PurePosixPath(rest).parent.parts, *PurePosixPath(target).parts):
        if part in (".", ""):
            continue
        if part == "..":
            if not resolved:
                return True
            resolved.pop()
        else:
            resolved.append(part)
    return False
