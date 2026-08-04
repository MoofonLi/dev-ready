"""Offline tests for scripts/sync_agent_targets.py."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

_SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "sync_agent_targets.py"
_spec = importlib.util.spec_from_file_location("sync_agent_targets", _SCRIPT_PATH)
assert _spec is not None and _spec.loader is not None
sync_agent_targets = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sync_agent_targets)

SOURCE = """
import { join } from 'path';
export const agents: Record<AgentType, AgentConfig> = {
  'claude-code': {
    name: 'claude-code',
    skillsDir: '.claude/skills',
    globalSkillsDir: join(home, '.claude/skills'),
    detectInstalled: async () => true,
  },
  codex: {
    name: 'codex',
    skillsDir: '.agents/skills',
    globalSkillsDir: join(home, '.codex/skills'),
    detectInstalled: async () => {
      return true;
    },
  },
  qoder: {
    name: 'qoder',
    skillsDir: '.qoder/skills',
    globalSkillsDir: join(home, '.qoder/skills'),
    detectInstalled: async () => true,
  },
};
"""


def test_derivation_partitions_targets_and_standard_compliant_agents() -> None:
    targets, standard_agents = sync_agent_targets.derive_agent_targets(SOURCE)

    assert targets == {
        "claude": {"skills_dir": ".claude/skills"},
        "qoder": {"skills_dir": ".qoder/skills"},
    }
    assert standard_agents == ["codex"]
    assert "globalSkillsDir" not in json.dumps(targets)


def test_derivation_requires_the_declared_rename_source() -> None:
    with pytest.raises(ValueError, match="rename source.*claude-code"):
        sync_agent_targets.derive_agent_targets(
            SOURCE.replace("'claude-code':", "claude:").replace(
                "name: 'claude-code'", "name: 'claude'"
            )
        )


def test_derivation_requires_the_agent_collection() -> None:
    with pytest.raises(ValueError, match="agent collection"):
        sync_agent_targets.derive_agent_targets("export const somethingElse = {};")


def test_derivation_rejects_an_entry_without_a_skills_directory() -> None:
    with pytest.raises(ValueError, match="codex.*skillsDir"):
        sync_agent_targets.derive_agent_targets(
            SOURCE.replace("    skillsDir: '.agents/skills',\n", "")
        )


def test_derivation_rejects_a_non_literal_skills_directory() -> None:
    with pytest.raises(ValueError, match="codex.*string literal"):
        sync_agent_targets.derive_agent_targets(
            SOURCE.replace("skillsDir: '.agents/skills'", "skillsDir: join('.agents', 'skills')")
        )


def test_derivation_rejects_an_entry_without_an_identifier() -> None:
    with pytest.raises(ValueError, match="identifier"):
        sync_agent_targets.derive_agent_targets(
            SOURCE.replace("  codex: {", "  [dynamicAgent]: {")
        )


def test_derivation_rejects_an_identified_entry_that_is_not_an_object() -> None:
    with pytest.raises(ValueError, match="codex.*object literal"):
        sync_agent_targets.derive_agent_targets(
            SOURCE.replace("  codex: {", "  codex: null,\n  codex_body: {")
        )


def test_derivation_rejects_an_identifier_outside_the_manifest_pattern() -> None:
    with pytest.raises(ValueError, match="identifier.*manifest pattern"):
        sync_agent_targets.derive_agent_targets(SOURCE.replace("  codex: {", "  'bad id': {"))


def test_regenerate_preserves_hand_declared_paths_and_check_detects_drift(
    tmp_path: Path,
) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "agent_targets": {
                    "claude": {
                        "skills_dir": ".old/skills",
                        "rules_file": "CLAUDE.md",
                        "mcp_file": ".mcp.json",
                    }
                },
                "standard_compliant_agents": [],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    assert sync_agent_targets.synchronize_manifest(manifest_path, SOURCE, check=False) is True
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert data["agent_targets"]["claude"] == {
        "skills_dir": ".claude/skills",
        "rules_file": "CLAUDE.md",
        "mcp_file": ".mcp.json",
    }
    assert data["standard_compliant_agents"] == ["codex"]
    assert sync_agent_targets.synchronize_manifest(manifest_path, SOURCE, check=True) is False

    drifted = SOURCE.replace(".qoder/skills", ".qoder/new-skills")
    assert sync_agent_targets.synchronize_manifest(manifest_path, drifted, check=True) is True
