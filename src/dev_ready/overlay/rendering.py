"""Render overlay templates from a resolved project selection."""

from dataclasses import dataclass
from importlib import resources
from importlib.resources.abc import Traversable
from pathlib import Path

from dev_ready.agent_targets import CANONICAL_SKILLS_ROOT
from dev_ready.errors import OverlayError
from dev_ready.manifest import CATALOG_COMPONENTS, CatalogItem, ComponentCatalog
from dev_ready.intent import Answers

TEMPLATE_SUFFIX = ".tmpl"
_DOCUMENTATION_ROOT = "docs"

_ARCHITECTURE_OWNERSHIP = (
    "Keep this architecture document current as module boundaries and "
    "dependency rules change."
)
_DOCUMENTATION_GUIDANCE = """## Architecture documentation

Read `docs/architecture.md` before structural changes; it records the system overview, module boundaries, and dependency rules."""

@dataclass(frozen=True)
class _AuthoredFlowGuidance:
    convention: str
    setup_project: str


@dataclass(frozen=True)
class _FlowGuidance:
    rules: str
    setup_project: str


_EMPTY_FLOW_GUIDANCE = _FlowGuidance(rules="", setup_project="")


def _render_chain_entry(entry: str | tuple[str, ...]) -> str:
    if isinstance(entry, str):
        return f"`{entry}`"
    return f"({' or '.join(f'`{opt}`' for opt in entry)})"


def render_chain_sentence(loop: CatalogItem) -> str:
    """Render the Flow Chain sentence from the loop's declared chain and invocation."""
    elements = ["`setup-project`", *(_render_chain_entry(e) for e in loop.chain)]
    chain_str = " → ".join(elements)
    if loop.invocation == "user":
        invocation_str = "Every step is user-invoked."
    elif loop.invocation == "model":
        invocation_str = "`setup-project` is user-invoked; subsequent steps are model-invoked."
    else:
        invocation_str = ""
    if invocation_str:
        return f"The default Flow Chain is {chain_str}. {invocation_str}"
    return f"The default Flow Chain is {chain_str}."


def render_flow_rules(loop: CatalogItem, guidance: _AuthoredFlowGuidance) -> str:
    """Render the full ## Engineering Flow section for AGENTS.md."""
    chain_sentence = render_chain_sentence(loop)
    if guidance.convention:
        return f"## Engineering Flow\n\n{chain_sentence}\n\n{guidance.convention}"
    return f"## Engineering Flow\n\n{chain_sentence}"


def _read_authored_prose(relative: str | None) -> str:
    if relative is None:
        return ""
    source = resources.files("dev_ready").joinpath("templates", *relative.split("/"))
    if not source.is_file():
        raise OverlayError(f"overlay asset missing: {relative}")
    try:
        return source.read_text(encoding="utf-8").rstrip("\n")
    except OSError as error:
        raise OverlayError(f"failed to read overlay asset for {relative}: {error}") from error


def _selected_flow_guidance(
    answers: Answers, catalog: ComponentCatalog
) -> _FlowGuidance:
    flow_id = answers.selection.development_loop
    if not flow_id:
        return _EMPTY_FLOW_GUIDANCE
    loop = next((item for item in catalog.loops() if item.id == flow_id), None)
    if loop is None:
        raise OverlayError(f"development loop {flow_id!r} not found in catalog")

    guidance = _AuthoredFlowGuidance(
        convention=_read_authored_prose(loop.convention),
        setup_project=_read_authored_prose(loop.setup_contribution),
    )
    rules = render_flow_rules(loop, guidance)
    return _FlowGuidance(rules=rules, setup_project=guidance.setup_project)


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


def template_values(
    answers: Answers, catalog: ComponentCatalog
) -> dict[str, str]:
    """Return every supported template token for one resolved selection."""
    flow_guidance = _selected_flow_guidance(answers, catalog)
    setup_snippet = (
        f"\n{flow_guidance.setup_project}\n"
        if flow_guidance.setup_project
        else ""
    )
    return {
        "project_name": answers.project_name,
        "engineering_flow_guidance": flow_guidance.rules,
        "engineering_flow_setup": setup_snippet,
        "documentation_guidance": _DOCUMENTATION_GUIDANCE,
        "architecture_ownership": _ARCHITECTURE_OWNERSHIP,
        "issue_tracker_configuration": _issue_tracker_configuration(),
        "clone_guidance": _clone_guidance(answers),
    }


def render_asset(
    source: Traversable,
    dest_rel: Path,
    answers: Answers | str,
    catalog: ComponentCatalog | None = None,
) -> bytes:
    """Render one package asset without writing it."""
    if not source.is_file():
        raise OverlayError(f"overlay asset missing: {source}")
    try:
        if source.name.endswith(TEMPLATE_SUFFIX):
            rendered = source.read_text(encoding="utf-8")
            if isinstance(answers, Answers):
                if catalog is None:
                    raise OverlayError("catalog is required to render project templates")
                values = template_values(answers, catalog)
            else:
                values = {"project_name": answers}
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
    selected_loop_id = answers.development_loop
    loop = next(
        (candidate for candidate in catalog.loops() if candidate.id == selected_loop_id),
        None,
    )
    if loop is None and selected_loop_id:
        raise OverlayError(
            f"development loop {selected_loop_id!r} not found in catalog"
        )
    roles = loop.roles if loop is not None else {}

    mounted_items = tuple(
        item
        for component in CATALOG_COMPONENTS
        for item in catalog.get(component, ())
        if item.mount is not None and item.id in answers.items(component)
    )

    step_items: dict[str, list[CatalogItem]] = {}
    for item in mounted_items:
        if item.mount is not None:
            for step in roles.get(item.mount, ()):
                step_items.setdefault(step, []).append(item)

    return {
        Path(*CANONICAL_SKILLS_ROOT, step, "SKILL.md").as_posix(): tuple(
            sorted(items, key=lambda candidate: candidate.id)
        )
        for step, items in sorted(step_items.items())
    }
