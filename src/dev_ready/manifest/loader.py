"""Load and validate manifest.json.

Single source of truth for upstream pins (ADR-002). The canonical manifest
ships inside the package at dev_ready/manifest.json so an installed CLI
always carries the pin it was released and tested with.
"""

import json
import re
from importlib import resources
from pathlib import Path, PureWindowsPath

from dev_ready.catalog_effects import CatalogEffectError, parse_catalog_effect
from dev_ready.errors import ManifestError
from dev_ready.manifest.models import (
    AgentTarget,
    CATALOG_COMPONENTS,
    CatalogItem,
    Category,
    ComponentCatalog,
    DefaultSet,
    ItemPath,
    Manifest,
    RETIRED_LOOP_ITEM_IDS,
    UpstreamPin,
    VendoredPin,
)

SUPPORTED_MANIFEST_VERSION = 1
ALLOWED_MODES = ("builtin", "vendor", "pinned-dependency")
DEFAULT_SET_SIZE_LIMIT = 3
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

    categories = _parse_categories(data, source)
    agent_targets = _parse_agent_targets(data, source)
    vendored = _parse_vendored(data, source)
    components = _parse_components(data, source, vendored, categories)
    _validate_non_empty_categories(components, categories, source)
    _validate_catalog_requirements(components, source)
    development_loop_ids = _validate_development_loops(components, source)
    default_set = _parse_default_set(
        data,
        components,
        development_loop_ids,
        source,
    )

    overlay_version = data.get("overlay_version")
    if not isinstance(overlay_version, str) or not overlay_version:
        raise ManifestError(f"{source}: 'overlay_version' must be a non-empty string")

    catalog = ComponentCatalog(
        components,
        agent_targets,
        categories,
        default_set,
    )
    return Manifest(
        manifest_version=version,
        upstream=upstream,
        overlay_version=overlay_version,
        components=catalog,
        agent_targets=agent_targets,
        categories=categories,
        default_set=default_set,
        vendored=vendored,
    )


def _validate_development_loops(
    components: dict[str, tuple[CatalogItem, ...]],
    source: str,
) -> tuple[str, ...]:
    """Validate relationships between parsed loops and Enhancements."""
    items = tuple(item for component in components.values() for item in component)
    loops = tuple(item for item in items if item.kind == "development-loop")
    for item in items:
        if item.id in RETIRED_LOOP_ITEM_IDS and not (
            item.id == "spec-loop" and item.kind == "development-loop"
        ):
            raise ManifestError(
                f"{source}: retired catalog id {item.id!r} cannot be declared selectable"
            )

    if not loops:
        raise ManifestError(
            f"{source}: Dev Category must declare at least one development loop"
        )

    loop_ids = {item.id for item in loops}
    step_ids = {step for loop in loops for step in loop.steps}
    duplicated_steps = sorted(({item.id for item in items} - loop_ids) & step_ids)
    if duplicated_steps:
        raise ManifestError(
            f"{source}: catalog item {duplicated_steps[0]!r} duplicates development "
            f"loop step {duplicated_steps[0]!r}"
        )
    for item in items:
        if item.kind == "development-loop" and item.mount is not None:
            raise ManifestError(
                f"{source}: development loop {item.id!r} cannot declare a mount"
            )
        if item.mount is not None and len(item.paths) != 1:
            raise ManifestError(
                f"{source}: catalog item {item.id!r} declaring a mount must have "
                "exactly one path"
            )
        if item.mount is not None and not all(
            item.mount in loop.steps for loop in loops
        ):
            raise ManifestError(
                f"{source}: catalog item {item.id!r} mount {item.mount!r} must name "
                "a step of every development loop"
            )
    return tuple(item.id for item in loops)


