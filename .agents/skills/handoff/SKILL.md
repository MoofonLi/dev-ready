---
name: handoff
description: Generate the multi-agent handoff documents for a dev-ready development phase (Tech Lead -> Senior -> Junior -> Reviewer workflow, ADR-007/ADR-011) - six docs per phase, plus a seventh release handoff (07-release) when the phase ships a version. Use when asked to create, generate, or regenerate handoff docs for a version/phase - e.g. "generate v0.3 phase 2 handoffs", "open a new phase", "this phase releases, add the release handoff".
---

# dev-ready Handoff Generator

Generate the complete handoff document set for one dev-ready phase, under
`docs/handoff/<version>/phase-<N>/` in the dev-ready repo:

```
docs/handoff/<version>/phase-<N>/
├── 01-plan.md              # brief to the Senior Engineer
├── 02-implementation.md  # the ONLY file the Junior receives
├── 03-review.md            # Senior's review brief (state machine entry)
├── 04-qa-review.md              # QA reviewer brief
├── 05-security-review.md        # Security reviewer brief
├── 06-sre-review.md             # SRE reviewer brief
├── 07-release.md           # Release Engineer brief — RELEASE PHASES ONLY
└── reports/README.md            # explains execution-report.md / problems.md
```

## Why the documents look the way they do

The CEO (Moofon) runs a file-triggered state machine: handing an agent one
file must be enough for that agent to know its role and act, with zero chat
context from anyone else. Every design rule below exists to keep that true:

- Self-contained: each doc restates the agent's role, inputs, outputs.
- `02` is single-trigger: it carries the Tech Lead's working rules on top
  AND a section "Task Breakdown & Implementation Details (Senior writes here)"
  that the Senior fills. The Junior gets `02` and nothing else.
- problems.md state machine: the Junior ALWAYS writes
  `reports/execution-report.md`; hard bugs additionally go to
  `reports/problems.md` whose header carries its own fix protocol for the
  Senior (fix all -> delete file + update report; unfixable -> mark
  `STATUS: ESCALATED-TO-CEO`). `03`'s entry check routes on the presence of
  problems.md: present = FIX mode, absent = review mode. After review the
  Senior ALWAYS appends a "Senior Review Addendum" to
  `reports/execution-report.md` (diff summary vs the breakdown, fixes made
  or "none") — the report is the phase's single on-disk record.
- All phase outputs land in `reports/`: the reviewer's three reports are
  written to `docs/handoff/<version>/phase-<N>/reports/{qa,security,sre}-review.md`;
  role definitions live in `.agents/skills/review/references/`.
- NO GIT for agents: all agents edit the working tree only. No commit,
  branch, push, reset, merge — read-only git (`status`/`diff`/`log`) is
  fine. Task headings carry Conventional Commit messages used at commit
  time. (History: an agent once committed straight to main; this rule is
  the countermeasure.)
- The ONE exemption — `07-release.md`: a phase that ships a version
  ends with `07`, which delegates the ENTIRE release to the Senior acting
  as Release Engineer — version bump, verification, phase overview report,
  staged commits, push, CI wait, tag, PyPI (see `.agents/skills/release/`).
  The exemption travels with the document, not the agent: the Senior holding
  `01`/`03` still must not touch git state; only the agent holding `07` may
  run state-changing git, and only for the release steps `07` lists. This
  is safe because `07`'s entry check requires every review gate to already
  be on disk: Senior verdict in `03`, three reviewer APPROVE reports, no
  `problems.md`.
- `docs/handoff/` is gitignored: handoffs are working files, never
  committed (ADR-011).
- Real-run checks generate into a scratch dir OUTSIDE the repo, once,
  deleted afterwards.
- Final verification loop in BOTH `02` and `03`: each ends with the same
  four-command suite, run in order — `uv sync --dev`, `uv run pytest`,
  `uv run ruff check .`, `uv run pytest -m network` — with fix-and-rerun
  from step 1 on any failure. The loop is bounded by the existing STOP
  rules (a failure surviving 2 real fix attempts is a hard bug →
  problems.md), so it cannot thrash tokens. The Senior reruns the suite
  himself in `03` Step 2 rather than trusting the Junior's report. This
  lives in the handoff docs, not in editor hooks, because the Junior runs in
  Antigravity where hooks do not reach — the doc is the only channel that
  reaches every agent.

