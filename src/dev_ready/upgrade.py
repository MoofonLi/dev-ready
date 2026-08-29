"""Offline, all-or-nothing re-application of overlay-managed project files."""

import hashlib
import os
import shutil
import sys
import tempfile
from pathlib import Path

from dev_ready import __version__
from dev_ready.agent_targets import CANONICAL_SKILLS_ROOT, project_targets
from dev_ready.catalog_effects import classify_shared_targets
from dev_ready.errors import StampInvalidError, UpgradeError, UpgradeNotSupportedError
from dev_ready.manifest import ComponentCatalog, load_default_manifest
from dev_ready.overlay import (
    build_overlay_content,
    content_inventory,
    generated_anchor_names,
    projected_skill_link_pairs,
    render_ignore_anchor,
    render_stamp,
)
from dev_ready.skill_links import (
    PathKind,
    classify_path,
    create_skill_link,
    has_link_component,
    remove_link_object,
)
from dev_ready.overlay.rendering import mounted_enhancements
from dev_ready.intent import Answers
from dev_ready.recorded import RecordedProject
from dev_ready.stamp import load_stamp


def _write_target(path: Path, data: bytes) -> None:
    """Write one planned target; kept tiny so commit failures are testable."""
    path.write_bytes(data)


def _relocate_path(source: Path, destination: Path) -> None:
    """Move a filesystem object without following it."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    os.replace(source, destination)


def _path_object_exists(path: Path) -> bool:
    return path.is_symlink() or path.is_junction() or path.exists()


def _remove_path_object(path: Path) -> None:
    """Remove a file, directory, symlink, or junction without following it."""
    if path.is_symlink() or path.is_junction():
        path.unlink()
        return
    if path.is_dir():
        shutil.rmtree(path)
        return
    path.unlink()


def _restore_path(backup: Path, target: Path) -> None:
    if _path_object_exists(target):
        _remove_path_object(target)
    _relocate_path(backup, target)


def _is_within(root: Path, path: Path) -> bool:
    try:
        path.resolve().relative_to(root)
    except ValueError:
        return False
    return True


def _has_symlink_component(root: Path, path: Path) -> bool:
    """Return whether ``path`` traverses a symlink or junction beneath ``root``."""
    return has_link_component(root, path)


def _under_skills_dir(path: str, skills_dir: str) -> bool:
    return path == skills_dir or path.startswith(f"{skills_dir}/")


def _parent_is_safe_directory(resolved: Path, target: Path) -> bool:
    parent = target.parent
    if not _is_within(resolved, parent) or _has_symlink_component(resolved, parent):
        return False
    if not _path_object_exists(parent):
        return True
    return classify_path(parent) == PathKind.DIRECTORY


def _cancel_target_mutations(
    skills_dir: str,
    resolved: Path,
    creates: list[tuple[Path, Path]],
    repairs: list[tuple[Path, Path]],
    deletions: list[Path],
    groups: dict[str, list[str]],
    stale_removals: list[Path] | None = None,
) -> None:
    creates[:] = [
        (path, canonical)
        for path, canonical in creates
        if not _under_skills_dir(path.relative_to(resolved).as_posix(), skills_dir)
    ]
    repairs[:] = [
        (path, canonical)
        for path, canonical in repairs
        if not _under_skills_dir(path.relative_to(resolved).as_posix(), skills_dir)
    ]
    deletions[:] = [
        path
        for path in deletions
        if not _under_skills_dir(path.relative_to(resolved).as_posix(), skills_dir)
    ]
    for key in ("links_created", "links_repaired", "stale_removed", "deleted"):
        groups[key][:] = [
            path for path in groups[key] if not _under_skills_dir(path, skills_dir)
        ]
    if stale_removals is not None:
        stale_removals[:] = [
            path
            for path in stale_removals
            if not _under_skills_dir(path.relative_to(resolved).as_posix(), skills_dir)
        ]


def _directory_has_remaining_entries(
    directory: Path, relative: Path, deleted_paths: set[str]
) -> bool:
    if not directory.is_dir() or directory.is_symlink() or directory.is_junction():
        return True
    for child in directory.iterdir():
        child_rel = (relative / child.name).as_posix()
        if child_rel in deleted_paths:
            continue
        if child.is_dir() and not child.is_symlink() and not child.is_junction():
            if _directory_has_remaining_entries(child, relative / child.name, deleted_paths):
                return True
            continue
        return True
    return False


def _agent_local_skill_root(path: str, skills_dirs: tuple[str, ...]) -> str | None:
    for skills_dir in skills_dirs:
        prefix = f"{skills_dir}/"
        if not path.startswith(prefix):
            continue
        name = path[len(prefix) :].split("/", 1)[0]
        if not name or name == ".gitignore":
            continue
        return f"{skills_dir}/{name}"
    return None


def _skill_directory_entries(root: Path, directory: Path) -> list[str]:
    entries: list[str] = []
    stack = [directory]
    while stack:
        current = stack.pop()
        if not current.is_dir() or current.is_symlink() or current.is_junction():
            continue
        for child in current.iterdir():
            relative = child.relative_to(root).as_posix()
            if child.is_symlink() or child.is_junction() or child.is_file():
                entries.append(relative)
            elif child.is_dir():
                stack.append(child)
    return entries


def _prune_empty_directories(path: Path) -> list[Path]:
    pruned: list[Path] = []
    if not path.is_dir() or path.is_symlink() or path.is_junction():
        return pruned
    for child in list(path.iterdir()):
        pruned.extend(_prune_empty_directories(child))
    try:
        path.rmdir()
    except OSError:
        return pruned
    pruned.append(path)
    return pruned


def _plan_stale_link_retirement(
    resolved: Path,
    recorded: dict[str, str],
    blocked_dirs: set[str],
    post_names: dict[str, list[str]],
    groups: dict[str, list[str]],
) -> list[Path]:
    """Remove trusted stale Skill Links named by unmodified nested anchors."""
    removals: list[Path] = []
    seen_anchors: set[str] = set()
    for path, digest in recorded.items():
        if not path.endswith("/.gitignore") or path == ".gitignore":
            continue
        skills_dir = str(Path(path).parent.as_posix())
        if skills_dir in blocked_dirs or path in seen_anchors:
            continue
        seen_anchors.add(path)
        anchor_path = resolved / path
        if classify_path(anchor_path) != PathKind.FILE:
            continue
        current = anchor_path.read_bytes()
        if hashlib.sha256(current).hexdigest() != digest:
            names = generated_anchor_names(current)
            desired = set(post_names.get(skills_dir, ()))
            if names and any(name not in desired for name in names):
                groups["conflict"].append(skills_dir)
            continue
        names = generated_anchor_names(current)
        if names is None:
            continue
        desired = set(post_names.get(skills_dir, ()))
        for name in names:
            if name in desired:
                continue
            occupant = resolved / skills_dir / name
            kind = classify_path(occupant)
            rel = f"{skills_dir}/{name}"
            if kind in {PathKind.SYMBOLIC_LINK, PathKind.JUNCTION}:
                groups["stale_removed"].append(rel)
                removals.append(occupant)
                continue
            if kind != PathKind.ABSENT:
                groups["conflict"].append(rel)
    return removals


def _plan_v3_skill_cohorts(
    resolved: Path,
    recorded: dict[str, str],
    new_content: dict[str, bytes],
    catalog: ComponentCatalog,
    blocked_dirs: set[str],
    ready_canonical_paths: set[str],
    groups: dict[str, list[str]],
    deletions: list[Path],
) -> tuple[set[str], list[Path]]:
    """Retire or preserve v3 full-copy skill directories as one cohort."""
    skills_dirs = tuple(
        target.skills_dir
        for target in project_targets(catalog, catalog.agent_target_ids).skill_targets
    )
    buckets: dict[str, list[str]] = {}
    for path in recorded:
        if path in new_content:
            continue
        root = _agent_local_skill_root(path, skills_dirs)
        if root is None:
            continue
        buckets.setdefault(root, []).append(path)

    handled: set[str] = set()
    convert_dirs: list[Path] = []
    for skill_root, paths in buckets.items():
        handled.update(paths)
        skills_dir = str(Path(skill_root).parent.as_posix())
        skill_name = Path(skill_root).name
        if skills_dir in blocked_dirs:
            continue
        directory = resolved / skill_root
        kind = classify_path(directory)
        if kind in {PathKind.SYMBOLIC_LINK, PathKind.JUNCTION}:
            continue
        if not _canonical_is_ready(
            resolved, Path(*CANONICAL_SKILLS_ROOT) / skill_name, ready_canonical_paths
        ):
            continue
        recorded_set = set(paths)
        modified: list[str] = []
        existing_recorded: list[str] = []
        for path in paths:
            target = resolved / path
            if classify_path(target) == PathKind.ABSENT:
                continue
            if classify_path(target) != PathKind.FILE:
                modified.append(path)
                continue
            if hashlib.sha256(target.read_bytes()).hexdigest() != recorded[path]:
                modified.append(path)
            else:
                existing_recorded.append(path)
        extras = [
            entry
            for entry in (
                _skill_directory_entries(resolved, directory)
                if kind == PathKind.DIRECTORY
                else []
            )
            if entry not in recorded_set
        ]
        if modified or extras:
            for path in modified:
                groups["preserved_obsolete_modified"].append(
                    f"{path}: preserved; review it and remove it manually "
                    "if it is no longer needed"
                )
                groups["divergence"].append(
                    f"{path}: retained outside the current managed inventory"
                )
            groups["conflict"].extend(extras)
            continue
        for path in existing_recorded:
            groups["deleted"].append(path)
            deletions.append(resolved / path)
        convert_dirs.append(directory)
    return handled, convert_dirs


def _canonical_is_ready(
    resolved: Path,
    canonical_rel: Path,
    ready_canonical_paths: set[str],
) -> bool:
    canonical = resolved / canonical_rel
    skill_md = canonical / "SKILL.md"
    skill_md_rel = f"{canonical_rel.as_posix()}/SKILL.md"
    prefix = f"{canonical_rel.as_posix()}/"
    if not _is_within(resolved, canonical) or not _is_within(resolved, skill_md):
        return False
    if _has_symlink_component(resolved, canonical) or _has_symlink_component(
        resolved, skill_md
    ):
        return False
    if (
        classify_path(canonical) == PathKind.DIRECTORY
        and classify_path(skill_md) == PathKind.FILE
    ):
        return True
    return skill_md_rel in ready_canonical_paths or any(
        path.startswith(prefix) for path in ready_canonical_paths
    )


def _link_is_correct(link_path: Path, canonical: Path) -> bool:
    kind = classify_path(link_path)
    if sys.platform == "win32":
        if kind != PathKind.JUNCTION:
            return False
        stored = os.readlink(link_path).removeprefix("\\\\?\\")
        try:
            return Path(stored).resolve() == canonical.resolve()
        except OSError:
            return False
    if kind != PathKind.SYMBOLIC_LINK:
        return False
    return os.readlink(link_path) == os.path.relpath(canonical, start=link_path.parent)


def _plan_skill_link_actions(
    resolved: Path,
    answers: Answers,
    catalog: ComponentCatalog,
    groups: dict[str, list[str]],
    deleted_paths: set[str],
    ready_canonical_paths: set[str],
    blocked_dirs: set[str],
) -> tuple[list[tuple[Path, Path]], list[tuple[Path, Path]], dict[str, list[str]]]:
    creates: list[tuple[Path, Path]] = []
    repairs: list[tuple[Path, Path]] = []
    post_names: dict[str, list[str]] = {}
    for link_rel, canonical_rel in projected_skill_link_pairs(answers, catalog):
        link_path = resolved / link_rel
        canonical = resolved / canonical_rel
        skills_dir = link_rel.parent.as_posix()
        if skills_dir in blocked_dirs:
            continue
        if _has_symlink_component(resolved, link_path.parent):
            groups["conflict"].append(link_rel.as_posix())
            continue
        if not _canonical_is_ready(resolved, canonical_rel, ready_canonical_paths):
            continue
        kind = classify_path(link_path)
        if _link_is_correct(link_path, canonical):
            post_names.setdefault(skills_dir, []).append(link_rel.name)
            continue
        path_text = link_rel.as_posix()
        if kind in {PathKind.SYMBOLIC_LINK, PathKind.JUNCTION}:
            groups["links_repaired"].append(path_text)
            repairs.append((link_path, canonical))
            post_names.setdefault(skills_dir, []).append(link_rel.name)
            continue
        remaining = False
        if kind == PathKind.DIRECTORY:
            remaining = _directory_has_remaining_entries(
                link_path, link_rel, deleted_paths
            )
        if kind == PathKind.ABSENT or (kind == PathKind.DIRECTORY and not remaining):
            groups["links_created"].append(path_text)
            creates.append((link_path, canonical))
            post_names.setdefault(skills_dir, []).append(link_rel.name)
            continue
        groups["conflict"].append(path_text)
    return creates, repairs, post_names


def _probe_link_support(project: Path) -> None:
    probe_link = project / ".dev-ready-link-probe"
    try:
        create_skill_link(probe_link, project)
    except OSError as error:
        raise UpgradeError(
            f"failed to create Skill Link at {probe_link}: {error}. "
            "Choose a different destination location on a filesystem that "
            "supports directory links."
        ) from error
    finally:
        try:
            remove_link_object(probe_link)
        except OSError:
            pass


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
        ("Restored", "restored"),
        ("Skipped (user-modified)", "skipped_modified"),
        ("Skipped (shared, not auto-upgraded)", "skipped_shared"),
        ("Skipped (missing)", "skipped_missing"),
        ("Deleted (obsolete)", "deleted"),
        ("Skill Links created", "links_created"),
        ("Skill Links repaired", "links_repaired"),
        ("Stale Skill Links removed", "stale_removed"),
        ("Preserved (obsolete, user-modified)", "preserved_obsolete_modified"),
        ("Divergence", "divergence"),
        ("Conflict", "conflict"),
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
            if key == "deleted" and dry_run:
                action = f"would delete {path}"
            elif key == "restored" and dry_run:
                action = f"would restore {path}"
            elif key == "restored":
                action = f"restored {path}"
            elif key == "links_created" and dry_run:
                action = f"would create {path}"
            elif key == "links_repaired" and dry_run:
                action = f"would repair {path}"
            elif key == "stale_removed" and dry_run:
                action = f"would remove {path}"
            elif key == "stale_removed":
                action = f"removed {path}"
            elif key in {"upgraded", "added"}:
                action = f"{prefix}{path}"
            else:
                action = path
            lines.append(f"  - {action}")
    action_word = "would change" if dry_run else "changed"
    change_count = (
        len(groups["upgraded"])
        + len(groups["added"])
        + len(groups["restored"])
        + len(groups["deleted"])
        + len(groups["links_created"])
        + len(groups["links_repaired"])
        + len(groups["stale_removed"])
    )
    lines.append("")
    lines.append(
        f"Summary: {len(groups['upgraded'])} upgraded, {len(groups['added'])} added, "
        f"{len(groups['deleted'])} deleted; {action_word} "
        f"{change_count} "
        "overlay-managed files."
    )
    unresolved_keys = (
        "skipped_modified",
        "skipped_missing",
        "preserved_obsolete_modified",
        "divergence",
        "conflict",
    )
    if change_count == 0 and not any(groups[key] for key in unresolved_keys):
        lines.append("No changes were needed.")
    return "\n".join(lines) + "\n"


def upgrade_project(project_dir: Path, dry_run: bool = False) -> str:
    """Safely update only clean, whole-file overlay content in ``project_dir``.

    Current overlay paths come from the manifest. Recorded paths are accessed
    only for obsolete-file retirement after containment and symlink checks.
    """
    resolved = project_dir.resolve()
    stamp = load_stamp(project_dir)
    if stamp.stamp_version < 3 or not stamp.inventory or stamp.project_name is None:
        raise UpgradeNotSupportedError(
            "projects generated with dev-ready v0.3–v0.5 can be inspected with "
            "dev-ready check but not upgraded; regenerate the project to enable upgrades."
        )

    manifest = load_default_manifest()
    recorded_project = RecordedProject.migrated(stamp, manifest)
    if (
        stamp.stamp_version >= 5
        and recorded_project.recorded_development_loop
        not in manifest.components.development_loop_ids
    ):
        raise StampInvalidError(
            ".dev-ready.json records unknown development_loop "
            f"{recorded_project.recorded_development_loop!r}"
        )
    if (
        stamp.stamp_version >= 5
        and recorded_project.recorded_development_loop
        != recorded_project.selection.development_loop
    ):
        raise StampInvalidError(
            ".dev-ready.json development_loop must also appear in "
            "components.skills.items"
        )
    manifest_pin = manifest.upstream["base_template"]
    pin = type(manifest_pin)(
        repo=stamp.upstream.repo,
        ref=manifest_pin.ref,
        commit=stamp.upstream.commit,
        license=manifest_pin.license,
        verified_at=manifest_pin.verified_at,
        exclude=manifest_pin.exclude,
        prune=manifest_pin.prune,
    )
    if recorded_project.removed_agent_targets:
        raise UpgradeError(
            "cannot upgrade a project that records a removed Agent Target: "
            + ", ".join(
                repr(target_id) for target_id in recorded_project.removed_agent_targets
            )
        )
    answers = Answers(
        project_name=stamp.project_name,
        target_dir=resolved,
        selection=recorded_project.selection,
    )
    new_content = build_overlay_content(answers, manifest.components)
    mounted_skill_paths = mounted_enhancements(answers, manifest.components).keys()
    # An MCP effect's manifest-declared target is never where it actually lands:
    # the projection retargets it onto each Agent Target's own MCP file.
    declared_targets = project_targets(
        manifest.components, manifest.components.agent_target_ids
    )
    selected_targets = project_targets(manifest.components, answers.agent_targets)
    shared_targets = classify_shared_targets(manifest.components, answers.selection)
    shared_all = set(shared_targets.all)
    shared_selected = set(shared_targets.selected)
    for item in manifest.components.get("mcp", ()):
        if item.effect is None:
            continue
        shared_all.discard(item.effect.target)
        shared_selected.discard(item.effect.target)
        shared_all.update(declared_targets.mcp_files)
        if item.id in answers.mcp_items:
            shared_selected.update(selected_targets.mcp_files)
    recorded = {entry.path: entry.sha256 for entry in stamp.inventory}
    groups: dict[str, list[str]] = {
        "upgraded": [],
        "added": [],
        "restored": [],
        "skipped_modified": [],
        "skipped_shared": [],
        "skipped_missing": [],
        "deleted": [],
        "links_created": [],
        "links_repaired": [],
        "stale_removed": [],
        "preserved_obsolete_modified": [],
        "divergence": [],
        "conflict": [],
    }
    upgrades: list[tuple[Path, bytes]] = []
    adds: list[tuple[Path, bytes]] = []
    deletions: list[Path] = []
    anchor_paths = {
        selected_targets.ignore_anchor_path(target).as_posix()
        for target in selected_targets.skill_targets
    }
    skills_by_anchor = {
        selected_targets.ignore_anchor_path(target).as_posix(): target.skills_dir
        for target in selected_targets.skill_targets
    }

    for path in sorted(new_content):
        if path in anchor_paths:
            continue
        target = resolved / path
        if not _is_within(resolved, target):
            raise UpgradeError(f"manifest overlay path escapes project directory: {path}")
        if _has_symlink_component(resolved, target):
            groups["conflict"].append(path)
            continue
        if path in shared_all:
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
                if path in mounted_skill_paths:
                    groups["divergence"].append(
                        f"{path}: preserved; mounted guidance was not updated because "
                        "the file is user-modified"
                    )
                elif stamp.stamp_version < 4 and path.startswith(".claude/skills/"):
                    canonical_path = path.removeprefix(".claude/")
                    groups["divergence"].append(
                        f"{path}: preserved; canonical content was added at "
                        f".agents/{canonical_path}; reconcile the two files manually"
                    )
                elif stamp.stamp_version < 4 and path == "CLAUDE.md":
                    groups["divergence"].append(
                        "CLAUDE.md: preserved; reference AGENTS.md manually to adopt "
                        "the canonical project rules"
                    )
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

    blocked_dirs: set[str] = set()
    pending_anchors: dict[str, str] = {}
    for target in selected_targets.skill_targets:
        skills_dir = target.skills_dir
        skills_path = resolved / skills_dir
        anchor_rel = selected_targets.ignore_anchor_path(target).as_posix()
        anchor_path = resolved / anchor_rel
        if _has_symlink_component(resolved, skills_path):
            if skills_dir not in groups["conflict"]:
                groups["conflict"].append(skills_dir)
            blocked_dirs.add(skills_dir)
            continue
        if not _parent_is_safe_directory(resolved, anchor_path):
            groups["conflict"].append(skills_dir)
            blocked_dirs.add(skills_dir)
            continue
        if anchor_rel in recorded:
            kind = classify_path(anchor_path)
            if kind == PathKind.ABSENT:
                pending_anchors[anchor_rel] = "restore"
                continue
            if kind != PathKind.FILE:
                groups["conflict"].append(skills_dir)
                blocked_dirs.add(skills_dir)
                continue
            current = anchor_path.read_bytes()
            if hashlib.sha256(current).hexdigest() != recorded[anchor_rel]:
                groups["skipped_modified"].append(anchor_rel)
                groups["conflict"].append(skills_dir)
                blocked_dirs.add(skills_dir)
                continue
            pending_anchors[anchor_rel] = "managed"
            continue
        kind = classify_path(anchor_path)
        if kind == PathKind.ABSENT:
            pending_anchors[anchor_rel] = "add"
        elif kind == PathKind.FILE:
            pending_anchors[anchor_rel] = "adopt"
        else:
            groups["conflict"].append(skills_dir)
            blocked_dirs.add(skills_dir)

    declared_skills_dirs = tuple(
        target.skills_dir
        for target in project_targets(
            manifest.components, manifest.components.agent_target_ids
        ).skill_targets
    )
    handled_legacy: set[str] = set()
    legacy_convert_dirs: list[Path] = []
    if stamp.stamp_version < 4:
        handled_legacy, legacy_convert_dirs = _plan_v3_skill_cohorts(
            resolved,
            recorded,
            new_content,
            manifest.components,
            blocked_dirs,
            {target.relative_to(resolved).as_posix() for target, _ in adds}
            | {target.relative_to(resolved).as_posix() for target, _ in upgrades},
            groups,
            deletions,
        )

    for path in sorted(recorded.keys() - new_content.keys()):
        target = resolved / path
        if not _is_within(resolved, target):
            raise UpgradeError(f"recorded obsolete path escapes project directory: {path}")
        if path in handled_legacy:
            continue
        if any(_under_skills_dir(path, skills_dir) for skills_dir in blocked_dirs):
            continue
        skill_root = _agent_local_skill_root(path, declared_skills_dirs)
        if skill_root is not None and classify_path(resolved / skill_root) in {
            PathKind.SYMBOLIC_LINK,
            PathKind.JUNCTION,
        }:
            continue
        if _has_symlink_component(resolved, target):
            groups["conflict"].append(path)
            continue
        if not target.exists():
            continue
        if not target.is_file():
            groups["conflict"].append(path)
            continue
        current_hash = hashlib.sha256(target.read_bytes()).hexdigest()
        if current_hash != recorded[path]:
            groups["preserved_obsolete_modified"].append(
                f"{path}: preserved; review it and remove it manually "
                "if it is no longer needed"
            )
            groups["divergence"].append(
                f"{path}: retained outside the current managed inventory"
            )
            continue
        groups["deleted"].append(path)
        deletions.append(target)

    # Some injection targets (for example frontend/package.json) are not
    # whole-file overlay content. They still merit an explicit report when the
    # selected item owns an injection there, because upgrade intentionally
    # never touches them.
    already_reported_shared = set(groups["skipped_shared"])
    groups["skipped_shared"].extend(
        sorted(shared_selected - already_reported_shared - set(new_content))
    )

    creates, repairs, post_names = _plan_skill_link_actions(
        resolved,
        answers,
        manifest.components,
        groups,
        {target.relative_to(resolved).as_posix() for target in deletions},
        {target.relative_to(resolved).as_posix() for target, _ in adds}
        | {target.relative_to(resolved).as_posix() for target, _ in upgrades},
        blocked_dirs,
    )
    stale_removals = _plan_stale_link_retirement(
        resolved,
        recorded,
        blocked_dirs,
        post_names,
        groups,
    )

    for anchor_rel, action in pending_anchors.items():
        skills_dir = skills_by_anchor[anchor_rel]
        names = tuple(sorted(post_names.get(skills_dir, ())))
        state_aware = render_ignore_anchor(names)
        new_content[anchor_rel] = state_aware
        anchor_path = resolved / anchor_rel
        if action == "adopt":
            if anchor_path.read_bytes() == state_aware:
                continue
            groups["conflict"].append(skills_dir)
            blocked_dirs.add(skills_dir)
            _cancel_target_mutations(
                skills_dir,
                resolved,
                creates,
                repairs,
                deletions,
                groups,
                stale_removals,
            )
            continue
        if action == "restore":
            groups["restored"].append(anchor_rel)
            adds.append((anchor_path, state_aware))
            continue
        if action == "add":
            groups["added"].append(anchor_rel)
            adds.append((anchor_path, state_aware))
            continue
        current = anchor_path.read_bytes()
        if current == state_aware:
            continue
        groups["upgraded"].append(anchor_rel)
        upgrades.append((anchor_path, state_aware))

    new_stamp = render_stamp(
        answers,
        pin,
        manifest.components,
        manifest.vendored,
        content_inventory(new_content),
        stamp_version=5,
    ).encode("utf-8")
    stamp_path = resolved / ".dev-ready.json"
    if not _is_within(resolved, stamp_path) or _has_symlink_component(resolved, stamp_path):
        raise UpgradeError("stamp path is unsafe for upgrade")
    try:
        stamp_changed = new_stamp != stamp_path.read_bytes()
    except OSError as error:
        raise UpgradeError(f"failed to read .dev-ready.json during upgrade: {error}") from error
    if stamp_changed:
        groups["upgraded"].append(".dev-ready.json")

    report = _format_report(resolved, stamp.dev_ready_version, stamp.stamp_version, groups, dry_run)
    has_writes = (
        bool(upgrades or adds or deletions or creates or repairs or stale_removals)
        or stamp_changed
    )
    if dry_run or not has_writes:
        return report
    if creates or repairs:
        _probe_link_support(resolved)

    try:
        backup_root = Path(
            tempfile.mkdtemp(prefix=".dev-ready-upgrade-", dir=resolved.parent)
        )
    except OSError as error:
        raise UpgradeError(
            f"failed to create a same-filesystem backup directory beside {resolved}: {error}"
        ) from error
    overwritten = [target for target, _ in upgrades] + deletions + [stamp_path]
    backups: dict[Path, Path] = {}
    created_files: list[Path] = []
    created_dirs: list[Path] = []
    created_links: list[Path] = []
    pruned_empty_dirs: list[Path] = []
    keep_backups = False
    try:
        for index, target in enumerate(overwritten):
            backup = backup_root / str(index)
            _relocate_path(target, backup)
            backups[target] = backup
        for directory in legacy_convert_dirs:
            pruned_empty_dirs.extend(_prune_empty_directories(directory))

        def _is_canonical_write(target: Path) -> bool:
            return target.relative_to(resolved).as_posix().startswith(".agents/skills/")

        def _is_anchor_write(target: Path) -> bool:
            return target.relative_to(resolved).as_posix() in anchor_paths

        def _write_new_file(target: Path, data: bytes) -> None:
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

        canonical_upgrades = [
            item for item in upgrades if _is_canonical_write(item[0])
        ]
        other_upgrades = [
            item
            for item in upgrades
            if not _is_canonical_write(item[0]) and not _is_anchor_write(item[0])
        ]
        anchor_upgrades = [item for item in upgrades if _is_anchor_write(item[0])]
        canonical_adds = [item for item in adds if _is_canonical_write(item[0])]
        other_adds = [
            item
            for item in adds
            if not _is_canonical_write(item[0]) and not _is_anchor_write(item[0])
        ]
        anchor_adds = [item for item in adds if _is_anchor_write(item[0])]

        for target, data in canonical_upgrades + other_upgrades:
            _write_target(target, data)
        for target, data in canonical_adds + other_adds:
            _write_new_file(target, data)
        for target, data in anchor_upgrades:
            _write_target(target, data)
        for target, data in anchor_adds:
            _write_new_file(target, data)
        for link_path in stale_removals:
            backup = backup_root / f"stale-{len(backups)}"
            _relocate_path(link_path, backup)
            backups[link_path] = backup
        for link_path, canonical in repairs:
            backup = backup_root / f"repair-{len(backups)}"
            _relocate_path(link_path, backup)
            backups[link_path] = backup
            create_skill_link(link_path, canonical)
            created_links.append(link_path)
        for link_path, canonical in creates:
            if classify_path(link_path) == PathKind.DIRECTORY:
                link_path.rmdir()
            create_skill_link(link_path, canonical)
            created_links.append(link_path)
        _write_target(stamp_path, new_stamp)
    except OSError as error:
        rollback_errors: list[OSError] = []
        for link_path in reversed(created_links):
            try:
                remove_link_object(link_path)
            except OSError as restore_error:
                rollback_errors.append(restore_error)
        for target, backup in backups.items():
            try:
                _restore_path(backup, target)
            except OSError as restore_error:
                rollback_errors.append(restore_error)
        for directory in pruned_empty_dirs:
            try:
                directory.mkdir(parents=True, exist_ok=True)
            except OSError as restore_error:
                rollback_errors.append(restore_error)
        for path in reversed(created_files):
            try:
                if _path_object_exists(path):
                    _remove_path_object(path)
            except OSError as remove_error:
                rollback_errors.append(remove_error)
        for directory in sorted(created_dirs, key=lambda path: len(path.parts), reverse=True):
            try:
                directory.rmdir()
            except OSError:
                # Existing/non-empty parents are deliberately retained.
                pass
        if rollback_errors:
            keep_backups = True
            first = rollback_errors[0]
            message = (
                f"upgrade failed: {error}; rollback encountered "
                f"{len(rollback_errors)} error(s) ({first}). "
                f"Parked originals remain in {backup_root}; "
                "manual recovery may be required"
            )
        else:
            message = (
                "upgrade failed and was rolled back; the original project was restored: "
                f"{error}. Retry the upgrade; if it fails again, report this error."
            )
        raise UpgradeError(message) from error
    finally:
        if not keep_backups:
            shutil.rmtree(backup_root, ignore_errors=True)
    return report
