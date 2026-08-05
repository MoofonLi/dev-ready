"""Integration test: the adopted root ignore file against the real pinned commit.

The comparison logic itself is unit-tested offline in
`tests/unit/test_check_ignore_drift.py`; this only proves the pinned upstream
file is what the adopted copy claims it is.
"""

import importlib.util
from pathlib import Path

import pytest

pytestmark = pytest.mark.network

_SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "check_ignore_drift.py"
_spec = importlib.util.spec_from_file_location("check_ignore_drift", _SCRIPT_PATH)
assert _spec is not None and _spec.loader is not None
check_ignore_drift = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check_ignore_drift)


def test_adopted_root_ignore_file_matches_upstream_at_the_pin() -> None:
    assert check_ignore_drift.check_ignore_drift() == []
