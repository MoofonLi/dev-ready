"""Canonical generation intent shared by flag and prompt adapters (ADR-004)."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from dev_ready.errors import InvalidArgumentsError
from dev_ready.manifest.models import CatalogItem

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
    agent_targets: frozenset[str] = frozenset()
    docs: bool = True

    @classmethod
    def _create(
        cls,
        *,
        skills: frozenset[str],
        mcp: frozenset[str],
        docs_items: frozenset[str],
        categories: frozenset[str],
        agent_targets: frozenset[str],
        docs: bool,
    ) -> ProjectSelection:
        selection = object.__new__(cls)
        object.__setattr__(selection, "skills", skills)
        object.__setattr__(selection, "mcp", mcp)
        object.__setattr__(selection, "docs_items", docs_items)
        object.__setattr__(selection, "categories", categories)
        object.__setattr__(selection, "agent_targets", agent_targets)
        object.__setattr__(selection, "docs", docs)
        return selection

    @classmethod
    def optional_only(cls) -> ProjectSelection:
        return cls._create(
            skills=frozenset(),
            mcp=frozenset(),
            docs_items=frozenset(),
            categories=frozenset(),
            agent_targets=frozenset({"claude"}),
            docs=True,
        )

    @classmethod
    def empty(cls) -> ProjectSelection:
        return cls._create(
            skills=frozenset(),
            mcp=frozenset(),
            docs_items=frozenset(),
            categories=frozenset(),
            agent_targets=frozenset(),
            docs=False,
        )

    @classmethod
    def from_items(
        cls,
        catalog: Mapping[str, tuple[CatalogItem, ...]],
        *,
        skills: frozenset[str] = frozenset(),
        mcp: frozenset[str] = frozenset(),
        docs_items: frozenset[str] | None = None,
        categories: frozenset[str] | None = None,
        agent_targets: frozenset[str] | None = None,
        docs: bool = True,
        handoff: bool = False,
    ) -> ProjectSelection:
        _ = handoff  # Compatibility for internal v0.8 lifecycle fixtures only.
        _validate_items("skills", skills, catalog)
        _validate_items("mcp", mcp, catalog)
        resolved_docs_items = (
            frozenset(item.id for item in catalog.get("docs", ()))
            if docs and docs_items is None
            else (docs_items or frozenset())
        )
        _validate_items("docs", resolved_docs_items, catalog)
        resolved_targets = _all_agent_target_ids(catalog) if agent_targets is None else agent_targets
        _validate_agent_targets(resolved_targets, catalog)
        resolved_categories = (
            _categories_for_items(
                catalog,
                skills=skills,
                mcp=mcp,
                docs=resolved_docs_items,
                include_legacy_docs=docs,
            )
            if categories is None
            else categories
        )
        return cls._create(
            skills=_resolve_requirements("skills", skills, catalog),
            mcp=_resolve_requirements("mcp", mcp, catalog),
            docs_items=_resolve_requirements("docs", resolved_docs_items, catalog),
            categories=resolved_categories,
            agent_targets=resolved_targets,
            docs=docs,
        )

    @classmethod
    def all(cls, catalog: Mapping[str, tuple[CatalogItem, ...]]) -> ProjectSelection:
        return cls._create(
            skills=frozenset(item.id for item in catalog.get("skills", ())),
            mcp=frozenset(item.id for item in catalog.get("mcp", ())),
            docs_items=frozenset(item.id for item in catalog.get("docs", ())),
            categories=frozenset(getattr(catalog, "categories", {})),
            agent_targets=_all_agent_target_ids(catalog),
            docs=True,
        )

    @classmethod
    def from_flags(
        cls,
        *,
        catalog: Mapping[str, tuple[CatalogItem, ...]],
        categories: str | None,
        category_items: Mapping[str, str | None],
        agents: str | None = None,
    ) -> ProjectSelection | None:
        """Resolve CLI selection flags, or return ``None`` when unspecified."""
        explicit_category_items = {
            category: value
            for category, value in category_items.items()
            if value is not None
        }
        explicit = categories is not None or bool(explicit_category_items) or agents is not None
        if not explicit:
            return None

        valid_categories = frozenset(getattr(catalog, "categories", {}))
        unknown_categories = sorted(set(category_items) - valid_categories)
        if unknown_categories:
            raise InvalidArgumentsError(
                f"unknown Category ids: {unknown_categories!r}; "
                f"valid ids: {sorted(valid_categories)!r}"
            )
        selected_categories = _resolve_category_ids(categories, valid_categories)
        if categories is not None:
            for category in explicit_category_items:
                if category not in selected_categories:
                    raise InvalidArgumentsError(
                        f"--{category} conflicts with --categories {categories!r}; "
                        "select the Category or remove its item flag."
                    )

        selected_ids: set[str] = set()
        for category in selected_categories:
            category_ids = frozenset(
                item.id
                for component in ("skills", "mcp", "docs")
                for item in catalog.get(component, ())
                if item.category == category
            )
            selected_ids.update(
                _resolve_category_items(
                    category,
                    explicit_category_items.get(category),
                    category_ids,
                )
            )
        selected_by_component = {
            component: frozenset(
                item.id
                for item in catalog.get(component, ())
                if item.id in selected_ids
            )
            for component in ("skills", "mcp", "docs")
        }

        return cls.from_items(
            catalog,
            skills=selected_by_component["skills"],
            mcp=selected_by_component["mcp"],
            docs_items=selected_by_component["docs"],
            categories=selected_categories,
            agent_targets=_resolve_agent_targets(agents, _all_agent_target_ids(catalog)),
            docs=bool(selected_by_component["docs"]),
        )

    def items(self, name: str) -> frozenset[str]:
        if name == "skills":
            return self.skills
        if name == "mcp":
            return self.mcp
        if name == "docs":
            return self.docs_items
        raise ValueError(f"catalog selection {name!r} has no items")

    def includes(self, name: str) -> bool:
        if name in {"skills", "mcp"}:
            return bool(self.items(name))
        if name == "docs":
            return self.docs
        raise ValueError(f"unknown selection {name!r}")


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
    unknown = sorted(requested - valid_ids)
    if unknown:
        raise InvalidArgumentsError(
            f"unknown {label} item ids: {unknown!r}; valid ids: {sorted(valid_ids)!r}"
        )
    return requested


def _validate_items(
    name: str,
    selected: frozenset[str],
    catalog: Mapping[str, tuple[CatalogItem, ...]],
) -> None:
    valid = frozenset(item.id for item in catalog.get(name, ()))
    unknown = sorted(selected - valid)
    if unknown:
        raise InvalidArgumentsError(
            f"unknown {name} item ids: {unknown!r}; valid ids: {sorted(valid)!r}"
        )


def _all_agent_target_ids(
    catalog: Mapping[str, tuple[CatalogItem, ...]],
) -> frozenset[str]:
    targets = getattr(catalog, "agent_targets", {})
    return frozenset(targets)


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
    catalog: Mapping[str, tuple[CatalogItem, ...]],
) -> None:
    valid = _all_agent_target_ids(catalog)
    unknown = sorted(selected - valid)
    if unknown:
        raise InvalidArgumentsError(
            f"unknown agent target ids: {unknown!r}; valid ids: {sorted(valid)!r}"
        )


def _resolve_requirements(
    name: str,
    selected: frozenset[str],
    catalog: Mapping[str, tuple[CatalogItem, ...]],
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
    catalog: Mapping[str, tuple[CatalogItem, ...]],
    *,
    skills: frozenset[str],
    mcp: frozenset[str],
    docs: frozenset[str],
    include_legacy_docs: bool,
) -> frozenset[str]:
    selected_by_component = {"skills": skills, "mcp": mcp, "docs": docs}
    categories = {
        item.category
        for component, selected in selected_by_component.items()
        for item in catalog.get(component, ())
        if item.id in selected and item.category
    }
    if include_legacy_docs and not catalog.get("docs"):
        categories.add("design")
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
