"""Render overlay templates from a resolved project selection."""

from importlib.resources.abc import Traversable
from pathlib import Path

from dev_ready.errors import OverlayError
from dev_ready.prompts import Answers

TEMPLATE_SUFFIX = ".tmpl"


def _handoff_guidance(answers: Answers) -> str:
    if not answers.includes("agents"):
        return ""
    return """## Handoff Protocol

`docs/handoffs/protocol.yaml` is the authoritative Protocol Configuration. Read it together with `docs/handoffs/README.md` before using the reusable process-v2 phase scaffold."""


def _spec_loop_guidance(answers: Answers) -> str:
    if "spec-loop" not in answers.items("skills"):
        return ""
    return """## Spec Loop

Use the installed loop as one end-to-end method: `grill-with-docs` -> `to-spec` -> `to-tickets` -> `tdd` -> `code-review` -> `improve-codebase-architecture`. Use `diagnosing-bugs` when failures need root-cause analysis.

Tracker and domain conventions are in `docs/agents/issue-tracker.md`, `docs/agents/triage-labels.md`, and `docs/agents/domain.md`. Follow those files when a skill asks where to publish specs or tickets; domain terminology is created lazily when a real term is resolved."""


def _methodology_mapping(answers: Answers) -> str:
    if not answers.includes("agents") or "spec-loop" not in answers.items("skills"):
        return ""
    return """## Process-v2 role mapping

- Planning - `tech_lead`: `grill-with-docs` and `to-spec`.
- Dispatch - `senior_engineer`: `to-tickets` and the Handoff Protocol.
- Execution - `junior_engineer`: `tdd`, `diagnosing-bugs`, and `code-review` within one ticket footprint.
- Verification - `qa_reviewer`, `security_reviewer`, and `sre_reviewer`: independent gates after `senior_engineer` spec review."""


def _documentation_values(answers: Answers) -> tuple[str, str, str]:
    guidance = ""
    ownership = (
        "Keep this architecture document current as module boundaries and "
        "dependency rules change."
    )
    tech_lead_responsibility = ""
    if not answers.includes("docs"):
        return guidance, ownership, tech_lead_responsibility

    guidance = """## Architecture documentation

Read `docs/architecture.md` before structural changes; it records the system overview, module boundaries, and dependency rules."""
    if answers.includes("agents"):
        guidance += " The Protocol Configuration assigns its maintenance to `tech_lead`."
        ownership = (
            "The `tech_lead` role maintains this document under "
            "`docs/handoffs/protocol.yaml`."
        )
        tech_lead_responsibility = (
            "      - Maintain docs/architecture.md as binding architecture guidance."
        )
    return guidance, ownership, tech_lead_responsibility


def _issue_tracker_configuration(answers: Answers) -> str:
    if answers.includes("agents"):
        return """# Issue tracker: Handoff Protocol files

Read `docs/handoffs/protocol.yaml` before publishing planning or dispatch artifacts.

- Durable accepted specs live under `docs/specs/<version>/`.
- Publish one tracer-bullet ticket per file under `docs/handoffs/phase-<number>/tickets/`.
- Record blocking edges, the exact file footprint, `parallel-safe`, and `Status: ready-for-agent` in each ticket.
- Active phase gates and reports live beside the tickets under the same numeric phase directory.

When a skill says to publish to or fetch from the issue tracker, use these local process-v2 paths."""

    return """# Issue tracker: local Markdown

Specs and tickets for this repository live as local Markdown files under `.scratch/`.

- Use one directory per feature: `.scratch/<feature-slug>/`.
- Publish the spec as `.scratch/<feature-slug>/spec.md`.
- Publish one tracer-bullet ticket per file under `.scratch/<feature-slug>/issues/`.
- Number tickets from `01`, record blocking edges, and use `Status: ready-for-agent` when approved.

When a skill says to publish to or fetch from the issue tracker, use these local files."""


def template_values(answers: Answers) -> dict[str, str]:
    """Return every supported template token for one resolved selection."""
    guidance, ownership, tech_lead_responsibility = _documentation_values(answers)
    return {
        "project_name": answers.project_name,
        "handoff_protocol_guidance": _handoff_guidance(answers),
        "spec_loop_guidance": _spec_loop_guidance(answers),
        "methodology_mapping": _methodology_mapping(answers),
        "documentation_guidance": guidance,
        "architecture_ownership": ownership,
        "tech_lead_architecture_responsibility": tech_lead_responsibility,
        "issue_tracker_configuration": _issue_tracker_configuration(answers),
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
