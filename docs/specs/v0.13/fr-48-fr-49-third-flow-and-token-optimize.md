# Phase 5 — The third Engineering Flow and a Token Optimize addition (FR-48, FR-49)

Status: **Accepted** by Moofon (2026-08-30), by dispatching `to-tickets`
against it (ADR-021).

Version: v0.13

Phase: 5

Governing decisions: **ADR-024** (Engineering Flow selection spine), as amended
through **2026-08-30** (the last announced entry goes, the machinery stays);
**ADR-029** (a flow declares its own shape), as amended **2026-08-30** (a step's
[[Step Source]] is manifest data, not its id); **ADR-008** (integration modes),
as amended **2026-08-30** (vendor mode vendors skills; commands and personas are
not an asset class). ADR-002, ADR-009, ADR-010, ADR-016, ADR-018, ADR-021,
ADR-023, ADR-026, ADR-028, and ADR-030 remain binding. **The stamp stays at
version 5.**

Source: the `grill-with-docs` session of 2026-08-30, run against
`addyosmani/agent-skills` and `ayghri/i-have-adhd` read at resolved pins before
anything was written about either. Seventeen decisions were settled there; the
four that outlive this phase are already recorded in the three ADR amendments
above and in `CONTEXT.md`'s [[Step Source]] and [[Announced Flow]] entries. The
rest are below.

---

## Problem Statement

Two problems, one phase.

**A developer cannot choose the [[Engineering Flow]] that fits their work,
because the third one does not exist.** The menu has offered `addyosmani` as
`(coming soon)` since v0.11. `--flow addyosmani` exits 2. A developer whose work
runs all the way to production — who wants security, performance, and
observability practice beside the build steps — has two flows to choose from and
neither is shaped for that. The placeholder has now survived two releases, which
is exactly the failure ADR-024 recorded when it said a menu accumulates
promises.

**A developer who selects Token Optimize gets shorter answers and cannot find
them.** The Category ships `caveman`, which compresses output, and `code-memory`,
which recalls codebase context. Both reduce token spend. Neither addresses the
complaint that a correct answer is buried in the middle of a wall of prose,
which is a different problem with the same symptom — the developer stops reading
the agent's output.

Underneath both sits a maintainer problem the third flow exposes and the first
two never could. `obra/superpowers` and `addyosmani/agent-skills` **both ship a
skill named `test-driven-development`, with different content**. dev-ready's
vendored templates root is flat and its frontmatter guard resolves a step's
files by convention from the step id, so the second upstream's file cannot be
vendored without overwriting the first's.

## Solution

`addyosmani` becomes selectable. A developer picks it from the menu or passes
`--flow addyosmani`, and receives a curated set of that pack's skills under
`.agents/skills/`, a generated `AGENTS.md` describing its own six-entry
[[Flow Chain]], a `docs/agents/addyosmani.md` explaining that chain, and a
[[Skill Link]] per skill for each selected [[Agent Target]]. The `(coming soon)`
row disappears; the menu offers three flows and no promises.

Before choosing, the developer reads three [[Flow Selection Criteria]] for each
flow — the comparison above the menu, the [[Generation Skill]]'s interview, and
`README.md` all render the same `choose_when` strings. `addyosmani`'s three say
what it is for: a written spec before code, production concerns beside the build
steps, and a chain that ends at shipping rather than at a finished branch.

Token Optimize gains `i-have-adhd`, and the Category description widens to say
what the Category now covers: `caveman` makes the answer shorter, `i-have-adhd`
keeps it findable, `code-memory` recalls context.

The collision is settled where it belongs. A step's [[Step Source]] is read from
that step's `paths` entry instead of derived from its id, and `addyosmani`'s
colliding skill is vendored under an upstream-qualified source directory with
its destination leaf unchanged. No project holds two flows, so no user ever sees
it.

## User Stories

### Choosing the third flow

1. As a developer running `dev-ready init` interactively, I want the Engineering
   Flow menu to offer three selectable flows, so that I am choosing between
   methods rather than reading an advertisement for one.
2. As that developer, I want no `(coming soon)` row anywhere in the menu, so
   that every row I can see is a row I can pick.
3. As that developer, I want the comparison above the menu to show three
   criteria for `addyosmani` in the same shape as the other two, so that I can
   compare flows on one axis rather than on three different ones.
