"""Render project records for fresh generation and legacy lifecycle rewrites."""

import json
from collections.abc import Collection

from dev_ready import __version__
from dev_ready.manifest import ComponentCatalog, UpstreamPin, VendoredPin
from dev_ready.prompts import Answers


def render_stamp(
    answers: Answers,
    pin: UpstreamPin,
    catalog: ComponentCatalog,
    vendored: Collection[VendoredPin] = (),
    inventory: Collection[tuple[str, str]] = (),
    *,
    stamp_version: int = 5,
) -> str:
    """Render a current or legacy-readable project stamp without writing it."""
    if stamp_version not in {4, 5}:
        raise ValueError(f"cannot render unsupported stamp version {stamp_version}")
    vendored_map = {vendor.repo: vendor.commit for vendor in vendored}

    def stamp_items(
        component: str,
        selected: Collection[str],
    ) -> list[dict[str, str | None]]:
        stamped = []
        for item in catalog.get(component, ()):
            if item.id not in selected:
                continue
            item_pin = item.pin
            if (
                item.mode == "vendor"
                and item.vendored_repo
                and item.vendored_repo in vendored_map
            ):
                item_pin = vendored_map[item.vendored_repo]
            stamped.append({"id": item.id, "pin": item_pin})
        return sorted(stamped, key=lambda entry: str(entry["id"]))

    data = {
        "stamp_version": stamp_version,
        "dev_ready_version": __version__,
        "project_name": answers.project_name,
        "agent_targets": sorted(answers.agent_targets),
        "components": {
            "skills": {
                "included": answers.includes("skills"),
                "items": stamp_items("skills", answers.items("skills")),
            },
            "mcp": {
                "included": answers.includes("mcp"),
                "items": stamp_items("mcp", answers.items("mcp")),
            },
            "docs": {"included": answers.includes("docs")},
        },
        "upstream": {"repo": pin.repo, "commit": pin.commit},
        "inventory": [
            {"path": path, "sha256": digest} for path, digest in sorted(inventory)
        ],
    }
    if stamp_version >= 5:
        data["categories"] = sorted(answers.selection.categories)
        data["development_loop"] = answers.selection.development_loop
        data["components"]["docs"]["items"] = stamp_items(
            "docs", answers.items("docs")
        )
    return json.dumps(data, indent=2) + "\n"
