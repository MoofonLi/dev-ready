"""Offline, all-or-nothing re-application of overlay-managed project files."""

import hashlib
import shutil
import tempfile
from pathlib import Path

from dev_ready import __version__
from dev_ready.errors import UpgradeError, UpgradeNotSupportedError
from dev_ready.manifest import load_default_manifest
from dev_ready.overlay import build_overlay_content, content_inventory, render_stamp
from dev_ready.prompts import Answers
from dev_ready.stamp import load_stamp


def _write_target(path: Path, data: bytes) -> None:
    """Write one planned target; kept tiny so commit failures are testable."""
    path.write_bytes(data)


def _is_within(root: Path, path: Path) -> bool:
    try:
        path.resolve().relative_to(root)
    except ValueError:
        return False
    return True


def _has_symlink_component(root: Path, path: Path) -> bool:
    """Return whether ``path`` traverses a symlink beneath ``root``."""
    try:
        relative = path.relative_to(root)
    except ValueError:
        return True
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            return True
    return False


def _format_report(
    project_dir: Path,
    recorded_version: str,
    stamp_version: int,
    groups: dict[str, list[str]],
    dry_run: bool,
) -> str:
    prefix = "would " if dry_run else ""
    labels = (
        ("Upgraded", "upgraded"),
        ("Added", "added"),
        ("Skipped (user-modified)", "skipped_modified"),
        ("Skipped (shared, not auto-upgraded)", "skipped_shared"),
        ("Skipped (missing)", "skipped_missing"),
        ("Conflict", "conflict"),
        ("Obsolete", "obsolete"),
    )
    lines = [
        f"dev-ready upgrade report for {project_dir}",
        f"Generated with: dev-ready {recorded_version} (stamp version {stamp_version})",
        f"Current CLI: dev-ready {__version__}",
        "",
    ]
    for heading, key in labels:
        entries = groups[key]
        lines.append(f"{heading} ({len(entries)}):")
        for path in entries:
            action = f"{prefix}{path}" if key in {"upgraded", "added"} else path
            lines.append(f"  - {action}")
    action_word = "would change" if dry_run else "changed"
    lines.append("")
    lines.append(
        f"Summary: {len(groups['upgraded'])} upgraded, {len(groups['added'])} added; "
        f"{action_word} {len(groups['upgraded']) + len(groups['added'])} overlay-managed files."
    )
    return "\n".join(lines) + "\n"


