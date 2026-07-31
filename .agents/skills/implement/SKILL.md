---
name: implement
description: "Implement a piece of work based on a spec or set of tickets."
disable-model-invocation: true
---

Implement the work described by the user in the spec or tickets.

Use /tdd where possible, at pre-agreed seams.

Run typechecking regularly, single test files regularly, and the full test suite once at the end.

Once done, use /code-review to review the work.

## dev-ready conventions (ADR-021)

This is the last step of the internal Spec Loop — grill-with-docs → to-spec →
to-tickets → **implement** — run wearing the Engineer hat, then the Reviewer hat.
Work one ticket at a time from `docs/handoff/<version>/phase-N/tickets/`:

- **One ticket at a time**, and only a frontier ticket (all its blockers done).
  Stay inside the ticket's declared file footprint; if the work genuinely needs a
  path outside it, stop and say so — don't expand silently.
- **TDD is mandatory, not "where possible"**: red (failing test) → green
  (minimal implementation) → refactor.
- **Verification loop before a ticket is done**, in order:
  1. `uv sync --dev`
  2. `uv run pytest`
  3. `uv run ruff check .`
  4. `uv run pytest -m network` (only when the ticket touches fetch/pins)

  Any failure: fix and restart from step 1. Bounded by the STOP rule below, so
  it cannot thrash.
- **Never run state-changing git without explicit permission** for that specific
  action, in the moment. No `commit`, `push`, `branch`, `merge`, `reset` on your
  own initiative — read-only git (`status`, `diff`, `log`) is always fine. Leave
  the changes in the working tree and tell Moofon what is ready to commit,
  including the Conventional Commit message you'd use.
- **Hard bug? STOP.** Do not keep grinding. Report it in the session — symptom,
  what you tried, suspected area — and move to the next unblocked ticket. Use
  /diagnosing-bugs for a bounded attempt, not as a license to grind.
- **Review is part of this step, not a separate gate.** When the ticket's work is
  green, run /code-review against the last commit (or the point the ticket
  started from). There are no QA / Security / SRE gate documents any more
  (ADR-021) — if a change wants a dedicated security or SRE pass, ask for it by
  name.
- **No phase reports.** Do not write execution reports, `problems.md`, or
  anything under `reports/`. The committed spec and the ticket files are the
  record.
