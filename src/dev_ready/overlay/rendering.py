"""Render overlay templates from a resolved project selection."""

from dataclasses import dataclass
from importlib.resources.abc import Traversable
from pathlib import Path

from dev_ready.agent_targets import CANONICAL_SKILLS_ROOT
from dev_ready.errors import OverlayError
from dev_ready.manifest import CATALOG_COMPONENTS, CatalogItem, ComponentCatalog
from dev_ready.prompts import Answers

TEMPLATE_SUFFIX = ".tmpl"
_DOCUMENTATION_ROOT = "docs"

_ARCHITECTURE_OWNERSHIP = (
    "Keep this architecture document current as module boundaries and "
    "dependency rules change."
)
_DOCUMENTATION_GUIDANCE = """## Architecture documentation

Read `docs/architecture.md` before structural changes; it records the system overview, module boundaries, and dependency rules."""

@dataclass(frozen=True)
class _FlowGuidance:
    rules: str
    setup_project: str


_EMPTY_FLOW_GUIDANCE = _FlowGuidance(rules="", setup_project="")
_FLOW_GUIDANCE = {
    "mattpocock": _FlowGuidance(
        rules="""## Engineering Flow

The default Flow Chain is `setup-project` → `grill-with-docs` → `to-spec` → `to-tickets` → `implement` → `improve-codebase-architecture`. Every step is user-invoked.

A step may reach for `tdd`, `code-review`, `diagnosing-bugs`, `codebase-design`, or `domain-modeling` as a tool; those tools are not additional chain entries.

Start at `implement` when the change adds no behaviour a user can observe — a rename, a formatting fix, a dependency bump, or a test for behaviour that already works. Start at `setup-project` or `grill-with-docs` for everything else.

Tracker and domain conventions are in `docs/agents/issue-tracker.md`, `docs/agents/triage-labels.md`, and `docs/agents/domain.md`. Follow those files when a skill asks where to publish specs or tickets; domain terminology is created lazily when a real term is resolved.""",
        setup_project="""The selected Engineering Flow also contributes **Issue tracker and domain conventions** to the section menu.

## Issue tracker and domain conventions

Read `docs/agents/issue-tracker.md`, `docs/agents/triage-labels.md`, and
`docs/agents/domain.md`. Report where specs and tickets currently live, the
triage-label vocabulary, and whether the domain document has been initialized.
Do not change any of those files while reporting their current state.

Ask whether the user wants this convention changed. Only if they answer yes,
explain that editing these managed files makes them user-modified, so a future
dev-ready upgrade preserves them and stops updating them. After the user accepts
that cost, hand off to `/setup-matt-pocock-skills`. Do not invoke that skill when
the user only asked to inspect current state.""",
    ),
}


def _selected_flow_guidance(answers: Answers) -> _FlowGuidance:
    flow_id = answers.selection.development_loop
    if not flow_id:
        return _EMPTY_FLOW_GUIDANCE
    try:
        return _FLOW_GUIDANCE[flow_id]
    except KeyError as error:
        raise OverlayError(f"flow guidance is missing: {flow_id}") from error


def _issue_tracker_configuration() -> str:
    return """# Issue tracker: local Markdown

Specs and tickets for this repository live as local Markdown files under `.scratch/`.

- Use one directory per feature: `.scratch/<feature-slug>/`.
- Publish the spec as `.scratch/<feature-slug>/spec.md`.
- Publish one tracer-bullet ticket per file under `.scratch/<feature-slug>/issues/`.
- Number tickets from `01`, record blocking edges, and use `Status: ready-for-agent` when approved.

When a skill says to publish to or fetch from the issue tracker, use these local files."""


def _clone_guidance(answers: Answers) -> str:
    if not answers.agent_targets:
        return ""
    return (
        "\nSelected coding agents discover those skills through machine-local "
        "links in their native skill directories. The links are not stored in "
        "git.\n\n"
        "## After cloning\n\n"
        "After cloning this repository, run `uvx dev-ready upgrade` once so "
        "those links are recreated.\n"
    )


def template_values(answers: Answers) -> dict[str, str]:
    """Return every supported template token for one resolved selection."""
    flow_guidance = _selected_flow_guidance(answers)
    return {
        "project_name": answers.project_name,
        "engineering_flow_guidance": flow_guidance.rules,
        "engineering_flow_setup": flow_guidance.setup_project,
        "documentation_guidance": _DOCUMENTATION_GUIDANCE,
        "architecture_ownership": _ARCHITECTURE_OWNERSHIP,
        "issue_tracker_configuration": _issue_tracker_configuration(),
        "clone_guidance": _clone_guidance(answers),
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
    return result


def inject_mounted_enhancements(
    content: dict[str, bytes], answers: Answers, catalog: ComponentCatalog
) -> None:
    """Append selected Enhancement guidance to its mounted loop skill."""
    mounted = mounted_enhancements(answers, catalog)
    for mounted_path, items in mounted.items():
        if mounted_path not in content:
            raise OverlayError(
                f"mounted development-loop skill is missing: {mounted_path}"
            )
        documentation_ids = catalog.item_ids("docs")
        per_item_entries = [
            f"- **{item.id}** — {item.description} See `{item.paths[0].dest}`."
            for item in items
            if item.id not in documentation_ids
        ]
        documentation_items = tuple(
            item for item in items if item.id in documentation_ids
        )
        if documentation_items:
            identifiers = ", ".join(f"`{item.id}`" for item in documentation_items)
            per_item_entries.append(
                f"- **Documentation references** — {identifiers}. "
                f"See `{_DOCUMENTATION_ROOT}/`."
            )
        entries = "\n".join(per_item_entries)
        block = (
            "<!-- dev-ready:mounted-enhancements:start -->\n"
            "## Mounted enhancements\n\n"
            "When running this skill, also apply the enhancements selected for this project.\n\n"
            f"{entries}\n"
            "<!-- dev-ready:mounted-enhancements:end -->\n"
        ).encode("utf-8")
        content[mounted_path] = content[mounted_path].rstrip(b"\r\n") + b"\n\n" + block


def mounted_enhancements(
    answers: Answers, catalog: ComponentCatalog
) -> dict[str, tuple[CatalogItem, ...]]:
    """Group selected mounted Enhancements by canonical loop-skill path."""
    mounted_items = tuple(
        item
        for component in CATALOG_COMPONENTS
        for item in catalog.get(component, ())
        if item.mount is not None and item.id in answers.items(component)
    )
    return {
        Path(*CANONICAL_SKILLS_ROOT, mount, "SKILL.md").as_posix(): tuple(
            item
            for item in sorted(mounted_items, key=lambda candidate: candidate.id)
            if item.mount == mount
        )
        for mount in sorted(
            {item.mount for item in mounted_items if item.mount is not None}
        )
    }
