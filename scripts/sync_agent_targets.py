#!/usr/bin/env python3
"""Derive the Agent Target Map from the pinned reference installer."""

from __future__ import annotations

import argparse
import ast
import copy
import json
import re
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_REFERENCE_REPO = "vercel-labs/skills"
_REFERENCE_SOURCE = Path("src/agents.ts")
_CANONICAL_SKILLS_DIR = ".agents/skills"
_ID_RENAMES = {"claude-code": "claude"}
_IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9-]*$")
_AGENT_COLLECTION = re.compile(
    r"export\s+const\s+agents\b[^=]*=\s*\{",
    re.MULTILINE,
)
_PROPERTY = re.compile(
    r"(?P<key>'(?:\\.|[^'])*'|\"(?:\\.|[^\"])*\"|[A-Za-z_$][A-Za-z0-9_$-]*)"
    r"\s*:\s*(?P<value>.*)\Z",
    re.DOTALL,
)


def derive_agent_targets(
    source_text: str,
) -> tuple[dict[str, dict[str, str]], list[str]]:
    """Return derived Agent Targets and standard-compliant ids from source text."""
    parsed_agents = _parse_upstream_agents(source_text)
    upstream_ids = {identifier for identifier, _ in parsed_agents}
    missing_renames = sorted(set(_ID_RENAMES) - upstream_ids)
    if missing_renames:
        raise ValueError(
            "declared identifier rename source is missing: " + ", ".join(missing_renames)
        )

    targets: dict[str, dict[str, str]] = {}
    standard_agents: list[str] = []
    for upstream_id, skills_dir in parsed_agents:
        identifier = _ID_RENAMES.get(upstream_id, upstream_id)
        if skills_dir == _CANONICAL_SKILLS_DIR:
            standard_agents.append(identifier)
        else:
            targets[identifier] = {"skills_dir": skills_dir}
    return targets, standard_agents


def _parse_upstream_agents(source_text: str) -> list[tuple[str, str]]:
    """Parse upstream Agent identifiers and literal project skills directories."""
    collection_match = _AGENT_COLLECTION.search(source_text)
    if collection_match is None:
        raise ValueError("upstream agent collection is missing")
    opening = collection_match.end() - 1
    closing = _matching_delimiter(source_text, opening, "{", "}")
    entries = _split_top_level(source_text[opening + 1 : closing])
    if not entries:
        raise ValueError("upstream agent collection is empty")

    parsed: list[tuple[str, str]] = []
    for entry in entries:
        try:
            upstream_id, raw_entry = _parse_property(entry)
        except ValueError as error:
            raise ValueError("upstream agent entry cannot be attributed to an identifier") from error
        if not _IDENTIFIER.fullmatch(upstream_id):
            raise ValueError(
                f"upstream agent identifier {upstream_id!r} does not match the manifest pattern"
            )
        entry_text = raw_entry.strip()
        if not entry_text.startswith("{") or not entry_text.endswith("}"):
            raise ValueError(f"upstream agent {upstream_id!r} must be an object literal")

        fields: dict[str, str] = {}
        for field_text in _split_top_level(entry_text[1:-1]):
            try:
                field, value = _parse_property(field_text)
            except ValueError as error:
                raise ValueError(
                    f"upstream agent {upstream_id!r} contains an unrecognized field"
                ) from error
            fields[field] = value.strip()
        if "skillsDir" not in fields:
            raise ValueError(f"upstream agent {upstream_id!r} has no skillsDir")
        skills_dir = _string_literal(fields["skillsDir"], upstream_id)
        parsed.append((upstream_id, skills_dir))
    return parsed