4. As a developer whose work runs to production, I want `addyosmani`'s criteria
   to name `security-and-hardening`, `performance-optimization`, and
   `observability-and-instrumentation`, so that I can tell it apart from the
   flow that ends at a merged branch.
5. As a developer choosing between the two model-driven flows, I want the
   criteria to distinguish them by the steps they ship rather than by
   `invocation`, so that a shared invocation model does not read as a shared
   purpose.
6. As a developer running non-interactively, I want `--flow addyosmani` to
   generate a project, so that the flag agrees with the menu.
7. As a developer who read v0.12's documentation, I want `--flow addyosmani` to
   stop exiting 2 with *not yet available*, so that a message that was true
   stops being printed after it stops being true.
8. As a developer using the [[Generation Skill]], I want the skill to stop
   telling my agent that `addyosmani` cannot be selected, so that my agent does
   not refuse a flow the CLI accepts.
9. As a developer passing an unknown `--flow` id, I want the error to list three
   valid ids, so that the suggestion set matches what the tool actually offers.

### The generated `addyosmani` project

10. As a developer who selected `addyosmani`, I want `.agents/skills/` to hold
    exactly the curated set, so that what I received is what the catalog
    described.
11. As that developer, I want each vendored skill byte-identical to upstream at
    the pinned commit, so that I am reading Addy Osmani's skills and not
    dev-ready's paraphrase of them.
12. As that developer, I want the generated `AGENTS.md` to describe my flow's own
    six-entry chain and nothing about the other two flows, so that my agent
    follows one method.
13. As that developer, I want the chain sentence to say the agent starts each
    entry after a user-invoked [[Setup Step]], so that the sentence is true about
    entry zero as well as the rest.
14. As that developer, I want a [[Flow Convention]] paragraph naming where this
    flow writes its plan and task list, so that the two skills that write those
    files do not each invent a location.
15. As that developer, I want `docs/agents/addyosmani.md` to explain the chain to
    me after I have already chosen, so that the human explanation is not
    competing with the selection criteria for the same job.
16. As that developer, I want the per-flow document to say plainly which upstream
    entry points did not come with the skills, so that a reference to a slash
    command I do not have is a documented gap rather than a bug I chase.
17. As that developer, I want no [[Setup Contribution]] section added to my Setup
    Step, so that a flow with no setup interview does not grow an empty one.
18. As that developer using Claude Code, Codex, or any other selected
    [[Agent Target]], I want one [[Skill Link]] per vendored skill, so that the
    third flow reaches my agent the same way the first two do.
19. As that developer, I want the MIT notice to travel inside each vendored skill
    directory, so that the licence is present wherever the skill is.

### The developer who did not select it

20. As a developer who selected `mattpocock` or `superpowers`, I want my
    generated project byte-identical to what v0.12 produced for the same
    selection, so that adding a third flow is not a change to the other two.
21. As that developer, I want `superpowers`' `test-driven-development` unchanged,
    so that a name collision inside dev-ready's own tree does not reach my
    project.
22. As a developer running `--yes`, I want `mattpocock` to remain the
    [[Default Set]]'s flow, so that a third option does not silently move the
    default.
23. As a developer running `check` or `upgrade` on a project generated before
    this phase, I want the recorded flow to resolve exactly as it did, so that a
    catalog addition is not a lifecycle event.

### Token Optimize

24. As a developer who finds agent answers hard to act on, I want `i-have-adhd`
    offered in the Token Optimize Category, so that "the answer is buried" is a
    problem the catalog addresses.
25. As that developer, I want the Category description to say it covers output
    legibility as well as token spend, so that I can tell from the Category name
    and description whether my problem is in it.
26. As that developer, I want `--token-optimize i-have-adhd` to generate, so that
    the flag reaches the new item.
27. As that developer, I want `--token-optimize all` to include it, so that "all"
    means all.
28. As that developer, I want the [[Generation Skill]]'s Token Optimize item list
    to name `i-have-adhd` and to say it is invoked by the user rather than by the
    model, so that I do not select it and then wonder why nothing changed.
29. As that developer, I want the Category id unchanged, so that a description
    rewrite does not break a flag I have in a script.
