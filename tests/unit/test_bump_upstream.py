"""Unit tests for scripts/bump_upstream.py (no network; filesystem confined to tmp_path).

`scripts/` is CI-only tooling, not part of the dev_ready package, so it is
loaded here via importlib.util from an explicit file path rather than a
normal package import (see docs/architecture.md, Dependency Rules).
"""

import importlib.util
import json
from pathlib import Path

import pytest

_SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "bump_upstream.py"
_spec = importlib.util.spec_from_file_location("bump_upstream", _SCRIPT_PATH)
assert _spec is not None and _spec.loader is not None
bump_upstream = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bump_upstream)

_VALID_SHA = "a" * 40
_OTHER_VALID_SHA = "b" * 40


class _FakeResponse:
    """Stand-in for the context-managed response urlopen() returns."""

    def __init__(self, payload: dict) -> None:
        self._body = json.dumps(payload).encode("utf-8")

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *exc_info: object) -> bool:
        return False

    def read(self) -> bytes:
        return self._body


def _patch_urlopen(monkeypatch: pytest.MonkeyPatch, payload: dict) -> None:
    monkeypatch.setattr(
        bump_upstream.urllib.request,
        "urlopen",
        lambda request, timeout: _FakeResponse(payload),
    )


# --- resolve_latest_commit: sha validation, no real network I/O ---


def test_resolve_latest_commit_accepts_valid_sha(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_urlopen(monkeypatch, {"sha": _VALID_SHA})
    assert bump_upstream.resolve_latest_commit("owner/repo", "main") == _VALID_SHA


@pytest.mark.parametrize(
    "bad_sha",
    [
        "short",
        "",
        "g" * 40,  # non-hex character
        "A" * 40,  # uppercase not accepted (lowercase only, per manifest loader)
        "a" * 39,  # one char short
        "a" * 41,  # one char long
    ],
)
def test_resolve_latest_commit_rejects_invalid_sha(
    monkeypatch: pytest.MonkeyPatch, bad_sha: str
) -> None:
    _patch_urlopen(monkeypatch, {"sha": bad_sha})
    with pytest.raises(RuntimeError):
        bump_upstream.resolve_latest_commit("owner/repo", "main")


def test_resolve_latest_commit_rejects_missing_sha_field(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_urlopen(monkeypatch, {"unexpected": "shape"})
    with pytest.raises(RuntimeError):
        bump_upstream.resolve_latest_commit("owner/repo", "main")


# --- update_manifest: structure preservation, no-op detection ---


def _write_manifest(path: Path, *, commit: str, verified_at: str) -> None:
    path.write_text(
        json.dumps(
            {
                "manifest_version": 1,
                "upstream": {
                    "base_template": {
                        "repo": "fastapi/full-stack-fastapi-template",
                        "ref": "master",
                        "commit": commit,
                        "verified_at": verified_at,
                        "license": "MIT",
                    }
                },
                "overlay_version": "0.1.0",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def test_update_manifest_updates_commit_and_verified_at(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    _write_manifest(manifest_path, commit=_VALID_SHA, verified_at="2026-01-01")

    changed = bump_upstream.update_manifest(manifest_path, _OTHER_VALID_SHA, "2026-07-14")

    assert changed is True
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    pin = data["upstream"]["base_template"]
    assert pin["commit"] == _OTHER_VALID_SHA
    assert pin["verified_at"] == "2026-07-14"


def test_update_manifest_preserves_all_other_keys_and_formatting(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    _write_manifest(manifest_path, commit=_VALID_SHA, verified_at="2026-01-01")

    bump_upstream.update_manifest(manifest_path, _OTHER_VALID_SHA, "2026-07-14")

    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    pin = data["upstream"]["base_template"]
    assert pin["repo"] == "fastapi/full-stack-fastapi-template"
    assert pin["ref"] == "master"
    assert pin["license"] == "MIT"
    assert data["manifest_version"] == 1
    assert data["overlay_version"] == "0.1.0"

    text = manifest_path.read_text(encoding="utf-8")
    assert text.endswith("\n") and not text.endswith("\n\n")
    assert "  " in text  # indent=2 preserved


def test_update_manifest_returns_false_when_pin_already_current(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    _write_manifest(manifest_path, commit=_VALID_SHA, verified_at="2026-01-01")

    changed = bump_upstream.update_manifest(manifest_path, _VALID_SHA, "2026-07-14")

    assert changed is False
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    # No-op: verified_at must NOT have been touched either.
    assert data["upstream"]["base_template"]["verified_at"] == "2026-01-01"


# --- main(): end-to-end against a monkeypatched manifest path, no network ---


def test_main_reports_unchanged_when_pin_already_current(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    manifest_path = tmp_path / "manifest.json"
    _write_manifest(manifest_path, commit=_VALID_SHA, verified_at="2026-01-01")
    monkeypatch.setattr(bump_upstream, "_MANIFEST_PATH", manifest_path)
    monkeypatch.setattr(bump_upstream, "resolve_latest_commit", lambda repo, ref: _VALID_SHA)

    assert bump_upstream.main() == 0
    assert capsys.readouterr().out.strip() == "unchanged"


def test_main_reports_updated_short_shas_when_pin_changes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    manifest_path = tmp_path / "manifest.json"
    _write_manifest(manifest_path, commit=_VALID_SHA, verified_at="2026-01-01")
    monkeypatch.setattr(bump_upstream, "_MANIFEST_PATH", manifest_path)
    monkeypatch.setattr(
        bump_upstream, "resolve_latest_commit", lambda repo, ref: _OTHER_VALID_SHA
    )

    assert bump_upstream.main() == 0
    out = capsys.readouterr().out.strip()
    assert out == f"updated {_VALID_SHA[:12]} -> {_OTHER_VALID_SHA[:12]}"
