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
The ordered steps of an [[Engineering Flow]], declared as manifest data in that
flow's `chain` field and rendered from it (ADR-029). A **default path, not a
rule** — a change adding no observable behaviour may start partway along it. An
entry is one step, or a **choice between steps** where the flow offers one, as
`superpowers` does at its fourth position. Steps a chain entry calls internally
are not chain entries: `tdd` and `code-review` belong to `implement`, which
invokes both, and listing them as peers turns tools into phases. The
[[Setup Step]] heads every chain but is **not** a `chain` entry, because it is
unconditional infrastructure rather than the flow's own (ADR-026). Whether the
user or the agent starts each entry is the chain's [[Flow Invocation]] and
differs per flow, so a generated project describes its own chain and never the
other's.
_Avoid_: pipeline, stages, the seven steps, phase order

**Flow Convention**:
The optional extra paragraph an [[Engineering Flow]] adds after its rendered
[[Flow Chain]] sentence in the generated `AGENTS.md`. A flow that declares none
is described by the chain sentence alone. Declared as a catalog source path on
the development-loop [[Catalog Item]]; it is overlay-interpolated and is never
a file in the generated project.
_Avoid_: flow guidance, guidance dict, convention paragraph, _FLOW_GUIDANCE

**Flow Invocation**:
Who starts a [[Flow Chain]]'s entries — the user, or the agent on its own.
Declared per [[Engineering Flow]] in the manifest as `user` or `model`, and
guarded by an **asymmetric** test so the declaration cannot drift from the files
(ADR-024, as amended 2026-08-18 and corrected 2026-08-20; guard shape in
ADR-029). `user` asserts every [[Flow Chain]] entry declares
`disable-model-invocation: true`; `model` asserts no shipped step declares it. A
symmetric rule fails on `setup-matt-pocock-skills`, which declares the flag and
is not a chain entry. `mattpocock` is `user`: measured 2026-08-14, exactly its
chain entries declare the flag and the tools they reach for do not.
`superpowers` is `model`: measured 2026-08-18, none of its twelve skills
declares it. dev-ready cannot change either, because FR-16 holds vendored files
byte-identical to upstream — so this is recorded, not chosen. The [[Setup Step]]
is user-invoked in **every** flow, so a `model` flow's chain is a user-invoked
head followed by model-invoked entries, and the generated sentence says so. It
is also the first of the two axes a flow recommendation may rest on.
_Avoid_: trigger mode, auto-invoke, activation, enforcement

**Flow Selection Criteria**:
The short, ordered list of observable situations that tell a user which
[[Engineering Flow]] to pick, declared per flow in the manifest as `choose_when`
(ADR-024, as amended 2026-08-23 and 2026-08-25). Every clause must name a
manifest field the flow declares — [[Flow Invocation]], [[Flow Chain]], `steps`
— or one of that flow's steps by id, **written in backticks**: a test runs both
directions, failing a clause that names nothing and a backticked name the flow
does not declare. Claims about the reader's coding agent, the reader's team, or
upstream behaviour dev-ready does not ship are excluded permanently. One
declaration feeds the three surfaces a user meets *before* choosing: the
comparison printed above the interactive flow menu, the [[Generation Skill]]'s
interview, and `README.md`. The per-flow document is not one of them — it is
written only when its flow is already selected. Distinct from the flow's
`description`, the one-line menu label, which says what the flow *is* and never
when to pick it.
_Avoid_: flow recommendation, flow comparison, which-flow guidance, pick-this-if

**Setup Step**:
The first entry of a [[Flow Chain]] — the run-once configuration a generated
project needs before any other step. Written into every project whichever
[[Engineering Flow]] is selected, because most of what it configures belongs to
the base template rather than to the flow (ADR-026). It **explains and stops**:
it never runs a destructive command itself, and it warns only where a section
can actually destroy data rather than at the top of every run. Re-running it is
normal rather than exceptional — it reads current state and offers each section
separately, so a user may configure email alone months later.
_Avoid_: init step, bootstrap, first-run wizard, install step, setup wizard

**Setup Contribution**:
The optional extra section an [[Engineering Flow]] adds to the [[Setup Step]]. A
flow that declares none leaves the Setup Step as the shared superuser, email,
and error-reporting interview. Declared as a catalog source path on the
development-loop [[Catalog Item]]; it is overlay-interpolated and is never a
file in the generated project.
_Avoid_: setup-project snippet, setup extras, engineering_flow_setup

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

