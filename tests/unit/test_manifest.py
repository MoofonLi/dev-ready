"""Unit tests for dev_ready.manifest."""

import json

import pytest

from dev_ready.errors import ManifestError
from dev_ready.manifest import (
    load_default_manifest,
    load_manifest,
    parse_manifest,
)

VALID = {
    "manifest_version": 1,
    "default_set": {
        "development_loop": "sample-skill",
        "enhancements": [],
    },
    "categories": {
        "dev": {
            "description": "Development methods for planning, implementation, and review."
        },
        "token-optimize": {
            "description": "Tools that reduce agent context use and improve codebase recall."
        },
    },
    "agent_targets": {
        "claude": {
            "description": "Claude Code native project configuration.",
            "skills_dir": ".claude/skills",
            "rules_file": "CLAUDE.md",
            "mcp_file": ".mcp.json",
        }
    },
    "upstream": {
        "base_template": {
            "repo": "fastapi/full-stack-fastapi-template",
            "ref": "master",
            "commit": "4cd0d9e51aebd1af6f82d91ad0df4c9e41f4dea2",
            "verified_at": "2026-07-04",
            "license": "MIT",
        }
    },
    "components": {
        "skills": {
            "items": [
                {
                    "id": "sample-skill",
                    "kind": "development-loop",
                    "steps": ["sample-step"],
                    "category": "dev",
                    "description": "Sample skill for manifest parsing.",
                    "mode": "builtin",
                    "license": "MIT",
                    "paths": [
                        {
                            "src": "claude/skills/sample-skill",
                            "dest": ".agents/skills/sample-skill",
                        }
                    ],
                }
            ]
        },
        "mcp": {
            "items": [
                {
                    "id": "mcp-config",
                    "category": "token-optimize",
                    "description": "Base .mcp.json MCP server configuration for the generated project.",
                    "mode": "builtin",
                    "license": "MIT",
                    "paths": [{"src": "mcp/mcp.json", "dest": ".mcp.json"}],
                }
            ]
        },
        "docs": {"items": []},
    },
    "overlay_version": "0.1.0",
}


def test_parse_valid_manifest() -> None:
    manifest = parse_manifest(json.dumps(VALID))
    assert manifest.manifest_version == 1
    assert manifest.overlay_version == "0.1.0"
    assert set(manifest.categories) == {"dev", "token-optimize"}
    assert manifest.categories["dev"].id == "dev"
    assert manifest.categories["dev"].description.startswith("Development methods")
    claude = manifest.agent_targets["claude"]
    assert claude.skills_dir == ".claude/skills"
    assert claude.rules_file == "CLAUDE.md"
    assert claude.mcp_file == ".mcp.json"
    pin = manifest.upstream["base_template"]
    assert pin.repo == "fastapi/full-stack-fastapi-template"
    assert pin.commit == "4cd0d9e51aebd1af6f82d91ad0df4c9e41f4dea2"
    assert pin.verified_at == "2026-07-04"
    assert pin.license == "MIT"
    assert len(manifest.components["skills"]) == 1
    skill = manifest.components["skills"][0]
    assert skill.id == "sample-skill"
    assert skill.category == "dev"
    assert skill.mode == "builtin"
    assert skill.license == "MIT"
    assert skill.paths[0].src == "claude/skills/sample-skill"
    assert skill.paths[0].dest == ".agents/skills/sample-skill"
    assert len(manifest.components["mcp"]) == 1
    mcp = manifest.components["mcp"][0]
    assert mcp.id == "mcp-config"
    assert mcp.category == "token-optimize"
    assert mcp.mode == "builtin"
    assert mcp.license == "MIT"
    assert mcp.paths[0].src == "mcp/mcp.json"
    assert mcp.paths[0].dest == ".mcp.json"


def test_catalog_item_display_name_falls_back_to_its_id() -> None:
    data = json.loads(json.dumps(VALID))

    fallback = parse_manifest(json.dumps(data)).components["skills"][0]
    assert fallback.display_name == "sample-skill"

    data["components"]["skills"]["items"][0]["title"] = "Sample Skill"
    titled = parse_manifest(json.dumps(data)).components["skills"][0]
    assert titled.title == "Sample Skill"
    assert titled.display_name == "Sample Skill"


def test_announced_flow_is_partitioned_out_of_every_selectable_catalog_view() -> None:
    data = json.loads(json.dumps(VALID))
    data["components"]["skills"]["items"].append(
        {
            "id": "future-flow",
            "kind": "development-loop",
            "category": "dev",
            "title": "Future Flow",
            "status": "coming-soon",
            "description": "An Engineering Flow that has been announced but not shipped.",
        }
    )

    catalog = parse_manifest(json.dumps(data)).components

    assert [(flow.id, flow.display_name, flow.status) for flow in catalog.announced_loops] == [
        ("future-flow", "Future Flow", "coming-soon")
    ]
    assert "future-flow" not in {item.id for item in catalog.all_items()}
    assert "future-flow" not in catalog.item_ids("skills")
    assert "future-flow" not in catalog.by_component({"future-flow"})["skills"]
    assert "future-flow" not in catalog.ids_in_category("dev")
    assert "future-flow" not in catalog.development_loop_ids


@pytest.mark.parametrize("status", [None, 42, "available-later"])
def test_announced_flow_status_has_exactly_one_legal_value(status: object) -> None:
    data = json.loads(json.dumps(VALID))
    data["components"]["skills"]["items"].append(
        {
            "id": "future-flow",
            "category": "dev",
            "status": status,
            "description": "A future Engineering Flow.",
        }
    )

    with pytest.raises(ManifestError, match="status.*coming-soon"):
        parse_manifest(json.dumps(data))


def test_announced_flow_cannot_declare_materialized_content() -> None:
    data = json.loads(json.dumps(VALID))
    data["components"]["skills"]["items"].append(
        {
            "id": "future-flow",
            "category": "dev",
            "status": "coming-soon",
            "description": "A future Engineering Flow.",
            "paths": [
                {
                    "src": "claude/skills/future-flow",
                    "dest": ".agents/skills/future-flow",
                }
            ],
        }
    )

    with pytest.raises(ManifestError, match="announced flow.*must not define.*paths"):
        parse_manifest(json.dumps(data))


