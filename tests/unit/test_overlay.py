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
    skills_items: frozenset[str] = frozenset({"caveman"}),
    mcp_items: frozenset[str] = frozenset({"code-memory"}),
    docs_items: frozenset[str] = frozenset({"design-stripe", "design-linear"}),
    agent_targets: frozenset[str] | None = None,
) -> Answers:
    return Answers(
        project_name=project_name,
        target_dir=tmp_path / "my-app",
        selection=ProjectSelection.from_items(
            CATALOG,
            skills=skills_items if include_skills else frozenset(),
            mcp=mcp_items if include_mcp else frozenset(),
            docs_items=docs_items if include_docs else frozenset(),
            agent_targets=agent_targets,
            docs=include_docs,
        ),
    )



def test_happy_path_writes_every_component_with_substitution(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    written = apply_overlay(_answers(tmp_path), project_dir, CATALOG, PIN)



    assert (project_dir / "AGENTS.md").exists()
    assert (project_dir / "CLAUDE.md").exists()
    assert (project_dir / "README.md").exists()
    assert (project_dir / ".agents" / "skills" / "caveman" / "SKILL.md").exists()
    assert (project_dir / ".claude" / "skills" / "caveman" / "SKILL.md").exists()
    assert (project_dir / ".windsurf" / "skills" / "caveman" / "SKILL.md").exists()
    assert (project_dir / ".mcp.json").exists()
    assert (project_dir / "docs" / "architecture.md").exists()
    assert (project_dir / "docs" / "requirements.md").exists()
    assert not (project_dir / "docs" / "handoffs").exists()

    for path in written:
        assert not path.is_absolute()
        assert (project_dir / path).exists()
        assert not str(path).endswith(".tmpl")

    claude_md = (project_dir / "CLAUDE.md").read_text(encoding="utf-8")
    assert claude_md == "@AGENTS.md\n"
    agents_md = (project_dir / "AGENTS.md").read_text(encoding="utf-8")
    assert "my-app" in agents_md
    assert "{{" not in agents_md
    assert "Handoff Protocol" not in agents_md

    architecture = (project_dir / "docs" / "architecture.md").read_text(encoding="utf-8")
    assert "my-app" in architecture
    assert "{{" not in architecture

    readme = (project_dir / "README.md").read_text(encoding="utf-8")
    assert "`AGENTS.md`" in readme
    assert "`CLAUDE.md` — guidance" not in readme


@pytest.mark.parametrize("selection_name", ["everything", "nothing", "mixed"])
def test_no_selection_writes_handoff_protocol_paths(
    tmp_path: Path, selection_name: str
) -> None:
    if selection_name == "everything":
        selection = ProjectSelection.all(CATALOG)
    elif selection_name == "nothing":
        selection = ProjectSelection.empty()
    else:
        selection = ProjectSelection.from_items(
            CATALOG,
            skills=frozenset({"tdd"}),
            mcp=frozenset(),
            agent_targets=frozenset({"claude"}),
            docs=True,
        )

    project_dir = tmp_path / selection_name
    (project_dir / "frontend").mkdir(parents=True)
    (project_dir / "frontend" / "package.json").write_text(
        json.dumps({"scripts": {}, "devDependencies": {}}), encoding="utf-8"
    )
    answers = Answers("my-app", project_dir, selection)

    apply_overlay(answers, project_dir, CATALOG, PIN)

    generated_paths = {
        path.relative_to(project_dir) for path in project_dir.rglob("*")
    }
    assert all(path.parts[:2] != ("docs", "handoffs") for path in generated_paths)


@pytest.mark.parametrize("selection_name", ["everything", "nothing", "mixed"])
def test_no_selection_writes_project_orientation_skill(
    tmp_path: Path, selection_name: str
) -> None:
    if selection_name == "everything":
        selection = ProjectSelection.all(CATALOG)
    elif selection_name == "nothing":
        selection = ProjectSelection.empty()
    else:
        selection = ProjectSelection.from_items(
            CATALOG,
            skills=frozenset({"caveman"}),
            mcp=frozenset(),
            agent_targets=frozenset({"claude"}),
            docs=True,
        )

    project_dir = tmp_path / selection_name
    (project_dir / "frontend").mkdir(parents=True)
    (project_dir / "frontend" / "package.json").write_text(
        json.dumps({"scripts": {}, "devDependencies": {}}), encoding="utf-8"
    )
    answers = Answers("my-app", project_dir, selection)

    apply_overlay(answers, project_dir, CATALOG, PIN)

    generated_paths = {
        path.relative_to(project_dir) for path in project_dir.rglob("*")
    }
    assert all("project-orientation" not in path.parts for path in generated_paths)


def test_apply_overlay_stamp_inventory_hashes_rendered_non_inject_files(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    apply_overlay(_answers(tmp_path), project_dir, CATALOG, PIN)

    stamp = json.loads((project_dir / ".dev-ready.json").read_text(encoding="utf-8"))
    inventory = {entry["path"]: entry["sha256"] for entry in stamp["inventory"]}
    for path in (
        "AGENTS.md",
        "CLAUDE.md",
        ".agents/skills/caveman/SKILL.md",
        ".claude/skills/caveman/SKILL.md",
    ):
        assert inventory[path] == hashlib.sha256((project_dir / path).read_bytes()).hexdigest()


def test_claude_pointer_stub_names_and_describes_canonical_skill(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    apply_overlay(_answers(tmp_path), project_dir, CATALOG, PIN)

    canonical = project_dir / ".agents" / "skills" / "caveman" / "SKILL.md"
    stub = project_dir / ".claude" / "skills" / "caveman" / "SKILL.md"
    stub_text = stub.read_text(encoding="utf-8")
    assert "name: caveman" in stub_text
    assert "Ultra-compressed communication mode." in stub_text
    assert ".agents/skills/caveman/SKILL.md" in stub_text
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
    assert (project_dir / ".agents/skills/caveman/SKILL.md").is_file()
    assert (project_dir / ".windsurf/skills/caveman/SKILL.md").is_file()
    assert not (project_dir / ".claude").exists()
    assert not (project_dir / "CLAUDE.md").exists()
    assert not (project_dir / ".mcp.json").exists()
    canonical = (project_dir / ".agents/skills/caveman/SKILL.md").read_text(
        encoding="utf-8"
    )
    assert "name: caveman" in canonical
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
    assert (project_dir / ".agents/skills/caveman/SKILL.md").is_file()
    assert not (project_dir / ".claude").exists()
    assert not (project_dir / ".windsurf").exists()
    assert not (project_dir / "CLAUDE.md").exists()
    assert not (project_dir / ".mcp.json").exists()


@pytest.mark.parametrize(
    ("flag", "missing_path", "sibling_paths"),
    [
        (
            "include_skills",
            Path(".claude") / "skills" / "caveman" / "SKILL.md",
            [Path(".mcp.json"), Path("docs") / "architecture.md"],
        ),
        (
            "include_mcp",
            Path(".mcp.json"),
            [
                Path(".claude") / "skills" / "caveman" / "SKILL.md",
                Path("docs") / "architecture.md",
            ],
        ),
        (
            "include_docs",
            Path("docs") / "architecture.md",
            [Path(".mcp.json"), Path(".claude") / "skills" / "caveman" / "SKILL.md"],
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
        _answers(tmp_path, include_skills=False, include_mcp=False, include_docs=False),
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


@pytest.mark.parametrize("include_spec_loop", [False, True])
@pytest.mark.parametrize("include_docs", [False, True])
def test_spec_loop_and_documentation_render_independently(
    tmp_path: Path,
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
    )

    apply_overlay(answers, project_dir, CATALOG, PIN)

    claude_md = (project_dir / "CLAUDE.md").read_text(encoding="utf-8")
    assert claude_md == "@AGENTS.md\n"
    agents_md = (project_dir / "AGENTS.md").read_text(encoding="utf-8")
    assert not (project_dir / "docs" / "handoffs").exists()
    assert ((project_dir / ".claude" / "skills" / "to-spec" / "SKILL.md").is_file()) is include_spec_loop
    assert ((project_dir / "docs" / "agents" / "issue-tracker.md").is_file()) is include_spec_loop
    assert ((project_dir / "docs" / "architecture.md").is_file()) is include_docs
    assert "## Handoff Protocol" not in agents_md
    assert ("## Spec Loop" in agents_md) is include_spec_loop
    assert ("docs/architecture.md" in agents_md) is include_docs
    assert "## Process-v2 role mapping" not in agents_md

    if include_spec_loop:
        tracker = (project_dir / "docs" / "agents" / "issue-tracker.md").read_text(
            encoding="utf-8"
        )
        assert "docs/specs/" not in tracker
        assert "docs/handoffs/" not in tracker
        assert ".scratch/" in tracker

    if include_docs:
        architecture = (project_dir / "docs" / "architecture.md").read_text(
            encoding="utf-8"
        )
        for heading in ("## System Overview", "## Module Boundary", "## Dependency Rules"):
            assert heading in architecture
        assert "`tech_lead`" not in architecture

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
    ans = _answers(
        tmp_path,
        skills_items=frozenset({"caveman", "react-doctor"}),
        mcp_items=frozenset({"code-memory"}),
    )
    stamp_text = render_stamp(ans, PIN, CATALOG)
    data = json.loads(stamp_text)
    assert data["stamp_version"] == 5
    assert data["categories"] == ["design", "quality", "token-optimize"]
    assert data["project_name"] == "my-app"
    assert data["inventory"] == []
    assert data["dev_ready_version"] == __version__
    assert data["components"]["skills"]["included"] is True
    assert data["components"]["skills"]["items"] == [
        {"id": "caveman", "pin": None},
        {"id": "react-doctor", "pin": "0.8.1"},
    ]
    assert data["components"]["mcp"]["included"] is True
    assert data["components"]["mcp"]["items"] == [{"id": "code-memory", "pin": "0.9.0"}]
    assert data["components"]["docs"]["included"] is True
    assert data["components"]["docs"]["items"] == [
        {"id": "design-linear", "pin": None},
        {"id": "design-stripe", "pin": None},
    ]
    assert "handoff" not in data["components"]
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
        _answers(tmp_path, mcp_items=frozenset({"code-memory"})),
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


def test_code_memory_without_selectable_mcp_config_creates_server_config(
    tmp_path: Path,
) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    apply_overlay(
        _answers(tmp_path, mcp_items=frozenset({"code-memory"})),
        project_dir,
        CATALOG,
        PIN,
    )

    mcp_json = json.loads((project_dir / ".mcp.json").read_text(encoding="utf-8"))
    assert mcp_json["mcpServers"]["codebase-memory"] == {
        "command": "uvx",
        "args": ["codebase-memory-mcp==0.9.0"],
    }


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
    answers = _answers(tmp_path, skills_items=frozenset({"caveman"}))
    raw = render_stamp(answers, PIN, manifest.components, manifest.vendored)
    data = json.loads(raw)
    assert data["stamp_version"] == 5
    items = data["components"]["skills"]["items"]
    caveman_item = next(i for i in items if i["id"] == "caveman")
    assert caveman_item["pin"] == "0d95a81d35a9f2d123a5e9430d1cfc43d55f1bb0"


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


@pytest.mark.parametrize(
    ("selected", "absent"),
    [
        ("design-stripe", "design-linear"),
        ("design-linear", "design-stripe"),
    ],
)
def test_either_design_reference_can_be_selected_alone(
    tmp_path: Path,
    selected: str,
    absent: str,
) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    answers = _answers(
        tmp_path,
        include_mcp=False,
        docs_items=frozenset({selected}),
    )

    apply_overlay(answers, project_dir, CATALOG, PIN)

    assert (project_dir / "docs" / f"{selected}.md").is_file()
    assert not (project_dir / "docs" / f"{absent}.md").exists()


def test_apply_overlay_deselected_vendored_skills_are_absent(tmp_path: Path) -> None:
    manifest = load_default_manifest()
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    # Leave all vendored skills deselected.
    answers = _answers(tmp_path, skills_items=frozenset())

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
    selected = frozenset({"caveman"})
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

    answers = _answers(tmp_path, skills_items=frozenset({"caveman"}))

    apply_overlay(answers, project_dir, manifest.components, PIN, manifest.vendored)

    assert not (project_dir / ".claude" / "skills" / "webapp-testing").exists()
    assert not (project_dir / ".claude" / "skills" / "frontend-design").exists()


def test_render_stamp_records_anthropics_pin(tmp_path: Path) -> None:
    manifest = load_default_manifest()
    answers = _answers(tmp_path, skills_items=frozenset({"webapp-testing"}))
    raw = render_stamp(answers, PIN, manifest.components, manifest.vendored)
    data = json.loads(raw)
    assert data["stamp_version"] == 5
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
    )

    apply_overlay(answers, project_dir, CATALOG, PIN)

    for skill_name in (
        "grill-with-docs",
        "grilling",
        "domain-modeling",
        "to-spec",
        "to-tickets",
        "implement",
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
            mcp=frozenset({"code-memory"}),
            agent_targets=frozenset({"custom"}),
            docs=False,
        ),
    )
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    apply_overlay(answers, project_dir, custom_catalog, PIN)

    config = json.loads((project_dir / ".custom/mcp.json").read_text(encoding="utf-8"))
    assert "codebase-memory" in config["mcpServers"]
    assert not (project_dir / ".mcp.json").exists()





