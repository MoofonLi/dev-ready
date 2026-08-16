"""Unit tests for dev_ready.overlay (no network, filesystem confined to tmp_path)."""

from pathlib import Path
import hashlib
import re
from dataclasses import replace

import pytest

import json

from dev_ready import __version__
from dev_ready.errors import InvalidArgumentsError, OverlayError
from dev_ready.inspection import ProjectExpectation, REQUIRED_UPSTREAM_PATHS, inspect_project
from dev_ready.manifest import AgentTarget, ComponentCatalog, UpstreamPin, load_default_manifest
from dev_ready.overlay import apply_overlay, build_overlay_content, render_stamp
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
    agent_targets: frozenset[str] = frozenset({"claude", "windsurf"}),
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
        ),
    )


def _selection_case(
    selection_name: str,
    *,
    mixed_skills: frozenset[str],
) -> ProjectSelection:
    if selection_name == "everything":
        return ProjectSelection.all(CATALOG)
    if selection_name == "nothing":
        return ProjectSelection.empty()
    assert selection_name == "mixed"
    return ProjectSelection.from_items(
        CATALOG,
        skills=mixed_skills,
        mcp=frozenset(),
        agent_targets=frozenset({"claude"}),
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


def test_default_set_tree_contains_structure_and_no_enhancements(tmp_path: Path) -> None:
    project_dir = tmp_path / "default-set"
    project_dir.mkdir()
    answers = Answers(
        "my-app",
        project_dir,
        ProjectSelection.default_set(CATALOG),
    )

    apply_overlay(answers, project_dir, CATALOG, PIN)

    assert (project_dir / ".agents" / "skills" / "implement" / "SKILL.md").is_file()
    assert (project_dir / "docs" / "architecture.md").is_file()
    assert (project_dir / "docs" / "requirements.md").is_file()
    assert not (project_dir / ".agents" / "skills" / "caveman").exists()
    assert not (project_dir / ".mcp.json").exists()
    assert not (project_dir / "docs" / "design-stripe.md").exists()
    assert not (project_dir / "docs" / "design-linear.md").exists()

    generated_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in project_dir.rglob("*")
        if path.is_file() and path.suffix in {".md", ".json", ".yaml"}
    )
    assert "setup-matt-pocock-skills" in generated_text


def test_shared_agent_target_directory_writes_one_stub_tree_and_inspects_cleanly(
    tmp_path: Path,
) -> None:
    shared_targets = {
        target_id: AgentTarget(
            id=target_id,
            description=f"{target_id} shared target",
            skills_dir=".shared/skills",
            rules_file=None,
            mcp_file=None,
        )
        for target_id in ("alpha", "beta")
    }
    catalog = ComponentCatalog(CATALOG, shared_targets)
    selection = ProjectSelection.from_items(
        catalog,
        skills=frozenset({"mattpocock"}),
        agent_targets=frozenset(shared_targets),
    )
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    for relative in REQUIRED_UPSTREAM_PATHS:
        path = project_dir / relative
        if relative in {"backend", "frontend"}:
            path.mkdir()
        else:
            path.write_text("upstream\n", encoding="utf-8")

    written = apply_overlay(Answers("my-app", project_dir, selection), project_dir, catalog, PIN)

    shared_stubs = list((project_dir / ".shared/skills").glob("*/SKILL.md"))
    assert len(shared_stubs) == len(
        tuple(path for path in project_dir.glob(".agents/skills/*/SKILL.md"))
    )
    assert inspect_project(
        project_dir,
        catalog,
        ProjectExpectation.generation(selection),
    ) == ()
    assert all(not path.is_absolute() for path in written)
    assert all((project_dir / path).resolve().is_relative_to(project_dir.resolve()) for path in written)


def test_overlay_still_rejects_a_genuine_duplicate_destination(tmp_path: Path) -> None:
    catalog = ComponentCatalog(
        CATALOG,
        {
            "collision": AgentTarget(
                id="collision",
                description="Rules collide with overlay infrastructure.",
                skills_dir=".collision/skills",
                rules_file="README.md",
                mcp_file=None,
            )
        },
    )
    selection = ProjectSelection.from_items(
        catalog,
        skills=frozenset({"mattpocock"}),
        agent_targets=frozenset({"collision"}),
    )

    with pytest.raises(OverlayError, match="overlay destination collision: README.md"):
        build_overlay_content(Answers("my-app", tmp_path / "project", selection), catalog)


