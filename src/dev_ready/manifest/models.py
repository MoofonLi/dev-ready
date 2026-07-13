"""Data models for the upstream pin manifest."""

from dataclasses import dataclass


@dataclass(frozen=True)
class UpstreamPin:
    """One pinned upstream source (repo at an exact commit)."""

    repo: str
    ref: str
    commit: str
    license: str
    verified_at: str | None = None


@dataclass(frozen=True)
class Manifest:
    """Validated content of manifest.json."""

    manifest_version: int
    upstream: dict[str, UpstreamPin]
    overlay_version: str