30. As that developer, I want the whole upstream skill directory vendored, so
    that I get the skill its author published rather than a subset dev-ready
    judged sufficient.

### The maintainer

31. As a maintainer adding this flow, I want it to be a catalog entry plus assets
    with no overlay Python edit naming the id, so that Phase 4's deepening is
    the thing that made this phase cheap.
32. As a maintainer, I want the frontmatter guard to cover the third flow with no
    new test code, so that the data-driven guard is data-driven.
33. As a maintainer, I want the `choose_when` traceability guard to cover the
    third flow's criteria with no new test code, so that Phase 1 bought what it
    was cut to buy.
34. As a maintainer, I want the guard to resolve a step's files through that
    step's `paths` entry, so that a second upstream shipping a familiar skill
    name is a source directory name and not an architecture problem.
35. As a maintainer, I want the colliding skill's destination leaf to stay
    `test-driven-development`, so that dev-ready's bookkeeping is invisible in
    the generated project.
36. As a maintainer, I want the vendored-drift job to hold both new upstreams
    byte-identical, so that a silent upstream edit is caught before a release.
37. As a maintainer, I want THIRD_PARTY_NOTICES and the generated NOTICE content
    to cover both new upstreams, so that the licence obligations are discharged
    where they are checked.
38. As a maintainer, I want a test asserting no catalog item carries `status`, so
    that the retirement of the last placeholder is enforced rather than
    remembered.
39. As a maintainer, I want the announced-flow loader rule, partition, disabled
    row, and exit-2 branch to survive with fixture coverage, so that the next
    announced flow is data rather than a re-implementation.
40. As a maintainer, I want the stamp untouched at version 5, so that no project
    is migrated for a catalog addition.

## Implementation Decisions

### Pins, read before written

Both upstreams were read at resolved commits on 2026-08-30, and nothing below is
asserted from a README's marketing.

- `addyosmani/agent-skills` at `d2c37ef6225dd8726cdd369a8030307f48592d26`
  (2026-08-28). MIT, `LICENSE` present at that commit. 25 skills at
  `skills/<name>/SKILL.md`, 377,493 bytes in total. There is no
  `.claude/skills/` directory and `.opencode/skills` is a symlink to `skills/`,
  so `skills/<name>` is the vendoring source.
- `ayghri/i-have-adhd` at `cbe69fb83c08a37cf54d5ec9ec6bb88c8bc9973c`
  (2026-08-26). MIT, `LICENSE` present. The skill is `skills/i-have-adhd/`,
  holding `SKILL.md` and an `agents/` directory with two files.

Both pins are recorded in `src/dev_ready/manifest.json`'s `vendored` section
with licence and provenance (ADR-009). No other pin moves in this phase.

### The flow's declared shape

`invocation` is **`model`**, measured: none of the 25 skills declares
`disable-model-invocation`. The asymmetric guard's `model` half — no shipped step
declares the flag — passes against the curated set as-is.

The **`chain` has six entries and does not fork**. Upstream declares a lifecycle
in its own `README.md` diagram and its `AGENTS.md` "Lifecycle Mapping": DEFINE →
PLAN → BUILD → VERIFY → REVIEW → SHIP. dev-ready quotes that lifecycle; it does
not compose one. Two adjustments follow from `CONTEXT.md`'s definition of a
[[Flow Chain]] rather than from taste:

- Upstream's BUILD is a **conjunction** of `incremental-implementation` and
  `test-driven-development`, not a choice between them. A `chain` fork means a
  choice at that position, as `superpowers` has at its fourth. The two therefore
  become two sequential entries, not a fork. **This flow's chain has no fork.**
- Upstream's VERIFY is `debugging-and-error-recovery`, which runs when something
  breaks. A step reached for conditionally is a tool, not a chain entry — the
  same rule that keeps `tdd` and `code-review` out of `mattpocock`'s chain. It
  stays in `steps`.

The resulting chain: `spec-driven-development` → `planning-and-task-breakdown` →
`incremental-implementation` → `test-driven-development` →
`code-review-and-quality` → `shipping-and-launch`. [[Setup Step]] heads it and is
not a `chain` entry (ADR-026).

`roles` maps `build → [incremental-implementation]`,
`test → [test-driven-development]`, `review → [code-review-and-quality]`. Every
role the shipped mounted Enhancements name resolves for this flow, which is the
loader rule ADR-029 states in both directions.

