# FR-37 — Tech Stack and Standards Source in the Generated `AGENTS.md`

Status: Accepted by Moofon (2026-08-05)

Version: v0.10

Phase: 5

Governing decisions: ADR-001, ADR-002, ADR-014, ADR-016, ADR-018, ADR-021, ADR-023

## Problem Statement

Every generated project ships a `code-review` step whose Standards axis has
nothing to read, and a set of commands that do not work.

**The Standards axis resolves to nothing.** The vendored `code-review` skill
identifies its standards sources as "anything in the repo that documents how
code should be written, such as `CODING_STANDARDS.md` or `CONTRIBUTING.md`" —
and `CONTRIBUTING.md` is in dev-ready's own prune list. The axis therefore falls
through to its built-in smell baseline in every project dev-ready has ever
generated. A grep of the whole `templates/` tree for `pytest`, `ruff` or `mypy`
returns exactly one hit: that line, asking for a file dev-ready deletes.

**The commands in `AGENTS.md` are wrong, and being wrong is worse than being
absent.** Measured against the manifest-pinned upstream commit:

- `cd frontend && npm install && npm run dev` names a package manager the
  project does not use. Upstream ships `bun.lock` and no npm lockfile, the root
  `package.json` is a Bun workspace, and `frontend`'s own `test` script is
  `bunx playwright test` — which needs Bun regardless of how the dependencies
  were installed.
- `cd backend && bash scripts/test.sh` runs `coverage run -m pytest` against a
  live PostgreSQL. On a fresh clone with nothing started it fails, and nothing
  in the file says a database is required or how to start one.
- `frontend`'s `lint` script is `biome check --write --unsafe`. An agent told to
  "run lint" to check its work gets its files rewritten with unsafe fixes
  instead.

An absent instruction makes an agent look at the repository. A wrong one makes
it act, and then report success.

**The stack the file does describe stops at the frameworks.** `## Stack` says
"React, TypeScript, Vite". It does not say Tailwind CSS, shadcn/ui, or TanStack
Query and Router, so an agent asked for a new screen has no way to know which UI
system it is writing into and will produce plausible code in the wrong one. This
is a larger practical failure than not knowing the linter's name.

**And nothing keeps any of this true.** FR-37's own premise — that a single
pinned base template (ADR-001, ADR-002) makes the stack a constant — is half
true. The pin is a constant at a moment; CI proposes a new one every Monday.
Upstream has already moved the frontend from npm to Bun and grown a *second*
backend type checker beside `mypy`. The `npm` line is not a hypothetical
regression, it is the shipped state, and it arrived exactly this way.

## Solution

The generated `AGENTS.md` becomes the project's [[Standards Source]] and its
accurate operating manual, and CI stops it from drifting back into fiction.

Four changes, all inside the one file every agent session already loads:

1. **`## Stack` is completed**, including the UI and data layers, so an agent
   knows what it is writing into before it writes.
2. **`## Commands` is completed and corrected**, so every command named is one
   that works from a fresh clone, with its prerequisites stated and its
   check-only forms preferred over its rewriting ones.
3. **A `## Standards` section declares the file the project's Standards Source**
   and states the rules no tool enforces. Naming tools is not enough on its own:
   the `code-review` skill explicitly tells the Standards axis to skip whatever
   tooling already enforces, so a list of `pytest`/`ruff`/`mypy`/`biome` is
   precisely the content that axis discards. What the axis can use is the
   guidance the template already carries in `## Development guardrails` — which
   it will now find, because the file says what it is — plus the project rules
   that exist in no configuration file.
4. **Every factual claim the file makes about upstream is drift-guarded**
   (ADR-023). A maintainer script checks each named tool and script against the
   project CI already generates against the pin, and runs as one step in that
   existing job — so the weekly upstream-bump PR passes through the guard
   automatically.

From the user's side, nothing about selection, flags, prompts, or the stamp
changes. A project generated with no Category selected gets all of it, because
`AGENTS.md` is [[Overlay Infrastructure]].

## User Stories

1. As an agent implementing a change in a generated project, I want `AGENTS.md`
   to name the test runner and how to run it, so that I can verify my own work
   instead of declaring it done.
2. As an agent running the generated `code-review` step, I want a documented
   standards source to resolve to, so that the Standards axis reports against
   this project rather than falling through to a generic smell baseline.
3. As an agent running that step, I want the standards source to contain rules
   no tool enforces, so that the axis has something to say that `ruff` and
   `biome` have not already said.
4. As an agent writing a new frontend screen, I want to know the project uses
   Tailwind CSS and shadcn/ui, so that I do not write CSS modules or a different
   component library into a codebase that uses neither.
5. As an agent writing a frontend data hook, I want to know the project uses
   TanStack Query and TanStack Router, so that I do not introduce a second
   fetching or routing library beside the one already there.
