"""Offline guard for the generated Flow Chain's user-invoked claim."""

from pathlib import Path

import pytest

_TEMPLATES_ROOT = (
    Path(__file__).resolve().parents[2] / "src" / "dev_ready" / "templates"
)
_VENDORED_USER_INVOKED_SKILLS = (
    "grill-with-docs",
    "to-spec",
    "to-tickets",
    "implement",
    "improve-codebase-architecture",
    "setup-matt-pocock-skills",
)


@pytest.mark.parametrize("skill_name", _VENDORED_USER_INVOKED_SKILLS)
def test_vendored_flow_step_remains_user_invoked(skill_name: str) -> None:
    source = _TEMPLATES_ROOT / "claude" / "skills" / skill_name / "SKILL.md"

    assert "disable-model-invocation: true" in _frontmatter(source).splitlines()


def test_setup_project_remains_user_invoked() -> None:
    source = _TEMPLATES_ROOT / "skills" / "setup-project" / "SKILL.md.tmpl"

    assert "disable-model-invocation: true" in _frontmatter(source).splitlines()


def _frontmatter(source: Path) -> str:
    text = source.read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"{source} has no YAML frontmatter"
    return text.split("---\n", 2)[1]
