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
    assert (dest / "README.md").exists()