def _parse_default_set(
    data: dict,
    components: dict[str, tuple[CatalogItem, ...]],
    development_loop_ids: tuple[str, ...],
    source: str,
) -> DefaultSet:
    raw = data.get("default_set")
    if not isinstance(raw, dict):
        raise ManifestError(f"{source}: 'default_set' must be an object")

    development_loop = raw.get("development_loop")
    if not isinstance(development_loop, str) or development_loop not in development_loop_ids:
        raise ManifestError(
            f"{source}: Default Set 'development_loop' must name one of "
            f"{list(development_loop_ids)!r}"
        )

    enhancements = _parse_default_set_ids(
        raw.get("enhancements"),
        field="enhancements",
        source=source,
    )
    item_by_id = {
        item.id: item for component_items in components.values() for item in component_items
    }
    unknown_enhancements = sorted(set(enhancements) - set(item_by_id))
    if unknown_enhancements:
        raise ManifestError(
            f"{source}: Default Set has unknown Enhancement ids "
            f"{unknown_enhancements!r}"
        )
    non_enhancements = sorted(
        item_id for item_id in enhancements if item_by_id[item_id].kind != "enhancement"
    )
    if non_enhancements:
        raise ManifestError(
            f"{source}: Default Set Enhancement ids must not name development loops: "
            f"{non_enhancements!r}"
        )

    current_size = 1 + len(enhancements)
    if current_size > DEFAULT_SET_SIZE_LIMIT:
        raise ManifestError(
            f"{source}: Default Set size {current_size} exceeds limit "
            f"{DEFAULT_SET_SIZE_LIMIT}; change DEFAULT_SET_SIZE_LIMIT in "
            "dev_ready.manifest.loader.py to revise the budget"
        )
    return DefaultSet(
        development_loop=development_loop,
        enhancements=enhancements,
    )


def _parse_default_set_ids(
    raw: object,
    *,
    field: str,
    source: str,
) -> tuple[str, ...]:
    if not isinstance(raw, list):
        raise ManifestError(f"{source}: Default Set field {field!r} must be a list")
    values: list[str] = []
    for value in raw:
        if not isinstance(value, str) or not value or not _ITEM_ID_PATTERN.fullmatch(value):
            raise ManifestError(
                f"{source}: Default Set field {field!r} entries must be identifiers"
            )
        if value in values:
            raise ManifestError(
                f"{source}: Default Set field {field!r} has duplicate id {value!r}"
            )
        values.append(value)
    return tuple(values)


def _parse_categories(data: dict, source: str) -> dict[str, Category]:
    raw = data.get("categories")
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ManifestError(f"{source}: 'categories' must be an object")

    categories: dict[str, Category] = {}
    for category_id, entry in raw.items():
        if (
            not isinstance(category_id, str)
            or not category_id
            or not _ITEM_ID_PATTERN.fullmatch(category_id)
        ):
            raise ManifestError(
                f"{source}: category id must match pattern, got {category_id!r}"
            )
        if not isinstance(entry, dict):
            raise ManifestError(f"{source}: category {category_id!r} must be an object")
        description = entry.get("description")
        if not isinstance(description, str) or not description:
            raise ManifestError(
                f"{source}: category {category_id!r} field 'description' "
                "must be a non-empty string"
            )
        categories[category_id] = Category(
            id=category_id,
            description=description,
        )
    return categories


