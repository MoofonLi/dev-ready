# Multi-Agent Handoff Protocol

This project was generated with the **agents** component. It sets up a fixed-role,
document-driven workflow for AI-assisted development. Agents coordinate ONLY through
the on-disk handoff documents in this directory — never through assumed chat context.

## Roles

| Role | Does | Never does |
|---|---|---|
| CEO (you) | Sets goals, approves plans, commits/merges | — |
| Tech Lead | Decisions, plans, writes handoff docs | Write or edit code |
| Senior Engineer | Task breakdown for the junior, code + architecture review, fixes escalated hard bugs | Write code the junior can handle |
| Junior Engineer | Implements tasks in the working tree, writes an execution report per phase | Run state-changing git; keep grinding on a hard bug |
| QA / Security / SRE | Reviews quality, security, and operability per phase | — |

Only the CEO runs state-changing git (commit / branch / push). Every other role edits
the working tree only.

## Per-phase files

Work is organized into phases. Each phase lives in `phase-N/` and uses these files, in order:

| File | Author | Purpose |
|---|---|---|
| `01-opus-plan.md` | Senior Engineer | Ordered task breakdown with implementation details |
| `02-gemini-implementation.md` | Junior Engineer | Implementation brief the junior executes |
| `03-opus-review.md` | Senior Engineer | Logic + architecture review of the implementation |
| `04-bob-qa.md` | QA | Quality review |
| `05-bob-security.md` | Security | Security review |
| `06-bob-sre.md` | SRE | Operability / release review |

## `reports/` convention

Each phase's Junior writes to `phase-N/reports/`:

- `execution-report.md` — ALWAYS written: per-task status, test evidence, files changed.
- `problems.md` — written ONLY when a hard bug was hit.

## The Junior's stop-and-escalate rule

A hard bug is: more than 2 failed fix attempts, a failure that cannot be localized to a
cause, or anything that seems to require crossing a module boundary or changing a
documented decision. On a hard bug the Junior STOPS, logs it in `phase-N/reports/problems.md`
(where / what happened / suspected cause / what was tried), and moves to the next
independent task — it does not keep grinding. The presence of `problems.md` blocks the
phase on the Senior Engineer.
