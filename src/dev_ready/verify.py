"""Generation-blocking policy over shared, read-only project inspection.

The heavy FR-5 verification (docker build, health endpoint) runs in CI. This
module translates the first local structural issue into ``VerificationError``;
the inspection implementation is shared with the offline ``check`` command.
"""

from collections.abc import Mapping
from pathlib import Path

from dev_ready.errors import VerificationError
from dev_ready.inspection import (
    FORBIDDEN_PATHS,
    REQUIRED_OVERLAY_PATHS,
    REQUIRED_UPSTREAM_PATHS,
    ProjectExpectation,
    inspect_project,
)
from dev_ready.manifest import CatalogItem
from dev_ready.prompts import Answers

__all__ = [
    "verify_project",
    "REQUIRED_UPSTREAM_PATHS",
    "REQUIRED_OVERLAY_PATHS",
    "FORBIDDEN_PATHS",
]


def verify_project(
    project_dir: Path,
    answers: Answers,
    catalog: Mapping[str, tuple[CatalogItem, ...]],
) -> None:
    """Raise the generation policy's typed error for the first observed issue."""
    issues = inspect_project(
        project_dir,
        catalog,
        ProjectExpectation.generation(answers.selection),
    )
    if issues:
        raise VerificationError(issues[0].verification_message)
