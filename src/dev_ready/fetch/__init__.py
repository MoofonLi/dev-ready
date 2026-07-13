"""fetch: download and verify the upstream snapshot at the manifest-pinned commit.

Only module allowed to make network calls. Knows nothing about overlay content.
See docs/architecture.md.
"""

from dev_ready.fetch.snapshot import fetch_snapshot

__all__ = ["fetch_snapshot"]
