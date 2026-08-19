"""Behavior tests for the shared project-inspection seam."""

from dataclasses import replace
from pathlib import Path
import shutil

from dev_ready.inspection import ProjectExpectation, inspect_project
from dev_ready.manifest import ComponentCatalog, ItemPath, load_default_manifest
from dev_ready.prompts import ProjectSelection
from project_factory import materialize_project_structure


MANIFEST = load_default_manifest()
CATALOG = MANIFEST.components


def _catalog_with_second_loop() -> ComponentCatalog:
    current = next(
        item for item in CATALOG["skills"] if item.kind == "development-loop"
    )
    alternate = replace(
        current,
        id="alternate-loop",
        steps=("alternate-step",),
        paths=(
            ItemPath(
                src="claude/skills/alternate-loop",
                dest=".agents/skills/alternate-loop",
            ),
        ),
    )
    components = dict(CATALOG)
    components["skills"] = (*CATALOG["skills"], alternate)
    return ComponentCatalog(
        components,
        CATALOG.agent_targets,
        CATALOG.categories,
        CATALOG.default_set,
    )


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


def test_lifecycle_inspection_requires_documentation_infrastructure(
    tmp_path: Path,
) -> None:
    selection = ProjectSelection.from_items(CATALOG, docs_items=frozenset())
    materialize_project_structure(tmp_path, CATALOG, selection)
    shutil.rmtree(tmp_path / "docs")

    issues = inspect_project(
        tmp_path,
        CATALOG,
        ProjectExpectation.lifecycle(selection),
    )

    assert any(
        issue.category == "missing overlay directory"
        and "documentation directory 'docs/' is missing" in issue.detail
        for issue in issues
    )


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


def test_generation_inspection_requires_the_development_loop_as_structure(
    tmp_path: Path,
) -> None:
    selection = ProjectSelection.empty()
    materialize_project_structure(tmp_path, CATALOG, selection)

    issues = inspect_project(
        tmp_path,
        CATALOG,
        ProjectExpectation.generation(selection),
    )

    assert any(
        issue.category == "missing item path"
        and "development loop item 'mattpocock'" in issue.detail
        for issue in issues
    )


def test_generation_inspection_requires_only_the_resolved_loop(tmp_path: Path) -> None:
    catalog = _catalog_with_second_loop()
    selection = ProjectSelection.default_set(catalog)
    materialize_project_structure(tmp_path, catalog, selection)

    issues = inspect_project(
        tmp_path,
        catalog,
        ProjectExpectation.generation(selection),
    )

    assert not any("alternate-loop" in issue.detail for issue in issues)


def test_inspection_reports_malformed_effect_target_as_a_fact(tmp_path: Path) -> None:
    target = tmp_path / ".mcp.json"
    target.write_text("[]", encoding="utf-8")
    selection = ProjectSelection.from_items(
        CATALOG,
        mcp=frozenset({"code-memory"}),
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
        skills=frozenset({"mattpocock"}),
    )

    # Fake generation of mattpocock asset without .tmpl suffix (rendered destination path)
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
    )
    materialize_project_structure(tmp_path, CATALOG, selection)
    missing_link = tmp_path / ".windsurf/skills/caveman"
    if missing_link.is_symlink() or missing_link.is_junction():
        missing_link.unlink()
    elif missing_link.exists():
        missing_link.unlink()

    issues = inspect_project(
        tmp_path,
        CATALOG,
        ProjectExpectation.lifecycle(selection),
    )

    assert any(
        issue.category == "missing agent target artifact"
        and "windsurf" in issue.detail
        and ".windsurf/skills/caveman" in issue.detail
        for issue in issues
    )
    assert not any("claude" in issue.detail for issue in issues)
    assert not any(".mcp.json" in issue.detail for issue in issues)


