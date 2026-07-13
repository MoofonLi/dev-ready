"""Placeholder so pytest collects successfully during bootstrap. Remove in Phase 1."""

from dev_ready import __version__


def test_package_imports() -> None:
    assert __version__
