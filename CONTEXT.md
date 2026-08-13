# dev-ready

Domain glossary for dev-ready — a CLI that scaffolds AI-assisted-development-ready
projects from a pinned upstream template plus a curated overlay. Glossary only:
no implementation details, no specs. Decisions live in `docs/decisions/`.

## Language

### Methodology

**Handoff Protocol**:
The macro, cross-role collaboration mechanism for a multi-agent team: role
definitions, handoff sequence, review gates, and loop rules (ADR-007).
**Retired.** It was generated into projects from v0.2 and configured as data
from v0.7; v0.9 removes it from the overlay (ADR-020) and ADR-021 retires it as
this repo's own practice too — development here runs the Spec Loop and nothing
else. The term survives only to name what was removed.
_Avoid_: workflow, team workflow, agent workflow, multi-agent flow

**Protocol Configuration**:
The authoritative runtime description of a Handoff Protocol: stable role ids
with editable titles and model assignments, read rather than copied. Retired
from generated projects in v0.9 along with the Protocol itself (ADR-020).
_Avoid_: rendered role table, workflow config

**Spec Loop**:
The micro, within-session development loop one agent follows for one task:
setup → grill → spec → tickets → implement (TDD, review) → architecture
cleanup. From v0.9 every generated project has one and none can decline it
(ADR-018). The name of the **method**; it is not the name of any one
implementation of it, and from v0.11 the item that vendors Matt Pocock's is
called `mattpocock` (ADR-024). Through v0.8 it shipped as the optional catalog
item `spec-loop`.
_Avoid_: spec-workflow, Pocock workflow, dev workflow, spine, backbone

**Engineering Flow**:
The development method a generated project is built around, chosen first and
recorded in the stamp — the [[Catalog Item]] the Dev Category holds. Named for
its source (`mattpocock`, with `superpowers` and `addyosmani` reserved) because
what distinguishes candidate flows is who wrote them, not that they are
spec-driven, which they all are (ADR-024). Asked even when the catalog offers
one, because at n=1 the question **discloses** rather than chooses: a user who
is never shown their project's development method does not know it has one.
_Avoid_: development loop (as a user-facing word), workflow, methodology,
pipeline, spine

**Announced Flow**:
An [[Engineering Flow]] listed in the menu as `(coming soon)` before it ships,
marked by a `status` field in the manifest. It is **not** a [[Catalog Item]] —
selectability is a Catalog Item's defining property and non-selectability is an
Announced Flow's whole point — so the loader partitions it into a separate
`announced_loops` collection that the selection machinery cannot see (ADR-024,
as amended 2026-08-13). Read by exactly two consumers: the flow prompt, which
renders it unselectable, and the `--flow` error path, which says *not yet
available* rather than *unknown*. Placeholder text carries no version number,
and each entry is deleted as its flow ships or the menu accumulates promises.
_Avoid_: placeholder item, disabled item, stub flow, future flow

**Flow Chain**:
The ordered steps of an [[Engineering Flow]] as a generated project describes
them. A **default path, not a rule** — every step is user-invoked
(`disable-model-invocation: true` upstream), and a small change may start at
`implement`. Steps a chain entry calls internally are not chain entries: `tdd`
and `code-review` belong to `implement`, which invokes both, and listing them as
peers turns tools into phases.
_Avoid_: pipeline, stages, the seven steps, phase order

**Workflow**:
Reserved exclusively for GitHub Actions workflow files (`ci.yml`, `release.yml`,
`upstream-bump.yml`). Never used for the Handoff Protocol or the Spec Loop.

### Catalog

**Category**:
The top-level axis a user selects along from v0.9: Dev, Security, Quality,
Design, Token Optimize (ADR-017). A Category cuts across Components — Design
holds both a skill and a design-doc template — and is the vocabulary prompts and
flags are expressed in. Dev holds the [[Engineering Flow]] and from v0.11 is
asked under that name instead of appearing in a checkbox, where selecting it
could not matter; the other four are multi-select, walked one at a time, and
declined by pressing Enter (ADR-024). Categories are named for what they hold
today, because adding one is free and renaming one breaks every stamped
project — a Category's *description* is free to change, which is why widening
one is the fix when membership grows past its wording.
_Avoid_: section, block, group, component (as a user-facing word), Ops

