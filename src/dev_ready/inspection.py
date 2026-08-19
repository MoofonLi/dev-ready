"""Deep, read-only inspection of generated-project structure."""

from __future__ import annotations

from dataclasses import dataclass
from importlib import resources
from importlib.resources.abc import Traversable
from pathlib import Path

from dev_ready.agent_targets import (
    CANONICAL_SKILLS_ROOT,
    TargetProjection,
    canonical_skill_names,
    project_targets,
    skill_names_from_content,
)
from dev_ready.overlay.infrastructure import skill_infrastructure_paths
from dev_ready.skill_links import PathKind, classify_path, has_link_component
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


def _desired_skill_names(
    catalog: ComponentCatalog, selection: ProjectSelection, required_development_loop: str
) -> tuple[str, ...]:
    catalog_names = canonical_skill_names(
        catalog, selection.skills | frozenset({required_development_loop})
    )
    infrastructure = (
        f"{destination.as_posix()}/SKILL.md"
        for _, destination in skill_infrastructure_paths()
    )
    extra = skill_names_from_content(infrastructure)
    return tuple(sorted(set(catalog_names) | set(extra)))


def _inspect_agent_target_artifacts(
    root: Path,
    catalog: ComponentCatalog,
    selection: ProjectSelection,
    required_development_loop: str,
    issues: list[ProjectIssue],
) -> None:
    selected = project_targets(catalog, selection.agent_targets)
    skill_names = _desired_skill_names(catalog, selection, required_development_loop)
    for target in selected.skill_targets:
        expected_files: list[Path] = []
        if target.rules_file is not None:
            expected_files.append(Path(target.rules_file))
        if selection.mcp and target.mcp_file is not None:
            expected_files.append(Path(target.mcp_file))
        for relative in expected_files:
            path_text = relative.as_posix()
            artifact = root / relative
            if not _is_safe(root, artifact):
                issues.append(_unsafe_path(path_text))
            elif artifact.is_symlink() or artifact.is_junction():
                issues.append(
                    ProjectIssue(
                        "invalid agent target artifact",
                        f"agent target {target.id!r} artifact {path_text!r} must not be a link",
                    )
                )
            elif not artifact.is_file():
                issues.append(
                    ProjectIssue(
                        "missing agent target artifact",
                        f"agent target {target.id!r} artifact {path_text!r} is missing",
                    )
                )
        skills_dir = Path(target.skills_dir)
        if has_link_component(root, root / skills_dir):
            issues.append(
                ProjectIssue(
                    "invalid agent target artifact",
                    f"agent target {target.id!r} skills directory {target.skills_dir!r} "
                    "must not be a link",
                )
            )
            continue
        if skill_names:
            _inspect_ignore_anchor(
                root,
                target.id,
                selected.ignore_anchor_path(target),
                skill_names,
                issues,
            )
        for skill_name in skill_names:
            relative = selected.link_path(target, skill_name)
            _inspect_skill_link(root, target.id, relative, skill_name, issues)
        _inspect_stale_skill_links(
            root, target.id, skills_dir, skill_names, issues
        )

    selected_dirs = {target.skills_dir for target in selected.skill_targets}
    declared = project_targets(catalog, catalog.agent_target_ids)
    for target in declared.skill_targets:
        if target.skills_dir in selected_dirs:
            continue
        skills_dir = Path(target.skills_dir)
        if has_link_component(root, root / skills_dir):
            continue
        anchor = declared.ignore_anchor_path(target)
        if classify_path(root / anchor) == PathKind.FILE:
            issues.append(
                ProjectIssue(
                    "invalid agent target artifact",
                    f"agent target {target.id!r} ignore file {anchor.as_posix()!r} "
                    "is an obsolete managed anchor",
                )
            )
        _inspect_stale_skill_links(root, target.id, skills_dir, (), issues)


