"""Build and apply dev-ready overlay content.

Overlay assets are local package resources.  This module never fetches from the
network; ``build_overlay_content`` is also shared with the offline upgrader so
there is one authoritative rendering of managed files.
"""

import hashlib
import json
from collections.abc import Collection, Mapping
from importlib import resources
from importlib.resources.abc import Traversable
from pathlib import Path

from dev_ready import __version__
from dev_ready.catalog_effects import CatalogEffectError
from dev_ready.errors import OverlayError
from dev_ready.manifest import CatalogItem, UpstreamPin, VendoredPin
from dev_ready.overlay.rendering import TEMPLATE_SUFFIX as _TEMPLATE_SUFFIX
from dev_ready.overlay.rendering import render_asset as _render_asset
from dev_ready.prompts import Answers

__all__ = ["apply_overlay", "build_overlay_content", "content_inventory", "render_stamp"]

def render_stamp(
    answers: Answers,
    pin: UpstreamPin,
    catalog: Mapping[str, tuple[CatalogItem, ...]],
    vendored: Collection[VendoredPin] = (),
    inventory: Collection[tuple[str, str]] = (),
) -> str:
    """Render the v3 project stamp without writing it."""
    vendored_map = {v.repo: v.commit for v in vendored}

    def _stamp_items(component: str, selected: Collection[str]) -> list[dict[str, str | None]]:
        out = []
        for item in catalog.get(component, ()):
            if item.id not in selected:
                continue
            item_pin = item.pin
            if item.mode == "vendor" and item.vendored_repo and item.vendored_repo in vendored_map:
                item_pin = vendored_map[item.vendored_repo]
            out.append({"id": item.id, "pin": item_pin})
        return sorted(out, key=lambda d: str(d["id"]))

    data = {
        "stamp_version": 3,
        "dev_ready_version": __version__,
        "project_name": answers.project_name,
        "components": {
            "skills": {
                "included": answers.includes("skills"),
                "items": _stamp_items("skills", answers.items("skills")),
            },
            "mcp": {
                "included": answers.includes("mcp"),
                "items": _stamp_items("mcp", answers.items("mcp")),
            },
            "docs": {"included": answers.includes("docs")},
            "agents": {"included": answers.includes("agents")},
        },
        "upstream": {"repo": pin.repo, "commit": pin.commit},
        "inventory": [{"path": path, "sha256": digest} for path, digest in sorted(inventory)],
    }
    return json.dumps(data, indent=2) + "\n"


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

    def add(source: Traversable, dest_rel: Path) -> None:
        path = dest_rel.as_posix()
        if path in content:
            raise OverlayError(f"overlay destination collision: {path}")
        content[path] = _render_asset(source, dest_rel, answers)

    def collect(source: Traversable, dest_rel: Path) -> None:
        if source.is_dir():
            for entry in sorted(source.iterdir(), key=lambda item: item.name):
                next_name = entry.name.removesuffix(_TEMPLATE_SUFFIX) if not entry.is_dir() else entry.name
                collect(entry, dest_rel / next_name)
            return
        add(source, dest_rel)

    add(templates_root.joinpath("claude", "CLAUDE.md.tmpl"), Path("CLAUDE.md"))
    add(templates_root.joinpath("readme", "README.md.tmpl"), Path("README.md"))

    for component in ("skills", "mcp"):
        selected = answers.items(component)
        for item in catalog.get(component, ()):
            if item.id not in selected:
                continue
            for item_path in item.paths:
                collect(
                    templates_root.joinpath(*item_path.src.split("/")),
                    Path(item_path.dest),
                )

    if answers.includes("docs"):
        collect(templates_root.joinpath("docs"), Path("docs"))
    if answers.includes("agents"):
        collect(templates_root.joinpath("agents"), Path("docs") / "handoffs")
    return content


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
            if item.id in selected and item.effect is not None:
                try:
                    item.effect.apply(project_dir)
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
