"""Orchestrate fetch + overlay + verify into one all-or-nothing pipeline.

Only `cli` (or this module, which only `cli` calls) sequences `fetch`,
`overlay`, and `verify` — see docs/architecture.md, Dependency Rules.
"""

import re
import secrets
import shutil
import sys
import tempfile
from pathlib import Path

from dev_ready.errors import TargetDirectoryError
from dev_ready.fetch import fetch_snapshot
from dev_ready.manifest import UpstreamPin
from dev_ready.overlay import apply_overlay
from dev_ready.prompts import Answers
from dev_ready.verify import verify_project

__all__ = ["generate"]


def generate(answers: Answers, pin: UpstreamPin) -> list[Path]:
    """Fetch the pinned upstream snapshot, apply the overlay, verify the
    result, then move the fully assembled project into `answers.target_dir`
    as the last step.

    All-or-nothing across the whole pipeline (fetch + overlay + verify), not
    just fetch: everything happens in a staging directory first, and
    `target_dir` is only touched by the final move. On any failure —
    including a verification failure — `target_dir` is left untouched and
    no temp artifacts are leaked.
    """
    _validate_target_dir(answers.target_dir)

    staging_root = Path(tempfile.mkdtemp(prefix="dev-ready-generate-"))
    try:
        project_staging = staging_root / "project"
        fetch_snapshot(pin, project_staging, _template_data(answers))
        written = apply_overlay(answers, project_staging)
        verify_project(project_staging)
        _finalize(project_staging, answers.target_dir)
    finally:
        shutil.rmtree(staging_root, ignore_errors=True)
        if staging_root.exists():
            print(f"warning: failed to remove temp directory {staging_root}", file=sys.stderr)

    return written


def _template_data(answers: Answers) -> dict[str, str]:
    """Answers for the upstream template's own copier.yml questions.

    Anything not listed here falls back to the template's defaults
    (fetch_snapshot runs Copier with defaults=True). Secrets are generated
    per-project so a generated project never ships the upstream "changethis"
    placeholders; the template's `_tasks` write them into the project's .env,
    which is where users find them (including the first superuser password).

    The question names are coupled to the pinned upstream commit; the weekly
    bump CI (ADR-002) regenerates a real project, so a rename upstream fails
    the bump PR rather than end users.
    """
    return {
        "project_name": answers.project_name,
        "stack_name": _slugify(answers.project_name),
        "secret_key": secrets.token_urlsafe(32),
        "postgres_password": secrets.token_urlsafe(32),
        "first_superuser_password": secrets.token_urlsafe(16),
    }


def _slugify(name: str) -> str:
    """Docker-Compose-label-safe stack name: lowercase, alnum and hyphens only."""
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "app"


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
        # shutil.move is non-atomic on cross-device moves (falls back to
        # copy+delete); the partial-visibility window is accepted (see
        # phase 2 SRE review).
        shutil.move(str(staging_dir), str(target_dir))
    except OSError as error:
        raise TargetDirectoryError(
            f"failed to write generated project into {target_dir}: {error}"
        ) from error
