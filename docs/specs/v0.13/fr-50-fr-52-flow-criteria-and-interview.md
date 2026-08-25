# FR-50 & FR-52 — Flow Selection Criteria, and the interview that uses them

Status: **Accepted** by Moofon (2026-08-25), by dispatching `to-tickets`
against it (ADR-021).

Version: v0.13

Phase: 1 (the whole phase; FR-50 and FR-52 are its only requirements)

Governing decisions: **ADR-024** (the [[Engineering Flow]] is the user-facing
selection spine), as amended 2026-08-13, amended 2026-08-18, **corrected
2026-08-20**, amended 2026-08-23 (the two-axis whitelist becomes a traceability
rule and the criteria get their own field), and amended **2026-08-25** (a name
is written in backticks and the guard runs in both directions); and **ADR-023**
(upstream facts under a pinned-commit drift guard), as amended 2026-08-23 (the
subject of the guard is the claim, not its destination). ADR-002 (pinned
generation), ADR-010 (item-level selection), ADR-011 (canonical paths), ADR-016
(English authored surfaces), ADR-017 (Category-first selection), ADR-018 (the
[[Default Set]] and the [[Mount Point]]), ADR-019 (the offline-fixture guard
pattern), ADR-021 (the Spec Loop), ADR-026 (`setup-project` is unconditional
infrastructure), ADR-027 (the repository root is the plugin), ADR-029 (a flow
declares its own shape), and ADR-030 remain binding. ADR-025 is superseded and
implements nothing.

Source: the `grill-with-docs` session of 2026-08-25, run against the shipped
v0.12.0 manifest, `skills/dev-ready/SKILL.md`, and the tests that hold them.
Ten decisions were settled there; the two that outlive this phase are already
recorded (ADR-024's 2026-08-25 amendment, and `CONTEXT.md`'s
[[Flow Selection Criteria]] and [[Must-Ask]] entries). The remaining eight are
below.

---

## Problem Statement

Two of the five complaints in the 2026-08-22 field report land here. Both are
cases of a user receiving the *wrong* thing rather than an unpolished one, and
both were repaired once already by the version that shipped them.

**The flow choice is unmakeable.** The CEO ran v0.12.0 end to end, selected an
[[Engineering Flow]], and afterwards could not tell which one he should have
picked. That is precisely the defect FR-47's recommendation was created to
prevent, surviving the version that shipped it. Two causes, both in ADR-024's
instrument rather than its purpose:

- The two-axis whitelist **rejects true, guarded sentences**. "It ships a step
  that verifies before it can claim to be done" names
  `verification-before-completion` — a `superpowers` step listed in `steps`,
  written to a declared path, held byte-identical to the pin by
  `vendored-drift`. Excluded. "Use it when the shape of the work is still
  unclear" names `grill-with-docs`, `grilling`, and `domain-modeling`, all
  `mattpocock` steps under the same guard. Excluded. Meanwhile the whitelist has
  no opinion at all on "your agent is weaker, so pick this one", which names
  nothing dev-ready ships and cannot be checked even in principle.
- The criteria were put in `description` — the single string
  `prompts/collect.py:212` renders as one menu row. A list of observable
  situations does not fit one row, which is why the shipped sentences describe
  mechanism instead of fit.

**The interview is a questionnaire.** The same run produced a fixed set of
questions, not an interview. It asked the developer what stack they were
building on, proposed a command, and then asked whether the frontend was React.
Every dev-ready project is FastAPI + React + PostgreSQL + Docker Compose,
because the base template is pinned — so the first question has no answer that
changes anything and the third has exactly one. It never asked the project's
name, never asked where the project should go, and never asked which design
language to reference: it silently resolved `frontend-design` out of 74
[[Design Reference]] entries and disclosed the choice only afterwards.

The cause is on disk. `skills/dev-ready/SKILL.md` never states the fixed stack,
and its Interview section (`:10-16`) bounds the *number* of follow-ups without
naming a single thing they must resolve, so an agent with no criteria falls back
to a generic questionnaire. `:47` instructs the agent to *choose* a project name
and says nothing about where the project goes. `:85` gives `react-doctor` and
`webapp-testing` triggers that read as conditions on having a React frontend —
a condition that is always true.

