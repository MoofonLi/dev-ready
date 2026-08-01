"""Offline drift policy over stamp, manifest, and shared project inspection."""

import json
from pathlib import Path
from typing import Any

from dev_ready import __version__
from dev_ready.errors import DriftError
from dev_ready.inspection import ProjectExpectation, inspect_project
from dev_ready.manifest import CatalogItem, load_default_manifest
from dev_ready.prompts import ProjectSelection
from dev_ready.stamp import load_stamp

__all__ = ["check_project"]


def check_project(project_dir: Path, json_output: bool = False) -> str:
    """Inspect ``project_dir`` and render the lifecycle drift policy's report."""
    resolved_dir = project_dir.resolve()
    stamp = load_stamp(project_dir)
    manifest = load_default_manifest()

    drifts: list[str] = []
    advisories: list[str] = []
    if stamp.dev_ready_version != __version__:
        drifts.append(
            f"[overlay version drift] recorded dev-ready {stamp.dev_ready_version} "
            f"differs from current {__version__}"
        )
    vendored_map = {vendor.repo: vendor.commit for vendor in manifest.vendored}
    current_upstream = manifest.upstream.get("base_template")
    if current_upstream is None:
        drifts.append("[manifest error] base_template missing from current manifest")
    elif (
        stamp.upstream.repo != current_upstream.repo
        or stamp.upstream.commit != current_upstream.commit
    ):
        advisories.append(
            f"[base update advisory] project Base Provenance is "
            f"{stamp.upstream.repo}@{stamp.upstream.commit[:7]}; current generation uses "
            f"{current_upstream.repo}@{current_upstream.commit[:7]}. "
            "Overlay upgrade does not replace upstream application content."
        )

    known_skills = frozenset(item.id for item in manifest.components.get("skills", ()))
    known_mcp = frozenset(item.id for item in manifest.components.get("mcp", ()))
    known_docs = frozenset(item.id for item in manifest.components.get("docs", ()))
    removed_agent_targets = sorted(set(stamp.agent_targets) - set(manifest.agent_targets))
    drifts.extend(
        f"[removed agent target] recorded Agent Target {target_id!r} "
        "is no longer present in CLI manifest"
        for target_id in removed_agent_targets
    )
    selection = ProjectSelection.from_recorded_items(
        manifest.components,
        skills=frozenset(item.id for item in stamp.skills_items) & known_skills,
        mcp=frozenset(item.id for item in stamp.mcp_items) & known_mcp,
        docs_items=(
            frozenset(item.id for item in stamp.docs_items) & known_docs
            if stamp.stamp_version >= 5
            else (known_docs if stamp.docs_included else frozenset())
        ),
        agent_targets=frozenset(stamp.agent_targets) & frozenset(manifest.agent_targets),
        docs=stamp.docs_included,
    )
    structural_issues = inspect_project(
        resolved_dir,
        manifest.components,
        ProjectExpectation.lifecycle(selection),
    )
    drifts.extend(f"[{issue.category}] {issue.detail}" for issue in structural_issues)

    def verify_item_pins(
        name: str,
        stamp_items: tuple[Any, ...],
        catalog_items: tuple[CatalogItem, ...],
    ) -> None:
        catalog_map = {item.id: item for item in catalog_items}
        for stamped in stamp_items:
            if stamped.id not in catalog_map:
                drifts.append(
                    f"[removed catalog item] recorded {name} item {stamped.id!r} "
                    "is no longer present in CLI catalog"
                )
                continue
            item = catalog_map[stamped.id]
            if stamp.stamp_version < 2 or stamped.pin is None:
                continue
            expected_pin = item.pin
            if item.mode == "vendor" and item.vendored_repo in vendored_map:
                expected_pin = vendored_map[item.vendored_repo]
            if stamped.pin != expected_pin:
                drifts.append(
                    f"[{name} pin drift] item {stamped.id!r} pin recorded {stamped.pin!r} "
                    f"differs from current {expected_pin!r}"
                )

    verify_item_pins("skills", stamp.skills_items, manifest.components.get("skills", ()))
    verify_item_pins("mcp", stamp.mcp_items, manifest.components.get("mcp", ()))
    verify_item_pins("docs", stamp.docs_items, manifest.components.get("docs", ()))

    report_data = {
        "project_dir": str(resolved_dir),
        "stamp_version": stamp.stamp_version,
        "dev_ready_version_recorded": stamp.dev_ready_version,
        "dev_ready_version_current": __version__,
        "upstream_pin_recorded": {
            "repo": stamp.upstream.repo,
            "commit": stamp.upstream.commit,
        },
        "upstream_pin_current": (
            {"repo": current_upstream.repo, "commit": current_upstream.commit}
            if current_upstream
            else None
        ),
        "clean": not drifts,
        "drift_count": len(drifts),
        "drifts": drifts,
        "advisory_count": len(advisories),
        "advisories": advisories,
    }

    if json_output:
        report = json.dumps(report_data, indent=2) + "\n"
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
            lines.extend(f"  - {drift}" for drift in drifts)
        else:
            lines.append("Status: CLEAN (0 drift detected)")
        if advisories:
            lines.append("")
            lines.append(f"Advisories ({len(advisories)}):")
            lines.extend(f"  - {advisory}" for advisory in advisories)
        report = "\n".join(lines) + "\n"

    if drifts:
        raise DriftError(report.rstrip())
    return report
