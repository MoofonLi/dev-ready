"""Generate the upstream base with Copier at the manifest-pinned commit (ADR-005).

Copier is the upstream template's officially supported consumption path: it
applies the template's own question defaults/answers (project name, stack
name, secrets written into .env via the template's `_tasks`) and its
`_exclude` list, neither of which a raw tarball download can do.
"""

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from dev_ready.errors import FetchError, TargetDirectoryError
from dev_ready.manifest import UpstreamPin


def fetch_snapshot(
    pin: UpstreamPin, dest: Path, template_data: dict[str, Any] | None = None
) -> Path:
    """Run Copier against the upstream template pinned by `pin`, into `dest`.

    `template_data` answers the template's own copier.yml questions; anything
    not provided falls back to the template's defaults (never an interactive
    prompt — `defaults=True`).

    All-or-nothing: `dest` is populated only after a fully successful Copier
    run. On any failure, all temp artifacts are removed and `dest` is left
    untouched.
    """
    _validate_target_dir(dest)
    if shutil.which("git") is None:
        raise FetchError(
            "git executable not found — Copier needs git to fetch the pinned template."
            " Install git and retry."
        )

    staging_dir = Path(tempfile.mkdtemp(prefix="dev-ready-staging-"))
    try:
        _run_copier(pin, staging_dir, template_data or {})
        _finalize(staging_dir, dest)
    finally:
        shutil.rmtree(staging_dir, ignore_errors=True)

    return dest


def _run_copier(pin: UpstreamPin, staging_dir: Path, data: dict[str, Any]) -> None:
    # Imported lazily so `dev-ready --help/--version` never pays Copier's
    # import cost (pydantic, jinja2, ...).
    import copier
    from copier.errors import CopierError

    # UpstreamPin.repo and .commit are validated by dev_ready.manifest (strict
    # owner/name pattern, 40-hex-char sha) before a pin ever reaches this
    # function, so no raw/unvalidated input is interpolated into the URL.
    src_url = f"https://github.com/{pin.repo}.git"
    try:
        copier.run_copy(
            src_url,
            staging_dir,
            data=data,
            vcs_ref=pin.commit,
            # Per-pin source paths Copier must skip, merged with the
            # template's own _exclude. Two reasons entries live here:
            # (1) the pinned template ships symlinks into .venv/ that dangle
            #     until the user creates the venv; Copier follows symlinks
            #     and crashes on them;
            # (2) the template defines its own _exclude, which REPLACES
            #     Copier's DEFAULT_EXCLUDE entirely — so .git and
            #     copier.yml/.yaml would otherwise be copied into the
            #     generated project (the .git worktree file makes the output
            #     look like a checkout of the upstream template).
            # See manifest.json and UpstreamPin.exclude. `pin.prune`
            # (curated repo-maintenance files, ADR-006) is merged in alongside `pin.exclude`.
            exclude=pin.exclude + pin.prune,
            # Unanswered template questions take the template's defaults;
            # dev-ready's own prompting happens in `prompts`, never here.
            defaults=True,
            # Required because the template declares `_tasks`
            # (.copier/update_dotenv.py). The executed code is pinned to a
            # CI-verified commit (ADR-002/ADR-005), not floating "latest".
            unsafe=True,
            quiet=True,
        )
    except (CopierError, subprocess.CalledProcessError, OSError) as error:
        raise FetchError(
            f"copier generation from {src_url}@{pin.commit} failed: {error}"
        ) from error


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
        raise FetchError(f"failed to move generated snapshot into {dest}: {error}") from error
