"""Build and apply dev-ready overlay content.

Overlay assets are local package resources.  This module never fetches from the
network; ``build_overlay_content`` is also shared with the offline upgrader so
there is one authoritative rendering of managed files.
"""

import hashlib
from collections.abc import Collection, Mapping
from importlib import resources
from importlib.resources.abc import Traversable
from pathlib import Path

from dev_ready.agent_targets import (
    CANONICAL_SKILLS_ROOT,
    project_targets,
    skill_names_from_content,
)
from dev_ready.catalog_effects import CatalogEffectError
from dev_ready.errors import OverlayError
from dev_ready.manifest import CATALOG_COMPONENTS, ComponentCatalog, UpstreamPin, VendoredPin
from dev_ready.overlay.infrastructure import (
    documentation_scaffold_paths,
    skill_infrastructure_paths,
)
from dev_ready.executable_modes import declared_executable_paths
from dev_ready.overlay.executable import apply_executable_modes
from dev_ready.overlay.rendering import TEMPLATE_SUFFIX as _TEMPLATE_SUFFIX
from dev_ready.overlay.rendering import inject_mounted_enhancements as _inject_mounts
from dev_ready.overlay.rendering import render_asset as _render_asset
from dev_ready.overlay.stamp_rendering import render_stamp
from dev_ready.prompts import Answers

__all__ = [
    "apply_overlay",
    "build_overlay_content",
    "content_inventory",
    "generated_anchor_names",
    "projected_skill_link_pairs",
    "render_ignore_anchor",
    "render_stamp",
]

_DESIGN_REFERENCE_REPO = "VoltAgent/awesome-design-md"
_DESIGN_REFERENCE_NOTICE = Path("docs/design-md-LICENSE.md")


def build_overlay_content(
    answers: Answers, catalog: ComponentCatalog
) -> dict[str, bytes]:
    """Return every whole-file overlay write, fully rendered but not written.

    Keys are POSIX-relative project paths and preserve generation's historical
    write order.  Reading package resources is necessary; this function never
    reads from or mutates the destination project.
    """
    templates_root = resources.files("dev_ready").joinpath("templates")
    content: dict[str, bytes] = {}
    projection = project_targets(catalog, answers.agent_targets)

    def add_bytes(dest_rel: Path, data: bytes) -> None:
        path = dest_rel.as_posix()
        if path in content:
            raise OverlayError(f"overlay destination collision: {path}")
        content[path] = data

    def add(source: Traversable, dest_rel: Path) -> None:
        add_bytes(dest_rel, _render_asset(source, dest_rel, answers, catalog=catalog))

    def collect(source: Traversable, dest_rel: Path) -> None:
        if source.is_dir():
            for entry in sorted(source.iterdir(), key=lambda item: item.name):
                next_name = entry.name.removesuffix(_TEMPLATE_SUFFIX) if not entry.is_dir() else entry.name
                collect(entry, dest_rel / next_name)
            return
        add(source, dest_rel)

    add(templates_root.joinpath("rules", "AGENTS.md.tmpl"), Path("AGENTS.md"))
    for rules_file in projection.rules_files:
        add_bytes(Path(rules_file), b"@AGENTS.md\n")
    add(templates_root.joinpath("readme", "README.md.tmpl"), Path("README.md"))
    # Upstream's root ignore file is pruned so this replacement can own the path
    # (FR-38, the shape FR-7/FR-8 already use for README.md). The source asset is
    # dotless: a real dotfile in the package tree would be read by git as an
    # ignore rule over its own directory and is the class most likely to be
    # dropped by a build backend's default exclusions.
    add(templates_root.joinpath("gitignore", "gitignore"), Path(".gitignore"))

    for target_path in projection.base_mcp_config_paths(catalog, answers.items("mcp")):
        collect(templates_root.joinpath("mcp", "mcp.json"), target_path)

    selected_vendored_repos: set[str] = set()
    for component in CATALOG_COMPONENTS:
        selected = answers.items(component)
        for item in catalog.get(component, ()):
            if item.id not in selected:
                continue
            if item.vendored_repo is not None:
                selected_vendored_repos.add(item.vendored_repo)
            written_items = (
                tuple(retargeted for _, retargeted in projection.retarget_mcp(item))
                if component == "mcp"
                else (item,)
            )
            for written_item in written_items:
                for item_path in written_item.paths:
                    collect(
                        templates_root.joinpath(*item_path.src.split("/")),
                        Path(item_path.dest),
                    )

    if _DESIGN_REFERENCE_REPO in selected_vendored_repos:
        add(
            templates_root.joinpath(*_DESIGN_REFERENCE_NOTICE.parts),
            _DESIGN_REFERENCE_NOTICE,
        )

    _inject_mounts(content, answers, catalog)

    for source, destination in skill_infrastructure_paths():
        collect(templates_root.joinpath(source), destination)

    skill_names = skill_names_from_content(content)
    if skill_names:
        anchor = render_ignore_anchor(skill_names)
        for target in projection.skill_targets:
            add_bytes(projection.ignore_anchor_path(target), anchor)

    for source, destination in documentation_scaffold_paths():
        collect(templates_root.joinpath(source), destination)
    return content