### Curation: 20 of 25

The standard is the one applied twice already — a skill ships when it is about
building the user's project, and it ships whole or not at all. Five are
excluded, each for a stated reason and not to hit a ratio:

- **`using-agent-skills`** — a catalog naming all 24 others. Shipping it beside a
  curated subset publishes a list that is false on arrival, and its subject is
  skill discovery rather than the user's project.
- **`context-engineering`** — configures the agent's own rules files and session
  context, not the project.
- **`browser-testing-with-devtools`** — its process depends on a
  `chrome-devtools` MCP server dev-ready does not configure, so it would arrive
  inert; it also overlaps the shipped `webapp-testing` Enhancement.
- **`idea-refine`** — pre-project ideation, and `interview-me` already covers the
  DEFINE-adjacent ground this flow needs.
- **`constraint-driven-development`** — its entire mechanism is four gates keyed
  to `/build`, `/test`, `/review`, and `/ship`, which are the command layer
  ADR-008's amendment declines to vendor. A skill that *mentions* a command
  ships; a skill that *is* the commands does not.

The other twenty ship: `api-and-interface-design`, `ci-cd-and-automation`,
`code-review-and-quality`, `code-simplification`, `debugging-and-error-recovery`,
`deprecation-and-migration`, `documentation-and-adrs`,
`doubt-driven-development`, `frontend-ui-engineering`,
`git-workflow-and-versioning`, `incremental-implementation`, `interview-me`,
`observability-and-instrumentation`, `performance-optimization`,
`planning-and-task-breakdown`, `security-and-hardening`, `shipping-and-launch`,
`source-driven-development`, `spec-driven-development`,
`test-driven-development`.

Each ships whole, including supporting files inside its own directory —
`constraint-driven-development/references/` leaves with that skill, and no
shipped skill references a file outside its own directory.

**Cutting `idea-refine` removes the only executable in the pack**
(`scripts/idea-refine.sh`, mode 100755). ADR-030's executable-bit obligation
therefore does not trigger for this flow. That is stated so a reviewer looking
for the exec-bit handling finds a recorded reason for its absence.

### The [[Step Source]] collision

The loader already requires every step id to have a `paths` entry whose
destination leaf equals it. What was never data is the **source**: the codebase
resolved a step's template files by convention from the step id, which holds only
while step ids are globally unique across upstreams. They no longer are.

Per ADR-029's 2026-08-30 amendment:

- A step's template source is resolved through that step's `paths` entry — the
  entry whose destination leaf equals the step id — and the id-to-source
  convention is deleted rather than special-cased. The frontmatter guard is the
  only consumer of the old convention and is the module that changes.
- `addyosmani`'s colliding skill is vendored to an upstream-qualified source
  directory. Its destination leaf stays `test-driven-development`, so the
  generated project is unchanged in name and the shipped `SKILL.md` still
  declares `name: test-driven-development`. FR-16 compares directory contents,
  so byte-identity is unaffected by the source directory's name.
- `superpowers`' entry is not touched. Only the new flow carries a qualified
  source name, and only for the one colliding step.

Full per-flow namespacing of the templates root is the better architecture, is
recorded in the amendment as the standing next candidate, and is **not** done
here.

### Announced Flow retirement

The `addyosmani` catalog entry loses `status` and gains the full flow shape. Per
ADR-024's 2026-08-30 amendment, the **entry** is deleted and the **machinery**
stays: the loader's `status` rule and `announced_loops` partition, the catalog
model's collection, the flow prompt's disabled row, and the `--flow` exit-2
*not yet available* branch all remain, covered by their existing fixture tests.
A test asserts that no shipped catalog item carries `status`.

The [[Generation Skill]]'s paragraph telling an agent that `addyosmani` cannot be
selected is removed. The `spec-loop` rename alias and its message are untouched.
The unknown-id error's valid-id list grows to three by construction.

### Flow Selection Criteria

Three clauses, the fixed count Phase 1 pinned, each carrying at least one
backticked name resolving to this flow's own `steps` or to `invocation`, `chain`,
`steps`:

1. "Choose this flow when `spec-driven-development` should produce a written spec
   before any code exists."