**Why these two are one phase.** FR-52's interview must ask which Engineering
Flow to use, and the text it asks with is FR-50's `choose_when`. Shipped alone,
FR-52 writes that question against the v0.12 descriptions — the exact strings
FR-50 exists to replace — and rewrites it one phase later. Both also land on the
same file, and both are mostly authored text under new tests rather than deep
code.

Two further problems were found while grilling this phase and are repaired here
because the change that exposes them is this one:

- **The guard as specified runs one way.** ADR-024's 2026-08-23 amendment
  describes a test that resolves the step ids *appearing* in a flow's criteria.
  A clause naming nothing appears nowhere in that rule, so the sentence the same
  amendment excludes by name would pass it. Settled and recorded as ADR-024's
  2026-08-25 amendment.
- **`description` has four hand-written copies and the phase plan names none of
  them.** `README.md:30-32` and `:77-78`, `README-pypi.md:23-26`, and
  `docs/plugin-directory-submission.md:77` each restate it; two tests pin the
  strings (`tests/unit/test_manifest.py:1631`,
  `tests/unit/test_generate_skill.py:389-393`). `README-pypi.md` is owned by no
  phase in v0.13 at all — FR-54 names only `README.md` and `README.zh-TW.md`.

## Solution

A development-loop catalog entry declares **`choose_when`**: an ordered list of
short criteria, each naming — in backticks — a manifest field that flow declares
or one of that flow's own steps. `description` keeps its place as the one-line
menu label and changes its job: it says what the flow **is** and never when to
pick it. One declaration feeds every surface that repeats it, and a table-driven
test holds each surface to the manifest's exact string.

The Generation Skill stops asking what it already knows and starts asking what
it cannot know. The fixed stack becomes a **stated known fact** under ADR-023's
guard — checked in place against the generated tree at the pinned commit — and a
fixed set of seven [[Must-Ask]] items replaces the open-ended "at most three
follow-ups". A Must-Ask is an obligation to *resolve*, not to utter: one the
developer has already answered is not asked again, but every one is accounted
for out loud in the proposed command, so no selection is made silently again.

The design question, the sharpest miss in the report, becomes two independent
open sub-questions matching the two things the manifest actually holds — a
methodology skill and a set of reference documents — and a product name the
catalog does not carry is said out loud rather than resolved to a near miss.

## User Stories

1. As a developer choosing an Engineering Flow, I want each flow to tell me the
   situations it is for, so that I can pick one without having already used both.
2. As a developer choosing an Engineering Flow, I want those situations to point
   at something the tool actually installs, so that the advice is checkable
   rather than marketing.
3. As a developer choosing an Engineering Flow, I want each flow's criteria to be
   the same shape and the same count, so that I am comparing like with like.
4. As a developer reading the flow menu, I want each row to tell me what the flow
   *is* in one line, so that a long list of situations does not have to fit in a
   terminal row.
5. As a developer, I want the criteria I read in the Generation Skill to be the
   same words the CLI would show me, so that switching between them does not
   change the advice.
6. As a developer, I never want dev-ready to tell me my coding agent is weak, so
   that the tool is describing itself rather than judging my setup.
7. As a developer, I do not want to read a description of an Engineering Flow
   that has not shipped, so that the menu is not making promises.
8. As a dev-ready maintainer, I want a criteria clause that names a step the flow
   does not ship to fail the build, so that a rename cannot leave prose behind.
9. As a dev-ready maintainer, I want a criteria clause that names nothing at all
   to fail the build, so that the rule I recorded is the rule that runs.
10. As a dev-ready maintainer, I want an upstream pin bump that touches a step
    named in a flow's criteria to force me to re-read that step, so that the
    guard holds meaning and not only bytes.
11. As a dev-ready maintainer, I want every hand-written copy of a flow's
    `description` to be pinned to the manifest by a test, so that four surfaces
    cannot drift apart the way they already did.
12. As a dev-ready maintainer, I want a manifest that declares a flow with no
    criteria to fail to load, so that a flow cannot ship unchoosable.
13. As a dev-ready maintainer, I want an [[Announced Flow]] that declares
    criteria to fail to load, so that the menu does not describe something a user
    cannot select.
14. As a developer talking to a coding agent, I want it to tell me the stack
    rather than ask me, so that I am not answering a question with one answer.
15. As a developer talking to a coding agent, I want it to know my project has a
    React frontend, so that it does not ask me to confirm the only possibility.
16. As a dev-ready maintainer, I want the stated stack to be checked against a
    real generated project at the pinned commit, so that an upstream change
    cannot make the Generation Skill lie.
