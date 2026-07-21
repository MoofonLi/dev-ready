"""overlay: apply dev-ready files (CLAUDE.md, skills, MCP config, docs) onto the base.

Pure local file operations — must never fetch from the network.
See docs/architecture.md.
"""

import json
import re
from collections.abc import Collection, Mapping
from importlib import resources
from importlib.resources.abc import Traversable
from pathlib import Path

from dev_ready import __version__
from dev_ready.errors import OverlayError
from dev_ready.manifest import CatalogItem, UpstreamPin
from dev_ready.prompts import Answers

__all__ = ["apply_overlay", "render_stamp"]

_PROJECT_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]*$")
_TEMPLATE_SUFFIX = ".tmpl"
_TEMPLATE_TOKEN = "{{project_name}}"


def render_stamp(
    answers: Answers, pin: UpstreamPin, catalog: Mapping[str, tuple[CatalogItem, ...]]
) -> str:
    def _stamp_items(component: str, selected: Collection[str]) -> list[dict[str, str | None]]:
        out = [
            {"id": item.id, "pin": item.pin}
            for item in catalog.get(component, ())
            if item.id in selected
        ]
        return sorted(out, key=lambda d: str(d["id"]))

    data = {
        "stamp_version": 2,
        "dev_ready_version": __version__,
        "components": {
            "skills": {"included": answers.include_skills, "items": _stamp_items("skills", answers.skills_items)},
            "mcp": {"included": answers.include_mcp, "items": _stamp_items("mcp", answers.mcp_items)},
            "docs": {"included": answers.include_docs},
            "agents": {"included": answers.include_agents},
        },
        "upstream": {"repo": pin.repo, "commit": pin.commit},
    }
    return json.dumps(data, indent=2) + "\n"


def apply_overlay(
    answers: Answers,
    project_dir: Path,
    catalog: Mapping[str, tuple[CatalogItem, ...]],
    pin: UpstreamPin,
) -> list[Path]:
    """Apply the selected overlay components onto `project_dir`.

    CLAUDE.md and README.md are always applied; `.claude/skills/`, `.mcp.json`, `docs/`, and `docs/handoffs/`
    follow `answers.skills_items` / `mcp_items` / `include_docs` / `include_agents`.

    Returns the paths written, relative to `project_dir`. Raises
    `OverlayError` on any destination collision, missing asset, or leftover
    `{{` template marker — never silently overwrites or partially templates.
    """
    _validate_project_name(answers.project_name)

    templates_root = resources.files("dev_ready").joinpath("templates")
    written: list[Path] = [
        _apply_file(
            templates_root.joinpath("claude", "CLAUDE.md.tmpl"),
            project_dir,
            Path("CLAUDE.md"),
            answers.project_name,
        ),
        _apply_file(
            templates_root.joinpath("readme", "README.md.tmpl"),
            project_dir,
            Path("README.md"),
            answers.project_name,
        ),
    ]

    for component, selected in (("skills", answers.skills_items), ("mcp", answers.mcp_items)):
        for item in catalog.get(component, ()):
            if item.id not in selected:
                continue
            for item_path in item.paths:
                source = templates_root.joinpath(*item_path.src.split("/"))
                dest_rel = Path(item_path.dest)
                if source.is_dir():
                    written.extend(_apply_tree(source, project_dir, dest_rel, answers.project_name))
                else:
                    written.append(_apply_file(source, project_dir, dest_rel, answers.project_name))

    for component, selected in (("skills", answers.skills_items), ("mcp", answers.mcp_items)):
        for item in catalog.get(component, ()):
            if item.id not in selected or item.inject is None:
                continue
            _apply_injection(item, project_dir)

    if answers.include_docs:
        written.extend(
            _apply_tree(
                templates_root.joinpath("docs"),
                project_dir,
                Path("docs"),
                answers.project_name,
            )
        )

    if answers.include_agents:
        written.extend(
            _apply_tree(
                templates_root.joinpath("agents"),
                project_dir,
                Path("docs") / "handoffs",
                answers.project_name,
            )
        )

    stamp_path = project_dir / ".dev-ready.json"
    if stamp_path.exists() or stamp_path.is_symlink():
        raise OverlayError("overlay destination already exists: .dev-ready.json")
    try:
        stamp_path.write_text(render_stamp(answers, pin, catalog), encoding="utf-8")
    except OSError as error:
        raise OverlayError(f"failed to write .dev-ready.json: {error}") from error
    written.append(Path(".dev-ready.json"))

    return written