2. "Choose it when the work runs to production and wants `security-and-hardening`,
   `performance-optimization`, and `observability-and-instrumentation` beside the
   build steps."
3. "Choose it when its `chain` should end at `shipping-and-launch` rather than at
   a finished branch."

`invocation` is deliberately absent from all three. Two of three flows are now
model-driven, so the axis that distinguished `superpowers` from `mattpocock`
cannot distinguish `addyosmani` from `superpowers`; the criteria rest on the
steps this flow ships instead. **`mattpocock`'s and `superpowers`' criteria are
not rewritten** — FR-50 was cut so that the third flow is a data addition on this
surface, and a third rewrite in two versions would spend that.

`description` stays a one-line menu label and never carries a situation.

### Flow Convention and Setup Contribution

`convention` is declared and points at a new asset under the overlay-only flows
root. It is one paragraph naming where this flow writes its plan and task list:
`planning-and-task-breakdown` and `spec-driven-development` both write
`tasks/plan.md` and a task list at `tasks/todo.md`, and the convention states
that so the two skills agree. It is authored dev-ready prose about vendored
content, in English (ADR-016), and is overlay-interpolated rather than copied
(ADR-029).

**No `.gitignore` change.** `tasks/plan.md` and `tasks/todo.md` are work product a
project commits, and Phase 4 put conditional root-ignore entries out of scope.

`setup_contribution` is **omitted**. The pack ships no setup skill, and omission
is how `superpowers` already expresses that.

### The per-flow document

`docs/agents/addyosmani.md` is written on the shape `mattpocock.md` and
`superpowers.md` established, copied by a `paths` entry into the generated
project's `docs/agents` exactly as theirs are. It explains the chain to someone
who has already chosen, says a flow need not complete in one session, and — per
ADR-008's amendment — states plainly that upstream's slash commands and personas
are not part of what dev-ready ships, so a reference to `/build` or to a
`code-reviewer` persona inside a vendored skill is a known gap. It is not where
selection criteria live.

### Token Optimize

`ayghri/i-have-adhd` vendors under ADR-008's vendor mode, **whole directory**:
`SKILL.md` plus its `agents/` subdirectory of two configuration files for other
agent runtimes. "Whole or not at all" is the rule, and the alternative is
dev-ready deciding which of an author's files count.

The skill declares `disable-model-invocation: true`, which `caveman` does not.
Within one Category two items therefore activate differently, and a developer who
selects it and waits for the model to apply it will wait forever. The
[[Generation Skill]]'s Token Optimize item list names it and says it is invoked
by the user. The frontmatter guard is flow-scoped and does not apply to an
Enhancement, so nothing else changes.

The Category **description** widens to cover output legibility beside token spend
and codebase recall. The Category **id** is unchanged: descriptions enter neither
the flag contract nor the stamp.

### Vendoring obligations

Both upstreams get an ADR-009 provenance entry in the manifest's `vendored`
section with repo, commit, licence, and path mappings; a THIRD_PARTY_NOTICES
section naming the licence, pinned commit, source, and vendored subset; and
FR-41 MIT notice propagation — the upstream `LICENSE` is vendored into each
vendored skill directory so it travels with the generated copy, which is the
pattern `caveman`, `mattpocock`, and `superpowers` already follow. Twenty-one
LICENSE copies result. A per-upstream single copy is a different decision and is
not made here.

### What does not change

The stamp stays at version 5 — this phase adds catalog identifiers to fields
that already hold identifiers and adds no recorded field. `--yes` still resolves
`mattpocock`. ADR-018's Default Set limit is untouched: `i-have-adhd` is an
Enhancement and is off by default. `check` and `upgrade` gain no reader. The
generation transaction (ADR-031) is not touched. No README is edited — Phase 6
owns both, and every CHANGELOG line this phase earns is Phase 6's to write.

## Testing Decisions

A good test here asserts what a developer receives for a resolved selection, what
the loader accepts or refuses, and what the CLI prints — never that a particular
Python helper ran or that a file exists on disk except as the cause of an
observable result. Two of the phase's guards are **data-driven and must gain no
new test code**: if the third flow needs a hand-written frontmatter test or a
hand-written criteria test, the guard is not data-driven and that is the finding.

Unit tests: `tmp_path`, no network. One network-marked job.

### Manifest load — `tests/unit/test_manifest.py`

