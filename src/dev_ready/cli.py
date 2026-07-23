"""CLI entry point. Wiring only — no generation logic lives here.

Responsibilities (see docs/architecture.md, Module Boundary):
- argument parsing and command dispatch (docs/cli-spec.md)
- mapping typed exceptions to exit codes and messages
"""

import argparse
import re
import sys
from collections.abc import Mapping
from pathlib import Path

from dev_ready import __version__
from dev_ready.check import check_project
from dev_ready.errors import AbortedError, DevReadyError, InvalidArgumentsError
from dev_ready.generate import generate
from dev_ready.manifest import CatalogItem, load_default_manifest
from dev_ready.prompts import Answers, PartialAnswers, collect_answers, confirm_generation
from dev_ready.report import render_report
from dev_ready.upgrade import upgrade_project

_PROJECT_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]*$")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dev-ready",
        description="Scaffold AI-development-ready FastAPI projects.",
    )
    parser.add_argument(
        "--version", action="version", version=f"dev-ready {__version__}"
    )
    subparsers = parser.add_subparsers(dest="command")

    init_parser = subparsers.add_parser("init", help="Generate a new project")
    init_parser.add_argument(
        "project_name", nargs="?", help="Name of the project to generate"
    )
    init_parser.add_argument(
        "-y", "--yes", action="store_true", help="Accept all defaults, no prompts"
    )
    init_parser.add_argument(
        "--dir",
        dest="target_dir",
        type=Path,
        default=None,
        help="Target directory (default: ./PROJECT_NAME)",
    )
    init_parser.add_argument(
        "--skills",
        dest="skills",
        default=None,
        help="Item selection for the skills component: comma-separated ids, or 'all' / 'none'.",
    )
    init_parser.add_argument(
        "--mcp",
        dest="mcp",
        default=None,
        help="Item selection for the mcp component: comma-separated ids, or 'all' / 'none'.",
    )
    init_parser.add_argument(
        "--no-skills", action="store_true", help="Skip Claude Code skills overlay"
    )
    init_parser.add_argument(
        "--no-mcp", action="store_true", help="Skip MCP server configuration overlay"
    )
    init_parser.add_argument(
        "--no-docs", action="store_true", help="Skip design-doc templates overlay"
    )
    init_parser.add_argument(
        "--no-agents", action="store_true", help="Exclude the agent-team handoff scaffold (docs/handoffs/)."
    )

    check_parser = subparsers.add_parser(
        "check", help="Inspect an existing project for structural or pin drift"
    )
    check_parser.add_argument(
        "target_dir",
        nargs="?",
        type=Path,
        default=Path("."),
        help="Target project directory to check (default: .)",
    )
    check_parser.add_argument(
        "--json",
        action="store_true",
        help="Output report in JSON format",
    )

    upgrade_parser = subparsers.add_parser(
        "upgrade", help="Re-apply managed overlay files without touching application code"
    )
    upgrade_parser.add_argument(
        "target_dir",
        nargs="?",
        type=Path,
        default=Path("."),
        help="Target project directory to upgrade (default: .)",
    )
    upgrade_parser.add_argument(
        "--dry-run", action="store_true", help="Report planned changes without writing files"
    )
    return parser



def _resolve_item_selection(
    component: str, raw_value: str | None, no_flag: bool, catalog_ids: frozenset[str]
) -> frozenset[str] | None:
    """None => unspecified (prompt or default-all later). Else a concrete id set."""
    if no_flag and raw_value is not None and raw_value.strip().lower() != "none":
        raise InvalidArgumentsError(
            f"--no-{component} conflicts with --{component} {raw_value!r}; use one."
        )
    if no_flag:
        return frozenset()
    if raw_value is None:
        return None

    val = raw_value.strip().lower()
    if val == "all":
        return catalog_ids
    if val == "none":
        return frozenset()

    requested = set()
    for item in raw_value.split(","):
        stripped = item.strip()
        if stripped:
            requested.add(stripped)

    if not requested:
        raise InvalidArgumentsError(f"empty item selection for --{component}")

    unknown = sorted(requested - catalog_ids)
    if unknown:
        raise InvalidArgumentsError(
            f"unknown {component} item ids: {unknown!r}; valid ids: {sorted(catalog_ids)!r}"
        )
    return frozenset(requested)


