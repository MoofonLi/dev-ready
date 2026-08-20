"""Offline tests for scripts/sync_design_references.py."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

_SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "sync_design_references.py"
_spec = importlib.util.spec_from_file_location("sync_design_references", _SCRIPT_PATH)
assert _spec is not None and _spec.loader is not None
sync_design_references = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sync_design_references)


def test_derivation_reproduces_shipped_identifiers_and_composes_catalog_fields() -> None:
    items, skill_section = sync_design_references.derive_design_references(
        ("stripe", "linear.app"),
        {
            "stripe": "# Stripe Inspired Design System Analysis",
            "linear.app": "# Linear Inspired Design System Analysis",
        },
    )

    assert items == [
        {
            "id": "design-linear",
            "title": "Linear",
            "category": "design",
            "mount": "build",
            "description": "Linear-inspired DESIGN.md reference.",
            "mode": "vendor",
            "license": "MIT",
            "vendored_repo": "VoltAgent/awesome-design-md",
            "paths": [
                {"src": "docs/design-linear.md", "dest": "docs/design-linear.md"}
            ],
        },
        {
            "id": "design-stripe",
            "title": "Stripe",
            "category": "design",
            "mount": "build",
            "description": "Stripe-inspired DESIGN.md reference.",
            "mode": "vendor",
            "license": "MIT",
            "vendored_repo": "VoltAgent/awesome-design-md",
            "paths": [
                {"src": "docs/design-stripe.md", "dest": "docs/design-stripe.md"}
            ],
        },
    ]
    assert skill_section == (
        "### design items\n\n"
        "- `frontend-design`: You want a distinctive, polished frontend rather than a generic interface.\n"
        "- `design-linear`: You want Linear's design language as a reference.\n"
        "- `design-stripe`: You want Stripe's design language as a reference.\n\n"
    )


def test_derivation_covers_dotted_slugs_and_declared_title_exceptions() -> None:
    items, _ = sync_design_references.derive_design_references(
        (
            "linear.app",
            "mistral.ai",
            "opencode.ai",
            "together.ai",
            "x.ai",
            "slack",
            "bmw-m",
            "theverge",
        ),
        {
            "linear.app": "# Linear Inspired Design System Analysis",
            "mistral.ai": "# Mistral AI Inspired Design System Analysis",
            "opencode.ai": "# OpenCode AI Inspired Design System Analysis",
            "together.ai": "# Together AI Inspired Design System Analysis",
            "x.ai": "# xAI Inspired Design System Analysis",
            "bmw-m": "# Bmw-m Inspired Design System Analysis",
            "theverge": "# Theverge Inspired Design System Analysis",
        },
    )

    assert {item["id"] for item in items} == {
        "design-linear",
        "design-mistral",
        "design-opencode",
        "design-together",
        "design-xai",
        "design-slack",
        "design-bmw-m",
        "design-theverge",
    }
    titles = {item["id"]: item["title"] for item in items}
    assert titles["design-slack"] == "Slack"
    assert titles["design-bmw-m"] == "BMW M"
    assert titles["design-theverge"] == "The Verge"


def test_derivation_rejects_an_identifier_outside_the_manifest_pattern() -> None:
    with pytest.raises(ValueError, match="identifier.*manifest pattern"):
        sync_design_references.derive_design_references(
            ("bad_slug",),
            {"bad_slug": "# Bad Slug Inspired Design System Analysis"},
        )


def test_derivation_fails_loudly_when_the_upstream_heading_shape_changes() -> None:
    with pytest.raises(ValueError, match="heading shape changed.*stripe"):
        sync_design_references.derive_design_references(
            ("stripe",),
            {"stripe": "# Stripe Design Notes"},
        )


def test_synchronization_is_idempotent_and_check_detects_a_hand_edited_skill_block(
    tmp_path: Path,
) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "vendored": [
                    {"repo": "other/source", "paths": []},
                    {
                        "repo": "VoltAgent/awesome-design-md",
                        "paths": [
                            {
                                "src": "LICENSE",
                                "dest": "src/dev_ready/templates/docs/design-md-LICENSE.md",
                            }
                        ],
                    },
                ],
                "components": {
                    "docs": {
                        "items": [
                            {
                                "id": "other-doc",
                                "vendored_repo": "other/source",
                            }
                        ]
                    }
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    skill_path = tmp_path / "SKILL.md"
    skill_path.write_text(
        "# Interview\n\n### design items\n\n- stale\n\n### token-optimize items\n",
        encoding="utf-8",
    )
    headings = {"stripe": "# Stripe Inspired Design System Analysis"}

    assert sync_design_references.synchronize_outputs(
        manifest_path,
        skill_path,
        ("stripe",),
        headings,
        check=False,
    ) is True
    first_manifest = manifest_path.read_bytes()
    first_skill = skill_path.read_bytes()
    synchronized = json.loads(first_manifest)
    reference_paths = synchronized["vendored"][1]["paths"]
    assert reference_paths[-1] == {
        "src": "LICENSE",
        "dest": "src/dev_ready/templates/docs/design-md-LICENSE.md",
    }
    assert sync_design_references.synchronize_outputs(
        manifest_path,
        skill_path,
        ("stripe",),
        headings,
        check=False,
    ) is False
    assert manifest_path.read_bytes() == first_manifest
    assert skill_path.read_bytes() == first_skill

    skill_path.write_text(
        skill_path.read_text(encoding="utf-8").replace(
            "You want Stripe's design language", "Hand-edited guidance"
        ),
        encoding="utf-8",
    )
    edited = skill_path.read_bytes()
    assert sync_design_references.synchronize_outputs(
        manifest_path,
        skill_path,
        ("stripe",),
        headings,
        check=True,
    ) is True
    assert skill_path.read_bytes() == edited