def test_bundled_manifest_loads_with_two_announced_flows() -> None:
    catalog = load_default_manifest().components

    assert catalog.loops()[0].display_name == "Matt Pocock's skills"
    assert [flow.id for flow in catalog.announced_loops] == [
        "superpowers",
        "addyosmani",
    ]
    assert all("coming soon" not in flow.display_name.casefold() for flow in catalog.announced_loops)
    assert all(not any(char.isdigit() for char in flow.display_name) for flow in catalog.announced_loops)
    assert all(not flow.paths and not flow.steps and flow.effect is None for flow in catalog.announced_loops)


def test_catalog_item_requires_a_category() -> None:
    data = json.loads(json.dumps(VALID))
    del data["components"]["skills"]["items"][0]["category"]

    with pytest.raises(ManifestError, match="item 'sample-skill'.*category"):
        parse_manifest(json.dumps(data))

    data["components"]["skills"]["items"][0]["category"] = "dev"
    assert parse_manifest(json.dumps(data)).components["skills"][0].category == "dev"


def test_catalog_item_category_must_be_declared() -> None:
    data = json.loads(json.dumps(VALID))
    data["components"]["skills"]["items"][0]["category"] = "unknown"

    with pytest.raises(ManifestError, match="item 'sample-skill'.*unknown category"):
        parse_manifest(json.dumps(data))

    data["components"]["skills"]["items"][0]["category"] = "dev"
    assert parse_manifest(json.dumps(data)).components["skills"][0].category == "dev"


def test_declared_category_must_contain_an_item() -> None:
    data = json.loads(json.dumps(VALID))
    data["categories"]["security"] = {
        "description": "Tools for finding and reducing security risks."
    }

    with pytest.raises(ManifestError, match="category 'security'.*no catalog items"):
        parse_manifest(json.dumps(data))

    security_item = json.loads(
        json.dumps(data["components"]["skills"]["items"][0])
    )
    security_item["id"] = "security-item"
    security_item["kind"] = "enhancement"
    security_item.pop("steps")
    security_item["category"] = "security"
    data["components"]["skills"]["items"].append(security_item)
    assert "security" in parse_manifest(json.dumps(data)).categories


def test_dev_category_must_declare_a_development_loop() -> None:
    data = json.loads(json.dumps(VALID))
    del data["components"]["skills"]["items"][0]["kind"]
    del data["components"]["skills"]["items"][0]["steps"]

    with pytest.raises(ManifestError, match="Dev Category.*development loop"):
        parse_manifest(json.dumps(data))

    data["components"]["skills"]["items"][0]["kind"] = "development-loop"
    data["components"]["skills"]["items"][0]["steps"] = ["sample-step"]
    assert parse_manifest(json.dumps(data)).components["skills"][0].id == "sample-skill"


def test_second_development_loop_is_valid_manifest_data() -> None:
    data = json.loads(json.dumps(VALID))
    alternate = json.loads(json.dumps(data["components"]["skills"]["items"][0]))
    alternate["id"] = "alternate-loop"
    alternate["steps"] = ["alternate-step"]
    alternate["paths"][0]["dest"] = ".agents/skills/alternate-loop"
    data["components"]["skills"]["items"].append(alternate)

    manifest = parse_manifest(json.dumps(data))

    assert manifest.components.development_loop_ids == (
        "sample-skill",
        "alternate-loop",
    )
    assert manifest.default_set.development_loop == "sample-skill"


def test_enhancement_mount_is_parsed_as_a_development_loop_step() -> None:
    data = json.loads(json.dumps(VALID))
    data["components"]["mcp"]["items"][0]["mount"] = "sample-step"

    item = parse_manifest(json.dumps(data)).components["mcp"][0]

    assert item.mount == "sample-step"


@pytest.mark.parametrize("mount", [None, "", 42])
def test_declared_mount_must_be_a_non_empty_string(mount: object) -> None:
    data = json.loads(json.dumps(VALID))
    data["components"]["mcp"]["items"][0]["mount"] = mount

    with pytest.raises(ManifestError, match="item 'mcp-config'.*mount.*non-empty string"):
        parse_manifest(json.dumps(data))


def test_mount_must_name_a_step_of_the_development_loop() -> None:
    data = json.loads(json.dumps(VALID))
    data["components"]["mcp"]["items"][0]["mount"] = "unknown-step"

    with pytest.raises(ManifestError, match="mount 'unknown-step'.*every development loop"):
        parse_manifest(json.dumps(data))


def test_mount_must_name_a_step_shared_by_every_development_loop() -> None:
    data = json.loads(json.dumps(VALID))
    data["components"]["mcp"]["items"][0]["mount"] = "sample-step"
    alternate = json.loads(json.dumps(data["components"]["skills"]["items"][0]))
    alternate["id"] = "alternate-loop"
    alternate["steps"] = ["alternate-step"]
    alternate["paths"][0]["dest"] = ".agents/skills/alternate-loop"
    data["components"]["skills"]["items"].append(alternate)

    with pytest.raises(ManifestError, match="mount 'sample-step'.*every development loop"):
        parse_manifest(json.dumps(data))


def test_development_loop_cannot_declare_a_mount() -> None:
    data = json.loads(json.dumps(VALID))
    data["components"]["skills"]["items"][0]["mount"] = "sample-step"

    with pytest.raises(ManifestError, match="development loop 'sample-skill'.*mount"):
        parse_manifest(json.dumps(data))


def test_mounted_enhancement_must_declare_one_content_path() -> None:
    data = json.loads(json.dumps(VALID))
    item = data["components"]["mcp"]["items"][0]
    item["mount"] = "sample-step"
    item["mode"] = "pinned-dependency"
    item["pin"] = "1.2.3"
    item.pop("paths")
    item["inject"] = {
        "kind": "mcp-server",
        "target": ".mcp.json",
        "server_name": "sample",
        "command": "uvx",
        "package": "sample-package",
    }

    with pytest.raises(ManifestError, match="item 'mcp-config'.*mount.*exactly one path"):
        parse_manifest(json.dumps(data))


def test_mounted_enhancement_cannot_declare_two_content_paths() -> None:
    data = json.loads(json.dumps(VALID))
    item = data["components"]["mcp"]["items"][0]
    item["mount"] = "sample-step"
    item["paths"].append(
        {"src": "mcp/other.json", "dest": ".config/other.json"}
    )

    with pytest.raises(ManifestError, match="item 'mcp-config'.*mount.*exactly one path"):
        parse_manifest(json.dumps(data))