6. As an agent about to edit `frontend/src/client/`, I want to be told it is
   generated, so that I regenerate it from the backend schema instead of
   hand-editing code that the next generation will overwrite.
7. As an agent changing a SQLModel model, I want to be told a migration is
   required, so that I do not ship a schema change that breaks the next start.
8. As an agent adding a backend test, I want to know where tests live and how
   they are laid out, so that my file lands where the suite expects it.
9. As an agent running the backend suite for the first time, I want to be told a
   database must be running and how to start it, so that my first verification
   attempt is not a failure I then misdiagnose as my own change.
10. As an agent checking frontend code, I want to be given the non-rewriting
    form of the lint command, so that checking my work does not silently modify
    it.
11. As an agent type-checking the frontend, I want the type-check command named
    separately from the build, so that I can check types without producing a
    bundle.
12. As an agent installing frontend dependencies, I want to be told the project
    uses Bun, so that I do not create an npm lockfile beside the one the project
    actually keeps.
13. As an agent adding backend code, I want both type checkers named, so that I
    do not fix one and get failed by the other.
14. As a developer who has just run `dev-ready init`, I want the generated
    project to describe its own tooling, so that I can start work without
    reading three configuration files first.
15. As a developer whose CI enforces a coverage floor, I want that floor stated
    in `AGENTS.md`, so that an agent writing code for me knows tests are not
    optional.
16. As a maintainer of dev-ready, I want CI to fail when `AGENTS.md` names a
    tool the pinned upstream commit no longer has, so that a bump cannot quietly
    turn the generated documentation into fiction.
17. As a maintainer reviewing the weekly upstream-bump PR, I want the guard to
    run inside a job that PR already triggers, so that I do not have to remember
    to check anything by hand.
18. As a maintainer, I want the guard to fail when someone deletes a documented
    tool from the template while upstream still uses it, so that the file cannot
    quietly become incomplete either.
19. As a maintainer, I want the guard's comparison logic testable offline, so
    that the unit suite keeps its no-network guarantee.
20. As a maintainer, I want no version numbers in the generated stack text, so
    that the guard has a small, stable surface and the file does not carry a
    second uncontrolled copy of a dependency constraint.
21. As a maintainer, I want the guard to run against the project CI already
    generates rather than fetching upstream itself, so that the check costs one
    step and no new job.
22. As a user upgrading an existing project, I want the corrected `AGENTS.md` to
    arrive through the normal overlay lifecycle, so that an untouched file is
    replaced and an edited one is preserved and reported (ADR-014).
23. As a user who edited their `AGENTS.md`, I want `upgrade` to leave it alone
    and tell me it diverged, so that my own project notes are not destroyed by a
    documentation fix.
24. As a Traditional Chinese speaker using dev-ready, I want the generated file
    to stay English, so that the model consuming it parses it as reliably as any
    other generated content (ADR-016).

## Implementation Decisions

### The measured upstream tooling

Measured directly against the manifest-pinned upstream commit and not to be
re-derived during implementation. It is recorded here because this spec is the
durable record of the phase, and because the drift guard exists precisely so
that this list can be trusted.

- **Backend.** `pytest` with `coverage` for tests, `ruff check` for lint,
  `ruff format` for formatting, and **two** type checkers — `mypy` in strict
  mode and `ty`. Upstream's own `backend/scripts/lint.sh` runs all four;
  `backend/scripts/format.sh` runs ruff. Backend tests require a live database:
  the sequence is to start the database and mail-catcher services, run
  `prestart.sh` for migrations, then `tests-start.sh`. CI enforces a coverage
  floor of 90%.
- **Frontend.** `biome` for both lint and format, `tsc` against the build
  TypeScript configuration for types — which is `noEmit` and `strict`, so it is
  a pure check — and Playwright as the *only* test runner. There is no frontend
  unit-test runner, and the file must not imply there is one.
- **Package manager.** Bun. The root `package.json` is a Bun workspace,
  `bun.lock` is the only lockfile, and the frontend `test` script shells out to
  `bunx`.
- **UI and data layers.** Tailwind CSS with shadcn/ui — evidenced by
  `frontend/components.json`, the Radix component packages, and the
  `class-variance-authority` / `clsx` / `tailwind-merge` trio — plus TanStack
  Query, Router and Table, and `react-hook-form` with `zod`.

### The content is static template text, not derived at generation time

The stack is a constant of the pinned base template (ADR-001, ADR-002), so the
new content is ordinary template text in the rules template, alongside the
`## Stack` and `## Commands` sections that already exist. No new template token
is introduced and no new value is threaded through the renderer. Deriving the
section from upstream at generation time was rejected: ADR-002 forbids resolving
anything but the pinned commit, and a rendered file that varies with something
other than the user's selection is a file `check` and `upgrade` would then have
to reason about.