17. As a developer, I want to be asked what to call my project, so that the agent
    does not name it for me.
18. As a developer, I want to be asked where the project should go, so that it
    does not land somewhere I did not choose.
19. As a developer, I want both the name and the destination repeated back in the
    proposed command, so that I can see them before anything is created.
20. As a developer who handles payments or personal data, I want to be asked
    about that directly, so that `security-audit` is offered rather than guessed.
21. As a developer who wants React health checks or browser-level tests, I want
    to be asked, so that `react-doctor` and `webapp-testing` are reachable
    through the interview.
22. As a developer who wants neither, I want them left out by default, so that a
    lean project stays lean.
23. As a developer who cares about the interface, I want to be asked how polished
    it should be, so that `frontend-design` is a choice rather than a default.
24. As a developer with a product in mind, I want to be asked which product's
    design language to reference, so that one of 74 references is picked by me.
25. As a developer who names a product dev-ready does not carry, I want to be
    told so out loud, so that I am not silently given a different one.
26. As a developer who describes an aesthetic without naming a product, I want to
    be offered candidates rather than assigned one, so that the match is mine.
27. As a developer who wants neither a methodology skill nor a reference, I want
    both to be declinable independently, so that the two are not bundled.
28. As a developer who cares about context use, I want to be asked, so that
    `caveman` and `code-memory` are reachable through the interview.
29. As a developer, I want every selection in the proposed command traced back to
    something I said, so that nothing is chosen silently the way
    `frontend-design` was.
30. As a developer who already described the project in one breath, I do not want
    to be re-asked what I just said, so that the interview is not a form.
31. As an agent running the Generation Skill, I want a fixed list of what must be
    resolved, so that I do not fall back to a generic questionnaire.
32. As an agent running the Generation Skill, I want the flow criteria in the
    same section I use to map words to ids, so that I am not matching against a
    label 60 lines from the criteria.
33. As a dev-ready maintainer, I want the cross-release gate to install the
    actual previous release, so that the lifecycle it proves is the one users
    will run.
34. As a reviewer, I want the phase's whole file footprint declared, including
    the copies of `description` the phase plan did not name, so that the review
    is against what actually changed.

## Implementation Decisions

### The N-1 baseline advances first, as its own unit of work

`tests/e2e/test_upgrade_from_release.py`'s `_RELEASED_VERSION` moves from
`0.11.0` to `0.12.0`. It stays one explicit reviewed constant — never a local
build, never a "latest" resolution. Its prerequisite is that `dev-ready 0.12.0`
is tagged and published to PyPI, which the v0.13 plan records as confirmed on
2026-08-22. This lands before anything else in the phase so that a failure here
is attributable to the baseline rather than to the phase's own changes.

VERIFY-AT-IMPLEMENTATION: confirm `dev-ready 0.12.0` resolves from PyPI before
changing the constant. If it does not, stop and report — do not substitute a
local build.

### `choose_when` is manifest data on a development-loop entry

A development-loop catalog entry declares `choose_when` beside `description`: an
ordered list of short, non-empty strings. It is parsed in
`src/dev_ready/manifest/loader.py` and surfaced on `CatalogItem` in
`src/dev_ready/manifest/models.py` as an immutable tuple, in declaration order.

Loader rules, mirroring the shape `steps` already has:

- **Required and non-empty for every declared development loop.** A loop
  declaring no `choose_when`, an empty list, a non-list, or a list containing a
  non-string or an empty string is a `ManifestError`.
- **Forbidden on an [[Announced Flow]].** An entry carrying `status` is
  partitioned out before it is parsed as a loop (ADR-024's 2026-08-13
  amendment); declaring `choose_when` on one is a `ManifestError`, in the same
  shape as the existing rejection of `paths` on an announced entry. An announced
  flow cannot help anyone choose, because it cannot be chosen.
- **Forbidden on an [[Enhancement]].** Same shape as the existing rejection of
  `steps` on a non-loop.

`choose_when` is never written into a project's stamp — it is catalog data a
user reads before choosing, not a record of what they chose. **The stamp stays
at version 5**, as the v0.13 plan requires: this adds no
recorded field, removes none, and re-types none.

### Every clause names something, in backticks, and the guard runs both ways

This is ADR-024's 2026-08-25 amendment, restated as the rule the phase builds.

