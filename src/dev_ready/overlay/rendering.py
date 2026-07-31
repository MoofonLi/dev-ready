"""Render overlay templates from a resolved project selection."""

from importlib.resources.abc import Traversable
from pathlib import Path

from dev_ready.errors import OverlayError
from dev_ready.prompts import Answers

TEMPLATE_SUFFIX = ".tmpl"


def _spec_loop_guidance(answers: Answers) -> str:
    if "spec-loop" not in answers.items("skills"):
        return ""
    return """## Spec Loop

Use the installed loop as one end-to-end method: `grill-with-docs` -> `to-spec` -> `to-tickets` -> `tdd` -> `code-review` -> `improve-codebase-architecture`. Use `diagnosing-bugs` when failures need root-cause analysis.

Tracker and domain conventions are in `docs/agents/issue-tracker.md`, `docs/agents/triage-labels.md`, and `docs/agents/domain.md`. Follow those files when a skill asks where to publish specs or tickets; domain terminology is created lazily when a real term is resolved."""


def _documentation_values(answers: Answers) -> tuple[str, str]:
    guidance = ""
    ownership = (
        "Keep this architecture document current as module boundaries and "
        "dependency rules change."
    )
    if not answers.includes("docs"):
        return guidance, ownership

    guidance = """## Architecture documentation

Read `docs/architecture.md` before structural changes; it records the system overview, module boundaries, and dependency rules."""
    return guidance, ownership


def _issue_tracker_configuration() -> str:
    return """# Issue tracker: local Markdown

Specs and tickets for this repository live as local Markdown files under `.scratch/`.

- Use one directory per feature: `.scratch/<feature-slug>/`.
- Publish the spec as `.scratch/<feature-slug>/spec.md`.
- Publish one tracer-bullet ticket per file under `.scratch/<feature-slug>/issues/`.
- Number tickets from `01`, record blocking edges, and use `Status: ready-for-agent` when approved.

When a skill says to publish to or fetch from the issue tracker, use these local files."""


def template_values(answers: Answers) -> dict[str, str]:
    """Return every supported template token for one resolved selection."""
    guidance, ownership = _documentation_values(answers)
    return {
        "project_name": answers.project_name,
        "spec_loop_guidance": _spec_loop_guidance(answers),
        "documentation_guidance": guidance,
        "architecture_ownership": ownership,
        "issue_tracker_configuration": _issue_tracker_configuration(),
    }


def render_asset(
    source: Traversable, dest_rel: Path, answers: Answers | str
) -> bytes:
    """Render one package asset without writing it."""
    if not source.is_file():
        raise OverlayError(f"overlay asset missing: {source}")
    try:
        if source.name.endswith(TEMPLATE_SUFFIX):
            rendered = source.read_text(encoding="utf-8")
            values = (
                template_values(answers)
                if isinstance(answers, Answers)
                else {"project_name": answers}
            )
            for name, value in values.items():
                rendered = rendered.replace(f"{{{{{name}}}}}", value)
            if "{{" in rendered or "}}" in rendered:
                raise OverlayError(f"unresolved template marker left in {dest_rel}")
            return rendered.encode("utf-8")
        return source.read_bytes()
    except OSError as error:
        raise OverlayError(f"failed to read overlay asset for {dest_rel}: {error}") from error
