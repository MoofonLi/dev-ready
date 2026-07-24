---
name: handoff
description: Generate the phase document set for a dev-ready development phase under internal process v2 (ADR-013) - the review-gate docs (03-07) plus the reports scaffold; specs come from to-spec and tickets from to-tickets. Use when asked to open a phase, generate/regenerate handoff or gate docs for a version/phase - e.g. "open v0.7 phase 1", "generate the gate docs", "this phase releases, add the release handoff".
---

# dev-ready Phase Handoff Generator (process v2, ADR-013)

Generate the working-document set for one dev-ready phase. Since ADR-013 the
phase runs as the four-layer loop, and the artifacts split accordingly:

```
docs/specs/<version>/fr-NN-<slug>.md      # Planning layer output (to-spec)
                                          # COMMITTED durable doc — replaces 01-plan.md
docs/handoff/<version>/phase-<N>/         # gitignored working tree (ADR-011)
├── tickets/<NN>-<slug>.md                # Dispatch layer output (to-tickets)
│                                         # one per ticket — replaces 02-implementation.md
├── 03-review.md                          # Senior's review brief (state machine entry)
├── 04-qa-review.md                       # QA reviewer brief
├── 05-security-review.md                 # Security reviewer brief
├── 06-sre-review.md                      # SRE reviewer brief
├── 07-release.md                         # Release Engineer brief — RELEASE PHASES ONLY
└── reports/README.md                     # explains execution-report.md / problems.md
```

This skill generates `03`–`07` and `reports/README.md`. The spec is produced by
`to-spec` (Planning layer) and the tickets by `to-tickets` (Dispatch layer) —
do not duplicate their content here; reference them by path.

## Why the documents look the way they do

The CEO (Moofon) runs a file-triggered state machine: handing an agent one
file must be enough for that agent to know its role and act, with zero chat
context from anyone else. Every design rule below exists to keep that true:

- Self-contained: each doc restates the agent's role, inputs, outputs.
- Each **ticket** is single-trigger: the Junior receives one ticket file and
  nothing else. Tickets therefore carry a standing-rules header (inserted by
  `to-tickets` from its dev-ready conventions): TDD mandatory, stay inside the
  declared file footprint, NO state-changing git, the STOP rule, and the
  four-command verification loop. The Junior also follows the `implement`
  skill; the header exists so the rules survive even where skills don't reach.
- problems.md state machine: the Junior ALWAYS writes
  `reports/execution-report.md`; hard bugs additionally go to
  `reports/problems.md` whose header carries its own fix protocol for the
  Senior (fix all -> delete file + update report; unfixable -> mark
  `STATUS: ESCALATED-TO-CEO`). `03`'s entry check routes on the presence of
  problems.md: present = FIX mode, absent = review mode. After review the
  Senior ALWAYS appends a "Senior Review Addendum" to
  `reports/execution-report.md` (diff summary vs the tickets, fixes made
  or "none") — the report is the phase's single on-disk record.
- `03` reviews the work against the **spec** (`docs/specs/<version>/...`) and
  the ticket set: every acceptance criterion checked off, no work outside the
  declared footprints.
- All phase outputs land in `reports/`: the reviewer's three reports are
  written to `docs/handoff/<version>/phase-<N>/reports/{qa,security,sre}-review.md`;
  role definitions live in `.agents/skills/review/references/`.
- NO GIT for agents: all agents edit the working tree only. No commit,
  branch, push, reset, merge — read-only git (`status`/`diff`/`log`) is
  fine. Ticket headings carry Conventional Commit messages used at commit
  time. (History: an agent once committed straight to main; this rule is
  the countermeasure.) Parallel tickets (`parallel-safe: yes`) run in
  separate git worktrees and deliver diffs; the CEO applies and commits —
  see `to-tickets` dev-ready conventions.
- The ONE exemption — `07-release.md`: a phase that ships a version
  ends with `07`, which delegates the ENTIRE release to the Senior acting
  as Release Engineer — version bump, verification, phase overview report,
  staged commits, push, CI wait, tag, PyPI (see `.agents/skills/release/`).
  The exemption travels with the document, not the agent: the Senior holding
  `03` still must not touch git state; only the agent holding `07` may
  run state-changing git, and only for the release steps `07` lists. This
  is safe because `07`'s entry check requires every review gate to already
  be on disk: Senior verdict in `03`, three reviewer APPROVE reports, no
  `problems.md`.
- `docs/handoff/` is gitignored: tickets and gate docs are working files,
  never committed (ADR-011). Specs are the exception by design (ADR-013):
  they live in `docs/specs/` and are committed — the durable record the
  code is reviewed against, in this phase and forever after.
- Real-run checks generate into a scratch dir OUTSIDE the repo, once,
  deleted afterwards.
