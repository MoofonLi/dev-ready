# ADR-012: Spec Loop as a single bundled catalog item, layered with the Handoff Protocol (v0.7)

- Status: Accepted (2026-07-24); amended (2026-07-25) after the v0.7
  `grill-with-docs` pass
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
    (multiple asset directories and required existing items, one explicit
    selection unit). Rationale: the loop's value is the whole cycle;
    selecting half a methodology is meaningless. Catalog lands at exactly 10/10.
    The curation principles gain the amendment: *a methodology bundle counts as one
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
  - **No pre-created `CONTEXT.md` in generated projects.** The auto-loaded entry point stays
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
  (**The rename happened, deliberately and with that cost paid — see the
  2026-08-12 amendment at the end of this file.**)
  The catalog cap is fully consumed: any future skill addition must evict an
  existing item or amend the cap by a new decision. The conditional-rendering
  rule is an acceptance criterion for FR-28's implementation and tests.

## 2026-07-25 amendment — dependency closure and generated process

The v0.7 plan audit found that the four advertised missing steps are not four
self-contained directories at the pinned mattpocock/skills commit.
`grill-with-docs` invokes `grilling` and `domain-modeling`; architecture cleanup
invokes `codebase-design`, `grilling`, and `domain-modeling`; the execution layer
depends on the already-catalogued `tdd`, `diagnosing-bugs`, and `code-review`
items. Vendoring only four directories would therefore ship a broken bundle,
and allowing those three existing items to be deselected would let CLAUDE.md
name skills that are absent.

`spec-loop` consequently owns the complete vendored asset closure of its four
advertised steps at the manifest-pinned commit and declares the three existing
catalog items as requirements. Selecting `spec-loop` automatically resolves
those requirements; the resolved selection is shown to the user and recorded
in the stamp. The existing item ids remain independently selectable for
backward compatibility. This changes neither the 10/10 catalog count nor the
one-explicit-selection promise.

The bundle also supplies a small original tracker/domain configuration so the
upstream skills do not fall through to an unshipped
`setup-matt-pocock-skills` command. Its standalone default is a role-neutral
local tracker; with Handoff Protocol selected it points at the process-v2 spec
and ticket locations. This is integration glue inside the same bundle, not an
additional catalog item or preset.

When Handoff Protocol and Spec Loop are selected together, generated projects
use the four-layer process-v2 artifact model rather than retaining the legacy
`01-plan.md` / `02-implementation.md` flow: durable specs, per-ticket dispatch,
one-ticket execution, and the `03`–`06` review gates. Active phase working files
are ignored while the protocol configuration, reusable scaffold, and specs are
durable. `docs/handoffs/protocol.yaml` is the sole runtime authority for role
titles and model assignments. Generated prose names stable role ids and reads
editable values from that file, so a one-line model edit cannot leave stale
copies in CLAUDE.md or gate templates.

The generator still does not pre-create `CONTEXT.md`; the vendored
domain-modeling companion may create that glossary lazily after a user resolves
a real domain term. That later skill output is not a generated instruction
entry point and does not replace `docs/architecture.md`.

## 2026-08-12 amendment — the id `spec-loop` is renamed `mattpocock` (ADR-024)

The naming clause above chose `spec-loop` over `spec-workflow` to keep
"workflow" reserved for GitHub Actions files. That reservation stands. What
changes is the other half of the name, and the cost this ADR recorded for
changing it is being paid deliberately rather than avoided.

`spec-loop` was chosen when the loop was the only one. With a second and third
Engineering Flow scheduled for v0.12 and v0.13 — `obra/superpowers` and
`addyosmani/agent-skills` — the id has to say **which** flow, and it cannot:
all three are spec-driven, so the property the name states is the property they
share. A name that describes every member of a set is not an identifier for one
of them.

Flows are therefore named for their source. `spec-loop` becomes `mattpocock`;
`superpowers` and `addyosmani` are reserved. The display name is
`Matt Pocock's skills`, carried in a new `title` field so the id is not asked to
be both a key and a label.

The compatibility cost this ADR predicted is real and is met head-on: `upgrade`
carries a permanent `spec-loop` → `mattpocock` alias for as long as v5 stamps
exist, and the flag contract, `docs/cli-spec.md`, `README.md`, and the
[[Generation Skill]] all change value. **The stamp version does not advance** —
no field is added, removed, or re-typed. It is done now because the v1.0
real-users gate has not been met, so there is no external project to migrate,
and the price will never be lower than it is today.

The *Spec Loop* term itself is not renamed. It stays the name of the method in
`CONTEXT.md`; `mattpocock` names the one implementation of it that dev-ready
vendors.
