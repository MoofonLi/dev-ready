"""Cross-release lifecycle gate from the exact released N-1 artifact."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, NamedTuple

import pytest

from dev_ready.agent_targets import CANONICAL_SKILLS_ROOT, project_targets
from dev_ready.manifest import load_default_manifest

pytestmark = pytest.mark.network

_RELEASED_VERSION = "0.9.0"
_REPO_ROOT = Path(__file__).resolve().parents[2]
_PROBE_PREFIX = "__DEV_READY_PROBE__="
_PROBE_AND_RUN = f"""
import json
import sys

import dev_ready
from dev_ready.cli import main

print({_PROBE_PREFIX!r} + json.dumps({{
    "version": dev_ready.__version__,
    "origin": dev_ready.__file__,
}}), flush=True)
raise SystemExit(main(sys.argv[1:]))
"""


class BaseProvenance(NamedTuple):
    repo: str
    commit: str


class OverlayCurrency(NamedTuple):
    dev_ready_version: Any
    components: Any
    inventory: Any


def _isolated_environment() -> dict[str, str]:
    environment = os.environ.copy()
    for name in ("PYTHONHOME", "PYTHONPATH", "VIRTUAL_ENV"):
        environment.pop(name, None)
    environment["PYTHONNOUSERSITE"] = "1"
    return environment


def _run_stage(
    stage: str,
    command: list[str],
    *,
    cwd: Path,
    expected_exit_codes: frozenset[int] = frozenset({0}),
    environment_overrides: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    environment = _isolated_environment()
    environment.update(environment_overrides or {})
    result = subprocess.run(
        command,
        cwd=cwd,
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=15 * 60,
        check=False,
    )
    print(f"[{stage}] command: {subprocess.list2cmdline(command)}")
    print(f"[{stage}] exit: {result.returncode}")
    if result.stdout:
        print(f"[{stage}] stdout:\n{result.stdout}", end="")
    if result.stderr:
        print(f"[{stage}] stderr:\n{result.stderr}", end="")
    assert result.returncode in expected_exit_codes, (
        f"{stage} failed with exit {result.returncode}\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )
    return result


def _probe(result: subprocess.CompletedProcess[str], stage: str) -> dict[str, str]:
    probe_lines = [
        line.removeprefix(_PROBE_PREFIX)
        for line in result.stdout.splitlines()
        if line.startswith(_PROBE_PREFIX)
    ]
    assert len(probe_lines) == 1, f"{stage} did not report exactly one package origin"
    probe = json.loads(probe_lines[0])
    assert isinstance(probe, dict), f"{stage} emitted an invalid origin probe"
    assert isinstance(probe.get("version"), str), f"{stage} did not report a version"
    assert isinstance(probe.get("origin"), str), f"{stage} did not report a module origin"
    return probe


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _checkout_stage(
    stage: str,
    arguments: list[str],
    *,
    cwd: Path,
    expected_exit_codes: frozenset[int] = frozenset({0}),
) -> tuple[subprocess.CompletedProcess[str], dict[str, str]]:
    result = _run_stage(
        stage,
        [sys.executable, "-c", _PROBE_AND_RUN, *arguments],
        cwd=cwd,
        expected_exit_codes=expected_exit_codes,
        environment_overrides={"PYTHONPATH": str(_REPO_ROOT / "src")},
    )
    probe = _probe(result, stage)
    assert _is_within(Path(probe["origin"]), _REPO_ROOT / "src"), (
        f"{stage} did not import the working tree: {probe['origin']}"
    )
    return result, probe


def _snapshot(root: Path) -> dict[str, tuple[str, bytes]]:
    """Capture names, kinds, links, and every file byte beneath ``root``."""
    snapshot: dict[str, tuple[str, bytes]] = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            snapshot[relative] = ("symlink", os.readlink(path).encode("utf-8"))
        elif path.is_dir():
            snapshot[relative] = ("directory", b"")
        else:
            snapshot[relative] = ("file", path.read_bytes())
    return snapshot


def _changed_paths(
    before: dict[str, tuple[str, bytes]], after: dict[str, tuple[str, bytes]]
) -> set[str]:
    return {
        path
        for path in before.keys() | after.keys()
        if before.get(path) != after.get(path)
    }


def _load_stamp(target: Path, stage: str) -> dict[str, Any]:
    try:
        stamp = json.loads((target / ".dev-ready.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        pytest.fail(f"{stage} left an unreadable generation stamp: {error}")
    assert isinstance(stamp, dict), f"{stage} stamp root is not an object"
    return stamp


def _assert_skill_projection(
    root: Path, stamp: dict[str, Any], skill_name: str, stage: str
) -> None:
    agent_target_ids = stamp.get("agent_targets")
    assert isinstance(agent_target_ids, list) and all(
        isinstance(target_id, str) for target_id in agent_target_ids
    ), f"{stage} stamp has invalid Agent Target selection"
    catalog = load_default_manifest().components
    projection = project_targets(catalog, agent_target_ids)
    canonical_skill = root.joinpath(*CANONICAL_SKILLS_ROOT, skill_name, "SKILL.md")
    assert canonical_skill.is_file(), f"{stage} omitted canonical {skill_name} content"
    for target in projection.targets:
        pointer_stub = root / projection.stub_path(target, skill_name)
        assert pointer_stub.is_file(), (
            f"{stage} omitted the {target.id} {skill_name} Pointer Stub"
        )
        assert canonical_skill.read_bytes() != pointer_stub.read_bytes(), (
            f"{stage} duplicated canonical {skill_name} bytes into {target.id}"
        )


def _json_report(result: subprocess.CompletedProcess[str], stage: str) -> dict[str, Any]:
    decoder = json.JSONDecoder()
    for stream in (result.stdout, result.stderr):
        report_stream = "\n".join(
            line for line in stream.splitlines() if not line.startswith(_PROBE_PREFIX)
        )
        object_start = report_stream.find("{")
        if object_start == -1:
            continue
        try:
            report, _ = decoder.raw_decode(report_stream[object_start:])
        except json.JSONDecodeError:
            continue
        assert isinstance(report, dict), f"{stage} JSON report root is not an object"
        return report
    pytest.fail(f"{stage} did not emit a parseable JSON report")


def _selection_arguments(stamp: dict[str, Any]) -> list[str]:
    components = stamp.get("components")
    assert isinstance(components, dict), "released stamp has no component selection"
    manifest = load_default_manifest()
    items_by_id = {
        item.id: item
        for component_items in manifest.components.values()
        for item in component_items
    }
    selected_by_category: dict[str, set[str]] = {}
    for component in ("skills", "mcp", "docs"):
        selected = components.get(component)
        assert isinstance(selected, dict), f"released stamp has no {component} selection"
        items = selected.get("items")
        assert isinstance(items, list), f"released stamp has invalid {component} items"
        item_ids = [entry.get("id") if isinstance(entry, dict) else entry for entry in items]
        assert all(isinstance(item_id, str) for item_id in item_ids), (
            f"released stamp has an invalid {component} item id"
        )
        if selected.get("included"):
            for item_id in item_ids:
                item = items_by_id.get(item_id)
                if item is not None and item.kind != "development-loop":
                    selected_by_category.setdefault(item.category, set()).add(item.id)

    categories = sorted(selected_by_category)
    arguments: list[str] = []
    if categories:
        arguments.extend(("--categories", ",".join(categories)))
        for category in categories:
            arguments.extend(
                (f"--{category}", ",".join(sorted(selected_by_category[category])))
            )
    elif not components["docs"].get("included"):
        arguments.extend(("--categories", "none"))
    agent_targets = stamp.get("agent_targets", ["claude"])
    assert isinstance(agent_targets, list) and all(
        isinstance(target_id, str) for target_id in agent_targets
    ), "released stamp has invalid Agent Target selection"
    if set(agent_targets) != set(manifest.agent_targets):
        arguments.extend(("--agents", ",".join(agent_targets) or "none"))
    return arguments


def _inventory_paths(stamp: dict[str, Any], stage: str) -> set[str]:
    inventory = stamp.get("inventory")
    assert isinstance(inventory, list), f"{stage} stamp has no managed-file inventory"
    paths: set[str] = set()
    for entry in inventory:
        assert isinstance(entry, dict), f"{stage} stamp has an invalid inventory entry"
        path = entry.get("path")
        assert isinstance(path, str), f"{stage} stamp inventory entry has no path"
        paths.add(path)
    return paths


def _managed_paths_with_parents(paths: set[str]) -> set[str]:
    managed = set(paths)
    for path in paths:
        parent = Path(path).parent
        while parent != Path("."):
            managed.add(parent.as_posix())
            parent = parent.parent
    return managed


def _base_provenance(stamp: dict[str, Any], stage: str) -> BaseProvenance:
    upstream = stamp.get("upstream")
    assert isinstance(upstream, dict), f"{stage} stamp has no upstream provenance"
    repo = upstream.get("repo")
    commit = upstream.get("commit")
    assert isinstance(repo, str), f"{stage} stamp has no upstream repository"
    assert isinstance(commit, str), f"{stage} stamp has no upstream commit"
    return BaseProvenance(repo=repo, commit=commit)


def _overlay_currency(stamp: dict[str, Any]) -> OverlayCurrency:
    return OverlayCurrency(
        dev_ready_version=stamp.get("dev_ready_version"),
        components=stamp.get("components"),
        inventory=stamp.get("inventory"),
    )


def test_upgrade_from_released_n_minus_one(tmp_path: Path) -> None:
    uv = shutil.which("uv")
    assert uv is not None, "old generation requires uv to create an isolated release environment"
    target = tmp_path / "released-project"
    released = _run_stage(
        "old generation",
        [
            uv,
            "run",
            "--isolated",
            "--no-project",
            "--with",
            f"dev-ready=={_RELEASED_VERSION}",
            "python",
            "-c",
            _PROBE_AND_RUN,
            "init",
            "released-project",
            "--yes",
            "--dir",
            str(target),
        ],
        cwd=tmp_path,
    )

    released_probe = _probe(released, "old generation")
    assert released_probe["version"] == _RELEASED_VERSION, (
        "old generation resolved the wrong dev-ready release"
    )
    assert not _is_within(Path(released_probe["origin"]), _REPO_ROOT), (
        "old generation imported the checkout instead of the isolated released artifact"
    )
    assert (target / ".dev-ready.json").is_file(), "old generation did not write its stamp"
    assert (target / "backend").is_dir(), "old generation omitted the backend application"
    assert (target / "frontend").is_dir(), "old generation omitted the frontend application"
    assert (target / "AGENTS.md").is_file(), "released project omitted canonical rules"
    assert (target / "CLAUDE.md").read_text(encoding="utf-8") == "@AGENTS.md\n", (
        "released project omitted the Claude rules pointer"
    )
    old_stamp = _load_stamp(target, "old generation")
    _assert_skill_projection(target, old_stamp, "implement", "released project")

    before_upgrade = _snapshot(target)
    old_provenance = _base_provenance(old_stamp, "old generation")

    reference_target = tmp_path / "checkout-reference"
    _, reference_probe = _checkout_stage(
        "checkout reference generation",
        [
            "init",
            "released-project",
            "--yes",
            "--dir",
            str(reference_target),
            *_selection_arguments(old_stamp),
        ],
        cwd=tmp_path,
    )
    reference_stamp = _load_stamp(reference_target, "checkout reference generation")
    reference_provenance = _base_provenance(
        reference_stamp, "checkout reference generation"
    )

    pre_check, _ = _checkout_stage(
        "pre-upgrade check",
        ["check", str(target), "--json"],
        cwd=tmp_path,
        expected_exit_codes=frozenset({0, 7}),
    )
    pre_check_report = _json_report(pre_check, "pre-upgrade check")
    if pre_check.returncode == 0:
        assert pre_check_report.get("clean") is True, (
            "pre-upgrade check exited 0 without reporting a clean project"
        )
        assert pre_check_report.get("drifts") == [], (
            "pre-upgrade check exited 0 while reporting drift"
        )
    else:
        drifts = pre_check_report.get("drifts")
        assert isinstance(drifts, list) and drifts, (
            "pre-upgrade check exited 7 without reporting drift evidence"
        )
        allowed_overlay_drift = (
            "overlay currency",
            "overlay version drift",
            "dev-ready version",
            "skills pin drift",
            "mcp pin drift",
            "removed catalog item",
            "missing required path",
            "missing overlay file",
            "missing item path",
            "missing agent target artifact",
        )
        unexpected_drifts = [
            drift
            for drift in drifts
            if not isinstance(drift, str)
            or not any(category in drift.casefold() for category in allowed_overlay_drift)
        ]
        assert not unexpected_drifts, (
            "pre-upgrade check reported non-overlay drift: " + repr(unexpected_drifts)
        )

    dry_run_result, _ = _checkout_stage(
        "dry-run upgrade",
        ["upgrade", str(target), "--dry-run"],
        cwd=tmp_path,
    )
    assert _snapshot(target) == before_upgrade, "dry-run upgrade mutated generated project bytes"

    _, checkout_probe = _checkout_stage(
        "real upgrade",
        ["upgrade", str(target)],
        cwd=tmp_path,
    )
    after_upgrade = _snapshot(target)
    new_stamp = _load_stamp(target, "real upgrade")

    assert (target / "AGENTS.md").is_file(), "upgrade omitted canonical rules"
    assert (target / "CLAUDE.md").read_text(encoding="utf-8") == "@AGENTS.md\n", (
        "upgrade omitted the Claude rules pointer"
    )
    _assert_skill_projection(target, new_stamp, "implement", "upgrade")
    for path in target.rglob("*"):
        assert not path.is_symlink(), f"upgrade produced a symbolic link: {path}"
    assert new_stamp.get("stamp_version") == 5, "upgrade changed the stamp format version"
    assert new_stamp.get("categories") == old_stamp.get("categories"), (
        "upgrade changed the released project's Categories"
    )
    assert new_stamp.get("development_loop") == old_stamp.get("development_loop"), (
        "upgrade changed the released project's development loop"
    )
    components = new_stamp.get("components")
    assert isinstance(components, dict) and "handoff" not in components, (
        "upgrade retained the retired Handoff component state"
    )
    assert new_stamp.get("agent_targets") == old_stamp.get("agent_targets"), (
        "upgrade changed the released project's Agent Target selection"
    )

    old_managed_files = _inventory_paths(old_stamp, "old generation")
    new_managed_files = _inventory_paths(new_stamp, "real upgrade")
    # Creating or deleting a managed file may necessarily create or remove its
    # otherwise-empty parent directories; directories contain no application bytes.
    old_managed_paths = _managed_paths_with_parents(old_managed_files)
    new_managed_paths = _managed_paths_with_parents(new_managed_files)
    unexpected_changes = {
        path
        for path in _changed_paths(before_upgrade, after_upgrade)
        if path != ".dev-ready.json"
        and not (
            path in old_managed_paths
            or path not in before_upgrade
            and path in new_managed_paths
        )
    }
    assert not unexpected_changes, (
        "real upgrade changed non-overlay application paths: "
        + ", ".join(sorted(unexpected_changes))
    )
    assert _base_provenance(new_stamp, "real upgrade") == old_provenance, (
        "real upgrade changed immutable Base Provenance"
    )
    assert checkout_probe["version"] == reference_probe["version"], (
        "checkout lifecycle commands and reference generation resolved different versions"
    )
    assert new_stamp.get("dev_ready_version") == checkout_probe["version"], (
        "real upgrade did not record the checkout's Overlay Currency"
    )
    assert _overlay_currency(new_stamp) == _overlay_currency(reference_stamp), (
        "real upgrade did not install the checkout's version, selected-item pins, "
        "and managed-file inventory"
    )

    post_check, _ = _checkout_stage(
        "post-upgrade check",
        ["check", str(target), "--json"],
        cwd=tmp_path,
    )
    post_check_report = _json_report(post_check, "post-upgrade check")
    assert post_check_report.get("clean") is True, "post-upgrade check did not report clean"
    if reference_provenance != old_provenance:
        assert "advis" in json.dumps(post_check_report).casefold(), (
            "post-upgrade check suppressed the available newer-base advisory"
        )

    before_repeat = _snapshot(target)
    stamp_mtime_before_repeat = (target / ".dev-ready.json").stat().st_mtime_ns
    idempotence_result, _ = _checkout_stage(
        "idempotence dry run",
        ["upgrade", str(target), "--dry-run"],
        cwd=tmp_path,
    )
    planned_actions = [
        line
        for line in idempotence_result.stdout.splitlines()
        if line.strip().casefold().startswith("- would ")
    ]
    assert not planned_actions, (
        "second upgrade still planned file changes:\n" + "\n".join(planned_actions)
    )
    assert _snapshot(target) == before_repeat, "idempotence dry run mutated the upgraded project"
    action_counts = {
        label.casefold(): int(count)
        for label, count in re.findall(
            r"^(Upgraded|Added|Deleted|Removed) \((\d+)\):$",
            idempotence_result.stdout,
            flags=re.MULTILINE,
        )
    }
    assert action_counts and not any(action_counts.values()), (
        "second upgrade reported a nonzero action plan: " + repr(action_counts)
    )
    assert "No changes were needed." in idempotence_result.stdout

    _checkout_stage(
        "idempotence real upgrade",
        ["upgrade", str(target)],
        cwd=tmp_path,
    )
    assert _snapshot(target) == before_repeat, "second real upgrade changed project bytes"
    assert (target / ".dev-ready.json").stat().st_mtime_ns == stamp_mtime_before_repeat, (
        "second real upgrade rewrote the stamp despite an empty plan"
    )
