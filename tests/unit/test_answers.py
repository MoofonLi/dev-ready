"""Behavior tests for the canonical generation-intent seam."""

from pathlib import Path

import pytest

from dev_ready.errors import InvalidArgumentsError
from dev_ready.manifest import CatalogItem, ItemPath, load_default_manifest
from dev_ready.prompts import Answers, ProjectSelection


CATALOG = load_default_manifest().components


def test_flag_and_prompt_adapters_share_one_canonical_selection() -> None:
    selection = ProjectSelection.from_flags(
        catalog=CATALOG,
        skills="project-orientation, tdd",
        mcp="none",
        no_skills=False,
        no_mcp=False,
        no_docs=True,
        no_handoff=False,
    )

    assert selection is not None
    answers = Answers(
        project_name="my-app",
        target_dir=Path("my-app"),
        selection=selection,
    )
    assert answers.items("skills") == frozenset({"project-orientation", "tdd"})
    assert answers.items("mcp") == frozenset()
    assert answers.includes("skills") is True
    assert answers.includes("mcp") is False
    assert answers.includes("docs") is False
    assert answers.includes("handoff") is True


def test_no_selection_flags_leave_selection_unresolved() -> None:
    assert (
        ProjectSelection.from_flags(
            catalog=CATALOG,
            skills=None,
            mcp=None,
            no_skills=False,
            no_mcp=False,
            no_docs=False,
            no_handoff=False,
        )
        is None
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


def _dependency_catalog() -> dict[str, tuple[CatalogItem, ...]]:
    def item(item_id: str, *requires: str) -> CatalogItem:
        return CatalogItem(
            id=item_id,
            description=item_id,
            mode="builtin",
            license="MIT",
            paths=(ItemPath(src=item_id, dest=item_id),),
            requires=requires,
        )

    return {
        "skills": (
            item("review"),
            item("tdd", "review"),
            item("spec-loop", "tdd"),
            item("standalone"),
        ),
        "mcp": (),
    }


def test_selection_resolves_transitive_requirements() -> None:
    selection = ProjectSelection.from_items(
        _dependency_catalog(), skills=frozenset({"spec-loop"})
    )

    assert selection.skills == frozenset({"spec-loop", "tdd", "review"})


def test_flag_selection_exposes_resolved_requirements() -> None:
    selection = ProjectSelection.from_flags(
        catalog=_dependency_catalog(),
        skills="spec-loop",
        mcp="none",
        no_skills=False,
        no_mcp=False,
        no_docs=False,
        no_handoff=False,
    )

    assert selection is not None
    assert selection.skills == frozenset({"spec-loop", "tdd", "review"})


def test_explicit_none_has_an_empty_dependency_closure() -> None:
    selection = ProjectSelection.from_flags(
        catalog=_dependency_catalog(),
        skills="none",
        mcp="none",
        no_skills=False,
        no_mcp=False,
        no_docs=False,
        no_handoff=False,
    )

    assert selection is not None
    assert selection.skills == frozenset()


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
        skills=None,
        mcp=None,
        agents=raw,
        no_skills=False,
        no_mcp=False,
        no_docs=False,
        no_handoff=False,
    )

    assert selection is not None
    assert selection.agent_targets == expected


def test_unknown_agent_target_lists_valid_ids() -> None:
    with pytest.raises(InvalidArgumentsError) as excinfo:
        ProjectSelection.from_flags(
            catalog=CATALOG,
            skills=None,
            mcp=None,
            agents="claud",
            no_skills=False,
            no_mcp=False,
            no_docs=False,
            no_handoff=False,
        )

    message = str(excinfo.value)
    assert "unknown agent target ids" in message
    assert "claude" in message
    assert "windsurf" in message
