"""CLI entry point. Wiring only — no generation logic lives here.

Responsibilities (see docs/architecture.md, Module Boundary):
- argument parsing and command dispatch (docs/cli-spec.md)
- mapping typed exceptions to exit codes and messages
"""

import argparse
import sys
import threading
from pathlib import Path
from typing import TextIO

from dev_ready import __version__
from dev_ready.check import check_project
from dev_ready.errors import AbortedError, DevReadyError, InvalidArgumentsError
from dev_ready.generate import (
    CleanupWarningEvent,
    GenerationEvent,
    GenerationStage,
    ProgressEvent,
    ProgressStatus,
    generate,
)
from dev_ready.manifest import ComponentCatalog, load_default_manifest
from dev_ready.prompts import (
    Answers,
    PartialAnswers,
    ProjectSelection,
    collect_answers,
    confirm_generation,
)
from dev_ready.report import render_report
from dev_ready.upgrade import upgrade_project

_STAGE_POSITION = {
    GenerationStage.FETCH: 1,
    GenerationStage.OVERLAY: 2,
    GenerationStage.VERIFY: 3,
    GenerationStage.FINALIZE: 4,
}

_CATEGORY_FLAGS = ("dev", "security", "quality", "design", "token-optimize")
_REMOVED_SELECTION_FLAGS = {
    "--no-handoff": "it was removed because dev-ready no longer generates the Handoff Protocol",
    "--no-agents": "it was removed because dev-ready no longer generates the Handoff Protocol",
    "--skills": "use --categories and the per-Category item flags instead",
    "--no-skills": "use --categories and the per-Category item flags instead",
    "--mcp": "use --token-optimize to select code-memory instead",
    "--no-mcp": "use --token-optimize none instead",
    "--no-docs": "use --design none instead",
}


