"""Stream a tarball over HTTPS to a file, enforcing timeout and size limits."""

import http.client
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path

from dev_ready.errors import FetchError

CONNECT_TIMEOUT = 30.0
MAX_DOWNLOAD_BYTES = 500 * 1024 * 1024

_CHUNK_SIZE = 64 * 1024

Opener = Callable[[urllib.request.Request, float], http.client.HTTPResponse]


def _default_opener(request: urllib.request.Request, timeout: float) -> http.client.HTTPResponse:
    return urllib.request.urlopen(request, timeout=timeout)  # noqa: S310 (url is https-only, built from validated pin fields)


def download(
    url: str,
    dest_path: Path,
    *,
    timeout: float | None = None,
    max_bytes: int | None = None,
    opener: Opener | None = None,
) -> None:
    """Stream `url` into `dest_path`, aborting with FetchError past `max_bytes`.

    `timeout`, `max_bytes`, and `opener` default to the module-level
    constants/function looked up by name (not bound as default arguments) so
    tests can monkeypatch CONNECT_TIMEOUT / MAX_DOWNLOAD_BYTES / _default_opener.
    """
    if not url.startswith("https://"):
        raise FetchError(f"refusing to download over a non-HTTPS url: {url}")

    effective_timeout = CONNECT_TIMEOUT if timeout is None else timeout
    effective_max_bytes = MAX_DOWNLOAD_BYTES if max_bytes is None else max_bytes
    active_opener = _default_opener if opener is None else opener

    request = urllib.request.Request(url, headers={"User-Agent": "dev-ready"})
    try:
        response = active_opener(request, effective_timeout)
    except urllib.error.HTTPError as error:
        raise FetchError(f"upstream download failed with HTTP {error.code}: {url}") from error
    except (urllib.error.URLError, OSError) as error:
        raise FetchError(f"upstream download failed: {error}") from error

    with response:
        status = getattr(response, "status", None)
        if status is not None and status >= 400:
            raise FetchError(f"upstream download failed with HTTP {status}: {url}")

        declared_length = _declared_content_length(response)
        if declared_length is not None and declared_length > effective_max_bytes:
            raise FetchError(
                f"upstream archive declares {declared_length} bytes,"
                f" exceeding the {effective_max_bytes}-byte limit: {url}"
            )

        try:
            written = 0
            with dest_path.open("wb") as out:
                while True:
                    chunk = response.read(_CHUNK_SIZE)
                    if not chunk:
                        break
                    written += len(chunk)
                    if written > effective_max_bytes:
                        raise FetchError(
                            f"upstream archive exceeded the {effective_max_bytes}-byte"
                            f" download limit: {url}"
                        )
                    out.write(chunk)
        except (urllib.error.URLError, OSError) as error:
            raise FetchError(f"upstream download failed: {error}") from error


def _declared_content_length(response: http.client.HTTPResponse) -> int | None:
    headers = getattr(response, "headers", None)
    if headers is None:
        return None
    value = headers.get("Content-Length")
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None
