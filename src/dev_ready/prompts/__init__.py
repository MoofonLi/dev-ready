"""prompts: collect Generation Intent via the terminal (ADR-004).

Must not perform any I/O other than the terminal. See docs/architecture.md.
Only `_questionary_asker.py` imports questionary, and only lazily — the
`--yes` path never constructs an asker.
"""

from dev_ready.prompts.asker import Asker
from dev_ready.prompts.collect import collect_answers, confirm_generation
from dev_ready.prompts.flags import agent_targets_from_flag, selection_from_flags

__all__ = [
    "Asker",
    "agent_targets_from_flag",
    "collect_answers",
    "confirm_generation",
    "selection_from_flags",
]
