"""prompts: collect user answers (interactive or via flags) into one Answers model.

Must not perform any I/O other than the terminal. See docs/architecture.md.
Interactive prompting (questionary) lands in a later phase; the Answers model
is defined here from the start so both paths share it (ADR-004).
"""

from dev_ready.prompts.answers import Answers

__all__ = ["Answers"]
