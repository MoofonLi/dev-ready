# Handoff templates

Placeholders: `{{VERSION}}` (e.g. v0.2), `{{N}}` (phase number), `{{TITLE}}`
(short phase title, e.g. "prune list + leak guard"), `{{FRS}}` (e.g. "FR-7,
FR-9"), `{{DATE}}` (today), plus content slots described inline. `{{DIR}}` =
`docs/handoff/{{VERSION}}/phase-{{N}}`. Release-only placeholders (`07`):
`{{RELEASE_VERSION}}` (X.Y.Z, no leading v) and `{{PHASES_COVERED}}` (the
phase(s) the release completes, e.g. "Phase 1–2"). Keep protocol wording
intact; fill slots.

---

## 01-plan.md

```markdown
# Phase {{N}} Handoff — 01: Senior Engineer Plan

- From: Tech Lead (ADR-007)
- To: Senior Engineer
- Phase: {{VERSION}} Phase {{N}} — {{TITLE}} ({{FRS}})
- Date: {{DATE}}
- Status: AWAITING TASK BREAKDOWN (write it into 02-implementation.md, then update this line)

## Your role

You are the Senior Engineer. In this handoff you do NOT write code. You read the phase scope below and write an ordered task breakdown WITH implementation details directly into `02-implementation.md`, in the section "Task Breakdown & Implementation Details (Senior writes here)" — and only in that section; everything above its divider is the Tech Lead's protocol and read-only. `02` is the single file the Junior (running in Antigravity) receives, so it must be self-contained: assume the Junior has no chat context.

## Precondition

{{PRECONDITION: what must be true before this phase starts (previous phase closed, release tagged, etc.) and what to do if it is not — usually "stop and flag it to the Tech Lead".}}

## Read before planning

1. `AGENTS.md` — hard rules and role table (binding)
2. `docs/handoff/{{VERSION}}/{{VERSION}}-plan.md` — Phase {{N}} section + Standing constraints
3. `docs/requirements.md` — {{FRS}}
4. `docs/architecture.md` + `docs/decisions/` — relevant ADRs, Module Boundary and Dependency Rules
5. `docs/cli-spec.md` — exit codes

## Phase {{N}} scope (fixed — do not expand or shrink)

{{SCOPE: numbered list from the plan, each item naming concrete files (src/dev_ready/...) and exact required behavior, plus the tests item. State cross-phase couplings as explicit DO NOTs.}}

## Known trap — call it out explicitly in the Junior's tasks

{{TRAP: anything the plan flags as needing empirical verification or easy to get wrong. If none: "None flagged by the plan — still list per-task acceptance checks."}}

## Constraints every task must respect

- Hard rules in AGENTS.md: pins only in `manifest.json`; network only in `fetch/`; all-or-nothing generation; unit tests use no network and no filesystem outside `tmp_path`; Conventional Commits (used by the CEO at commit time).
- Nobody but the CEO touches git state: the Junior (and you, when fixing) edit the working tree only; the CEO commits after 03–06 pass, using the Conventional Commit messages from the task headings.
- No new runtime dependencies.
- Module boundaries per `docs/architecture.md`. A task that seems to need crossing one is escalated to the Tech Lead, not crossed.

## Acceptance criteria for the phase (verbatim from the plan)

{{ACCEPTANCE: bullet list copied from the plan's acceptance line.}}

## Breakdown requirements

- 4–6 ordered tasks, each with a Conventional Commit message in its heading (used later by the CEO — agents never commit).
- Per task: files touched, what "done" means (testable), required tests.
- Include any real-run verification as its own step with instructions (ONE generation into a scratch dir OUTSIDE the repo, deleted afterwards).
- Keep it executable by an agent with no chat history — the Junior gets `02` and nothing else.
- Remind the Junior of the problems.md flow (already templated in `02`): hard bugs go to `reports/problems.md`; the execution report is written no matter what.
```

---

## 02-implementation.md

```markdown
# Phase {{N}} Handoff — 02: Junior Engineer Implementation Brief

- From: Tech Lead (ADR-007)
- To: Junior Engineer
- Phase: {{VERSION}} Phase {{N}} — {{TITLE}} ({{FRS}})
- Date: {{DATE}}

## Your role

You are the Junior Engineer. You write the code for this phase. This file is self-contained: the working rules are here at the top (Tech Lead), and your task list with implementation details is in the "Task Breakdown & Implementation Details" section below (Senior Engineer). If that section is empty, stop — the phase has not been planned yet.

## Read before writing code

1. `AGENTS.md` — hard rules (binding)
2. This file, top to bottom
3. `docs/architecture.md` — Module Boundary, Dependency Rules, Coding Standards
4. `docs/cli-spec.md` — exit codes
5. `tests/README.md` — test tiers

## Execution protocol

- NO GIT (binding): you edit files in the working tree directly and NEVER run any git command that changes state — no commit, no branch, no checkout, no push, no reset, no stash. Read-only git (`git status`, `git diff`, `git log`) is fine. The CEO commits after the Senior's review (03) and the reviewer's passes (04–06) pass, using the Conventional Commit messages attached to each task as guidance.
- Work the tasks strictly in order.
- After every task: `uv run pytest` and `uv run ruff check .` must both pass before you move to the next task.
- Unit tests: no network, no filesystem outside `tmp_path`.
- Fully type-annotate public functions. No business logic in `__init__.py`.

## STOP rules (binding — token discipline per ADR-007)

On a hard bug or a task you cannot implement:

1. STOP generating code for that task immediately. Do not thrash — a hard bug is: more than 2 failed fix attempts, a failure you cannot localize to a cause, or anything that seems to require crossing a module boundary or changing a documented decision.
2. Add an entry to `reports/problems.md` (create it from the template below if it does not exist): where (file/test), what happened (exact error output), suspected cause, what you already tried.
3. Move on to the next task if it does not depend on the blocked one; otherwise stop the phase.

## Never do

- Run any state-changing git command (see NO GIT rule above).
- Change the upstream pin (`repo`/`ref`/`commit`) in `manifest.json`.
- Add dependencies (runtime or dev).
- Make network calls outside `src/dev_ready/fetch/`.
- Weaken or delete existing tests to make them pass.
- Edit anything in this file outside your own reports. The breakdown section below is the Senior's; the protocol above is the Tech Lead's.

## Final verification (after the last task, before writing the report)

The per-task `pytest` + `ruff` runs above only cover the state after each
task; a later task can break an earlier one, and the network tier is never
exercised along the way. So when all tasks are DONE (or the remaining ones
are BLOCKED in problems.md), run the full suite once, in order, from the
repo root:

1. `uv sync --dev`
2. `uv run pytest`
3. `uv run ruff check .`
4. `uv run pytest -m network`

If any step fails: fix the cause, then rerun the sequence from step 1 — a
fix can invalidate a step that already passed. Failures here are subject to
the same STOP rules as any other bug: a failure that survives 2 real fix
attempts, or that you cannot localize, is a hard bug — log it in
`reports/problems.md` and stop fixing it rather than thrashing. The test
evidence in your report must come from the final run of this sequence.

## Output when done (ALWAYS, hard bugs or not)

Write `{{DIR}}/reports/execution-report.md`:

- Per-task status table: task id, files changed, status (DONE / PROBLEM / BLOCKED).
- Test evidence: output summary of the final verification sequence (all four commands, from its last full run).
- {{REPORT_EXTRAS: phase-specific evidence the report must contain, e.g. real-run checklists.}}
- Files changed, and any deviation from the breakdown with one-line justification.

If you hit any hard bugs, ALSO write `{{DIR}}/reports/problems.md` using exactly this template (one `##` entry per bug):

    # Problems — {{VERSION}} Phase {{N}}
    STATUS: OPEN

    Senior Engineer: reproduce and fix each bug below. Code fixes go
    directly into the working tree (no git). When ALL bugs are fixed: update
    reports/execution-report.md with what changed, then DELETE this file.
    If a bug cannot be fixed after a real attempt: set STATUS: ESCALATED-TO-CEO
    at the top and stop — the CEO and Tech Lead take over from there.

    ## <task-id> — <one-line summary>
    - Where: <file / test>
    - What happened: <exact error output>
    - Suspected cause: <your hypothesis>
    - What was tried: <attempts so far>

Save both files. The presence of `reports/problems.md` means the phase is blocked on the Senior; its absence plus your execution report means the phase moves to review (`03-review.md`). Nothing is committed at this stage — code stays in the working tree until the CEO commits after all reviews pass.

---

## Task Breakdown & Implementation Details (Senior writes here)

This section is written and maintained by the Senior Engineer only. Everything above the divider is the Tech Lead's protocol and is read-only for all agents. Junior: if anything here conflicts with the protocol above, the protocol wins — record it in `reports/problems.md` instead of guessing.

_Empty — the Senior Engineer fills this section per `01-plan.md`._
```

---

## 03-review.md

```markdown
# Phase {{N}} Handoff — 03: Senior Engineer Review & Close

- From: Tech Lead (ADR-007)
- To: Senior Engineer
- Phase: {{VERSION}} Phase {{N}} — {{TITLE}} ({{FRS}})
- Date: {{DATE}}

## Entry check (do this first)

1. `{{DIR}}/reports/execution-report.md` must exist. If not, stop — the Junior has not finished; nothing to review.
2. `{{DIR}}/reports/problems.md` must NOT exist. If it exists, the phase is in FIX mode, not review mode: work from `problems.md` (its header tells you the fix protocol) together with the breakdown in `02-implementation.md`. Come back to this file only after `problems.md` is resolved and deleted.

## Your role

Review the Junior's Phase {{N}} work and close the phase. All Phase {{N}} work lives as UNCOMMITTED working-tree changes on top of main — nobody commits until the CEO does, after all reviews pass. You are the only agent who fixes bugs directly (also straight into the working tree). Start from files on disk — the Junior's chat context does not exist for you.

## Read first

1. `{{DIR}}/reports/execution-report.md`
2. The breakdown you wrote in `02-implementation.md`
3. The actual diff: `git status` and `git diff` (read-only git is allowed; state-changing git is not)

## Step 1 — code review (logic and architecture)

{{REVIEW_FOCUS: bullets derived from the phase scope — one per scope item stating what correct looks like, plus cross-phase DO NOT checks, plus:}}
- Tests exist at the right tier and unit tests touch no network and nothing outside `tmp_path`.
- Nothing was committed: `git log --oneline -3` shows no new commits on main; all changes are working-tree only, confined to {{ALLOWED_PATHS}}.

## Step 2 — gates

Run the full verification suite yourself on the working tree, in order,
from the repo root — do not trust the Junior's report as evidence that it
passes now:

1. `uv sync --dev`
2. `uv run pytest`
3. `uv run ruff check .`
4. `uv run pytest -m network`

If any step fails, fix and rerun the whole sequence from step 1 until all
four pass: a trivial cause (typo-level, no design judgment) you fix directly
in the working tree; anything beyond trivial goes to `reports/problems.md`
and the phase enters FIX mode (Step 3) — this review restarts from the
entry check afterwards.

All must pass before you close:

- The four-command sequence above, green end to end on its final run.
- Acceptance: {{ACCEPTANCE_INLINE}}. (CI generate-and-verify runs after the CEO commits and pushes — local real-run checks are its pre-commit stand-in.)

## Step 3 — findings

- Trivial defects (typo-level, no design judgment): fix directly in the working tree (no commits), note it for the verdict.
- Anything beyond trivial: write `{{DIR}}/reports/problems.md` (same template the Junior uses — its header carries the fix protocol), one `##` entry per issue, and STOP. The phase re-enters FIX mode; this review restarts from the entry check afterwards.
- If, during FIX mode, a problem survives a real fix attempt: set `STATUS: ESCALATED-TO-CEO` at the top of `problems.md` and stop — the CEO and Tech Lead take over.

## Step 4 — update the execution report (ALWAYS, findings or not)

Append a "## Senior Review Addendum" section to `{{DIR}}/reports/execution-report.md` and save. Do this on every review pass — even a clean one — because the execution report is the single on-disk record of the phase: the reviewer (04–06) and the CEO read it instead of your chat context, so anything that lives only in this file is invisible to them. Include:

- What actually changed: summarize `git status` / `git diff` (read-only) against the previous phase's state — files touched and what changed, compared against what the breakdown in `02` promised. Note any drift.
- Fixes made during review or FIX mode: what was broken, what you changed. If none: state "no fixes needed".
- Gate evidence: the summary lines from your own final run of the four-command verification sequence (Step 2) — the reviewer and the CEO rely on this, not on rerunning it themselves.
- Anything the Junior's report missed, misstated, or that you verified independently.

## Step 5 — verdict (only when Step 2 gates pass and no problems.md exists)

Append "## Review Verdict" to this file and save (docs/handoff/ is gitignored — do not commit it):

- PASS/FAIL per acceptance criterion.
- Problems fixed along the way: what was broken, what you changed.
- Review findings you fixed vs. accepted as-is.
- Statement that the phase is ready for review (04–06) — or what blocks it.
- Suggested Conventional Commit message(s) for the CEO (one per task, or a sensible squash), taken from the task headings in `02`.

You do not commit, merge, or release under THIS document. For a non-release phase, the CEO commits and pushes after the reviewer passes; CI generate-and-verify on that push is the final backstop. For a release phase, git authority arrives only with `07-release.md`, which the CEO hands over after the reviewer's three APPROVE reports are on disk.
```

---

## 04-qa-review.md / 05-security-review.md / 06-sre-review.md

Common shape — instantiate three times with role = QA / Security / SRE:

```markdown
# Phase {{N}} Handoff — 0X: {{ROLE}} Review

- From: Tech Lead (ADR-007)
- To: Reviewer ({{ROLE}})
- Phase: {{VERSION}} Phase {{N}} — {{TITLE}} ({{FRS}})
- Precondition: `03-review.md` contains a Review Verdict marked ready for review

Your role definition is `.agents/skills/review/references/{{qa|security|sre}}.md` — read and follow it. The change under review is UNCOMMITTED working-tree changes on top of main: inspect with `git status` / `git diff` (read-only git only). Context docs: `docs/handoff/{{VERSION}}/{{VERSION}}-plan.md` (Phase {{N}}), `docs/requirements.md` {{FRS}}, {{ROLE_CONTEXT_DOCS}}.

## Verify specifically

{{ROLE_SPECIFIC_NUMBERED_LIST}}

## Output

Write `{{DIR}}/reports/{{qa|security|sre}}-review.md` (NOT any separate reviews directory — all phase records live together in `{{DIR}}/reports/`; if your role file says otherwise, this path wins): Verdict (`APPROVE` / `REQUEST CHANGES`), blocking issues (file:line, what, why, suggested fix), non-blocking suggestions in a separate section. Do not modify code. Report only.
```

Role-specific list guidance:

- QA: each new behavior has tests at the right tier (unit = no network, tmp_path only); every invalid-input shape asserted with the typed error, not bare exceptions; error paths assert exit codes per `docs/cli-spec.md`; regressions (existing tests untouched and green, `uv run pytest -q` + `uv run ruff check .` pass); evidence in the execution report for anything only verifiable by a real run; scope confined to the phase's allowed paths.
- Security: trace every new untrusted input path to its validation; leak/bypass surface of any new guard (does it run before finalize? can callers skip it?); pins unchanged — flag ANY pin change as blocking; no new dependencies; no workflow permission expansion; secrets absent from new content.
- SRE: all-or-nothing generation preserved end-to-end for each new failure mode; failure messages state what failed + likely cause + user action, correct exit codes, no silent failures; no new manual maintenance outside the weekly bump loop; false-positive risk of new checks.

---

## 07-release.md — RELEASE PHASES ONLY

Generate this file only when the phase ships a release (SKILL.md Step 2).
It is the single document that grants git authority; every other handoff
doc's NO GIT rule stays binding.

```markdown
# Phase {{N}} Handoff — 07: Release Engineer — Ship v{{RELEASE_VERSION}}

- From: Tech Lead (ADR-007)
- To: Senior Engineer acting as Release Engineer
- Release: v{{RELEASE_VERSION}}, completing {{PHASES_COVERED}}
- Date: {{DATE}}

## Entry check (do this first — touch NOTHING until all four hold)

1. `{{DIR}}/03-review.md` ends with a Review Verdict stating the phase is ready for review.
2. `{{DIR}}/reports/qa-review.md`, `security-review.md`, and `sre-review.md` all exist with Verdict `APPROVE`.
3. `{{DIR}}/reports/problems.md` does NOT exist.
4. `git log --oneline -5` shows no commits you cannot account for — the phase's work must still be uncommitted working-tree changes on top of main.

If any check fails, STOP and report to the CEO. Do not "release anyway": these checks are the reason it is safe to hand you git at all.

## Your role and your git authority

You are the Release Engineer. You run the ENTIRE release yourself — version bump, verification, phase overview report, staged commits, push, CI wait, tag, and post-release checks. This document is the ONLY exemption from the repo's NO-GIT-for-agents rule, and the exemption is scoped: exactly the git operations listed in the steps below, on this repo, for this release. Still forbidden: force-push, rebase, reset, amend, deleting commits, branch operations, and touching any tag other than `v{{RELEASE_VERSION}}` (except the re-tag flow in Troubleshooting). If a situation seems to need a forbidden operation, STOP and escalate to the CEO.

Why the discipline matters: the steps up to and including CI are reversible; the tag push triggers publication to PyPI, which can NEVER be unpublished. Treat the tag as the point of no return and front-load all verification before it.

## Repo facts this release depends on

- The version lives in BOTH `src/dev_ready/__init__.py` (`__version__`) and `pyproject.toml` (`version`). `release.yml` refuses to publish if the pushed tag does not match `pyproject.toml`; the CLI prints `__version__`. A mismatch ships a CLI that reports the wrong version.
- `docs/handoff/` is gitignored — never stage or commit anything under it.
- Conventional Commits are mandatory; the commit messages come from the task headings in `02-implementation.md`.
- Run every command from the dev-ready repo root.

## Step 1 — bump the version in two files

1. `src/dev_ready/__init__.py`: `__version__ = "{{RELEASE_VERSION}}"`
2. `pyproject.toml`: `version = "{{RELEASE_VERSION}}"`

Sanity: `{{RELEASE_VERSION}}` must be greater than the version currently in `pyproject.toml`. If it is not, the handoff is stale — STOP and ask the CEO.

## Step 2 — local verification (all four must pass)

1. `uv sync --dev`   (also refreshes `uv.lock` with the new version — include it in the chore commit later)
2. `uv run pytest`
3. `uv run ruff check .`
4. `uv run pytest -m network`

If any step fails: a trivial cause (typo-level, no design judgment) you fix in the working tree and rerun from step 1. Anything beyond trivial means something changed under the reviewer's approvals — STOP the release, write `{{DIR}}/reports/problems.md` (standard template), and escalate to the CEO, who decides whether the phase re-enters the ADR-007 fix loop. Never "release now, fix later": the pipeline ends at PyPI, which cannot be unpublished.

## Step 3 — phase overview report

Only after Step 2 is green. For each phase in {{PHASES_COVERED}}, read everything under `docs/handoff/{{VERSION}}/phase-<N>/` (the handoff docs plus `reports/`) and write `docs/handoff/{{VERSION}}/reports/phase-<N>-overview.md` with:

- **Scope**: which FRs/ADRs the phase implemented (cite requirements.md / architecture.md numbers)
- **What was built**: modules touched, behavior changes, from the execution report
- **Problems encountered**: from problems.md history and escalations — what happened, how it was resolved, by whom (junior / senior)
- **Review outcomes**: verdicts from the Senior review and the reviewer's QA / Security / SRE reports
- **Test evidence**: the Step 2 results you just produced

These files stay in the gitignored handoff tree — they are the CEO's record, not repo docs. Do not commit them.

## Step 4 — staged commits

Group the working-tree changes into separate Conventional Commits, in this order (each commit must leave the tree in a working state):

1. `feat:` / `fix:` — implementation changes (one commit per coherent change, not per file)
2. `docs:` — documentation-only changes
3. `chore: bump version to {{RELEASE_VERSION}}` — the two version files + `uv.lock`, ALWAYS the last commit before tagging

Never `git add .` blindly: run `git status` first and confirm nothing from `docs/handoff/` or scratch files is staged. Use the commit messages from the task headings in `02`.

## Step 5 — push and wait for CI green

    git push

Both jobs on main must pass: `test` (lint + unit) and `generate-and-verify` (real generation + docker compose health check — takes several minutes). Watch with `gh run watch` if `gh` is available, otherwise poll `gh run list`. Do NOT tag until CI is green — the tag is what publishes.

## Step 6 — tag and release (point of no return)

    git tag v{{RELEASE_VERSION}}
    git push origin v{{RELEASE_VERSION}}

`release.yml` then verifies the tag matches the pyproject version, builds, smoke-tests the wheel, publishes to PyPI (trusted publishing), and creates the GitHub Release.

## Step 7 — post-release verification

- `uvx dev-ready@{{RELEASE_VERSION}} --version` reports the new version.
- `uvx dev-ready@{{RELEASE_VERSION}} init smoke-test --yes` in a scratch dir OUTSIDE the repo generates a clean project (in particular: no `.git`, no `copier.yml` in the output). Delete the scratch dir afterwards.

## Step 8 — release report (ALWAYS, success or not)

Append a "## Release Report (v{{RELEASE_VERSION}})" section to `{{DIR}}/reports/execution-report.md`: commits made (hash + message), CI run result, tag pushed, PyPI publish + GitHub Release status, Step 7 evidence, and anything that deviated from this document. This is the CEO's on-disk record of the release — your chat context does not exist for anyone else.

## Troubleshooting

**CI fails after the tag was pushed** — fix the problem (Step 2 discipline applies: trivial = fix, beyond trivial = STOP + escalate), commit and push (Steps 4–5), then move the tag and re-push to re-trigger the pipeline:

    git tag -d v{{RELEASE_VERSION}}
    git push origin :refs/tags/v{{RELEASE_VERSION}}
    git tag v{{RELEASE_VERSION}}
    git push origin v{{RELEASE_VERSION}}

Only safe while the PyPI publish has NOT succeeded — PyPI rejects re-uploading a published version. If PyPI already has {{RELEASE_VERSION}}, do NOT fight it and do NOT pick a new version yourself: releasing the next patch version is a new release decision — STOP and escalate to the CEO.

**`fatal: Unable to create ... index.lock: File exists`** — a previous git process died. Confirm no git process is running, then delete the leftover lock (`rm -f .git/index.lock`, or `del .git\index.lock` on Windows).

**Tag/version mismatch error in release.yml** — the tag and `pyproject.toml` disagree. Fix the version files (Step 1), commit, and re-tag per the flow above.

**Release published to PyPI but no GitHub Release** — the last workflow step failed after publish. Do NOT re-tag (PyPI already has the version); create the release manually: `gh release create v{{RELEASE_VERSION}} --generate-notes`.

## STOP rules (binding, same spirit as ADR-007)

- Any failure that survives 2 real fix attempts: stop, log it in `{{DIR}}/reports/problems.md`, write the Step 8 report with current status, and escalate to the CEO.
- Never force-push, never rewrite history, never re-tag after a successful PyPI publish, never pick a different version number on your own.
```

---

## reports/README.md

```markdown
Phase {{N}} reports (gitignored — nothing here is committed).

- execution-report.md — written by the Junior when implementation ends, ALWAYS (bugs or not). The Senior ALWAYS appends a "Senior Review Addendum" after review — diff summary, fixes, corrections — so this file is the complete phase record. For a release phase, the Release Engineer (07) also appends a "Release Report" here.
- qa-review.md / security-review.md / sre-review.md — the reviewer's review reports (04–06), written here.
- problems.md — open hard bugs. Presence = phase blocked on the Senior (FIX mode); the Senior deletes it when all bugs are fixed. STATUS: ESCALATED-TO-CEO at its top = CEO + Tech Lead take over.
- Release phases only: the phase overview report lives one level up, at `docs/handoff/{{VERSION}}/reports/phase-{{N}}-overview.md`, written by the Release Engineer (07) before committing.
```