@pytest.mark.parametrize(
    "retired_id",
    ["spec-loop", "tdd", "diagnosing-bugs", "code-review", "setup-all"],
)
def test_retired_loop_catalog_ids_cannot_be_declared(retired_id: str) -> None:
    data = json.loads(json.dumps(VALID))
    _add_required_skill(data, item_id=retired_id)

    with pytest.raises(ManifestError, match=f"retired.*{retired_id}"):
        parse_manifest(json.dumps(data))

    data["components"]["skills"]["items"][-1]["id"] = "new-enhancement"
    assert parse_manifest(json.dumps(data)).components["skills"][-1].id == "new-enhancement"


def test_catalog_item_cannot_duplicate_a_development_loop_step() -> None:
    data = json.loads(json.dumps(VALID))
    data["components"]["skills"]["items"][0]["steps"] = ["unit-test"]
    _add_required_skill(data, item_id="unit-test")

    with pytest.raises(ManifestError, match="duplicates development loop step 'unit-test'"):
        parse_manifest(json.dumps(data))

    data["components"]["skills"]["items"][-1]["id"] = "new-enhancement"
    assert parse_manifest(json.dumps(data)).components["skills"][-1].id == "new-enhancement"


def test_default_set_cannot_exceed_its_declared_size_budget() -> None:
    data = json.loads(json.dumps(VALID))
    for item_id in ("first-extra", "second-extra", "third-extra"):
        _add_required_skill(data, item_id=item_id)
    data["default_set"]["enhancements"] = [
        "first-extra",
        "second-extra",
        "third-extra",
    ]

    with pytest.raises(
        ManifestError,
        match=r"Default Set size 4 exceeds limit 3.*DEFAULT_SET_SIZE_LIMIT",
    ):
        parse_manifest(json.dumps(data))

    data["default_set"]["enhancements"] = ["first-extra", "second-extra"]
    default_set = parse_manifest(json.dumps(data)).default_set
    assert default_set.development_loop == "sample-skill"
    assert default_set.enhancements == ("first-extra", "second-extra")
    assert not hasattr(default_set, "documentation")


def test_default_set_ignores_the_retired_documentation_field() -> None:
    data = json.loads(json.dumps(VALID))
    data["default_set"]["documentation"] = ["architecture", "requirements"]

    default_set = parse_manifest(json.dumps(data)).default_set

    assert default_set.development_loop == "sample-skill"
    assert default_set.enhancements == ()
    assert not hasattr(default_set, "documentation")


def test_default_manifest_declares_verified_claude_and_windsurf_targets() -> None:
    targets = load_default_manifest().agent_targets

    assert {"claude", "windsurf"} <= set(targets)
    assert targets["claude"].skills_dir == ".claude/skills"
    assert targets["claude"].rules_file == "CLAUDE.md"
    assert targets["claude"].mcp_file == ".mcp.json"
    assert targets["windsurf"].skills_dir == ".windsurf/skills"
    assert targets["windsurf"].rules_file is None
    assert targets["windsurf"].mcp_file is None
    assert all(target.description is None for target in targets.values())


def test_default_manifest_declares_the_derived_agent_partition() -> None:
    manifest = load_default_manifest()

    assert len(manifest.agent_targets) == 57
    assert len(manifest.standard_compliant_agents) == 19
    assert manifest.components.standard_compliant_agents == manifest.standard_compliant_agents
    assert all(
        target.skills_dir != ".agents/skills"
        for target in manifest.agent_targets.values()
    )
    assert manifest.agent_targets["aider-desk"].skills_dir == ".aider-desk/skills"
    assert manifest.agent_targets["astrbot"].skills_dir == "data/skills"
    assert manifest.agent_targets["openclaw"].skills_dir == "skills"
    assert {"codex", "cursor", "github-copilot", "zed"} <= set(
        manifest.standard_compliant_agents
    )


def test_reference_installer_provenance_is_pathless() -> None:
    pin = next(
        entry
        for entry in load_default_manifest().vendored
        if entry.repo == "vercel-labs/skills"
    )

    assert pin.commit == "1164afa5f0e21ebd01e6fc11249759353f494ad1"
    assert pin.license == "MIT"
    assert pin.paths == ()


def test_agent_target_description_is_optional_but_skills_directory_is_not() -> None:
    data = json.loads(json.dumps(VALID))
    data["agent_targets"]["claude"]["description"] = None

    target = parse_manifest(json.dumps(data)).agent_targets["claude"]

    assert target.description is None

    data["agent_targets"]["claude"].pop("description")
    assert parse_manifest(json.dumps(data)).agent_targets["claude"].description is None

    data["agent_targets"]["claude"].pop("skills_dir")
    with pytest.raises(ManifestError, match="agent target 'claude'.*skills_dir"):
        parse_manifest(json.dumps(data))


def test_default_manifest_declares_category_assignments() -> None:
    manifest = load_default_manifest()
    items = {
        item.id: item
        for component_items in manifest.components.values()
        for item in component_items
    }

    assert set(manifest.categories) == {
        "dev",
        "security",
        "quality",
        "design",
        "token-optimize",
    }
    assert items["mattpocock"].category == "dev"
    assert items["security-audit"].category == "security"
    assert items["react-doctor"].category == "quality"
    assert items["webapp-testing"].category == "quality"
    assert items["frontend-design"].category == "design"
    assert items["caveman"].category == "token-optimize"
    assert items["code-memory"].category == "token-optimize"


def test_default_manifest_declares_the_six_expected_mounts() -> None:
    items = {
        item.id: item
        for component_items in load_default_manifest().components.values()
        for item in component_items
    }

    assert {
        item_id: item.mount
        for item_id, item in items.items()
        if item.mount is not None
    } == {
        "design-linear": "implement",
        "design-stripe": "implement",
        "frontend-design": "implement",
        "react-doctor": "code-review",
        "security-audit": "code-review",
        "webapp-testing": "tdd",
    }
    assert items["caveman"].mount is None
    assert items["code-memory"].mount is None


@pytest.mark.parametrize("field", ["skills_dir", "rules_file", "mcp_file"])
def test_agent_target_paths_must_stay_inside_project(field: str) -> None:
    data = json.loads(json.dumps(VALID))
    data["agent_targets"]["claude"][field] = "../escape"

    with pytest.raises(ManifestError, match="agent target 'claude'.*relative path"):
        parse_manifest(json.dumps(data))


