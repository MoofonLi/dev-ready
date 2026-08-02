"""Behavior tests for the canonical generation-intent seam."""

from dataclasses import replace
from pathlib import Path

import pytest

from dev_ready.errors import InvalidArgumentsError
from dev_ready.manifest import CatalogItem, ComponentCatalog, ItemPath, load_default_manifest
from dev_ready.prompts import Answers, ProjectSelection


CATALOG = load_default_manifest().components


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


def test_flag_and_prompt_adapters_share_one_canonical_selection() -> None:
    selection = ProjectSelection.from_flags(
        catalog=CATALOG,
        categories="all",
        category_items={
            "dev": "none",
            "security": "none",
            "quality": "none",
            "design": "none",
            "token-optimize": "caveman",
        },
    )

    assert selection is not None
    answers = Answers(
        project_name="my-app",
        target_dir=Path("my-app"),
        selection=selection,
    )
    assert answers.items("skills") == frozenset(
        {"caveman", "spec-loop"}
    )
    assert answers.items("mcp") == frozenset()
    assert answers.includes("skills") is True
    assert answers.includes("mcp") is False
    assert answers.includes("docs") is False


def test_handoff_is_not_a_generation_selection_axis() -> None:
    selection = ProjectSelection.all(CATALOG)

    with pytest.raises(ValueError, match="unknown selection"):
        selection.includes("handoff")
    assert not hasattr(selection, "handoff")


def test_default_set_is_the_loop_without_selected_documentation_items() -> None:
    selection = ProjectSelection.default_set(CATALOG)

    assert selection.development_loop == "spec-loop"
    assert selection.items("skills") == frozenset({"spec-loop"})
    assert selection.items("mcp") == frozenset()
    assert selection.items("docs") == frozenset()
    assert selection.includes("docs") is False
    assert not hasattr(selection, "docs")
    assert selection.categories == frozenset({"dev"})


def test_second_loop_is_a_data_addition_with_one_resolved_default() -> None:
    catalog = _catalog_with_second_loop()

    default_selection = ProjectSelection.default_set(catalog)
    all_selection = ProjectSelection.all(catalog)
    empty_enhancements = ProjectSelection.from_flags(
        catalog=catalog,
        categories="none",
        category_items={},
    )
    alternate_selection = ProjectSelection.from_items(
        catalog,
        skills=frozenset({"alternate-loop"}),
    )
    alternate_flag_selection = ProjectSelection.from_flags(
        catalog=catalog,
        categories="none",
        category_items={},
        development_loop="alternate-loop",
    )

    for selection in (default_selection, all_selection, empty_enhancements):
        assert selection is not None
        assert selection.development_loop == "spec-loop"
        assert "spec-loop" in selection.skills
        assert "alternate-loop" not in selection.skills
    assert alternate_selection.development_loop == "alternate-loop"
    assert alternate_flag_selection is not None
    assert alternate_flag_selection.development_loop == "alternate-loop"

    with pytest.raises(InvalidArgumentsError, match="unknown development loop"):
        ProjectSelection.from_flags(
            catalog=catalog,
            categories="none",
            category_items={},
            development_loop="unknown-loop",
        )


def test_explicit_whole_catalog_selection_still_includes_every_enhancement() -> None:
    selection = ProjectSelection.all(CATALOG)

    assert selection.items("skills") == frozenset(
        item.id for item in CATALOG["skills"]
    )
    assert selection.items("mcp") == frozenset(item.id for item in CATALOG["mcp"])
    assert selection.items("docs") == frozenset(item.id for item in CATALOG["docs"])


def test_no_selection_flags_leave_selection_unresolved() -> None:
    assert (
        ProjectSelection.from_flags(
            catalog=CATALOG,
            categories=None,
            category_items={},
        )
        is None
    )


@pytest.mark.parametrize(
    ("raw", "expected_skills", "expected_mcp", "expected_docs"),
    [
        (
            "all",
            frozenset(item.id for item in CATALOG["skills"]),
            frozenset(item.id for item in CATALOG["mcp"]),
            True,
        ),
        (
            "none",
            frozenset({"spec-loop"}),
            frozenset(),
            False,
        ),
    ],
)
def test_category_level_all_and_none(
    raw: str,
    expected_skills: frozenset[str],
    expected_mcp: frozenset[str],
    expected_docs: bool,
) -> None:
    selection = ProjectSelection.from_flags(
        catalog=CATALOG,
        categories=raw,
        category_items={},
    )

    assert selection is not None
    assert selection.items("skills") == expected_skills
    assert selection.items("mcp") == expected_mcp
    assert selection.includes("docs") is expected_docs