Prior art: the Announced Flow materialization ban, the enhancement-forbidden loop
fields, and the existing `addyosmani` announced-entry case at `:220`, which is
retired rather than kept.

- the shipped manifest loads with three development loops and one new
  token-optimize Enhancement;
- **no catalog item carries `status`**, asserted over the whole catalog;
- `announced_loops` is empty for the shipped manifest, and the announced-flow
  rules still reject a malformed fixture entry in both directions — a `status`
  value other than `coming-soon`, and an announced entry declaring materialized
  content;
- every role `addyosmani` declares resolves to steps it ships, and every role a
  mounted Enhancement names is declared by all three flows;
- every declared step has a `paths` entry whose destination leaf equals it,
  including the qualified-source step.

### The flow frontmatter guard — `tests/unit/test_flow_frontmatter.py`

The module that changes. Its step-to-source resolution moves from the id
convention to a `paths` lookup, and the shipped-manifest test then covers the
third flow with **no new case**.

- the existing shipped-manifest test passes unchanged in intent across all three
  flows;
- a fixture flow whose colliding step declares a qualified source is resolved
  through `paths`, proving the guard reads data rather than a convention;
- a fixture flow declaring a step whose `paths` source does not exist fails
  loudly, so a typo is caught by the guard rather than by a user;
- the asymmetric halves keep their existing fixture coverage: `user` asserts
  chain entries declare the flag, `model` asserts no shipped step does.

### Flow Selection Criteria — `tests/unit/test_flow_selection_criteria.py`

No new test code. The shipped-manifest test already runs both directions over
every declared flow and already asserts the fixed count of three. Its passing
with `addyosmani` present is the phase's evidence that Phase 1 bought what it was
cut to buy.

### CLI and flags — `tests/unit/test_cli.py`

Prior art: the `(("--flow", "addyosmani"), "not yet available")` case at `:682`,
which inverts.

- `--flow addyosmani` generates instead of exiting 2;
- an unknown `--flow` id lists three valid ids;
- `--flow spec-loop` still exits 2 with the rename message;
- `--token-optimize i-have-adhd` generates;
- `--token-optimize all` resolves to a set containing it;
- `--yes` still resolves `mattpocock` and still produces a project with no
  Enhancement.

### Selection prompts — `tests/unit/test_prompts.py`

- the flow menu offers three selectable rows and passes no disabled choices,
  since `announced_loops` is empty;
- the disabled-row rendering still works when a fixture catalog does declare an
  announced flow, which is the fixture coverage ADR-024's amendment relies on.

### Overlay content — `tests/unit/test_overlay.py`

The highest seam, and the one Phase 4 established for exactly this.

- an `addyosmani` selection produces an `AGENTS.md` Engineering Flow section
  carrying the six chain entries in order, no fork, and the model-invocation
  sentence with its user-invoked head;
- its [[Flow Convention]] paragraph is present and names the plan and task-list
  locations;
- its Setup Step gains no flow section;
- `mattpocock` and `superpowers` overlay bytes are unchanged for a fixed
  selection — the regression that matters most, since the collision fix touches
  shared machinery.

### Generation Skill sync — `tests/unit/test_generate_skill.py`

Prior art: the assertion at `:288` that the skill states `addyosmani` is not yet
available, which is retired, and Phase 1's assertions that repeated strings
resolve to the manifest's.

- the skill's flow criteria for all three flows resolve to the manifest's
  `choose_when`;
- the skill no longer contains the announced-flow paragraph or the
  *not yet available* message;
- the skill's valid-flow-id list matches the catalog's selectable loops;
- the Token Optimize item list names `i-have-adhd` and states it is user-invoked;
- the Category description in the skill matches the manifest's.

### Vendoring and notices

- `tests/unit/test_sync_vendored.py` — the path mappings build for both new pins,
  including the qualified source, offline against fixtures;
- `tests/unit/test_notices_sync.py` — THIRD_PARTY_NOTICES covers every entry in
  the manifest's `vendored` section, which fails until both new sections exist;
- `tests/unit/test_line_endings.py` and the [[Skill Link]] tests cover the new
  directories by construction;
- the **network-marked `vendored-drift` job** holds both new upstreams
  byte-identical at their pins. It is the only network test this phase adds and
  is deselected by default.

