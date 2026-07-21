"""Cheap, offline, structural post-generation checks.

The heavy FR-5 verification (docker build, health endpoint) runs in CI on
every PR and every upstream-bump PR — never on the user's machine at
generation time, so `uvx dev-ready` never requires Docker (see
docs/architecture.md, Deployment Architecture). This module only confirms
the staged project still has the shape dev-ready depends on; it reads the
staging directory only — no network, no writes (Module Boundary).
"""

import json
from collections.abc import Mapping
from pathlib import Path

from dev_ready.errors import VerificationError
from dev_ready.manifest import CatalogItem
from dev_ready.prompts import Answers

__all__ = [
    "verify_project",
    "REQUIRED_UPSTREAM_PATHS",
    "REQUIRED_OVERLAY_PATHS",
    "FORBIDDEN_PATHS",
]

# Derived from a real fetch of the manifest-pinned commit
# (fastapi/full-stack-fastapi-template @ 4cd0d9e51aebd1af6f82d91ad0df4c9e41f4dea2).
# Kept coarse on purpose: this exists to catch an upstream restructure at
# bump time, not to inventory the template. Revisit this list alongside any
# manifest bump that changes the upstream layout.
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


def verify_project(
    project_dir: Path, answers: Answers, catalog: Mapping[str, tuple[CatalogItem, ...]]
) -> None:
    """Check that `project_dir` has the upstream paths dev-ready depends on.

    Raises `VerificationError` naming the first missing path, with the
    likely cause and the action to take.
    """
    for rel_path in REQUIRED_UPSTREAM_PATHS:
        if not (project_dir / rel_path).exists():
            raise VerificationError(
                f"generated project is missing expected upstream path {rel_path!r}. "
                "Likely cause: the upstream layout changed at the manifest-pinned "
                "commit. Action: file an issue against dev-ready, or do not use "
                "this pin."
            )

    for rel_path in REQUIRED_OVERLAY_PATHS:
        if not (project_dir / rel_path).exists():
            raise VerificationError(
                f"generated project is missing required overlay path {rel_path!r}. "
                "Likely cause: an overlay/stamp regression."
            )

    for path in FORBIDDEN_PATHS:
        if (project_dir / path).exists():
            raise VerificationError(
                f"generated project contains forbidden path {path!r} — an upstream/Copier change "
                "reintroduced a template-repo leak (.git worktree or copier.yml). Action: "
                "file an issue against dev-ready; do not use this pin."
            )

    for component, selected in (("skills", answers.skills_items), ("mcp", answers.mcp_items)):
        for item in catalog.get(component, ()):
            expected = item.id in selected
            for item_path in item.paths:
                present = (project_dir / item_path.dest).exists()
                if expected and not present:
                    raise VerificationError(
                        f"selected {component} item {item.id!r} is missing its path {item_path.dest!r}"
                    )
                if not expected and present:
                    raise VerificationError(
                        f"unselected {component} item {item.id!r} left path {item_path.dest!r} in the output"
                    )

            if item.inject is not None:
                present = _check_inject_present(project_dir, item)
                if expected and not present:
                    raise VerificationError(
                        f"selected {component} item {item.id!r} is missing its inject effect in {item.inject.target}"
                    )
                if not expected and present:
                    raise VerificationError(
                        f"unselected {component} item {item.id!r} left inject effect in {item.inject.target}"
                    )


def _check_inject_present(project_dir: Path, item: CatalogItem) -> bool:
    inject = item.inject
    assert inject is not None
    target_path = project_dir / inject.target
    if not target_path.exists():
        return False

    try:
        data = json.loads(target_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise VerificationError(
            f"failed to parse {inject.target} while verifying item {item.id!r}: {error}"
        ) from error

    if not isinstance(data, dict):
        raise VerificationError(
            f"{inject.target} root must be a JSON object while verifying item {item.id!r}"
        )

    if inject.kind == "mcp-server":
        mcp_servers = data.get("mcpServers")
        if not isinstance(mcp_servers, dict):
            return False
        assert inject.server_name is not None
        return inject.server_name in mcp_servers

    elif inject.kind == "npm-dev-dependency":
        dev_deps = data.get("devDependencies")
        if not isinstance(dev_deps, dict):
            return False
        scripts = data.get("scripts")
        if not isinstance(scripts, dict):
            return False
        has_pkg = inject.package in dev_deps
        has_scripts = all(name in scripts for name, _ in inject.scripts)
        return has_pkg and has_scripts

    return False