**Component**:
An internal grouping that decides where a Catalog Item's files are written:
skills, mcp, docs. It was the user-facing selection axis through v0.8 and is not
one from v0.9 (ADR-017). A fourth, `handoff` — named `agents` through v0.7 —
generated the Handoff Protocol scaffold and is removed in v0.9 (ADR-020).
_Avoid_: agents (as a component name); using it for anything a user picks

**Catalog Item**:
An individually selectable unit, declared as data in the manifest (ADR-010) and
presented under exactly one Category. **Selectable is the defining word**: an
entry a user cannot choose is not a Catalog Item however it is declared, which
is what puts an [[Announced Flow]] outside the type and outside the catalog the
loader builds.
_Avoid_: skill entry, module, addon

**Generation Skill**:
The single skill this repository distributes for installation into a user's own
coding agent, which interviews the user about what they are building and
composes one `dev-ready init` command from the answers (FR-24, rewritten as an
interview by FR-34). It is defined by three things it is not: never a
[[Catalog Item]], never part of a generated project's overlay, and not one of
this repository's own process skills. Singular by construction — the repository
distributes exactly one, from one source path, however many channels carry it:
the cross-agent installer reaches every agent, and the Claude and Codex plugin
manifests are additional storefronts over the same directory, never second
copies. From v0.12 the interview also recommends an [[Engineering Flow]], which
is why no second interviewing skill may exist — two would question the user
twice.
_Avoid_: setup skill, init skill, the dev-ready skill, bootstrap skill, generate skill

**Enhancement**:
A Catalog Item outside the Spec Loop, optionally declaring the [[Mount Point]]
it attaches to. Everything a user can add or drop is an Enhancement.
_Avoid_: plugin, extra, addon, optional skill

**Mount Point**:
The Spec Loop skill an [[Enhancement]] attaches to, declared as manifest data
and optional — an Enhancement whose guidance has no single right moment
declares none. A mount decides *when* an agent is reminded, never whether it can
find the skill: a [[Pointer Stub]] already makes every selected skill
discoverable, so a mount at the wrong step is worse than no mount. Guidance is
injected at generation time; nothing rewrites a skill at runtime (ADR-018, as
amended 2026-08-03).
_Avoid_: hook, anchor, attachment point, phase

**Default Set**:
What a generated project receives when the user accepts every default: the Spec
Loop. From v0.11 it is a **non-interactive concept only** — what `--yes` and the
flag path resolve to. It stopped being an interactive question once both answers
were measured to produce byte-identical selections (ADR-024). It is the only
thing the size limit governs — the rest of the catalog is
unbounded (ADR-018). Every Enhancement is off by default, reference
design-document templates included. The project's own documentation skeletons
were part of it until the 2026-08-02 amendment moved them out of selection
entirely; they are [[Overlay Infrastructure]] now.
_Avoid_: default selection, baseline, starter set, the cap

**Overlay Infrastructure**:
Overlay content every generated project receives unconditionally, named by no
Category and selectable by nothing: `AGENTS.md`, the project `README.md`, the
Spec Loop, `docs/architecture.md`, `docs/requirements.md`, and the stamp. A
mandatory process may not have optional outputs — the loop writes the two
documentation skeletons, so they are not a [[Catalog Item]] (ADR-018,
2026-08-02 amendment). `.mcp.json` is adjacent but conditional: it appears only
when a selected Enhancement needs it.
_Avoid_: always-on item, implicit default, base overlay, core set

**Standards Source**:
The file a generated project offers to a review step asking what this repository
documents about how its code should be written. It is the generated `AGENTS.md`,
which says so in its own text — the project's tooling and the rules no tool
enforces belong in the one file every agent session already loads, so the answer
is never a hop away and never a second copy. Naming the linter does not make one:
a reviewer is told to skip whatever tooling already enforces, so a tool list
answers a different question than this one. Singular per project, and always
[[Overlay Infrastructure]].
_Avoid_: coding standards file, CONTRIBUTING.md, style guide, house style, conventions doc

**Bundle**:
A catalog item that materializes multiple related assets selected as one unit
because they are only valuable together, including the dependency closure those
assets need.

**Design Reference**:
An [[Enhancement]] that is a whole design system written for an agent to build
against — tokens, type scale, component rules — rather than guidance about how
to work. Multi-select on purpose: a project legitimately wants one direction for
its marketing surface and another for its dashboard, and the two shipped
references are already recorded together in stamps, so single-select would break
a contract to prevent a cost only a deliberate user incurs (FR-40). Which
reference governs which surface is the user's to record in their own project
documents; dev-ready declares no mapping and will not invent one.
_Avoid_: theme, skin, style guide, brand pack, DESIGN.md (the file, not the concept)

