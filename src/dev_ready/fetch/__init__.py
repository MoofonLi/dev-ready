"""fetch: generate the upstream base via Copier at the manifest-pinned commit.

Only module allowed to make network calls (Copier's git clone happens here).
Knows nothing about overlay content. See docs/architecture.md (ADR-005).
"""

from dev_ready.fetch.snapshot import fetch_snapshot

__all__ = ["fetch_snapshot"]
