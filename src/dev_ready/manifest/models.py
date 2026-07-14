"""Data models for the upstream pin manifest."""

from dataclasses import dataclass


@dataclass(frozen=True)
class UpstreamPin:
    """One pinned upstream source (repo at an exact commit).

    `exclude` lists source paths Copier must skip for this pin, on top of the
    template's own `_exclude` (Copier merges both). Needed for entries that
    are broken by design at clone time — e.g. the FastAPI template ships
    symlinks into `.venv/` that dangle until the user creates the venv, and
    Copier follows symlinks by default. The list lives next to the pin so a
    weekly bump PR that hits new dangling entries fails CI loudly and gets
    fixed here, in one reviewed place (ADR-002/ADR-005).
    """

    repo: str
    ref: str
    commit: str
    license: str
    verified_at: str | None = None
    exclude: tuple[str, ...] = ()


@dataclass(frozen=True)
class Manifest:
    """Validated content of manifest.json."""

    manifest_version: int
    upstream: dict[str, UpstreamPin]
    overlay_version: str
