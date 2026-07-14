"""Asker: the injectable seam between prompt orchestration and the terminal.

Defining this as a plain Protocol (no questionary import here) lets unit
tests supply a fake without ever touching a real TTY. Only
`prompts/_questionary_asker.py` may import questionary — see
docs/architecture.md, Dependency Rules.
"""

from collections.abc import Sequence
from typing import Protocol


class Asker(Protocol):
    """Terminal-prompt surface `collect_answers`/`confirm_generation` need.

    Each method returns `None` when the user cancels (Ctrl-C / Esc) instead
    of raising, matching questionary's own `.ask()` convention.
    """

    def text(self, message: str) -> str | None: ...

    def checkbox(self, message: str, choices: Sequence[str]) -> list[str] | None: ...

    def confirm(self, message: str, *, default: bool = True) -> bool | None: ...
