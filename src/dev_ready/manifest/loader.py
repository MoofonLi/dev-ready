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
from dev_ready.manifest.models import (
    CatalogItem,
    Injection,
    ItemPath,
    Manifest,
    UpstreamPin,
    VendoredPin,
)

SUPPORTED_MANIFEST_VERSION = 1
ALLOWED_MODES = ("builtin", "vendor", "pinned-dependency")
ALLOWED_INJECT_KINDS = ("mcp-server", "npm-dev-dependency")
CATALOG_COMPONENTS = ("skills", "mcp")
_ITEM_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")
_PIN_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:[-+.][0-9A-Za-z.-]+)?$")

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

    vendored = _parse_vendored(data, source)
    components = _parse_components(data, source, vendored)

    overlay_version = data.get("overlay_version")
    if not isinstance(overlay_version, str) or not overlay_version:
        raise ManifestError(f"{source}: 'overlay_version' must be a non-empty string")

    return Manifest(
        manifest_version=version,
        upstream=upstream,
        overlay_version=overlay_version,
        components=components,
        vendored=vendored,
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


def _parse_vendored_pin(index: int, entry: object, source: str) -> VendoredPin:
    if not isinstance(entry, dict):
        raise ManifestError(f"{source}: vendored entry[{index}] must be an object")

    repo = entry.get("repo")
    if not isinstance(repo, str) or not repo or not _REPO_PATTERN.fullmatch(repo):
        raise ManifestError(
            f"{source}: vendored entry[{index}] repo must look like 'owner/name', got {repo!r}"
        )

    commit = entry.get("commit")
    if not isinstance(commit, str) or not commit or not _COMMIT_PATTERN.fullmatch(commit):
        raise ManifestError(
            f"{source}: vendored entry[{index}] commit must be a 40-character lowercase hex sha, got {commit!r}"
        )

    lic = entry.get("license")
    if not isinstance(lic, str) or not lic:
        raise ManifestError(
            f"{source}: vendored entry[{index}] field 'license' must be a non-empty string"
        )

    paths_raw = entry.get("paths")
    parsed_paths: list[ItemPath] = []
    if paths_raw is not None:
        if not isinstance(paths_raw, list):
            raise ManifestError(
                f"{source}: vendored entry[{index}] field 'paths' must be a list"
            )
        for path_entry in paths_raw:
            if not isinstance(path_entry, dict):
                raise ManifestError(
                    f"{source}: vendored entry[{index}] path entry must be an object"
                )
            src = _parse_catalog_path("vendored", f"entry[{index}]", "src", path_entry.get("src"), source)
            dest = _parse_catalog_path("vendored", f"entry[{index}]", "dest", path_entry.get("dest"), source)
            parsed_paths.append(ItemPath(src=src, dest=dest))

    return VendoredPin(
        repo=repo,
        commit=commit,
        license=lic,
        paths=tuple(parsed_paths),
    )


def _parse_vendored(data: dict, source: str) -> tuple[VendoredPin, ...]:
    if "vendored" not in data:
        return ()
    raw = data["vendored"]
    if not isinstance(raw, list):
        raise ManifestError(f"{source}: 'vendored' must be a list")

    pins: list[VendoredPin] = []
    seen: set[tuple[str, str]] = set()
    for idx, entry in enumerate(raw):
        pin = _parse_vendored_pin(idx, entry, source)
        key = (pin.repo, pin.commit)
        if key in seen:
            raise ManifestError(
                f"{source}: duplicate vendored entry for repo {pin.repo!r} and commit {pin.commit!r}"
            )
        seen.add(key)
        pins.append(pin)
    return tuple(pins)


def _parse_components(
    data: dict, source: str, vendored: tuple[VendoredPin, ...]
) -> dict[str, tuple[CatalogItem, ...]]:
    raw = data.get("components")
    if not isinstance(raw, dict):
        raise ManifestError(f"{source}: 'components' must be an object")

    for key in raw:
        if key not in CATALOG_COMPONENTS:
            raise ManifestError(f"{source}: unknown component key in 'components': {key!r}")

    for req in CATALOG_COMPONENTS:
        if req not in raw:
            raise ManifestError(f"{source}: missing required component in 'components': {req!r}")

    result: dict[str, tuple[CatalogItem, ...]] = {}
    for comp_name, comp_dict in raw.items():
        if not isinstance(comp_dict, dict):
            raise ManifestError(f"{source}: component '{comp_name}' must be an object")
        items_raw = comp_dict.get("items")
        if not isinstance(items_raw, list):
            raise ManifestError(f"{source}: component '{comp_name}' field 'items' must be a list")

        seen_ids: set[str] = set()
        parsed_items: list[CatalogItem] = []
        for item_entry in items_raw:
            if not isinstance(item_entry, dict):
                raise ManifestError(f"{source}: item in '{comp_name}' must be an object")

            item_id = item_entry.get("id")
            if not isinstance(item_id, str) or not item_id or not _ITEM_ID_PATTERN.fullmatch(item_id):
                raise ManifestError(
                    f"{source}: component '{comp_name}' item 'id' must match pattern, got {item_id!r}"
                )

            if item_id in seen_ids:
                raise ManifestError(
                    f"{source}: duplicate item id {item_id!r} in component '{comp_name}'"
                )
            seen_ids.add(item_id)

            desc = item_entry.get("description")
            if not isinstance(desc, str) or not desc:
                raise ManifestError(
                    f"{source}: component '{comp_name}' item '{item_id}' field 'description' must be a non-empty string"
                )

            mode = item_entry.get("mode")
            if not isinstance(mode, str) or mode not in ALLOWED_MODES:
                raise ManifestError(
                    f"{source}: component '{comp_name}' item '{item_id}' field 'mode' must be one of {ALLOWED_MODES!r}, got {mode!r}"
                )

            lic = item_entry.get("license")
            if not isinstance(lic, str) or not lic:
                raise ManifestError(
                    f"{source}: component '{comp_name}' item '{item_id}' field 'license' must be a non-empty string"
                )

            vendored_repo_val = item_entry.get("vendored_repo")
            if mode == "vendor":
                if not isinstance(vendored_repo_val, str) or not vendored_repo_val:
                    raise ManifestError(
                        f"{source}: component '{comp_name}' item '{item_id}' with mode 'vendor'"
                        " must have a non-empty 'vendored_repo' field"
                    )
                # cross-reference: the named repo must appear in vendored
                vendored_repos = {v.repo for v in vendored}
                if vendored_repo_val not in vendored_repos:
                    raise ManifestError(
                        f"{source}: component '{comp_name}' item '{item_id}' references"
                        f" vendored_repo {vendored_repo_val!r} which is not in the 'vendored' section"
                    )
            else:
                if vendored_repo_val is not None:
                    raise ManifestError(
                        f"{source}: component '{comp_name}' item '{item_id}' field 'vendored_repo'"
                        " is only allowed for mode 'vendor' items"
                    )

            paths_raw = item_entry.get("paths")
            parsed_paths: list[ItemPath] = []
            if paths_raw is not None:
                if not isinstance(paths_raw, list):
                    raise ManifestError(
                        f"{source}: component '{comp_name}' item '{item_id}' field 'paths' must be a list"
                    )
                for path_entry in paths_raw:
                    if not isinstance(path_entry, dict):
                        raise ManifestError(
                            f"{source}: component '{comp_name}' item '{item_id}' path entry must be an object"
                        )
                    src = _parse_catalog_path(comp_name, item_id, "src", path_entry.get("src"), source)
                    dest = _parse_catalog_path(comp_name, item_id, "dest", path_entry.get("dest"), source)
                    parsed_paths.append(ItemPath(src=src, dest=dest))

            pin = item_entry.get("pin")
            if mode == "pinned-dependency":
                if not isinstance(pin, str) or not pin or not _PIN_PATTERN.fullmatch(pin):
                    raise ManifestError(
                        f"{source}: component '{comp_name}' item '{item_id}' field 'pin' must be a valid exact-semver string, got {pin!r}"
                    )
            else:
                if pin is not None:
                    raise ManifestError(
                        f"{source}: component '{comp_name}' item '{item_id}' field 'pin' is only allowed for pinned-dependency items"
                    )

            inject = _parse_injection(comp_name, item_id, mode, item_entry.get("inject"), source)

            if not parsed_paths and inject is None:
                raise ManifestError(
                    f"{source}: component '{comp_name}' item '{item_id}' must define paths, inject, or both"
                )

            parsed_items.append(
                CatalogItem(
                    id=item_id,
                    description=desc,
                    mode=mode,
                    license=lic,
                    paths=tuple(parsed_paths),
                    pin=pin,
                    inject=inject,
                    vendored_repo=vendored_repo_val if mode == "vendor" else None,
                )
            )

        result[comp_name] = tuple(parsed_items)
    return result


def _parse_injection(
    component: str, item_id: str, mode: str, raw: object, source: str
) -> Injection | None:
    if raw is None:
        return None
    if mode != "pinned-dependency":
        raise ManifestError(
            f"{source}: component '{component}' item '{item_id}' field 'inject' is only allowed"
            " for pinned-dependency items"
        )
    if not isinstance(raw, dict):
        raise ManifestError(
            f"{source}: component '{component}' item '{item_id}' field 'inject' must be an object"
        )

    kind = raw.get("kind")
    if not isinstance(kind, str) or kind not in ALLOWED_INJECT_KINDS:
        raise ManifestError(
            f"{source}: component '{component}' item '{item_id}' inject field 'kind' must be"
            f" one of {ALLOWED_INJECT_KINDS!r}, got {kind!r}"
        )

    target = _parse_catalog_path(component, item_id, "target", raw.get("target"), source)

    package = raw.get("package")
    if not isinstance(package, str) or not package:
        raise ManifestError(
            f"{source}: component '{component}' item '{item_id}' inject field 'package' must be"
            " a non-empty string"
        )

    if kind == "mcp-server":
        if "scripts" in raw and raw.get("scripts") is not None:
            raise ManifestError(
                f"{source}: component '{component}' item '{item_id}' inject kind 'mcp-server' must not have 'scripts'"
            )
        server_name = raw.get("server_name")
        if not isinstance(server_name, str) or not server_name:
            raise ManifestError(
                f"{source}: component '{component}' item '{item_id}' inject field 'server_name' must be"
                " a non-empty string"
            )
        command = raw.get("command")
        if not isinstance(command, str) or not command:
            raise ManifestError(
                f"{source}: component '{component}' item '{item_id}' inject field 'command' must be"
                " a non-empty string"
            )
        return Injection(
            kind=kind,
            target=target,
            package=package,
            server_name=server_name,
            command=command,
        )

    elif kind == "npm-dev-dependency":
        if ("server_name" in raw and raw.get("server_name") is not None) or (
            "command" in raw and raw.get("command") is not None
        ):
            raise ManifestError(
                f"{source}: component '{component}' item '{item_id}' inject kind 'npm-dev-dependency' must not have 'server_name' or 'command'"
            )
        scripts_raw = raw.get("scripts")
        if not isinstance(scripts_raw, dict) or not scripts_raw:
            raise ManifestError(
                f"{source}: component '{component}' item '{item_id}' inject field 'scripts' must be"
                " a non-empty object"
            )
        scripts_list: list[tuple[str, str]] = []
        for s_name, s_cmd in scripts_raw.items():
            if not isinstance(s_name, str) or not s_name or not isinstance(s_cmd, str) or not s_cmd:
                raise ManifestError(
                    f"{source}: component '{component}' item '{item_id}' inject script entry must be"
                    " a non-empty string -> non-empty string mapping"
                )
            scripts_list.append((s_name, s_cmd))
        return Injection(
            kind=kind,
            target=target,
            package=package,
            scripts=tuple(scripts_list),
        )

    return None


def _parse_catalog_path(
    component: str, item_id: str, field: str, value: object, source: str
) -> str:
    if not isinstance(value, str) or not value:
        raise ManifestError(
            f"{source}: component '{component}' item '{item_id}' path field '{field}' must be a non-empty string"
        )
    if (
        value.startswith("/")
        or value.startswith("\\")
        or "\\" in value
        or any(seg == ".." for seg in value.split("/"))
    ):
        raise ManifestError(
            f"{source}: component '{component}' item '{item_id}' path field '{field}' must be a relative path without '..', got {value!r}"
        )
    return value