A clause satisfies the guard when **it contains at least one backticked token**
and **every backticked token in it resolves** either to one of that flow's own
declared `steps` or to one of the literal field names `invocation`, `chain`,
`steps`. A clause with no backticked token fails; a clause whose backticked token
is not one of that flow's steps fails.

Backticks are the naming signal because bare-token matching cannot be trusted in
both directions: `implement` is both a `mattpocock` step id and an ordinary
English verb, so a clause using the verb would resolve to a step it does not
mean — a false pass, which is the failure direction that matters.

**Every declared flow carries the same number of clauses.** The guard asserts
it. This is a decision made in writing this spec rather than in the grilling
session, and it exists for one reason: Phase 2 prints the criteria as a
side-by-side comparison, and a comparison whose columns have different lengths
is a rendering special case bought for nothing. Phase 1 sets the number at
**three**. FR-48 inherits it when it authors `addyosmani`'s criteria. If Moofon
would rather leave the count free, striking this paragraph costs one assertion
and hands Phase 2 the special case.

Two exclusions are permanent and a reviewer rejects them on sight: **anything
about the reader's own coding agent or team**, and **anything about
`addyosmani`**, which no phase before Phase 5 has read.

### `description` says what the flow is, never when to pick it

Both shipped descriptions are rewritten. They stop being selection advice
addressed to the reader ("You start each step yourself…") and become one-line
statements of what the flow is — user-driven or agent-driven, single-session or
fanned out across subagents. The rewritten strings are authored at
implementation; the rule is what this spec fixes.

This is a user-visible change to shipped strings, for the second time in two
versions, and belongs in Phase 6's CHANGELOG.

`prompts/collect.py:212` continues to render `"{display_name} — {description}"`
as one row per flow, unchanged. **Phase 1 does not touch the interactive
prompt** — Phase 2 owns every CLI screen, including the comparison panel printed
above this menu.

### Every repeated copy is table-driven and byte-exact

A single data-driven test holds every surface that restates a flow's
`description` or `choose_when` to the manifest's exact string. The table is the
guard; adding a surface is adding a row.

| surface | field | lands |
|---|---|---|
| `skills/dev-ready/SKILL.md` | `description` and `choose_when` | Phase 1 |
| `README.md` | `description` (two places) | Phase 1 |
| `README-pypi.md` | `description` | Phase 1 |
| `docs/plugin-directory-submission.md` | one `choose_when` clause | Phase 1 |
| the terminal flow comparison | `choose_when` | Phase 2 |
| `README.md` flow comparison | `choose_when` | Phase 6 (FR-54) |

**Comparison is verbatim substring containment, with no normaliser.** A
normaliser is a second place where "close enough" is defined, and it has no
guard of its own; a surface that must quote the string exactly cannot drift by
rewording. This has one consequence the phase pays for: `README-pypi.md:23-26`
currently embeds the descriptions *rewritten* — lower-cased, de-punctuated,
reflowed inside parentheses — so that bullet is restructured to quote them
directly.

`README.md` is edited **only at `:30-32` and `:77-78`**, and only the strings.
No structure, no headings, no other section. This narrows the v0.13 plan's "no
earlier phase edits a README" rule to what it was protecting — the two files
FR-54 rewrites, and there only against a *rewrite*, not against a string fix.
`README-pypi.md` needed the narrowing regardless: FR-54 names only `README.md`
and `README.zh-TW.md`, so no phase in v0.13 owns it.

`docs/plugin-directory-submission.md:77` currently calls `description` "the
`superpowers` Engineering Flow **criterion**". Criteria are now `choose_when`'s
job, so that sentence quotes a `choose_when` clause instead, and
`tests/unit/test_generate_skill.py:389-393` follows it.

`README.zh-TW.md` is untouched. No product fact it states changes here
(ADR-016).

`docs/cli-spec.md` is untouched: it names flow ids and never restates a
description.

### The Generation Skill states its known facts

`skills/dev-ready/SKILL.md` gains a block of facts that are **declared and never
asked**:

- Every dev-ready project is **FastAPI + React + PostgreSQL + Docker Compose**.
- Every project has a frontend.
- The frontend is React.

Claims are stated at tool-identity granularity and never at version granularity,
per ADR-023's third rule.

### The stack claim is guarded in place, by the script that already does this