def _inspect_ignore_anchor(
    root: Path,
    target_id: str,
    relative: Path,
    skill_names: tuple[str, ...],
    issues: list[ProjectIssue],
) -> None:
    path_text = relative.as_posix()
    artifact = root / relative
    kind = classify_path(artifact)
    if kind == PathKind.ABSENT:
        issues.append(
            ProjectIssue(
                "missing agent target artifact",
                f"agent target {target_id!r} ignore file {path_text!r} is missing",
            )
        )
        return
    if kind != PathKind.FILE:
        issues.append(
            ProjectIssue(
                "invalid agent target artifact",
                f"agent target {target_id!r} ignore file {path_text!r} must be a file",
            )
        )
        return
    current_names = [
        line
        for line in artifact.read_text(encoding="utf-8", errors="replace").splitlines()
        if line and not line.startswith("#")
    ]
    missing = [name for name in skill_names if name not in current_names]
    extra = [name for name in current_names if name not in skill_names]
    if missing:
        issues.append(
            ProjectIssue(
                "invalid agent target artifact",
                f"agent target {target_id!r} ignore file {path_text!r} "
                "does not match the desired Skill Link set; "
                f"missing {', '.join(missing)}",
            )
        )
    if extra:
        issues.append(
            ProjectIssue(
                "invalid agent target artifact",
                f"agent target {target_id!r} ignore file {path_text!r} "
                f"has extra generated entries {', '.join(extra)}",
            )
        )


def _inspect_stale_skill_links(
    root: Path,
    target_id: str,
    skills_dir: Path,
    skill_names: tuple[str, ...],
    issues: list[ProjectIssue],
) -> None:
    directory = root / skills_dir
    if classify_path(directory) != PathKind.DIRECTORY:
        return
    desired = set(skill_names)
    for child in directory.iterdir():
        if child.name in desired or child.name == ".gitignore":
            continue
        kind = classify_path(child)
        if kind not in {PathKind.SYMBOLIC_LINK, PathKind.JUNCTION}:
            continue
        path_text = (skills_dir / child.name).as_posix()
        issues.append(
            ProjectIssue(
                "invalid agent target artifact",
                f"agent target {target_id!r} Skill Link {path_text!r} is stale",
            )
        )


def _inspect_skill_link(
    root: Path,
    target_id: str,
    relative: Path,
    skill_name: str,
    issues: list[ProjectIssue],
) -> None:
    path_text = relative.as_posix()
    artifact = root / relative
    kind = classify_path(artifact)
    if kind not in {PathKind.SYMBOLIC_LINK, PathKind.JUNCTION}:
        if kind == PathKind.ABSENT:
            issues.append(
                ProjectIssue(
                    "missing agent target artifact",
                    f"agent target {target_id!r} artifact {path_text!r} is missing",
                )
            )
        else:
            issues.append(
                ProjectIssue(
                    "invalid agent target artifact",
                    f"agent target {target_id!r} artifact {path_text!r} must be a Skill Link",
                )
            )
        return
    canonical = root.joinpath(*CANONICAL_SKILLS_ROOT, skill_name)
    if (
        classify_path(canonical) != PathKind.DIRECTORY
        or classify_path(canonical / "SKILL.md") != PathKind.FILE
    ):
        issues.append(
            ProjectIssue(
                "invalid agent target artifact",
                f"agent target {target_id!r} Skill Link {path_text!r} "
                "does not target a real canonical skill",
            )
        )
        return
    try:
        resolved = artifact.resolve()
    except OSError:
        issues.append(
            ProjectIssue(
                "invalid agent target artifact",
                f"agent target {target_id!r} Skill Link {path_text!r} is unresolvable",
            )
        )
        return
    if not _is_safe(root, resolved):
        issues.append(_unsafe_path(path_text))
        return
    if resolved != canonical.resolve():
        issues.append(
            ProjectIssue(
                "invalid agent target artifact",
                f"agent target {target_id!r} Skill Link {path_text!r} "
                "does not point at the corresponding canonical skill",
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