**Generation Intent**:
The resolved project name, destination, catalog selection, and Agent Targets for
one `init` or `upgrade` run. The flag adapter and the prompt adapter write the
same model (ADR-004); overlay and lifecycle commands read it.
_Avoid_: answers model, project selection (as a package name), canonical intent

**Generation Skill**:
The single skill this repository distributes for installation into a user's own
coding agent, which interviews the user about what they are building and
composes one `dev-ready init` command from the answers (FR-24, rewritten as an
interview by FR-34). It is defined by three things it is not: never a
[[Catalog Item]], never part of a generated project's overlay, and not one of
this repository's own process skills. Singular by construction — the repository
distributes exactly one, from one source path, however many channels carry it:
the cross-agent installer reaches every agent, and the Claude and Codex
[[Plugin Manifest]] files describe that same directory to two more ecosystems,
never as second copies. From v0.12 the interview also recommends an [[Engineering Flow]], which
is why no second interviewing skill may exist — two would question the user
twice.
_Avoid_: setup skill, init skill, the dev-ready skill, bootstrap skill, generate skill

**Must-Ask**:
One of the fixed set of things the [[Generation Skill]]'s interview must resolve
before it proposes a command — the only answers that can change what the command
says. An obligation to *resolve*, not to utter: one the developer has already
answered is not asked again, but every one is accounted for out loud in the
proposal, so no selection is made silently. Its opposite is a known fact, which
the skill states and never asks.
_Avoid_: required question, mandatory prompt, questionnaire item, checklist

**Enhancement**:
A Catalog Item outside the Spec Loop, optionally declaring the [[Mount Point]]
it attaches to. Everything a user can add or drop is an Enhancement.
_Avoid_: plugin, extra, addon, optional skill

**Mount Point**:
The **role** an [[Enhancement]] attaches to — `build`, `test`, or `review` —
declared as manifest data and optional; an Enhancement whose guidance has no
single right moment declares none. A role, not a skill name, because two flows
share no step names: each [[Engineering Flow]] declares which of its own steps
plays each role, and one role may resolve to **more than one** step where the
[[Flow Chain]] forks (ADR-029, amending ADR-018). A mount decides *when* an
agent is reminded, never whether it can find the skill: a [[Skill Link]] already
makes every selected skill discoverable, so a mount at the wrong step is worse
than no mount. Guidance is injected at generation time; nothing rewrites a
vendored skill at runtime (ADR-018, as amended 2026-08-03).
_Avoid_: hook, anchor, attachment point, phase, mount role

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
its marketing surface and another for its dashboard, and the two references
shipped through v0.10 are already recorded together in stamps, so single-select
would break a contract to prevent a cost only a deliberate user incurs (FR-40).
The set is **derived, not curated**: FR-40 vendors all 74 `DESIGN.md` documents
at the pinned `VoltAgent/awesome-design-md` commit, with identifiers, titles,
and descriptions produced by a maintainer script rather than typed. Because a
Design Reference is a document rather than behaviour, its Mount Point exists for
discovery alone, and a selection of them renders as one collapsed line in the
mounted skill rather than one bullet each (ADR-018, 2026-08-16). Which
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
**Retired in v0.12** by the [[Skill Link]] (ADR-028) — not because it failed,
but to follow the ecosystem convention of linking rather than restating. The
term survives to name what generated projects carried from v0.8 to v0.11, which
`upgrade` must still recognise and retire.
_Avoid_: shim, alias, symlink, mirror, proxy

**Skill Link**:
The link an [[Agent Target]]'s skills directory holds in place of content — one
per skill, pointing at that skill's [[Canonical Content]] under
`.agents/skills/`. A relative symbolic link on macOS and Linux, a junction on
Windows, because a junction is the only directory link Windows offers without
elevation. Nothing is chosen and nothing is recorded: a link is derived state,
recomputed from the stamp, so `check` reports a missing one as drift and
`upgrade` recreates it. Machine-local by design — a `.gitignore` beside the
links keeps them out of version control and acts as the ownership anchor for
safe retirement when the projection later shrinks or moves. A clone carries
Canonical Content and nothing else until `upgrade` runs. A project selecting no
Agent Target projects no Skill Links and requires no link-capable filesystem.
_Avoid_: shortcut, alias, shim, pointer, mount, delivery mode, install mode