ADR-023's 2026-08-23 amendment makes the subject of the guard the claim rather
than its destination, which brings an authored file in this repository inside a
guard written for generated projects. `scripts/check_stack_facts.py` already has
the exact shape needed — a claim record pairing a claim file, the claim's
needles, and the upstream evidence that keeps it true — and `STACK_FACTS`
already maps all four tokens to upstream subjects that survive pruning
(`backend/pyproject.toml` for FastAPI and `psycopg`, `frontend/package.json` for
React, `compose.yml` for Docker Compose).

The one gap is that every claim path it resolves is relative to the *generated
project*. The script gains a notion of which root a claim path resolves against
— the generated project, or the repository — and a repository root it can
default from its own location. Upstream evidence paths stay project-relative and
unchanged. **The CI invocation does not change**: `generate-and-verify` already
runs the script from the repository checkout against `demo-app`, so the
comparison stays in place, with no fetch, no upstream fixture, and no new job,
exactly as ADR-023's first rule requires.

A second script was considered and rejected: two near-identical comparison
engines is the second-source failure this repository keeps paying for. A
network-marked pytest that generates its own tree was rejected because ADR-023's
first rule names the tree `generate-and-verify` already builds.

VERIFY-AT-IMPLEMENTATION: confirm each stack clause's subject is present in a
real generated tree at the current pin before the claim is written —
`frontend/package.json` declaring `react`, `backend/pyproject.toml` declaring
`fastapi` and `psycopg`, and the compose files. Resolve the exact needles
against the tree, not against the manifest.

### Seven Must-Asks, and what a Must-Ask means

The Interview section (`:10-16`) is rewritten as known facts plus a fixed list.
A **[[Must-Ask]]** is an obligation to resolve, not to utter: one the developer
has already answered in their own words is not asked again, but **every one is
accounted for out loud in the proposal**. The existing "if the developer already
described the project and agent choices, do not ask them to repeat that
information" rule stays and now governs the list. That is what keeps this a
fixed list of *obligations* rather than the fixed questionnaire the same section
currently forbids.

The seven, in the order the interview resolves them:

1. **Project name and destination** — never asked at all today.
2. **How much the developer wants to steer** → the [[Engineering Flow]], quoting
   the flow's `choose_when` clauses verbatim.
3. **Whether the project handles accounts, payments, or personal data** →
   `security-audit`.
4. **Whether automated React health checks or browser-level tests are wanted** →
   `react-doctor`, `webapp-testing`.
5. **Interface ambition, and which product's design language to reference** →
   `frontend-design` and a `design-<id>`, as two independent sub-questions.
6. **Whether context-saving behaviour is wanted** → `caveman`, `code-memory`.
7. **Which coding agents are in use** → `--agents`, resolved against the Agent
   Target and standard-compliant lists as today.

Items 4 and 6 are additions to the list the v0.13 plan wrote. The plan listed
five while separately requiring `react-doctor` and `webapp-testing` to become
Must-Asks, and dropped Token Optimize entirely although `:16-17` asks for it
today. Left as written, four Enhancements — `react-doctor`, `webapp-testing`,
`caveman`, `code-memory` — become unreachable through the interview, and FR-49
is about to add more Token Optimize items to a Category nobody asks about.
Settled in the grilling session of 2026-08-25.

Completed, the list is one item per optional Category plus the flow, the
destination, and the agents — the same walk ADR-024 fixed for the interactive
prompt, arriving at the other surface.

### The design question is two questions, and never a silent match

The manifest holds two different things here, in two different components:
`frontend-design` is a methodology skill in `skills` (how to build good frontend
UI, vendored from `anthropics/skills`), and the 74 `design-*` entries are
reference documents in `docs` (what good design systems look like, vendored from
`VoltAgent/awesome-design-md`). The manifest's own description says so. Binding
them is the shape of the v0.12.0 defect.

- **Interface ambition** is asked on its own and governs `frontend-design`.
- **Which product's design language to reference** is asked on its own and
  governs a `design-<id>`.
- All four combinations are legal. Neither answer implies the other.

**Matching is by product name the developer states.** An aesthetic described
without naming a product is not a match: the agent says so, may offer a few
named candidates for the developer to choose between, and never chooses one
itself. This is the same rule `SKILL.md` already applies to agent identifiers —
"do not guess a near-miss identifier" — applied to the surface where guessing
actually happened.

When nothing matches, the skill says "no matching Design Reference" out loud.
It does not downgrade to `frontend-design` in silence, and it does not treat the
absence of a reference as a reason to drop the ambition answer.

