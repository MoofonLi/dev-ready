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


@dataclass(frozen=True)
class PartialAnswers:
    """What the CLI flags already answered; `None`/`components_explicit=False`
    marks what `collect_answers` still needs to fill in.

    `target_dir=None` means "default to `Path.cwd() / project_name`", which
    can only be resolved once the project name is known.
    """

    project_name: str | None
    target_dir: Path | None
    include_skills: bool
    include_mcp: bool
    include_docs: bool
    components_explicit: bool
    assume_yes: bool = False