@pytest.mark.parametrize("field", ["skills_dir", "rules_file", "mcp_file"])
def test_agent_target_paths_reject_windows_drive_paths(field: str) -> None:
    data = json.loads(json.dumps(VALID))
    data["agent_targets"]["claude"][field] = "C:/outside"

    with pytest.raises(ManifestError, match="agent target 'claude'.*relative path"):
        parse_manifest(json.dumps(data))


def test_agent_target_record_must_be_an_object() -> None:
    data = json.loads(json.dumps(VALID))
    data["agent_targets"]["claude"] = "invalid"

    with pytest.raises(ManifestError, match="agent target 'claude' must be an object"):
        parse_manifest(json.dumps(data))


def test_manifest_requires_agent_target_policy() -> None:
    data = json.loads(json.dumps(VALID))
    data.pop("agent_targets")

    with pytest.raises(ManifestError, match="'agent_targets' must be a non-empty object"):
        parse_manifest(json.dumps(data))


def _add_required_skill(
    data: dict[str, object],
    *,
    item_id: str,
    requires: list[str] | None = None,
) -> None:
    components = data["components"]
    assert isinstance(components, dict)
    skills = components["skills"]
    assert isinstance(skills, dict)
    items = skills["items"]
    assert isinstance(items, list)
    item: dict[str, object] = {
        "id": item_id,
        "category": "dev",
        "description": f"{item_id} skill",
        "mode": "builtin",
        "license": "MIT",
        "paths": [{"src": f"claude/skills/{item_id}", "dest": f".claude/skills/{item_id}"}],
    }
    if requires is not None:
        item["requires"] = requires
    items.append(item)


def test_catalog_item_requirements_are_parsed_in_manifest_order() -> None:
    data = json.loads(json.dumps(VALID))
    _add_required_skill(data, item_id="unit-test")
    _add_required_skill(data, item_id="bundle", requires=["unit-test", "sample-skill"])

    manifest = parse_manifest(json.dumps(data))

    assert manifest.components["skills"][-1].requires == ("unit-test", "sample-skill")


@pytest.mark.parametrize(
    ("requires", "match"),
    [
        (["missing"], "unknown item"),
        (["bundle"], "cannot require itself"),
    ],
)
def test_catalog_item_requirements_reject_invalid_references(
    requires: list[str], match: str
) -> None:
    data = json.loads(json.dumps(VALID))
    _add_required_skill(data, item_id="bundle", requires=requires)

    with pytest.raises(ManifestError, match=match):
        parse_manifest(json.dumps(data))


def test_catalog_item_requirements_reject_cross_component_reference() -> None:
    data = json.loads(json.dumps(VALID))
    _add_required_skill(data, item_id="bundle", requires=["mcp-config"])

    with pytest.raises(ManifestError, match="same component"):
        parse_manifest(json.dumps(data))


def test_catalog_item_requirements_reject_cycles() -> None:
    data = json.loads(json.dumps(VALID))
    _add_required_skill(data, item_id="grill", requires=["bundle"])
    _add_required_skill(data, item_id="bundle", requires=["grill"])

    with pytest.raises(ManifestError, match="dependency cycle.*grill.*bundle"):
        parse_manifest(json.dumps(data))


def test_default_manifest_contains_complete_spec_loop_bundle() -> None:
    manifest = load_default_manifest()
    skills = {item.id: item for item in manifest.components["skills"]}

    assert len(skills) == 6
    assert "project-orientation" not in skills
    assert {"tdd", "diagnosing-bugs", "code-review", "setup-all"}.isdisjoint(skills)
    assert skills["mattpocock"].vendored_repo == "mattpocock/skills"
    assert {path.dest for path in skills["mattpocock"].paths} == {
        ".agents/skills/tdd",
        ".agents/skills/diagnosing-bugs",
        ".agents/skills/code-review",
        ".agents/skills/grill-with-docs",
        ".agents/skills/grilling",
        ".agents/skills/domain-modeling",
        ".agents/skills/to-spec",
        ".agents/skills/to-tickets",
        ".agents/skills/implement",
        ".agents/skills/improve-codebase-architecture",
        ".agents/skills/codebase-design",
        ".agents/skills/setup-matt-pocock-skills",
        "docs/agents",
    }

    mattpocock = next(pin for pin in manifest.vendored if pin.repo == "mattpocock/skills")
    assert mattpocock.commit == "ed37663cc5fbef691ddfecd080dff42f7e7e350d"
    assert {path.src for path in mattpocock.paths} >= {
        "skills/engineering/grill-with-docs",
        "skills/productivity/grilling",
        "skills/engineering/domain-modeling",
        "skills/engineering/to-spec",
        "skills/engineering/to-tickets",
        "skills/engineering/implement",
        "skills/engineering/improve-codebase-architecture",
        "skills/engineering/codebase-design",
    }


def test_setup_skill_is_owned_by_the_mandatory_development_loop() -> None:
    manifest = load_default_manifest()
    loop = next(item for item in manifest.components["skills"] if item.id == "mattpocock")

    assert "setup-all" not in manifest.components.item_ids("skills")
    assert "setup-matt-pocock-skills" in loop.steps
    assert ".agents/skills/setup-matt-pocock-skills" in {
        path.dest for path in loop.paths
    }



def test_verified_at_may_be_null() -> None:
    data = json.loads(json.dumps(VALID))
    data["upstream"]["base_template"]["verified_at"] = None
    pin = parse_manifest(json.dumps(data)).upstream["base_template"]
    assert pin.verified_at is None


def test_load_manifest_from_path(tmp_path) -> None:
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(VALID), encoding="utf-8")
    manifest = load_manifest(path)
    assert "base_template" in manifest.upstream


def test_load_manifest_missing_file(tmp_path) -> None:
    with pytest.raises(ManifestError, match="cannot read manifest"):
        load_manifest(tmp_path / "nope.json")


def test_invalid_json() -> None:
    with pytest.raises(ManifestError, match="not valid JSON"):
        parse_manifest("{not json")


def test_top_level_must_be_object() -> None:
    with pytest.raises(ManifestError, match="top level"):
        parse_manifest("[1, 2]")