def test_inspection_reports_incomplete_ignore_anchor_against_the_full_projection(
    tmp_path: Path,
) -> None:
    selection = ProjectSelection.from_items(
        CATALOG,
        skills=frozenset({"caveman"}),
        mcp=frozenset(),
        agent_targets=frozenset({"claude"}),
    )
    materialize_project_structure(tmp_path, CATALOG, selection)
    from dev_ready.overlay import render_ignore_anchor

    anchor = tmp_path / ".claude" / "skills" / ".gitignore"
    anchor.write_bytes(render_ignore_anchor(["setup-project"]))

    issues = inspect_project(
        tmp_path,
        CATALOG,
        ProjectExpectation.lifecycle(selection),
    )

    assert any(
        ".claude/skills/.gitignore" in issue.detail
        and "caveman" in issue.detail
        for issue in issues
    )


def test_inspection_reports_redirected_skills_directory_without_traversing(
    tmp_path: Path,
) -> None:
    from dev_ready.skill_links import create_skill_link

    selection = ProjectSelection.from_items(
        CATALOG,
        skills=frozenset({"caveman"}),
        mcp=frozenset(),
        agent_targets=frozenset({"claude"}),
    )
    materialize_project_structure(tmp_path, CATALOG, selection)
    skills = tmp_path / ".claude" / "skills"
    real = tmp_path / ".claude" / "skills-real"
    skills.rename(real)
    create_skill_link(skills, real)

    issues = inspect_project(
        tmp_path,
        CATALOG,
        ProjectExpectation.lifecycle(selection),
    )

    details = [issue.detail for issue in issues]
    assert any(
        "claude" in detail and ".claude/skills" in detail and "must not be a link" in detail
        for detail in details
    )
    assert not any("caveman" in detail for detail in details)
    assert not any(".gitignore" in detail for detail in details)


def test_inspection_reports_stale_links_and_extra_anchor_names(
    tmp_path: Path,
) -> None:
    from dev_ready.overlay import render_ignore_anchor
    from dev_ready.skill_links import create_skill_link

    selection = ProjectSelection.from_items(
        CATALOG,
        skills=frozenset({"caveman"}),
        mcp=frozenset(),
        agent_targets=frozenset({"claude"}),
    )
    materialize_project_structure(tmp_path, CATALOG, selection)
    canonical = tmp_path / ".agents" / "skills" / "caveman"
    stale = tmp_path / ".claude" / "skills" / "retired-skill"
    create_skill_link(stale, canonical)
    names = ["setup-project", "caveman", "retired-skill"]
    (tmp_path / ".claude" / "skills" / ".gitignore").write_bytes(
        render_ignore_anchor(names)
    )

    issues = inspect_project(
        tmp_path,
        CATALOG,
        ProjectExpectation.lifecycle(selection),
    )
    details = [issue.detail for issue in issues]
    assert any("retired-skill" in detail and "stale" in detail for detail in details)
    assert any(".gitignore" in detail and "retired-skill" in detail for detail in details)


def test_inspection_reports_an_obsolete_unselected_nested_anchor(
    tmp_path: Path,
) -> None:
    selection = ProjectSelection.from_items(
        CATALOG,
        skills=frozenset({"caveman"}),
        mcp=frozenset(),
        agent_targets=frozenset({"claude", "windsurf"}),
    )
    materialize_project_structure(tmp_path, CATALOG, selection)
    claude_only = ProjectSelection.from_items(
        CATALOG,
        skills=frozenset({"caveman"}),
        mcp=frozenset(),
        agent_targets=frozenset({"claude"}),
    )

    issues = inspect_project(
        tmp_path,
        CATALOG,
        ProjectExpectation.lifecycle(claude_only),
    )
    details = [issue.detail for issue in issues]
    assert (tmp_path / ".windsurf" / "skills" / ".gitignore").is_file()
    assert any(
        "windsurf" in detail
        and ".windsurf/skills/.gitignore" in detail
        and "obsolete" in detail
        for detail in details
    )
