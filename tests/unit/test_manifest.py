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
                    "id": "project-orientation",
                    "description": "Skill that orients an AI agent to the generated project's layout, stack, and dev workflow.",
                    "mode": "builtin",
                    "license": "MIT",
                    "paths": [
                        {
                            "src": "claude/skills/project-orientation",
                            "dest": ".claude/skills/project-orientation",
                        }
                    ],
                }
            ]
        },
        "mcp": {
            "items": [
                {
                    "id": "mcp-config",
                    "description": "Base .mcp.json MCP server configuration for the generated project.",
                    "mode": "builtin",
                    "license": "MIT",
                    "paths": [{"src": "mcp/mcp.json", "dest": ".mcp.json"}],
                }
            ]
        },
    },
    "overlay_version": "0.1.0",
}


def test_parse_valid_manifest() -> None:
    manifest = parse_manifest(json.dumps(VALID))
    assert manifest.manifest_version == 1
    assert manifest.overlay_version == "0.1.0"
    pin = manifest.upstream["base_template"]
    assert pin.repo == "fastapi/full-stack-fastapi-template"
    assert pin.commit == "4cd0d9e51aebd1af6f82d91ad0df4c9e41f4dea2"
    assert pin.verified_at == "2026-07-04"
    assert pin.license == "MIT"
    assert len(manifest.components["skills"]) == 1
    skill = manifest.components["skills"][0]
    assert skill.id == "project-orientation"
    assert skill.mode == "builtin"
    assert skill.license == "MIT"
    assert skill.paths[0].src == "claude/skills/project-orientation"
    assert skill.paths[0].dest == ".claude/skills/project-orientation"
    assert len(manifest.components["mcp"]) == 1
    mcp = manifest.components["mcp"][0]
    assert mcp.id == "mcp-config"
    assert mcp.mode == "builtin"
    assert mcp.license == "MIT"
    assert mcp.paths[0].src == "mcp/mcp.json"
    assert mcp.paths[0].dest == ".mcp.json"



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


def test_missing_components_rejected() -> None:
    data = json.loads(json.dumps(VALID))
    del data["components"]
    with pytest.raises(ManifestError, match="'components' must be an object"):
        parse_manifest(json.dumps(data))


def test_unknown_component_key_rejected() -> None:
    data = json.loads(json.dumps(VALID))
    data["components"]["docs"] = {"items": []}
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
    assert item.inject is not None
    assert item.inject.kind == "mcp-server"
    assert item.inject.target == ".mcp.json"
    assert item.inject.package == "codebase-memory-mcp"
    assert item.inject.server_name == "codebase-memory"
    assert item.inject.command == "uvx"


def test_valid_pinned_dependency_npm_dev_dependency() -> None:
    data = json.loads(json.dumps(VALID))
    data["components"]["skills"]["items"].append({
        "id": "react-doctor",
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
    assert item.inject is not None
    assert item.inject.kind == "npm-dev-dependency"
    assert item.inject.scripts == (("doctor", "react-doctor"),)


@pytest.mark.parametrize("bad_pin", ["", "latest", "^1.2.3", "1.2", "1.2.3 "])
def test_malformed_pin_rejected(bad_pin: str) -> None:
    data = json.loads(json.dumps(VALID))
    data["components"]["mcp"]["items"].append({
        "id": "code-memory",
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
        "description": "Empty item",
        "mode": "pinned-dependency",
        "license": "MIT",
        "pin": "1.0.0",
    })
    with pytest.raises(ManifestError, match="must define paths, inject, or both"):
        parse_manifest(json.dumps(data))


def test_builtin_items_regression() -> None:
    manifest = load_default_manifest()
    mcp_items = {item.id: item for item in manifest.components["mcp"]}
    assert "code-memory" in mcp_items
    assert mcp_items["code-memory"].pin == "0.9.0"
    assert mcp_items["mcp-config"].pin is None
    skills_items = {item.id: item for item in manifest.components["skills"]}
    assert "react-doctor" in skills_items
    assert skills_items["react-doctor"].pin == "0.8.1"
    assert skills_items["react-doctor"].inject is not None
    assert skills_items["react-doctor"].inject.kind == "npm-dev-dependency"


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
        "description": "Builtin skill with vendored_repo",
        "mode": "builtin",
        "license": "MIT",
        "vendored_repo": "JuliusBrussee/caveman",
        "paths": [{"src": "claude/skills/foo", "dest": ".claude/skills/foo"}],
    })
    with pytest.raises(ManifestError, match="only allowed for mode 'vendor'"):
        parse_manifest(json.dumps(data))




