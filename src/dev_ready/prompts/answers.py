"""Canonical generation intent shared by flag and prompt adapters (ADR-004)."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from dev_ready.errors import InvalidArgumentsError
from dev_ready.manifest.models import (
    CATALOG_COMPONENTS,
    ComponentCatalog,
    RETIRED_LOOP_ITEM_IDS,
)

_PROJECT_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]*$")


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
        categories: frozenset[str] | None = None,
        agent_targets: frozenset[str] | None = None,
        handoff: bool = False,
    ) -> ProjectSelection:
        _ = handoff  # Compatibility for internal v0.8 lifecycle fixtures only.
        return cls._from_items(
            catalog,
            skills=skills,
            mcp=mcp,
            docs_items=docs_items,
            categories=categories,
            agent_targets=agent_targets,
            require_development_loop=True,
        )

    @classmethod
    def from_recorded_items(
        cls,
        catalog: ComponentCatalog,
        *,
        skills: frozenset[str],
        mcp: frozenset[str],
        docs_items: frozenset[str],
        agent_targets: frozenset[str] | None = None,
    ) -> ProjectSelection:
        """Reconstruct existing intent without applying Phase 4 migration policy."""
        return cls._from_items(
            catalog,
            skills=skills,
            mcp=mcp,
            docs_items=docs_items,
            categories=None,
            agent_targets=agent_targets,
            require_development_loop=False,
        )

    @classmethod
    def _from_items(
        cls,
        catalog: ComponentCatalog,
        *,
        skills: frozenset[str],
        mcp: frozenset[str],
        docs_items: frozenset[str],
        categories: frozenset[str] | None,
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
        resolved_categories = (
            _categories_for_items(
                catalog,
                skills=resolved_skills,
                mcp=mcp,
                docs=docs_items,
            )
            if categories is None
            else categories
            | (frozenset({"dev"}) if development_loop else frozenset())
        )
        return cls._create(
            skills=_resolve_requirements("skills", resolved_skills, catalog),
            mcp=_resolve_requirements("mcp", mcp, catalog),
            docs_items=_resolve_requirements("docs", docs_items, catalog),
            categories=resolved_categories,
            development_loop=development_loop,
            agent_targets=resolved_targets,
        )

    @classmethod
    def all(cls, catalog: ComponentCatalog) -> ProjectSelection:
        default_loop = catalog.default_development_loop
        return cls.from_items(
            catalog,
            skills=frozenset(
                item.id
                for item in catalog.get("skills", ())
                if item.kind != "development-loop" or item.id == default_loop
            ),
            mcp=catalog.item_ids("mcp"),
            docs_items=catalog.item_ids("docs"),
            categories=catalog.category_ids,
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
            agent_targets=catalog.agent_target_ids,
        )

    @classmethod
    def from_flags(
        cls,
        *,
        catalog: ComponentCatalog,
        categories: str | None,
        category_items: Mapping[str, str | None],
        agents: str | None = None,
        development_loop: str | None = None,
    ) -> ProjectSelection | None:
        """Resolve CLI selection flags, or return ``None`` when unspecified."""
        explicit_category_items = {
            category: value
            for category, value in category_items.items()
            if value is not None
        }
        explicit = (
            categories is not None
            or bool(explicit_category_items)
            or agents is not None
            or development_loop is not None
        )
        if not explicit:
            return None

        valid_categories = catalog.category_ids
        unknown_categories = sorted(set(category_items) - valid_categories)
        if unknown_categories:
            raise InvalidArgumentsError(
                f"unknown Category ids: {unknown_categories!r}; "
                f"valid ids: {sorted(valid_categories)!r}"
            )
        requested_categories = _resolve_category_ids(categories, valid_categories)
        selected_categories = requested_categories | (
            frozenset({"dev"}) if "dev" in valid_categories else frozenset()
        )
        if categories is not None:
            for category in explicit_category_items:
                if category != "dev" and category not in requested_categories:
                    raise InvalidArgumentsError(
                        f"--{category} conflicts with --categories {categories!r}; "
                        "select the Category or remove its item flag."
                    )

        selected_ids: set[str] = set()
        for category in selected_categories:
            category_ids = catalog.ids_in_category(category)
            if category == "dev":
                category_ids -= frozenset(catalog.development_loop_ids)
            raw_items = explicit_category_items.get(category)
            if category == "dev" and category not in requested_categories and raw_items is None:
                raw_items = "none"
            selected_ids.update(
                _resolve_category_items(
                    category,
                    raw_items,
                    category_ids,
                )
            )
        selected_by_component = catalog.by_component(selected_ids)
        selected_loop = _resolve_development_loop_id(
            development_loop,
            catalog.development_loop_ids,
        )

        return cls.from_items(
            catalog,
            skills=selected_by_component["skills"]
            | (frozenset({selected_loop}) if selected_loop else frozenset()),
            mcp=selected_by_component["mcp"],
            docs_items=selected_by_component["docs"],
            categories=selected_categories,
            agent_targets=_resolve_agent_targets(agents, catalog.agent_target_ids),
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


def _resolve_category_ids(
    raw_value: str | None,
    valid_ids: frozenset[str],
) -> frozenset[str]:
    if raw_value is not None and raw_value.strip().lower() == "none":
        return frozenset()
    if raw_value is None or raw_value.strip().lower() == "all":
        return valid_ids

    requested = frozenset(item.strip() for item in raw_value.split(",") if item.strip())
    if not requested:
        raise InvalidArgumentsError("empty Category selection for --categories")
    unknown = sorted(requested - valid_ids)
    if unknown:
        raise InvalidArgumentsError(
            f"unknown Category ids: {unknown!r}; valid ids: {sorted(valid_ids)!r}"
        )
    return requested


def _resolve_development_loop_id(
    requested: str | None,
    valid_ids: tuple[str, ...],
) -> str:
    if requested is None:
        return ""
    if requested not in valid_ids:
        raise InvalidArgumentsError(
            f"unknown development loop id {requested!r}; valid ids: {sorted(valid_ids)!r}"
        )
    return requested


def _resolve_category_items(
    category: str,
    raw_value: str | None,
    valid_ids: frozenset[str],
) -> frozenset[str]:
    if raw_value is None or raw_value.strip().lower() == "all":
        return valid_ids
    if raw_value.strip().lower() == "none":
        return frozenset()
    requested = frozenset(item.strip() for item in raw_value.split(",") if item.strip())
    label = category.replace("-", " ").title()
    if not requested:
        raise InvalidArgumentsError(f"empty item selection for --{category}")
    retired = sorted(requested & RETIRED_LOOP_ITEM_IDS)
    if retired:
        joined = ", ".join(repr(item_id) for item_id in retired)
        raise InvalidArgumentsError(
            f"retired Dev item id(s) {joined}; each is now part of the mandatory "
            "Dev development loop 'spec-loop'"
        )
    unknown = sorted(requested - valid_ids)
    if unknown:
        raise InvalidArgumentsError(
            f"unknown {label} item ids: {unknown!r}; valid ids: {sorted(valid_ids)!r}"
        )
    return requested


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


def _resolve_agent_targets(
    raw_value: str | None,
    valid_ids: frozenset[str],
) -> frozenset[str]:
    if raw_value is None or raw_value.strip().lower() == "all":
        return valid_ids
    if raw_value.strip().lower() == "none":
        return frozenset()
    requested = frozenset(item.strip() for item in raw_value.split(",") if item.strip())
    if not requested:
        raise InvalidArgumentsError("empty agent target selection for --agents")
    unknown = sorted(requested - valid_ids)
    if unknown:
        raise InvalidArgumentsError(
            f"unknown agent target ids: {unknown!r}; valid ids: {sorted(valid_ids)!r}"
        )
    return requested


def _validate_agent_targets(
    selected: frozenset[str],
    catalog: ComponentCatalog,
) -> None:
    valid = catalog.agent_target_ids
    unknown = sorted(selected - valid)
    if unknown:
        raise InvalidArgumentsError(
            f"unknown agent target ids: {unknown!r}; valid ids: {sorted(valid)!r}"
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
    def agent_targets(self) -> frozenset[str]:
        return self.selection.agent_targets


@dataclass(frozen=True)
class PartialAnswers:
    """Generation intent whose selection and/or project name may need prompting."""

    project_name: str | None
    target_dir: Path | None
    selection: ProjectSelection | None
    assume_yes: bool = False

    def __post_init__(self) -> None:
        if self.project_name is not None:
            validate_project_name(self.project_name)
