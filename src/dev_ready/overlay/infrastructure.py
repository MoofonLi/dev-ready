"""Resolve infrastructure files implied by a selection.

Agent-Target-shaped infrastructure (native MCP config paths, Pointer Stubs)
lives in `dev_ready.agent_targets`, which owns that projection outright.
"""

from pathlib import Path

from dev_ready.agent_targets import CANONICAL_SKILLS_ROOT

_DOCUMENTATION_SCAFFOLD_PATHS = (
    (Path("docs", "architecture.md.tmpl"), Path("docs", "architecture.md")),
    (Path("docs", "requirements.md.tmpl"), Path("docs", "requirements.md")),
)
_SKILL_INFRASTRUCTURE_PATHS = (
    (
        Path("skills", "setup-project"),
        Path(*CANONICAL_SKILLS_ROOT, "setup-project"),
    ),
)


def documentation_scaffold_paths() -> tuple[tuple[Path, Path], ...]:
    """Return the unconditional documentation scaffold paths."""
    return _DOCUMENTATION_SCAFFOLD_PATHS


def skill_infrastructure_paths() -> tuple[tuple[Path, Path], ...]:
    """Return unconditional skills that must exist before Agent Target projection."""
    return _SKILL_INFRASTRUCTURE_PATHS
