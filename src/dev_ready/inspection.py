"""Deep, read-only inspection of generated-project structure."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from dev_ready.catalog_effects import CatalogEffectError
from dev_ready.manifest import CatalogItem
from dev_ready.prompts import ProjectSelection

REQUIRED_UPSTREAM_PATHS: tuple[str, ...] = (
    "backend",
    "frontend",
    "compose.yml",
    "compose.override.yml",
    ".env",
    "LICENSE",
)

REQUIRED_OVERLAY_PATHS: tuple[str, ...] = (".dev-ready.json",)

FORBIDDEN_PATHS: tuple[str, ...] = (
    ".git",
    "copier.yml",
    "copier.yaml",
    ".copier",
    ".copier-answers.yml",
)

_CORE_OVERLAY_FILES = ("CLAUDE.md", "README.md")


@dataclass(frozen=True)
class ProjectExpectation:
    """Structural state expected by one lifecycle policy."""

    selection: ProjectSelection
    exact_catalog_selection: bool
    require_lifecycle_overlay: bool

    @classmethod
    def generation(cls, selection: ProjectSelection) -> ProjectExpectation:
        return cls(
            selection=selection,
            exact_catalog_selection=True,
            require_lifecycle_overlay=False,
        )

    @classmethod
    def lifecycle(cls, selection: ProjectSelection) -> ProjectExpectation:
        return cls(
            selection=selection,
            exact_catalog_selection=False,
            require_lifecycle_overlay=True,
        )


@dataclass(frozen=True)
class ProjectIssue:
    """One observed mismatch, independent of CLI error/report policy."""

    category: str
    detail: str
    verification_detail: str | None = None

    @property
    def verification_message(self) -> str:
        return self.verification_detail or self.detail


def inspect_project(
    project_dir: Path,
    catalog: Mapping[str, tuple[CatalogItem, ...]],
    expectation: ProjectExpectation,
) -> tuple[ProjectIssue, ...]:
    """Return every structural mismatch through one local-filesystem seam."""
    root = project_dir.resolve()
    issues: list[ProjectIssue] = []

    for relative in REQUIRED_UPSTREAM_PATHS:
        target = root / relative
        if not _is_safe(root, target):
            issues.append(_unsafe_path(relative))
        elif not target.exists():
            issues.append(
                ProjectIssue(
                    "missing upstream path",
                    f"required path {relative!r} is missing",
                    f"generated project is missing expected upstream path {relative!r}. "
                    "Likely cause: the upstream layout changed at the manifest-pinned "
                    "commit. Action: file an issue against dev-ready, or do not use this pin.",
                )
            )

    for relative in REQUIRED_OVERLAY_PATHS:
        target = root / relative
        if not _is_safe(root, target):
            issues.append(_unsafe_path(relative))
        elif not target.exists():
            issues.append(
                ProjectIssue(
                    "missing overlay path",
                    f"required path {relative!r} is missing",
                    f"generated project is missing required overlay path {relative!r}. "
                    "Likely cause: an overlay/stamp regression.",
                )
            )

    if expectation.require_lifecycle_overlay:
        for relative in _CORE_OVERLAY_FILES:
            if not (root / relative).exists():
                issues.append(
                    ProjectIssue(
                        "missing overlay file",
                        f"required file {relative!r} is missing",
                    )
                )
        if expectation.selection.docs and not (root / "docs").exists():
            issues.append(
                ProjectIssue(
                    "missing overlay directory",
                    "recorded 'docs' selection but 'docs/' directory is missing",
                )
            )
        if expectation.selection.agents and not (root / "docs" / "handoffs").exists():
            issues.append(
                ProjectIssue(
                    "missing overlay directory",
                    "recorded 'agents' selection but 'docs/handoffs/' directory is missing",
                )
            )

    for relative in FORBIDDEN_PATHS:
        if (root / relative).exists():
            issues.append(
                ProjectIssue(
                    "forbidden path present",
                    f"target directory contains forbidden path {relative!r}",
                    f"generated project contains forbidden path {relative!r} — an upstream/Copier "
                    "change reintroduced a template-repo leak (.git worktree or copier.yml). "
                    "Action: file an issue against dev-ready; do not use this pin.",
                )
            )

    for name in ("skills", "mcp"):
        selected = expectation.selection.items(name)
        for item in catalog.get(name, ()):
            expected = item.id in selected
            if expected or expectation.exact_catalog_selection:
                _inspect_item_paths(root, name, item, expected, issues)
                _inspect_item_effect(root, name, item, expected, issues)

    return tuple(issues)


def _inspect_item_paths(
    root: Path,
    name: str,
    item: CatalogItem,
    expected: bool,
    issues: list[ProjectIssue],
) -> None:
    for item_path in item.paths:
        target = root / item_path.dest
        if not _is_safe(root, target):
            issues.append(
                ProjectIssue(
                    "security error",
                    f"item {item.id!r} destination {item_path.dest!r} escapes target directory",
                )
            )
            continue
        present = target.exists()
        if expected and not present:
            detail = f"selected {name} item {item.id!r} path {item_path.dest!r} is missing"
            verification = (
                f"selected {name} item {item.id!r} is missing its path {item_path.dest!r}"
            )
            issues.append(ProjectIssue("missing item path", detail, verification))
        elif not expected and present:
            detail = f"unselected {name} item {item.id!r} left path {item_path.dest!r} in the output"
            issues.append(ProjectIssue("unexpected item path", detail, detail))


def _inspect_item_effect(
    root: Path,
    name: str,
    item: CatalogItem,
    expected: bool,
    issues: list[ProjectIssue],
) -> None:
    if item.effect is None:
        return
    try:
        present = item.effect.is_present(root)
    except CatalogEffectError as error:
        issues.append(ProjectIssue("invalid inject target", str(error), str(error)))
        return
    if expected and not present:
        detail = (
            f"selected {name} item {item.id!r} is missing its inject effect "
            f"in {item.effect.target}"
        )
        issues.append(ProjectIssue("missing inject effect", detail, detail))
    elif not expected and present:
        detail = (
            f"unselected {name} item {item.id!r} left inject effect in {item.effect.target}"
        )
        issues.append(ProjectIssue("unexpected inject effect", detail, detail))


def _is_safe(root: Path, target: Path) -> bool:
    try:
        resolved = target.resolve()
        return resolved == root or root in resolved.parents
    except OSError:
        return False


def _unsafe_path(relative: str) -> ProjectIssue:
    detail = f"unsafe path traversal detected for path {relative!r}"
    return ProjectIssue("security error", detail, detail)