def test_unsupported_version() -> None:
    data = json.loads(json.dumps(VALID))
    data["manifest_version"] = 99
    with pytest.raises(ManifestError, match="unsupported manifest_version"):
        parse_manifest(json.dumps(data))


@pytest.mark.parametrize("field", ["repo", "ref", "commit", "license"])
def test_missing_pin_field(field: str) -> None:
    data = json.loads(json.dumps(VALID))
    del data["upstream"]["base_template"][field]
    with pytest.raises(ManifestError, match=f"field '{field}'"):
        parse_manifest(json.dumps(data))


@pytest.mark.parametrize(
    "commit",
    [
        "abc123",  # too short
        "4CD0D9E51AEBD1AF6F82D91AD0DF4C9E41F4DEA2",  # uppercase
        "master",  # a ref, not a sha
        "4cd0d9e51aebd1af6f82d91ad0df4c9e41f4dea2x",  # too long
    ],
)
def test_commit_must_be_full_lowercase_sha(commit: str) -> None:
    data = json.loads(json.dumps(VALID))
    data["upstream"]["base_template"]["commit"] = commit
    with pytest.raises(ManifestError, match="40-character lowercase"):
        parse_manifest(json.dumps(data))


def test_repo_must_be_owner_slash_name() -> None:
    data = json.loads(json.dumps(VALID))
    data["upstream"]["base_template"]["repo"] = "https://github.com/x/y"
    with pytest.raises(ManifestError, match="owner/name"):
        parse_manifest(json.dumps(data))


@pytest.mark.parametrize(
    "bad_repo",
    [
        "..x/y",  # owner segment starting with '.' (traversal-shaped)
        "x/..y",  # name segment starting with '.'
        ".hidden/y",  # leading dot owner
        "-x/y",  # owner cannot start with a hyphen
        "x/-y",  # name cannot start with a hyphen
        "owner//name",  # empty segment
        "owner/name/extra",  # more than one path segment
    ],
)
def test_repo_rejects_traversal_shaped_values(bad_repo: str) -> None:
    # The URL fetch builds is https://github.com/<repo>.git; each side must
    # start with an alphanumeric so no segment can begin with '.' or '-'.
    data = json.loads(json.dumps(VALID))
    data["upstream"]["base_template"]["repo"] = bad_repo
    with pytest.raises(ManifestError, match="owner/name"):
        parse_manifest(json.dumps(data))


def test_repo_accepts_dots_and_underscores_in_name() -> None:
    # GitHub repo names may contain '.' and '_' (just not as the first char).
    data = json.loads(json.dumps(VALID))
    data["upstream"]["base_template"]["repo"] = "octo-org/my_repo.name"
    assert parse_manifest(json.dumps(data)).upstream["base_template"].repo == "octo-org/my_repo.name"


def test_empty_upstream_rejected() -> None:
    data = json.loads(json.dumps(VALID))
    data["upstream"] = {}
    with pytest.raises(ManifestError, match="non-empty"):
        parse_manifest(json.dumps(data))


def test_exclude_defaults_to_empty_tuple() -> None:
    manifest = parse_manifest(json.dumps(VALID))
    assert manifest.upstream["base_template"].exclude == ()


def test_exclude_parsed_as_tuple_of_patterns() -> None:
    data = json.loads(json.dumps(VALID))
    data["upstream"]["base_template"]["exclude"] = [".agents/skills/fastapi", "docs/junk.md"]
    pin = parse_manifest(json.dumps(data)).upstream["base_template"]
    assert pin.exclude == (".agents/skills/fastapi", "docs/junk.md")


def test_exclude_must_be_a_list() -> None:
    data = json.loads(json.dumps(VALID))
    data["upstream"]["base_template"]["exclude"] = ".agents"
    with pytest.raises(ManifestError, match="must be a list"):
        parse_manifest(json.dumps(data))


@pytest.mark.parametrize("bad_entry", ["", 42, None])
def test_exclude_entries_must_be_non_empty_strings(bad_entry: object) -> None:
    data = json.loads(json.dumps(VALID))
    data["upstream"]["base_template"]["exclude"] = [bad_entry]
    with pytest.raises(ManifestError, match="non-empty strings"):
        parse_manifest(json.dumps(data))


@pytest.mark.parametrize("bad_entry", ["//etc/passwd", "\\windows", "../outside", "a/../b"])
def test_exclude_entries_must_be_relative_without_traversal(bad_entry: str) -> None:
    data = json.loads(json.dumps(VALID))
    data["upstream"]["base_template"]["exclude"] = [bad_entry]
    with pytest.raises(ManifestError, match="relative"):
        parse_manifest(json.dumps(data))


def test_prune_defaults_to_empty_tuple() -> None:
    manifest = parse_manifest(json.dumps(VALID))
    assert manifest.upstream["base_template"].prune == ()


def test_prune_parsed_as_tuple_of_patterns() -> None:
    data = json.loads(json.dumps(VALID))
    data["upstream"]["base_template"]["prune"] = ["docs/junk.md"]
    pin = parse_manifest(json.dumps(data)).upstream["base_template"]
    assert pin.prune == ("docs/junk.md",)


def test_prune_must_be_a_list() -> None:
    data = json.loads(json.dumps(VALID))
    data["upstream"]["base_template"]["prune"] = ".agents"
    with pytest.raises(ManifestError, match="must be a list"):
        parse_manifest(json.dumps(data))


@pytest.mark.parametrize("bad_entry", ["", 42, None])
def test_prune_entries_must_be_non_empty_strings(bad_entry: object) -> None:
    data = json.loads(json.dumps(VALID))
    data["upstream"]["base_template"]["prune"] = [bad_entry]
    with pytest.raises(ManifestError, match="non-empty strings"):
        parse_manifest(json.dumps(data))


@pytest.mark.parametrize("bad_entry", ["//etc/passwd", "\\windows", "../outside", "a/../b"])
def test_prune_entries_must_be_relative_without_traversal(bad_entry: str) -> None:
    data = json.loads(json.dumps(VALID))
    data["upstream"]["base_template"]["prune"] = [bad_entry]
    with pytest.raises(ManifestError, match="relative"):
        parse_manifest(json.dumps(data))


