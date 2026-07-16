"""Cheap, offline, structural post-generation checks.

The heavy FR-5 verification (docker build, health endpoint) runs in CI on
every PR and every upstream-bump PR — never on the user's machine at
generation time, so `uvx dev-ready` never requires Docker (see
docs/architecture.md, Deployment Architecture). This module only confirms
the staged project still has the shape dev-ready depends on; it reads the
staging directory only — no network, no writes (Module Boundary).
"""

from pathlib import Path

from dev_ready.errors import VerificationError

__all__ = ["verify_project", "REQUIRED_UPSTREAM_PATHS", "FORBIDDEN_PATHS"]

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

FORBIDDEN_PATHS: tuple[str, ...] = (".git", "copier.yml", "copier.yaml")


def verify_project(project_dir: Path) -> None:
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

    for path in FORBIDDEN_PATHS:
        if (project_dir / path).exists():
            raise VerificationError(
                f"generated project contains forbidden path {path!r} — an upstream/Copier change "
                "reintroduced a template-repo leak (.git worktree or copier.yml). Action: "
                "file an issue against dev-ready; do not use this pin."
            )
