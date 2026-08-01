"""Render overlay templates from a resolved project selection."""

from importlib.resources.abc import Traversable
from pathlib import Path

from dev_ready.errors import OverlayError
from dev_ready.prompts import Answers

TEMPLATE_SUFFIX = ".tmpl"

_UNSELECTED_SETUP_REPLACEMENTS = {
    ".agents/skills/code-review/SKILL.md": (
        (
            "The issue tracker should have been provided to you — run "
            "`/setup-matt-pocock-skills` if `docs/agents/issue-tracker.md` is missing.",
            "Issue tracker configuration is in `docs/agents/issue-tracker.md`.",
        ),
    ),
    ".agents/skills/to-spec/SKILL.md": (
        (
            "The issue tracker and triage label vocabulary should have been provided "
            "to you — run `/setup-matt-pocock-skills` if not.",
            "Issue tracker and triage conventions are in `docs/agents/`.",
        ),
    ),
    ".agents/skills/to-tickets/SKILL.md": (
        (
            "The issue tracker and triage label vocabulary should have been provided "
            "to you — run `/setup-matt-pocock-skills` if not.",
            "Issue tracker and triage conventions are in `docs/agents/`.",
        ),
        (
            "Publish the approved tickets. **How** depends on the tracker "
            "`/setup-matt-pocock-skills` configured — the tickets are the same either "
            "way, only the shape of the blocking edges changes:",
            "Publish the approved tickets using `docs/agents/issue-tracker.md` — "
            "the tickets are the same for every tracker; only the shape of the "
            "blocking edges changes:",
        ),
    ),
}


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
            result = rendered.encode("utf-8")
        else:
            result = source.read_bytes()
    except OSError as error:
        raise OverlayError(f"failed to read overlay asset for {dest_rel}: {error}") from error
    if isinstance(answers, Answers):
        return _adapt_unselected_setup_references(result, dest_rel, answers)
    return result


def _adapt_unselected_setup_references(
    rendered: bytes,
    dest_rel: Path,
    answers: Answers,
) -> bytes:
    """Keep loop guidance self-contained when its setup Enhancement is absent."""
    replacements = _UNSELECTED_SETUP_REPLACEMENTS.get(dest_rel.as_posix(), ())
    if not replacements or "setup-all" in answers.items("skills"):
        return rendered
    text = rendered.decode("utf-8")
    for old, new in replacements:
        if old not in text:
            raise OverlayError(f"expected setup guidance is missing from {dest_rel.as_posix()}")
        text = text.replace(old, new)
    return text.encode("utf-8")