### `react-doctor` and `webapp-testing` stop being conditional

Their triggers at `:85` currently read as conditions on having a React frontend,
which is now a stated known fact and therefore always true. The condition is
removed from both trigger lines; they are offered on that stated ground as
Must-Ask 4.

**They stay off by default.** ADR-018's [[Default Set]] limit is not reopened —
it was considered for exactly these two items and declined (version plan,
2026-08-23). A phase that finds itself adding an Enhancement to the Default Set
has strayed into a decision already made.

### The destination is asked, not chosen

`:47` currently instructs the agent to *choose* a valid project name and says
nothing about where the project goes. It becomes: ask the developer for both the
name and the destination, and repeat both in the proposed command.

**The safety rules at `:49` do not change in this phase.** Until FR-53 ships in
Phase 3, a non-empty destination really is refused, and the skill must keep
saying so. A skill that promises Phase 3's behaviour before Phase 3 exists is
the same defect class as a description of an unshipped flow.

### `choose_when` renders in the trigger list, once

In `skills/dev-ready/SKILL.md`, each flow keeps its existing one-line entry in
`### Engineering Flows` — `` - `id`: <description> `` — and gains **indented
sub-bullets, one per `choose_when` clause, verbatim**. Must-Ask 2 in the
Interview section points at that section rather than restating the clauses.

One copy, one location, and both jobs the section has: the label a reader sees
and the criteria an agent matches words against. The existing id-extraction
regex anchors on `^- `, so indented sub-bullets are invisible to it and every
current assertion in `test_generate_skill.py` keeps working unchanged.

Putting the clauses only in the Interview section was rejected: the trigger list
is the part of the file that maps a developer's words to an id, and stripping it
back to a bare label removes exactly that capability. Putting them in both
places was rejected as a second hand-written copy inside one file — the failure
ADR-024's single-declaration rule exists to end.

## Testing Decisions

A good test here asserts what a developer or an agent can observe: a manifest
that loads or does not, a string that appears in a file a user reads, a rule
that fails the build. None of these tests reach into how the loader is
structured or how the skill file is parsed internally.

**Prior art is followed rather than invented.** All but one seam already exists.

### The traceability guard — the one new seam

New file `tests/unit/test_flow_selection_criteria.py`, built in the shape of
`tests/unit/test_flow_frontmatter.py`, which solves the same problem one field
over: a **pure checking function taking a `CatalogItem`**, exercised against the
real manifest and against synthetic `CatalogItem`s for the failure directions.
Keeping the function in the test module matches that prior art exactly.

Cases:

- every declared flow in the bundled manifest passes;
- a synthetic flow whose clause names a step it does not declare fails;
- a synthetic flow whose clause carries no backticked token at all fails;
- a synthetic flow naming `invocation`, `chain`, or `steps` passes;
- flows declaring different numbers of clauses fail.

The guard runs over the real manifest, so a pin bump that renames a step named
in a criteria clause fails the build rather than leaving prose behind.

### Loader rules — existing seam

`tests/unit/test_manifest.py`, via `parse_manifest(json.dumps(data))` over a
mutated copy of the module's `VALID` fixture, exactly as the announced-flow
rules are tested today. `VALID`'s `sample-skill` loop gains a `choose_when` so
the fixture stays valid; every test that reuses it is unaffected by anything
else. Cases: missing, empty list, non-list, non-string member, empty-string
member, declared on an announced entry, declared on an Enhancement, and one
positive case asserting order is preserved onto `CatalogItem`.

`test_default_manifest_loads_superpowers_declarations` and its `mattpocock`
counterpart gain `choose_when` assertions and follow the rewritten
`description`.

### The repeated-surface table — existing seam

`tests/unit/test_generate_skill.py` already holds all four paths as module
constants (`SKILL_PATH`, `README_PATHS`, `SUBMISSION_PATH`), which makes it the
highest existing seam for this. One parametrised test walks the table and
asserts verbatim containment of the manifest's string in each surface. Adding
Phase 2's and Phase 6's surfaces is adding a row.

The existing assertion pinning the old `superpowers` description in the
submission document moves to the `choose_when` clause that replaces it.

### The Generation Skill's interview — existing seam

Also `tests/unit/test_generate_skill.py`, reading the file and asserting on its
text, as `test_skill_documents_safe_failure_and_verification_behavior` and
`test_skill_leads_with_interview_before_selection_flags` already do. This is the
answer to the file going false seven times in one day during v0.12: the existing
tests compare identifier lists only, so prose was unguarded.

