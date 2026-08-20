"""Offline tests for scripts/check_ignore_drift.py (no network; fixture-driven)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "check_ignore_drift.py"
_spec = importlib.util.spec_from_file_location("check_ignore_drift", _SCRIPT_PATH)
assert _spec is not None and _spec.loader is not None
check_ignore_drift = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check_ignore_drift)

UPSTREAM = """.vscode/*
!.vscode/extensions.json
node_modules/
backend/app/frontend/
/test-results/
/playwright-report/
/blob-report/
/playwright/.cache/
"""

ADOPTED = """# Managed by dev-ready.
.vscode/*
!.vscode/extensions.json
node_modules/
backend/app/frontend/
/test-results/
/playwright-report/
/blob-report/
/playwright/.cache/

# --- dev-ready ---
.env
.env*
.superpowers/
"""


def test_entries_drop_comments_and_blank_lines() -> None:
    assert check_ignore_drift.ignore_entries(ADOPTED) == (
        ".vscode/*",
        "!.vscode/extensions.json",
        "node_modules/",
        "backend/app/frontend/",
        "/test-results/",
        "/playwright-report/",
        "/blob-report/",
        "/playwright/.cache/",
        ".env",
        ".env*",
        ".superpowers/",
    )


def test_carriage_returns_never_change_an_entry() -> None:
    assert check_ignore_drift.ignore_entries("node_modules/\r\n.env\r\n") == (
        "node_modules/",
        ".env",
    )


def test_dev_ready_additions_are_excluded_from_the_comparison() -> None:
    """The two `.env` lines are deliberately not upstream's and must never fail the check."""
    derived = check_ignore_drift.upstream_derived_entries(ADOPTED)
    assert ".env" not in derived
    assert ".env*" not in derived
    assert derived == check_ignore_drift.ignore_entries(UPSTREAM)


def test_matching_files_report_no_drift() -> None:
    assert check_ignore_drift.compare_ignore_files(UPSTREAM, ADOPTED) == []


def test_an_entry_added_upstream_is_reported_by_name() -> None:
    drifted = UPSTREAM + ".turbo/\n"

    failures = check_ignore_drift.compare_ignore_files(drifted, ADOPTED)

    assert len(failures) == 1
    assert ".turbo/" in failures[0]
    assert "added" in failures[0]


def test_an_entry_removed_upstream_is_reported_by_name() -> None:
    drifted = UPSTREAM.replace("/blob-report/\n", "")

    failures = check_ignore_drift.compare_ignore_files(drifted, ADOPTED)

    assert len(failures) == 1
    assert "/blob-report/" in failures[0]
    assert "no longer" in failures[0]


def test_a_reorder_upstream_is_reported_without_naming_a_phantom_entry() -> None:
    drifted = """node_modules/
.vscode/*
!.vscode/extensions.json
backend/app/frontend/
/test-results/
/playwright-report/
/blob-report/
/playwright/.cache/
"""

    failures = check_ignore_drift.compare_ignore_files(drifted, ADOPTED)

    assert len(failures) == 1
    assert "order" in failures[0]


def test_an_upstream_file_that_is_missing_entirely_fails_loudly() -> None:
    failures = check_ignore_drift.compare_ignore_files(None, ADOPTED)

    assert len(failures) == 1
    assert "missing" in failures[0]


def test_upstream_adopted_by_dev_ready_is_still_reported() -> None:
    """If upstream adopts `.env` itself, the exclusion-by-construction must not hide it."""
    drifted = UPSTREAM + ".env\n"

    failures = check_ignore_drift.compare_ignore_files(drifted, ADOPTED)

    assert len(failures) == 1
    assert ".env" in failures[0]


def test_the_shipped_template_is_the_file_the_check_reads() -> None:
    adopted = check_ignore_drift.adopted_ignore_text()

    assert check_ignore_drift.upstream_derived_entries(adopted) == check_ignore_drift.ignore_entries(
        UPSTREAM
    )


def test_the_shipped_template_carries_the_dev_ready_additions() -> None:
    entries = check_ignore_drift.ignore_entries(check_ignore_drift.adopted_ignore_text())

    assert set(check_ignore_drift.DEV_READY_ADDITIONS) <= set(entries)


@pytest.mark.parametrize("empty", ["", "\n\n", "# only a comment\n"])
def test_an_empty_upstream_file_is_drift_rather_than_agreement(empty: str) -> None:
    assert check_ignore_drift.compare_ignore_files(empty, ADOPTED) != []