def _parse_agent_targets(data: dict, source: str) -> dict[str, AgentTarget]:
    raw = data.get("agent_targets")
    if not isinstance(raw, dict) or not raw:
        raise ManifestError(f"{source}: 'agent_targets' must be a non-empty object")

    targets: dict[str, AgentTarget] = {}
    for target_id, entry in raw.items():
        if (
            not isinstance(target_id, str)
            or not target_id
            or not _ITEM_ID_PATTERN.fullmatch(target_id)
        ):
            raise ManifestError(
                f"{source}: agent target id must match pattern, got {target_id!r}"
            )
        if not isinstance(entry, dict):
            raise ManifestError(f"{source}: agent target {target_id!r} must be an object")

        description = entry.get("description")
        if not isinstance(description, str) or not description:
            raise ManifestError(
                f"{source}: agent target {target_id!r} field 'description' "
                "must be a non-empty string"
            )
        skills_dir = _parse_agent_target_path(
            target_id, "skills_dir", entry.get("skills_dir"), source, nullable=False
        )
        rules_file = _parse_agent_target_path(
            target_id, "rules_file", entry.get("rules_file"), source, nullable=True
        )
        mcp_file = _parse_agent_target_path(
            target_id, "mcp_file", entry.get("mcp_file"), source, nullable=True
        )
        assert skills_dir is not None
        targets[target_id] = AgentTarget(
            id=target_id,
            description=description,
            skills_dir=skills_dir,
            rules_file=rules_file,
            mcp_file=mcp_file,
        )
    return targets


def _parse_agent_target_path(
    target_id: str,
    field: str,
    value: object,
    source: str,
    *,
    nullable: bool,
) -> str | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str) or not value:
        expected = "a relative path or null" if nullable else "a non-empty relative path"
        raise ManifestError(
            f"{source}: agent target {target_id!r} field {field!r} must be {expected}"
        )
    if (
        value.startswith(("/", "\\"))
        or bool(PureWindowsPath(value).drive)
        or "\\" in value
        or any(segment in {"", ".."} for segment in value.split("/"))
    ):
        raise ManifestError(
            f"{source}: agent target {target_id!r} field {field!r} must be a relative path "
            f"without '..', got {value!r}"
        )
    return value



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
    data: dict,
    source: str,
    vendored: tuple[VendoredPin, ...],
    categories: dict[str, Category],
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

            category = item_entry.get("category")
            if not isinstance(category, str) or not category:
                raise ManifestError(
                    f"{source}: component '{comp_name}' item '{item_id}' field "
                    "'category' must be a non-empty string"
                )
            if category not in categories:
                raise ManifestError(
                    f"{source}: component '{comp_name}' item '{item_id}' references "
                    f"unknown category {category!r}"
                )

            kind, steps = _parse_item_kind_and_steps(
                item_entry,
                component=comp_name,
                item_id=item_id,
                category=category,
                source=source,
            )
            mount = item_entry.get("mount")
            if "mount" in item_entry and (
                not isinstance(mount, str) or not mount
            ):
                raise ManifestError(
                    f"{source}: component '{comp_name}' item '{item_id}' field "
                    "'mount' must be a non-empty string"
                )

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

            requires = _parse_requirements(comp_name, item_id, item_entry, source)

            try:
                effect = parse_catalog_effect(
                    item_entry.get("inject"),
                    mode=mode,
                    pin=pin,
                    location=f"{source}: component '{comp_name}' item '{item_id}'",
                )
            except CatalogEffectError as error:
                raise ManifestError(str(error)) from error

            if not parsed_paths and effect is None:
                raise ManifestError(
                    f"{source}: component '{comp_name}' item '{item_id}' must define paths, inject, or both"
                )

            parsed_items.append(
                CatalogItem(
                    id=item_id,
                    category=category,
                    mount=mount if isinstance(mount, str) else None,
                    kind=kind,
                    steps=steps,
                    description=desc,
                    mode=mode,
                    license=lic,
                    paths=tuple(parsed_paths),
                    pin=pin,
                    effect=effect,
                    vendored_repo=vendored_repo_val if mode == "vendor" else None,
                    requires=requires,
                )
            )

        result[comp_name] = tuple(parsed_items)
    return result