### Agent targets

**Agent Target**:
A coding agent whose native configuration layout a generated project renders
into, selected per project and independently of catalog items. Never written as
a bare "target" — in this project that word means the output directory.
_Avoid_: target, render target, harness, IDE, editor

**Canonical Content**:
The single authoritative copy of an overlay-managed skill or rule set in a
generated project, written at the open-standard location regardless of which
Agent Targets are selected. Every Agent Target reaches the same bytes.
_Avoid_: master copy, source-of-truth copy, primary

**Pointer Stub**:
A small file at an Agent Target's native path that identifies an item and
directs the agent to its [[Canonical Content]], preserving the canonical
frontmatter so discovery still sees the skill's name and description.
**Retired in v0.12** by [[Skill Delivery Mode]] (ADR-025) — not because it
failed, but to follow the ecosystem convention of offering symlink or copy. The
term survives to name what generated projects carried from v0.8 to v0.11, which
`upgrade` must still recognise and retire.
_Avoid_: shim, alias, symlink, mirror, proxy

**Skill Delivery Mode**:
How an [[Agent Target]]'s skills directory receives content: `symlink` (a link
to the [[Canonical Content]]) or `copy` (the full content). A recorded user
selection, never a detected platform fallback — an explicit input keeps output
deterministic (NFR-1) where a fallback would make one dev-ready version produce
different projects on different machines. Asked only when a selected target
declares a directory other than `.agents/skills/`; `copy` is the
non-interactive default, because it is the mode that survives `git clone`
everywhere. Canonical Content is written in both modes and is never the thing
being chosen.
_Avoid_: install mode, link mode, symlinking, deployment mode

**Agent Target Map**:
The manifest's record of each Agent Target's project-level skills directory,
derived from the reference installer's machine-readable agent list and held to
it by a drift check (ADR-019). Never a transcription — every entry is generated,
and an entry a human typed is a defect. Rules and MCP paths are absent from that
source and stay hand-declared.
_Avoid_: agent table, path map, target registry, transcription

**Standard-Compliant Agent**:
A coding agent that reads [[Canonical Content]] at `.agents/skills/` and is
therefore never an [[Agent Target]] — it needs no Pointer Stub and no selection.
Absence from the Agent Target Map means full support, not missing support, which
is why the selection prompt, the generation report, and the [[Generation Skill]]'s
interview all name these agents. The interview is the earliest of the three: it
runs before the CLI does, so it is where the misreading is cheapest to prevent.
_Avoid_: standard agent, generic agent, default agent, unsupported agent

### Lifecycle

**Base Provenance**:
The immutable identity of the upstream template snapshot from which a project
was originally generated. An overlay-only upgrade never changes it.
_Avoid_: current upstream pin, upgraded base

**Overlay Currency**:
How current a generated project's dev-ready-managed overlay is: the dev-ready
version, selected catalog items and their pins, and managed-file inventory.
It can advance without changing Base Provenance.
_Avoid_: project version, upstream currency

### Written language

**Language Boundary**:
The rule fixing what language each surface is written in (ADR-016). Everything
dev-ready emits and everything it generates is English — generated content's
consumer is a model, and English is what models parse most reliably. Chinese
exists only in repository documentation addressed to external readers, today
`README.zh-TW.md`. dev-ready has no localized runtime and records no language.
_Avoid_: localization, i18n, localized surface, translation policy

### Internal process (ADR-021)

**Spec**:
The durable, committed record of what one FR builds and why, produced by
`to-spec` and accepted by Moofon. Code is reviewed against it, in the phase and
after — and it is the only artifact of the phase that outlives it.
_Avoid_: plan, PRD, 01-plan

**Ticket**:
A tracer-bullet vertical slice sized for one session, declaring its blocked-by
edges, file footprint, parallel-safety, and commit message. A gitignored working
file with a one-phase lifespan, self-contained enough to run cold.
_Avoid_: task, issue, 02-implementation

**File footprint**:
The set of paths a ticket is expected to create or modify; the basis for
deciding whether tickets may run in parallel.

**Hat**:
One of the three roles a session wears in turn — Tech Lead, Engineer, Reviewer.
Worn, not assigned: no hat binds to a model, a tool, or a separate session, and
no document has to pass between them.
_Avoid_: role assignment, agent identity, CEO / Senior / Junior (retired with
ADR-007)