def build_answers(
    args: argparse.Namespace, catalog: Mapping[str, tuple[CatalogItem, ...]]
) -> Answers:
    """Turn parsed flags into the shared Answers model.

    Used only on the --yes path, where all values must come from the command
    line; the interactive path goes through `_build_partial_answers` +
    `collect_answers` instead.
    """
    name = args.project_name
    if not name:
        raise InvalidArgumentsError(
            "project name is required: dev-ready init <project-name>"
        )
    if not _PROJECT_NAME_PATTERN.fullmatch(name):
        raise InvalidArgumentsError(
            f"invalid project name {name!r}: use letters, digits, '.', '_', '-',"
            " starting with a letter or digit"
        )

    all_skill_ids = frozenset(i.id for i in catalog.get("skills", ()))
    all_mcp_ids = frozenset(i.id for i in catalog.get("mcp", ()))

    skills_resolved = _resolve_item_selection("skills", args.skills, args.no_skills, all_skill_ids)
    mcp_resolved = _resolve_item_selection("mcp", args.mcp, args.no_mcp, all_mcp_ids)

    skills_items = skills_resolved if skills_resolved is not None else all_skill_ids
    mcp_items = mcp_resolved if mcp_resolved is not None else all_mcp_ids

    target_dir = args.target_dir if args.target_dir is not None else Path.cwd() / name
    return Answers(
        project_name=name,
        target_dir=target_dir,
        include_skills=bool(skills_items),
        include_mcp=bool(mcp_items),
        include_docs=not args.no_docs,
        include_agents=not args.no_agents,
        skills_items=skills_items,
        mcp_items=mcp_items,
        assume_yes=args.yes,
    )


def _build_partial_answers(
    args: argparse.Namespace, catalog: Mapping[str, tuple[CatalogItem, ...]]
) -> PartialAnswers:
    """Same flag mapping as `build_answers`, but tolerates a missing name —
    `collect_answers` prompts for whatever this leaves unanswered.
    """
    name = args.project_name
    if name is not None and not _PROJECT_NAME_PATTERN.fullmatch(name):
        raise InvalidArgumentsError(
            f"invalid project name {name!r}: use letters, digits, '.', '_', '-',"
            " starting with a letter or digit"
        )

    all_skill_ids = frozenset(i.id for i in catalog.get("skills", ()))
    all_mcp_ids = frozenset(i.id for i in catalog.get("mcp", ()))

    skills_resolved = _resolve_item_selection("skills", args.skills, args.no_skills, all_skill_ids)
    mcp_resolved = _resolve_item_selection("mcp", args.mcp, args.no_mcp, all_mcp_ids)

    components_explicit = (
        args.no_skills
        or args.no_mcp
        or args.no_docs
        or args.no_agents
        or args.skills is not None
        or args.mcp is not None
    )

    if components_explicit:
        skills_selection = skills_resolved if skills_resolved is not None else all_skill_ids
        mcp_selection = mcp_resolved if mcp_resolved is not None else all_mcp_ids
    else:
        skills_selection = None
        mcp_selection = None

    include_skills = (
        bool(skills_selection) if skills_selection is not None else (not args.no_skills)
    )
    include_mcp = bool(mcp_selection) if mcp_selection is not None else (not args.no_mcp)

    return PartialAnswers(
        project_name=name,
        target_dir=args.target_dir,
        include_skills=include_skills,
        include_mcp=include_mcp,
        include_docs=not args.no_docs,
        include_agents=not args.no_agents,
        components_explicit=components_explicit,
        skills_selection=skills_selection,
        mcp_selection=mcp_selection,
        assume_yes=args.yes,
    )


def _run_init(args: argparse.Namespace) -> int:
    manifest = load_default_manifest()
    pin = manifest.upstream["base_template"]

    if args.yes:
        answers = build_answers(args, manifest.components)
    else:
        partial = _build_partial_answers(args, manifest.components)
        answers = collect_answers(partial, catalog=manifest.components)
        if not confirm_generation(answers, pin):
            print("aborted: nothing was written", file=sys.stderr)
            return 1

    written = generate(answers, pin, manifest.components, vendored=manifest.vendored)
    print(render_report(answers, pin, written))
    return 0


def _run_check(args: argparse.Namespace) -> int:
    target_dir = args.target_dir if args.target_dir is not None else Path(".")
    report = check_project(target_dir, json_output=args.json)
    print(report, end="")
    return 0


def _run_upgrade(args: argparse.Namespace) -> int:
    report = upgrade_project(args.target_dir, dry_run=args.dry_run)
    print(report, end="")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0
    try:
        if args.command == "init":
            return _run_init(args)
        if args.command == "check":
            return _run_check(args)
        if args.command == "upgrade":
            return _run_upgrade(args)
        raise InvalidArgumentsError(f"unknown command: {args.command}")
    except AbortedError:
        print("aborted: nothing was written", file=sys.stderr)
        return 1
    except DevReadyError as error:
        print(f"error: {error}", file=sys.stderr)
        return error.exit_code
