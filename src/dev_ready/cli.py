"""CLI entry point. Wiring only — no generation logic lives here.

Responsibilities (see docs/architecture.md, Module Boundary):
- argument parsing and command dispatch (docs/cli-spec.md)
- mapping typed exceptions to exit codes and messages
"""

import argparse
import re
import sys
from pathlib import Path

from dev_ready import __version__
from dev_ready.errors import AbortedError, DevReadyError, InvalidArgumentsError
from dev_ready.generate import generate
from dev_ready.manifest import load_default_manifest
from dev_ready.prompts import Answers, PartialAnswers, collect_answers, confirm_generation
from dev_ready.report import render_report

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
        "--no-skills", action="store_true", help="Skip Claude Code skills overlay"
    )
    init_parser.add_argument(
        "--no-mcp", action="store_true", help="Skip MCP server configuration overlay"
    )
    init_parser.add_argument(
        "--no-docs", action="store_true", help="Skip design-doc templates overlay"
    )
    return parser


def build_answers(args: argparse.Namespace) -> Answers:
    """Turn parsed flags into the shared Answers model.

    Interactive prompting for missing values lands in a later phase; until
    then the project name is required on the command line.
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
    target_dir = args.target_dir if args.target_dir is not None else Path.cwd() / name
    return Answers(
        project_name=name,
        target_dir=target_dir,
        include_skills=not args.no_skills,
        include_mcp=not args.no_mcp,
        include_docs=not args.no_docs,
        assume_yes=args.yes,
    )


def _build_partial_answers(args: argparse.Namespace) -> PartialAnswers:
    """Same flag mapping as `build_answers`, but tolerates a missing name —
    `collect_answers` prompts for whatever this leaves unanswered.
    """
    name = args.project_name
    if name is not None and not _PROJECT_NAME_PATTERN.fullmatch(name):
        raise InvalidArgumentsError(
            f"invalid project name {name!r}: use letters, digits, '.', '_', '-',"
            " starting with a letter or digit"
        )
    return PartialAnswers(
        project_name=name,
        target_dir=args.target_dir,
        include_skills=not args.no_skills,
        include_mcp=not args.no_mcp,
        include_docs=not args.no_docs,
        components_explicit=args.no_skills or args.no_mcp or args.no_docs,
        assume_yes=args.yes,
    )


def _run_init(args: argparse.Namespace) -> int:
    manifest = load_default_manifest()
    pin = manifest.upstream["base_template"]

    if args.yes:
        answers = build_answers(args)
    else:
        partial = _build_partial_answers(args)
        answers = collect_answers(partial)
        if not confirm_generation(answers, pin):
            print("aborted: nothing was written", file=sys.stderr)
            return 1

    written = generate(answers, pin)
    print(render_report(answers, pin, written))
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
        raise InvalidArgumentsError(f"unknown command: {args.command}")
    except AbortedError:
        print("aborted: nothing was written", file=sys.stderr)
        return 1
    except DevReadyError as error:
        print(f"error: {error}", file=sys.stderr)
        return error.exit_code
