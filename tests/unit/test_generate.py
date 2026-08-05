"""Unit tests for dev_ready.generate (no network; filesystem confined to tmp_path)."""

import tempfile
from pathlib import Path

import pytest

import dev_ready.generate as generate_module
from dev_ready.errors import FetchError, OverlayError, TargetDirectoryError, VerificationError
from dev_ready.generate import (
    CleanupWarningEvent,
    GenerationStage,
    ProgressEvent,
    ProgressStatus,
    generate,
)
from dev_ready.manifest import UpstreamPin, load_default_manifest
from dev_ready.prompts import Answers, ProjectSelection
from dev_ready.verify import REQUIRED_UPSTREAM_PATHS

PIN = UpstreamPin(
    repo="fastapi/full-stack-fastapi-template",
    ref="master",
    commit="4cd0d9e51aebd1af6f82d91ad0df4c9e41f4dea2",
    license="MIT",
)
CATALOG = load_default_manifest().components

_VERIFY_DIRECTORY_ENTRIES = {"backend", "frontend"}


def _answers(target_dir: Path, *, project_name: str = "my-app") -> Answers:
    return Answers(
        project_name=project_name,
        target_dir=target_dir,
        selection=ProjectSelection.from_items(
            CATALOG,
            skills=frozenset({"caveman"}),
            mcp=frozenset({"code-memory"}),
        ),
    )


@pytest.fixture(autouse=True)
def _isolated_tempdir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Force tempfile.mkdtemp() to land inside tmp_path so leak checks are deterministic."""
    temp_root = tmp_path / "_systmp"
    temp_root.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(temp_root))
    return temp_root


def _fake_fetch_ok(
    pin: UpstreamPin, dest: Path, template_data: dict[str, str] | None = None
) -> Path:
    dest.mkdir(parents=True)
    (dest / "backend").mkdir()
    (dest / "backend" / "main.py").write_text("print('hi')", encoding="utf-8")
    # Every path verify_project checks for must be present, or the happy-path
    # tests below would fail verification rather than exercising the thing
    # they're actually testing.
    for rel_path in REQUIRED_UPSTREAM_PATHS:
        path = dest / rel_path
        if rel_path in _VERIFY_DIRECTORY_ENTRIES:
            path.mkdir(exist_ok=True)
        elif not path.exists():
            path.write_text("stub", encoding="utf-8")
    return dest


def test_generate_happy_path_merges_upstream_and_overlay(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(generate_module, "fetch_snapshot", _fake_fetch_ok)

    target_dir = tmp_path / "my-app"
    answers = _answers(target_dir)

    written = generate(answers, PIN, CATALOG)

    assert (target_dir / "README.md").exists()
    readme = (target_dir / "README.md").read_text(encoding="utf-8")
    assert "my-app" in readme
    assert "MoofonLi/dev-ready" in readme
    assert (target_dir / "backend" / "main.py").exists()
    assert (target_dir / "AGENTS.md").is_file()
    assert (target_dir / "CLAUDE.md").exists()
    canonical_skill = target_dir / ".agents" / "skills" / "caveman" / "SKILL.md"
    claude_stub = target_dir / ".claude" / "skills" / "caveman" / "SKILL.md"
    assert canonical_skill.is_file()
    assert claude_stub.is_file()
    assert canonical_skill.read_bytes() != claude_stub.read_bytes()
    assert not any(path.is_symlink() for path in target_dir.rglob("*"))
    assert (target_dir / ".mcp.json").exists()
    assert Path("AGENTS.md") in written
    assert Path("CLAUDE.md") in written


# Upstream's own `.env` at the manifest-pinned commit, reduced to the lines this
# ticket reasons about. The Copier `_tasks` substitute the generated secrets, so
# the fake below does the same thing at the same moment.
_UPSTREAM_ENV = """\
# Domain
DOMAIN=localhost
# To test the local Traefik config
# DOMAIN=localhost.tiangolo.com

