"""Offline guard for Engineering Flow Selection Criteria declarations."""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import replace

import pytest

from dev_ready.manifest import CatalogItem, load_default_manifest

_DECLARED_FLOW_FIELDS = frozenset({"invocation", "chain", "steps"})
_EXPECTED_CRITERIA_COUNT = 3
_BACKTICKED_NAME = re.compile(r"`([^`]+)`")


def check_flow_selection_criteria(loop: CatalogItem) -> None:
    """Assert that every criterion names only declarations owned by its flow."""
    allowed_names = _DECLARED_FLOW_FIELDS | frozenset(loop.steps)
    for clause in loop.choose_when:
        names = _BACKTICKED_NAME.findall(clause)
        assert names, f"flow {loop.id!r} criterion names no declared field or step"
        unknown_names = sorted(set(names) - allowed_names)
        assert not unknown_names, (
            f"flow {loop.id!r} criterion names undeclared value {unknown_names[0]!r}"
        )


def check_flow_selection_criteria_counts(loops: Iterable[CatalogItem]) -> None:
    """Assert that every flow declares the fixed, comparable criteria count."""
    counts = {loop.id: len(loop.choose_when) for loop in loops}
    assert counts and set(counts.values()) == {_EXPECTED_CRITERIA_COUNT}, (
        "flows must each declare exactly "
        f"{_EXPECTED_CRITERIA_COUNT} criteria, got {counts!r}"
    )


def _loop(*criteria: str) -> CatalogItem:
    return CatalogItem(
        id="test-flow",
        category="dev",
        kind="development-loop",
        description="Test flow.",
        mode="builtin",
        license="MIT",
        steps=("test-step",),
        choose_when=criteria,
        invocation="user",
        chain=("test-step",),
    )


def test_default_manifest_flows_satisfy_selection_criteria_invariants() -> None:
    loops = load_default_manifest().components.loops()
    assert loops
    for loop in loops:
        check_flow_selection_criteria(loop)
    check_flow_selection_criteria_counts(loops)


def test_criterion_rejects_a_name_the_flow_does_not_declare() -> None:
    with pytest.raises(AssertionError, match="undeclared value 'missing-step'"):
        check_flow_selection_criteria(_loop("Use `missing-step` first."))


def test_criterion_rejects_a_clause_without_a_backticked_name() -> None:
    with pytest.raises(AssertionError, match="names no declared field or step"):
        check_flow_selection_criteria(_loop("Use this flow for uncertain work."))


@pytest.mark.parametrize("field", ["invocation", "chain", "steps"])
def test_criterion_accepts_a_declared_flow_field(field: str) -> None:
    check_flow_selection_criteria(_loop(f"Use the flow's `{field}` declaration."))


def test_flows_reject_different_criteria_counts() -> None:
    three_criteria = _loop("Use `steps`.", "Use `chain`.", "Use `invocation`.")
    two_criteria = replace(
        three_criteria,
        id="other-flow",
        choose_when=("Use `steps`.", "Use `chain`."),
    )

    with pytest.raises(AssertionError, match="each declare exactly 3 criteria"):
        check_flow_selection_criteria_counts((three_criteria, two_criteria))
