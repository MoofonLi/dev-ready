"""Generation Intent: resolved name, destination, catalog selection, Agent Targets."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from dev_ready.errors import InvalidArgumentsError
from dev_ready.manifest.models import (
    CATALOG_COMPONENTS,
    ComponentCatalog,
)

_PROJECT_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]*$")
_DEFAULT_AGENT_TARGETS = frozenset({"claude"})


def validate_project_name(project_name: str) -> None:
    """Validate the project name once at the generation-intent seam."""
    if not _PROJECT_NAME_PATTERN.fullmatch(project_name):
        raise InvalidArgumentsError(
            f"invalid project name {project_name!r}: use letters, digits, '.', '_', '-',"
            " starting with a letter or digit"
        )


@dataclass(frozen=True, init=False)
class ProjectSelection:
    """Canonical catalog and optional-content selection.

    Inclusion of skills and MCP is derived from the selected item sets, so
    callers cannot construct contradictory boolean/item-set state.
    """

    skills: frozenset[str] = frozenset()
    mcp: frozenset[str] = frozenset()
    docs_items: frozenset[str] = frozenset()
    categories: frozenset[str] = frozenset()
    development_loop: str = ""
    agent_targets: frozenset[str] = frozenset()

    @classmethod
    def _create(
        cls,
        *,
        skills: frozenset[str],
        mcp: frozenset[str],
        docs_items: frozenset[str],
        categories: frozenset[str],
        development_loop: str,
        agent_targets: frozenset[str],
    ) -> ProjectSelection:
        selection = object.__new__(cls)
        object.__setattr__(selection, "skills", skills)
        object.__setattr__(selection, "mcp", mcp)
        object.__setattr__(selection, "docs_items", docs_items)
        object.__setattr__(selection, "categories", categories)
        object.__setattr__(selection, "development_loop", development_loop)
        object.__setattr__(selection, "agent_targets", agent_targets)
        return selection

    @classmethod
    def optional_only(cls) -> ProjectSelection:
        """Return unresolved fallback intent for callers that have no catalog."""
        return cls._create(
            skills=frozenset(),
            mcp=frozenset(),
            docs_items=frozenset(),
            categories=frozenset(),
            development_loop="",
            agent_targets=frozenset({"claude"}),
        )

    @classmethod
    def default_agent_targets(cls, catalog: ComponentCatalog) -> frozenset[str]:
        """Return the validated default Agent Target selection."""
        return _default_agent_targets(catalog.agent_target_ids)

    def with_agent_targets(
        self,
        catalog: ComponentCatalog,
        agent_targets: frozenset[str],
    ) -> ProjectSelection:
        """Return this content selection with its Agent Target answer replaced."""
        return self.from_items(
            catalog,
            skills=self.skills,
            mcp=self.mcp,
            docs_items=self.docs_items,
            agent_targets=agent_targets,
        )

    @classmethod
    def empty(cls) -> ProjectSelection:
        """Return deliberately malformed intent for inspection and lifecycle tests."""
        return cls._create(
            skills=frozenset(),
            mcp=frozenset(),
            docs_items=frozenset(),
            categories=frozenset(),
            development_loop="",
            agent_targets=frozenset(),
        )

    @classmethod
    def from_items(
        cls,
        catalog: ComponentCatalog,
        *,
        skills: frozenset[str] = frozenset(),
        mcp: frozenset[str] = frozenset(),
        docs_items: frozenset[str] = frozenset(),
        agent_targets: frozenset[str] | None = None,
        require_development_loop: bool = True,
        handoff: bool = False,
    ) -> ProjectSelection:
        """Build selection intent; ``None`` retains the lifecycle-fixture all-target sentinel.

        Product construction paths must pass their Agent Target intent explicitly.
        `recorded` reconstructs with ``require_development_loop=False``.
        """
        _ = handoff  # Compatibility for internal v0.8 lifecycle fixtures only.
        return cls._from_items(
            catalog,
            skills=skills,
            mcp=mcp,
            docs_items=docs_items,
            agent_targets=agent_targets,
            require_development_loop=require_development_loop,
        )

    @classmethod
    def _from_items(
        cls,
        catalog: ComponentCatalog,
        *,
        skills: frozenset[str],
        mcp: frozenset[str],
        docs_items: frozenset[str],
        agent_targets: frozenset[str] | None,
        require_development_loop: bool,
    ) -> ProjectSelection:
        _validate_items("skills", skills, catalog)
        _validate_items("mcp", mcp, catalog)
        _validate_items("docs", docs_items, catalog)
        resolved_targets = (
            catalog.agent_target_ids if agent_targets is None else agent_targets
        )
        _validate_agent_targets(resolved_targets, catalog)
        resolved_skills, development_loop = _resolve_development_loop(
            catalog,
            skills,
            required=require_development_loop,
        )
        resolved_skills = _resolve_requirements("skills", resolved_skills, catalog)
        resolved_mcp = _resolve_requirements("mcp", mcp, catalog)
        resolved_docs = _resolve_requirements("docs", docs_items, catalog)
        resolved_categories = _categories_for_items(
            catalog,
            skills=resolved_skills,
            mcp=resolved_mcp,
            docs=resolved_docs,
        )
        return cls._create(
            skills=resolved_skills,
            mcp=resolved_mcp,
            docs_items=resolved_docs,
            categories=resolved_categories,
            development_loop=development_loop,
            agent_targets=resolved_targets,
        )

    @classmethod
    def all(
        cls,
        catalog: ComponentCatalog,
        *,
        development_loop: str | None = None,
    ) -> ProjectSelection:
        chosen_loop = (
            development_loop
            if development_loop is not None
            else catalog.default_development_loop
        )
        return cls.from_items(
            catalog,
            skills=frozenset(
                item.id
                for item in catalog.get("skills", ())
                if item.kind != "development-loop" or item.id == chosen_loop
            ),
            mcp=catalog.item_ids("mcp"),
            docs_items=catalog.item_ids("docs"),
            agent_targets=catalog.agent_target_ids,
        )

    @classmethod
    def default_set(cls, catalog: ComponentCatalog) -> ProjectSelection:
        """Resolve the manifest-declared lean selection used by ``--yes``."""
        default_set = catalog.default_set
        if default_set is None:
            raise InvalidArgumentsError("catalog does not declare a Default Set")
        selected_by_component = catalog.by_component(default_set.enhancements)
        loop_skills = selected_by_component["skills"] | frozenset(
            {default_set.development_loop}
        )
        return cls.from_items(
            catalog,
            skills=loop_skills,
            mcp=selected_by_component["mcp"],
            docs_items=selected_by_component["docs"],
            agent_targets=cls.default_agent_targets(catalog),
        )

    def items(self, name: str) -> frozenset[str]:
        if name == "skills":
            return self.skills
        if name == "mcp":
            return self.mcp
        if name == "docs":
            return self.docs_items
        raise ValueError(f"unknown selection {name!r}")

    def includes(self, name: str) -> bool:
        return bool(self.items(name))


def _validate_items(
    name: str,
    selected: frozenset[str],
    catalog: ComponentCatalog,
) -> None:
    valid = catalog.item_ids(name)
    unknown = sorted(selected - valid)
    if unknown:
        raise InvalidArgumentsError(
            f"unknown {name} item ids: {unknown!r}; valid ids: {sorted(valid)!r}"
        )


def _resolve_development_loop(
    catalog: ComponentCatalog,
    selected_skills: frozenset[str],
    *,
    required: bool,
) -> tuple[frozenset[str], str]:
    loop_ids = catalog.development_loop_ids
    if not loop_ids:
        return selected_skills, ""
    selected_loops = frozenset(loop_ids) & selected_skills
    if len(selected_loops) > 1:
        raise InvalidArgumentsError(
            f"select exactly one development loop from {sorted(loop_ids)!r}"
        )
    if selected_loops:
        development_loop = next(iter(selected_loops))
    elif not required:
        return selected_skills, ""
    elif len(loop_ids) == 1:
        development_loop = loop_ids[0]
    else:
        development_loop = catalog.default_development_loop
        if development_loop not in loop_ids:
            raise InvalidArgumentsError(
                f"select exactly one development loop from {sorted(loop_ids)!r}"
            )
    return selected_skills | frozenset({development_loop}), development_loop


def _default_agent_targets(valid_ids: frozenset[str]) -> frozenset[str]:
    return _DEFAULT_AGENT_TARGETS & valid_ids


def _validate_agent_targets(
    selected: frozenset[str],
    catalog: ComponentCatalog,
) -> None:
    valid = catalog.agent_target_ids
    standard_agents = frozenset(catalog.standard_compliant_agents)
    for target in sorted(selected):
        if target in standard_agents:
            raise InvalidArgumentsError(
                f"Agent Target {target!r} reads standard '.agents/skills/' directly, "
                "needs no Agent Target, and is already supported."
            )
    unknown = sorted(selected - valid)
    if unknown:
        raise InvalidArgumentsError(
            f"unknown agent target ids: {unknown!r} (run interactively or pass valid targets)"
        )


def _resolve_requirements(
    name: str,
    selected: frozenset[str],
    catalog: ComponentCatalog,
) -> frozenset[str]:
    item_by_id = {item.id: item for item in catalog.get(name, ())}
    resolved = set(selected)
    pending = sorted(selected)
    while pending:
        item_id = pending.pop(0)
        for required_id in item_by_id[item_id].requires:
            if required_id not in resolved:
                resolved.add(required_id)
                pending.append(required_id)
    return frozenset(resolved)


def _categories_for_items(
    catalog: ComponentCatalog,
    *,
    skills: frozenset[str],
    mcp: frozenset[str],
    docs: frozenset[str],
) -> frozenset[str]:
    selected_by_component = dict(zip(CATALOG_COMPONENTS, (skills, mcp, docs)))
    categories = {
        item.category
        for component, selected in selected_by_component.items()
        for item in catalog.get(component, ())
        if item.id in selected and item.category
    }
    return frozenset(categories)


@dataclass(frozen=True)
class Answers:
    """Complete generation intent behind one invariant-preserving interface."""

    project_name: str
    target_dir: Path
    selection: ProjectSelection = field(default_factory=ProjectSelection.optional_only)
    assume_yes: bool = False

    def __post_init__(self) -> None:
        validate_project_name(self.project_name)

    def items(self, name: str) -> frozenset[str]:
        return self.selection.items(name)

    def includes(self, name: str) -> bool:
        return self.selection.includes(name)

    @property
    def skills_items(self) -> frozenset[str]:
        return self.items("skills")

    @property
    def mcp_items(self) -> frozenset[str]:
        return self.items("mcp")

    @property
    def include_skills(self) -> bool:
        return self.includes("skills")

    @property
    def include_mcp(self) -> bool:
        return self.includes("mcp")

    @property
    def include_docs(self) -> bool:
        return self.includes("docs")

    @property
    def development_loop(self) -> str:
        return self.selection.development_loop

    @property
    def agent_targets(self) -> frozenset[str]:
        return self.selection.agent_targets


@dataclass(frozen=True)
class PartialAnswers:
    """Generation intent whose selection and/or project name may need prompting."""

    project_name: str | None
    target_dir: Path | None
    selection: ProjectSelection | None
    agent_targets: frozenset[str] | None = None
    assume_yes: bool = False

    def __post_init__(self) -> None:
        if self.project_name is not None:
            validate_project_name(self.project_name)