**Agent Target Map**:
The manifest's record of each Agent Target's project-level skills directory,
derived from the reference installer's machine-readable agent list and held to
it by a drift check (ADR-019). Never a transcription — every entry is generated,
and an entry a human typed is a defect. Rules and MCP paths are absent from that
source and stay hand-declared.
_Avoid_: agent table, path map, target registry, transcription

**Standard-Compliant Agent**:
A coding agent that reads [[Canonical Content]] at `.agents/skills/` and is
therefore never an [[Agent Target]] — it needs no Skill Link and no selection.
Absence from the Agent Target Map means full support, not missing support, which
is why the selection prompt, the generation report, and the [[Generation Skill]]'s
interview all name these agents. The interview is the earliest of the three: it
runs before the CLI does, so it is where the misreading is cheapest to prevent.
_Avoid_: standard agent, generic agent, default agent, unsupported agent

### Lifecycle

**Occupied Target**:
A destination directory that already holds content when `init` runs. Accepted
from v0.13 when no top-level entry of the destination shares a name with a
top-level entry dev-ready is about to create; any collision is exit 4 and names
the colliding entries (ADR-031). It is the case a developer who has already run
`git init` is in, and it is the only case in which generation is not a single
atomic rename: entries move one at a time, each move atomic, and a failure
restores what dev-ready moved and never touches what was there first. An absent
or empty destination is not an Occupied Target and keeps the original guarantee.
_Avoid_: non-empty target, existing directory, in-place init, merge mode

**Base Provenance**:
The immutable identity of the upstream template snapshot from which a project
was originally generated. An overlay-only upgrade never changes it.
_Avoid_: current upstream pin, upgraded base

**Overlay Currency**:
How current a generated project's dev-ready-managed overlay is: the dev-ready
version, selected catalog items and their pins, and managed-file inventory.
It can advance without changing Base Provenance.
_Avoid_: project version, upstream currency

### Presentation (ADR-003)

**Static Screen**:
A screen dev-ready prints in full and does not wait on — the pre-generation
confirmation, the Engineering Flow comparison, and the generation report. From
v0.13 these three are the only surfaces `rich` renders, in one frameless idiom
of whitespace and colour. `questionary` owns every interactive prompt, and the
progress stages, `check`, `upgrade`, and error messages stay plain text. Colour
is stripped whenever `NO_COLOR` is set or stdout is not a terminal, so a Static
Screen must remain fully legible with every escape sequence removed.
_Avoid_: report screen, output panel, view, coloured output

### Distribution (ADR-027)

**Plugin Manifest**:
The file that describes dev-ready as one plugin to one agent ecosystem —
`.claude-plugin/plugin.json` for Claude Code, `.codex-plugin/plugin.json` for
Codex. It describes; it publishes nothing and reaches nobody on its own. Naming
it a storefront is the confusion ADR-027 exists to end.
_Avoid_: storefront, plugin config, plugin definition, listing

**Marketplace Catalog**:
The file that publishes plugins so a user can install one by name, fetched by
`/plugin marketplace add` and `codex plugin marketplace add`. dev-ready declares
the repository root as its own plugin's source, so one skill directory serves
every channel and no second copy exists. A catalog makes dev-ready installable
to someone who already knows its name; it does not make anyone find it.
_Avoid_: marketplace, registry, index, store

**Plugin Directory**:
The public, browsable storefront a plugin reaches only through submission and
review — Anthropic's `claude-community`, and the universal directory ChatGPT and
Codex share. This is the discovery surface FR-45 is justified by, and the only
one that reaches a user who has never heard of dev-ready. Entry is another
organization's decision on another organization's schedule, so a dev-ready
version records that it submitted, never that it was listed.
_Avoid_: marketplace, app store, catalog, storefront listing

### Written language

**Language Boundary**:
The rule fixing what language each authored surface is written in (ADR-016).
Everything dev-ready authors, emits, composes, or adapts is English — generated
content's consumer is a model, and English is what models parse most reliably.
Byte-identical vendored third-party snapshots retain their upstream language,
because translating them would break provenance; they are not a localized
surface. Chinese authored by this repository exists only in outward-facing
documentation, today `README.zh-TW.md`. dev-ready has no localized runtime and
records no language.
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
