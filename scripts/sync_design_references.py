#!/usr/bin/env python3
"""Derive Design References from the pinned awesome-design-md source."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections.abc import Iterable, Mapping
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_REFERENCE_REPO = "VoltAgent/awesome-design-md"
_REFERENCE_ROOT = Path("design-md")
_IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9-]*$")
_HEADING = re.compile(r"# (?P<title>.+) Inspired Design System Analysis")
_DESIGN_SECTION = re.compile(
    r"^### design items\n.*?(?=^### |\Z)",
    re.MULTILINE | re.DOTALL,
)
_ID_OVERRIDES = {"x.ai": "design-xai"}
_TITLE_OVERRIDES = {
    "bmw-m": "BMW M",
    "slack": "Slack",
    "theverge": "The Verge",
}
_FRONTEND_DESIGN_SKILL_LINE = (
    "- `frontend-design`: You want a distinctive, polished frontend rather than a "
    "generic interface."
)


def _reference_entry(data: dict[str, object]) -> dict[str, object]:
    vendored = data.get("vendored")
    if not isinstance(vendored, list):
        raise ValueError("manifest vendored provenance must be a list")
    for entry in vendored:
        if isinstance(entry, dict) and entry.get("repo") == _REFERENCE_REPO:
            return entry
    raise ValueError(f"manifest has no vendored entry for {_REFERENCE_REPO}")


def _identifier_for(slug: str) -> str:
    return _ID_OVERRIDES.get(slug, f"design-{slug.split('.', 1)[0]}")


def derive_design_references(
    slugs: Iterable[str], readme_headings: Mapping[str, str]
) -> tuple[list[dict[str, object]], str]:
    """Return derived catalog entries and the Generation Skill design section."""
    derived: list[tuple[str, dict[str, object]]] = []
    for slug in slugs:
        identifier = _identifier_for(slug)
        if not _IDENTIFIER.fullmatch(identifier):
            raise ValueError(
                f"derived identifier {identifier!r} does not match the manifest pattern"
            )

        if slug == "slack":
            title = _TITLE_OVERRIDES[slug]
        else:
            heading = readme_headings.get(slug)
            match = _HEADING.fullmatch(heading or "")
            if match is None:
                raise ValueError(f"upstream heading shape changed for {slug!r}")
            title = _TITLE_OVERRIDES.get(slug, match.group("title"))

        path = f"docs/{identifier}.md"
        derived.append(
            (
                slug,
                {
                    "id": identifier,
                    "title": title,
                    "category": "design",
                    "mount": "implement",
                    "description": f"{title}-inspired DESIGN.md reference.",
                    "mode": "vendor",
                    "license": "MIT",
                    "vendored_repo": _REFERENCE_REPO,
                    "paths": [{"src": path, "dest": path}],
                },
            )
        )

    derived.sort(key=lambda pair: str(pair[1]["id"]))
    items = [item for _, item in derived]
    skill_lines = [_FRONTEND_DESIGN_SKILL_LINE]
    skill_lines.extend(
        f"- `{item['id']}`: You want {item['title']}'s design language as a reference."
        for item in items
    )
    skill_section = "### design items\n\n" + "\n".join(skill_lines) + "\n\n"
    return items, skill_section


def synchronize_outputs(
    manifest_path: Path,
    skill_path: Path,
    slugs: Iterable[str],
    readme_headings: Mapping[str, str],
    *,
    check: bool,
) -> bool:
    """Regenerate derived outputs, or report whether check mode finds drift."""
    ordered_slugs = tuple(sorted(slugs))
    items, skill_section = derive_design_references(ordered_slugs, readme_headings)
    data = json.loads(manifest_path.read_text(encoding="utf-8"))

    reference_entry = _reference_entry(data)
    existing_paths = reference_entry.get("paths", [])
    if not isinstance(existing_paths, list):
        raise ValueError(f"vendored entry for {_REFERENCE_REPO} paths must be a list")
    preserved_paths = [
        path
        for path in existing_paths
        if not (
            isinstance(path, dict)
            and isinstance(path.get("src"), str)
            and path["src"].startswith("design-md/")
            and path["src"].endswith("/DESIGN.md")
        )
    ]
    reference_entry["paths"] = [
        {
            "src": f"design-md/{slug}/DESIGN.md",
            "dest": "src/dev_ready/templates/docs/" f"{_identifier_for(slug)}.md",
        }
        for slug in ordered_slugs
    ] + preserved_paths

    components = data.get("components")
    if not isinstance(components, dict):
        raise ValueError("manifest components must be an object")
    docs = components.get("docs")
    if not isinstance(docs, dict) or not isinstance(docs.get("items"), list):
        raise ValueError("manifest docs items must be a list")
    docs["items"] = [
        item
        for item in docs["items"]
        if not isinstance(item, dict) or item.get("vendored_repo") != _REFERENCE_REPO
    ] + items

    rendered_manifest = json.dumps(data, indent=2, ensure_ascii=True) + "\n"
    skill_text = skill_path.read_text(encoding="utf-8")
    if _DESIGN_SECTION.search(skill_text) is None:
        raise ValueError("Generation Skill design items section is missing")
    rendered_skill = _DESIGN_SECTION.sub(skill_section, skill_text, count=1)
    drifted = (
        rendered_manifest != manifest_path.read_text(encoding="utf-8")
        or rendered_skill != skill_text
    )
    if check or not drifted:
        return drifted
    manifest_path.write_text(rendered_manifest, encoding="utf-8")
    skill_path.write_text(rendered_skill, encoding="utf-8")
    return True


def _reference_pin(data: dict[str, object]) -> tuple[str, str]:
    entry = _reference_entry(data)
    commit = entry.get("commit")
    if not isinstance(commit, str):
        raise ValueError(f"vendored entry for {_REFERENCE_REPO} has no commit")
    return _REFERENCE_REPO, commit


def _read_upstream_source(clone_dir: Path) -> tuple[tuple[str, ...], dict[str, str]]:
    design_root = clone_dir / _REFERENCE_ROOT
    slugs = tuple(
        path.parent.name
        for path in sorted(design_root.glob("*/DESIGN.md"), key=lambda path: path.parent.name)
    )
    if not slugs:
        raise ValueError("upstream design reference set is empty")
    headings: dict[str, str] = {}
    for slug in slugs:
        readme = design_root / slug / "README.md"
        if readme.is_file():
            headings[slug] = readme.read_text(encoding="utf-8").splitlines()[0]
    return slugs, headings


def clone_or_fetch(repo: str, commit: str, target_dir: Path) -> None:
    """Clone or refresh one GitHub repository and check out its pinned commit."""
    if (target_dir / ".git").is_dir():
        command = ["git", "fetch", "--depth=1", "origin", commit]
        cwd = target_dir
    else:
        target_dir.parent.mkdir(parents=True, exist_ok=True)
        command = [
            "git",
            "clone",
            "--filter=blob:none",
            "--no-checkout",
            f"https://github.com/{repo}.git",
            str(target_dir),
        ]
        cwd = None
    result = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git sync failed for {repo}: {result.stderr}")
    result = subprocess.run(
        ["git", "checkout", "--detach", commit],
        cwd=target_dir,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git checkout failed for {repo} at {commit}: {result.stderr}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Regenerate Design References or check them for drift."
    )
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    manifest_path = _REPO_ROOT / "src" / "dev_ready" / "manifest.json"
    skill_path = _REPO_ROOT / "skills" / "dev-ready" / "SKILL.md"
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        repo, commit = _reference_pin(data)
        clone_dir = _REPO_ROOT / ".sync-cache" / repo.replace("/", "_")
        clone_or_fetch(repo, commit, clone_dir)
        slugs, headings = _read_upstream_source(clone_dir)
        drifted = synchronize_outputs(
            manifest_path,
            skill_path,
            slugs,
            headings,
            check=args.check,
        )
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as error:
        print(f"Design Reference sync failed: {error}", file=sys.stderr)
        return 1
    if args.check and drifted:
        print("Design Reference drift detected", file=sys.stderr)
        return 1
    print("Design References are current" if not drifted else "Design References regenerated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
