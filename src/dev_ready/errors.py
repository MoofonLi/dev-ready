"""Typed exceptions for dev-ready.

Raised anywhere, caught only at the cli layer, mapped to exit codes there
(see docs/cli-spec.md and docs/architecture.md, Coding Standards).
"""


class DevReadyError(Exception):
    """Base class for all expected dev-ready failures."""

    exit_code: int = 1


class InvalidArgumentsError(DevReadyError):
    """Invalid command-line arguments or user input."""

    exit_code = 2


class FetchError(DevReadyError):
    """Network or download failure while fetching the upstream snapshot."""

    exit_code = 3


class TargetDirectoryError(DevReadyError):
    """Target directory exists and is not empty, or cannot be created."""

    exit_code = 4


class ManifestError(DevReadyError):
    """manifest.json is missing, unreadable, or fails validation."""

    exit_code = 1


class OverlayError(DevReadyError):
    """Overlay asset missing, destination collision, or templating failure."""

    exit_code = 1


class AbortedError(DevReadyError):
    """User cancelled an interactive prompt (Ctrl-C or an unanswered prompt)."""

    exit_code = 1


class VerificationError(DevReadyError):
    """Generated project failed a post-generation structural check."""

    exit_code = 5
