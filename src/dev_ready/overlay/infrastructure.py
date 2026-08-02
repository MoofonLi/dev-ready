"""Resolve infrastructure files implied by a selection.

Agent-Target-shaped infrastructure (native MCP config paths, Pointer Stubs)
lives in `dev_ready.agent_targets`, which owns that projection outright.
"""

from pathlib import Path

_DOCUMENTATION_SCAFFOLD_PATHS = (
    (Path("docs", "architecture.md.tmpl"), Path("docs", "architecture.md")),
    (Path("docs", "requirements.md.tmpl"), Path("docs", "requirements.md")),
)


def documentation_scaffold_paths() -> tuple[tuple[Path, Path], ...]:
    """Return the unconditional documentation scaffold paths."""
    return _DOCUMENTATION_SCAFFOLD_PATHS