def _validate_project_name(project_name: str) -> None:
    if not _PROJECT_NAME_PATTERN.fullmatch(project_name):
        raise OverlayError(f"invalid project name {project_name!r}")


def _apply_tree(
    source_dir: Traversable, project_dir: Path, dest_root: Path, project_name: str
) -> list[Path]:
    if not source_dir.is_dir():
        raise OverlayError(f"overlay asset directory missing: {source_dir}")

    written: list[Path] = []
    for entry in sorted(source_dir.iterdir(), key=lambda item: item.name):
        if entry.is_dir():
            written.extend(_apply_tree(entry, project_dir, dest_root / entry.name, project_name))
            continue
        dest_name = (
            entry.name[: -len(_TEMPLATE_SUFFIX)]
            if entry.name.endswith(_TEMPLATE_SUFFIX)
            else entry.name
        )
        written.append(_apply_file(entry, project_dir, dest_root / dest_name, project_name))
    return written


def _apply_file(
    source: Traversable, project_dir: Path, dest_rel: Path, project_name: str
) -> Path:
    if not source.is_file():
        raise OverlayError(f"overlay asset missing: {source}")

    dest = project_dir / dest_rel
    # is_symlink() also catches dangling symlinks, which exists() reports as False.
    if dest.exists() or dest.is_symlink():
        raise OverlayError(f"overlay destination already exists: {dest_rel}")

    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        if source.name.endswith(_TEMPLATE_SUFFIX):
            content = source.read_text(encoding="utf-8").replace(_TEMPLATE_TOKEN, project_name)
            if "{{" in content or "}}" in content:
                raise OverlayError(f"unresolved template marker left in {dest_rel}")
            dest.write_text(content, encoding="utf-8")
        else:
            dest.write_bytes(source.read_bytes())
    except OSError as error:
        raise OverlayError(f"failed to write {dest_rel}: {error}") from error

    return dest_rel


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
            f"item '{item.id}' requires base target '{item.inject.target}' from 'mcp-config' — include 'mcp-config' as well"
        )

    try:
        raw_text = target_path.read_text(encoding="utf-8")
        data = json.loads(raw_text)
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

    mcp_servers[server_name] = {
        "command": item.inject.command,
        "args": [f"{item.inject.package}=={item.pin}"],
    }

    try:
        target_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    except OSError as error:
        raise OverlayError(f"failed to write {item.inject.target}: {error}") from error


def _inject_npm_dev_dependency(item: CatalogItem, project_dir: Path) -> None:
    assert item.inject is not None
    target_path = project_dir / item.inject.target
    if not target_path.exists():
        raise OverlayError(
            f"item '{item.id}' target '{item.inject.target}' is missing — upstream layout changed or fetch incomplete"
        )

    try:
        raw_text = target_path.read_text(encoding="utf-8")
        data = json.loads(raw_text)
    except (OSError, json.JSONDecodeError) as error:
        raise OverlayError(f"failed to parse {item.inject.target}: {error}") from error

    if not isinstance(data, dict):
        raise OverlayError(f"{item.inject.target} root must be a JSON object")

    dev_deps = data.setdefault("devDependencies", {})
    if not isinstance(dev_deps, dict):
        raise OverlayError(f"'devDependencies' in {item.inject.target} must be a JSON object")

    pkg_name = item.inject.package
    if pkg_name in dev_deps:
        raise OverlayError(
            f"package '{pkg_name}' already declared in {item.inject.target} devDependencies"
        )
    assert item.pin is not None
    dev_deps[pkg_name] = item.pin

    scripts = data.setdefault("scripts", {})
    if not isinstance(scripts, dict):
        raise OverlayError(f"'scripts' in {item.inject.target} must be a JSON object")

    for s_name, s_cmd in item.inject.scripts:
        if s_name in scripts:
            raise OverlayError(
                f"script '{s_name}' already declared in {item.inject.target} scripts"
            )
        scripts[s_name] = s_cmd

    try:
        target_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    except OSError as error:
        raise OverlayError(f"failed to write {item.inject.target}: {error}") from error