Assertions: the known-facts block names all four stack tokens; all seven
Must-Asks are present; the design question is open and instructs against
guessing a near miss; the destination instruction asks for a name and a
destination and no longer instructs the agent to choose one; `react-doctor` and
`webapp-testing` triggers carry no React-frontend condition; `:49`'s non-empty
refusal is still stated.

One behavioural assertion rather than a text one: `react-doctor` and
`webapp-testing` remain absent from a `--yes` project.

### The stack claim — existing seam, offline

`tests/unit/test_check_stack_facts.py` already builds a fixture project tree and
runs the comparison offline, per the FR-16 and ADR-019 pattern. It gains a
fixture repository directory holding a `SKILL.md`, and cases for: the claim
present and upstream evidence present (passes); the claim present and evidence
missing (fails); the claim missing from the authored file (fails).

In CI the check is network-marked by inheritance — it runs inside
`generate-and-verify`, which already generates against the pin. It never runs in
the offline unit suite.

### The cross-release gate

`tests/e2e/test_upgrade_from_release.py` is unchanged apart from the constant.
It stays network-marked and stays in its own CI job.

Every unit test in this phase runs offline, under `tmp_path`, with no network
and no filesystem access outside `tmp_path` and the repository's own committed
files.

## Out of Scope

- **Every CLI screen.** No comparison panel, no colour, no `rich` dependency, no
  re-layout of the generation report or the confirmation summary. Phase 2 owns
  all of it, including the surface that renders `choose_when` in a terminal. The
  interactive flow prompt keeps its current one-row-per-flow rendering.
- **Generation into an occupied destination.** `_validate_target_dir`,
  `FORBIDDEN_PATHS`, the finalize sequence, `--dir .`, and the name-from-
  directory default are Phase 3's (FR-53, ADR-031). `SKILL.md:49` keeps telling
  the developer a non-empty destination is refused, because until Phase 3 it is.
- **`addyosmani`.** Not described, not given criteria, not made selectable. FR-48
  in Phase 5 reads it first.
- **New Token Optimize items.** FR-49 in Phase 5 adds them. Phase 1 only makes
  the Category reachable through the interview.
- **The Default Set.** ADR-018's limit is not reopened.
- **`README.md`'s structure, `README.zh-TW.md`, and the CHANGELOG.** Phase 6
  owns the README rewrite (FR-54) and every CHANGELOG entry, including the one
  recording this phase's second rewrite of the shipped descriptions. Phase 1
  touches `README.md` only at the four description lines.
- **The stamp.** No field is added, removed, or re-typed; it stays at version 5.
  A ticket that finds itself proposing version 6 has found something this spec
  got wrong and stops.
- **`docs/agents/<flow-id>.md`.** Deliberately not a `choose_when` surface: it is
  written only when its flow is already selected, so it cannot help anyone
  choose (ADR-024, 2026-08-23).

## Further Notes

**Two documents were written during the grilling session and are already on
disk**, because ADR-021's `grill-with-docs` step requires anything outliving the
phase to be recorded before the phase moves on:

- `docs/decisions/adr-024-engineering-flow-selection-spine.md` — the 2026-08-25
  amendment recording the backtick signal and the two-direction guard, with the
  structured-clause-object and leave-it-to-review alternatives and why each was
  rejected.
- `CONTEXT.md` — [[Flow Selection Criteria]] updated with the backtick
  convention and with `description`'s narrowed job; [[Must-Ask]] added.

**This phase repairs a repair.** FR-50 repairs FR-47's recommendation and the
interview corrections repair FR-34's interview. The complaint that produced both
is recorded in the version plan's 2026-08-23 amendment and does not need
re-litigating; a ticket that finds itself re-deriving the complaint rather than
building the repair has lost the thread.

**The guard holds the file, not the meaning.** A clause naming
`verification-before-completion` is held true only in the sense that the step
exists and is byte-identical to the pin. A pin bump that changes what that step
*does* requires a human to re-read it. That is stated here rather than left to a
reviewer's attention, and it is the same limitation ADR-023 accepts by design.

**Nothing in this phase is deep code.** It is manifest data, authored text, and
tests over both. The one seam that is genuinely new mirrors an existing one
field-for-field. If a ticket finds itself designing an abstraction here, it has
found something this spec got wrong.
