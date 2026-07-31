"""Build and apply dev-ready overlay content.

Overlay assets are local package resources.  This module never fetches from the
network; ``build_overlay_content`` is also shared with the offline upgrader so
there is one authoritative rendering of managed files.
"""

import hashlib
from collections.abc import Collection, Mapping
from dataclasses import replace
from importlib import resources
from importlib.resources.abc import Traversable
from pathlib import Path

from dev_ready.catalog_effects import CatalogEffectError
from dev_ready.errors import OverlayError
from dev_ready.manifest import AgentTarget, CatalogItem, ComponentCatalog, UpstreamPin, VendoredPin
from dev_ready.overlay.infrastructure import (
    base_mcp_config_targets,
    documentation_scaffold_paths,
)
from dev_ready.overlay.rendering import TEMPLATE_SUFFIX as _TEMPLATE_SUFFIX
from dev_ready.overlay.rendering import render_asset as _render_asset
from dev_ready.overlay.stamp_rendering import render_stamp
from dev_ready.prompts import Answers

__all__ = ["apply_overlay", "build_overlay_content", "content_inventory", "render_stamp"]


def build_overlay_content(
    answers: Answers, catalog: Mapping[str, tuple[CatalogItem, ...]]
) -> dict[str, bytes]:
    """Return every whole-file overlay write, rendered but not injected or written.

    Keys are POSIX-relative project paths and preserve generation's historical
    write order.  Reading package resources is necessary; this function never
    reads from or mutates the destination project.
    """
    templates_root = resources.files("dev_ready").joinpath("templates")
    content: dict[str, bytes] = {}
    declared_agent_targets = (
        catalog.agent_targets if isinstance(catalog, ComponentCatalog) else {}
    )
    agent_targets = {
        target_id: target
        for target_id, target in declared_agent_targets.items()
        if target_id in answers.agent_targets
    }

    def add_bytes(dest_rel: Path, data: bytes) -> None:
        path = dest_rel.as_posix()
        if path in content:
            raise OverlayError(f"overlay destination collision: {path}")
        content[path] = data

    def add(source: Traversable, dest_rel: Path) -> None:
        add_bytes(dest_rel, _render_asset(source, dest_rel, answers))

    def collect(source: Traversable, dest_rel: Path) -> None:
        if source.is_dir():
            for entry in sorted(source.iterdir(), key=lambda item: item.name):
                next_name = entry.name.removesuffix(_TEMPLATE_SUFFIX) if not entry.is_dir() else entry.name
                collect(entry, dest_rel / next_name)
            return
        add(source, dest_rel)

    add(templates_root.joinpath("rules", "AGENTS.md.tmpl"), Path("AGENTS.md"))
    for target in agent_targets.values():
        if target.rules_file is not None:
            add_bytes(Path(target.rules_file), b"@AGENTS.md\n")
    add(templates_root.joinpath("readme", "README.md.tmpl"), Path("README.md"))

    for target_path in base_mcp_config_targets(
        catalog,
        answers.items("mcp"),
        agent_targets,
    ):
        collect(templates_root.joinpath("mcp", "mcp.json"), target_path)

    for component in ("skills", "mcp", "docs"):
        selected = answers.items(component)
        for item in catalog.get(component, ()):
            if item.id not in selected:
                continue
            for item_path in item.paths:
                source = templates_root.joinpath(*item_path.src.split("/"))
                if component == "mcp":
                    for target in agent_targets.values():
                        if target.mcp_file is not None:
                            collect(source, Path(target.mcp_file))
                else:
                    collect(source, Path(item_path.dest))

    canonical_skill_files = {
        path: data
        for path, data in content.items()
        if path.startswith(".agents/skills/") and path.endswith("/SKILL.md")
    }
    for target in agent_targets.values():
        for canonical_path, canonical_bytes in canonical_skill_files.items():
            relative = Path(canonical_path).relative_to(Path(".agents") / "skills")
            if len(relative.parts) != 2 or relative.name != "SKILL.md":
                continue
            stub_path = Path(target.skills_dir) / relative
            add_bytes(
                stub_path,
                _render_pointer_stub(canonical_bytes, relative.parts[0], canonical_path, target),
            )

    for source, destination in documentation_scaffold_paths(answers.includes("docs")):
        collect(templates_root.joinpath(source), destination)
    return content


def _render_pointer_stub(
    canonical: bytes,
    skill_name: str,
    canonical_path: str,
    target: AgentTarget,
) -> bytes:
    """Preserve canonical frontmatter and replace the body with a native pointer."""
    try:
        text = canonical.decode("utf-8")
    except UnicodeDecodeError as error:
        raise OverlayError(f"canonical skill {canonical_path!r} is not UTF-8") from error
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise OverlayError(f"canonical skill {canonical_path!r} is missing YAML frontmatter")
    try:
        end = lines.index("---", 1)
    except ValueError as error:
        raise OverlayError(
            f"canonical skill {canonical_path!r} has unterminated YAML frontmatter"
        ) from error
    frontmatter = "\n".join(lines[: end + 1])
    return (
        f"{frontmatter}\n\n"
        f"# {skill_name} (pointer)\n\n"
        f"The authoritative version of this skill lives at `{canonical_path}` "
        f"(open Agent Skills format). This file is only a {target.id} discovery stub.\n\n"
        f"Read `{canonical_path}` in full and follow it exactly. Do not act on this stub alone.\n"
    ).encode("utf-8")


def content_inventory(content: Mapping[str, bytes]) -> tuple[tuple[str, str], ...]:
    """Return a deterministic SHA-256 inventory for rendered overlay files."""
    return tuple(
        (path, hashlib.sha256(data).hexdigest()) for path, data in sorted(content.items())
    )


def apply_overlay(
    answers: Answers,
    project_dir: Path,
    catalog: Mapping[str, tuple[CatalogItem, ...]],
    pin: UpstreamPin,
    vendored: Collection[VendoredPin] = (),
) -> list[Path]:
    """Apply selected overlay content and return paths written relative to the project."""
    content = build_overlay_content(answers, catalog)
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

    for component in ("skills", "mcp"):
        selected = answers.items(component)
        for item in catalog.get(component, ()):
            if item.id not in selected or item.effect is None:
                continue
            effects = (item.effect,)
            if component == "mcp":
                effects = tuple(
                    replace(item.effect, target=target.mcp_file)
                    for target_id, target in getattr(catalog, "agent_targets", {}).items()
                    if target_id in answers.agent_targets and target.mcp_file is not None
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
