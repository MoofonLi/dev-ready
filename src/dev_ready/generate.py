"""Orchestrate fetch + overlay + verify into one all-or-nothing pipeline.

Only `cli` (or this module, which only `cli` calls) sequences `fetch`,
`overlay`, and `verify` — see docs/architecture.md, Dependency Rules.
"""

import re
import secrets
import shutil
import tempfile
import time
from collections.abc import Callable, Collection, Mapping
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TypeVar

from dev_ready.errors import TargetDirectoryError
from dev_ready.fetch import fetch_snapshot
from dev_ready.manifest import CatalogItem, UpstreamPin, VendoredPin
from dev_ready.overlay import apply_overlay
from dev_ready.prompts import Answers
from dev_ready.verify import verify_project

__all__ = [
    "CleanupWarningEvent",
    "GenerationStage",
    "GenerationEvent",
    "ProgressEvent",
    "ProgressStatus",
    "generate",
]


class GenerationStage(str, Enum):
    """Stable identities for the four observable generation stages."""

    FETCH = "fetch"
    OVERLAY = "overlay"
    VERIFY = "verify"
    FINALIZE = "finalize"


class ProgressStatus(str, Enum):
    """Lifecycle state of a generation stage."""

    STARTED = "started"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class ProgressEvent:
    """Typed observational event emitted by :func:`generate`."""

    stage: GenerationStage
    status: ProgressStatus
    elapsed_seconds: float | None = None
    commit: str | None = None


@dataclass(frozen=True, slots=True)
class CleanupWarningEvent:
    """Non-stage warning emitted when temporary staging cannot be removed."""

    path: Path


GenerationEvent = ProgressEvent | CleanupWarningEvent
ProgressCallback = Callable[[GenerationEvent], None]
_Result = TypeVar("_Result")


def generate(
    answers: Answers,
    pin: UpstreamPin,
    catalog: Mapping[str, tuple[CatalogItem, ...]],
    vendored: Collection[VendoredPin] = (),
    progress: ProgressCallback | None = None,
    *,
    clock: Callable[[], float] = time.monotonic,
) -> list[Path]:
    """Fetch the pinned upstream snapshot, apply the overlay, verify the
    result, then move the fully assembled project into `answers.target_dir`
    as the last step.

    All-or-nothing across the whole pipeline (fetch + overlay + verify), not
    just fetch: everything happens in a staging directory first, and
    `target_dir` is only touched by the final move. On any failure —
    including a verification failure — `target_dir` is left untouched and
    no temp artifacts are leaked.
    """
    target_was_empty = _validate_target_dir(answers.target_dir)

    staging_root = _create_staging_root(answers.target_dir)
    try:
        project_staging = staging_root / "project"
        _run_stage(
            GenerationStage.FETCH,
            progress,
            clock,
            lambda: _fetch_and_clean(pin, project_staging, answers),
            commit=pin.commit,
        )
        written = _run_stage(
            GenerationStage.OVERLAY,
            progress,
            clock,
            lambda: apply_overlay(
                answers, project_staging, catalog, pin, vendored=vendored
            ),
        )
        _run_stage(
            GenerationStage.VERIFY,
            progress,
            clock,
            lambda: verify_project(project_staging, answers, catalog),
        )
        _run_stage(
            GenerationStage.FINALIZE,
            progress,
            clock,
            lambda: _finalize_project(
                project_staging,
                answers.target_dir,
                restore_empty_target=target_was_empty,
            ),
        )

    finally:
        shutil.rmtree(staging_root, ignore_errors=True)
        if staging_root.exists():
            _emit_event(progress, CleanupWarningEvent(staging_root))

    return written


def _run_stage(
    stage: GenerationStage,
    progress: ProgressCallback | None,
    clock: Callable[[], float],
    operation: Callable[[], _Result],
    *,
    commit: str | None = None,
) -> _Result:
    started_at = clock()
    _emit_event(
        progress,
        ProgressEvent(stage=stage, status=ProgressStatus.STARTED, commit=commit),
    )
    try:
        result = operation()
    except BaseException:
        _emit_event(
            progress,
            ProgressEvent(
                stage=stage,
                status=ProgressStatus.FAILED,
                elapsed_seconds=max(0.0, clock() - started_at),
                commit=commit,
            ),
        )
        raise
    _emit_event(
        progress,
        ProgressEvent(
            stage=stage,
            status=ProgressStatus.COMPLETED,
            elapsed_seconds=max(0.0, clock() - started_at),
            commit=commit,
        ),
    )
    return result


def _emit_event(progress: ProgressCallback | None, event: GenerationEvent) -> None:
    if progress is None:
        return
    try:
        progress(event)
    except Exception:
        # Progress is observational and must never affect generation.
        pass


def _fetch_and_clean(pin: UpstreamPin, project_staging: Path, answers: Answers) -> None:
    fetch_snapshot(pin, project_staging, _template_data(answers))

    # Copier metadata is generator machinery and never belongs in the output.
    copier_dir = project_staging / ".copier"
    if copier_dir.exists():
        shutil.rmtree(copier_dir)
    copier_answers = project_staging / ".copier-answers.yml"
    if copier_answers.exists():
        copier_answers.unlink()


def _finalize_project(
    project_staging: Path, target_dir: Path, *, restore_empty_target: bool
) -> None:
    _prune_empty_dirs(project_staging)
    _finalize(
        project_staging,
        target_dir,
        restore_empty_target=restore_empty_target,
    )


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


def _validate_target_dir(target_dir: Path) -> bool:
    if not target_dir.exists():
        return False
    if not target_dir.is_dir():
        raise TargetDirectoryError(
            f"target {target_dir} exists and is not a directory — remove or rename it and retry."
        )
    if any(target_dir.iterdir()):
        raise TargetDirectoryError(
            f"target directory {target_dir} is not empty — remove or rename it and retry."
        )
    return True


def _create_staging_root(target_dir: Path) -> Path:
    try:
        return Path(
            tempfile.mkdtemp(
                prefix=f".{target_dir.name}.dev-ready-",
                dir=target_dir.parent,
            )
        )
    except OSError as error:
        raise TargetDirectoryError(
            f"failed to create staging beside {target_dir}: {error}"
        ) from error


def _finalize(
    staging_dir: Path, target_dir: Path, *, restore_empty_target: bool
) -> None:
    removed_empty_target = False
    try:
        if target_dir.exists():
            if not restore_empty_target:
                raise TargetDirectoryError(
                    f"target {target_dir} appeared during generation; refusing to overwrite it."
                )
            _validate_target_dir(target_dir)
            target_dir.rmdir()
            removed_empty_target = True
        elif restore_empty_target:
            raise TargetDirectoryError(
                f"target {target_dir} changed during generation; refusing to finalize."
            )
        staging_dir.rename(target_dir)
    except TargetDirectoryError:
        raise
    except OSError as error:
        if removed_empty_target and not target_dir.exists():
            try:
                target_dir.mkdir()
            except OSError as restore_error:
                raise TargetDirectoryError(
                    f"failed to write generated project into {target_dir}: {error}; "
                    f"also failed to restore the original empty target: {restore_error}"
                ) from error
        raise TargetDirectoryError(
            f"failed to write generated project into {target_dir}: {error}"
        ) from error


def _prune_empty_dirs(root: Path) -> None:
    """Recursively remove empty directories from bottom to top."""
    import os
    for dirpath, _, _ in os.walk(root, topdown=False):
        path = Path(dirpath)
        if path == root:
            continue
        if not any(path.iterdir()):
            try:
                path.rmdir()
            except OSError:
                pass