BACKEND_CORS_ORIGINS="http://localhost,https://localhost,http://localhost.tiangolo.com"
SECRET_KEY={secret_key}
FIRST_SUPERUSER=admin@example.com
FIRST_SUPERUSER_PASSWORD={first_superuser_password}
POSTGRES_PASSWORD={postgres_password}
POSTGRES_DB=app
"""


def _fetch_writing_env(env_body: str, seen: dict[str, str]):
    """Return a fetch fake that also writes the `.env` Copier's tasks would."""

    def _fetch(
        pin: UpstreamPin, dest: Path, template_data: dict[str, str] | None = None
    ) -> Path:
        _fake_fetch_ok(pin, dest, template_data)
        seen.update(template_data or {})
        (dest / ".env").write_text(env_body.format_map(seen), encoding="utf-8")
        return dest

    return _fetch


def _cors_value(env_text: str) -> str:
    for line in env_text.splitlines():
        if line.startswith("BACKEND_CORS_ORIGINS="):
            return line.partition("=")[2].strip('"')
    raise AssertionError("generated .env has no BACKEND_CORS_ORIGINS line")


def test_generated_cors_allowlist_drops_the_third_party_hostname(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: dict[str, str] = {}
    monkeypatch.setattr(
        generate_module, "fetch_snapshot", _fetch_writing_env(_UPSTREAM_ENV, seen)
    )
    target_dir = tmp_path / "my-app"

    generate(_answers(target_dir), PIN, CATALOG)

    env_text = (target_dir / ".env").read_text(encoding="utf-8")
    assert _cors_value(env_text) == "http://localhost,https://localhost"


def test_generated_cors_correction_leaves_the_secrets_and_the_rest_alone(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: dict[str, str] = {}
    monkeypatch.setattr(
        generate_module, "fetch_snapshot", _fetch_writing_env(_UPSTREAM_ENV, seen)
    )
    target_dir = tmp_path / "my-app"

    generate(_answers(target_dir), PIN, CATALOG)

    env_text = (target_dir / ".env").read_text(encoding="utf-8")
    assert f"SECRET_KEY={seen['secret_key']}" in env_text
    assert f"POSTGRES_PASSWORD={seen['postgres_password']}" in env_text
    assert f"FIRST_SUPERUSER_PASSWORD={seen['first_superuser_password']}" in env_text
    # Only the one key's value changes; every other line is byte-identical,
    # including the commented DOMAIN line naming the same hostname.
    original = _UPSTREAM_ENV.format_map(seen).splitlines()
    generated = env_text.splitlines()
    assert [
        line for line in original if not line.startswith("BACKEND_CORS_ORIGINS=")
    ] == [line for line in generated if not line.startswith("BACKEND_CORS_ORIGINS=")]
    assert "# DOMAIN=localhost.tiangolo.com" in generated


@pytest.mark.parametrize(
    "env_body",
    [
        pytest.param(
            _UPSTREAM_ENV.replace(
                'BACKEND_CORS_ORIGINS="http://localhost,https://localhost,'
                'http://localhost.tiangolo.com"\n',
                "",
            ),
            id="key-absent",
        ),
        pytest.param(
            _UPSTREAM_ENV.replace(",http://localhost.tiangolo.com", ""),
            id="hostname-already-absent",
        ),
        pytest.param("", id="empty-env"),
    ],
)
def test_generation_succeeds_when_there_is_nothing_to_correct(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, env_body: str
) -> None:
    """An upstream default that changed shape is the bump job's problem, not the user's."""
    seen: dict[str, str] = {}
    monkeypatch.setattr(
        generate_module, "fetch_snapshot", _fetch_writing_env(env_body, seen)
    )
    target_dir = tmp_path / "my-app"

    generate(_answers(target_dir), PIN, CATALOG)

    assert (target_dir / ".env").read_text(encoding="utf-8") == env_body.format_map(seen)


def test_an_env_file_without_the_key_passes_through_untouched(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`.env` is a required upstream path, so the reachable no-op is a file with no key."""
    monkeypatch.setattr(generate_module, "fetch_snapshot", _fake_fetch_ok)
    target_dir = tmp_path / "my-app"

    generate(_answers(target_dir), PIN, CATALOG)

    assert (target_dir / ".env").read_text(encoding="utf-8") == "stub"
    assert (target_dir / "AGENTS.md").is_file()


def test_the_cors_correction_happens_inside_staging(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A later failure must still leave no partial target behind."""
    seen: dict[str, str] = {}
    monkeypatch.setattr(
        generate_module, "fetch_snapshot", _fetch_writing_env(_UPSTREAM_ENV, seen)
    )

    def _failing_verify(*args: object, **kwargs: object) -> None:
        raise VerificationError("boom")

    monkeypatch.setattr(generate_module, "verify_project", _failing_verify)
    target_dir = tmp_path / "my-app"

    with pytest.raises(VerificationError):
        generate(_answers(target_dir), PIN, CATALOG)

    assert not target_dir.exists()


def test_generate_emits_typed_stage_events_in_pipeline_order(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(generate_module, "fetch_snapshot", _fake_fetch_ok)
    times = iter((10.0, 11.0, 20.0, 22.0, 30.0, 33.0, 40.0, 44.0))
    events: list[ProgressEvent] = []

    generate(
        _answers(tmp_path / "my-app"),
        PIN,
        CATALOG,
        progress=events.append,
        clock=lambda: next(times),
    )

    assert [(event.stage, event.status) for event in events] == [
        (GenerationStage.FETCH, ProgressStatus.STARTED),
        (GenerationStage.FETCH, ProgressStatus.COMPLETED),
        (GenerationStage.OVERLAY, ProgressStatus.STARTED),
        (GenerationStage.OVERLAY, ProgressStatus.COMPLETED),
        (GenerationStage.VERIFY, ProgressStatus.STARTED),
        (GenerationStage.VERIFY, ProgressStatus.COMPLETED),
        (GenerationStage.FINALIZE, ProgressStatus.STARTED),
        (GenerationStage.FINALIZE, ProgressStatus.COMPLETED),
    ]
    assert events[0].commit == PIN.commit
    assert [event.elapsed_seconds for event in events[1::2]] == [1.0, 2.0, 3.0, 4.0]


def test_generate_emits_one_failed_terminal_event_for_the_active_stage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _failing_fetch(
        pin: UpstreamPin, dest: Path, template_data: dict[str, str] | None = None
    ) -> Path:
        raise FetchError("simulated network failure")

    monkeypatch.setattr(generate_module, "fetch_snapshot", _failing_fetch)
    times = iter((5.0, 6.25))
    events: list[ProgressEvent] = []

    with pytest.raises(FetchError):
        generate(
            _answers(tmp_path / "my-app"),
            PIN,
            CATALOG,
            progress=events.append,
            clock=lambda: next(times),
        )

    assert events == [
        ProgressEvent(
            stage=GenerationStage.FETCH,
            status=ProgressStatus.STARTED,
            commit=PIN.commit,
        ),
        ProgressEvent(
            stage=GenerationStage.FETCH,
            status=ProgressStatus.FAILED,
            elapsed_seconds=1.25,
            commit=PIN.commit,
        ),
    ]


def test_progress_observer_failure_cannot_change_generation_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(generate_module, "fetch_snapshot", _fake_fetch_ok)

    def _broken_observer(event: ProgressEvent) -> None:
        raise RuntimeError(f"cannot render {event.stage.value}")

    target_dir = tmp_path / "my-app"
    written = generate(_answers(target_dir), PIN, CATALOG, progress=_broken_observer)

    assert target_dir.is_dir()
    assert Path("CLAUDE.md") in written


def test_progress_observer_failure_cannot_replace_generation_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _failing_fetch(
        pin: UpstreamPin, dest: Path, template_data: dict[str, str] | None = None
    ) -> Path:
        raise FetchError("underlying failure")

    monkeypatch.setattr(generate_module, "fetch_snapshot", _failing_fetch)

    with pytest.raises(FetchError, match="underlying failure"):
        generate(
            _answers(tmp_path / "my-app"),
            PIN,
            CATALOG,
            progress=lambda event: (_ for _ in ()).throw(RuntimeError("observer failed")),
        )


@pytest.mark.parametrize(
    ("stage", "error"),
    [
        (GenerationStage.FETCH, FetchError("fetch failed")),
        (GenerationStage.OVERLAY, OverlayError("overlay failed")),
        (GenerationStage.VERIFY, VerificationError("verify failed")),
        (GenerationStage.FINALIZE, TargetDirectoryError("finalize failed")),
    ],
)
def test_generate_reports_failure_for_each_stage_and_leaves_target_untouched(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    stage: GenerationStage,
    error: Exception,
) -> None:
    monkeypatch.setattr(generate_module, "fetch_snapshot", _fake_fetch_ok)

    if stage is GenerationStage.FETCH:
        monkeypatch.setattr(
            generate_module,
            "fetch_snapshot",
            lambda *args, **kwargs: (_ for _ in ()).throw(error),
        )
    elif stage is GenerationStage.OVERLAY:
        monkeypatch.setattr(
            generate_module,
            "apply_overlay",
            lambda *args, **kwargs: (_ for _ in ()).throw(error),
        )
    elif stage is GenerationStage.VERIFY:
        monkeypatch.setattr(
            generate_module,
            "verify_project",
            lambda *args, **kwargs: (_ for _ in ()).throw(error),
        )
    else:
        monkeypatch.setattr(
            generate_module,
            "_finalize_project",
            lambda *args, **kwargs: (_ for _ in ()).throw(error),
        )

    target_dir = tmp_path / "my-app"
    events: list[ProgressEvent | CleanupWarningEvent] = []

    with pytest.raises(type(error), match=str(error)):
        generate(_answers(target_dir), PIN, CATALOG, progress=events.append)

    stage_events = [
        event
        for event in events
        if isinstance(event, ProgressEvent) and event.stage is stage
    ]
    assert [event.status for event in stage_events] == [
        ProgressStatus.STARTED,
        ProgressStatus.FAILED,
    ]
    assert not target_dir.exists()


def test_temp_cleanup_failure_emits_a_non_stage_warning_event(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(generate_module, "fetch_snapshot", _fake_fetch_ok)
    original_rmtree = generate_module.shutil.rmtree
    events: list[ProgressEvent | CleanupWarningEvent] = []

    def _leave_generation_staging(path, *args, **kwargs) -> None:
        candidate = Path(path)
        if candidate.parent == tmp_path and candidate.name.startswith(".my-app.dev-ready-"):
            return
        original_rmtree(path, *args, **kwargs)

    monkeypatch.setattr(generate_module.shutil, "rmtree", _leave_generation_staging)

    generate(_answers(tmp_path / "my-app"), PIN, CATALOG, progress=events.append)

    warnings = [event for event in events if isinstance(event, CleanupWarningEvent)]
    assert len(warnings) == 1
    assert warnings[0].path.parent == tmp_path
    original_rmtree(warnings[0].path)


def test_generation_staging_is_adjacent_to_target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target_dir = tmp_path / "destination" / "my-app"
    target_dir.parent.mkdir()
    staging_roots: list[Path] = []

    def _capture_fetch(
        pin: UpstreamPin, dest: Path, template_data: dict[str, str] | None = None
    ) -> Path:
        staging_roots.append(dest.parent)
        return _fake_fetch_ok(pin, dest, template_data)

    monkeypatch.setattr(generate_module, "fetch_snapshot", _capture_fetch)

    generate(_answers(target_dir), PIN, CATALOG)

    assert staging_roots[0].parent == target_dir.parent


def test_finalize_uses_directory_rename_without_copy_fallback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(generate_module, "fetch_snapshot", _fake_fetch_ok)

    def _forbidden_move(*args, **kwargs) -> None:
        raise AssertionError("shutil.move permits a cross-filesystem copy fallback")

    monkeypatch.setattr(generate_module.shutil, "move", _forbidden_move)
    target_dir = tmp_path / "my-app"

    generate(_answers(target_dir), PIN, CATALOG)

    assert (target_dir / "backend" / "main.py").is_file()


def test_finalize_refuses_empty_target_created_during_generation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(generate_module, "fetch_snapshot", _fake_fetch_ok)
    target_dir = tmp_path / "my-app"

    def _create_racing_target(project_dir: Path, answers: Answers, catalog) -> None:
        target_dir.mkdir()

    monkeypatch.setattr(generate_module, "verify_project", _create_racing_target)

    with pytest.raises(TargetDirectoryError, match="appeared during generation"):
        generate(_answers(target_dir), PIN, CATALOG)

    assert target_dir.is_dir()
    assert list(target_dir.iterdir()) == []


@pytest.mark.parametrize("initially_empty", [False, True])
def test_finalize_failure_exposes_no_partial_target_and_restores_empty_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, initially_empty: bool
) -> None:
    monkeypatch.setattr(generate_module, "fetch_snapshot", _fake_fetch_ok)
    target_dir = tmp_path / "my-app"
    if initially_empty:
        target_dir.mkdir()
    original_rename = Path.rename
    events: list[ProgressEvent | CleanupWarningEvent] = []

    def _failing_project_rename(path: Path, target: Path) -> Path:
        if path.name == "project":
            raise OSError("simulated atomic rename failure")
        return original_rename(path, target)

    monkeypatch.setattr(Path, "rename", _failing_project_rename)

    with pytest.raises(TargetDirectoryError, match="simulated atomic rename failure"):
        generate(_answers(target_dir), PIN, CATALOG, progress=events.append)

    assert target_dir.exists() is initially_empty
    if initially_empty:
        assert list(target_dir.iterdir()) == []
    assert not list(tmp_path.glob(".my-app.dev-ready-*"))
    assert [
        event.status
        for event in events
        if isinstance(event, ProgressEvent) and event.stage is GenerationStage.FINALIZE
    ] == [ProgressStatus.STARTED, ProgressStatus.FAILED]


def test_preflight_rejects_non_empty_target_dir_before_fetch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[Path] = []

    def _spy_fetch(
        pin: UpstreamPin, dest: Path, template_data: dict[str, str] | None = None
    ) -> Path:
        calls.append(dest)
        return _fake_fetch_ok(pin, dest)

    monkeypatch.setattr(generate_module, "fetch_snapshot", _spy_fetch)

    target_dir = tmp_path / "my-app"
    target_dir.mkdir()
    (target_dir / "existing.txt").write_text("keep me", encoding="utf-8")

    with pytest.raises(TargetDirectoryError):
        generate(_answers(target_dir), PIN, CATALOG)

    assert calls == []
    assert (target_dir / "existing.txt").read_text(encoding="utf-8") == "keep me"


def test_preflight_rejects_target_dir_that_is_a_file(tmp_path: Path) -> None:
    target_dir = tmp_path / "my-app"
    target_dir.write_text("i am a file", encoding="utf-8")

    with pytest.raises(TargetDirectoryError):
        generate(_answers(target_dir), PIN, CATALOG)


def test_fetch_failure_leaves_target_untouched_and_no_leaked_temp_dirs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, _isolated_tempdir: Path
) -> None:
    def _failing_fetch(
        pin: UpstreamPin, dest: Path, template_data: dict[str, str] | None = None
    ) -> Path:
        raise FetchError("simulated network failure")

    monkeypatch.setattr(generate_module, "fetch_snapshot", _failing_fetch)

    target_dir = tmp_path / "my-app"
    with pytest.raises(FetchError):
        generate(_answers(target_dir), PIN, CATALOG)

    assert not target_dir.exists()
    assert list(_isolated_tempdir.iterdir()) == []


def test_overlay_failure_leaves_target_untouched_and_no_leaked_temp_dirs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, _isolated_tempdir: Path
) -> None:
    def _fetch_with_preexisting_claude_md(
        pin: UpstreamPin, dest: Path, template_data: dict[str, str] | None = None
    ) -> Path:
        dest.mkdir(parents=True)
        # upstream already ships a CLAUDE.md -> overlay must collide and fail
        (dest / "CLAUDE.md").write_text("not ours", encoding="utf-8")
        return dest

    monkeypatch.setattr(generate_module, "fetch_snapshot", _fetch_with_preexisting_claude_md)

    target_dir = tmp_path / "my-app"
    with pytest.raises(OverlayError):
        generate(_answers(target_dir), PIN, CATALOG)

    assert not target_dir.exists()
    assert list(_isolated_tempdir.iterdir()) == []


def test_success_leaves_no_leaked_temp_dirs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, _isolated_tempdir: Path
) -> None:
    monkeypatch.setattr(generate_module, "fetch_snapshot", _fake_fetch_ok)

    generate(_answers(tmp_path / "my-app"), PIN, CATALOG)

    assert list(_isolated_tempdir.iterdir()) == []


def test_verification_failure_leaves_target_untouched_and_no_leaked_temp_dirs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, _isolated_tempdir: Path
) -> None:
    def _fetch_missing_frontend(
        pin: UpstreamPin, dest: Path, template_data: dict[str, str] | None = None
    ) -> Path:
        # Upstream restructured and no longer ships a frontend/ directory ->
        # verify_project must catch it before anything reaches target_dir.
        dest.mkdir(parents=True)
        (dest / "backend").mkdir()
        return dest

    monkeypatch.setattr(generate_module, "fetch_snapshot", _fetch_missing_frontend)

    target_dir = tmp_path / "my-app"
    with pytest.raises(VerificationError):
        generate(_answers(target_dir), PIN, CATALOG)

    assert not target_dir.exists()
    assert list(_isolated_tempdir.iterdir()) == []