### Tool identity, never version

Every claim is stated at the granularity of a tool's identity. No version
constraint, no Python version, no Bun version appears in the generated text.
The Python version already lives in the project's own version file and the
toolchain honours it, so restating it creates a second copy with no owner, and
versions are the fastest-drifting facts in the tree. The coverage floor is
retained deliberately: it is a standard the project holds code to, not a version
number.

### `AGENTS.md` becomes the Standards Source by saying so and by carrying rules

Two moves, and the first is useless without the second.

The file declares itself the [[Standards Source]]. This is what makes the
`## Development guardrails` section the template already carries reachable by
the `code-review` Standards axis — that section has always been documented
standards; nothing said it was.

The file also states the project rules that no configuration file expresses and
no tool can enforce:

- the generated frontend API client and the generated route tree are never
  hand-edited, and are regenerated through the upstream client-generation script;
- a model change requires an Alembic migration;
- backend tests mirror the application package's layout.

These are chosen because they are true of the pinned template, they are exactly
the class of mistake an agent makes confidently, and each one is mechanically
checkable — the client directory, the route-tree file, the migrations directory
and the test package all exist in the generated tree, so the drift guard covers
them at no extra cost.

A `CODING_STANDARDS.md` stub naming what the vendored skill greps for literally
was weighed and rejected. It would guarantee resolution, but it buys a second
overlay file to keep in sync against a skill that already says "anything in the
repo", and it contradicts the location argument FR-37 itself makes: the stack
applies at every step, per-skill copies would duplicate and drift, and a
separate file is one hop an agent may not take.

### The three shipped command defects are corrected in this phase

They are not adjacent cleanups. FR-37's acceptance criterion is that an agent
can implement and verify a change, and each defect defeats it outright. They sit
in the same section of the same file this phase is already rewriting, and the
drift guard would flag the `npm` claim on its first run regardless. Correcting
them here is cheaper than recording them and correcting them later.

The corrected section names, for each side of the project: how to serve it, how
to test it *including its prerequisites*, how to check it without modifying it,
and how to format it. Where upstream provides an aggregate script, that script
is the command given and the tools behind it are named in parentheses, so an
agent can run the whole gate or reach for one tool deliberately.

### The whole-repo pre-commit gate is deliberately omitted

Upstream's pre-commit configuration survives pruning, but it references a
release-date script that dev-ready prunes. The hook's own file filter points at
a release-notes file that dev-ready also prunes, so the hook should never fire —
and "should never" is not a strong enough basis for shipping a command into
every generated project. The aggregate pre-commit command is therefore not
written into `AGENTS.md` by this phase. It may be added later by a change that
first proves it runs clean in the real-generation job.

### The drift guard is one pure function in a maintainer script

A new maintainer script sits beside the existing sync and check scripts, exposing
one function that takes a generated project directory and returns the claims that
do not hold, plus a thin command-line wrapper returning an exit code. It performs
no network access of its own.

The script holds a mapping from each claim to the upstream file where that claim
must be true. It then checks in both directions:

- every claim in the mapping must appear in the project's `AGENTS.md` — this
  catches a documented tool being quietly dropped from the template while
  upstream still uses it;
- every claim that appears in the project's `AGENTS.md` must hold in the
  upstream file the mapping names for it — this catches upstream removing or
  renaming a tool the file still advertises.

**Completeness is deliberately not checked.** An upstream *addition* that
`AGENTS.md` does not yet mention is not a failure. ADR-023 obliges stated facts
to be true; it does not oblige the file to be exhaustive, and enforcing
exhaustiveness would turn every routine upstream dependency addition into a red
build — noise, not signal, and noise is what stops a guard from being read.

The template remains the single source of truth for what the file says. The
script does not hold a copy of the prose; it holds only the claim-to-location
mapping, which is the thing a copy could not be derived from anyway.

### The guard runs in the existing real-generation job

CI's real-generation job already runs `init` against the pinned commit and
produces a complete project on disk before it builds anything. The guard is one
step added to that job, immediately after generation and before the container
build, so a failure is reported in seconds rather than after a Docker build.

This is the in-place comparison shape ADR-023 prescribes, and it applies here
because every upstream file the claims concern — the backend project file, the
frontend package file, the backend scripts, the shadcn configuration file, the
lockfile — survives pruning and is present in the generated project. FR-38's
more expensive fetch-the-pinned-commit shape is **not** to be copied: it exists
because FR-38's subject file is pruned at fetch time and is therefore never
generated at all.

### Nothing else moves

No new selectable surface, no Category change, no manifest change, no stamp
change, no new runtime dependency, and no change to any module under the
runtime package. The stamp stays at version 5, as the v0.10 plan requires.
`upgrade` behaviour follows for free from the file being ordinary overlay
content: an untouched `AGENTS.md` is replaced, an edited one is preserved and
reported (ADR-014). Assert it; do not implement it.

