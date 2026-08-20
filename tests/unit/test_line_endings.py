"""Line endings must not depend on the machine that produced a file.

Generation copies most template assets byte for byte (`overlay/rendering.py`
reads a non-template asset with `read_bytes`). A template checked out or
written with CRLF therefore travels into the user's project unchanged, so the
same dev-ready version would emit different files on different platforms.
NFR-1 forbids that.

`.gitattributes` declares `src/dev_ready/templates/** text eol=lf`, so any
correct checkout satisfies this on every platform. The guard exists to catch a
working tree that a script or an older tool rewrote in place, because git
normalizes on `add` and reports such a file as clean.
"""

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATES_ROOT = REPO_ROOT / "src" / "dev_ready" / "templates"


def _tracked_template_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z", "src/dev_ready/templates"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )
    names = [name for name in result.stdout.split("\0") if name]
    return [REPO_ROOT / name for name in names]


def test_the_repository_tracks_template_assets() -> None:
    """Guard the guard: an empty file list would make the next test vacuous."""
    assert len(_tracked_template_files()) > 100


def test_no_template_asset_holds_a_carriage_return() -> None:
    offenders = [
        path.relative_to(REPO_ROOT).as_posix()
        for path in _tracked_template_files()
        if path.is_file() and b"\r\n" in path.read_bytes()
    ]
    assert offenders == [], (
        "template assets hold CRLF and would carry it into a generated project; "
        "restore them with: git ls-files -z src/dev_ready/templates | "
        "xargs -0 rm -f && git checkout -- src/dev_ready/templates"
    )
