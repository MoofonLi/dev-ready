"""Build and apply dev-ready overlay content.

Overlay assets are local package resources.  This module never fetches from the
network; ``build_overlay_content`` is also shared with the offline upgrader so
there is one authoritative rendering of managed files.
"""

import hashlib
import json
import re
from collections.abc import Collection, Mapping
from importlib import resources
from importlib.resources.abc import Traversable
from pathlib import Path

from dev_ready import __version__
from dev_ready.errors import OverlayError
from dev_ready.manifest import CatalogItem, UpstreamPin, VendoredPin
from dev_ready.prompts import Answers

__all__ = ["apply_overlay", "build_overlay_content", "content_inventory", "render_stamp"]

_PROJECT_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]*$")
_TEMPLATE_SUFFIX = ".tmpl"
_TEMPLATE_TOKEN = "{{project_name}}"


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
            "skills": {"included": answers.include_skills, "items": _stamp_items("skills", answers.skills_items)},
            "mcp": {"included": answers.include_mcp, "items": _stamp_items("mcp", answers.mcp_items)},
            "docs": {"included": answers.include_docs},
            "agents": {"included": answers.include_agents},
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
    _validate_project_name(answers.project_name)
    templates_root = resources.files("dev_ready").joinpath("templates")
    content: dict[str, bytes] = {}

    def add(source: Traversable, dest_rel: Path) -> None:
        path = dest_rel.as_posix()
        if path in content:
            raise OverlayError(f"overlay destination collision: {path}")
        content[path] = _render_asset(source, dest_rel, answers.project_name)

    def collect(source: Traversable, dest_rel: Path) -> None:
        if source.is_dir():
            for entry in sorted(source.iterdir(), key=lambda item: item.name):
                next_name = entry.name.removesuffix(_TEMPLATE_SUFFIX) if not entry.is_dir() else entry.name
                collect(entry, dest_rel / next_name)
            return
        add(source, dest_rel)

    add(templates_root.joinpath("claude", "CLAUDE.md.tmpl"), Path("CLAUDE.md"))
    add(templates_root.joinpath("readme", "README.md.tmpl"), Path("README.md"))

    for component, selected in (("skills", answers.skills_items), ("mcp", answers.mcp_items)):
        for item in catalog.get(component, ()):
            if item.id not in selected:
                continue
            for item_path in item.paths:
                collect(
                    templates_root.joinpath(*item_path.src.split("/")),
                    Path(item_path.dest),
                )

    if answers.include_docs:
        collect(templates_root.joinpath("docs"), Path("docs"))
    if answers.include_agents:
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

    for component, selected in (("skills", answers.skills_items), ("mcp", answers.mcp_items)):
        for item in catalog.get(component, ()):
            if item.id in selected and item.inject is not None:
                _apply_injection(item, project_dir)

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


def _validate_project_name(project_name: str) -> None:
    if not _PROJECT_NAME_PATTERN.fullmatch(project_name):
        raise OverlayError(f"invalid project name {project_name!r}")


def _render_asset(source: Traversable, dest_rel: Path, project_name: str) -> bytes:
    """Render one package asset without writing it."""
    if not source.is_file():
        raise OverlayError(f"overlay asset missing: {source}")
    try:
        if source.name.endswith(_TEMPLATE_SUFFIX):
            rendered = source.read_text(encoding="utf-8").replace(_TEMPLATE_TOKEN, project_name)
            if "{{" in rendered or "}}" in rendered:
                raise OverlayError(f"unresolved template marker left in {dest_rel}")
            return rendered.encode("utf-8")
        return source.read_bytes()
    except OSError as error:
        raise OverlayError(f"failed to read overlay asset for {dest_rel}: {error}") from error


def _apply_injection(item: CatalogItem, project_dir: Path) -> None:
    if item.inject is None:
        return
    if item.inject.kind == "mcp-server":
        _inject_mcp_server(item, project_dir)
    elif item.inject.kind == "npm-dev-dependency":
        _inject_npm_dev_dependency(item, project_dir)
    else:
        raise OverlayError(f"unrecognized injection kind {item.inject.kind!r}")


def _inject_mcp_server(item: CatalogItem, project_dir: Path) -> None:
    assert item.inject is not None
    target_path = project_dir / item.inject.target
    if not target_path.exists():
        raise OverlayError(
            f"item '{item.id}' requires base target '{item.inject.target}' from 'mcp-config' â€” include 'mcp-config' as well"
        )
    try:
        data = json.loads(target_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise OverlayError(f"failed to parse {item.inject.target}: {error}") from error
    if not isinstance(data, dict):
        raise OverlayError(f"{item.inject.target} root must be a JSON object")
    mcp_servers = data.setdefault("mcpServers", {})
    if not isinstance(mcp_servers, dict):
        raise OverlayError(f"'mcpServers' field in {item.inject.target} must be a JSON object")
    server_name = item.inject.server_name
    assert server_name is not None
    if server_name in mcp_servers:
        raise OverlayError(f"server '{server_name}' already exists in {item.inject.target}")
    mcp_servers[server_name] = {"command": item.inject.command, "args": [f"{item.inject.package}=={item.pin}"]}
    try:
        target_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    except OSError as error:
        raise OverlayError(f"failed to write {item.inject.target}: {error}") from error


def _inject_npm_dev_dependency(item: CatalogItem, project_dir: Path) -> None:
    assert item.inject is not None
    target_path = project_dir / item.inject.target
    if not target_path.exists():
        raise OverlayError(
            f"item '{item.id}' target '{item.inject.target}' is missing â€” upstream layout changed or fetch incomplete"
        )
    try:
        data = json.loads(target_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise OverlayError(f"failed to parse {item.inject.target}: {error}") from error
    if not isinstance(data, dict):
        raise OverlayError(f"{item.inject.target} root must be a JSON object")
    dev_deps = data.setdefault("devDependencies", {})
    if not isinstance(dev_deps, dict):
        raise OverlayError(f"'devDependencies' in {item.inject.target} must be a JSON object")
    pkg_name = item.inject.package
    if pkg_name in dev_deps:
        raise OverlayError(f"package '{pkg_name}' already declared in {item.inject.target} devDependencies")
    assert item.pin is not None
    dev_deps[pkg_name] = item.pin
    scripts = data.setdefault("scripts", {})
    if not isinstance(scripts, dict):
        raise OverlayError(f"'scripts' in {item.inject.target} must be a JSON object")
    for s_name, s_cmd in item.inject.scripts:
        if s_name in scripts:
            raise OverlayError(f"script '{s_name}' already declared in {item.inject.target} scripts")
        scripts[s_name] = s_cmd
    try:
        target_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    except OSError as error:
        raise OverlayError(f"failed to write {item.inject.target}: {error}") from error
