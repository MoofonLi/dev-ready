"""Data models for the upstream pin manifest."""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from dev_ready.catalog_effects import CatalogEffect

RETIRED_LOOP_ITEM_IDS = frozenset(
    {"spec-loop", "tdd", "diagnosing-bugs", "code-review", "setup-all"}
)

# The Components a Catalog Item can be written under, in manifest order. The
# loader rejects any other key, so this tuple is the complete set — iterate it
# instead of restating the literal at a call site.
CATALOG_COMPONENTS: tuple[str, ...] = ("skills", "mcp", "docs")


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
class DefaultSet:
    """Manifest-declared content produced when the user accepts defaults."""

    development_loop: str
    enhancements: tuple[str, ...]


@dataclass(frozen=True)
class CatalogItem:
    id: str
    description: str
    mode: str
    license: str
    category: str = ""
    mount: str | None = None
    kind: str = "enhancement"
    steps: tuple[str, ...] = ()
    paths: tuple[ItemPath, ...] = ()
    pin: str | None = None
    effect: CatalogEffect | None = None
    vendored_repo: str | None = None
    requires: tuple[str, ...] = ()


@dataclass(frozen=True)
class AgentTarget:
    """One native Agent Target layout declared by the manifest."""

    id: str
    description: str | None
    skills_dir: str
    rules_file: str | None
    mcp_file: str | None


class ComponentCatalog(dict[str, tuple[CatalogItem, ...]]):
    """The catalog every module queries: items, Categories, Agent Targets.

    Callers take this type, not the bare mapping it subclasses — the extra axes
    are part of the interface, and every question they get asked is answered
    here rather than re-derived at the call site.
    """

    def __init__(
        self,
        components: Mapping[str, tuple[CatalogItem, ...]],
        agent_targets: Mapping[str, AgentTarget],
        categories: Mapping[str, Category] | None = None,
        default_set: DefaultSet | None = None,
        standard_compliant_agents: Iterable[str] = (),
    ) -> None:
        super().__init__(components)
        self.agent_targets = dict(agent_targets)
        self.categories = dict(categories or {})
        self.default_set = default_set
        self.standard_compliant_agents = tuple(standard_compliant_agents)
        loops = tuple(
            item for item in self.all_items() if item.kind == "development-loop"
        )
        self.development_loop_ids = tuple(item.id for item in loops)
        self.development_loop_steps = {item.id: item.steps for item in loops}

    def all_items(self) -> tuple[CatalogItem, ...]:
        """Every declared item, in Component then declaration order."""
        return tuple(
            item
            for component in CATALOG_COMPONENTS
            for item in self.get(component, ())
        )

    def item_ids(self, component: str) -> frozenset[str]:
        """Every id declared under one Component."""
        return frozenset(item.id for item in self.get(component, ()))

    def by_component(self, item_ids: Iterable[str]) -> dict[str, frozenset[str]]:
        """Split one flat id set into the Component each id is written under."""
        wanted = frozenset(item_ids)
        return {
            component: frozenset(
                item.id for item in self.get(component, ()) if item.id in wanted
            )
            for component in CATALOG_COMPONENTS
        }

    def ids_in_category(self, category_id: str) -> frozenset[str]:
        """Every item id presented under one Category, across Components."""
        return frozenset(
            item.id for item in self.all_items() if item.category == category_id
        )

    def loops(self) -> tuple[CatalogItem, ...]:
        """Every development loop the Dev Category declares."""
        return tuple(
            item for item in self.all_items() if item.kind == "development-loop"
        )

    @property
    def category_ids(self) -> frozenset[str]:
        return frozenset(self.categories)

    @property
    def agent_target_ids(self) -> frozenset[str]:
        return frozenset(self.agent_targets)

    @property
    def default_development_loop(self) -> str:
        """The Default Set's loop, or '' for a catalog that declares no Default Set."""
        return self.default_set.development_loop if self.default_set is not None else ""


@dataclass(frozen=True)
class Manifest:
    """Validated content of manifest.json."""

    manifest_version: int
    upstream: dict[str, UpstreamPin]
    overlay_version: str
    components: ComponentCatalog
    agent_targets: dict[str, AgentTarget]
    categories: dict[str, Category]
    default_set: DefaultSet
    standard_compliant_agents: tuple[str, ...]
    vendored: tuple[VendoredPin, ...] = ()
