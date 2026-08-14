"""The only module allowed to import questionary — see docs/architecture.md,
Dependency Rules. Imported lazily (function-local import in
`collect.py::_default_asker`) so the `--yes` path never triggers it.
"""

from collections.abc import Sequence

import questionary

_QUESTION_MARK = "◆"
_POINTER = "›"
_CHECKBOX_INSTRUCTION = "(Space to select, Enter to continue; type to filter)"
_PROMPT_STYLE = questionary.Style(
    [
        ("qmark", "fg:#5fd7ff bold"),
        ("question", "bold"),
        ("answer", "fg:#5fd7ff bold"),
        ("pointer", "fg:#5fd7ff bold"),
        ("highlighted", "fg:#5fd7ff bold"),
        ("selected", "fg:#87d75f bold"),
        ("instruction", "fg:#808080 italic"),
        ("disabled", "fg:#808080 italic"),
    ]
)


class QuestionaryAsker:
    """Concrete `Asker` backed by questionary."""

    def text(self, message: str) -> str | None:
        return questionary.text(
            message,
            qmark=_QUESTION_MARK,
            style=_PROMPT_STYLE,
        ).ask()

    def select(
        self,
        message: str,
        choices: Sequence[str],
        *,
        disabled_choices: Sequence[str],
    ) -> str | None:
        disabled = frozenset(disabled_choices)
        return questionary.select(
            message,
            choices=[
                questionary.Choice(
                    choice,
                    disabled=True if choice in disabled else None,
                )
                for choice in choices
            ],
            qmark=_QUESTION_MARK,
            pointer=_POINTER,
            style=_PROMPT_STYLE,
            show_selected=True,
        ).ask()

    def checkbox(
        self,
        message: str,
        choices: Sequence[str],
        *,
        initially_selected: Sequence[str],
    ) -> list[str] | None:
        return questionary.checkbox(
            message,
            choices=[
                questionary.Choice(
                    choice,
                    checked=choice in initially_selected,
                )
                for choice in choices
            ],
            use_search_filter=True,
            # questionary rejects the two together: with a prefix filter active,
            # j and k are filter text, not movement. Arrow keys still move.
            use_jk_keys=False,
            qmark=_QUESTION_MARK,
            pointer=_POINTER,
            style=_PROMPT_STYLE,
            instruction=_CHECKBOX_INSTRUCTION,
        ).ask()

    def confirm(self, message: str, *, default: bool = True) -> bool | None:
        return questionary.confirm(
            message,
            default=default,
            qmark=_QUESTION_MARK,
            style=_PROMPT_STYLE,
        ).ask()
