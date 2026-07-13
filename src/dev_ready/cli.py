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
from dev_ready.errors import DevReadyError, InvalidArgumentsError
from dev_ready.generate import generate
from dev_ready.manifest import UpstreamPin, load_default_manifest
from dev_ready.prompts import Answers

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


def _run_init(args: argparse.Namespace) -> int:
    answers = build_answers(args)
    manifest = load_default_manifest()
    pin = manifest.upstream["base_template"]
    generate(answers, pin)
    _print_success(answers, pin)
    return 0


def _print_success(answers: Answers, pin: UpstreamPin) -> None:
    components = [
        name
        for name, included in (
            ("skills", answers.include_skills),
            ("mcp", answers.include_mcp),
            ("docs", answers.include_docs),
        )
        if included
    ]
    overlay_parts = ["CLAUDE.md", *components]
    print(f"project generated: {answers.project_name}")
    print(f"location:  {answers.target_dir}")
    print(f"upstream:  {pin.repo}@{pin.commit[:12]} ({pin.ref})")
    print(f"overlay:   {', '.join(overlay_parts)}")
    print()
    print("next steps:")
    print(f"  1. cd {answers.target_dir}")
    print("  2. docker compose watch   (see CLAUDE.md for other commands)")
    print("  3. read CLAUDE.md for the full picture")


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
    except DevReadyError as error:
        print(f"error: {error}", file=sys.stderr)
        return error.exit_code
