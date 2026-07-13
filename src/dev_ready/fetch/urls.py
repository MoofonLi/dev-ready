"""Build the codeload.github.com tarball URL for a pinned upstream commit."""

from dev_ready.manifest import UpstreamPin


def build_download_url(pin: UpstreamPin) -> str:
    """Build the tarball download URL from validated UpstreamPin fields only.

    UpstreamPin.repo and .commit are validated by dev_ready.manifest (strict
    owner/name pattern, 40-hex-char sha) before a pin ever reaches this
    function, so no raw/unvalidated input is interpolated into the URL.
    """
    return f"https://codeload.github.com/{pin.repo}/tar.gz/{pin.commit}"
