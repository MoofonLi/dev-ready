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
cleanup. From v0.9 every generated project has one and none can decline it — it
is the single option in the mandatory Dev Category, not an unnamed constant, so
the stamp records which loop a project uses (ADR-018). Through v0.8 it shipped
as the optional catalog item `spec-loop`.
_Avoid_: spec-workflow, Pocock workflow, dev workflow, spine, backbone

**Workflow**:
Reserved exclusively for GitHub Actions workflow files (`ci.yml`, `release.yml`,
`upstream-bump.yml`). Never used for the Handoff Protocol or the Spec Loop.

### Catalog

**Category**:
The top-level axis a user selects along from v0.9: Dev, Security, Quality,
Design, Token Optimize (ADR-017). A Category cuts across Components — Design
holds both a skill and a design-doc template — and is the vocabulary prompts and
flags are expressed in. Dev is a mandatory single-select; the rest are
multi-select and may be declined. Categories are named for what they hold today,
because adding one is free and renaming one breaks every stamped project.
_Avoid_: section, block, group, component (as a user-facing word), Ops

**Component**:
An internal grouping that decides where a Catalog Item's files are written:
skills, mcp, docs. It was the user-facing selection axis through v0.8 and is not
one from v0.9 (ADR-017). A fourth, `handoff` — named `agents` through v0.7 —
generated the Handoff Protocol scaffold and is removed in v0.9 (ADR-020).
_Avoid_: agents (as a component name); using it for anything a user picks

**Catalog Item**:
An individually selectable unit, declared as data in the manifest (ADR-010) and
presented under exactly one Category.
_Avoid_: skill entry, module, addon

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
Loop. It is the only thing the size limit governs — the rest of the catalog is
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

**Bundle**:
A catalog item that materializes multiple related assets selected as one unit
because they are only valuable together, including the dependency closure those
assets need.

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
directs the agent to its [[Canonical Content]]. A stub is neither a symlink nor
a second copy of the content — generated projects must remain portable to
filesystems and platforms where symlinks are unavailable.
_Avoid_: shim, alias, symlink, mirror, proxy

**Agent Target Map**:
The manifest's transcription of every Agent Target's project-level skills
directory, derived from the reference installer's machine-readable agent list
and held to it by a drift check (ADR-019). Rules and MCP paths are absent from
that source and stay hand-declared.
_Avoid_: agent table, path map, target registry

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
