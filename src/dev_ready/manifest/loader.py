"""Load and validate manifest.json.

Single source of truth for upstream pins (ADR-002). The canonical manifest
ships inside the package at dev_ready/manifest.json so an installed CLI
always carries the pin it was released and tested with.
"""

import json
import re
from importlib import resources
from pathlib import Path

from dev_ready.errors import ManifestError
from dev_ready.manifest.models import Manifest, UpstreamPin

SUPPORTED_MANIFEST_VERSION = 1

_COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")
# owner/name, GitHub-shaped: each side must start with an alphanumeric so no
# segment can begin with '.' (blocks traversal-shaped values like '..x/y' that
# the old `[\w.-]+` permitted). owner is alphanumeric + hyphen; repo name also
# allows '.' and '_'. Defense-in-depth for the URL built in fetch, hardening the
# path before load_manifest() is ever pointed at a non-bundled manifest.
_REPO_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9-]*/[a-zA-Z0-9][a-zA-Z0-9._-]*$")


def load_manifest(path: Path) -> Manifest:
    """Load and validate a manifest from an explicit path."""
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as error:
        raise ManifestError(f"cannot read manifest at {path}: {error}") from error
    return parse_manifest(raw, source=str(path))


def load_default_manifest() -> Manifest:
    """Load the manifest bundled inside the dev_ready package."""
    resource = resources.files("dev_ready").joinpath("manifest.json")
    try:
        raw = resource.read_text(encoding="utf-8")
    except OSError as error:
        raise ManifestError(f"bundled manifest.json is missing or unreadable: {error}") from error
    return parse_manifest(raw, source="dev_ready/manifest.json")


def parse_manifest(raw: str, source: str = "<string>") -> Manifest:
    """Parse and validate manifest JSON text."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as error:
        raise ManifestError(f"{source} is not valid JSON: {error}") from error
    if not isinstance(data, dict):
        raise ManifestError(f"{source}: top level must be a JSON object")

    version = data.get("manifest_version")
    if version != SUPPORTED_MANIFEST_VERSION:
        raise ManifestError(
            f"{source}: unsupported manifest_version {version!r},"
            f" expected {SUPPORTED_MANIFEST_VERSION}"
        )

    upstream_raw = data.get("upstream")
    if not isinstance(upstream_raw, dict) or not upstream_raw:
        raise ManifestError(f"{source}: 'upstream' must be a non-empty object")
    upstream = {name: _parse_pin(name, entry, source) for name, entry in upstream_raw.items()}

    overlay_version = data.get("overlay_version")
    if not isinstance(overlay_version, str) or not overlay_version:
        raise ManifestError(f"{source}: 'overlay_version' must be a non-empty string")

    return Manifest(
        manifest_version=version,
        upstream=upstream,
        overlay_version=overlay_version,
    )


def _parse_pin(name: str, entry: object, source: str) -> UpstreamPin:
    if not isinstance(entry, dict):
        raise ManifestError(f"{source}: upstream '{name}' must be an object")

    values: dict[str, str] = {}
    for field in ("repo", "ref", "commit", "license"):
        value = entry.get(field)
        if not isinstance(value, str) or not value:
            raise ManifestError(
                f"{source}: upstream '{name}' field '{field}' must be a non-empty string"
            )
        values[field] = value

    if not _REPO_PATTERN.fullmatch(values["repo"]):
        raise ManifestError(
            f"{source}: upstream '{name}' repo must look like 'owner/name',"
            f" got {values['repo']!r}"
        )
    if not _COMMIT_PATTERN.fullmatch(values["commit"]):
        raise ManifestError(
            f"{source}: upstream '{name}' commit must be a 40-character lowercase"
            f" hex sha, got {values['commit']!r}"
        )

    verified_at = entry.get("verified_at")
    if verified_at is not None and not isinstance(verified_at, str):
        raise ManifestError(
            f"{source}: upstream '{name}' field 'verified_at' must be a string or null"
        )

    exclude = _parse_path_list(name, entry, source, "exclude")
    prune = _parse_path_list(name, entry, source, "prune")

    return UpstreamPin(
        repo=values["repo"],
        ref=values["ref"],
        commit=values["commit"],
        license=values["license"],
        verified_at=verified_at,
        exclude=exclude,
        prune=prune,
    )


def _parse_path_list(name: str, entry: dict, source: str, field: str) -> tuple[str, ...]:
    """Validate optional per-pin path lists (exclude or prune).

    Entries are gitwildmatch patterns handed to Copier's path matcher, never to
    filesystem APIs. Two accepted shapes:

    - relative pattern (``img/**``, ``CONTRIBUTING.md``): gitwildmatch treats a
      slash-free pattern as matching at ANY depth.
    - root-anchored pattern with a single leading ``/`` (``/README.md``): the
      leading slash anchors the match to the template root, so it hits only the
      top-level entry and not same-named entries in subdirectories. The ``/`` is
      a match anchor, not an absolute filesystem path.

    Rejected in every case: backslash-prefixed entries, a double leading slash,
    ``..`` path segments, and empty strings.
    """
    raw = entry.get(field)
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise ManifestError(f"{source}: upstream '{name}' field '{field}' must be a list")
    patterns: list[str] = []
    for item in raw:
        if not isinstance(item, str) or not item:
            raise ManifestError(
                f"{source}: upstream '{name}' '{field}' entries must be non-empty strings"
            )
        # A single leading '/' is a gitwildmatch root anchor, not an absolute
        # path; strip it before the traversal checks. Backslash prefixes and
        # double leading slashes stay rejected.
        unanchored = item[1:] if item.startswith("/") else item
        if (
            item.startswith("\\")
            or unanchored.startswith(("/", "\\"))
            or not unanchored
            or ".." in unanchored.split("/")
        ):
            raise ManifestError(
                f"{source}: upstream '{name}' '{field}' entries must be relative paths"
                f" (an optional single leading '/' root anchor is allowed),"
                f" without '..', got {item!r}"
            )
        patterns.append(item)
    return tuple(patterns)
