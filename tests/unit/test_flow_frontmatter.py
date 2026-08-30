"""Offline guard for the generated Flow Chain's user/model invocation claims."""

from __future__ import annotations

from pathlib import Path

import pytest

from dev_ready.manifest import CatalogItem, ItemPath, load_default_manifest

_TEMPLATES_ROOT = (
    Path(__file__).resolve().parents[2] / "src" / "dev_ready" / "templates"
)


def _frontmatter(source: Path) -> str:
    text = source.read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"{source} has no YAML frontmatter"
    return text.split("---\n", 2)[1]


def _flatten_chain(chain: tuple[str | tuple[str, ...], ...]) -> tuple[str, ...]:
    flat: list[str] = []
    for entry in chain:
        if isinstance(entry, str):
            flat.append(entry)
        else:
            flat.extend(entry)
    return tuple(flat)


def _step_skill_path(
    loop: CatalogItem, step: str, templates_root: Path = _TEMPLATES_ROOT
) -> Path:
    item_path = next(path for path in loop.paths if Path(path.dest).name == step)
    source = templates_root / item_path.src
    assert source.is_dir(), f"step source {item_path.src!r} does not exist"
    return source / "SKILL.md"


def check_flow_invocation(
    loop: CatalogItem, templates_root: Path = _TEMPLATES_ROOT
) -> None:
    """Assert that a development loop's shipped skill files match its declared invocation model."""
    if loop.invocation == "user":
        for step in _flatten_chain(loop.chain):
            source = _step_skill_path(loop, step, templates_root)
            lines = _frontmatter(source).splitlines()
            assert (
                "disable-model-invocation: true" in lines
            ), f"user-invoked loop {loop.id!r} chain step {step!r} must carry 'disable-model-invocation: true'"
    elif loop.invocation == "model":
        for step in loop.steps:
            source = _step_skill_path(loop, step, templates_root)
            lines = _frontmatter(source).splitlines()
            assert (
                "disable-model-invocation: true" not in lines
            ), f"model-invoked loop {loop.id!r} step {step!r} must not carry 'disable-model-invocation: true'"


def test_default_manifest_flows_satisfy_invocation_invariants() -> None:
    manifest = load_default_manifest()
    loops = manifest.components.loops()
    assert len(loops) >= 1
    for loop in loops:
        check_flow_invocation(loop)


def test_superpowers_shipped_skills_satisfy_model_invocation_invariant() -> None:
    superpowers_steps = (
        "brainstorming",
        "dispatching-parallel-agents",
        "executing-plans",
        "finishing-a-development-branch",
        "receiving-code-review",
        "requesting-code-review",
        "subagent-driven-development",
        "systematic-debugging",
        "test-driven-development",
        "using-git-worktrees",
        "verification-before-completion",
        "writing-plans",
    )
    loop = CatalogItem(
        id="superpowers",
        category="dev",
        kind="development-loop",
        description="Obra's Superpowers.",
        mode="vendor",
        license="MIT",
        vendored_repo="obra/superpowers",
        steps=superpowers_steps,
        paths=tuple(
            ItemPath(src=f"claude/skills/{s}", dest=f".agents/skills/{s}")
            for s in superpowers_steps
        ),
        invocation="model",
        chain=(
            "brainstorming",
            "using-git-worktrees",
            "writing-plans",
            ("subagent-driven-development", "executing-plans"),
            "test-driven-development",
            "requesting-code-review",
            "finishing-a-development-branch",
        ),
    )
    check_flow_invocation(loop)


def test_setup_project_remains_user_invoked() -> None:
    source = _TEMPLATES_ROOT / "skills" / "setup-project" / "SKILL.md.tmpl"
    assert "disable-model-invocation: true" in _frontmatter(source).splitlines()


