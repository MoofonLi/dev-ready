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
from dev_ready.stamp import Stamp, StampItem

__all__ = ["RecordedProject", "ResolvedRecordedItem"]

_RECORDED_ITEM_ALIASES = {"spec-loop": "mattpocock"}


@dataclass(frozen=True)
class ResolvedRecordedItem:
    """A stamped catalog item after current record-id aliases are applied."""

    id: str
    pin: str | None


@dataclass(frozen=True)
class RecordedProject:
    """A stamp resolved against the current catalog, plus what no longer exists."""

    selection: ProjectSelection
    removed_agent_targets: tuple[str, ...]
    recorded_development_loop: str
    recorded_skills_items: tuple[ResolvedRecordedItem, ...]
    recorded_mcp_items: tuple[ResolvedRecordedItem, ...]
    recorded_docs_items: tuple[ResolvedRecordedItem, ...]

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
    recorded_skills_items = _resolve_recorded_items(
        stamp.skills_items,
        resolve_aliases=True,
    )
    recorded_mcp_items = _resolve_recorded_items(stamp.mcp_items)
    recorded_docs_items = _resolve_recorded_items(stamp.docs_items)

    selected_skills = (
        frozenset(item.id for item in recorded_skills_items)
        & catalog.item_ids("skills")
    )
    if (
        adopt_default_development_loop
        and stamp.stamp_version < 5
        and catalog.default_development_loop
    ):
        selected_skills |= frozenset({catalog.default_development_loop})

    # Stamp version 5 is the first to record which documentation items were
    # chosen; earlier versions recorded only whether documentation was included.
    selected_docs_items = (
        frozenset(item.id for item in recorded_docs_items) & known_docs
        if stamp.stamp_version >= 5
        else (known_docs if stamp.docs_included else frozenset())
    )

    return RecordedProject(
        selection=ProjectSelection.from_recorded_items(
            catalog,
            skills=selected_skills,
            mcp=frozenset(item.id for item in recorded_mcp_items)
            & catalog.item_ids("mcp"),
            docs_items=selected_docs_items,
            agent_targets=frozenset(stamp.agent_targets) & catalog.agent_target_ids,
        ),
        removed_agent_targets=tuple(
            sorted(set(stamp.agent_targets) - catalog.agent_target_ids)
        ),
        recorded_development_loop=_resolve_recorded_id(stamp.development_loop),
        recorded_skills_items=recorded_skills_items,
        recorded_mcp_items=recorded_mcp_items,
        recorded_docs_items=recorded_docs_items,
    )


def _resolve_recorded_id(item_id: str) -> str:
    return _RECORDED_ITEM_ALIASES.get(item_id, item_id)


def _resolve_recorded_items(
    items: tuple[StampItem, ...],
    *,
    resolve_aliases: bool = False,
) -> tuple[ResolvedRecordedItem, ...]:
    return tuple(
        ResolvedRecordedItem(
            id=_resolve_recorded_id(item.id) if resolve_aliases else item.id,
            pin=item.pin,
        )
        for item in items
    )