def test_declining_every_category_still_resolves_the_development_loop() -> None:
    selection = ProjectSelection.from_flags(
        catalog=CATALOG,
        categories="none",
        category_items={},
    )

    assert selection is not None
    assert selection.development_loop == "spec-loop"
    assert selection.items("skills") == frozenset({"spec-loop"})
    assert selection.categories == frozenset({"dev"})


def test_recorded_selection_does_not_apply_the_phase_4_loop_migration() -> None:
    selection = ProjectSelection.from_recorded_items(
        CATALOG,
        skills=frozenset({"caveman"}),
        mcp=frozenset(),
        docs_items=frozenset(),
        agent_targets=frozenset({"claude"}),
    )

    assert selection.development_loop == ""
    assert selection.items("skills") == frozenset({"caveman"})
    assert "dev" not in selection.categories


def test_unknown_category_lists_valid_ids() -> None:
    with pytest.raises(InvalidArgumentsError) as excinfo:
        ProjectSelection.from_flags(
            catalog=CATALOG,
            categories="performance",
            category_items={},
        )

    message = str(excinfo.value)
    assert "unknown Category ids: ['performance']" in message
    assert "['design', 'dev', 'quality', 'security', 'token-optimize']" in message


def test_unknown_category_item_lists_valid_ids() -> None:
    with pytest.raises(InvalidArgumentsError) as excinfo:
        ProjectSelection.from_flags(
            catalog=CATALOG,
            categories="security",
            category_items={"security": "ghost"},
        )

    message = str(excinfo.value)
    assert "unknown Security item ids: ['ghost']" in message
    assert "valid ids: ['security-audit']" in message


def test_category_override_must_belong_to_selected_categories() -> None:
    with pytest.raises(InvalidArgumentsError, match="--quality conflicts with --categories"):
        ProjectSelection.from_flags(
            catalog=CATALOG,
            categories="security",
            category_items={"quality": "react-doctor"},
        )


def test_answers_rejects_invalid_project_name_at_its_interface() -> None:
    with pytest.raises(InvalidArgumentsError, match="invalid project name"):
        Answers(
            project_name="../escape",
            target_dir=Path("escape"),
            selection=ProjectSelection.empty(),
        )


def test_canonical_selection_rejects_unknown_catalog_items() -> None:
    with pytest.raises(InvalidArgumentsError, match="unknown skills item ids"):
        ProjectSelection.from_items(CATALOG, skills=frozenset({"ghost-skill"}))


def _dependency_catalog() -> ComponentCatalog:
    def item(item_id: str, *requires: str) -> CatalogItem:
        return CatalogItem(
            id=item_id,
            category="dev",
            description=item_id,
            mode="builtin",
            license="MIT",
            paths=(ItemPath(src=item_id, dest=item_id),),
            requires=requires,
        )

    return ComponentCatalog(
        {
            "skills": (
                item("review"),
                item("tdd", "review"),
                item("spec-loop", "tdd"),
                item("standalone"),
            ),
            "mcp": (),
        },
        agent_targets={},
    )


def test_selection_resolves_transitive_requirements() -> None:
    selection = ProjectSelection.from_items(
        _dependency_catalog(), skills=frozenset({"spec-loop"})
    )

    assert selection.skills == frozenset({"spec-loop", "tdd", "review"})


def test_category_flag_selection_exposes_the_named_development_loop() -> None:
    selection = ProjectSelection.from_flags(
        catalog=CATALOG,
        categories="dev",
        category_items={"dev": "none"},
    )

    assert selection is not None
    assert selection.skills == frozenset({"spec-loop"})


def test_explicit_none_keeps_the_mandatory_loop_dependency_closure() -> None:
    selection = ProjectSelection.from_flags(
        catalog=CATALOG,
        categories="dev",
        category_items={"dev": "none"},
    )

    assert selection is not None
    assert selection.skills == frozenset({"spec-loop"})


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("claude,windsurf", frozenset({"claude", "windsurf"})),
        ("all", frozenset({"claude", "windsurf"})),
        ("none", frozenset()),
    ],
)
def test_agent_target_flag_selection(raw: str, expected: frozenset[str]) -> None:
    selection = ProjectSelection.from_flags(
        catalog=CATALOG,
        categories=None,
        category_items={},
        agents=raw,
    )

    assert selection is not None
    assert selection.agent_targets == expected


def test_unknown_agent_target_lists_valid_ids() -> None:
    with pytest.raises(InvalidArgumentsError) as excinfo:
        ProjectSelection.from_flags(
            catalog=CATALOG,
            categories=None,
            category_items={},
            agents="claud",
        )

    message = str(excinfo.value)
    assert "unknown agent target ids" in message
    assert "claude" in message
    assert "windsurf" in message
