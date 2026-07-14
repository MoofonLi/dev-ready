"""report: post-generation summary and next steps.

Read-only over the generated project — must not mutate it, and performs no
filesystem access at all: renders purely from its arguments. See
docs/architecture.md.
"""

from dev_ready.report.render import render_report

__all__ = ["render_report"]