class ProgressRenderer:
    """Render generation progress at the terminal boundary."""

    _FRAMES = ("⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏")

    def __init__(
        self,
        stream: TextIO,
        *,
        is_tty: bool | None = None,
        spinner_interval: float = 0.08,
    ) -> None:
        self._stream = stream
        self._is_tty = stream.isatty() if is_tty is None else is_tty
        self._spinner_interval = spinner_interval
        self._closed = False
        self._write_lock = threading.Lock()
        self._spinner_stop: threading.Event | None = None
        self._spinner_thread: threading.Thread | None = None
        self._active_text = ""

    def __call__(self, event: GenerationEvent) -> None:
        if self._closed:
            return
        if isinstance(event, CleanupWarningEvent):
            self._stop_spinner()
            self._write(f"warning: failed to remove temp directory {event.path}\n")
            return
        position = _STAGE_POSITION[event.stage]
        description = self._description(event)
        if event.status is ProgressStatus.STARTED:
            text = f"[{position}/4] {description}…"
            if self._is_tty:
                self._start_spinner(text)
            else:
                self._write(f"{text}\n")
            return
        self._stop_spinner()
        outcome = "done" if event.status is ProgressStatus.COMPLETED else "failed"
        elapsed = max(0.0, event.elapsed_seconds or 0.0)
        self._write(f"[{position}/4] {description} {outcome} ({elapsed:.2f}s)\n")

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._stop_spinner()

    def _start_spinner(self, text: str) -> None:
        self._stop_spinner()
        stop = threading.Event()
        self._spinner_stop = stop
        self._active_text = text
        self._write(f"\r{self._FRAMES[0]} {text}")

        def _animate() -> None:
            frame_index = 1
            while not stop.wait(self._spinner_interval):
                self._write(f"\r{self._FRAMES[frame_index]} {text}")
                frame_index = (frame_index + 1) % len(self._FRAMES)

        thread = threading.Thread(target=_animate, name="dev-ready-progress", daemon=True)
        self._spinner_thread = thread
        thread.start()

    def _stop_spinner(self) -> None:
        stop = self._spinner_stop
        thread = self._spinner_thread
        active_text = self._active_text
        self._spinner_stop = None
        self._spinner_thread = None
        self._active_text = ""
        if stop is None:
            return
        stop.set()
        if thread is not None:
            thread.join(timeout=0.2)
        self._write(f"\r{' ' * (len(active_text) + 2)}\r")

    def _description(self, event: ProgressEvent) -> str:
        if event.stage is GenerationStage.FETCH:
            if event.status is ProgressStatus.STARTED:
                return f"Fetching base template (commit {event.commit})"
            return "Fetching base template"
        return {
            GenerationStage.OVERLAY: "Applying dev-ready overlay",
            GenerationStage.VERIFY: "Verifying generated project",
            GenerationStage.FINALIZE: "Finalizing project",
        }[event.stage]

    def _write(self, text: str) -> None:
        try:
            with self._write_lock:
                self._stream.write(text)
                self._stream.flush()
        except Exception:
            # Rendering is observational and must not affect generation.
            pass

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
        "-y", "--yes", action="store_true", help="Accept the Default Set, no prompts"
    )
    init_parser.add_argument(
        "--dir",
        dest="target_dir",
        type=Path,
        default=None,
        help="Target directory (default: ./PROJECT_NAME)",
    )
    init_parser.add_argument(
        "--categories",
        default=None,
        help="Category selection: comma-separated ids, or 'all' / 'none'.",
    )
    init_parser.add_argument(
        "--flow",
        "--development-loop",
        dest="development_loop",
        metavar="ID",
        default=None,
        help="Mandatory Engineering Flow id (defaults to the manifest Default Set).",
    )
    for category in _CATEGORY_FLAGS:
        init_parser.add_argument(
            f"--{category}",
            dest=category.replace("-", "_"),
            default=None,
            help=(
                f"{category.replace('-', ' ').title()} item selection: "
                "comma-separated ids, or 'all' / 'none'."
            ),
        )
    init_parser.add_argument(
        "--agents",
        default=None,
        help="Agent Target selection: comma-separated ids, or 'all' / 'none'.",
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



def build_answers(
    args: argparse.Namespace, catalog: ComponentCatalog
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
    selection = ProjectSelection.from_flags(
        catalog=catalog,
        categories=args.categories,
        category_items=_category_items_from_args(args),
        development_loop=getattr(args, "development_loop", None),
    ) or ProjectSelection.default_set(catalog)
    if args.agents is not None:
        selection = selection.with_agent_targets(
            catalog,
            ProjectSelection.agent_targets_from_flag(catalog, args.agents),
        )

    target_dir = args.target_dir if args.target_dir is not None else Path.cwd() / name
    return Answers(
        project_name=name,
        target_dir=target_dir,
        selection=selection,
        assume_yes=args.yes,
    )


def _build_partial_answers(
    args: argparse.Namespace, catalog: ComponentCatalog
) -> PartialAnswers:
    """Same flag mapping as `build_answers`, but tolerates a missing name —
    `collect_answers` prompts for whatever this leaves unanswered.
    """
    name = args.project_name
    selection = ProjectSelection.from_flags(
        catalog=catalog,
        categories=args.categories,
        category_items=_category_items_from_args(args),
        development_loop=getattr(args, "development_loop", None),
    )
    agent_targets = (
        ProjectSelection.agent_targets_from_flag(catalog, args.agents)
        if args.agents is not None
        else None
    )
    if selection is not None and agent_targets is not None:
        selection = selection.with_agent_targets(catalog, agent_targets)
        agent_targets = None

    return PartialAnswers(
        project_name=name,
        target_dir=args.target_dir,
        selection=selection,
        agent_targets=agent_targets,
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

    progress = ProgressRenderer(sys.stderr)
    try:
        written = generate(
            answers,
            pin,
            manifest.components,
            vendored=manifest.vendored,
            progress=progress,
        )
    finally:
        progress.close()
    print(render_report(answers, pin, written, manifest.components))
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


def _category_items_from_args(args: argparse.Namespace) -> dict[str, str | None]:
    return {
        category: getattr(args, category.replace("-", "_"))
        for category in _CATEGORY_FLAGS
    }


def _reject_removed_selection_flags(argv: list[str]) -> None:
    for argument in argv:
        flag = argument.partition("=")[0]
        replacement = _REMOVED_SELECTION_FLAGS.get(flag)
        if replacement is not None:
            raise InvalidArgumentsError(
                f"{flag} was removed; {replacement}"
            )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    resolved_argv = sys.argv[1:] if argv is None else argv
    try:
        _reject_removed_selection_flags(resolved_argv)
        args = parser.parse_args(resolved_argv)
        if args.command is None:
            parser.print_help()
            return 0
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
