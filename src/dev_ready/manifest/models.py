"""Data models for the upstream pin manifest."""

from collections.abc import Mapping
from dataclasses import dataclass

from dev_ready.catalog_effects import CatalogEffect


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

    `prune` = paths that generate fine but do not belong in a user project
    (curated, reviewed at bump time), vs `exclude` = broken-by-design paths (ADR-006).
    """

    repo: str
    ref: str
    commit: str
    license: str
    verified_at: str | None = None
    exclude: tuple[str, ...] = ()
    prune: tuple[str, ...] = ()


@dataclass(frozen=True)
class ItemPath:
    src: str
    dest: str


@dataclass(frozen=True)
class VendoredPin:
    """One pinned vendored source (external repo at an exact commit).

    `repo` is in `owner/name` shape. `commit` is a 40-char lowercase hex sha.
    `license` is a non-empty SPDX-style string (e.g. "MIT"). `paths` maps each
    upstream source path (relative to the cloned repo root) to its destination
    path under `templates/` (relative to the repo root) — literal path pairs,
    no gitwildmatch patterns.
    """

    repo: str
    commit: str
    license: str
    paths: tuple[ItemPath, ...]


@dataclass(frozen=True)
class Category:
    """One user-facing catalog grouping."""

    id: str
    description: str


@dataclass(frozen=True)
class CatalogItem:
    id: str
    description: str
    mode: str
    license: str
    category: str = ""
    paths: tuple[ItemPath, ...] = ()
    pin: str | None = None
    effect: CatalogEffect | None = None
    vendored_repo: str | None = None
    requires: tuple[str, ...] = ()


@dataclass(frozen=True)
class AgentTarget:
    """One native Agent Target layout declared by the manifest."""

    id: str
    description: str
    skills_dir: str
    rules_file: str | None
    mcp_file: str | None


class ComponentCatalog(dict[str, tuple[CatalogItem, ...]]):
    """Catalog component mapping carrying the independent Agent Target axis."""

    def __init__(
        self,
        components: Mapping[str, tuple[CatalogItem, ...]],
        agent_targets: Mapping[str, AgentTarget],
        categories: Mapping[str, Category] | None = None,
    ) -> None:
        super().__init__(components)
        self.agent_targets = dict(agent_targets)
        self.categories = dict(categories or {})


@dataclass(frozen=True)
class Manifest:
    """Validated content of manifest.json."""

    manifest_version: int
    upstream: dict[str, UpstreamPin]
    overlay_version: str
    components: ComponentCatalog
    agent_targets: dict[str, AgentTarget]
    categories: dict[str, Category]
    vendored: tuple[VendoredPin, ...] = ()