## Testing Decisions

A good test here asserts what a user or an agent can observe — the bytes of a
generated file, and the pass/fail verdict of the guard on a project tree. It
does not assert how the template is rendered, which template tokens exist, or
how the script walks a directory. Two seams carry all of it, and only one of
them is new.

**Seam 1 — generated content, through the existing overlay content builder.**
Assertions are made on the rendered `AGENTS.md` for a selection that takes
nothing at all, which is both the strictest case and the common one. This is the
seam every existing generated-content test already uses, including the mount
injection tests added in Phase 2 and the skill-copy tests before them; no new
seam is opened and no new helper is needed. Covered:

- the named test, lint, format and type-check commands for both backend and
  frontend survive rendering;
- both backend type checkers are named;
- the UI and data layers are named;
- the standards-source declaration is present, and at least one rule no tool
  enforces is present with it;
- the backend test prerequisite is stated;
- the check-only frontend lint form is the one named;
- no version number appears in the stack or command text;
- the whole-repo pre-commit command is absent.

**Seam 2 — the guard, through one pure function.** The function takes a project
directory and returns the failing claims, so every case is expressed as a small
tree built in `tmp_path` and a list compared against. Offline, no network, no
filesystem outside `tmp_path`. Prior art for both the seam shape and the way the
test loads a maintainer script is the existing offline test for the notices sync
check, with the agent-target derivation test as the closer analogue for a check
that also runs network-marked in CI. Covered:

- a tree that satisfies every claim returns no failures;
- a tree whose backend project file has lost a named type checker returns that
  claim and only that claim;
- a tree whose frontend package file has lost a named tool returns that claim;
- a tree missing a named upstream script returns that claim;
- an `AGENTS.md` that has dropped a mapped claim returns it, proving the reverse
  direction;
- an upstream addition the mapping does not know about returns nothing, pinning
  the deliberate decision not to enforce completeness;
- a missing `AGENTS.md` fails loudly rather than passing vacuously.

**Upgrade behaviour** is asserted at the existing upgrade seam rather than
implemented: an untouched generated `AGENTS.md` is replaced by `upgrade`, and an
edited one is preserved and reported as divergent.

The guard step in CI is not itself a pytest test; it is a script invocation in a
job that already has network. The unit suite stays offline and unchanged in that
respect.

## Out of Scope

- **Any README work.** Phase 6 owns `README.md`, `README-pypi.md` and
  `README.zh-TW.md`. This phase writes none of them.
- **Editing the vendored `code-review` skill.** It is under the byte-equality
  drift guard. The Standards axis is served by giving it something to find, not
  by changing what it looks for.
- **A `CODING_STANDARDS.md` or any second standards file.** Rejected above.
- **Per-project or per-template stack customization.** The stack is a constant
  of the single pinned base template. This becomes a real decision when FR-27
  adds a second template, and this phase is the reason it will be visible then.
- **Enforcing that `AGENTS.md` documents every tool upstream has.** The guard
  checks that stated facts are true, not that the file is exhaustive.
- **Version constraints of any kind** in the generated text.
- **The whole-repo pre-commit command**, pending proof that it runs clean in a
  generated project.
- **Fixing the stale `--yes` agent-target assertion in the real-`init` e2e test,
  and the fact that no CI job runs that file.** Found while choosing this
  phase's seams and reported in the session; it is a defect of Phase 3's landing
  and of the CI job list, not of FR-37, and folding it in here would tie this
  phase to a repair that is not its own. It is recorded so it is not lost.
- Any change to selection, flags, prompts, exit codes, the manifest, or the
  stamp.

## Further Notes

The reason this phase is worth more than its size suggests is that it closes a
class of defect rather than an instance. Before it, every fact dev-ready stated
about the upstream tree was a promise nothing kept — the `npm` line proves the
class is real and already realised. ADR-023 turns that into a standing rule with
a mechanical answer, and FR-37 is the first FR to pay for it in the same phase
that incurs it. FR-39 and FR-40 both write about upstream and will pay the same
way.

The two guard shapes ADR-023 distinguishes are worth restating once, because
choosing wrongly is invisible until it is expensive: the subject of a claim that
**survives pruning** is compared in place inside the real-generation job, and the
subject of a claim that is **pruned** must be fetched from the pinned commit
because it is never generated. FR-37 is the first case and FR-38 is the second.
The prune list decides which, not preference.

Finally, the guard's value is asymmetric in a way worth keeping in mind when it
someday fails: it will most often fail on a Monday, inside a bump PR, and the
correct response will usually be to update the generated text rather than to
reject the bump. A red build there means the guard is working.