def test_user_invoked_flow_fails_when_chain_entry_is_missing_flag(
    tmp_path: Path,
) -> None:
    skill_dir = tmp_path / "claude" / "skills" / "step-a"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: step-a\n---\nBody\n", encoding="utf-8"
    )

    loop = CatalogItem(
        id="test-loop",
        category="dev",
        kind="development-loop",
        description="Test loop.",
        mode="builtin",
        license="MIT",
        steps=("step-a",),
        paths=(ItemPath(src="claude/skills/step-a", dest=".agents/skills/step-a"),),
        invocation="user",
        chain=("step-a",),
    )

    with pytest.raises(
        AssertionError,
        match="chain step 'step-a' must carry 'disable-model-invocation: true'",
    ):
        check_flow_invocation(loop, templates_root=tmp_path)


def test_user_invoked_flow_ignores_non_chain_step_missing_flag(
    tmp_path: Path,
) -> None:
    for name in ("step-chain", "step-tool"):
        skill_dir = tmp_path / "claude" / "skills" / name
        skill_dir.mkdir(parents=True)
        flag = "disable-model-invocation: true\n" if name == "step-chain" else ""
        (skill_dir / "SKILL.md").write_text(
            f"---\nname: {name}\n{flag}---\nBody\n", encoding="utf-8"
        )

    loop = CatalogItem(
        id="test-loop",
        category="dev",
        kind="development-loop",
        description="Test loop.",
        mode="builtin",
        license="MIT",
        steps=("step-chain", "step-tool"),
        paths=(
            ItemPath(src="claude/skills/step-chain", dest=".agents/skills/step-chain"),
            ItemPath(src="claude/skills/step-tool", dest=".agents/skills/step-tool"),
        ),
        invocation="user",
        chain=("step-chain",),
    )

    check_flow_invocation(loop, templates_root=tmp_path)


def test_flow_resolves_step_source_from_its_paths_entry(tmp_path: Path) -> None:
    skill_dir = tmp_path / "claude" / "skills" / "qualified-step-source"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: step-chain\ndisable-model-invocation: true\n---\nBody\n",
        encoding="utf-8",
    )

    loop = CatalogItem(
        id="test-loop",
        category="dev",
        kind="development-loop",
        description="Test loop.",
        mode="builtin",
        license="MIT",
        steps=("step-chain",),
        paths=(
            ItemPath(
                src="claude/skills/qualified-step-source",
                dest=".agents/skills/step-chain",
            ),
        ),
        invocation="user",
        chain=("step-chain",),
    )

    check_flow_invocation(loop, templates_root=tmp_path)


def test_flow_fails_loudly_when_declared_step_source_is_missing(
    tmp_path: Path,
) -> None:
    missing_source = "claude/skills/missing-step-source"
    loop = CatalogItem(
        id="test-loop",
        category="dev",
        kind="development-loop",
        description="Test loop.",
        mode="builtin",
        license="MIT",
        steps=("step-chain",),
        paths=(
            ItemPath(src=missing_source, dest=".agents/skills/step-chain"),
        ),
        invocation="user",
        chain=("step-chain",),
    )

    with pytest.raises(AssertionError, match=missing_source):
        check_flow_invocation(loop, templates_root=tmp_path)


def test_model_invoked_flow_fails_when_any_step_carries_flag(
    tmp_path: Path,
) -> None:
    skill_dir = tmp_path / "claude" / "skills" / "step-b"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: step-b\ndisable-model-invocation: true\n---\nBody\n",
        encoding="utf-8",
    )

    loop = CatalogItem(
        id="test-loop",
        category="dev",
        kind="development-loop",
        description="Test loop.",
        mode="builtin",
        license="MIT",
        steps=("step-b",),
        paths=(ItemPath(src="claude/skills/step-b", dest=".agents/skills/step-b"),),
        invocation="model",
        chain=("step-b",),
    )

    with pytest.raises(
        AssertionError,
        match="step 'step-b' must not carry 'disable-model-invocation: true'",
    ):
        check_flow_invocation(loop, templates_root=tmp_path)