def synchronize_manifest(
    manifest_path: Path,
    source_text: str,
    *,
    check: bool,
) -> bool:
    """Regenerate derived manifest structures, or return whether check mode finds drift."""
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    targets, standard_agents = derive_agent_targets(source_text)
    existing_targets = data.get("agent_targets", {})
    if not isinstance(existing_targets, dict):
        raise ValueError("manifest agent_targets must be an object")

    for target_id, target in targets.items():
        existing = existing_targets.get(target_id, {})
        if not isinstance(existing, dict):
            raise ValueError(f"manifest Agent Target {target_id!r} must be an object")
        for field in ("rules_file", "mcp_file"):
            value = existing.get(field)
            if value is not None:
                target[field] = value

    drifted = (
        data.get("agent_targets") != targets
        or data.get("standard_compliant_agents") != standard_agents
    )
    if check or not drifted:
        return drifted

    updated = copy.deepcopy(data)
    updated["agent_targets"] = targets
    updated["standard_compliant_agents"] = standard_agents
    manifest_path.write_text(
        json.dumps(updated, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    return True


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


def _reference_pin(data: dict[str, object]) -> tuple[str, str]:
    vendored = data.get("vendored")
    if not isinstance(vendored, list):
        raise ValueError("manifest vendored provenance must be a list")
    for entry in vendored:
        if isinstance(entry, dict) and entry.get("repo") == _REFERENCE_REPO:
            commit = entry.get("commit")
            if not isinstance(commit, str):
                raise ValueError(f"vendored entry for {_REFERENCE_REPO} has no commit")
            return _REFERENCE_REPO, commit
    raise ValueError(f"manifest has no vendored entry for {_REFERENCE_REPO}")


def _parse_property(text: str) -> tuple[str, str]:
    match = _PROPERTY.fullmatch(_remove_comments(text).strip())
    if match is None:
        raise ValueError("not a property")
    return _property_key(match.group("key")), match.group("value")


def _property_key(raw: str) -> str:
    if raw.startswith(("'", '"')):
        value = ast.literal_eval(raw)
        if not isinstance(value, str) or not value:
            raise ValueError("invalid property identifier")
        return value
    return raw


def _string_literal(raw: str, identifier: str) -> str:
    try:
        value = ast.literal_eval(raw)
    except (SyntaxError, ValueError) as error:
        raise ValueError(
            f"upstream agent {identifier!r} skillsDir must be a string literal"
        ) from error
    if not isinstance(value, str) or not value:
        raise ValueError(
            f"upstream agent {identifier!r} skillsDir must be a string literal"
        )
    return value


def _remove_comments(text: str) -> str:
    return "".join(
        character if state not in {"line_comment", "block_comment"} else " "
        for _, character, state in _lex(text)
    )


def _matching_delimiter(text: str, opening: int, opener: str, closer: str) -> int:
    depth = 0
    for index, character, state in _lex(text, opening):
        if state != "code":
            continue
        if character == opener:
            depth += 1
        elif character == closer:
            depth -= 1
            if depth == 0:
                return index
    raise ValueError("upstream agent collection has an unterminated object")


def _split_top_level(text: str) -> list[str]:
    segments: list[str] = []
    start = 0
    depths = {"{": 0, "(": 0, "[": 0}
    closing = {"}": "{", ")": "(", "]": "["}
    for index, character, state in _lex(text):
        if state != "code":
            continue
        if character in depths:
            depths[character] += 1
        elif character in closing:
            depths[closing[character]] -= 1
        elif character == "," and all(depth == 0 for depth in depths.values()):
            segment = text[start:index].strip()
            if segment:
                segments.append(segment)
            start = index + 1
    tail = text[start:].strip()
    if tail:
        segments.append(tail)
    return segments


def _lex(text: str, start: int = 0):
    state = "code"
    quote = ""
    escaped = False
    index = start
    while index < len(text):
        character = text[index]
        next_character = text[index + 1] if index + 1 < len(text) else ""
        if state == "string":
            yield index, character, state
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == quote:
                state = "code"
        elif state == "line_comment":
            yield index, character, state
            if character == "\n":
                state = "code"
        elif state == "block_comment":
            yield index, character, state
            if character == "*" and next_character == "/":
                yield index + 1, next_character, state
                index += 1
                state = "code"
        elif character in {"'", '"', "`"}:
            quote = character
            state = "string"
            yield index, character, state
        elif character == "/" and next_character == "/":
            state = "line_comment"
            yield index, character, state
            yield index + 1, next_character, state
            index += 1
        elif character == "/" and next_character == "*":
            state = "block_comment"
            yield index, character, state
            yield index + 1, next_character, state
            index += 1
        else:
            yield index, character, state
        index += 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Regenerate the Agent Target Map or check it for drift."
    )
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    manifest_path = _REPO_ROOT / "src" / "dev_ready" / "manifest.json"
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        repo, commit = _reference_pin(data)
        clone_dir = _REPO_ROOT / ".sync-cache" / repo.replace("/", "_")
        clone_or_fetch(repo, commit, clone_dir)
        source_text = (clone_dir / _REFERENCE_SOURCE).read_text(encoding="utf-8")
        drifted = synchronize_manifest(manifest_path, source_text, check=args.check)
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as error:
        print(f"Agent Target sync failed: {error}", file=sys.stderr)
        return 1
    if args.check and drifted:
        print("Agent Target Map drift detected", file=sys.stderr)
        return 1
    print("Agent Target Map is current" if not drifted else "Agent Target Map regenerated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