def upgrade_project(project_dir: Path, dry_run: bool = False) -> str:
    """Safely update only clean, whole-file overlay content in ``project_dir``.

    The inventory is trusted only for its hashes and report strings: every path
    considered for filesystem access is rebuilt from the current manifest.
    """
    resolved = project_dir.resolve()
    stamp = load_stamp(project_dir)
    if stamp.stamp_version < 3 or not stamp.inventory or stamp.project_name is None:
        raise UpgradeNotSupportedError(
            "projects generated with dev-ready v0.3–v0.5 can be inspected with "
            "dev-ready check but not upgraded; regenerate the project to enable upgrades."
        )

    manifest = load_default_manifest()
    pin = manifest.upstream["base_template"]
    answers = Answers(
        project_name=stamp.project_name,
        target_dir=resolved,
        include_skills=stamp.skills_included,
        include_mcp=stamp.mcp_included,
        include_docs=stamp.docs_included,
        include_agents=stamp.agents_included,
        skills_items=frozenset(item.id for item in stamp.skills_items),
        mcp_items=frozenset(item.id for item in stamp.mcp_items),
    )
    new_content = build_overlay_content(answers, manifest.components)
    inject_targets = {
        item.inject.target
        for items in manifest.components.values()
        for item in items
        if item.inject is not None
    }
    selected_inject_targets = {
        item.inject.target
        for component, selected in (("skills", answers.skills_items), ("mcp", answers.mcp_items))
        for item in manifest.components.get(component, ())
        if item.id in selected and item.inject is not None
    }
    recorded = {entry.path: entry.sha256 for entry in stamp.inventory}
    groups: dict[str, list[str]] = {
        "upgraded": [],
        "added": [],
        "skipped_modified": [],
        "skipped_shared": [],
        "skipped_missing": [],
        "conflict": [],
        "obsolete": sorted(path for path in recorded if path not in new_content),
    }
    upgrades: list[tuple[Path, bytes]] = []
    adds: list[tuple[Path, bytes]] = []

    for path in sorted(new_content):
        target = resolved / path
        if not _is_within(resolved, target):
            raise UpgradeError(f"manifest overlay path escapes project directory: {path}")
        if _has_symlink_component(resolved, target):
            groups["conflict"].append(path)
            continue
        if path in inject_targets:
            groups["skipped_shared"].append(path)
            continue
        if path in recorded:
            if not target.exists() or target.is_symlink() and not target.resolve().exists():
                groups["skipped_missing"].append(path)
                continue
            if not target.is_file():
                groups["conflict"].append(path)
                continue
            current = target.read_bytes()
            if hashlib.sha256(current).hexdigest() != recorded[path]:
                groups["skipped_modified"].append(path)
            elif current == new_content[path]:
                # It is present and current, so it belongs in no action group.
                continue
            else:
                groups["upgraded"].append(path)
                upgrades.append((target, new_content[path]))
        elif target.exists() or target.is_symlink():
            groups["conflict"].append(path)
        else:
            groups["added"].append(path)
            adds.append((target, new_content[path]))

    # Some injection targets (for example frontend/package.json) are not
    # whole-file overlay content. They still merit an explicit report when the
    # selected item owns an injection there, because upgrade intentionally
    # never touches them.
    already_reported_shared = set(groups["skipped_shared"])
    groups["skipped_shared"].extend(
        sorted(selected_inject_targets - already_reported_shared - set(new_content))
    )

    new_stamp = render_stamp(
        answers,
        pin,
        manifest.components,
        manifest.vendored,
        content_inventory(new_content),
    ).encode("utf-8")
    stamp_path = resolved / ".dev-ready.json"
    if not _is_within(resolved, stamp_path) or _has_symlink_component(resolved, stamp_path):
        raise UpgradeError("stamp path is unsafe for upgrade")
    try:
        stamp_changed = new_stamp != stamp_path.read_bytes()
    except OSError as error:
        raise UpgradeError(f"failed to read .dev-ready.json during upgrade: {error}") from error

    report = _format_report(resolved, stamp.dev_ready_version, stamp.stamp_version, groups, dry_run)
    has_writes = bool(upgrades or adds) or stamp_changed
    if dry_run or not has_writes:
        return report

    backup_root = Path(tempfile.mkdtemp(prefix="dev-ready-upgrade-"))
    overwritten = [target for target, _ in upgrades] + [stamp_path]
    backups: dict[Path, Path] = {}
    created_files: list[Path] = []
    created_dirs: list[Path] = []
    try:
        for index, target in enumerate(overwritten):
            backup = backup_root / str(index)
            shutil.copy2(target, backup)
            backups[target] = backup

        for target, data in upgrades:
            _write_target(target, data)
        for target, data in adds:
            parent = target.parent
            to_create: list[Path] = []
            while not parent.exists():
                to_create.append(parent)
                parent = parent.parent
            # Record intended paths before mkdir: it can create a subset and
            # then fail, in which case rollback still has to remove that subset.
            created_dirs.extend(to_create)
            target.parent.mkdir(parents=True, exist_ok=True)
            _write_target(target, data)
            created_files.append(target)
        _write_target(stamp_path, new_stamp)
    except OSError as error:
        rollback_errors: list[OSError] = []
        for target, backup in backups.items():
            try:
                _write_target(target, backup.read_bytes())
            except OSError as restore_error:
                rollback_errors.append(restore_error)
        for path in reversed(created_files):
            try:
                if path.exists() or path.is_symlink():
                    path.unlink()
            except OSError as remove_error:
                rollback_errors.append(remove_error)
        for directory in created_dirs:
            try:
                directory.rmdir()
            except OSError:
                # Existing/non-empty parents are deliberately retained.
                pass
        message = f"upgrade failed and was rolled back: {error}"
        if rollback_errors:
            message += f" (rollback encountered {len(rollback_errors)} error(s))"
        raise UpgradeError(message) from error
    finally:
        shutil.rmtree(backup_root, ignore_errors=True)
    return report
