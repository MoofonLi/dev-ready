"""Unit tests for dev_ready.overlay (no network, filesystem confined to tmp_path)."""

from pathlib import Path

import pytest

import json

from dev_ready import __version__
from dev_ready.errors import OverlayError
from dev_ready.manifest import UpstreamPin, load_default_manifest
from dev_ready.overlay import apply_overlay, render_stamp
from dev_ready.prompts import Answers

CATALOG = load_default_manifest().components
PIN = UpstreamPin(
    repo="fastapi/full-stack-fastapi-template",
    ref="master",
    commit="4cd0d9e51aebd1af6f82d91ad0df4c9e41f4dea2",
    license="MIT",
)


def _answers(tmp_path: Path, **overrides: object) -> Answers:
    defaults: dict[str, object] = {
        "project_name": "my-app",
        "target_dir": tmp_path / "my-app",
        "include_skills": True,
        "include_mcp": True,
        "include_docs": True,
        "include_agents": True,
        "skills_items": frozenset({"project-orientation"}),
        "mcp_items": frozenset({"mcp-config"}),
    }
    defaults.update(overrides)
    if "skills_items" in overrides and "include_skills" not in overrides:
        defaults["include_skills"] = bool(defaults["skills_items"])
    if "mcp_items" in overrides and "include_mcp" not in overrides:
        defaults["include_mcp"] = bool(defaults["mcp_items"])
    if "include_skills" in overrides and not overrides["include_skills"] and "skills_items" not in overrides:
        defaults["skills_items"] = frozenset()
    if "include_mcp" in overrides and not overrides["include_mcp"] and "mcp_items" not in overrides:
        defaults["mcp_items"] = frozenset()
    return Answers(**defaults)  # type: ignore[arg-type]



def test_happy_path_writes_every_component_with_substitution(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    written = apply_overlay(_answers(tmp_path), project_dir, CATALOG, PIN)



    assert (project_dir / "CLAUDE.md").exists()
    assert (project_dir / "README.md").exists()
    assert (project_dir / ".claude" / "skills" / "project-orientation" / "SKILL.md").exists()
    assert (project_dir / ".mcp.json").exists()
    assert (project_dir / "docs" / "architecture.md").exists()
    assert (project_dir / "docs" / "requirements.md").exists()
    assert (project_dir / "docs" / "handoffs" / "README.md").exists()
    assert (project_dir / "docs" / "handoffs" / "phase-N" / "01-plan.md").exists()

    for path in written:
        assert not path.is_absolute()
        assert (project_dir / path).exists()
        assert not str(path).endswith(".tmpl")

    claude_md = (project_dir / "CLAUDE.md").read_text(encoding="utf-8")
    assert "my-app" in claude_md
    assert "{{" not in claude_md
    assert "docs/handoffs/README.md" in claude_md

    architecture = (project_dir / "docs" / "architecture.md").read_text(encoding="utf-8")
    assert "my-app" in architecture
    assert "{{" not in architecture

    handoffs_readme = (project_dir / "docs" / "handoffs" / "README.md").read_text(encoding="utf-8")
    assert "{{" not in handoffs_readme


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
            "include_agents",
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
        _answers(tmp_path, include_skills=False, include_mcp=False, include_docs=False, include_agents=False),
        project_dir,
        CATALOG,
        PIN,
    )

    assert written == [Path("CLAUDE.md"), Path("README.md"), Path(".dev-ready.json")]
    assert (project_dir / "CLAUDE.md").exists()
    assert (project_dir / "README.md").exists()
    assert (project_dir / ".dev-ready.json").exists()
    assert not (project_dir / ".claude").exists()
    assert not (project_dir / ".mcp.json").exists()
    assert not (project_dir / "docs").exists()


