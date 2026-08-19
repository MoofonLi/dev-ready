"""Skill Link writer: native create and classify, no target following."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from dev_ready.skill_links import PathKind, classify_path, create_skill_link, has_link_component

WINDOWS = sys.platform == "win32"


def _canonical_skill(tmp_path: Path, name: str = "to-spec") -> Path:
    canonical = tmp_path / ".agents" / "skills" / name
    canonical.mkdir(parents=True)
    (canonical / "SKILL.md").write_text("# skill\n", encoding="utf-8")
    return canonical


def test_windows_createjunction_is_present() -> None:
    if not WINDOWS:
        pytest.skip("Windows junction API is not part of the POSIX branch")
    import _winapi

    assert hasattr(_winapi, "CreateJunction")


@pytest.mark.skipif(not WINDOWS, reason="native Windows junction branch")
def test_create_skill_link_writes_a_junction_to_the_absolute_canonical_dir(
    tmp_path: Path,
) -> None:
    canonical = _canonical_skill(tmp_path)
    link = tmp_path / ".claude" / "skills" / "to-spec"

    create_skill_link(link, canonical)

    assert link.is_junction()
    assert not link.is_symlink()
    assert (link / "SKILL.md").is_file()
    stored = os.readlink(link)
    assert Path(stored.removeprefix("\\\\?\\")) == canonical.resolve()


@pytest.mark.skipif(WINDOWS, reason="native POSIX symlink branch")
def test_create_skill_link_writes_a_relative_directory_symlink(tmp_path: Path) -> None:
    canonical = _canonical_skill(tmp_path)
    link = tmp_path / ".claude" / "skills" / "to-spec"

    create_skill_link(link, canonical)

    assert link.is_symlink()
    assert not link.is_junction()
    assert (link / "SKILL.md").is_file()
    assert os.readlink(link) == "../../.agents/skills/to-spec"


def test_classify_path_distinguishes_real_files_and_directories(tmp_path: Path) -> None:
    file_path = tmp_path / "README.md"
    file_path.write_text("hi\n", encoding="utf-8")
    directory = tmp_path / ".agents"
    directory.mkdir()

    assert classify_path(file_path) == PathKind.FILE
    assert classify_path(directory) == PathKind.DIRECTORY
    assert classify_path(tmp_path / "missing") == PathKind.ABSENT
    assert has_link_component(tmp_path, directory / "nested") is False


@pytest.mark.skipif(not WINDOWS, reason="native Windows junction branch")
def test_classify_path_names_live_and_broken_junctions_without_following(
    tmp_path: Path,
) -> None:
    canonical = _canonical_skill(tmp_path)
    live = tmp_path / ".claude" / "skills" / "live"
    broken = tmp_path / ".claude" / "skills" / "broken"
    gone = tmp_path / "gone"
    gone.mkdir()

    create_skill_link(live, canonical)
    create_skill_link(broken, gone)
    gone.rmdir()

    assert classify_path(live) == PathKind.JUNCTION
    assert classify_path(broken) == PathKind.JUNCTION
    assert not broken.exists()
    assert (canonical / "SKILL.md").read_text(encoding="utf-8") == "# skill\n"


@pytest.mark.skipif(WINDOWS, reason="native POSIX symlink branch")
def test_classify_path_names_live_and_broken_symlinks_without_following(
    tmp_path: Path,
) -> None:
    canonical = _canonical_skill(tmp_path)
    live = tmp_path / ".claude" / "skills" / "live"
    broken = tmp_path / ".claude" / "skills" / "broken"
    gone = tmp_path / "gone"
    gone.mkdir()

    create_skill_link(live, canonical)
    create_skill_link(broken, gone)
    gone.rmdir()

    assert classify_path(live) == PathKind.SYMBOLIC_LINK
    assert classify_path(broken) == PathKind.SYMBOLIC_LINK
    assert not broken.exists()
    assert (canonical / "SKILL.md").read_text(encoding="utf-8") == "# skill\n"
