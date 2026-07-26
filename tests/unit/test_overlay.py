"""Unit tests for dev_ready.overlay (no network, filesystem confined to tmp_path)."""

from pathlib import Path
import hashlib

import pytest

import json

from dev_ready import __version__
from dev_ready.errors import InvalidArgumentsError, OverlayError
from dev_ready.manifest import AgentTarget, ComponentCatalog, UpstreamPin, load_default_manifest
from dev_ready.overlay import apply_overlay, render_stamp
from dev_ready.prompts import Answers, ProjectSelection

CATALOG = load_default_manifest().components
PIN = UpstreamPin(
    repo="fastapi/full-stack-fastapi-template",
    ref="master",
    commit="4cd0d9e51aebd1af6f82d91ad0df4c9e41f4dea2",
    license="MIT",
)


def _answers(
    tmp_path: Path,
    *,
    project_name: str = "my-app",
    include_skills: bool = True,
    include_mcp: bool = True,
    include_docs: bool = True,
    include_handoff: bool = True,
    skills_items: frozenset[str] = frozenset({"project-orientation"}),
    mcp_items: frozenset[str] = frozenset({"mcp-config"}),
    agent_targets: frozenset[str] | None = None,
) -> Answers:
    return Answers(
        project_name=project_name,
        target_dir=tmp_path / "my-app",
        selection=ProjectSelection.from_items(
            CATALOG,
            skills=skills_items if include_skills else frozenset(),
            mcp=mcp_items if include_mcp else frozenset(),
            agent_targets=agent_targets,
            docs=include_docs,
            handoff=include_handoff,
        ),
    )