@pytest.mark.parametrize("field", ["exclude", "prune"])
def test_path_list_accepts_single_leading_slash_root_anchor(field: str) -> None:
    data = json.loads(json.dumps(VALID))
    data["upstream"]["base_template"][field] = ["/README.md"]
    pin = parse_manifest(json.dumps(data)).upstream["base_template"]
    assert getattr(pin, field) == ("/README.md",)  # stored verbatim, anchor kept


def test_bundled_manifest_is_valid() -> None:
    manifest = load_default_manifest()
    assert "base_template" in manifest.upstream
    # The pinned FastAPI template ships dangling .venv symlinks that Copier
    # would otherwise follow and crash on (see UpstreamPin.exclude docstring).
    assert manifest.upstream["base_template"].exclude != ()
    assert manifest.upstream["base_template"].prune != ()
    assert ".github/workflows/test-backend.yml" not in manifest.upstream["base_template"].prune


@pytest.mark.parametrize(
    "workflow",
    [".github/workflows/deploy-production.yml", ".github/workflows/deploy-staging.yml"],
)
def test_deployment_workflows_are_not_pruned(workflow: str) -> None:
    """FR-38: upstream wrote both for downstream users, and `deployment.md` teaches them."""
    pin = load_default_manifest().upstream["base_template"]
    assert workflow not in pin.prune
    assert workflow not in pin.exclude


def test_root_ignore_file_is_pruned_and_root_anchored() -> None:
    """FR-38: dev-ready replaces the root ignore file; `backend/` and `frontend/` keep theirs."""
    pin = load_default_manifest().upstream["base_template"]
    assert "/.gitignore" in pin.prune
    assert ".gitignore" not in pin.prune


def test_repository_maintenance_workflows_stay_pruned() -> None:
    pin = load_default_manifest().upstream["base_template"]
    assert {
        ".github/workflows/issue-manager.yml",
        ".github/workflows/labeler.yml",
        ".github/workflows/add-to-project.yml",
        ".github/workflows/latest-changes.yml",
        ".github/workflows/smokeshow.yml",
        ".github/workflows/detect-conflicts.yml",
        ".github/workflows/zizmor.yml",
        ".github/workflows/guard-dependencies.yml",
    } <= set(pin.prune)


def test_missing_components_rejected() -> None:
    data = json.loads(json.dumps(VALID))
    del data["components"]
    with pytest.raises(ManifestError, match="'components' must be an object"):
        parse_manifest(json.dumps(data))


def test_unknown_component_key_rejected() -> None:
    data = json.loads(json.dumps(VALID))
    data["components"]["unknown"] = {"items": []}
    with pytest.raises(ManifestError, match="unknown component key"):
        parse_manifest(json.dumps(data))


def test_missing_required_component_rejected() -> None:
    data = json.loads(json.dumps(VALID))
    del data["components"]["mcp"]
    with pytest.raises(ManifestError, match="missing required component"):
        parse_manifest(json.dumps(data))


@pytest.mark.parametrize("bad_id", ["UPPERCASE", "-leading", "has,comma", "has space", ""])
def test_bad_item_id_rejected(bad_id: str) -> None:
    data = json.loads(json.dumps(VALID))
    data["components"]["skills"]["items"][0]["id"] = bad_id
    with pytest.raises(ManifestError, match="must match pattern"):
        parse_manifest(json.dumps(data))


def test_duplicate_item_id_rejected() -> None:
    data = json.loads(json.dumps(VALID))
    item = data["components"]["skills"]["items"][0]
    data["components"]["skills"]["items"].append(item)
    with pytest.raises(ManifestError, match="duplicate item id"):
        parse_manifest(json.dumps(data))


def test_empty_description_rejected() -> None:
    data = json.loads(json.dumps(VALID))
    data["components"]["skills"]["items"][0]["description"] = ""
    with pytest.raises(ManifestError, match="description"):
        parse_manifest(json.dumps(data))


def test_invalid_mode_rejected() -> None:
    data = json.loads(json.dumps(VALID))
    data["components"]["skills"]["items"][0]["mode"] = "unknown-mode"
    with pytest.raises(ManifestError, match="mode"):
        parse_manifest(json.dumps(data))


def test_empty_license_rejected() -> None:
    data = json.loads(json.dumps(VALID))
    data["components"]["skills"]["items"][0]["license"] = ""
    with pytest.raises(ManifestError, match="license"):
        parse_manifest(json.dumps(data))


def test_empty_paths_rejected() -> None:
    data = json.loads(json.dumps(VALID))
    data["components"]["skills"]["items"][0]["paths"] = []
    with pytest.raises(ManifestError, match="paths"):
        parse_manifest(json.dumps(data))


@pytest.mark.parametrize("bad_path", ["/abs/path", "\\win\\path", "with\\backslash", "../outside", "a/../b", ""])
def test_invalid_item_path_rejected(bad_path: str) -> None:
    data = json.loads(json.dumps(VALID))
    data["components"]["skills"]["items"][0]["paths"][0]["src"] = bad_path
    with pytest.raises(ManifestError, match=r"relative path|non-empty string"):
        parse_manifest(json.dumps(data))


def test_valid_pinned_dependency_mcp_server() -> None:
    data = json.loads(json.dumps(VALID))
    data["components"]["mcp"]["items"].append({
        "id": "code-memory",
        "category": "token-optimize",
        "description": "Codebase memory server",
        "mode": "pinned-dependency",
        "license": "MIT",
        "pin": "0.9.0",
        "inject": {
            "kind": "mcp-server",
            "target": ".mcp.json",
            "server_name": "codebase-memory",
            "command": "uvx",
            "package": "codebase-memory-mcp",
        },
    })
    manifest = parse_manifest(json.dumps(data))
    item = manifest.components["mcp"][1]
    assert item.id == "code-memory"
    assert item.mode == "pinned-dependency"
    assert item.pin == "0.9.0"
    assert item.paths == ()
    assert item.effect is not None
    assert item.effect.target == ".mcp.json"


