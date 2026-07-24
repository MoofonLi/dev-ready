# ADR-013: Internal process v2 — the Spec Loop layered into the Handoff Protocol (amends ADR-007, ADR-011)

- Status: Accepted (2026-07-24)
- Context: dev-ready's own development ran on the ADR-007 handoff loop with a
  seven-document set (`01-plan` … `07-release`), all gitignored working files
  (ADR-011). The CEO adopted the same four-phase model dev-ready will ship to
  users (ADR-012) for internal development itself: Planning → Dispatch →
  Execution → Verification, with the Spec Loop steps (grill → spec → tickets →
  TDD → review) as the concrete moves inside each layer. Three frictions had to
  be resolved: (1) the old `01/02` documents overlapped with what specs and
  tickets now produce; (2) everything in the handoff tree evaporates after a
  phase (gitignored), but the Spec Loop's anti-drift value depends on the spec
  surviving next to the code; (3) the flow's steps are executed via agent
  skills, which must not re-bind roles to one tool, and parallel ticket
  dispatch collides with the single-working-tree, only-CEO-commits rule.
- Decision:
  - **Specs are durable, committed docs** at `docs/specs/<version>/fr-NN-<slug>.md`,
    aligned with FR numbering. They replace `01-plan.md`. This is an explicit
    exemption to ADR-011's "handoff artifacts are never committed" rule —
    tickets and gate docs remain gitignored working files. Rationale: the spec
    is what code is reviewed against, in the phase and long after; a spec that
    evaporates at phase end only prevents drift while the phase is open.
  - **Tickets replace `02-implementation.md`**: one file per tracer-bullet
    ticket under `docs/handoff/<version>/phase-N/tickets/`, each declaring
    blocked-by edges, an expected **file footprint**, and a `parallel-safe`
    marker. `03`–`06` (Senior review, QA/Security/SRE gates) and `07`
    (release, with its scoped git exemption) survive unchanged; `03` now
    reviews against the spec.
  - **Sequential by default, parallel as a controlled exception.** One Junior,
    one ticket, main working tree, no state-changing git — unchanged. Parallel
    dispatch is allowed only for tickets whose footprints are provably
    disjoint (`parallel-safe: yes`); each parallel Junior works in its own git
    worktree and delivers a diff/patch that the CEO applies and commits in
    order. The only-CEO-commits rule is never relaxed (07-release remains the
    sole exemption).
  - **Steps live as repo process skills, tool-agnostically.** All Spec Loop
    step skills are versioned in `.agents/skills/` (open Agent Skills format,
    `.claude/skills/` stubs); AGENTS.md describes the loop by step names, and
    agents without skill support follow the SKILL.md files as written
    instructions. The skill set is curated to the loop; sixteen skills remain
    and eight unrelated ones were removed (2026-07-24).
- Consequences: `docs/specs/` becomes a committed, growing record of what was
  built and why — review gates and future agents read it instead of chat
  history. The `handoff` skill now generates only `03`–`07` + reports; specs
  and tickets come from `to-spec` / `to-tickets`. `to-tickets` gains hard
  requirements (footprint + parallel-safe declarations) that make the parallel
  rule enforceable at dispatch time rather than discovered at merge time.
  Pre-v2 phases (v0.1–v0.6) keep their old document sets in the gitignored
  tree; nothing is migrated. If parallel dispatch proves routinely valuable,
  granting Juniors scoped commit rights on ticket branches is the designated
  upgrade path (revisit by new ADR).
