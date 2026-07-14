"""The only module allowed to import questionary — see docs/architecture.md,
Dependency Rules. Imported lazily (function-local import in
`collect.py::_default_asker`) so the `--yes` path never triggers it.
"""

from collections.abc import Sequence

import questionary


class QuestionaryAsker:
    """Concrete `Asker` backed by questionary."""

    def text(self, message: str) -> str | None:
        return questionary.text(message).ask()

    def checkbox(self, message: str, choices: Sequence[str]) -> list[str] | None:
        return questionary.checkbox(
            message,
            choices=[questionary.Choice(choice, checked=True) for choice in choices],
        ).ask()

    def confirm(self, message: str, *, default: bool = True) -> bool | None:
        return questionary.confirm(message, default=default).ask()
