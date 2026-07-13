"""Unit tests for dev_ready.fetch (no network; filesystem confined to tmp_path)."""

import io
import tarfile
import tempfile
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path

import pytest

import dev_ready.fetch.download as download_module
from dev_ready.errors import FetchError, TargetDirectoryError
from dev_ready.fetch import fetch_snapshot
from dev_ready.manifest import UpstreamPin

PIN = UpstreamPin(
    repo="fastapi/full-stack-fastapi-template",
    ref="master",
    commit="4cd0d9e51aebd1af6f82d91ad0df4c9e41f4dea2",
    license="MIT",
)
PREFIX = "full-stack-fastapi-template-4cd0d9e51aebd1af6f82d91ad0df4c9e41f4dea2"


@pytest.fixture(autouse=True)
def _isolated_tempdir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Force tempfile.mkdtemp() (dir=None) to land inside tmp_path.

    fetch_snapshot uses tempfile.mkdtemp() directly, which otherwise writes
    outside tmp_path; this keeps the whole test file filesystem-confined and
    lets leak checks be deterministic.
    """
    temp_root = tmp_path / "_systmp"
    temp_root.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(temp_root))
    return temp_root


class _FakeResponse:
    def __init__(
        self, data: bytes, *, status: int = 200, headers: dict[str, str] | None = None
    ) -> None:
        self._buf = io.BytesIO(data)
        self.status = status
        self.headers = headers or {}

    def read(self, amt: int) -> bytes:
        return self._buf.read(amt)

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *exc: object) -> None:
        return None


def _opener_for(tar_path: Path, **response_kwargs: object) -> Callable[..., _FakeResponse]:
    data = tar_path.read_bytes()

    def _opener(request: object, timeout: object) -> _FakeResponse:
        return _FakeResponse(data, **response_kwargs)

    return _opener


def _add_file(tar: tarfile.TarFile, name: str, content: bytes = b"") -> None:
    info = tarfile.TarInfo(name=name)
    info.size = len(content)
    tar.addfile(info, io.BytesIO(content))


def _add_dir(tar: tarfile.TarFile, name: str) -> None:
    info = tarfile.TarInfo(name=name)
    info.type = tarfile.DIRTYPE
    tar.addfile(info)


def _add_symlink(tar: tarfile.TarFile, name: str, target: str) -> None:
    info = tarfile.TarInfo(name=name)
    info.type = tarfile.SYMTYPE
    info.linkname = target
    tar.addfile(info)


def _add_hardlink(tar: tarfile.TarFile, name: str, target: str) -> None:
    info = tarfile.TarInfo(name=name)
    info.type = tarfile.LNKTYPE
    info.linkname = target
    tar.addfile(info)


def _build_tarball(tar_path: Path, build: Callable[[tarfile.TarFile], None]) -> Path:
    with tarfile.open(tar_path, "w:gz") as tar:
        build(tar)
    return tar_path


def _happy_path_layout(tar: tarfile.TarFile) -> None:
    _add_dir(tar, PREFIX)
    _add_dir(tar, f"{PREFIX}/backend")
    _add_file(tar, f"{PREFIX}/README.md", b"hello")
    _add_file(tar, f"{PREFIX}/backend/main.py", b"print('hi')")


def test_fetch_snapshot_happy_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    tar_path = _build_tarball(tmp_path / "src.tar.gz", _happy_path_layout)
    monkeypatch.setattr(download_module, "_default_opener", _opener_for(tar_path))

    dest = tmp_path / "out"
    result = fetch_snapshot(PIN, dest)

    assert result == dest
    assert (dest / "README.md").read_text() == "hello"
    assert (dest / "backend" / "main.py").read_text() == "print('hi')"
    # the wrapping "{name}-{sha}/" directory itself must not appear in dest
    assert not (dest / PREFIX).exists()


def test_safe_internal_symlink_is_preserved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Symlinks resolving inside the root must survive extraction.

    The real upstream template ships one (.agents/skills/fastapi); rejecting
    all symlinks outright would break every fetch of the real repo.
    """

    def build(tar: tarfile.TarFile) -> None:
        _add_dir(tar, PREFIX)
        _add_file(tar, f"{PREFIX}/target.txt", b"real file")
        _add_symlink(tar, f"{PREFIX}/link.txt", "target.txt")

    tar_path = _build_tarball(tmp_path / "src.tar.gz", build)
    monkeypatch.setattr(download_module, "_default_opener", _opener_for(tar_path))

    dest = tmp_path / "out"
    fetch_snapshot(PIN, dest)

    assert (dest / "target.txt").read_text() == "real file"
    assert (dest / "link.txt").read_text() == "real file"


def test_fetch_snapshot_into_existing_empty_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tar_path = _build_tarball(tmp_path / "src.tar.gz", _happy_path_layout)
    monkeypatch.setattr(download_module, "_default_opener", _opener_for(tar_path))

    dest = tmp_path / "out"
    dest.mkdir()
    fetch_snapshot(PIN, dest)

    assert (dest / "README.md").read_text() == "hello"


