"""Read a project stamp back as a selection over the current catalog.

`check` and `upgrade` both have to answer the same question — what did this
project select, expressed in ids the current catalog still knows? — and both
have to apply the same stamp-version migration rules to answer it. Those rules
live here once. The two commands differ only in what they do with what had to
be dropped: `check` reports it as drift, `upgrade` refuses to proceed.
"""

from __future__ import annotations

from dataclasses import dataclass

from dev_ready.manifest import Manifest
from dev_ready.prompts import ProjectSelection
from dev_ready.stamp import Stamp

__all__ = ["RecordedProject"]


@dataclass(frozen=True)
class RecordedProject:
    """A stamp resolved against the current catalog, plus what no longer exists."""

    selection: ProjectSelection
    removed_agent_targets: tuple[str, ...]

    @classmethod
    def observed(cls, stamp: Stamp, manifest: Manifest) -> RecordedProject:
        """Resolve the stamp exactly as recorded — the drift-inspection view.

        Nothing is added that the project does not already claim, so a project
        stamped before the loop was mandatory is not reported as missing it.
        """
        return _resolve(stamp, manifest, adopt_default_development_loop=False)

    @classmethod
    def migrated(cls, stamp: Stamp, manifest: Manifest) -> RecordedProject:
        """Resolve the stamp as the current layout — the re-application view.

        A project stamped before version 5 recorded no development loop, so
        carrying it forward means adopting the Default Set's (ADR-018).
        """
        return _resolve(stamp, manifest, adopt_default_development_loop=True)


def _resolve(
    stamp: Stamp,
    manifest: Manifest,
    *,
    adopt_default_development_loop: bool,
) -> RecordedProject:
    catalog = manifest.components
    known_docs = catalog.item_ids("docs")

    selected_skills = (
        frozenset(item.id for item in stamp.skills_items) & catalog.item_ids("skills")
    )
    if (
        adopt_default_development_loop
        and stamp.stamp_version < 5
        and catalog.default_development_loop
    ):
        selected_skills |= frozenset({catalog.default_development_loop})

    # Stamp version 5 is the first to record which documentation items were
    # chosen; earlier versions recorded only whether documentation was included.
    docs_items = (
        frozenset(item.id for item in stamp.docs_items) & known_docs
        if stamp.stamp_version >= 5
        else (known_docs if stamp.docs_included else frozenset())
    )

    return RecordedProject(
        selection=ProjectSelection.from_recorded_items(
            catalog,
            skills=selected_skills,
            mcp=frozenset(item.id for item in stamp.mcp_items) & catalog.item_ids("mcp"),
            docs_items=docs_items,
            agent_targets=frozenset(stamp.agent_targets) & catalog.agent_target_ids,
        ),
        removed_agent_targets=tuple(
            sorted(set(stamp.agent_targets) - catalog.agent_target_ids)
        ),
    )