def test_happy_path_writes_every_component_with_substitution(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    written = apply_overlay(_answers(tmp_path), project_dir, CATALOG, PIN)



    assert (project_dir / "AGENTS.md").exists()
    assert (project_dir / "CLAUDE.md").exists()
    assert (project_dir / "README.md").exists()
    assert (project_dir / ".agents" / "skills" / "project-orientation" / "SKILL.md").exists()
    assert (project_dir / ".claude" / "skills" / "project-orientation" / "SKILL.md").exists()
    assert (project_dir / ".windsurf" / "skills" / "project-orientation" / "SKILL.md").exists()
    assert (project_dir / ".mcp.json").exists()
    assert (project_dir / "docs" / "architecture.md").exists()
    assert (project_dir / "docs" / "requirements.md").exists()
    assert (project_dir / "docs" / "handoffs" / "README.md").exists()
    assert (project_dir / "docs" / "handoffs" / "protocol.yaml").exists()
    assert (project_dir / "docs" / "handoffs" / ".gitignore").exists()
    assert (project_dir / "docs" / "handoffs" / "phase-N" / "03-review.md").exists()
    assert (project_dir / "docs" / "handoffs" / "phase-N" / "tickets" / "README.md").exists()
    assert (
        project_dir / "docs" / "handoffs" / "phase-N" / "reports" / "execution-report.md"
    ).exists()
    assert not (project_dir / "docs" / "handoffs" / "phase-N" / "01-plan.md").exists()
    assert not (project_dir / "docs" / "handoffs" / "phase-N" / "02-implementation.md").exists()
    phase_scaffold = project_dir / "docs" / "handoffs" / "phase-N"
    for document in phase_scaffold.rglob("*.md"):
        heading = document.read_text(encoding="utf-8").splitlines()[0]
        if document.name != "README.md":
            assert heading.startswith("# Phase N -"), document

    for path in written:
        assert not path.is_absolute()
        assert (project_dir / path).exists()
        assert not str(path).endswith(".tmpl")

    claude_md = (project_dir / "CLAUDE.md").read_text(encoding="utf-8")
    assert claude_md == "@AGENTS.md\n"
    agents_md = (project_dir / "AGENTS.md").read_text(encoding="utf-8")
    assert "my-app" in agents_md
    assert "{{" not in agents_md
    assert "docs/handoffs/README.md" in agents_md
    assert "docs/handoffs/protocol.yaml" in agents_md

    architecture = (project_dir / "docs" / "architecture.md").read_text(encoding="utf-8")
    assert "my-app" in architecture
    assert "{{" not in architecture

    handoffs_readme = (project_dir / "docs" / "handoffs" / "README.md").read_text(encoding="utf-8")
    assert "{{" not in handoffs_readme
    readme = (project_dir / "README.md").read_text(encoding="utf-8")
    assert "`AGENTS.md`" in readme
    assert "`CLAUDE.md` — guidance" not in readme


def test_apply_overlay_stamp_inventory_hashes_rendered_non_inject_files(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    apply_overlay(_answers(tmp_path), project_dir, CATALOG, PIN)

    stamp = json.loads((project_dir / ".dev-ready.json").read_text(encoding="utf-8"))
    inventory = {entry["path"]: entry["sha256"] for entry in stamp["inventory"]}
    for path in (
        "AGENTS.md",
        "CLAUDE.md",
        ".agents/skills/project-orientation/SKILL.md",
        ".claude/skills/project-orientation/SKILL.md",
    ):
        assert inventory[path] == hashlib.sha256((project_dir / path).read_bytes()).hexdigest()


def test_claude_pointer_stub_names_and_describes_canonical_skill(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    apply_overlay(_answers(tmp_path), project_dir, CATALOG, PIN)

    canonical = project_dir / ".agents" / "skills" / "project-orientation" / "SKILL.md"
    stub = project_dir / ".claude" / "skills" / "project-orientation" / "SKILL.md"
    stub_text = stub.read_text(encoding="utf-8")
    assert "name: project-orientation" in stub_text
    assert "description: Orient in this project's structure" in stub_text
    assert ".agents/skills/project-orientation/SKILL.md" in stub_text
    assert stub.read_bytes() != canonical.read_bytes()
    assert not canonical.is_symlink()
    assert not stub.is_symlink()


def test_windsurf_only_writes_windsurf_stubs_and_no_project_mcp(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    apply_overlay(
        _answers(tmp_path, agent_targets=frozenset({"windsurf"})),
        project_dir,
        CATALOG,
        PIN,
    )

    assert (project_dir / "AGENTS.md").is_file()
    assert (project_dir / ".agents/skills/project-orientation/SKILL.md").is_file()
    assert (project_dir / ".windsurf/skills/project-orientation/SKILL.md").is_file()
    assert not (project_dir / ".claude").exists()
    assert not (project_dir / "CLAUDE.md").exists()
    assert not (project_dir / ".mcp.json").exists()
    canonical = (project_dir / ".agents/skills/project-orientation/SKILL.md").read_text(
        encoding="utf-8"
    )
    assert "AGENTS.md" in canonical
    assert "read `CLAUDE.md`" not in canonical


def test_no_agent_targets_still_writes_only_canonical_content(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    apply_overlay(
        _answers(tmp_path, agent_targets=frozenset()),
        project_dir,
        CATALOG,
        PIN,
    )

    assert (project_dir / "AGENTS.md").is_file()
    assert (project_dir / ".agents/skills/project-orientation/SKILL.md").is_file()
    assert not (project_dir / ".claude").exists()
    assert not (project_dir / ".windsurf").exists()
    assert not (project_dir / "CLAUDE.md").exists()
    assert not (project_dir / ".mcp.json").exists()


@pytest.mark.parametrize(
    ("flag", "missing_path", "sibling_paths"),
    [
        (
            "include_skills",
            Path(".claude") / "skills" / "project-orientation" / "SKILL.md",
            [Path(".mcp.json"), Path("docs") / "architecture.md"],
        ),
        (
            "include_mcp",
            Path(".mcp.json"),
            [
                Path(".claude") / "skills" / "project-orientation" / "SKILL.md",
                Path("docs") / "architecture.md",
            ],
        ),
        (
            "include_docs",
            Path("docs") / "architecture.md",
            [Path(".mcp.json"), Path(".claude") / "skills" / "project-orientation" / "SKILL.md"],
        ),
        (
            "include_handoff",
            Path("docs") / "handoffs" / "README.md",
            [
                Path(".mcp.json"),
                Path(".claude") / "skills" / "project-orientation" / "SKILL.md",
                Path("docs") / "architecture.md",
            ],
        ),
    ],
)
def test_component_flag_skips_exactly_its_component(
    tmp_path: Path, flag: str, missing_path: Path, sibling_paths: list[Path]
) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    apply_overlay(_answers(tmp_path, **{flag: False}), project_dir, CATALOG, PIN)

    assert (project_dir / "CLAUDE.md").exists()
    assert not (project_dir / missing_path).exists()
    for sibling in sibling_paths:
        assert (project_dir / sibling).exists()


def test_claude_md_always_present_even_with_all_components_disabled(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    written = apply_overlay(
        _answers(tmp_path, include_skills=False, include_mcp=False, include_docs=False, include_handoff=False),
        project_dir,
        CATALOG,
        PIN,
    )

    assert written == [
        Path("AGENTS.md"),
        Path("CLAUDE.md"),
        Path("README.md"),
        Path(".dev-ready.json"),
    ]
    assert (project_dir / "AGENTS.md").exists()
    assert (project_dir / "CLAUDE.md").exists()
    assert (project_dir / "README.md").exists()
    assert (project_dir / ".dev-ready.json").exists()
    assert not (project_dir / ".claude").exists()
    assert not (project_dir / ".agents" / "skills").exists()
    assert not (project_dir / ".mcp.json").exists()
    assert not (project_dir / "docs").exists()


def test_coexistence_docs_and_handoff(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    apply_overlay(_answers(tmp_path, include_docs=True, include_handoff=True), project_dir, CATALOG, PIN)
    assert (project_dir / "docs" / "architecture.md").exists()
    assert (project_dir / "docs" / "handoffs" / "README.md").exists()


def test_docs_without_handoff(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    apply_overlay(_answers(tmp_path, include_docs=True, include_handoff=False), project_dir, CATALOG, PIN)
    assert (project_dir / "docs" / "architecture.md").exists()
    assert not (project_dir / "docs" / "handoffs").exists()


def test_protocol_configuration_is_the_single_role_authority(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    apply_overlay(_answers(tmp_path, include_handoff=True), project_dir, CATALOG, PIN)

    handoffs = project_dir / "docs" / "handoffs"
    protocol = (handoffs / "protocol.yaml").read_text(encoding="utf-8")
    role_ids = (
        "ceo",
        "tech_lead",
        "senior_engineer",
        "junior_engineer",
        "qa_reviewer",
        "security_reviewer",
        "sre_reviewer",
    )
    for role_id in role_ids:
        assert f"  {role_id}:" in protocol
    assert protocol.count("    model: null") == 7
    for field in ("title:", "responsibilities:", "never_does:"):
        assert protocol.count(f"    {field}") == 7
    for rule in ("handoff_sequence:", "stop_rule:", "escalation_rule:", "reporting_rule:", "commit_authority:"):
        assert rule in protocol

    other_prose = "\n".join(
        path.read_text(encoding="utf-8")
        for path in handoffs.rglob("*.md")
    )
    assert "model:" not in other_prose
    assert "Chief Executive" not in other_prose
    assert "Architecture Lead" not in other_prose
    assert "protocol.yaml" in other_prose


def test_handoff_gitignore_keeps_only_active_numeric_phases_ephemeral(
    tmp_path: Path,
) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    apply_overlay(_answers(tmp_path, include_handoff=True), project_dir, CATALOG, PIN)

    handoffs = project_dir / "docs" / "handoffs"
    assert (handoffs / ".gitignore").read_text(encoding="utf-8") == "/phase-[0-9]*/\n"
    assert (handoffs / "protocol.yaml").is_file()
    assert (handoffs / "README.md").is_file()
    assert (handoffs / "phase-N").is_dir()
    assert (project_dir / "docs" / "requirements.md").is_file()


@pytest.mark.parametrize("include_handoff", [False, True])
@pytest.mark.parametrize("include_spec_loop", [False, True])
@pytest.mark.parametrize("include_docs", [False, True])
def test_methodology_and_documentation_axes_render_independently(
    tmp_path: Path,
    include_handoff: bool,
    include_spec_loop: bool,
    include_docs: bool,
) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    answers = _answers(
        tmp_path,
        skills_items=frozenset({"spec-loop"}) if include_spec_loop else frozenset(),
        include_mcp=False,
        include_docs=include_docs,
        include_handoff=include_handoff,
    )

    apply_overlay(answers, project_dir, CATALOG, PIN)

    claude_md = (project_dir / "CLAUDE.md").read_text(encoding="utf-8")
    assert claude_md == "@AGENTS.md\n"
    agents_md = (project_dir / "AGENTS.md").read_text(encoding="utf-8")
    assert ((project_dir / "docs" / "handoffs" / "protocol.yaml").is_file()) is include_handoff
    assert ((project_dir / ".claude" / "skills" / "to-spec" / "SKILL.md").is_file()) is include_spec_loop
    assert ((project_dir / "docs" / "agents" / "issue-tracker.md").is_file()) is include_spec_loop
    assert ((project_dir / "docs" / "architecture.md").is_file()) is include_docs
    assert ("## Handoff Protocol" in agents_md) is include_handoff
    assert ("## Spec Loop" in agents_md) is include_spec_loop
    assert ("docs/architecture.md" in agents_md) is include_docs
    assert ("## Process-v2 role mapping" in agents_md) is (
        include_handoff and include_spec_loop
    )

    if include_spec_loop:
        tracker = (project_dir / "docs" / "agents" / "issue-tracker.md").read_text(
            encoding="utf-8"
        )
        assert ("docs/specs/" in tracker) is include_handoff
        assert ("docs/handoffs/phase-<number>/tickets/" in tracker) is include_handoff
        assert (".scratch/" in tracker) is (not include_handoff)

    if include_handoff:
        protocol = (project_dir / "docs" / "handoffs" / "protocol.yaml").read_text(
            encoding="utf-8"
        )
        assert ("Maintain docs/architecture.md" in protocol) is include_docs

    if include_docs:
        architecture = (project_dir / "docs" / "architecture.md").read_text(
            encoding="utf-8"
        )
        for heading in ("## System Overview", "## Module Boundary", "## Dependency Rules"):
            assert heading in architecture
        assert ("`tech_lead`" in architecture) is include_handoff

    assert "{{" not in agents_md


def test_readme_is_about_the_project_not_the_template(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    apply_overlay(_answers(tmp_path), project_dir, CATALOG, PIN)

    readme = (project_dir / "README.md").read_text(encoding="utf-8")
    assert "my-app" in readme
    assert "{{" not in readme
    assert "MoofonLi/dev-ready" in readme
    assert "img/" not in readme


def test_collision_on_existing_readme_raises_overlay_error(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "README.md").write_text("pre-existing", encoding="utf-8")

    with pytest.raises(OverlayError, match="README.md"):
        apply_overlay(_answers(tmp_path), project_dir, CATALOG, PIN)

    assert (project_dir / "README.md").read_text(encoding="utf-8") == "pre-existing"


def test_collision_on_existing_claude_md_raises_overlay_error(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "CLAUDE.md").write_text("pre-existing", encoding="utf-8")

    with pytest.raises(OverlayError, match="CLAUDE.md"):
        apply_overlay(_answers(tmp_path), project_dir, CATALOG, PIN)

    # the pre-existing file must not have been overwritten
    assert (project_dir / "CLAUDE.md").read_text(encoding="utf-8") == "pre-existing"
    # nothing from other components should have been written either
    assert not (project_dir / ".mcp.json").exists()


def test_collision_on_nested_asset_raises_overlay_error(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    (project_dir / "docs").mkdir(parents=True)
    (project_dir / "docs" / "architecture.md").write_text("pre-existing", encoding="utf-8")

    with pytest.raises(OverlayError, match="architecture.md"):
        apply_overlay(_answers(tmp_path), project_dir, CATALOG, PIN)


@pytest.mark.parametrize(
    "bad_name",
    ["../etc", "a b", "-app", "app/x", ""],
)
def test_invalid_project_name_is_rejected_before_overlay(tmp_path: Path, bad_name: str) -> None:
    with pytest.raises(InvalidArgumentsError, match="invalid project name"):
        _answers(tmp_path, project_name=bad_name)


def test_leftover_template_marker_raises_overlay_error(tmp_path: Path) -> None:
    """Exercises the real substitution + leftover-marker guard in _render_asset."""
    import dev_ready.overlay as overlay_module

    source = tmp_path / "asset.txt.tmpl"
    source.write_text("hello {{project_name}}, also {{unresolved}}", encoding="utf-8")
    with pytest.raises(OverlayError, match="template marker"):
        overlay_module._render_asset(source, Path("out.txt"), "my-app")


class _MissingAssetTraversable:
    """Minimal Traversable stub simulating a broken install: nothing exists."""

    def joinpath(self, *_parts: str) -> "_MissingAssetTraversable":
        return self

    def is_file(self) -> bool:
        return False

    def is_dir(self) -> bool:
        return False


def test_missing_overlay_asset_raises_overlay_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Simulates a corrupt/broken install where packaged template assets are absent."""
    import dev_ready.overlay as overlay_module

    monkeypatch.setattr(
        overlay_module.resources, "files", lambda _package: _MissingAssetTraversable()
    )
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    with pytest.raises(OverlayError, match="overlay asset missing"):
        apply_overlay(_answers(tmp_path), project_dir, CATALOG, PIN)


def test_render_stamp_structure(tmp_path: Path) -> None:
    ans = _answers(tmp_path, skills_items=frozenset({"project-orientation", "react-doctor"}), mcp_items=frozenset({"code-memory"}))
    stamp_text = render_stamp(ans, PIN, CATALOG)
    data = json.loads(stamp_text)
    assert data["stamp_version"] == 4
    assert data["project_name"] == "my-app"
    assert data["inventory"] == []
    assert data["dev_ready_version"] == __version__
    assert data["components"]["skills"]["included"] is True
    assert data["components"]["skills"]["items"] == [
        {"id": "project-orientation", "pin": None},
        {"id": "react-doctor", "pin": "0.8.1"},
    ]
    assert data["components"]["mcp"]["included"] is True
    assert data["components"]["mcp"]["items"] == [{"id": "code-memory", "pin": "0.9.0"}]
    assert data["components"]["docs"]["included"] is True
    assert data["components"]["handoff"]["included"] is True
    assert data["agent_targets"] == ["claude", "windsurf"]
    assert "agents" not in data["components"]
    assert data["upstream"]["repo"] == PIN.repo
    assert data["upstream"]["commit"] == PIN.commit
    assert "ref" not in data["upstream"]
    assert "vendored" not in data




def test_asset_read_via_importlib_resources() -> None:
    """Prove templates are accessed as package data, not repo-root paths."""
    from importlib import resources

    resource = resources.files("dev_ready").joinpath("templates", "mcp", "mcp.json")
    assert resource.is_file()
    content = resource.read_text(encoding="utf-8")
    assert '"mcpServers"' in content


def test_code_memory_injection(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    apply_overlay(
        _answers(tmp_path, mcp_items=frozenset({"mcp-config", "code-memory"})),
        project_dir,
        CATALOG,
        PIN,
    )
    mcp_json = json.loads((project_dir / ".mcp.json").read_text(encoding="utf-8"))
    assert "codebase-memory" in mcp_json["mcpServers"]
    assert mcp_json["mcpServers"]["codebase-memory"] == {
        "command": "uvx",
        "args": ["codebase-memory-mcp==0.9.0"],
    }


def test_code_memory_without_mcp_config_raises_overlay_error(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    with pytest.raises(OverlayError, match="requires target"):
        apply_overlay(
            _answers(tmp_path, mcp_items=frozenset({"code-memory"})),
            project_dir,
            CATALOG,
            PIN,
        )


def test_react_doctor_skill_copy(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "frontend").mkdir()
    (project_dir / "frontend" / "package.json").write_text("{}", encoding="utf-8")
    apply_overlay(
        _answers(tmp_path, skills_items=frozenset({"react-doctor"})),
        project_dir,
        CATALOG,
        PIN,
    )
    skill_path = project_dir / ".agents" / "skills" / "react-doctor" / "SKILL.md"
    assert skill_path.exists()
    content = skill_path.read_text(encoding="utf-8")
    assert "react-doctor" in content
    assert "npm run doctor" in content


def test_npm_dev_dependency_injection_happy_path(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    pkg_json_path = project_dir / "frontend" / "package.json"
    pkg_json_path.parent.mkdir()
    pkg_json_path.write_text(
        json.dumps({
            "name": "frontend",
            "scripts": {"dev": "vite", "build": "tsc && vite build"},
            "devDependencies": {"typescript": "^5.0.0"},
        }),
        encoding="utf-8",
    )

    apply_overlay(
        _answers(tmp_path, skills_items=frozenset({"react-doctor"})),
        project_dir,
        CATALOG,
        PIN,
    )

    data = json.loads(pkg_json_path.read_text(encoding="utf-8"))
    assert data["name"] == "frontend"
    assert data["scripts"]["dev"] == "vite"
    assert data["scripts"]["build"] == "tsc && vite build"
    assert data["scripts"]["doctor"] == "react-doctor"
    assert data["devDependencies"]["typescript"] == "^5.0.0"
    assert data["devDependencies"]["react-doctor"] == "0.8.1"


def test_npm_dev_dependency_missing_target_raises_overlay_error(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    with pytest.raises(OverlayError, match="is missing"):
        apply_overlay(
            _answers(tmp_path, skills_items=frozenset({"react-doctor"})),
            project_dir,
            CATALOG,
            PIN,
        )


def test_npm_dev_dependency_unparseable_target_raises_overlay_error(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    pkg_json_path = project_dir / "frontend" / "package.json"
    pkg_json_path.parent.mkdir()
    pkg_json_path.write_text("{ not json", encoding="utf-8")

    with pytest.raises(OverlayError, match="failed to parse"):
        apply_overlay(
            _answers(tmp_path, skills_items=frozenset({"react-doctor"})),
            project_dir,
            CATALOG,
            PIN,
        )


def test_render_stamp_records_vendored_pins(tmp_path: Path) -> None:
    manifest = load_default_manifest()
    answers = _answers(tmp_path, skills_items=frozenset({"caveman", "project-orientation"}))
    raw = render_stamp(answers, PIN, manifest.components, manifest.vendored)
    data = json.loads(raw)
    assert data["stamp_version"] == 4
    items = data["components"]["skills"]["items"]
    caveman_item = next(i for i in items if i["id"] == "caveman")
    po_item = next(i for i in items if i["id"] == "project-orientation")
    assert caveman_item["pin"] == "0d95a81d35a9f2d123a5e9430d1cfc43d55f1bb0"
    assert po_item["pin"] is None


def test_apply_overlay_writes_vendored_skills_and_docs(tmp_path: Path) -> None:
    manifest = load_default_manifest()
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    skills_to_test = frozenset(
        {
            "caveman",
            "security-audit",
            "tdd",
            "diagnosing-bugs",
            "code-review",
            "webapp-testing",
            "frontend-design",
        }
    )
    answers = _answers(tmp_path, skills_items=skills_to_test, include_docs=True)

    written = apply_overlay(answers, project_dir, manifest.components, PIN, manifest.vendored)

    for skill in skills_to_test:
        assert (project_dir / ".claude" / "skills" / skill / "SKILL.md").exists()

    assert (project_dir / "docs" / "design-stripe.md").exists()
    assert (project_dir / "docs" / "design-linear.md").exists()
    assert Path(".claude/skills/caveman/SKILL.md") in written
    assert Path("docs/design-stripe.md") in written


def test_apply_overlay_deselected_vendored_skills_are_absent(tmp_path: Path) -> None:
    manifest = load_default_manifest()
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    # Select only builtin item; leave all vendored skills deselected
    answers = _answers(tmp_path, skills_items=frozenset({"project-orientation"}))

    written = apply_overlay(answers, project_dir, manifest.components, PIN, manifest.vendored)

    all_vendored_skills = {
        "caveman",
        "security-audit",
        "tdd",
        "diagnosing-bugs",
        "code-review",
        "webapp-testing",
        "frontend-design",
    }
    for skill in all_vendored_skills:
        assert not (project_dir / ".claude" / "skills" / skill).exists()
        assert Path(f".claude/skills/{skill}/SKILL.md") not in written


def test_apply_overlay_mixed_vendored_skills_selection(tmp_path: Path) -> None:
    manifest = load_default_manifest()
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    # Mixed selection: caveman selected, remaining vendored skills deselected
    selected = frozenset({"project-orientation", "caveman"})
    answers = _answers(tmp_path, skills_items=selected)

    written = apply_overlay(answers, project_dir, manifest.components, PIN, manifest.vendored)

    assert (project_dir / ".claude" / "skills" / "caveman" / "SKILL.md").exists()
    assert Path(".claude/skills/caveman/SKILL.md") in written

    deselected_vendored = {
        "security-audit",
        "tdd",
        "diagnosing-bugs",
        "code-review",
        "webapp-testing",
        "frontend-design",
    }
    for skill in deselected_vendored:
        assert not (project_dir / ".claude" / "skills" / skill).exists()
        assert Path(f".claude/skills/{skill}/SKILL.md") not in written


def test_anthropics_skills_selection_and_license_propagation(tmp_path: Path) -> None:
    manifest = load_default_manifest()
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    answers = _answers(
        tmp_path,
        skills_items=frozenset({"webapp-testing", "frontend-design"}),
    )

    written = apply_overlay(answers, project_dir, manifest.components, PIN, manifest.vendored)

    expected_files = [
        ".agents/skills/webapp-testing/SKILL.md",
        ".agents/skills/webapp-testing/LICENSE.txt",
        ".agents/skills/webapp-testing/scripts/with_server.py",
        ".agents/skills/webapp-testing/examples/console_logging.py",
        ".agents/skills/frontend-design/SKILL.md",
        ".agents/skills/frontend-design/LICENSE.txt",
    ]

    for rel_path in expected_files:
        full_path = project_dir / rel_path
        assert full_path.exists(), f"Expected {rel_path} to exist"
        assert full_path.stat().st_size > 0, f"Expected {rel_path} to be non-empty"
        assert Path(rel_path) in written


def test_anthropics_skills_deselected_not_written(tmp_path: Path) -> None:
    manifest = load_default_manifest()
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    answers = _answers(tmp_path, skills_items=frozenset({"project-orientation"}))

    apply_overlay(answers, project_dir, manifest.components, PIN, manifest.vendored)

    assert not (project_dir / ".claude" / "skills" / "webapp-testing").exists()
    assert not (project_dir / ".claude" / "skills" / "frontend-design").exists()


def test_render_stamp_records_anthropics_pin(tmp_path: Path) -> None:
    manifest = load_default_manifest()
    answers = _answers(tmp_path, skills_items=frozenset({"webapp-testing"}))
    raw = render_stamp(answers, PIN, manifest.components, manifest.vendored)
    data = json.loads(raw)
    assert data["stamp_version"] == 4
    items = data["components"]["skills"]["items"]
    webapp_item = next(i for i in items if i["id"] == "webapp-testing")
    assert webapp_item["pin"] == "1f630fdf9259cec4a14913127dfd7c3b69ef72eb"


def test_claude_md_contains_karpathy_guardrails(tmp_path: Path) -> None:
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    apply_overlay(_answers(tmp_path), project_dir, CATALOG, PIN)

    claude_md = (project_dir / "AGENTS.md").read_text(encoding="utf-8")
    # Attribution (Security-reviewed wording): MIT + README basis + upstream repo.
    assert "multica-ai/andrej-karpathy-skills" in claude_md
    assert "(MIT, per its README)" in claude_md
    # A representative guardrail line is folded in.
    assert "Simplicity first" in claude_md
    # Length budget is an acceptance property, not a preference.
    assert len(claude_md.splitlines()) <= 75
    assert "{{" not in claude_md


def test_standalone_spec_loop_is_complete_and_role_neutral(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    answers = _answers(
        tmp_path,
        skills_items=frozenset({"spec-loop"}),
        include_mcp=False,
        include_docs=False,
        include_handoff=False,
    )

    apply_overlay(answers, project_dir, CATALOG, PIN)

    for skill_name in (
        "grill-with-docs",
        "grilling",
        "domain-modeling",
        "to-spec",
        "to-tickets",
        "improve-codebase-architecture",
        "codebase-design",
        "tdd",
        "diagnosing-bugs",
        "code-review",
    ):
        assert (project_dir / ".agents" / "skills" / skill_name / "SKILL.md").is_file()
        assert (project_dir / ".claude" / "skills" / skill_name / "SKILL.md").is_file()
    assert (project_dir / "docs" / "agents" / "issue-tracker.md").is_file()
    assert (project_dir / "docs" / "agents" / "domain.md").is_file()
    assert not (project_dir / "CONTEXT.md").exists()

    claude_md = (project_dir / "AGENTS.md").read_text(encoding="utf-8")
    assert "## Spec Loop" in claude_md
    assert "docs/agents/issue-tracker.md" in claude_md
    assert "Handoff Protocol" not in claude_md
    assert "tech_lead" not in claude_md
    assert "setup-matt-pocock-skills" not in claude_md


def test_deselected_spec_loop_emits_no_bundle_configuration_or_guidance(
    tmp_path: Path,
) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    answers = _answers(
        tmp_path,
        include_skills=False,
        include_mcp=False,
        include_docs=False,
        include_handoff=False,
    )

    apply_overlay(answers, project_dir, CATALOG, PIN)

    assert not (project_dir / "docs").exists()
    claude_md = (project_dir / "AGENTS.md").read_text(encoding="utf-8")
    assert "Spec Loop" not in claude_md
    assert "Handoff Protocol" not in claude_md


def test_spec_loop_stamp_records_the_resolved_selection_and_complete_inventory(
    tmp_path: Path,
) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    answers = _answers(
        tmp_path,
        skills_items=frozenset({"spec-loop"}),
        include_mcp=False,
        include_docs=False,
        include_handoff=False,
    )

    apply_overlay(answers, project_dir, CATALOG, PIN, load_default_manifest().vendored)

    stamp = json.loads((project_dir / ".dev-ready.json").read_text(encoding="utf-8"))
    assert {item["id"] for item in stamp["components"]["skills"]["items"]} == {
        "spec-loop",
        "tdd",
        "diagnosing-bugs",
        "code-review",
    }
    inventory_paths = {entry["path"] for entry in stamp["inventory"]}
    assert ".agents/skills/domain-modeling/ADR-FORMAT.md" in inventory_paths
    assert "docs/agents/issue-tracker.md" in inventory_paths
    assert not (project_dir / "CONTEXT.md").exists()


def test_manifest_only_project_mcp_path_retargets_catalog_effects(tmp_path: Path) -> None:
    custom_catalog = ComponentCatalog(
        CATALOG,
        {
            "custom": AgentTarget(
                id="custom",
                description="Custom project-local MCP target.",
                skills_dir=".custom/skills",
                rules_file=None,
                mcp_file=".custom/mcp.json",
            )
        },
    )
    answers = Answers(
        project_name="my-app",
        target_dir=tmp_path / "project",
        selection=ProjectSelection.from_items(
            custom_catalog,
            mcp=frozenset({"mcp-config", "code-memory"}),
            agent_targets=frozenset({"custom"}),
            docs=False,
            handoff=False,
        ),
    )
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    apply_overlay(answers, project_dir, custom_catalog, PIN)

    config = json.loads((project_dir / ".custom/mcp.json").read_text(encoding="utf-8"))
    assert "codebase-memory" in config["mcpServers"]
    assert not (project_dir / ".mcp.json").exists()





