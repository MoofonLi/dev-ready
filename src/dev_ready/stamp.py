"""Stamp loading and validation module.

Reads `.dev-ready.json` project stamps. Pure local I/O — must never import `dev_ready.fetch`.
"""

from dataclasses import dataclass
import json
from pathlib import Path

from dev_ready.errors import StampInvalidError, StampMissingError

__all__ = ["Stamp", "StampItem", "UpstreamStampInfo", "load_stamp"]


@dataclass(frozen=True)
class StampItem:
    id: str
    pin: str | None = None


@dataclass(frozen=True)
class UpstreamStampInfo:
    repo: str
    commit: str


@dataclass(frozen=True)
class Stamp:
    stamp_version: int
    dev_ready_version: str
    skills_included: bool
    skills_items: tuple[StampItem, ...]
    mcp_included: bool
    mcp_items: tuple[StampItem, ...]
    docs_included: bool
    agents_included: bool
    upstream: UpstreamStampInfo


def load_stamp(project_dir: Path) -> Stamp:
    """Load and validate `.dev-ready.json` from `project_dir`.

    Raises `StampMissingError` if missing or target path is invalid.
    Raises `StampInvalidError` if JSON is corrupt or stamp schema/version is unsupported.
    """
    if not project_dir.exists() or not project_dir.is_dir():
        raise StampMissingError(f"target path '{project_dir}' is not an existing directory")

    stamp_path = project_dir / ".dev-ready.json"
    if not stamp_path.is_file():
        raise StampMissingError(
            f"target directory '{project_dir}' is missing .dev-ready.json stamp. "
            "Note: projects generated before dev-ready v0.3 have no stamp and cannot be checked."
        )

    try:
        content = stamp_path.read_text(encoding="utf-8")
        data = json.loads(content)
    except (OSError, json.JSONDecodeError) as error:
        raise StampInvalidError(f"failed to read or parse .dev-ready.json: {error}") from error

    if not isinstance(data, dict):
        raise StampInvalidError(".dev-ready.json root must be a JSON object")

    version = data.get("stamp_version")
    if not isinstance(version, int) or isinstance(version, bool):
        raise StampInvalidError(".dev-ready.json is missing a valid integer 'stamp_version'")

    if version < 1 or version > 2:
        raise StampInvalidError(
            f"unsupported stamp_version {version}; this CLI supports stamp versions 1 and 2."
        )

    dev_ready_ver = data.get("dev_ready_version")
    if not isinstance(dev_ready_ver, str):
        raise StampInvalidError(".dev-ready.json is missing 'dev_ready_version'")

    upstream_raw = data.get("upstream")
    if not isinstance(upstream_raw, dict):
        raise StampInvalidError(".dev-ready.json is missing 'upstream' object")
    repo = upstream_raw.get("repo")
    commit = upstream_raw.get("commit")
    if not isinstance(repo, str) or not isinstance(commit, str):
        raise StampInvalidError(".dev-ready.json 'upstream' must contain string 'repo' and 'commit'")

    components = data.get("components")
    if not isinstance(components, dict):
        raise StampInvalidError(".dev-ready.json is missing 'components' object")

    def _parse_component_items(comp_name: str) -> tuple[bool, tuple[StampItem, ...]]:
        comp_raw = components.get(comp_name)
        if not isinstance(comp_raw, dict):
            raise StampInvalidError(f".dev-ready.json components missing '{comp_name}' object")
        included = bool(comp_raw.get("included", False))
        items_raw = comp_raw.get("items", [])
        if not isinstance(items_raw, list):
            raise StampInvalidError(f".dev-ready.json components.{comp_name}.items must be a list")

        parsed_items: list[StampItem] = []
        for raw_item in items_raw:
            if isinstance(raw_item, str):
                parsed_items.append(StampItem(id=raw_item, pin=None))
            elif isinstance(raw_item, dict):
                item_id = raw_item.get("id")
                if not isinstance(item_id, str):
                    raise StampInvalidError(f"invalid item entry in components.{comp_name}")
                item_pin = raw_item.get("pin")
                if item_pin is not None and not isinstance(item_pin, str):
                    raise StampInvalidError(f"invalid item pin in components.{comp_name}")
                parsed_items.append(StampItem(id=item_id, pin=item_pin))
            else:
                raise StampInvalidError(f"unrecognized item entry format in components.{comp_name}")

        return included, tuple(parsed_items)

    skills_included, skills_items = _parse_component_items("skills")
    mcp_included, mcp_items = _parse_component_items("mcp")

    docs_raw = components.get("docs")
    docs_included = bool(docs_raw.get("included", False)) if isinstance(docs_raw, dict) else False

    agents_raw = components.get("agents")
    agents_included = bool(agents_raw.get("included", False)) if isinstance(agents_raw, dict) else False

    return Stamp(
        stamp_version=version,
        dev_ready_version=dev_ready_ver,
        skills_included=skills_included,
        skills_items=skills_items,
        mcp_included=mcp_included,
        mcp_items=mcp_items,
        docs_included=docs_included,
        agents_included=agents_included,
        upstream=UpstreamStampInfo(repo=repo, commit=commit),
    )
