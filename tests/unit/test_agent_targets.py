"""The Agent Target projection is the single owner of native-path layout."""

from pathlib import Path

from dev_ready.agent_targets import (
    TargetProjection,
    canonical_skill_names,
    project_targets,
)
from dev_ready.catalog_effects import parse_catalog_effect
from dev_ready.manifest import (
    AgentTarget,
    CatalogItem,
    ComponentCatalog,
    ItemPath,
    load_default_manifest,
)

CATALOG = load_default_manifest().components

_ALPHA = AgentTarget(
    id="alpha",
    description="Target with every native artifact.",
    skills_dir=".alpha/skills",
    rules_file="ALPHA.md",
    mcp_file=".alpha/mcp.json",
)
_BETA = AgentTarget(
    id="beta",
    description="Target with no rules or MCP file.",
    skills_dir=".beta/skills",
    rules_file=None,
    mcp_file=None,
)
_GAMMA = AgentTarget(
    id="gamma",
    description="Target sharing Alpha's skill directory.",
    skills_dir=".alpha/skills",
    rules_file="GAMMA.md",
    mcp_file=None,
)


def _catalog(*, mcp_items: tuple[CatalogItem, ...] = ()) -> ComponentCatalog:
    return ComponentCatalog(
        {"skills": (), "mcp": mcp_items, "docs": ()},
        {"alpha": _ALPHA, "beta": _BETA},
    )


def _mcp_item(item_id: str = "code-memory") -> CatalogItem:
    return CatalogItem(
        id=item_id,
        description=item_id,
        mode="pinned-dependency",
        license="MIT",
        category="token-optimize",
        paths=(ItemPath(src="mcp/mcp.json", dest=".mcp.json"),),
        pin="1.2.3",
        effect=parse_catalog_effect(
            {
                "kind": "mcp-server",
                "target": ".mcp.json",
                "package": "code-memory",
                "server_name": "code-memory",
                "command": "uvx",
            },
            mode="pinned-dependency",
            pin="1.2.3",
            location="test",
        ),
    )


def test_projection_keeps_catalog_order_and_drops_unselected_targets() -> None:
    projection = project_targets(_catalog(), {"beta"})

    assert [target.id for target in projection.skill_targets] == ["beta"]
    assert [
        target.id
        for target in project_targets(_catalog(), {"beta", "alpha"}).skill_targets
    ] == ["alpha", "beta"]


def test_projection_omits_targets_that_declare_no_rules_or_mcp_file() -> None:
    projection = project_targets(_catalog(), {"alpha", "beta"})

    assert projection.rules_files == ("ALPHA.md",)
    assert projection.mcp_files == (".alpha/mcp.json",)


def test_retarget_moves_both_paths_and_effect_onto_the_native_mcp_file() -> None:
    projection = project_targets(_catalog(), {"alpha", "beta"})

    retargeted = projection.retarget_mcp(_mcp_item())

    assert len(retargeted) == 1, "beta declares no MCP file and must be skipped"
    target, item = retargeted[0]
    assert target.id == "alpha"
    assert [path.dest for path in item.paths] == [".alpha/mcp.json"]
    assert item.effect is not None
    assert item.effect.target == ".alpha/mcp.json"
    assert [path.src for path in item.paths] == ["mcp/mcp.json"], "source is untouched"


def test_base_mcp_config_is_requested_only_when_a_selected_effect_needs_it() -> None:
    item = _mcp_item()
    catalog = _catalog(mcp_items=(item,))
    projection = project_targets(catalog, {"alpha", "beta"})

    assert projection.base_mcp_config_paths(catalog, {item.id}) == (
        Path(".alpha/mcp.json"),
    )
    assert projection.base_mcp_config_paths(catalog, frozenset()) == ()


def test_stub_path_places_the_pointer_under_the_targets_own_skills_dir() -> None:
    projection = project_targets(_catalog(), {"alpha"})

    assert projection.stub_path(_ALPHA, "mattpocock") == Path(
        ".alpha/skills/mattpocock/SKILL.md"
    )


def test_projection_yields_each_shared_skill_destination_once() -> None:
    catalog = ComponentCatalog(
        {"skills": (), "mcp": (), "docs": ()},
        {"alpha": _ALPHA, "gamma": _GAMMA, "beta": _BETA},
    )

    projection = project_targets(catalog, {"alpha", "gamma", "beta"})
    stub_paths = [
        projection.stub_path(target, "mattpocock") for target in projection.skill_targets
    ]

    assert stub_paths == [
        Path(".alpha/skills/mattpocock/SKILL.md"),
        Path(".beta/skills/mattpocock/SKILL.md"),
    ]
    assert projection.rules_files == ("ALPHA.md", "GAMMA.md")


def test_canonical_skill_names_reads_only_canonical_skill_destinations() -> None:
    catalog = ComponentCatalog(
        {
            "skills": (
                CatalogItem(
                    id="loop",
                    description="loop",
                    mode="builtin",
                    license="MIT",
                    paths=(
                        ItemPath(src="a", dest=".agents/skills/to-spec"),
                        ItemPath(src="b", dest="docs/agents/issue-tracker.md"),
                    ),
                ),
                CatalogItem(
                    id="unselected",
                    description="unselected",
                    mode="builtin",
                    license="MIT",
                    paths=(ItemPath(src="c", dest=".agents/skills/never"),),
                ),
            ),
            "mcp": (),
            "docs": (),
        },
        {},
    )

    assert canonical_skill_names(catalog, {"loop"}) == ("to-spec",)


def test_the_real_catalog_projects_a_stub_for_every_canonical_spec_loop_skill() -> None:
    projection = project_targets(CATALOG, CATALOG.agent_target_ids)
    names = canonical_skill_names(CATALOG, {"mattpocock"})

    assert "to-spec" in names
    for target in projection.skill_targets:
        assert projection.stub_path(target, "to-spec").parts[0] != ".agents", (
            "a Pointer Stub must never be written over Canonical Content"
        )


def test_newly_derived_targets_project_to_their_native_skill_directories() -> None:
    projection = project_targets(CATALOG, {"aider-desk", "astrbot", "openclaw"})

    assert {
        projection.stub_path(target, "to-spec").as_posix()
        for target in projection.skill_targets
    } == {
        ".aider-desk/skills/to-spec/SKILL.md",
        "data/skills/to-spec/SKILL.md",
        "skills/to-spec/SKILL.md",
    }


def test_an_empty_projection_answers_every_question_without_targets() -> None:
    projection = TargetProjection()

    assert projection.rules_files == ()
    assert projection.mcp_files == ()
    assert projection.retarget_mcp(_mcp_item()) == ()