@pytest.mark.parametrize(
    "build",
    [
        pytest.param(
            lambda tar: (_add_dir(tar, PREFIX), _add_file(tar, "/etc/passwd", b"pwned")),
            id="absolute-path",
        ),
        pytest.param(
            lambda tar: (
                _add_dir(tar, PREFIX),
                _add_file(tar, f"{PREFIX}/../../evil", b"pwned"),
            ),
            id="dot-dot-traversal",
        ),
        pytest.param(
            lambda tar: (
                _add_dir(tar, PREFIX),
                _add_symlink(tar, f"{PREFIX}/link", "../../etc/passwd"),
            ),
            id="symlink-escaping-root",
        ),
        pytest.param(
            lambda tar: (
                _add_dir(tar, PREFIX),
                _add_file(tar, f"{PREFIX}/original.txt", b"data"),
                _add_hardlink(tar, f"{PREFIX}/link.txt", f"{PREFIX}/original.txt"),
            ),
            id="hardlink",
        ),
    ],
)
def test_malicious_archive_members_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    build: Callable[[tarfile.TarFile], None],
) -> None:
    tar_path = _build_tarball(tmp_path / "src.tar.gz", build)
    monkeypatch.setattr(download_module, "_default_opener", _opener_for(tar_path))

    dest = tmp_path / "out"
    with pytest.raises(FetchError):
        fetch_snapshot(PIN, dest)
    assert not dest.exists()


@pytest.mark.parametrize(
    "build",
    [
        pytest.param(lambda tar: _add_file(tar, "README.md", b"hi"), id="no-top-level-dir"),
        pytest.param(
            lambda tar: (
                _add_dir(tar, "a"),
                _add_file(tar, "a/x", b"1"),
                _add_dir(tar, "b"),
                _add_file(tar, "b/y", b"2"),
            ),
            id="two-top-level-dirs",
        ),
    ],
)
def test_unexpected_archive_layout_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    build: Callable[[tarfile.TarFile], None],
) -> None:
    tar_path = _build_tarball(tmp_path / "src.tar.gz", build)
    monkeypatch.setattr(download_module, "_default_opener", _opener_for(tar_path))

    dest = tmp_path / "out"
    with pytest.raises(FetchError, match="unexpected archive layout"):
        fetch_snapshot(PIN, dest)
    assert not dest.exists()


def test_http_error_raises_fetch_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def _opener(request: urllib.request.Request, timeout: float) -> _FakeResponse:
        raise urllib.error.HTTPError(request.full_url, 404, "Not Found", {}, None)  # type: ignore[arg-type]

    monkeypatch.setattr(download_module, "_default_opener", _opener)

    dest = tmp_path / "out"
    with pytest.raises(FetchError):
        fetch_snapshot(PIN, dest)
    assert not dest.exists()


def test_timeout_raises_fetch_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def _opener(request: object, timeout: object) -> _FakeResponse:
        raise TimeoutError("timed out")

    monkeypatch.setattr(download_module, "_default_opener", _opener)

    dest = tmp_path / "out"
    with pytest.raises(FetchError):
        fetch_snapshot(PIN, dest)
    assert not dest.exists()


def test_oversized_download_raises_fetch_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(download_module, "MAX_DOWNLOAD_BYTES", 10)

    def _opener(request: object, timeout: object) -> _FakeResponse:
        return _FakeResponse(b"x" * 1000)  # no Content-Length header: streaming guard must catch it

    monkeypatch.setattr(download_module, "_default_opener", _opener)

    dest = tmp_path / "out"
    with pytest.raises(FetchError):
        fetch_snapshot(PIN, dest)
    assert not dest.exists()


def test_oversized_content_length_header_raises_fetch_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(download_module, "MAX_DOWNLOAD_BYTES", 10)

    def _opener(request: object, timeout: object) -> _FakeResponse:
        return _FakeResponse(b"x" * 1000, headers={"Content-Length": "1000"})

    monkeypatch.setattr(download_module, "_default_opener", _opener)

    dest = tmp_path / "out"
    with pytest.raises(FetchError):
        fetch_snapshot(PIN, dest)
    assert not dest.exists()


def test_non_empty_dest_raises_target_directory_error(tmp_path: Path) -> None:
    dest = tmp_path / "out"
    dest.mkdir()
    (dest / "existing.txt").write_text("keep me")

    with pytest.raises(TargetDirectoryError):
        fetch_snapshot(PIN, dest)
    assert (dest / "existing.txt").read_text() == "keep me"


def test_dest_that_is_a_file_raises_target_directory_error(tmp_path: Path) -> None:
    dest = tmp_path / "out"
    dest.write_text("i am a file")

    with pytest.raises(TargetDirectoryError):
        fetch_snapshot(PIN, dest)


def test_failure_leaves_no_leaked_temp_dirs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, _isolated_tempdir: Path
) -> None:
    def _opener(request: urllib.request.Request, timeout: float) -> _FakeResponse:
        raise urllib.error.HTTPError(request.full_url, 500, "Server Error", {}, None)  # type: ignore[arg-type]

    monkeypatch.setattr(download_module, "_default_opener", _opener)

    dest = tmp_path / "out"
    with pytest.raises(FetchError):
        fetch_snapshot(PIN, dest)

    assert not dest.exists()
    assert list(_isolated_tempdir.iterdir()) == []


def test_success_leaves_no_leaked_temp_dirs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, _isolated_tempdir: Path
) -> None:
    tar_path = _build_tarball(tmp_path / "src.tar.gz", _happy_path_layout)
    monkeypatch.setattr(download_module, "_default_opener", _opener_for(tar_path))

    fetch_snapshot(PIN, tmp_path / "out")

    assert list(_isolated_tempdir.iterdir()) == []
