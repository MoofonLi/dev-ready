"""Orchestrate downloading and safely extracting an upstream snapshot."""

import shutil
import tempfile
from pathlib import Path

import dev_ready.fetch.download as _download
from dev_ready.errors import FetchError, TargetDirectoryError
from dev_ready.fetch.extract import extract_snapshot
from dev_ready.fetch.urls import build_download_url
from dev_ready.manifest import UpstreamPin


def fetch_snapshot(pin: UpstreamPin, dest: Path) -> Path:
    """Download and extract the snapshot pinned by `pin` into `dest`.

    All-or-nothing: `dest` is populated only after a fully successful
    download and safe extraction. On any failure, all temp artifacts are
    removed and `dest` is left untouched.
    """
    _validate_target_dir(dest)

    download_dir = Path(tempfile.mkdtemp(prefix="dev-ready-fetch-"))
    staging_dir = Path(tempfile.mkdtemp(prefix="dev-ready-staging-"))
    try:
        url = build_download_url(pin)
        tar_path = download_dir / "snapshot.tar.gz"
        _download.download(url, tar_path)
        extract_snapshot(tar_path, staging_dir)
        _finalize(staging_dir, dest)
    finally:
        shutil.rmtree(download_dir, ignore_errors=True)
        shutil.rmtree(staging_dir, ignore_errors=True)

    return dest


def _validate_target_dir(dest: Path) -> None:
    # When called from generate(), dest is always a fresh subdirectory of a
    # just-created staging root, so this check is a no-op in that path; it
    # only bites when fetch_snapshot is called directly at an existing path.
    if not dest.exists():
        return
    if not dest.is_dir():
        raise TargetDirectoryError(
            f"target {dest} exists and is not a directory — remove or rename it and retry."
        )
    if any(dest.iterdir()):
        raise TargetDirectoryError(
            f"target directory {dest} is not empty — remove or rename it and retry."
        )


def _finalize(staging_dir: Path, dest: Path) -> None:
    try:
        if dest.exists():
            dest.rmdir()
        shutil.move(str(staging_dir), str(dest))
    except OSError as error:
        raise FetchError(f"failed to move extracted snapshot into {dest}: {error}") from error
