"""Behavior tests for the shared project-inspection seam."""

from pathlib import Path

from dev_ready.inspection import ProjectExpectation, inspect_project
from dev_ready.manifest import load_default_manifest
from dev_ready.prompts import ProjectSelection
from project_factory import materialize_project_structure


MANIFEST = load_default_manifest()
CATALOG = MANIFEST.components


def test_lifecycle_inspection_aggregates_shared_structural_facts(tmp_path: Path) -> None:
    issues = inspect_project(
        tmp_path,
        CATALOG,
        ProjectExpectation.lifecycle(ProjectSelection.empty()),
    )

    categories = {issue.category for issue in issues}
    assert "missing upstream path" in categories
    assert "missing overlay path" in categories
    assert "missing overlay file" in categories


def test_generation_inspection_rejects_unselected_catalog_paths(tmp_path: Path) -> None:
    leaked = tmp_path / ".agents" / "skills" / "caveman" / "SKILL.md"
    leaked.parent.mkdir(parents=True)
    leaked.write_text("leak", encoding="utf-8")

    issues = inspect_project(
        tmp_path,
        CATALOG,
        ProjectExpectation.generation(ProjectSelection.empty()),
    )

    assert any(
        issue.category == "unexpected item path" and "caveman" in issue.detail
        for issue in issues
    )


def test_inspection_reports_malformed_effect_target_as_a_fact(tmp_path: Path) -> None:
    target = tmp_path / ".mcp.json"
    target.write_text("[]", encoding="utf-8")
    selection = ProjectSelection.from_items(
        CATALOG,
        mcp=frozenset({"code-memory"}),
        docs=False,
    )

    issues = inspect_project(
        tmp_path,
        CATALOG,
        ProjectExpectation.lifecycle(selection),
    )

    assert any(
        issue.category == "invalid inject target" and "JSON object" in issue.detail
        for issue in issues
    )


def test_inspection_strips_template_suffix_from_catalog_assets(tmp_path: Path) -> None:
    selection = ProjectSelection.from_items(
        CATALOG,
        skills=frozenset({"spec-loop"}),
        docs=False,
    )

    # Fake generation of spec-loop asset without .tmpl suffix (rendered destination path)
    asset_dir = tmp_path / "docs" / "agents"
    asset_dir.mkdir(parents=True)
    (asset_dir / "issue-tracker.md").write_text("tracker", encoding="utf-8")
    (asset_dir / "triage-labels.md").write_text("labels", encoding="utf-8")
    (asset_dir / "domain.md").write_text("domain", encoding="utf-8")

    issues = inspect_project(
        tmp_path,
        CATALOG,
        ProjectExpectation.generation(selection),
    )

    # Should not report missing asset issue-tracker.md.tmpl
    assert not any("issue-tracker.md.tmpl" in issue.detail for issue in issues)


def test_inspection_requires_the_selected_design_reference(tmp_path: Path) -> None:
    selection = ProjectSelection.from_items(
        CATALOG,
        docs_items=frozenset({"design-stripe"}),
        docs=True,
    )

    issues = inspect_project(
        tmp_path,
        CATALOG,
        ProjectExpectation.generation(selection),
    )

    assert any(
        issue.category == "missing item path"
        and "docs item 'design-stripe'" in issue.detail
        for issue in issues
    )


def test_inspection_requires_only_selected_agent_target_artifacts(tmp_path: Path) -> None:
    selection = ProjectSelection.from_items(
        CATALOG,
        skills=frozenset({"caveman"}),
        mcp=frozenset({"code-memory"}),
        agent_targets=frozenset({"windsurf"}),
        docs=False,
    )
    materialize_project_structure(tmp_path, CATALOG, selection)
    missing_stub = tmp_path / ".windsurf/skills/caveman/SKILL.md"
    missing_stub.unlink()

    issues = inspect_project(
        tmp_path,
        CATALOG,
        ProjectExpectation.lifecycle(selection),
    )

    assert any(
        issue.category == "missing agent target artifact"
        and "windsurf" in issue.detail
        and ".windsurf/skills/caveman/SKILL.md" in issue.detail
        for issue in issues
    )
    assert not any("claude" in issue.detail for issue in issues)
    assert not any(".mcp.json" in issue.detail for issue in issues)