def test_verify_runs_after_overlay_and_before_move(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    call_order: list[str] = []
    target_dir = tmp_path / "my-app"
    answers = _answers(target_dir)

    def _spy_fetch(
        pin: UpstreamPin, dest: Path, template_data: dict[str, str] | None = None
    ) -> Path:
        call_order.append("fetch")
        return _fake_fetch_ok(pin, dest)

    def _spy_overlay(passed_answers: Answers, project_dir: Path, cat, pin, **kwargs) -> list[Path]:
        call_order.append("overlay")
        return []

    def _spy_verify(project_dir: Path, passed_answers: Answers, cat) -> None:
        call_order.append("verify")
        # verify must run before the staging dir is moved into target_dir
        assert not target_dir.exists()

    monkeypatch.setattr(generate_module, "fetch_snapshot", _spy_fetch)
    monkeypatch.setattr(generate_module, "apply_overlay", _spy_overlay)
    monkeypatch.setattr(generate_module, "verify_project", _spy_verify)

    generate(answers, PIN, CATALOG)

    assert call_order == ["fetch", "overlay", "verify"]
    assert target_dir.exists()


def test_fetch_receives_template_data_with_generated_secrets(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    received: dict[str, str] = {}

    def _spy_fetch(
        pin: UpstreamPin, dest: Path, template_data: dict[str, str] | None = None
    ) -> Path:
        received.update(template_data or {})
        return _fake_fetch_ok(pin, dest)

    monkeypatch.setattr(generate_module, "fetch_snapshot", _spy_fetch)

    generate(_answers(tmp_path / "my-app", project_name="My_Cool-App"), PIN, CATALOG)

    assert received["project_name"] == "My_Cool-App"
    assert received["stack_name"] == "my-cool-app"
    # Secrets must be generated per-project, never the upstream placeholder.
    for key in ("secret_key", "postgres_password", "first_superuser_password"):
        assert received[key] != "changethis"
        assert len(received[key]) >= 16