- Final verification loop in BOTH the tickets and `03`: the same
  four-command suite, run in order — `uv sync --dev`, `uv run pytest`,
  `uv run ruff check .`, `uv run pytest -m network` — with fix-and-rerun
  from step 1 on any failure. The loop is bounded by the existing STOP
  rules (a failure surviving 2 real fix attempts is a hard bug →
  problems.md), so it cannot thrash tokens. The Senior reruns the suite
  himself in `03` Step 2 rather than trusting the Junior's report.

## Steps

1. Read the phase scope. Sources, in order:
   `docs/handoff/<version>/<version>-plan.md` (the phase section +
   "Standing constraints"), the phase's spec(s) in `docs/specs/<version>/`
   (if already written), `docs/version-plan.md` (roadmap context),
   `docs/requirements.md` (the FRs the phase cites), `docs/architecture.md`
   (Module Boundary + Dependency Rules), `docs/decisions/` (the ADRs the
   phase cites — always ADR-013), `docs/cli-spec.md` (exit codes),
   `AGENTS.md` (hard rules),
   `.agents/skills/review/references/{qa,security,sre}.md` (the reviewer's
   standing role definitions). Extract: scope items (with concrete
   `src/dev_ready/...` file paths), acceptance criteria, known traps the
   plan calls out, and cross-phase couplings (things this phase must NOT do
   because a later phase owns them).

2. Check the loop position. If no spec exists yet for this phase's FR(s),
   tell the CEO the Planning layer comes first (grill-with-docs → to-spec)
   and stop — gate docs generated against no spec review nothing. If specs
   exist but no tickets, note that `to-tickets` is the next step; `03`–`06`
   can still be generated in advance from the spec.

3. Determine whether this phase ships a release. Check the plan: does this
   phase close out a version (version bump / release / tag mentioned in the
   phase section or close-out notes)? Not every phase releases. If it does,
   extract the release version `X.Y.Z` (must be greater than the current
   `version` in `pyproject.toml`) and which phase(s) the release covers. If
   the plan is ambiguous, ask the CEO instead of guessing — `07` grants git
   authority, so generating it for a non-release phase is exactly the
   failure mode to avoid.

4. Read `references/templates.md` (next to this file) and instantiate
   `03`–`06` plus `reports/README.md`, replacing every `{{...}}`
   placeholder. (The `01`/`02` templates in that file are superseded by
   specs/tickets — skip them.) For a release phase, additionally
   instantiate `07-release.md`. Do not weaken protocol wording (STOP rules,
   NO GIT, the `07` git-exemption scoping, problems.md template) —
   phase-specific content goes in the marked slots only.

5. Derive the reviewer's phase-specific "Verify specifically" lists from the
   spec and ticket footprints: QA = test-tier coverage of each new behavior +
   error paths + regressions; Security = untrusted input paths, leak/bypass
   surface, pins/deps/workflow-permission deltas; SRE = new failure modes,
   all-or-nothing preservation, message/exit-code quality, added
   maintenance load.

6. Sanity checklist before finishing:
   - All paths use `docs/handoff/<version>/phase-<N>/` (no root-level
     `handoff/`, no `docs/handoffs` — that name is the PRODUCT overlay
     scaffold shipped to generated projects, FR-10, an entirely different
     thing). Specs use `docs/specs/<version>/`.
   - Reviewer reports go to `<phase>/reports/{qa,security,sre}-review.md`.
   - `03` contains the ALWAYS-update-execution-report step before the
     verdict, and names the spec path it reviews against.
   - No instruction telling any agent to commit, branch, or merge — EXCEPT
     inside `07`, whose git authority is explicitly scoped to its own
     release steps. No other file may grant or imply git authority.
   - `07` exists if and only if this phase ships a release; its `X.Y.Z` is
     consistent everywhere in the file and greater than the current
     pyproject version; its entry check names the Senior verdict, all three
     reviewer APPROVE reports, and the absence of `problems.md`.
   - Version/phase strings consistent across all files.
   - Couplings stated (e.g. "Do NOT include README.md — that is Phase 2").

7. Tell the CEO the trigger sequence: Planning (grill-with-docs → to-spec,
   CEO accepts the spec) -> Dispatch (to-tickets, CEO approves the
   breakdown) -> Execution (hand each frontier ticket to a Junior; if
   `reports/problems.md` appears give it + the ticket to the Senior) ->
   Verification (give `03` to the Senior -> `04`–`06` to the Reviewer) ->
   non-release phase: CEO applies any parallel-ticket diffs in order and
   commits using the Conventional Commit messages from the ticket headings;
   release phase: give `07` to the Senior, who runs the whole release
   (commits, push, CI, tag, PyPI) and reports back.
