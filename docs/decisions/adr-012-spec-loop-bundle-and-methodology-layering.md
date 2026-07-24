# ADR-012: Spec Loop as a single bundled catalog item, layered with the Handoff Protocol (v0.7)

- Status: Accepted (2026-07-24)
- Context: The CEO adopted Matt Pocock's within-session development loop (grill →
  spec → tickets → TDD → review → architecture cleanup) as content dev-ready should
  ship. Three of its steps (tdd, diagnosing-bugs, code-review) are already catalog
  items vendored from mattpocock/skills; four are not (grill, to-spec, to-tickets,
  improve-architecture). Adding four separate items would put the catalog at 13,
  over the hard cap of 10 (version-plan curation principles). Separately, generated
  projects can already include the multi-agent Handoff Protocol (FR-10, ADR-007) —
  a second methodology in the same CLAUDE.md, so an agent needs to know which one
  governs when. Industry practice also suggested a root `CONTEXT.md` architecture
  file, which would compete with CLAUDE.md as an entry point. Finally, the word
  "workflow" had come to mean three unrelated things (the FR-23 handoff config,
  the Pocock loop, GitHub Actions files).
- Decision:
  - **One bundle, not four items.** The four missing steps ship as a single
    catalog item, id `spec-loop`, in the `skills` component — a *bundle*
    (multiple asset directories, one selection unit; the manifest `paths` list
    already supports this). Rationale: the loop's value is the whole cycle;
    selecting half a methodology is meaningless. Catalog lands at exactly 10/10.
    The curation principles gain the amendment: *a workflow bundle counts as one
    item against the cap.* Same vendored repo and pin as the existing mattpocock
    items — near-zero added maintenance.
  - **Layering, not exclusion and not presets.** When a project selects both
    `agents` and `spec-loop`, the generated CLAUDE.md renders a four-phase
    mapping — Planning (Lead: grill/to-spec) → Dispatch (Senior: to-tickets +
    handoff) → Execution (Junior: tdd/code-review) → Verification (QA/Security/SRE
    gates). The Handoff Protocol is the exoskeleton (cross-role coordination);
    the Spec Loop is the neuromuscular system (within-session execution).
    Rendering is strictly conditional: selecting only one side must produce no
    reference to the other side's skills. Rejected alternatives: mutual
    exclusion (a solo user with occasional multi-agent runs is legitimate) and
    promoting the Spec Loop to a second FR-23 preset (violates D-1's
    "preset, not framework" deferral).
  - **No `CONTEXT.md` in generated projects.** The auto-loaded entry point stays
    CLAUDE.md alone (matching the AGENTS.md standard and FR-26 portability).
    The architecture-truth role is filled by a new `architecture.md` template in
    the `docs` component (system overview / module boundaries / dependency
    rules skeleton), maintained by the Tech Lead role and linked from CLAUDE.md.
    (dev-ready's own repo `CONTEXT.md` is unrelated: it is this repo's domain
    glossary, not a generated artifact.)
  - **Naming.** The macro mechanism keeps its ADR-007 name, *Handoff Protocol*;
    the FR-23 config file is `docs/handoffs/protocol.yaml` (amending D-1's
    provisional `workflow.yaml`). The micro loop is the *Spec Loop* (item id
    `spec-loop`, not `spec-workflow`). "Workflow" is reserved for GitHub Actions
    files. Recorded in the root `CONTEXT.md` glossary.
- Consequences: The id `spec-loop` and the four-phase CLAUDE.md section become
  compatibility surface once v0.7 ships — the id enters user stamps and the
  `--skills` flag contract, and the rendered section enters the stamp inventory
  as an upgrade-managed file; renaming either later breaks check/upgrade.
  The catalog cap is fully consumed: any future skill addition must evict an
  existing item or amend the cap by a new decision. The conditional-rendering
  rule is an acceptance criterion for FR-28's implementation and tests.
