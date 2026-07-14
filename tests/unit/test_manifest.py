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


def test_bundled_manifest_is_valid() -> None:
    manifest = load_default_manifest()
    assert "base_template" in manifest.upstream
