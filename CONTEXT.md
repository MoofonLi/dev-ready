# dev-ready

Domain glossary for dev-ready — a CLI that scaffolds AI-assisted-development-ready
projects from a pinned upstream template plus a curated overlay. Glossary only:
no implementation details, no specs. Decisions live in `docs/decisions/`.

## Language

### Methodology

**Handoff Protocol**:
The macro, cross-role collaboration mechanism for a multi-agent team: role
definitions, handoff sequence, review gates, and loop rules (ADR-007). Configured
as data in generated projects from v0.7 (FR-23).
_Avoid_: workflow, team workflow, agent workflow, multi-agent flow

**Protocol Configuration**:
The authoritative runtime description of a generated project's Handoff
Protocol. Agent-facing prose refers to its stable role ids; editable titles and
model assignments are read from the configuration rather than copied elsewhere.
_Avoid_: rendered role table, workflow config

**Spec Loop**:
The micro, within-session development loop one agent follows for one task:
grill → spec → tickets → TDD → review → architecture cleanup. Ships as a single
catalog item (`spec-loop`). The Handoff Protocol is the exoskeleton; the Spec
Loop is the neuromuscular system inside each role's session.
_Avoid_: spec-workflow, Pocock workflow, dev workflow

**Workflow**:
Reserved exclusively for GitHub Actions workflow files (`ci.yml`, `release.yml`,
`upstream-bump.yml`). Never used for the Handoff Protocol or the Spec Loop.

### Catalog

**Component**:
One of the four top-level overlay groups a user selects: skills, mcp, docs,
handoff (FR-3/FR-14). The `handoff` component was named `agents` through v0.7;
it always meant the Handoff Protocol scaffold, never a coding agent.
_Avoid_: agents (as a component name)

**Catalog Item**:
An individually selectable unit inside a component, declared as data in the
manifest (ADR-010). The unit of the 10-item cap.
_Avoid_: skill entry, module, addon

**Bundle**:
A catalog item that materializes multiple related assets selected as one unit
because they are only valuable together (e.g. `spec-loop`). A bundle includes
the dependency closure needed for those assets to work and counts as one item
against the cap.

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

### Internal process (ADR-013)

**Spec**:
The durable, committed record of what one FR builds and why, produced by the
Planning layer and accepted by the CEO. Code is reviewed against it, in the
phase and after.
_Avoid_: plan, PRD, 01-plan

**Ticket**:
A tracer-bullet vertical slice dispatched to one Junior session, declaring its
blocked-by edges, file footprint, and parallel-safety. A gitignored working
file with a one-phase lifespan.
_Avoid_: task, issue, 02-implementation

**File footprint**:
The set of paths a ticket is expected to create or modify; the basis for
deciding whether tickets may run in parallel.

**Gate**:
A review pass that must approve before a phase's work is committed: Senior
review (03), then QA / Security / SRE (04–06).
_Avoid_: check, audit (Security's gate is "the security review", not "an audit")
