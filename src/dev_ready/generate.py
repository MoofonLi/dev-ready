"""Orchestrate fetch + overlay into one all-or-nothing pipeline.

Only `cli` (or this module, which only `cli` calls) sequences `fetch` and
`overlay` — see docs/architecture.md, Dependency Rules.
"""

import shutil
import tempfile
from pathlib import Path

from dev_ready.errors import TargetDirectoryError
from dev_ready.fetch import fetch_snapshot
from dev_ready.manifest import UpstreamPin
from dev_ready.overlay import apply_overlay
from dev_ready.prompts import Answers

__all__ = ["generate"]


def generate(answers: Answers, pin: UpstreamPin) -> list[Path]:
    """Fetch the pinned upstream snapshot, apply the overlay, then move the
    fully assembled project into `answers.target_dir` as the last step.

    All-or-nothing across the whole pipeline (fetch + overlay), not just
    fetch: everything happens in a staging directory first, and
    `target_dir` is only touched by the final move. On any failure,
    `target_dir` is left untouched and no temp artifacts are leaked.
    """
    _validate_target_dir(answers.target_dir)

    staging_root = Path(tempfile.mkdtemp(prefix="dev-ready-generate-"))
    try:
        project_staging = staging_root / "project"
        fetch_snapshot(pin, project_staging)
        written = apply_overlay(answers, project_staging)
        _finalize(project_staging, answers.target_dir)
    finally:
        shutil.rmtree(staging_root, ignore_errors=True)

    return written


def _validate_target_dir(target_dir: Path) -> None:
    if not target_dir.exists():
        return
    if not target_dir.is_dir():
        raise TargetDirectoryError(
            f"target {target_dir} exists and is not a directory — remove or rename it and retry."
        )
    if any(target_dir.iterdir()):
        raise TargetDirectoryError(
            f"target directory {target_dir} is not empty — remove or rename it and retry."
        )


def _finalize(staging_dir: Path, target_dir: Path) -> None:
    try:
        if target_dir.exists():
            target_dir.rmdir()
        shutil.move(str(staging_dir), str(target_dir))
    except OSError as error:
        raise TargetDirectoryError(
            f"failed to write generated project into {target_dir}: {error}"
        ) from error
