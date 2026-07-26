"""Behavior tests for the catalog-item effect seam."""

import json
from pathlib import Path

import pytest

from dev_ready.catalog_effects import (
    CatalogEffectError,
    classify_shared_targets,
    parse_catalog_effect,
)
from dev_ready.manifest import load_default_manifest
from dev_ready.prompts import ProjectSelection


def test_mcp_effect_applies_and_observes_through_one_interface(tmp_path: Path) -> None:
    target = tmp_path / ".mcp.json"
    target.write_text('{"mcpServers": {"existing": {"command": "x"}}}', encoding="utf-8")
    effect = parse_catalog_effect(
        {
            "kind": "mcp-server",
            "target": ".mcp.json",
            "package": "codebase-memory-mcp",
            "server_name": "codebase-memory",
            "command": "uvx",
        },
        mode="pinned-dependency",
        pin="0.9.0",
        location="manifest item 'code-memory'",
    )

    assert effect is not None
    effect.apply(tmp_path)

    assert effect.is_present(tmp_path) is True
    data = json.loads(target.read_text(encoding="utf-8"))
    assert data["mcpServers"]["existing"] == {"command": "x"}
    assert data["mcpServers"]["codebase-memory"] == {
        "command": "uvx",
        "args": ["codebase-memory-mcp==0.9.0"],
    }


def test_npm_effect_applies_and_observes_through_one_interface(tmp_path: Path) -> None:
    target = tmp_path / "frontend" / "package.json"
    target.parent.mkdir()
    target.write_text('{"scripts": {"test": "vitest"}}', encoding="utf-8")
    effect = parse_catalog_effect(
        {
            "kind": "npm-dev-dependency",
            "target": "frontend/package.json",
            "package": "react-doctor",
            "scripts": {"doctor": "react-doctor"},
        },
        mode="pinned-dependency",
        pin="1.2.3",
        location="manifest item 'react-doctor'",
    )

    assert effect is not None
    effect.apply(tmp_path)

    assert effect.is_present(tmp_path) is True
    data = json.loads(target.read_text(encoding="utf-8"))
    assert data["devDependencies"]["react-doctor"] == "1.2.3"
    assert data["scripts"] == {"test": "vitest", "doctor": "react-doctor"}


def test_effect_reports_malformed_shared_target_at_the_same_seam(tmp_path: Path) -> None:
    target = tmp_path / ".mcp.json"
    target.write_text("[]", encoding="utf-8")
    effect = parse_catalog_effect(
        {
            "kind": "mcp-server",
            "target": ".mcp.json",
            "package": "codebase-memory-mcp",
            "server_name": "codebase-memory",
            "command": "uvx",
        },
        mode="pinned-dependency",
        pin="0.9.0",
        location="manifest item 'code-memory'",
    )

    assert effect is not None
    with pytest.raises(CatalogEffectError, match="root must be a JSON object"):
        effect.is_present(tmp_path)


def test_effect_presence_requires_exact_configured_values(tmp_path: Path) -> None:
    target = tmp_path / ".mcp.json"
    target.write_text("{}", encoding="utf-8")
    effect = parse_catalog_effect(
        {
            "kind": "mcp-server",
            "target": ".mcp.json",
            "package": "codebase-memory-mcp",
            "server_name": "codebase-memory",
            "command": "uvx",
        },
        mode="pinned-dependency",
        pin="0.9.0",
        location="manifest item 'code-memory'",
    )
    assert effect is not None
    effect.apply(tmp_path)
    data = json.loads(target.read_text(encoding="utf-8"))
    data["mcpServers"]["codebase-memory"]["args"] = ["codebase-memory-mcp==latest"]
    target.write_text(json.dumps(data), encoding="utf-8")

    assert effect.is_present(tmp_path) is False


def test_npm_effect_presence_requires_exact_pin_and_scripts(tmp_path: Path) -> None:
    target = tmp_path / "frontend" / "package.json"
    target.parent.mkdir()
    target.write_text("{}", encoding="utf-8")
    effect = parse_catalog_effect(
        {
            "kind": "npm-dev-dependency",
            "target": "frontend/package.json",
            "package": "react-doctor",
            "scripts": {"doctor": "react-doctor"},
        },
        mode="pinned-dependency",
        pin="1.2.3",
        location="manifest item 'react-doctor'",
    )
    assert effect is not None
    effect.apply(tmp_path)
    data = json.loads(target.read_text(encoding="utf-8"))
    data["devDependencies"]["react-doctor"] = "latest"
    data["scripts"]["doctor"] = "different-command"
    target.write_text(json.dumps(data), encoding="utf-8")

    assert effect.is_present(tmp_path) is False


def test_effect_rejects_symlink_that_escapes_project(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "package.json").write_text("{}", encoding="utf-8")
    try:
        (project / "frontend").symlink_to(outside, target_is_directory=True)
    except OSError as error:
        pytest.skip(f"symlinks unavailable: {error}")

    effect = parse_catalog_effect(
        {
            "kind": "npm-dev-dependency",
            "target": "frontend/package.json",
            "package": "react-doctor",
            "scripts": {"doctor": "react-doctor"},
        },
        mode="pinned-dependency",
        pin="1.2.3",
        location="manifest item 'react-doctor'",
    )

    assert effect is not None
    with pytest.raises(CatalogEffectError, match="unsafe target"):
        effect.apply(project)
    assert json.loads((outside / "package.json").read_text(encoding="utf-8")) == {}


def test_shared_target_classification_stays_behind_effect_seam() -> None:
    manifest = load_default_manifest()
    selection = ProjectSelection.from_items(
        manifest.components,
        mcp=frozenset({"mcp-config", "code-memory"}),
        docs=False,
        handoff=False,
    )

    targets = classify_shared_targets(manifest.components, selection)

    assert "frontend/package.json" in targets.all
    assert ".mcp.json" in targets.selected
