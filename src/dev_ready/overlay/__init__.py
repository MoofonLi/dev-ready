"""overlay: apply dev-ready files (CLAUDE.md, skills, MCP config, docs) onto the base.

Pure local file operations — must never fetch from the network.
See docs/architecture.md.
"""

import json
import re
from collections.abc import Mapping
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
    data = {
        "stamp_version": 1,
        "dev_ready_version": __version__,
        "components": {
            "skills": {"included": answers.include_skills, "items": sorted(answers.skills_items)},
            "mcp": {"included": answers.include_mcp, "items": sorted(answers.mcp_items)},
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