def test_valid_pinned_dependency_npm_dev_dependency() -> None:
    data = json.loads(json.dumps(VALID))
    data["components"]["skills"]["items"].append({
        "id": "react-doctor",
        "category": "dev",
        "description": "React doctor skill",
        "mode": "pinned-dependency",
        "license": "MIT",
        "pin": "0.8.1",
        "paths": [{"src": "claude/skills/react-doctor", "dest": ".claude/skills/react-doctor"}],
        "inject": {
            "kind": "npm-dev-dependency",
            "target": "frontend/package.json",
            "package": "react-doctor",
            "scripts": {"doctor": "react-doctor"},
        },
    })
    manifest = parse_manifest(json.dumps(data))
    item = manifest.components["skills"][1]
    assert item.id == "react-doctor"
    assert item.pin == "0.8.1"
    assert item.effect is not None
    assert item.effect.target == "frontend/package.json"


@pytest.mark.parametrize("bad_pin", ["", "latest", "^1.2.3", "1.2", "1.2.3 "])
def test_malformed_pin_rejected(bad_pin: str) -> None:
    data = json.loads(json.dumps(VALID))
    data["components"]["mcp"]["items"].append({
        "id": "code-memory",
        "category": "token-optimize",
        "description": "Codebase memory server",
        "mode": "pinned-dependency",
        "license": "MIT",
        "pin": bad_pin,
        "inject": {
            "kind": "mcp-server",
            "target": ".mcp.json",
            "server_name": "codebase-memory",
            "command": "uvx",
            "package": "codebase-memory-mcp",
        },
    })
    with pytest.raises(ManifestError, match="pin"):
        parse_manifest(json.dumps(data))


def test_pinned_dependency_without_pin_rejected() -> None:
    data = json.loads(json.dumps(VALID))
    data["components"]["mcp"]["items"].append({
        "id": "code-memory",
        "category": "token-optimize",
        "description": "Codebase memory server",
        "mode": "pinned-dependency",
        "license": "MIT",
        "inject": {
            "kind": "mcp-server",
            "target": ".mcp.json",
            "server_name": "codebase-memory",
            "command": "uvx",
            "package": "codebase-memory-mcp",
        },
    })
    with pytest.raises(ManifestError, match="pin"):
        parse_manifest(json.dumps(data))


def test_pin_on_builtin_item_rejected() -> None:
    data = json.loads(json.dumps(VALID))
    data["components"]["skills"]["items"][0]["pin"] = "1.0.0"
    with pytest.raises(ManifestError, match="is only allowed for pinned-dependency"):
        parse_manifest(json.dumps(data))


def test_inject_on_builtin_item_rejected() -> None:
    data = json.loads(json.dumps(VALID))
    data["components"]["skills"]["items"][0]["inject"] = {
        "kind": "mcp-server",
        "target": ".mcp.json",
        "server_name": "foo",
        "command": "bar",
        "package": "baz",
    }
    with pytest.raises(ManifestError, match="inject.*only allowed for pinned-dependency"):
        parse_manifest(json.dumps(data))


def test_unknown_inject_kind_rejected() -> None:
    data = json.loads(json.dumps(VALID))
    data["components"]["mcp"]["items"].append({
        "id": "code-memory",
        "category": "token-optimize",
        "description": "Codebase memory server",
        "mode": "pinned-dependency",
        "license": "MIT",
        "pin": "0.9.0",
        "inject": {
            "kind": "unknown-kind",
            "target": ".mcp.json",
            "package": "pkg",
        },
    })
    with pytest.raises(ManifestError, match="inject field 'kind'"):
        parse_manifest(json.dumps(data))


def test_mcp_server_missing_server_name_rejected() -> None:
    data = json.loads(json.dumps(VALID))
    data["components"]["mcp"]["items"].append({
        "id": "code-memory",
        "category": "token-optimize",
        "description": "Codebase memory server",
        "mode": "pinned-dependency",
        "license": "MIT",
        "pin": "0.9.0",
        "inject": {
            "kind": "mcp-server",
            "target": ".mcp.json",
            "command": "uvx",
            "package": "codebase-memory-mcp",
        },
    })
    with pytest.raises(ManifestError, match="server_name"):
        parse_manifest(json.dumps(data))


def test_npm_dev_dependency_missing_scripts_rejected() -> None:
    data = json.loads(json.dumps(VALID))
    data["components"]["skills"]["items"].append({
        "id": "react-doctor",
        "category": "dev",
        "description": "React doctor skill",
        "mode": "pinned-dependency",
        "license": "MIT",
        "pin": "0.8.1",
        "paths": [{"src": "claude/skills/react-doctor", "dest": ".claude/skills/react-doctor"}],
        "inject": {
            "kind": "npm-dev-dependency",
            "target": "frontend/package.json",
            "package": "react-doctor",
        },
    })
    with pytest.raises(ManifestError, match="scripts"):
        parse_manifest(json.dumps(data))


def test_inject_target_traversal_rejected() -> None:
    data = json.loads(json.dumps(VALID))
    data["components"]["mcp"]["items"].append({
        "id": "code-memory",
        "category": "token-optimize",
        "description": "Codebase memory server",
        "mode": "pinned-dependency",
        "license": "MIT",
        "pin": "0.9.0",
        "inject": {
            "kind": "mcp-server",
            "target": "../outside.json",
            "server_name": "codebase-memory",
            "command": "uvx",
            "package": "codebase-memory-mcp",
        },
    })
    with pytest.raises(ManifestError, match="target"):
        parse_manifest(json.dumps(data))


def test_item_with_neither_paths_nor_inject_rejected() -> None:
    data = json.loads(json.dumps(VALID))
    data["components"]["mcp"]["items"].append({
        "id": "empty-item",
        "category": "token-optimize",
        "description": "Empty item",
        "mode": "pinned-dependency",
        "license": "MIT",
        "pin": "1.0.0",
    })
    with pytest.raises(ManifestError, match="must define paths, inject, or both"):
        parse_manifest(json.dumps(data))


def test_default_catalog_excludes_mcp_infrastructure() -> None:
    manifest = load_default_manifest()
    mcp_items = {item.id: item for item in manifest.components["mcp"]}
    assert "code-memory" in mcp_items
    assert mcp_items["code-memory"].pin == "0.9.0"
    assert "mcp-config" not in mcp_items
    docs_items = {item.id: item for item in manifest.components["docs"]}
    assert set(docs_items) == {"design-stripe", "design-linear"}
    assert docs_items["design-stripe"].category == "design"
    assert docs_items["design-stripe"].paths[0].dest == "docs/design-stripe.md"
    assert docs_items["design-linear"].category == "design"
    assert docs_items["design-linear"].paths[0].dest == "docs/design-linear.md"
    skills_items = {item.id: item for item in manifest.components["skills"]}
    assert "react-doctor" in skills_items
    assert skills_items["react-doctor"].pin == "0.8.1"
    assert skills_items["react-doctor"].effect is not None
    assert skills_items["react-doctor"].effect.target == "frontend/package.json"


