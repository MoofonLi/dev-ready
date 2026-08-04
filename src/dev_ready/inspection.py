"""Deep, read-only inspection of generated-project structure."""

from __future__ import annotations

from dataclasses import dataclass
from importlib import resources
from importlib.resources.abc import Traversable
from pathlib import Path

from dev_ready.agent_targets import TargetProjection, canonical_skill_names, project_targets
from dev_ready.catalog_effects import CatalogEffectError
from dev_ready.manifest import CATALOG_COMPONENTS, CatalogItem, ComponentCatalog
from dev_ready.overlay.rendering import TEMPLATE_SUFFIX
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

_CORE_OVERLAY_FILES = ("AGENTS.md", "README.md")


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
    catalog: ComponentCatalog,
    expectation: ProjectExpectation,
) -> tuple[ProjectIssue, ...]:
    """Return every structural mismatch through one local-filesystem seam."""
    root = project_dir.resolve()
    issues: list[ProjectIssue] = []
    required_development_loop = expectation.selection.development_loop
    if expectation.exact_catalog_selection and not required_development_loop:
        required_development_loop = catalog.default_development_loop
    # Every declared target, not only the selected ones: generation must also
    # observe that an unselected Agent Target left nothing behind.
    declared = project_targets(catalog, catalog.agent_target_ids)

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

    for relative in _CORE_OVERLAY_FILES:
        if not (root / relative).exists():
            issues.append(
                ProjectIssue(
                    "missing overlay file",
                    f"required file {relative!r} is missing",
                )
            )
    if not (root / "docs").exists():
        issues.append(
            ProjectIssue(
                "missing overlay directory",
                "documentation directory 'docs/' is missing",
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

    for name in CATALOG_COMPONENTS:
        selected = expectation.selection.items(name)
        for item in catalog.get(name, ()):
            if name == "mcp":
                _inspect_target_mcp_item(
                    root,
                    item,
                    declared,
                    expectation.selection,
                    expectation.exact_catalog_selection,
                    issues,
                )
                continue
            is_development_loop = item.kind == "development-loop"
            expected = item.id in selected or (
                is_development_loop and item.id == required_development_loop
            )
            if expected or expectation.exact_catalog_selection:
                item_group = "development loop" if is_development_loop else name
                _inspect_item_paths(root, item_group, item, expected, issues)
                _inspect_item_effect(root, item_group, item, expected, issues)

    _inspect_agent_target_artifacts(
        root,
        catalog,
        expectation.selection,
        required_development_loop,
        issues,
    )

    return tuple(issues)


def _inspect_target_mcp_item(
    root: Path,
    item: CatalogItem,
    declared: TargetProjection,
    selection: ProjectSelection,
    exact_catalog_selection: bool,
    issues: list[ProjectIssue],
) -> None:
    for target, retargeted in declared.retarget_mcp(item):
        expected = item.id in selection.mcp and target.id in selection.agent_targets
        if not expected and not exact_catalog_selection:
            continue
        _inspect_item_paths(root, "mcp", retargeted, expected, issues)
        _inspect_item_effect(root, "mcp", retargeted, expected, issues)


def _inspect_agent_target_artifacts(
    root: Path,
    catalog: ComponentCatalog,
    selection: ProjectSelection,
    required_development_loop: str,
    issues: list[ProjectIssue],
) -> None:
    selected = project_targets(catalog, selection.agent_targets)
    skill_names = canonical_skill_names(
        catalog,
        selection.skills | frozenset({required_development_loop}),
    )
    for target in selected.skill_targets:
        expected_paths: list[Path] = []
        if target.rules_file is not None:
            expected_paths.append(Path(target.rules_file))
        if selection.mcp and target.mcp_file is not None:
            expected_paths.append(Path(target.mcp_file))
        expected_paths.extend(
            selected.stub_path(target, skill_name) for skill_name in skill_names
        )
        for relative in expected_paths:
            path_text = relative.as_posix()
            artifact = root / relative
            if not _is_safe(root, artifact):
                issues.append(_unsafe_path(path_text))
            elif artifact.is_symlink():
                issues.append(
                    ProjectIssue(
                        "invalid agent target artifact",
                        f"agent target {target.id!r} artifact {path_text!r} must not be a symbolic link",
                    )
                )
            elif not artifact.is_file():
                issues.append(
                    ProjectIssue(
                        "missing agent target artifact",
                        f"agent target {target.id!r} artifact {path_text!r} is missing",
                    )
                )


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
        if present and target.is_symlink():
            issues.append(
                ProjectIssue(
                    "invalid item path",
                    f"selected {name} item {item.id!r} path {item_path.dest!r} must not be a symbolic link",
                )
            )
            continue
        if expected and not present:
            detail = f"selected {name} item {item.id!r} path {item_path.dest!r} is missing"
            verification = (
                f"selected {name} item {item.id!r} is missing its path {item_path.dest!r}"
            )
            issues.append(ProjectIssue("missing item path", detail, verification))
        elif expected:
            source = resources.files("dev_ready").joinpath(
                "templates", *item_path.src.split("/")
            )
            if source.is_dir():
                if not target.is_dir():
                    detail = (
                        f"selected {name} item {item.id!r} path {item_path.dest!r} "
                        "must be a directory"
                    )
                    issues.append(ProjectIssue("invalid item path", detail, detail))
                    continue
                for relative in _resource_files(source):
                    expected_file = target.joinpath(*relative.parts)
                    if not _is_safe(root, expected_file) or not expected_file.is_file():
                        asset = (Path(item_path.dest) / relative).as_posix()
                        detail = (
                            f"selected {name} item {item.id!r} asset {asset!r} is missing"
                        )
                        issues.append(ProjectIssue("missing item asset", detail, detail))
            elif source.is_file() and not target.is_file():
                detail = (
                    f"selected {name} item {item.id!r} asset {item_path.dest!r} is missing"
                )
                issues.append(ProjectIssue("missing item asset", detail, detail))
        elif not expected and present:
            detail = f"unselected {name} item {item.id!r} left path {item_path.dest!r} in the output"
            issues.append(ProjectIssue("unexpected item path", detail, detail))


def _resource_files(
    directory: Traversable, prefix: Path = Path()
) -> tuple[Path, ...]:
    files: list[Path] = []
    for entry in sorted(directory.iterdir(), key=lambda item: item.name):
        name = entry.name.removesuffix(TEMPLATE_SUFFIX) if not entry.is_dir() else entry.name
        relative = prefix / name
        if entry.is_dir():
            files.extend(_resource_files(entry, relative))
        elif entry.is_file():
            files.append(relative)
    return tuple(files)


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
