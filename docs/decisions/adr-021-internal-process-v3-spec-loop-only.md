# ADR-021: Internal process v3 — the Spec Loop only, no generated gate documents (supersedes ADR-007's protocol; amends ADR-011, ADR-013)

- Status: Accepted (2026-07-31)
- Context: This repository's own development ran the ADR-007 handoff protocol,
  narrowed by ADR-013 into a four-layer loop. Every phase generated a document
  set — `03-review.md`, `04-qa-review.md`, `05-security-review.md`,
  `06-sre-review.md`, `reports/README.md`, plus `07-release.md` on release
  phases — and produced four more files during the run (execution report, three
  reviewer reports, sometimes `problems.md`). All of it is gitignored with a
  one-phase lifespan: generated, read once, discarded. Three frictions made the
  ceremony no longer worth its cost. (1) The gate briefs mostly restate standing
  role definitions that already live in the skills, so generating them per phase
  buys repetition, not information. (2) The review layer duplicates work the
  `code-review` skill already does at the end of `implement` — two axes,
  Standards and Spec, in parallel sub-agents. (3) The methodology dev-ready
  itself vendors and ships is the Spec Loop — grill → spec → tickets → implement
  — and this repo had been running a heavier variant of it, so the process we
  practise drifted from the one we publish. ADR-020 already stopped *generating*
  the Handoff Protocol for users on the grounds that it is this repo's practice,
  not a product surface; this ADR simplifies the practice itself.
- Decision:
  - **The internal process is the Spec Loop, four steps, nothing more**:
    `grill-with-docs` → `to-spec` → `to-tickets` → `implement`. Review is a step
    *inside* `implement` (run `code-review` when a ticket's work is done), not a
    layer with its own documents.
  - **No phase document set is generated.** `03`–`07` and the `reports/`
    scaffold are retired, along with the execution report and `problems.md`. The
    `handoff` and `review` process skills are deleted; the QA / Security / SRE
    standing definitions go with them.
  - **Artifacts unchanged where they were already right**: specs stay durable
    and committed at `docs/specs/<version>/fr-NN-<slug>.md` (ADR-013); tickets
    stay gitignored working files at
    `docs/handoff/<version>/phase-N/tickets/<NN>-<slug>.md`; version plans stay
    at `docs/handoff/<version>/<version>-plan.md`. A phase is still the unit a
    version is cut into (`planning`), and a release is still run by `release`.
  - **Three roles, worn rather than assigned**: Tech Lead (grill, spec,
    decisions), Engineer (tickets, implement, TDD), Reviewer (the `code-review`
    pass). One agent session may wear all three in sequence. No role binds to a
    model or a tool, no role needs to be designated up front, and no handoff
    document is required to pass work between them. This replaces ADR-007's
    CEO / Tech Lead / Senior / Junior / IBM Bob table.
  - **Git authority is per-action consent**: no agent runs `commit`, `push`,
    `branch`, `merge`, or `reset` unless Moofon grants permission for that
    specific action, in the moment. Read-only git (`status`, `diff`, `log`) is
    always fine. This replaces both the blanket "only the CEO commits" rule and
    the `07-release.md` scoped git exemption — `release` now runs under the same
    consent rule as every other step.
  - **Escalation without a file**: a hard bug stops the ticket and is reported
    to Moofon in the session. Nothing is written to `problems.md`, because there
    is no longer a second agent who would read it from disk.
- Consequences: per-phase generated documents drop from five-plus briefs and
  four reports to zero — the only per-phase artifacts are the committed spec and
  the ticket files. Two losses are accepted deliberately. First, QA / Security /
  SRE stop being a required gate; their substance is not lost from the repo
  (hard rules in `AGENTS.md`, exit codes in `docs/cli-spec.md`, the two-axis
  `code-review` skill), but a dedicated security or SRE pass now has to be asked
  for by name. Second, the file-triggered state machine no longer holds for
  review — it still holds for execution, where a ticket file plus the `implement`
  skill is enough to run a ticket cold, which is why tickets keep their
  standing-rules header. `docs/handoff/run-handoff.sh`, the pipeline that drove
  `01`→`07`, has no documents left to drive and is retired with them. Historical
  phase folders (v0.1 through the v0.9 phases already generated) keep their old
  document sets in the gitignored tree; nothing is migrated. ADR-007's protocol
  and role table and ADR-013's four-layer loop and gate documents are superseded
  by this ADR; ADR-011's layout decision stands, minus the `handoff` and `review`
  skills it created. If the missing review depth ever costs a real defect, the
  designated upgrade path is to reinstate the lenses as an on-demand skill — not
  as a per-phase generated document (revisit by new ADR).
