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
    docs: bool = True
    agents: bool = True

    @classmethod
    def _create(
        cls,
        *,
        skills: frozenset[str],
        mcp: frozenset[str],
        docs: bool,
        agents: bool,
    ) -> ProjectSelection:
        selection = object.__new__(cls)
        object.__setattr__(selection, "skills", skills)
        object.__setattr__(selection, "mcp", mcp)
        object.__setattr__(selection, "docs", docs)
        object.__setattr__(selection, "agents", agents)
        return selection

    @classmethod
    def optional_only(cls) -> ProjectSelection:
        return cls._create(
            skills=frozenset(),
            mcp=frozenset(),
            docs=True,
            agents=True,
        )

    @classmethod
    def empty(cls) -> ProjectSelection:
        return cls._create(
            skills=frozenset(),
            mcp=frozenset(),
            docs=False,
            agents=False,
        )

    @classmethod
    def from_items(
        cls,
        catalog: Mapping[str, tuple[CatalogItem, ...]],
        *,
        skills: frozenset[str] = frozenset(),
        mcp: frozenset[str] = frozenset(),
        docs: bool = True,
        agents: bool = True,
    ) -> ProjectSelection:
        _validate_items("skills", skills, catalog)
        _validate_items("mcp", mcp, catalog)
        return cls._create(
            skills=_resolve_requirements("skills", skills, catalog),
            mcp=_resolve_requirements("mcp", mcp, catalog),
            docs=docs,
            agents=agents,
        )

    @classmethod
    def all(cls, catalog: Mapping[str, tuple[CatalogItem, ...]]) -> ProjectSelection:
        return cls._create(
            skills=frozenset(item.id for item in catalog.get("skills", ())),
            mcp=frozenset(item.id for item in catalog.get("mcp", ())),
            docs=True,
            agents=True,
        )

    @classmethod
    def from_flags(
        cls,
        *,
        catalog: Mapping[str, tuple[CatalogItem, ...]],
        skills: str | None,
        mcp: str | None,
        no_skills: bool,
        no_mcp: bool,
        no_docs: bool,
        no_agents: bool,
    ) -> ProjectSelection | None:
        """Resolve CLI selection flags, or return ``None`` when unspecified."""
        explicit = no_skills or no_mcp or no_docs or no_agents or skills is not None or mcp is not None
        if not explicit:
            return None

        all_skills = frozenset(item.id for item in catalog.get("skills", ()))
        all_mcp = frozenset(item.id for item in catalog.get("mcp", ()))
        return cls.from_items(
            catalog,
            skills=_resolve_items("skills", skills, no_skills, all_skills),
            mcp=_resolve_items("mcp", mcp, no_mcp, all_mcp),
            docs=not no_docs,
            agents=not no_agents,
        )

    def items(self, name: str) -> frozenset[str]:
        if name == "skills":
            return self.skills
        if name == "mcp":
            return self.mcp
        raise ValueError(f"catalog selection {name!r} has no items")

    def includes(self, name: str) -> bool:
        if name in {"skills", "mcp"}:
            return bool(self.items(name))
        if name == "docs":
            return self.docs
        if name == "agents":
            return self.agents
        raise ValueError(f"unknown selection {name!r}")


def _resolve_items(
    name: str,
    raw_value: str | None,
    no_flag: bool,
    catalog_ids: frozenset[str],
) -> frozenset[str]:
    if no_flag and raw_value is not None and raw_value.strip().lower() != "none":
        raise InvalidArgumentsError(
            f"--no-{name} conflicts with --{name} {raw_value!r}; use one."
        )
    if no_flag or (raw_value is not None and raw_value.strip().lower() == "none"):
        return frozenset()
    if raw_value is None or raw_value.strip().lower() == "all":
        return catalog_ids

    requested = frozenset(item.strip() for item in raw_value.split(",") if item.strip())
    if not requested:
        raise InvalidArgumentsError(f"empty item selection for --{name}")
    unknown = sorted(requested - catalog_ids)
    if unknown:
        raise InvalidArgumentsError(
            f"unknown {name} item ids: {unknown!r}; valid ids: {sorted(catalog_ids)!r}"
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
    def include_agents(self) -> bool:
        return self.includes("agents")


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
