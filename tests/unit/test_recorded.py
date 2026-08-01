"""Stamp rehydration: one migration policy, two lifecycle views."""

from dev_ready.manifest import load_default_manifest
from dev_ready.recorded import RecordedProject
from dev_ready.stamp import InventoryEntry, Stamp, StampItem, UpstreamStampInfo

MANIFEST = load_default_manifest()
CATALOG = MANIFEST.components


def _stamp(
    *,
    version: int,
    skills: tuple[str, ...] = (),
    mcp: tuple[str, ...] = (),
    docs: tuple[str, ...] = (),
    docs_included: bool = True,
    agent_targets: tuple[str, ...] = ("claude",),
    development_loop: str = "",
) -> Stamp:
    return Stamp(
        stamp_version=version,
        dev_ready_version="0.9.0",
        skills_included=bool(skills),
        skills_items=tuple(StampItem(id=item_id) for item_id in skills),
        mcp_included=bool(mcp),
        mcp_items=tuple(StampItem(id=item_id) for item_id in mcp),
        docs_included=docs_included,
        docs_items=tuple(StampItem(id=item_id) for item_id in docs),
        handoff_included=False,
        agent_targets=agent_targets,
        upstream=UpstreamStampInfo(repo="fastapi/full-stack-fastapi-template", commit="a" * 40),
        project_name="my-app",
        development_loop=development_loop,
        inventory=(InventoryEntry(path="AGENTS.md", sha256="0" * 64),),
    )


def test_only_the_migrated_view_adopts_the_default_loop_for_a_pre_v5_stamp() -> None:
    stamp = _stamp(version=4, skills=())

    observed = RecordedProject.observed(stamp, MANIFEST)
    migrated = RecordedProject.migrated(stamp, MANIFEST)

    assert observed.selection.development_loop == ""
    assert migrated.selection.development_loop == CATALOG.default_development_loop
    assert CATALOG.default_development_loop in migrated.selection.skills


def test_a_v5_stamp_is_read_identically_by_both_views() -> None:
    loop = CATALOG.default_development_loop
    stamp = _stamp(version=5, skills=(loop,), development_loop=loop)

    observed = RecordedProject.observed(stamp, MANIFEST)
    migrated = RecordedProject.migrated(stamp, MANIFEST)

    assert observed.selection == migrated.selection


def test_a_pre_v5_stamp_falls_back_to_every_known_documentation_item() -> None:
    included = RecordedProject.observed(_stamp(version=4, docs_included=True), MANIFEST)
    declined = RecordedProject.observed(_stamp(version=4, docs_included=False), MANIFEST)

    assert included.selection.docs_items == CATALOG.item_ids("docs")
    assert declined.selection.docs_items == frozenset()


def test_a_v5_stamp_records_its_own_documentation_items() -> None:
    kept, *_ = sorted(CATALOG.item_ids("docs"))
    recorded = RecordedProject.observed(
        _stamp(version=5, docs=(kept,), development_loop=CATALOG.default_development_loop),
        MANIFEST,
    )

    assert recorded.selection.docs_items == frozenset({kept})
    assert recorded.selection.docs_items != CATALOG.item_ids("docs"), (
        "a v5 stamp must not fall back to the whole docs Component"
    )


def test_ids_the_current_catalog_no_longer_declares_are_dropped() -> None:
    recorded = RecordedProject.observed(
        _stamp(version=5, skills=("retired-skill",), mcp=("retired-mcp",)),
        MANIFEST,
    )

    assert recorded.selection.skills == frozenset()
    assert recorded.selection.mcp == frozenset()


def test_a_removed_agent_target_is_reported_rather_than_silently_dropped() -> None:
    recorded = RecordedProject.observed(
        _stamp(version=5, agent_targets=("claude", "long-gone")), MANIFEST
    )

    assert recorded.removed_agent_targets == ("long-gone",)
    assert "long-gone" not in recorded.selection.agent_targets
    assert "claude" in recorded.selection.agent_targets


def test_a_stamp_with_no_removals_reports_none() -> None:
    recorded = RecordedProject.observed(_stamp(version=5), MANIFEST)

    assert recorded.removed_agent_targets == ()