def test_coexistence_docs_and_agents(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    apply_overlay(_answers(tmp_path, include_docs=True, include_agents=True), project_dir, CATALOG, PIN)
    assert (project_dir / "docs" / "architecture.md").exists()
    assert (project_dir / "docs" / "handoffs" / "README.md").exists()


def test_docs_without_agents(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    apply_overlay(_answers(tmp_path, include_docs=True, include_agents=False), project_dir, CATALOG, PIN)
    assert (project_dir / "docs" / "architecture.md").exists()
    assert not (project_dir / "docs" / "handoffs").exists()


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
def test_invalid_project_name_raises_overlay_error(tmp_path: Path, bad_name: str) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    with pytest.raises(OverlayError):
        apply_overlay(_answers(tmp_path, project_name=bad_name), project_dir, CATALOG, PIN)

    assert list(project_dir.iterdir()) == []


def test_leftover_template_marker_raises_overlay_error(tmp_path: Path) -> None:
    """Exercises the real substitution + leftover-marker guard in _apply_file."""
    import dev_ready.overlay as overlay_module

    source = tmp_path / "asset.txt.tmpl"
    source.write_text("hello {{project_name}}, also {{unresolved}}", encoding="utf-8")
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    with pytest.raises(OverlayError, match="template marker"):
        overlay_module._apply_file(source, project_dir, Path("out.txt"), "my-app")

    assert not (project_dir / "out.txt").exists()


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
    assert data["stamp_version"] == 2
    assert data["dev_ready_version"] == __version__
    assert data["components"]["skills"]["included"] is True
    assert data["components"]["skills"]["items"] == [
        {"id": "project-orientation", "pin": None},
        {"id": "react-doctor", "pin": "0.8.1"},
    ]
    assert data["components"]["mcp"]["included"] is True
    assert data["components"]["mcp"]["items"] == [{"id": "code-memory", "pin": "0.9.0"}]
    assert data["components"]["docs"]["included"] is True
    assert data["components"]["agents"]["included"] is True
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


def test_code_memory_preserves_existing_mcp_servers(tmp_path: Path) -> None:
    import dev_ready.overlay as overlay_module

    project_dir = tmp_path / "project"
    project_dir.mkdir()
    mcp_path = project_dir / ".mcp.json"
    mcp_path.write_text(
        json.dumps({"mcpServers": {"existing-server": {"command": "node", "args": ["index.js"]}}}),
        encoding="utf-8",
    )

    code_memory_item = next(item for item in CATALOG["mcp"] if item.id == "code-memory")
    overlay_module._inject_mcp_server(code_memory_item, project_dir)

    mcp_json = json.loads(mcp_path.read_text(encoding="utf-8"))
    assert "existing-server" in mcp_json["mcpServers"]
    assert "codebase-memory" in mcp_json["mcpServers"]
    assert mcp_json["mcpServers"]["existing-server"]["command"] == "node"
    assert mcp_json["mcpServers"]["codebase-memory"]["args"] == ["codebase-memory-mcp==0.9.0"]


def test_code_memory_without_mcp_config_raises_overlay_error(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    with pytest.raises(OverlayError, match="include 'mcp-config' as well"):
        apply_overlay(
            _answers(tmp_path, mcp_items=frozenset({"code-memory"})),
            project_dir,
            CATALOG,
            PIN,
        )


def test_mcp_server_collision_raises_overlay_error(tmp_path: Path) -> None:
    import dev_ready.overlay as overlay_module

    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / ".mcp.json").write_text(
        json.dumps({"mcpServers": {"codebase-memory": {"command": "existing"}}}),
        encoding="utf-8",
    )

    code_memory_item = next(item for item in CATALOG["mcp"] if item.id == "code-memory")
    with pytest.raises(OverlayError, match="already exists"):
        overlay_module._inject_mcp_server(code_memory_item, project_dir)


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
    skill_path = project_dir / ".claude" / "skills" / "react-doctor" / "SKILL.md"
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


def test_npm_dev_dependency_pkg_collision_raises_overlay_error(tmp_path: Path) -> None:
    import dev_ready.overlay as overlay_module

    project_dir = tmp_path / "project"
    project_dir.mkdir()
    pkg_json_path = project_dir / "frontend" / "package.json"
    pkg_json_path.parent.mkdir()
    pkg_json_path.write_text(
        json.dumps({"devDependencies": {"react-doctor": "0.8.0"}}), encoding="utf-8"
    )

    react_doctor_item = next(item for item in CATALOG["skills"] if item.id == "react-doctor")
    with pytest.raises(OverlayError, match="already declared"):
        overlay_module._inject_npm_dev_dependency(react_doctor_item, project_dir)


def test_npm_dev_dependency_script_collision_raises_overlay_error(tmp_path: Path) -> None:
    import dev_ready.overlay as overlay_module

    project_dir = tmp_path / "project"
    project_dir.mkdir()
    pkg_json_path = project_dir / "frontend" / "package.json"
    pkg_json_path.parent.mkdir()
    pkg_json_path.write_text(
        json.dumps({"scripts": {"doctor": "echo doctor"}}), encoding="utf-8"
    )

    react_doctor_item = next(item for item in CATALOG["skills"] if item.id == "react-doctor")
    with pytest.raises(OverlayError, match="already declared"):
        overlay_module._inject_npm_dev_dependency(react_doctor_item, project_dir)


def test_render_stamp_records_vendored_pins(tmp_path: Path) -> None:
    manifest = load_default_manifest()
    answers = _answers(tmp_path, skills_items=frozenset({"caveman", "project-orientation"}))
    raw = render_stamp(answers, PIN, manifest.components, manifest.vendored)
    data = json.loads(raw)
    assert data["stamp_version"] == 2
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
        ".claude/skills/webapp-testing/SKILL.md",
        ".claude/skills/webapp-testing/LICENSE.txt",
        ".claude/skills/webapp-testing/scripts/with_server.py",
        ".claude/skills/webapp-testing/examples/console_logging.py",
        ".claude/skills/frontend-design/SKILL.md",
        ".claude/skills/frontend-design/LICENSE.txt",
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
    assert data["stamp_version"] == 2
    items = data["components"]["skills"]["items"]
    webapp_item = next(i for i in items if i["id"] == "webapp-testing")
    assert webapp_item["pin"] == "1f630fdf9259cec4a14913127dfd7c3b69ef72eb"