def _parse_item_kind_and_steps(
    entry: dict,
    *,
    component: str,
    item_id: str,
    category: str,
    source: str,
) -> tuple[str, tuple[str, ...]]:
    kind = entry.get("kind", "enhancement")
    if kind not in {"development-loop", "enhancement"}:
        raise ManifestError(
            f"{source}: component '{component}' item {item_id!r} field 'kind' "
            "must be 'development-loop' or 'enhancement'"
        )
    if kind == "enhancement":
        if "steps" in entry:
            raise ManifestError(
                f"{source}: component '{component}' item {item_id!r} field 'steps' "
                "is only allowed for a development loop"
            )
        return kind, ()
    if category != "dev":
        raise ManifestError(
            f"{source}: development loop {item_id!r} must belong to the Dev Category"
        )
    raw_steps = entry.get("steps")
    if not isinstance(raw_steps, list) or not raw_steps:
        raise ManifestError(
            f"{source}: development loop {item_id!r} field 'steps' must be a non-empty list"
        )
    steps: list[str] = []
    for step in raw_steps:
        if (
            not isinstance(step, str)
            or not step
            or not _ITEM_ID_PATTERN.fullmatch(step)
        ):
            raise ManifestError(
                f"{source}: development loop {item_id!r} step ids must match "
                f"the catalog id pattern, got {step!r}"
            )
        if step in steps:
            raise ManifestError(
                f"{source}: development loop {item_id!r} has duplicate step {step!r}"
            )
        steps.append(step)
    return kind, tuple(steps)


def _validate_non_empty_categories(
    components: dict[str, tuple[CatalogItem, ...]],
    categories: dict[str, Category],
    source: str,
) -> None:
    used = {item.category for items in components.values() for item in items}
    for category_id in categories:
        if category_id not in used:
            raise ManifestError(
                f"{source}: category {category_id!r} contains no catalog items"
            )


def _parse_requirements(
    component: str, item_id: str, entry: dict[str, object], source: str
) -> tuple[str, ...]:
    raw = entry.get("requires")
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise ManifestError(
            f"{source}: component '{component}' item '{item_id}' field 'requires' must be a list"
        )

    requirements: list[str] = []
    for required_id in raw:
        if (
            not isinstance(required_id, str)
            or not required_id
            or not _ITEM_ID_PATTERN.fullmatch(required_id)
        ):
            raise ManifestError(
                f"{source}: component '{component}' item '{item_id}' requirement ids must match pattern, got {required_id!r}"
            )
        if required_id in requirements:
            raise ManifestError(
                f"{source}: component '{component}' item '{item_id}' has duplicate requirement {required_id!r}"
            )
        requirements.append(required_id)
    return tuple(requirements)


def _validate_catalog_requirements(
    components: dict[str, tuple[CatalogItem, ...]], source: str
) -> None:
    all_components_by_id = {
        item.id: component
        for component, items in components.items()
        for item in items
    }

    for component, items in components.items():
        item_by_id = {item.id: item for item in items}
        for item in items:
            for required_id in item.requires:
                if required_id == item.id:
                    raise ManifestError(
                        f"{source}: component '{component}' item '{item.id}' cannot require itself"
                    )
                if required_id not in item_by_id:
                    other_component = all_components_by_id.get(required_id)
                    if other_component is not None:
                        raise ManifestError(
                            f"{source}: component '{component}' item '{item.id}' requirement {required_id!r} must reference an item in the same component, not '{other_component}'"
                        )
                    raise ManifestError(
                        f"{source}: component '{component}' item '{item.id}' requires unknown item {required_id!r}"
                    )

        visiting: list[str] = []
        visited: set[str] = set()

        def visit(item_id: str) -> None:
            if item_id in visited:
                return
            if item_id in visiting:
                cycle_start = visiting.index(item_id)
                cycle = [*visiting[cycle_start:], item_id]
                raise ManifestError(
                    f"{source}: component '{component}' dependency cycle: {' -> '.join(cycle)}"
                )
            visiting.append(item_id)
            for required_id in item_by_id[item_id].requires:
                visit(required_id)
            visiting.pop()
            visited.add(item_id)

        for item in items:
            visit(item.id)


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