### What is not a seam

No test asserts a Python helper is absent. No test for the stamp — nothing
recorded changed. `check` and `upgrade` gain no case: they resolve a recorded
flow through machinery this phase does not touch, and the existing lifecycle
tests are the specification of that. No test of upstream's own content beyond
byte-identity — dev-ready does not assert what a vendored skill says.

## Out of Scope

- **Any README change**, English or Chinese, and every CHANGELOG line. Phase 6
  owns all of it, including the entry recording the third flow, the retirement of
  the last `(coming soon)` row, and the widened Category description.
- **`headroomlabs-ai/headroom`.** It failed two of five gate conditions on
  2026-08-12 — it writes outside the project and its outbound telemetry defaults
  on — and remains a recorded candidate. A phase that finds itself adding it has
  strayed.
- **Vendoring upstream's slash commands, personas, subagent definitions, hooks,
  or plugin manifests.** ADR-008's 2026-08-30 amendment declines the asset class;
  adding one is a decision on its own evidence.
- **Editing vendored content to remove references to those missing entry
  points.** FR-16 holds vendored files byte-identical. The residue is documented,
  not patched.
- **Per-flow namespacing of the whole templates root.** Recorded in ADR-029's
  amendment as the next architecture candidate; this phase qualifies one source
  directory.
- **Deleting the Announced Flow machinery.** Explicitly kept by ADR-024's
  amendment.
- **Rewriting `mattpocock`'s or `superpowers`' `description` or `choose_when`.**
- **Reopening ADR-018's Default Set limit.** `i-have-adhd` is off by default.
- **A stamp version bump**, and any recording of a new field.
- **Generation transaction work** (ADR-031). Phase 3 owns it and this phase must
  not touch it.
- **A per-upstream single LICENSE copy** in place of the per-skill-directory
  pattern.

## Further Notes

**Three ADR amendments were written before this spec** and are the durable record
of what the grilling settled: ADR-029 (a step's [[Step Source]] is manifest data),
ADR-024 (the last announced entry goes, the machinery stays), and ADR-008 (vendor
mode vendors skills). `CONTEXT.md` gained [[Step Source]] and amended
[[Announced Flow]]. No new ADR: each finding belongs to an existing decision's
owner, and a fourth record spanning all three would overlap them.

**This is the widest phase in v0.13** — 21 vendored directories, a guard
refactor, a catalog retirement, and a second upstream. If it needs splitting, the
seam is between the collision fix plus the flow (FR-48) and the Token Optimize
addition (FR-49); they share no module and FR-49 is independently shippable.

**The chain is upstream's, quoted.** If a reviewer disagrees with the six
entries, the disagreement is with `addyosmani/agent-skills`' own `README.md` and
`AGENTS.md` at the pinned commit, not with a dev-ready composition. The two
adjustments — BUILD as two sequential entries rather than a fork, and VERIFY as a
tool rather than a chain entry — are applications of `CONTEXT.md`'s
[[Flow Chain]] definition and are the only places dev-ready's reading departs
from upstream's diagram.

**A phase that finds itself proposing stamp version 6 has discovered something
the version plan got wrong and must stop and say so.**

## Acceptance

- `--flow addyosmani` generates a project whose `.agents/skills/` holds exactly
  the twenty curated skills, each byte-identical to upstream at the pin;
- the interactive flow menu offers three selectable flows and no `(coming soon)`
  row;
- no shipped catalog item carries `status`, asserted by test, while the
  announced-flow machinery keeps its fixture coverage;
- the third flow's `choose_when` passes Phase 1's guard with no new test code,
  and the frontmatter guard covers it with no new test code;
- the frontmatter guard resolves a step's files through `paths`, and both
  `test-driven-development` skills coexist in the templates tree;
- `mattpocock` and `superpowers` generated output is byte-identical to v0.12 for
  a fixed selection;
- `docs/agents/addyosmani.md` reaches a generated project that selected the flow,
  and no other;
- `--token-optimize i-have-adhd` generates and `--token-optimize all` includes
  it, with the whole upstream skill directory present;
- THIRD_PARTY_NOTICES and the generated NOTICE content cover both new upstreams;
- the stamp is untouched at version 5;
- the full suite passes, and the network-marked `vendored-drift` job passes
  against both new pins.
