"""Integration test: one real download of the manifest-pinned upstream commit."""

from pathlib import Path

import pytest

from dev_ready.fetch import fetch_snapshot
from dev_ready.manifest import load_default_manifest

pytestmark = pytest.mark.network


def test_fetch_real_pinned_snapshot(tmp_path: Path) -> None:
    manifest = load_default_manifest()
    pin = manifest.upstream["base_template"]
    dest = tmp_path / "snapshot"

    result = fetch_snapshot(pin, dest)

    assert result == dest
    # Root README.md is in the manifest prune list since phase 2 (FR-8):
    # the snapshot must NOT contain it, while subdir READMEs survive.
    assert not (dest / "README.md").exists()
    assert (dest / "backend" / "README.md").exists()
