"""Generation-blocking policy over shared, read-only project inspection.

The heavy FR-5 verification (docker build, health endpoint) runs in CI. This
module translates the first local structural issue into ``VerificationError``;
the inspection implementation is shared with the offline ``check`` command.
"""

from pathlib import Path

from dev_ready.errors import VerificationError
from dev_ready.inspection import (
    FORBIDDEN_PATHS,
    REQUIRED_OVERLAY_PATHS,
    REQUIRED_UPSTREAM_PATHS,
    ProjectExpectation,
    inspect_project,
)
from dev_ready.manifest import ComponentCatalog
from dev_ready.overlay import projected_skill_link_pairs
from dev_ready.prompts import Answers
from dev_ready.skill_links import (
    PathKind,
    classify_path,
    create_skill_link,
    remove_link_object,
)

__all__ = [
    "verify_project",
    "REQUIRED_UPSTREAM_PATHS",
    "REQUIRED_OVERLAY_PATHS",
    "FORBIDDEN_PATHS",
]


def verify_project(
    project_dir: Path,
    answers: Answers,
    catalog: ComponentCatalog,
) -> None:
    """Raise the generation policy's typed error for the first observed issue."""
    created: list[Path] = []
    try:
        created.extend(_materialize_projected_links(project_dir, answers, catalog))
        issues = inspect_project(
            project_dir,
            catalog,
            ProjectExpectation.generation(answers.selection),
        )
        if issues:
            raise VerificationError(issues[0].verification_message)
    finally:
        for link_path in created:
            try:
                remove_link_object(link_path)
            except OSError:
                pass


def _materialize_projected_links(
    project_dir: Path, answers: Answers, catalog: ComponentCatalog
) -> list[Path]:
    created: list[Path] = []
    for link_rel, canonical_rel in projected_skill_link_pairs(answers, catalog):
        link_path = project_dir / link_rel
        canonical = project_dir / canonical_rel
        if classify_path(canonical) != PathKind.DIRECTORY:
            continue
        try:
            if classify_path(link_path) in {PathKind.SYMBOLIC_LINK, PathKind.JUNCTION}:
                remove_link_object(link_path)
            create_skill_link(link_path, canonical)
        except FileExistsError as error:
            raise VerificationError(
                f"generated project has invalid Skill Link structure at {link_path}: {error}"
            ) from error
        except OSError as error:
            raise VerificationError(
                f"failed to create Skill Link at {link_path}: {error}. "
                "Choose a different destination location on a filesystem that "
                "supports directory links."
            ) from error
        created.append(link_path)
    return created
