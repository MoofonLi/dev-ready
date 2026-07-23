"""Offline, read-only structural drift inspection module.

Compares target project directory state and `.dev-ready.json` stamp against the
running CLI manifest and expected filesystem layout.

Must not import `dev_ready.fetch`, perform network I/O, or modify target project.
See docs/architecture.md.
"""

import json
from pathlib import Path
from typing import Any

from dev_ready import __version__
from dev_ready.errors import DriftError
from dev_ready.manifest import CatalogItem, load_default_manifest
from dev_ready.stamp import load_stamp
from dev_ready.verify import FORBIDDEN_PATHS, REQUIRED_OVERLAY_PATHS, REQUIRED_UPSTREAM_PATHS, _check_inject_present

__all__ = ["check_project"]



def _is_path_safe(base_dir: Path, target_path: Path) -> bool:
    """Ensure `target_path` is strictly contained within `base_dir`."""
    try:
        base_resolved = base_dir.resolve()
        target_resolved = target_path.resolve()
        return base_resolved == target_resolved or base_resolved in target_resolved.parents
    except OSError:
        return False


def check_project(project_dir: Path, json_output: bool = False) -> str:
    """Inspect `project_dir` for structural or pin drift.

    Returns formatted report string if clean.
    Raises `DriftError` containing detailed drift report if any drift is found.
    Never mutates target project directory under any code path.
    """
    resolved_dir = project_dir.resolve()
    stamp = load_stamp(project_dir)
    manifest = load_default_manifest()

    drifts: list[str] = []
    vendored_map = {v.repo: v.commit for v in manifest.vendored}

    # 1. Upstream pin check
    current_upstream = manifest.upstream.get("base_template")
    if current_upstream is None:
        drifts.append("[manifest error] base_template missing from current manifest")
    else:
        if (
            stamp.upstream.repo != current_upstream.repo
            or stamp.upstream.commit != current_upstream.commit
        ):
            drifts.append(
                f"[upstream pin drift] recorded {stamp.upstream.repo}@{stamp.upstream.commit[:7]} "
                f"differs from current {current_upstream.repo}@{current_upstream.commit[:7]}"
            )

    # 2. Required upstream & overlay paths
    for rel_path in REQUIRED_UPSTREAM_PATHS:
        target = resolved_dir / rel_path
        if not _is_path_safe(resolved_dir, target):
            drifts.append(f"[security error] unsafe path traversal detected for path '{rel_path}'")
            continue
        if not target.exists():
            drifts.append(f"[missing upstream path] required path '{rel_path}' is missing")

    for rel_path in REQUIRED_OVERLAY_PATHS:
        target = resolved_dir / rel_path
        if not _is_path_safe(resolved_dir, target):
            drifts.append(f"[security error] unsafe path traversal detected for path '{rel_path}'")
            continue
        if not target.exists():
            drifts.append(f"[missing overlay path] required path '{rel_path}' is missing")

    # Always required overlay files
    for req_file in ("CLAUDE.md", "README.md"):
        target = resolved_dir / req_file
        if not target.exists():
            drifts.append(f"[missing overlay file] required file '{req_file}' is missing")

    # Optional component root paths
    if stamp.docs_included:
        if not (resolved_dir / "docs").exists():
            drifts.append("[missing overlay directory] recorded 'docs' component but 'docs/' directory is missing")

    if stamp.agents_included:
        if not (resolved_dir / "docs" / "handoffs").exists():
            drifts.append(
                "[missing overlay directory] recorded 'agents' component but 'docs/handoffs/' directory is missing"
            )

    # 3. Forbidden paths
    for rel_path in FORBIDDEN_PATHS:
        target = resolved_dir / rel_path
        if target.exists():
            drifts.append(f"[forbidden path present] target directory contains forbidden path '{rel_path}'")

    # 4. Item selection and pin checks
    def _verify_component_items(
        comp_name: str, stamp_items: tuple[Any, ...], catalog_items: tuple[CatalogItem, ...]
    ) -> None:
        catalog_map = {item.id: item for item in catalog_items}
        for s_item in stamp_items:
            item_id = s_item.id
            recorded_pin = s_item.pin

            if item_id not in catalog_map:
                drifts.append(
                    f"[removed catalog item] recorded {comp_name} item '{item_id}' is no longer present in CLI catalog"
                )
                continue

            cat_item = catalog_map[item_id]

            # Pin check for stamp version 2
            if stamp.stamp_version >= 2 and recorded_pin is not None:
                expected_pin = cat_item.pin
                if (
                    cat_item.mode == "vendor"
                    and cat_item.vendored_repo
                    and cat_item.vendored_repo in vendored_map
                ):
                    expected_pin = vendored_map[cat_item.vendored_repo]

                if recorded_pin != expected_pin:
                    drifts.append(
                        f"[{comp_name} pin drift] item '{item_id}' pin recorded '{recorded_pin}' "
                        f"differs from current '{expected_pin}'"
                    )

            # Paths check for item
            for item_path in cat_item.paths:
                dest_path = resolved_dir / item_path.dest
                if not _is_path_safe(resolved_dir, dest_path):
                    drifts.append(
                        f"[security error] item '{item_id}' destination '{item_path.dest}' escapes target directory"
                    )
                    continue
                if not dest_path.exists():
                    drifts.append(
                        f"[missing item path] selected {comp_name} item '{item_id}' path '{item_path.dest}' is missing"
                    )

            # Inject effect check
            if cat_item.inject is not None:
                if not _check_inject_present(resolved_dir, cat_item):
                    drifts.append(
                        f"[missing inject effect] selected {comp_name} item '{item_id}' missing inject effect in '{cat_item.inject.target}'"
                    )

    _verify_component_items("skills", stamp.skills_items, manifest.components.get("skills", ()))
    _verify_component_items("mcp", stamp.mcp_items, manifest.components.get("mcp", ()))

    report_data = {
        "project_dir": str(resolved_dir),
        "stamp_version": stamp.stamp_version,
        "dev_ready_version_recorded": stamp.dev_ready_version,
        "dev_ready_version_current": __version__,
        "upstream_pin_recorded": {"repo": stamp.upstream.repo, "commit": stamp.upstream.commit},
        "upstream_pin_current": (
            {"repo": current_upstream.repo, "commit": current_upstream.commit}
            if current_upstream
            else None
        ),
        "clean": len(drifts) == 0,
        "drift_count": len(drifts),
        "drifts": drifts,
    }

    if json_output:
        formatted_report = json.dumps(report_data, indent=2) + "\n"
    else:
        lines = [
            f"dev-ready check report for {resolved_dir}",
            f"Generated with: dev-ready {stamp.dev_ready_version} (stamp version {stamp.stamp_version})",
            f"Current CLI: dev-ready {__version__}",
            f"Upstream pin: {stamp.upstream.repo}@{stamp.upstream.commit[:7]}",
            "",
        ]
        if drifts:
            lines.append(f"Drift detected ({len(drifts)} items):")
            for drift in drifts:
                lines.append(f"  - {drift}")
        else:
            lines.append("Status: CLEAN (0 drift detected)")
        formatted_report = "\n".join(lines) + "\n"

    if drifts:
        raise DriftError(formatted_report.rstrip())

    return formatted_report
