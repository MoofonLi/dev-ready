"""Unit tests for dev_ready.verify (no network, filesystem confined to tmp_path)."""

from pathlib import Path

import pytest

from dev_ready.errors import VerificationError
from dev_ready.verify import FORBIDDEN_PATHS, REQUIRED_UPSTREAM_PATHS, verify_project


_DIRECTORY_ENTRIES = {"backend", "frontend"}


def _make_complete_project(root: Path) -> None:
    for rel_path in REQUIRED_UPSTREAM_PATHS:
        path = root / rel_path
        if rel_path in _DIRECTORY_ENTRIES:
            path.mkdir(parents=True)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("stub", encoding="utf-8")


def test_verify_passes_when_all_required_paths_present(tmp_path: Path) -> None:
    _make_complete_project(tmp_path)
    verify_project(tmp_path)  # must not raise


@pytest.mark.parametrize("missing_path", REQUIRED_UPSTREAM_PATHS)
def test_verify_raises_when_one_required_path_is_missing(
    tmp_path: Path, missing_path: str
) -> None:
    _make_complete_project(tmp_path)
    target = tmp_path / missing_path
    if target.is_dir():
        target.rmdir()
    else:
        target.unlink()

    with pytest.raises(VerificationError) as excinfo:
        verify_project(tmp_path)

    message = str(excinfo.value)
    assert missing_path in message


def test_verify_error_message_contains_actionable_guidance(tmp_path: Path) -> None:
    # Empty project dir: the first path in REQUIRED_UPSTREAM_PATHS is missing.
    tmp_path_missing = tmp_path / "empty"
    tmp_path_missing.mkdir()

    with pytest.raises(VerificationError) as excinfo:
        verify_project(tmp_path_missing)

    message = str(excinfo.value)
    assert "upstream layout changed" in message
    assert "file an issue" in message


@pytest.mark.parametrize("forbidden_path", FORBIDDEN_PATHS)
def test_verify_raises_when_forbidden_path_is_present(
    tmp_path: Path, forbidden_path: str
) -> None:
    _make_complete_project(tmp_path)
    target = tmp_path / forbidden_path
    if forbidden_path == ".git":
        target.mkdir()
    else:
        target.write_text("stub", encoding="utf-8")

    with pytest.raises(VerificationError) as excinfo:
        verify_project(tmp_path)

    message = str(excinfo.value)
    assert forbidden_path in message
    assert "file an issue" in message
