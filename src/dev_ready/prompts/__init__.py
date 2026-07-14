"""prompts: collect user answers (interactive or via flags) into one Answers model.

Must not perform any I/O other than the terminal. See docs/architecture.md.
Only `_questionary_asker.py` imports questionary, and only lazily — the
`--yes` flag path in cli.py never calls into this package at all, so it
never triggers that import (ADR-004).
"""

from dev_ready.prompts.answers import Answers, PartialAnswers
from dev_ready.prompts.asker import Asker
from dev_ready.prompts.collect import collect_answers, confirm_generation

__all__ = [
    "Answers",
    "Asker",
    "PartialAnswers",
    "collect_answers",
    "confirm_generation",
]
