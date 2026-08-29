"""Flag-string adapters that write Generation Intent (ADR-004)."""

from __future__ import annotations

from collections.abc import Mapping

from dev_ready.errors import InvalidArgumentsError
from dev_ready.intent import ProjectSelection
from dev_ready.manifest.models import RETIRED_LOOP_ITEM_IDS, ComponentCatalog

_RENAMED_DEVELOPMENT_LOOP_ID = "spec-loop"


def selection_from_flags(
    *,
    catalog: ComponentCatalog,
    categories: str | None,
    category_items: Mapping[str, str | None],
    development_loop: str | None = None,
) -> ProjectSelection | None:
    """Resolve CLI selection flags, or return ``None`` when unspecified."""
    explicit_category_items = {
        category: value
        for category, value in category_items.items()
        if value is not None
    }
    content_explicit = (
        categories is not None
        or bool(explicit_category_items)
        or development_loop is not None
    )
    if not content_explicit:
        return None

    valid_categories = catalog.category_ids
    unknown_categories = sorted(set(category_items) - valid_categories)
    if unknown_categories:
        raise InvalidArgumentsError(
            f"unknown Category ids: {unknown_categories!r}; "
            f"valid ids: {sorted(valid_categories)!r}"
        )
    requested_categories = (
        frozenset(explicit_category_items)
        if categories is None
        else _resolve_category_ids(categories, valid_categories)
    )
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

    default_enhancements = (
        catalog.default_set.enhancements
        if categories is None and catalog.default_set is not None
        else ()
    )
    item_categories = {item.id: item.category for item in catalog.all_items()}
    selected_ids = {
        item_id
        for item_id in default_enhancements
        if item_categories[item_id] not in explicit_category_items
    }
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
        catalog,
    )

    return ProjectSelection.from_items(
        catalog,
        skills=selected_by_component["skills"]
        | (frozenset({selected_loop}) if selected_loop else frozenset()),
        mcp=selected_by_component["mcp"],
        docs_items=selected_by_component["docs"],
        agent_targets=ProjectSelection.default_agent_targets(catalog),
    )


def agent_targets_from_flag(
    catalog: ComponentCatalog,
    raw_value: str | None,
) -> frozenset[str]:
    """Resolve one Agent Target flag independently of catalog content."""
    valid_ids = catalog.agent_target_ids
    if raw_value is None:
        return ProjectSelection.default_agent_targets(catalog)
    if raw_value.strip().lower() == "all":
        return valid_ids
    if raw_value.strip().lower() == "none":
        return frozenset()
    requested = frozenset(item.strip() for item in raw_value.split(",") if item.strip())
    if not requested:
        raise InvalidArgumentsError("empty agent target selection for --agents")
    standard_agents = frozenset(catalog.standard_compliant_agents)
    for target in sorted(requested):
        if target in standard_agents:
            raise InvalidArgumentsError(
                f"Agent Target {target!r} reads standard '.agents/skills/' directly, "
                "needs no Agent Target, and is already supported."
            )
    unknown = sorted(requested - valid_ids)
    if unknown:
        raise InvalidArgumentsError(
            f"unknown agent target ids: {unknown!r} (run interactively or pass valid targets)"
        )
    return requested


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
    catalog: ComponentCatalog,
) -> str:
    if requested is None:
        return ""
    if requested == _RENAMED_DEVELOPMENT_LOOP_ID:
        raise InvalidArgumentsError(
            f"Engineering Flow id {requested!r} was renamed to "
            f"{catalog.default_development_loop!r}"
        )
    if requested in {flow.id for flow in catalog.announced_loops}:
        raise InvalidArgumentsError(
            f"Engineering Flow {requested!r} is not yet available"
        )
    valid_ids = catalog.development_loop_ids
    if requested not in valid_ids:
        raise InvalidArgumentsError(
            f"unknown Engineering Flow id {requested!r}; valid ids: {sorted(valid_ids)!r}"
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
            "Engineering Flow"
        )
    unknown = sorted(requested - valid_ids)
    if unknown:
        raise InvalidArgumentsError(
            f"unknown {label} item ids: {unknown!r}; valid ids: {sorted(valid_ids)!r}"
        )
    return requested
