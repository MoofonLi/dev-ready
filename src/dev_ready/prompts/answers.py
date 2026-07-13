"""The single Answers model shared by interactive and flag-based paths (ADR-004)."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Answers:
    """Everything generation needs to know, regardless of how it was collected."""

    project_name: str
    target_dir: Path
    include_skills: bool = True
    include_mcp: bool = True
    include_docs: bool = True
    assume_yes: bool = False