VALID_VENDORED_ENTRY = {
    "repo": "JuliusBrussee/caveman",
    "commit": "a" * 40,
    "license": "MIT",
    "paths": [{"src": "SKILL.md", "dest": "templates/claude/skills/caveman/SKILL.md"}],
}


def test_parse_manifest_with_empty_vendored_list() -> None:
    data = json.loads(json.dumps(VALID))
    data["vendored"] = []
    manifest = parse_manifest(json.dumps(data))
    assert manifest.vendored == ()


def test_parse_manifest_with_absent_vendored_key() -> None:
    data = json.loads(json.dumps(VALID))
    data.pop("vendored", None)
    manifest = parse_manifest(json.dumps(data))
    assert manifest.vendored == ()


def test_parse_manifest_with_valid_vendored_entry() -> None:
    data = json.loads(json.dumps(VALID))
    data["vendored"] = [VALID_VENDORED_ENTRY]
    manifest = parse_manifest(json.dumps(data))
    assert len(manifest.vendored) == 1
    v = manifest.vendored[0]
    assert v.repo == "JuliusBrussee/caveman"
    assert v.commit == "a" * 40
    assert v.license == "MIT"
    assert len(v.paths) == 1
    assert v.paths[0].src == "SKILL.md"
    assert v.paths[0].dest == "templates/claude/skills/caveman/SKILL.md"


def test_vendored_39hex_commit_rejected() -> None:
    data = json.loads(json.dumps(VALID))
    bad_entry = json.loads(json.dumps(VALID_VENDORED_ENTRY))
    bad_entry["commit"] = "a" * 39
    data["vendored"] = [bad_entry]
    with pytest.raises(ManifestError, match="commit"):
        parse_manifest(json.dumps(data))


def test_vendored_uppercase_commit_rejected() -> None:
    data = json.loads(json.dumps(VALID))
    bad_entry = json.loads(json.dumps(VALID_VENDORED_ENTRY))
    bad_entry["commit"] = "A" * 40
    data["vendored"] = [bad_entry]
    with pytest.raises(ManifestError, match="commit"):
        parse_manifest(json.dumps(data))


def test_vendored_bad_repo_shape_rejected() -> None:
    data = json.loads(json.dumps(VALID))
    bad_entry = json.loads(json.dumps(VALID_VENDORED_ENTRY))
    bad_entry["repo"] = "not-a-repo"
    data["vendored"] = [bad_entry]
    with pytest.raises(ManifestError, match="repo"):
        parse_manifest(json.dumps(data))


def test_vendored_dotdot_path_rejected() -> None:
    data = json.loads(json.dumps(VALID))
    bad_entry = json.loads(json.dumps(VALID_VENDORED_ENTRY))
    bad_entry["paths"] = [{"src": "../outside", "dest": "templates/foo"}]
    data["vendored"] = [bad_entry]
    with pytest.raises(ManifestError, match=r"relative path without '\.\.'"):
        parse_manifest(json.dumps(data))


def test_vendored_leading_slash_path_rejected() -> None:
    data = json.loads(json.dumps(VALID))
    bad_entry = json.loads(json.dumps(VALID_VENDORED_ENTRY))
    bad_entry["paths"] = [{"src": "/README.md", "dest": "templates/foo"}]
    data["vendored"] = [bad_entry]
    with pytest.raises(ManifestError, match=r"relative path without '\.\.'"):
        parse_manifest(json.dumps(data))


def test_vendored_empty_license_rejected() -> None:
    data = json.loads(json.dumps(VALID))
    bad_entry = json.loads(json.dumps(VALID_VENDORED_ENTRY))
    bad_entry["license"] = ""
    data["vendored"] = [bad_entry]
    with pytest.raises(ManifestError, match="license"):
        parse_manifest(json.dumps(data))


def test_vendored_duplicate_repo_commit_rejected() -> None:
    data = json.loads(json.dumps(VALID))
    data["vendored"] = [VALID_VENDORED_ENTRY, VALID_VENDORED_ENTRY]
    with pytest.raises(ManifestError, match="duplicate"):
        parse_manifest(json.dumps(data))


def test_vendor_mode_item_without_vendored_repo_rejected() -> None:
    data = json.loads(json.dumps(VALID))
    data["vendored"] = [VALID_VENDORED_ENTRY]
    data["components"]["skills"]["items"].append({
        "id": "caveman",
        "category": "dev",
        "description": "Caveman skill",
        "mode": "vendor",
        "license": "MIT",
        "paths": [{"src": "SKILL.md", "dest": "templates/claude/skills/caveman/SKILL.md"}],
    })
    with pytest.raises(ManifestError, match="vendored_repo"):
        parse_manifest(json.dumps(data))


def test_vendor_mode_item_dangling_vendored_repo_rejected() -> None:
    data = json.loads(json.dumps(VALID))
    data["vendored"] = [VALID_VENDORED_ENTRY]
    data["components"]["skills"]["items"].append({
        "id": "caveman",
        "category": "dev",
        "description": "Caveman skill",
        "mode": "vendor",
        "license": "MIT",
        "vendored_repo": "other/repo",
        "paths": [{"src": "SKILL.md", "dest": "templates/claude/skills/caveman/SKILL.md"}],
    })
    with pytest.raises(ManifestError, match="not in the 'vendored' section"):
        parse_manifest(json.dumps(data))


def test_vendored_repo_on_non_vendor_item_rejected() -> None:
    data = json.loads(json.dumps(VALID))
    data["vendored"] = [VALID_VENDORED_ENTRY]
    data["components"]["skills"]["items"].append({
        "id": "builtin-skill",
        "category": "dev",
        "description": "Builtin skill with vendored_repo",
        "mode": "builtin",
        "license": "MIT",
        "vendored_repo": "JuliusBrussee/caveman",
        "paths": [{"src": "claude/skills/foo", "dest": ".claude/skills/foo"}],
    })
    with pytest.raises(ManifestError, match="only allowed for mode 'vendor'"):
        parse_manifest(json.dumps(data))