## Steps

1. Read the phase scope. Sources, in order:
   `docs/handoff/<version>/<version>-plan.md` (the phase section +
   "Standing constraints"), `docs/version-plan.md` (roadmap context),
   `docs/requirements.md` (the FRs the phase cites), `docs/architecture.md`
   (Module Boundary + Dependency Rules), `docs/decisions/` (the ADRs the
   phase cites), `docs/cli-spec.md` (exit codes), `AGENTS.md` (hard rules),
   `.agents/skills/review/references/{qa,security,sre}.md` (the reviewer's
   standing role definitions). Extract: scope items (with concrete `src/dev_ready/...`
   file paths), acceptance criteria, known traps the plan calls out, and
   cross-phase couplings (things this phase must NOT do because a later
   phase owns them).

2. Determine whether this phase ships a release. Check the plan: does this
   phase close out a version (version bump / release / tag mentioned in the
   phase section or close-out notes)? Not every phase releases. If it does,
   extract the release version `X.Y.Z` (must be greater than the current
   `version` in `pyproject.toml`) and which phase(s) the release covers. If
   the plan is ambiguous, ask the CEO instead of guessing — `07` grants git
   authority, so generating it for a non-release phase is exactly the
   failure mode to avoid.

3. Read `references/templates.md` (next to this file) and instantiate the
   seven base files, replacing every `{{...}}` placeholder. For a release
   phase, additionally instantiate `07-release.md`. Do not weaken
   protocol wording (STOP rules, NO GIT, the `07` git-exemption scoping,
   problems.md template) — phase-specific content goes in the marked slots
   only.

4. Derive the reviewer's phase-specific "Verify specifically" lists from the phase's
   change surface: QA = test-tier coverage of each new behavior + error
   paths + regressions; Security = untrusted input paths, leak/bypass
   surface, pins/deps/workflow-permission deltas; SRE = new failure modes,
   all-or-nothing preservation, message/exit-code quality, added
   maintenance load.

5. Sanity checklist before finishing:
   - All paths use `docs/handoff/<version>/phase-<N>/` (no root-level
     `handoff/`, no `docs/handoffs` — that name is the PRODUCT overlay
     scaffold shipped to generated projects, FR-10, an entirely different
     thing).
   - Reviewer reports go to `<phase>/reports/{qa,security,sre}-review.md`.
   - `03` contains the ALWAYS-update-execution-report step before the verdict.
   - No instruction telling any agent to commit, branch, or merge — EXCEPT
     inside `07`, whose git authority is explicitly scoped to its own
     release steps. No other file may grant or imply git authority.
   - `07` exists if and only if this phase ships a release; its `X.Y.Z` is
     consistent everywhere in the file and greater than the current
     pyproject version; its entry check names the Senior verdict, all three
     reviewer APPROVE reports, and the absence of `problems.md`.
   - Version/phase strings consistent across all files.
   - Couplings stated (e.g. "Do NOT include README.md — that is Phase 2").
   - `01` Status says AWAITING TASK BREAKDOWN; `02` Senior section says
     it is empty until the Senior fills it.
   - `02` and `03` both carry the four-command final verification sequence
     (`uv sync --dev` → `uv run pytest` → `uv run ruff check .` →
     `uv run pytest -m network`) with the fix-and-rerun loop, and `02`'s
     loop explicitly defers to the STOP rules.

6. Tell the CEO the trigger sequence: give `01` to the Senior -> give `02` to
   the Junior -> if `reports/problems.md` appears give it + `02` to the Senior ->
   otherwise give `03` to the Senior -> then `04`–`06` to the Reviewer -> non-release
   phase: CEO commits using the Conventional Commit messages from the task
   headings; release phase: give `07` to the Senior, who runs the whole release
   (commits, push, CI, tag, PyPI) and reports back.
