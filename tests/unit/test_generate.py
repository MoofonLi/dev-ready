"""Unit tests for dev_ready.generate (no network; filesystem confined to tmp_path)."""

import tempfile
from pathlib import Path

import pytest

import dev_ready.generate as generate_module
from dev_ready.errors import FetchError, OverlayError, TargetDirectoryError, VerificationError
from dev_ready.generate import generate
from dev_ready.manifest import UpstreamPin
from dev_ready.prompts import Answers
from dev_ready.verify import REQUIRED_UPSTREAM_PATHS

PIN = UpstreamPin(
    repo="fastapi/full-stack-fastapi-template",
    ref="master",
    commit="4cd0d9e51aebd1af6f82d91ad0df4c9e41f4dea2",
    license="MIT",
)

_VERIFY_DIRECTORY_ENTRIES = {"backend", "frontend"}


@pytest.fixture(autouse=True)
def _isolated_tempdir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Force tempfile.mkdtemp() to land inside tmp_path so leak checks are deterministic."""
    temp_root = tmp_path / "_systmp"
    temp_root.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(temp_root))
    return temp_root


def _fake_fetch_ok(pin: UpstreamPin, dest: Path) -> Path:
    dest.mkdir(parents=True)
    (dest / "README.md").write_text("hello", encoding="utf-8")
    (dest / "backend").mkdir()
    (dest / "backend" / "main.py").write_text("print('hi')", encoding="utf-8")
    # Every path verify_project checks for must be present, or the happy-path
    # tests below would fail verification rather than exercising the thing
    # they're actually testing.
    for rel_path in REQUIRED_UPSTREAM_PATHS:
        path = dest / rel_path
        if rel_path in _VERIFY_DIRECTORY_ENTRIES:
            path.mkdir(exist_ok=True)
        elif not path.exists():
            path.write_text("stub", encoding="utf-8")
    return dest


def test_generate_happy_path_merges_upstream_and_overlay(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(generate_module, "fetch_snapshot", _fake_fetch_ok)

    target_dir = tmp_path / "my-app"
    answers = Answers(project_name="my-app", target_dir=target_dir)

    written = generate(answers, PIN)

    assert (target_dir / "README.md").read_text(encoding="utf-8") == "hello"
    assert (target_dir / "backend" / "main.py").exists()
    assert (target_dir / "CLAUDE.md").exists()
    assert (target_dir / ".mcp.json").exists()
    assert Path("CLAUDE.md") in written


def test_preflight_rejects_non_empty_target_dir_before_fetch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[Path] = []

    def _spy_fetch(pin: UpstreamPin, dest: Path) -> Path:
        calls.append(dest)
        return _fake_fetch_ok(pin, dest)

    monkeypatch.setattr(generate_module, "fetch_snapshot", _spy_fetch)

    target_dir = tmp_path / "my-app"
    target_dir.mkdir()
    (target_dir / "existing.txt").write_text("keep me", encoding="utf-8")

    with pytest.raises(TargetDirectoryError):
        generate(Answers(project_name="my-app", target_dir=target_dir), PIN)

    assert calls == []
    assert (target_dir / "existing.txt").read_text(encoding="utf-8") == "keep me"


def test_preflight_rejects_target_dir_that_is_a_file(tmp_path: Path) -> None:
    target_dir = tmp_path / "my-app"
    target_dir.write_text("i am a file", encoding="utf-8")

    with pytest.raises(TargetDirectoryError):
        generate(Answers(project_name="my-app", target_dir=target_dir), PIN)


def test_fetch_failure_leaves_target_untouched_and_no_leaked_temp_dirs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, _isolated_tempdir: Path
) -> None:
    def _failing_fetch(pin: UpstreamPin, dest: Path) -> Path:
        raise FetchError("simulated network failure")

    monkeypatch.setattr(generate_module, "fetch_snapshot", _failing_fetch)

    target_dir = tmp_path / "my-app"
    with pytest.raises(FetchError):
        generate(Answers(project_name="my-app", target_dir=target_dir), PIN)

    assert not target_dir.exists()
    assert list(_isolated_tempdir.iterdir()) == []


def test_overlay_failure_leaves_target_untouched_and_no_leaked_temp_dirs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, _isolated_tempdir: Path
) -> None:
    def _fetch_with_preexisting_claude_md(pin: UpstreamPin, dest: Path) -> Path:
        dest.mkdir(parents=True)
        # upstream already ships a CLAUDE.md -> overlay must collide and fail
        (dest / "CLAUDE.md").write_text("not ours", encoding="utf-8")
        return dest

    monkeypatch.setattr(generate_module, "fetch_snapshot", _fetch_with_preexisting_claude_md)

    target_dir = tmp_path / "my-app"
    with pytest.raises(OverlayError):
        generate(Answers(project_name="my-app", target_dir=target_dir), PIN)

    assert not target_dir.exists()
    assert list(_isolated_tempdir.iterdir()) == []


def test_success_leaves_no_leaked_temp_dirs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, _isolated_tempdir: Path
) -> None:
    monkeypatch.setattr(generate_module, "fetch_snapshot", _fake_fetch_ok)

    generate(Answers(project_name="my-app", target_dir=tmp_path / "my-app"), PIN)

    assert list(_isolated_tempdir.iterdir()) == []


def test_verification_failure_leaves_target_untouched_and_no_leaked_temp_dirs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, _isolated_tempdir: Path
) -> None:
    def _fetch_missing_frontend(pin: UpstreamPin, dest: Path) -> Path:
        # Upstream restructured and no longer ships a frontend/ directory ->
        # verify_project must catch it before anything reaches target_dir.
        dest.mkdir(parents=True)
        (dest / "backend").mkdir()
        return dest

    monkeypatch.setattr(generate_module, "fetch_snapshot", _fetch_missing_frontend)

    target_dir = tmp_path / "my-app"
    with pytest.raises(VerificationError):
        generate(Answers(project_name="my-app", target_dir=target_dir), PIN)

    assert not target_dir.exists()
    assert list(_isolated_tempdir.iterdir()) == []


def test_verify_runs_after_overlay_and_before_move(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    call_order: list[str] = []
    target_dir = tmp_path / "my-app"
    answers = Answers(project_name="my-app", target_dir=target_dir)

    def _spy_fetch(pin: UpstreamPin, dest: Path) -> Path:
        call_order.append("fetch")
        return _fake_fetch_ok(pin, dest)

    def _spy_overlay(passed_answers: Answers, project_dir: Path) -> list[Path]:
        call_order.append("overlay")
        return []

    def _spy_verify(project_dir: Path) -> None:
        call_order.append("verify")
        # verify must run before the staging dir is moved into target_dir
        assert not target_dir.exists()

    monkeypatch.setattr(generate_module, "fetch_snapshot", _spy_fetch)
    monkeypatch.setattr(generate_module, "apply_overlay", _spy_overlay)
    monkeypatch.setattr(generate_module, "verify_project", _spy_verify)

    generate(answers, PIN)

    assert call_order == ["fetch", "overlay", "verify"]
    assert target_dir.exists()
