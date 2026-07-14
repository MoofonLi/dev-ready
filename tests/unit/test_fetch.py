"""Unit tests for dev_ready.fetch (no network; Copier is mocked)."""

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import copier
import pytest
from copier.errors import CopierError

import dev_ready.fetch.snapshot as snapshot_module
from dev_ready.errors import FetchError, TargetDirectoryError
from dev_ready.fetch import fetch_snapshot
from dev_ready.manifest import UpstreamPin

PIN = UpstreamPin(
    repo="fastapi/full-stack-fastapi-template",
    ref="master",
    commit="4cd0d9e51aebd1af6f82d91ad0df4c9e41f4dea2",
    license="MIT",
    exclude=(".agents/skills/fastapi", ".claude/skills/fastapi"),
)


@pytest.fixture(autouse=True)
def _isolated_tempdir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Force tempfile.mkdtemp() (dir=None) to land inside tmp_path.

    fetch_snapshot uses tempfile.mkdtemp() directly, which otherwise writes
    outside tmp_path; this keeps the whole test file filesystem-confined and
    lets leak checks be deterministic.
    """
    temp_root = tmp_path / "_systmp"
    temp_root.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(temp_root))
    return temp_root


@pytest.fixture(autouse=True)
def _git_available(monkeypatch: pytest.MonkeyPatch) -> None:
    """Unit tests never shell out; pretend git exists unless a test overrides."""
    monkeypatch.setattr(snapshot_module.shutil, "which", lambda _name: "/usr/bin/git")


def _install_fake_run_copy(
    monkeypatch: pytest.MonkeyPatch, recorded: dict[str, Any]
) -> None:
    def _fake_run_copy(
        src_path: str, dst_path: Path | str, data: dict[str, Any] | None = None, **kwargs: Any
    ) -> None:
        recorded["src_path"] = src_path
        recorded["dst_path"] = Path(dst_path)
        recorded["data"] = data
        recorded["kwargs"] = kwargs
        # Copier writes into an existing destination directory.
        (Path(dst_path) / "README.md").write_text("upstream", encoding="utf-8")
        (Path(dst_path) / "backend").mkdir()

    monkeypatch.setattr(copier, "run_copy", _fake_run_copy)


def test_happy_path_populates_dest_and_pins_copier_call(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    recorded: dict[str, Any] = {}
    _install_fake_run_copy(monkeypatch, recorded)
    dest = tmp_path / "snapshot"
    data = {"project_name": "My App", "secret_key": "s3cret"}

    result = fetch_snapshot(PIN, dest, data)

    assert result == dest
    assert (dest / "README.md").read_text(encoding="utf-8") == "upstream"
    assert (dest / "backend").is_dir()
    assert recorded["src_path"] == f"https://github.com/{PIN.repo}.git"
    assert recorded["data"] == data
    assert recorded["kwargs"]["vcs_ref"] == PIN.commit
    assert recorded["kwargs"]["defaults"] is True
    assert recorded["kwargs"]["unsafe"] is True
    # The pin's exclude list must reach Copier: the pinned template ships
    # dangling .venv symlinks that crash Copier if not skipped.
    assert recorded["kwargs"]["exclude"] == PIN.exclude


def test_pin_without_exclude_passes_empty_exclude(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    recorded: dict[str, Any] = {}
    _install_fake_run_copy(monkeypatch, recorded)
    bare_pin = UpstreamPin(
        repo=PIN.repo, ref=PIN.ref, commit=PIN.commit, license=PIN.license
    )

    fetch_snapshot(bare_pin, tmp_path / "snapshot")

    assert recorded["kwargs"]["exclude"] == ()


def test_template_data_defaults_to_empty_dict(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    recorded: dict[str, Any] = {}
    _install_fake_run_copy(monkeypatch, recorded)

    fetch_snapshot(PIN, tmp_path / "snapshot")

    assert recorded["data"] == {}


def test_success_leaves_no_leaked_temp_dirs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, _isolated_tempdir: Path
) -> None:
    _install_fake_run_copy(monkeypatch, {})

    fetch_snapshot(PIN, tmp_path / "snapshot")

    assert list(_isolated_tempdir.iterdir()) == []


@pytest.mark.parametrize(
    "raised",
    [
        CopierError("template broke"),
        subprocess.CalledProcessError(returncode=128, cmd=["git", "clone"]),
        OSError("disk full"),
    ],
)
def test_copier_failure_maps_to_fetch_error_and_leaves_dest_untouched(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    _isolated_tempdir: Path,
    raised: Exception,
) -> None:
    def _failing_run_copy(*args: Any, **kwargs: Any) -> None:
        raise raised

    monkeypatch.setattr(copier, "run_copy", _failing_run_copy)
    dest = tmp_path / "snapshot"

    with pytest.raises(FetchError):
        fetch_snapshot(PIN, dest)

    assert not dest.exists()
    assert list(_isolated_tempdir.iterdir()) == []


def test_missing_git_fails_before_copier_runs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(snapshot_module.shutil, "which", lambda _name: None)

    def _must_not_run(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("copier.run_copy must not be called when git is missing")

    monkeypatch.setattr(copier, "run_copy", _must_not_run)

    with pytest.raises(FetchError, match="git"):
        fetch_snapshot(PIN, tmp_path / "snapshot")


def test_rejects_dest_that_is_a_file(tmp_path: Path) -> None:
    dest = tmp_path / "snapshot"
    dest.write_text("i am a file", encoding="utf-8")

    with pytest.raises(TargetDirectoryError):
        fetch_snapshot(PIN, dest)

    assert dest.read_text(encoding="utf-8") == "i am a file"


def test_rejects_non_empty_dest_dir(tmp_path: Path) -> None:
    dest = tmp_path / "snapshot"
    dest.mkdir()
    (dest / "existing.txt").write_text("keep me", encoding="utf-8")

    with pytest.raises(TargetDirectoryError):
        fetch_snapshot(PIN, dest)

    assert (dest / "existing.txt").read_text(encoding="utf-8") == "keep me"


def test_finalize_failure_maps_to_fetch_error_and_cleans_temp(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, _isolated_tempdir: Path
) -> None:
    _install_fake_run_copy(monkeypatch, {})

    def _failing_move(src: str, dst: str) -> None:
        raise OSError("cross-device chaos")

    monkeypatch.setattr(shutil, "move", _failing_move)
    dest = tmp_path / "snapshot"

    with pytest.raises(FetchError):
        fetch_snapshot(PIN, dest)

    assert not dest.exists()
    assert list(_isolated_tempdir.iterdir()) == []
