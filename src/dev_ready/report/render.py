"""Render the post-generation success report.

Pure function of its arguments — no filesystem access, so it stays valid
even if the caller passes paths that were never actually written (as the
unit tests do). See docs/architecture.md, Module Boundary.
"""

from pathlib import Path

from dev_ready.manifest import UpstreamPin
from dev_ready.prompts import Answers

__all__ = ["render_report"]


def render_report(answers: Answers, pin: UpstreamPin, written: list[Path]) -> str:
    """Render the full success message `cli.py` prints verbatim after generation."""
    overlay_paths = ", ".join(str(path) for path in written) if written else "(none)"
    lines = [
        f"project generated: {answers.project_name}",
        f"location:  {answers.target_dir}",
        f"upstream:  {pin.repo}@{pin.commit[:12]} ({pin.ref})",
        f"overlay:   {overlay_paths}",
        "",
        "next steps:",
        f"  1. cd {answers.target_dir}",
        # "docker compose watch" is the dev workflow for
        # fastapi/full-stack-fastapi-template as of the manifest-pinned commit.
        # Update when a manifest bump changes the upstream workflow.
        "  2. docker compose watch   (see CLAUDE.md for other commands)",
        "  3. read CLAUDE.md for the full picture",
    ]
    return "\n".join(lines)
