"""overlay: apply dev-ready files (CLAUDE.md, skills, MCP config, docs) onto the base.

Pure local file operations — must never fetch from the network.
See docs/architecture.md.
"""

import re
from importlib import resources
from importlib.resources.abc import Traversable
from pathlib import Path

from dev_ready.errors import OverlayError
from dev_ready.prompts import Answers

__all__ = ["apply_overlay"]

_PROJECT_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]*$")
_TEMPLATE_SUFFIX = ".tmpl"
_TEMPLATE_TOKEN = "{{project_name}}"


def apply_overlay(answers: Answers, project_dir: Path) -> list[Path]:
    """Apply the selected overlay components onto `project_dir`.

    CLAUDE.md is always applied; `.claude/skills/`, `.mcp.json`, and `docs/`
    follow `answers.include_skills` / `include_mcp` / `include_docs`.

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
        )
    ]

    if answers.include_skills:
        written.extend(
            _apply_tree(
                templates_root.joinpath("claude", "skills"),
                project_dir,
                Path(".claude") / "skills",
                answers.project_name,
            )
        )

    if answers.include_mcp:
        written.append(
            _apply_file(
                templates_root.joinpath("mcp", "mcp.json"),
                project_dir,
                Path(".mcp.json"),
                answers.project_name,
            )
        )

    if answers.include_docs:
        written.extend(
            _apply_tree(
                templates_root.joinpath("docs"),
                project_dir,
                Path("docs"),
                answers.project_name,
            )
        )

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
