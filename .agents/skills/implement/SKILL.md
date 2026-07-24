---
name: implement
description: "Implement a piece of work based on a spec or set of tickets."
disable-model-invocation: true
---

Implement the work described by the user in the spec or tickets.

Use /tdd where possible, at pre-agreed seams.

Run typechecking regularly, single test files regularly, and the full test suite once at the end.

Once done, use /code-review to review the work.

## dev-ready conventions (ADR-013)

This is the Execution-layer step of the internal four-phase process, run by the
Junior role on one ticket from `docs/handoff/<version>/phase-N/tickets/`:

- **One ticket at a time.** Stay inside the ticket's declared file footprint;
  if the work genuinely needs a path outside it, stop and report — don't
  expand silently.
- **TDD is mandatory, not "where possible"**: red (failing test) → green
  (minimal implementation) → refactor. `uv run pytest` and
  `uv run ruff check .` must pass before the ticket is done.
- **Never run state-changing git** (commit/branch/push). In the default
  sequential mode you work in the main working tree and leave the changes for
  the CEO to commit after reviews. In parallel mode (ticket marked
  `parallel-safe: yes`) you work in your assigned git worktree and deliver a
  diff/patch back.
- **Hard bug? STOP.** Do not keep grinding: log it in the phase
  `reports/problems.md` (symptom, what you tried, suspected area) and move to
  the next unblocked ticket. Hard bugs escalate to the Senior role — use
  /diagnosing-bugs only within a bounded attempt, not as a license to grind.
- Finish by updating the phase execution report in `reports/` (what was built,
  test evidence, per ticket).