def test_real_shared_directory_pair_generates_one_stub_tree(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    selection = ProjectSelection.from_items(
        CATALOG,
        skills=frozenset({"mattpocock"}),
        agent_targets=frozenset({"qoder", "qoder-cn"}),
    )

    apply_overlay(Answers("my-app", project_dir, selection), project_dir, CATALOG, PIN)

    canonical = tuple(project_dir.glob(".agents/skills/*/SKILL.md"))
    shared = tuple(project_dir.glob(".qoder/skills/*/SKILL.md"))
    assert len(shared) == len(canonical)
    assert not (project_dir / ".qoder-cn").exists()


def test_setup_skill_arrives_through_the_mandatory_development_loop(
    tmp_path: Path,
) -> None:
    project_dir = tmp_path / "setup-selected"
    project_dir.mkdir()
    selection = ProjectSelection.default_set(CATALOG)

    apply_overlay(Answers("my-app", project_dir, selection), project_dir, CATALOG, PIN)

    assert (
        project_dir
        / ".agents"
        / "skills"
        / "setup-matt-pocock-skills"
        / "SKILL.md"
    ).is_file()
    assert (project_dir / "docs" / "agents" / "issue-tracker.md").is_file()
    assert (project_dir / "docs" / "agents" / "domain.md").is_file()
    code_review = (
        project_dir / ".agents" / "skills" / "code-review" / "SKILL.md"
    ).read_text(encoding="utf-8")
    assert "run `/setup-matt-pocock-skills`" in code_review


@pytest.mark.parametrize("selection_name", ["everything", "nothing", "mixed"])
def test_no_selection_writes_handoff_protocol_paths(
    tmp_path: Path, selection_name: str
) -> None:
    selection = _selection_case(
        selection_name,
        mixed_skills=frozenset({"mattpocock"}),
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
    selection = _selection_case(
        selection_name,
        mixed_skills=frozenset({"caveman"}),
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


@pytest.mark.parametrize("selection_name", ["everything", "nothing", "mixed"])
def test_every_selection_writes_setup_project_canonical_skill(
    tmp_path: Path, selection_name: str
) -> None:
    selection = _selection_case(
        selection_name,
        mixed_skills=frozenset({"caveman"}),
    )
    content = build_overlay_content(
        Answers("my-app", tmp_path / selection_name, selection), CATALOG
    )

    assert ".agents/skills/setup-project/SKILL.md" in content


def test_apply_overlay_stamp_inventory_hashes_rendered_non_inject_files(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    apply_overlay(_answers(tmp_path), project_dir, CATALOG, PIN)

    stamp = json.loads((project_dir / ".dev-ready.json").read_text(encoding="utf-8"))
    inventory = {entry["path"]: entry["sha256"] for entry in stamp["inventory"]}
    for path in (
        "AGENTS.md",
        "CLAUDE.md",
        ".agents/skills/setup-project/SKILL.md",
        ".claude/skills/setup-project/SKILL.md",
        ".agents/skills/caveman/SKILL.md",
        ".claude/skills/caveman/SKILL.md",
        "docs/agents/mattpocock.md",
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


def test_setup_project_reaches_every_selected_agent_target(tmp_path: Path) -> None:
    content = build_overlay_content(_answers(tmp_path), CATALOG)
    canonical_path = ".agents/skills/setup-project/SKILL.md"

    assert canonical_path in content
    for stub_path in (
        ".claude/skills/setup-project/SKILL.md",
        ".windsurf/skills/setup-project/SKILL.md",
    ):
        stub = content[stub_path].decode("utf-8")
        assert "name: setup-project" in stub
        assert "description: Configure a generated project before first start" in stub
        assert "disable-model-invocation: true" in stub
        assert canonical_path in stub


def test_setup_project_is_original_infrastructure_not_manifest_content(
    tmp_path: Path,
) -> None:
    manifest = load_default_manifest()
    content = build_overlay_content(
        _answers(tmp_path, agent_targets=frozenset()), manifest.components
    )
    setup_skill = content[".agents/skills/setup-project/SKILL.md"].decode("utf-8")

    assert "disable-model-invocation: true" in setup_skill
    assert "{{" not in setup_skill
    assert "}}" not in setup_skill
    assert not any("setup-project" in flow.steps for flow in manifest.components.loops())
    assert not any(
        "setup-project" in path.src or "setup-project" in path.dest
        for pin in manifest.vendored
        for path in pin.paths
    )
    assert not any(
        path.startswith(".claude/skills/setup-project/")
        or path.startswith(".windsurf/skills/setup-project/")
        for path in content
    )


def test_setup_project_offers_email_and_error_reporting_as_individual_sections(
    tmp_path: Path,
) -> None:
    content = build_overlay_content(_answers(tmp_path), CATALOG)

    router = content[".agents/skills/setup-project/SKILL.md"].decode("utf-8")
    walk_path = ".agents/skills/setup-project/email-and-error-reporting.md"
    walk = content[walk_path].decode("utf-8")
    assert "**Email sending**" in router
    assert "**Error reporting**" in router
    assert "email-and-error-reporting.md" in router
    assert "default is No" in walk
    for index, key in enumerate(
        ("SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD", "EMAILS_FROM_EMAIL"),
        start=1,
    ):
        assert f"{index}. `{key}`" in walk
    assert "1. `SENTRY_DSN`" in walk
    assert "asks exactly\nfive values" in walk
    assert "Email sending alone never walks through Error reporting" in walk
    assert "Error reporting alone never asks for SMTP values" in walk
    assert "stored transcript" in walk
    assert "Leave this blank" in walk
    assert "SMTP_PORT=587" in walk
    assert "SMTP_TLS=True" in walk
    assert "SMTP_SSL=False" in walk
    assert "data loss" not in walk.lower()
    assert "{{" not in walk
    assert "}}" not in walk


def test_setup_project_uses_the_selected_flow_configuration_handoff(
    tmp_path: Path,
) -> None:
    manifest = load_default_manifest()
    content = build_overlay_content(_answers(tmp_path), manifest.components)
    setup_skill = content[".agents/skills/setup-project/SKILL.md"].decode("utf-8")
    flow = next(item for item in manifest.components.loops() if item.id == "mattpocock")

    assert "docs/agents/issue-tracker.md" in setup_skill
    assert "docs/agents/triage-labels.md" in setup_skill
    assert "docs/agents/domain.md" in setup_skill
    assert "setup-matt-pocock-skills" in setup_skill
    assert "user-modified" in setup_skill
    assert "stops updating" in setup_skill
    assert "setup-matt-pocock-skills" in flow.steps
    assert "{{" not in setup_skill


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
    assert (project_dir / ".agents/skills/setup-project/SKILL.md").is_file()
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
            Path("docs") / "design-stripe.md",
            [
                Path(".mcp.json"),
                Path(".claude") / "skills" / "caveman" / "SKILL.md",
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


def test_mandatory_loop_is_present_with_all_enhancements_disabled(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    written = apply_overlay(
        _answers(tmp_path, include_skills=False, include_mcp=False, include_docs=False),
        project_dir,
        CATALOG,
        PIN,
    )

    assert Path(".agents/skills/implement/SKILL.md") in written
    assert (project_dir / "AGENTS.md").exists()
    assert (project_dir / "CLAUDE.md").exists()
    assert (project_dir / "README.md").exists()
    assert (project_dir / ".dev-ready.json").exists()
    assert (project_dir / ".claude" / "skills" / "implement" / "SKILL.md").is_file()
    assert (project_dir / ".agents" / "skills" / "implement" / "SKILL.md").is_file()
    assert not (project_dir / ".mcp.json").exists()
    assert (project_dir / "docs" / "architecture.md").is_file()
    assert (project_dir / "docs" / "requirements.md").is_file()
    assert "docs/architecture.md" in (project_dir / "AGENTS.md").read_text(
        encoding="utf-8"
    )


@pytest.mark.parametrize("include_docs", [False, True])
def test_mandatory_engineering_flow_renders_independently_of_documentation_items(
    tmp_path: Path,
    include_docs: bool,
) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    answers = _answers(
        tmp_path,
        skills_items=frozenset(),
        include_mcp=False,
        include_docs=include_docs,
    )

    apply_overlay(answers, project_dir, CATALOG, PIN)

    claude_md = (project_dir / "CLAUDE.md").read_text(encoding="utf-8")
    assert claude_md == "@AGENTS.md\n"
    agents_md = (project_dir / "AGENTS.md").read_text(encoding="utf-8")
    assert not (project_dir / "docs" / "handoffs").exists()
    assert (project_dir / ".claude" / "skills" / "to-spec" / "SKILL.md").is_file()
    assert (project_dir / "docs" / "agents" / "issue-tracker.md").is_file()
    assert (project_dir / "docs" / "architecture.md").is_file()
    assert (project_dir / "docs" / "requirements.md").is_file()
    assert "## Handoff Protocol" not in agents_md
    assert "## Engineering Flow" in agents_md
    assert "docs/architecture.md" in agents_md
    assert "## Process-v2 role mapping" not in agents_md

    tracker = (project_dir / "docs" / "agents" / "issue-tracker.md").read_text(
        encoding="utf-8"
    )
    assert "docs/specs/" not in tracker
    assert "docs/handoffs/" not in tracker
    assert ".scratch/" in tracker

    architecture = (project_dir / "docs" / "architecture.md").read_text(
        encoding="utf-8"
    )
    for heading in ("## System Overview", "## Module Boundary", "## Dependency Rules"):
        assert heading in architecture
    assert "`tech_lead`" not in architecture

    assert "{{" not in agents_md


def test_selected_flow_without_authored_guidance_fails_at_overlay_seam(
    tmp_path: Path,
) -> None:
    loop = next(item for item in CATALOG.loops() if item.id == "mattpocock")
    unmapped_loop = replace(loop, id="unmapped-flow")
    components = {
        component: tuple(
            unmapped_loop if item.id == loop.id else item
            for item in CATALOG.get(component, ())
        )
        for component in CATALOG
    }
    catalog = ComponentCatalog(
        components,
        CATALOG.agent_targets,
        CATALOG.categories,
        CATALOG.default_set,
        CATALOG.standard_compliant_agents,
        CATALOG.announced_loops,
    )
    selection = ProjectSelection.from_items(
        catalog,
        skills=frozenset({"unmapped-flow"}),
        agent_targets=frozenset(),
    )

    with pytest.raises(OverlayError, match="flow guidance is missing: unmapped-flow"):
        build_overlay_content(Answers("my-app", tmp_path / "project", selection), catalog)


def test_engineering_flow_guidance_states_the_exact_chain_and_skip_rule(
    tmp_path: Path,
) -> None:
    content = build_overlay_content(_answers(tmp_path), CATALOG)
    agents_md = content["AGENTS.md"].decode("utf-8")

    guidance = agents_md.split("## Engineering Flow\n", 1)[1].split(
        "\n\n## Architecture documentation", 1
    )[0]
    assert guidance == (
        "\nThe default Flow Chain is `setup-project` → `grill-with-docs` → "
        "`to-spec` → `to-tickets` → `implement` → "
        "`improve-codebase-architecture`. Every step is user-invoked.\n\n"
        "A step may reach for `tdd`, `code-review`, `diagnosing-bugs`, "
        "`codebase-design`, or `domain-modeling` as a tool; those tools are not "
        "additional chain entries.\n\nStart at `implement` when the change adds no "
        "behaviour a user can observe — a rename, a formatting fix, a dependency "
        "bump, or a test for behaviour that already works. Start at `setup-project` "
        "or `grill-with-docs` for everything else.\n\nTracker and domain "
        "conventions are in `docs/agents/issue-tracker.md`, "
        "`docs/agents/triage-labels.md`, and `docs/agents/domain.md`. Follow those "
        "files when a skill asks where to publish specs or tickets; domain "
        "terminology is created lazily when a real term is resolved."
    )
    assert all(
        "## Spec Loop" not in data.decode("utf-8")
        for data in content.values()
    )


def test_selected_flow_writes_its_human_explainer_and_unselected_flow_does_not(
    tmp_path: Path,
) -> None:
    selected = build_overlay_content(_answers(tmp_path), CATALOG)
    unselected = build_overlay_content(
        Answers("my-app", tmp_path / "empty", ProjectSelection.empty()), CATALOG
    )
    explainer_path = "docs/agents/mattpocock.md"

    assert explainer_path in selected
    assert explainer_path not in unselected
    explainer = selected[explainer_path].decode("utf-8")
    for step in (
        "setup-project",
        "grill-with-docs",
        "to-spec",
        "to-tickets",
        "implement",
        "improve-codebase-architecture",
    ):
        assert f"`{step}`" in explainer
    assert "does not need to finish in one session" in explainer
    assert "no behaviour a user can observe" in explainer
    assert "For everything else" in explainer
    assert "otherwise start at `grill-with-docs`" in explainer


def test_readme_is_about_the_project_not_the_template(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    apply_overlay(_answers(tmp_path), project_dir, CATALOG, PIN)

    readme = (project_dir / "README.md").read_text(encoding="utf-8")
    assert "my-app" in readme
    assert "{{" not in readme
    assert "MoofonLi/dev-ready" in readme
    assert "img/" not in readme


# The root ignore file at the manifest-pinned upstream commit, in upstream's own
# order. Restated here so a silent drop is a test failure; scripts/check_ignore_drift.py
# is what keeps this honest against the real repository.
_UPSTREAM_IGNORE_ENTRIES = [
    ".vscode/*",
    "!.vscode/extensions.json",
    "node_modules/",
    "backend/app/frontend/",
    "/test-results/",
    "/playwright-report/",
    "/blob-report/",
    "/playwright/.cache/",
]


def _ignore_entries(text: str) -> list[str]:
    """Return the ignore patterns a git implementation would act on."""
    return [
        line for line in text.splitlines() if line.strip() and not line.startswith("#")
    ]


def _bare_answers(tmp_path: Path) -> Answers:
    """A selection that takes nothing at all — the `--yes`-with-empty-Category case."""
    return _answers(
        tmp_path,
        include_skills=False,
        include_mcp=False,
        include_docs=False,
        agent_targets=frozenset({"claude"}),
    )


def test_generated_project_ignores_the_env_file_it_was_given_secrets_in(
    tmp_path: Path,
) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    apply_overlay(_bare_answers(tmp_path), project_dir, CATALOG, PIN)

    entries = _ignore_entries((project_dir / ".gitignore").read_text(encoding="utf-8"))
    assert ".env" in entries
    assert ".env*" in entries


def test_generated_ignore_file_keeps_upstream_entries_and_adds_only_the_env_lines(
    tmp_path: Path,
) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    apply_overlay(_bare_answers(tmp_path), project_dir, CATALOG, PIN)

    entries = _ignore_entries((project_dir / ".gitignore").read_text(encoding="utf-8"))
    assert entries == _UPSTREAM_IGNORE_ENTRIES + [".env", ".env*"]


def test_generated_ignore_file_is_inventoried_and_matches_the_bytes_on_disk(
    tmp_path: Path,
) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    written = apply_overlay(_bare_answers(tmp_path), project_dir, CATALOG, PIN)

    assert Path(".gitignore") in written
    stamp = json.loads((project_dir / ".dev-ready.json").read_text(encoding="utf-8"))
    inventory = {entry["path"]: entry["sha256"] for entry in stamp["inventory"]}
    assert inventory[".gitignore"] == hashlib.sha256(
        (project_dir / ".gitignore").read_bytes()
    ).hexdigest()


def test_readme_names_the_superuser_login_and_the_first_start_rule(
    tmp_path: Path,
) -> None:
    """FR-38: the report scrolls away; the README is what survives the session."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    apply_overlay(_bare_answers(tmp_path), project_dir, CATALOG, PIN)

    readme = (project_dir / "README.md").read_text(encoding="utf-8")
    assert "admin@example.com" in readme
    assert "FIRST_SUPERUSER_PASSWORD" in readme
    assert "`.env`" in readme
    assert "first start" in readme
    assert "reset" in readme


def test_readme_names_the_password_key_but_never_a_value(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    apply_overlay(_bare_answers(tmp_path), project_dir, CATALOG, PIN)

    readme = (project_dir / "README.md").read_text(encoding="utf-8")
    assert "FIRST_SUPERUSER_PASSWORD=" not in readme
    assert "SECRET_KEY" not in readme
    assert "POSTGRES_PASSWORD" not in readme


def test_ignore_file_is_written_verbatim_without_template_markers(
    tmp_path: Path,
) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    apply_overlay(_bare_answers(tmp_path), project_dir, CATALOG, PIN)

    text = (project_dir / ".gitignore").read_text(encoding="utf-8")
    assert "{{" not in text
    assert text.endswith("\n")


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
    assert data["categories"] == ["design", "dev", "quality", "token-optimize"]
    assert data["project_name"] == "my-app"
    assert data["inventory"] == []
    assert data["dev_ready_version"] == __version__
    assert data["components"]["skills"]["included"] is True
    assert data["components"]["skills"]["items"] == [
        {"id": "caveman", "pin": None},
        {"id": "mattpocock", "pin": None},
        {"id": "react-doctor", "pin": "0.8.1"},
    ]
    assert data["development_loop"] == "mattpocock"
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


def test_selected_mount_appends_derived_guidance_to_the_loop_skill(
    tmp_path: Path,
) -> None:
    content = build_overlay_content(
        _answers(
            tmp_path,
            skills_items=frozenset({"react-doctor"}),
            include_mcp=False,
            include_docs=False,
            agent_targets=frozenset(),
        ),
        CATALOG,
    )

    code_review = content[".agents/skills/code-review/SKILL.md"].decode("utf-8")
    assert code_review.endswith(
        "\n\n<!-- dev-ready:mounted-enhancements:start -->\n"
        "## Mounted enhancements\n\n"
        "When running this skill, also apply the enhancements selected for this project.\n\n"
        "- **react-doctor** — Wrapper skill teaching the agent when to run "
        "react-doctor on the frontend and how to act on its findings. "
        "See `.agents/skills/react-doctor`.\n"
        "<!-- dev-ready:mounted-enhancements:end -->\n"
    )


def test_review_mount_lists_both_selected_enhancements_in_identifier_order(
    tmp_path: Path,
) -> None:
    content = build_overlay_content(
        _answers(
            tmp_path,
            skills_items=frozenset({"react-doctor", "security-audit"}),
            include_mcp=False,
            include_docs=False,
            agent_targets=frozenset(),
        ),
        CATALOG,
    )

    code_review = content[".agents/skills/code-review/SKILL.md"].decode("utf-8")
    assert code_review.count("<!-- dev-ready:mounted-enhancements:start -->") == 1
    assert code_review.count("<!-- dev-ready:mounted-enhancements:end -->") == 1
    react_entry = (
        "- **react-doctor** — Wrapper skill teaching the agent when to run "
        "react-doctor on the frontend and how to act on its findings. "
        "See `.agents/skills/react-doctor`."
    )
    security_entry = (
        "- **security-audit** — Multi-phase security auditing skill for "
        "vulnerability scanning and risk assessment. "
        "See `.agents/skills/security-audit`."
    )
    assert react_entry in code_review
    assert security_entry in code_review
    assert code_review.index(react_entry) < code_review.index(security_entry)


def test_document_mount_collapses_selected_references_to_one_directory_line(
    tmp_path: Path,
) -> None:
    content = build_overlay_content(
        _answers(
            tmp_path,
            skills_items=frozenset(),
            include_mcp=False,
            docs_items=frozenset({"design-stripe", "design-linear"}),
            agent_targets=frozenset(),
        ),
        CATALOG,
    )

    implement = content[".agents/skills/implement/SKILL.md"].decode("utf-8")
    documentation_entry = (
        "- **Documentation references** — `design-linear`, `design-stripe`. "
        "See `docs/`."
    )
    assert documentation_entry in implement
    assert implement.count("\n- **Documentation references**") == 1
    assert "See `docs/design-linear.md`." not in implement
    assert "See `docs/design-stripe.md`." not in implement


def test_mixed_mount_keeps_skill_guidance_before_collapsed_documentation(
    tmp_path: Path,
) -> None:
    content = build_overlay_content(
        _answers(
            tmp_path,
            skills_items=frozenset({"frontend-design"}),
            include_mcp=False,
            docs_items=frozenset({"design-stripe", "design-linear"}),
            agent_targets=frozenset(),
        ),
        CATALOG,
    )

    implement = content[".agents/skills/implement/SKILL.md"].decode("utf-8")
    skill_entry = (
        "- **frontend-design** — Methodology skill for how to build high-quality "
        "frontend UI — layout, spacing, visual hierarchy, and interaction polish. "
        "Distinct from the awesome-design-md DESIGN.md reference templates in the "
        "docs component (which show what good design systems like Stripe and Linear "
        "look like): this is the how-to process, those are the what-good-looks-like "
        "references. Vendored from anthropics/skills (Apache-2.0). "
        "See `.agents/skills/frontend-design`."
    )
    documentation_entry = (
        "- **Documentation references** — `design-linear`, `design-stripe`. "
        "See `docs/`."
    )
    assert skill_entry in implement
    assert documentation_entry in implement
    assert implement.index(skill_entry) < implement.index(documentation_entry)


def test_browser_testing_mounts_on_the_test_writing_step(tmp_path: Path) -> None:
    content = build_overlay_content(
        _answers(
            tmp_path,
            skills_items=frozenset({"webapp-testing"}),
            include_mcp=False,
            include_docs=False,
            agent_targets=frozenset(),
        ),
        CATALOG,
    )

    tdd = content[".agents/skills/tdd/SKILL.md"].decode("utf-8")
    assert tdd.endswith(
        "\n\n<!-- dev-ready:mounted-enhancements:start -->\n"
        "## Mounted enhancements\n\n"
        "When running this skill, also apply the enhancements selected for this project.\n\n"
        "- **webapp-testing** — Browser-automation skill for testing web apps "
        "end-to-end — drives a headless browser to exercise UI flows, capture "
        "console logs, and discover elements. Vendored from anthropics/skills "
        "(Apache-2.0). See `.agents/skills/webapp-testing`.\n"
        "<!-- dev-ready:mounted-enhancements:end -->\n"
    )


def test_unmounted_enhancements_do_not_change_loop_skills(tmp_path: Path) -> None:
    baseline = build_overlay_content(
        _answers(
            tmp_path,
            skills_items=frozenset(),
            include_mcp=False,
            include_docs=False,
            agent_targets=frozenset(),
        ),
        CATALOG,
    )
    selected = build_overlay_content(
        _answers(
            tmp_path,
            skills_items=frozenset({"caveman"}),
            mcp_items=frozenset({"code-memory"}),
            include_docs=False,
            agent_targets=frozenset(),
        ),
        CATALOG,
    )
    loop = next(item for item in CATALOG.loops() if item.id == "mattpocock")
    loop_skill_paths = {
        f"{item_path.dest}/SKILL.md"
        for item_path in loop.paths
        if item_path.dest.startswith(".agents/skills/")
    }

    assert {path: selected[path] for path in loop_skill_paths} == {
        path: baseline[path] for path in loop_skill_paths
    }


def test_default_set_leaves_every_loop_skill_byte_identical_to_its_template(
    tmp_path: Path,
) -> None:
    from importlib import resources

    answers = Answers(
        "my-app",
        tmp_path / "project",
        ProjectSelection.default_set(CATALOG),
    )

    content = build_overlay_content(answers, CATALOG)
    templates_root = resources.files("dev_ready").joinpath("templates")
    loop = next(item for item in CATALOG.loops() if item.id == "mattpocock")
    template_bytes = {
        f"{item_path.dest}/SKILL.md": templates_root.joinpath(
            *item_path.src.split("/"), "SKILL.md"
        ).read_bytes()
        for item_path in loop.paths
        if item_path.dest.startswith(".agents/skills/")
    }

    assert {path: content[path] for path in template_bytes} == template_bytes


def test_mounted_guidance_is_deterministic_and_does_not_change_pointer_stubs(
    tmp_path: Path,
) -> None:
    without_mount = build_overlay_content(
        _answers(
            tmp_path,
            skills_items=frozenset(),
            include_mcp=False,
            include_docs=False,
            agent_targets=frozenset({"claude"}),
        ),
        CATALOG,
    )
    answers = _answers(
        tmp_path,
        skills_items=frozenset({"react-doctor"}),
        include_mcp=False,
        include_docs=False,
        agent_targets=frozenset({"claude"}),
    )

    first = build_overlay_content(answers, CATALOG)
    second = build_overlay_content(answers, CATALOG)

    assert first == second
    assert (
        first[".claude/skills/code-review/SKILL.md"]
        == without_mount[".claude/skills/code-review/SKILL.md"]
    )


def test_mounted_skill_inventory_hash_matches_written_bytes(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    (project_dir / "frontend").mkdir(parents=True)
    (project_dir / "frontend" / "package.json").write_text(
        json.dumps({"scripts": {}, "devDependencies": {}}),
        encoding="utf-8",
    )

    apply_overlay(
        _answers(
            tmp_path,
            skills_items=frozenset({"react-doctor"}),
            include_mcp=False,
            include_docs=False,
        ),
        project_dir,
        CATALOG,
        PIN,
    )

    stamp = json.loads((project_dir / ".dev-ready.json").read_text(encoding="utf-8"))
    inventory = {entry["path"]: entry["sha256"] for entry in stamp["inventory"]}
    mounted_path = ".agents/skills/code-review/SKILL.md"
    assert inventory[mounted_path] == hashlib.sha256(
        (project_dir / mounted_path).read_bytes()
    ).hexdigest()


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

    selected_items = frozenset(
        {
            "caveman",
            "security-audit",
            "webapp-testing",
            "frontend-design",
        }
    )
    expected_skill_dirs = selected_items | {
        "tdd",
        "diagnosing-bugs",
        "code-review",
        "setup-matt-pocock-skills",
    }
    answers = _answers(tmp_path, skills_items=selected_items, include_docs=True)

    written = apply_overlay(answers, project_dir, manifest.components, PIN, manifest.vendored)

    for skill in expected_skill_dirs:
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

    optional_vendored_skills = {
        "caveman",
        "security-audit",
        "webapp-testing",
        "frontend-design",
    }
    for skill in optional_vendored_skills:
        assert not (project_dir / ".claude" / "skills" / skill).exists()
        assert Path(f".claude/skills/{skill}/SKILL.md") not in written
    for skill in {"tdd", "diagnosing-bugs", "code-review"}:
        assert (project_dir / ".claude" / "skills" / skill / "SKILL.md").is_file()


def test_lean_selection_carries_the_notice_in_every_engineering_flow_skill(
    tmp_path: Path,
) -> None:
    manifest = load_default_manifest()
    content = build_overlay_content(
        _answers(
            tmp_path,
            skills_items=frozenset(),
            include_mcp=False,
            include_docs=False,
            agent_targets=frozenset(),
        ),
        manifest.components,
    )
    flow_skills = (
        "tdd",
        "diagnosing-bugs",
        "code-review",
        "grill-with-docs",
        "grilling",
        "domain-modeling",
        "to-spec",
        "to-tickets",
        "implement",
        "improve-codebase-architecture",
        "codebase-design",
        "setup-matt-pocock-skills",
    )

    for skill in flow_skills:
        notice = content[f".agents/skills/{skill}/LICENSE"]
        assert hashlib.sha256(notice).hexdigest() == (
            "4981c5f6a90eb3a969dacabb9350f5a75695ff3910b39b6534952908dfdc5ff7"
        )


@pytest.mark.parametrize(
    ("skill", "expected_hash"),
    [
        (
            "caveman",
            "17a8a03e790cd0b662021daeefc008b0af05810c041215a95dfa19abc496d3b9",
        ),
        (
            "security-audit",
            "c007a58f958f8a5b2870aa35d8a17aa72a546447aecee6d2b72e19fea530890b",
        ),
    ],
)
def test_optional_mit_skill_notice_follows_its_selection(
    tmp_path: Path,
    skill: str,
    expected_hash: str,
) -> None:
    manifest = load_default_manifest()
    selected = build_overlay_content(
        _answers(
            tmp_path,
            skills_items=frozenset({skill}),
            include_mcp=False,
            include_docs=False,
            agent_targets=frozenset(),
        ),
        manifest.components,
    )
    deselected = build_overlay_content(
        _answers(
            tmp_path,
            skills_items=frozenset(),
            include_mcp=False,
            include_docs=False,
            agent_targets=frozenset(),
        ),
        manifest.components,
    )
    notice_path = f".agents/skills/{skill}/LICENSE"

    assert hashlib.sha256(selected[notice_path]).hexdigest() == expected_hash
    assert notice_path not in deselected


def test_mit_skill_notices_are_recorded_in_the_stamp_inventory(tmp_path: Path) -> None:
    manifest = load_default_manifest()
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    answers = _answers(
        tmp_path,
        skills_items=frozenset({"caveman", "security-audit"}),
        include_mcp=False,
        include_docs=False,
        agent_targets=frozenset(),
    )

    apply_overlay(answers, project_dir, manifest.components, PIN, manifest.vendored)

    stamp = json.loads((project_dir / ".dev-ready.json").read_text(encoding="utf-8"))
    inventory = {entry["path"]: entry["sha256"] for entry in stamp["inventory"]}
    for notice_path in (
        ".agents/skills/caveman/LICENSE",
        ".agents/skills/security-audit/LICENSE",
        ".agents/skills/implement/LICENSE",
    ):
        assert inventory[notice_path] == hashlib.sha256(
            (project_dir / notice_path).read_bytes()
        ).hexdigest()


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


def test_generated_agents_md_describes_stack_commands_and_standards_source(
    tmp_path: Path,
) -> None:
    answers = Answers(
        "my-app",
        tmp_path / "project",
        ProjectSelection.empty(),
    )

    agents_md = build_overlay_content(answers, CATALOG)["AGENTS.md"].decode("utf-8")

    for fact in (
        "Tailwind CSS",
        "shadcn/ui",
        "TanStack Query",
        "TanStack Router",
        "TanStack Table",
        "react-hook-form",
        "zod",
        "Alembic",
        "pytest",
        "coverage",
        "ruff check",
        "ruff format",
        "mypy",
        "ty",
        "Playwright",
        "biome",
        "tsc",
        "Bun",
        "90%",
        "Standards Source",
        "generated frontend API client",
        "generated route tree",
        "Alembic migration",
        "backend tests mirror",
        "live services required",
    ):
        assert fact in agents_md

    for command in (
        "docker compose up -d",
        "docker compose watch",
        "docker compose down",
        "cd backend && uv run fastapi dev app/main.py",
        "docker compose up -d db mailcatcher",
        "bash scripts/prestart.sh",
        "bash scripts/tests-start.sh",
        "cd backend && bash scripts/lint.sh",
        "cd backend && bash scripts/format.sh",
        "bun install",
        "cd frontend && bun run dev",
        "cd frontend && bunx playwright test",
        "cd frontend && bunx biome check ./",
        "cd frontend && bunx tsc -p tsconfig.build.json",
        "cd frontend && bunx biome format --write ./",
    ):
        assert command in agents_md

    stack_and_commands = agents_md.split("## Repo layout", 1)[0]
    assert not re.search(
        r"\b(?:Python|Bun|Node|React|TypeScript|Vite|FastAPI)\s+v?\d",
        stack_and_commands,
    )
    assert "frontend && npm install" not in agents_md
    assert "frontend && npm run dev" not in agents_md
    assert "biome check --write --unsafe" not in agents_md
    assert "pre-commit run" not in agents_md


def test_standalone_engineering_flow_is_complete_and_role_neutral(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    answers = _answers(
        tmp_path,
        skills_items=frozenset({"mattpocock"}),
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
    assert "## Engineering Flow" in claude_md
    assert "`to-tickets` → `implement` → `improve-codebase-architecture`" in claude_md
    assert "docs/agents/issue-tracker.md" in claude_md
    assert "Handoff Protocol" not in claude_md
    assert "tech_lead" not in claude_md


def test_declining_every_enhancement_keeps_bundle_configuration_and_guidance(
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

    assert (project_dir / "docs" / "agents" / "issue-tracker.md").is_file()
    claude_md = (project_dir / "AGENTS.md").read_text(encoding="utf-8")
    assert "Engineering Flow" in claude_md
    assert "Handoff Protocol" not in claude_md


def test_engineering_flow_stamp_records_the_resolved_selection_and_complete_inventory(
    tmp_path: Path,
) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    answers = _answers(
        tmp_path,
        skills_items=frozenset({"mattpocock"}),
        include_mcp=False,
        include_docs=False,
    )

    apply_overlay(answers, project_dir, CATALOG, PIN, load_default_manifest().vendored)

    stamp = json.loads((project_dir / ".dev-ready.json").read_text(encoding="utf-8"))
    assert stamp["development_loop"] == "mattpocock"
    assert {item["id"] for item in stamp["components"]["skills"]["items"]} == {
        "mattpocock"
    }
    assert stamp["components"]["docs"] == {"included": False, "items": []}
    inventory_paths = {entry["path"] for entry in stamp["inventory"]}
    assert ".agents/skills/domain-modeling/ADR-FORMAT.md" in inventory_paths
    assert "docs/agents/issue-tracker.md" in inventory_paths
    assert "docs/architecture.md" in inventory_paths
    assert "docs/requirements.md" in inventory_paths
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
        ),
    )
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    apply_overlay(answers, project_dir, custom_catalog, PIN)

    config = json.loads((project_dir / ".custom/mcp.json").read_text(encoding="utf-8"))
    assert "codebase-memory" in config["mcpServers"]
    assert not (project_dir / ".mcp.json").exists()