_IGNORE_ANCHOR_HEADER = (
    "# Machine-local Skill Links. They are not version-controlled.\n"
    "# After cloning, restore them with: uvx dev-ready upgrade\n"
)


def render_ignore_anchor(skill_names: Collection[str]) -> bytes:
    """Render one nested Git safety anchor for the projected Skill Links."""
    return (
        _IGNORE_ANCHOR_HEADER + "".join(f"{name}\n" for name in skill_names)
    ).encode("utf-8")


def generated_anchor_names(data: bytes) -> tuple[str, ...] | None:
    """Return generated link names if ``data`` is an exact nested-anchor rendering."""
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return None
    names = tuple(
        line for line in text.splitlines() if line and not line.startswith("#")
    )
    if render_ignore_anchor(names) != data:
        return None
    return names


def projected_skill_link_pairs(
    answers: Answers, catalog: ComponentCatalog
) -> tuple[tuple[Path, Path], ...]:
    """Relative (link, canonical) pairs derived from desired overlay content."""
    names = skill_names_from_content(build_overlay_content(answers, catalog))
    projection = project_targets(catalog, answers.agent_targets)
    return tuple(
        (projection.link_path(target, name), Path(*CANONICAL_SKILLS_ROOT) / name)
        for target in projection.skill_targets
        for name in names
    )


def content_inventory(content: Mapping[str, bytes]) -> tuple[tuple[str, str], ...]:
    """Return a deterministic SHA-256 inventory for rendered overlay files."""
    return tuple(
        (path, hashlib.sha256(data).hexdigest()) for path, data in sorted(content.items())
    )


def apply_overlay(
    answers: Answers,
    project_dir: Path,
    catalog: ComponentCatalog,
    pin: UpstreamPin,
    vendored: Collection[VendoredPin],
) -> list[Path]:
    """Apply selected overlay content and return paths written relative to the project."""
    content = build_overlay_content(answers, catalog)
    projection = project_targets(catalog, answers.agent_targets)
    written: list[Path] = []
    for path, data in content.items():
        dest_rel = Path(path)
        dest = project_dir / dest_rel
        if dest.exists() or dest.is_symlink():
            raise OverlayError(f"overlay destination already exists: {dest_rel}")
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
        except OSError as error:
            raise OverlayError(f"failed to write {dest_rel}: {error}") from error
        written.append(dest_rel)

    apply_executable_modes(
        project_dir,
        declared_executable_paths(catalog, answers, vendored),
    )

    for component in ("skills", "mcp"):
        selected = answers.items(component)
        for item in catalog.get(component, ()):
            if item.id not in selected or item.effect is None:
                continue
            effects = (
                tuple(
                    retargeted.effect
                    for _, retargeted in projection.retarget_mcp(item)
                    if retargeted.effect is not None
                )
                if component == "mcp"
                else (item.effect,)
            )
            for effect in effects:
                try:
                    effect.apply(project_dir)
                except CatalogEffectError as error:
                    raise OverlayError(str(error)) from error

    stamp_path = project_dir / ".dev-ready.json"
    if stamp_path.exists() or stamp_path.is_symlink():
        raise OverlayError("overlay destination already exists: .dev-ready.json")
    try:
        stamp_path.write_bytes(
            render_stamp(answers, pin, catalog, vendored, content_inventory(content)).encode("utf-8")
        )
    except OSError as error:
        raise OverlayError(f"failed to write .dev-ready.json: {error}") from error
    written.append(Path(".dev-ready.json"))
    return written
