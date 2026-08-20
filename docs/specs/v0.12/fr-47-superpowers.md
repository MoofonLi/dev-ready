# FR-47 — `superpowers` becomes the second Engineering Flow

Status: Accepted by Moofon (2026-08-20), under the blanket authorization
given for this phase — accepted without a separate review pass.

Version: v0.12

Phase: 2 (the whole phase; FR-47 is its only requirement)

Governing decisions: **ADR-024** (the [[Engineering Flow]] is the user-facing
selection spine, as amended 2026-08-18 and **corrected 2026-08-20**),
**ADR-029** (a flow declares its own `chain` and its own mount roles), and
**ADR-030** (a vendored skill may ship executable files, and dev-ready carries
the executable bit) govern the feature. ADR-002 (pinned generation), ADR-004
(all-or-nothing generation), ADR-008 (vendor mode), ADR-009 (provenance),
ADR-010 (item-level selection), ADR-011 (canonical paths), ADR-014 (truthful
overlay lifecycle state), ADR-016 (English authored surfaces), ADR-017
(Category-first selection), ADR-018 (the Mount Point, as amended by ADR-029),
ADR-021 (the Spec Loop), ADR-023 (upstream facts under a drift guard), ADR-026
(`setup-project` is unconditional infrastructure), ADR-027 (the repository root
is a shipping surface), and ADR-028 ([[Skill Link]] delivery) remain binding.
ADR-025 is superseded in full and implements nothing.

**The stamp stays at version 5.** Every field this spec adds is manifest data.
No recorded field is added, removed, or re-typed, and there is no migration.

---

## Problem Statement

A generated project is built around one development method, and dev-ready asks
which one before anything else. Since v0.11 the question has had one answer.
Asking it at n=1 was deliberate — it discloses to a user that their project has
a method — but a question with one answer cannot help anyone choose, and two
further flows have been announced in the menu as `(coming soon)` since v0.11
shipped. `superpowers` has been named there for a version without arriving.

Adding the second flow looked like a data change. The v0.12 plan said so
explicitly: FR-46 landing first would make FR-47's addition "data-only". That
estimate was wrong, and the Phase 2 grill found four reasons before any code was
written.

The manifest stops loading the moment a second flow exists. Seventy-eight
Catalog Items declare a [[Mount Point]] naming one of `code-review`, `tdd`, or
`implement`, and the loader requires every mount to name a step of *every*
flow. `obra/superpowers` ships none of those three names, so the whole catalog
fails to load and every test that reads it fails with it. Relaxing the loader
alone moves the failure from the maintainer to the user, because generation
raises when it cannot find the skill file a mount names.

The generated text assumes both flows behave alike, and they do not. Of the
twelve `mattpocock/skills` items dev-ready vendors, the chain entries declare
`disable-model-invocation: true` and the tools do not. Of superpowers' twelve,
**none** declares it. A generated `AGENTS.md` that tells a superpowers project
its steps are user-invoked ships a false statement about the flow the user
selected — the exact defect class FR-43 spent a phase removing.

The guard meant to prevent that cannot be written as specified. ADR-024 asked a
test to assert the declared invocation against every step a flow ships, but
`mattpocock` declares `user` and ships six steps that are model-invokable by
design. The list the test needs — which steps are chain entries — exists only as
prose inside a Python string, where no test can read it.

And the twelve skills are not documentation. Six of their files are executable
upstream, their skills invoke those files bare, and dev-ready writes every
generated file with a bytes write that sets no mode. A user selecting this flow
would receive a project whose first step answers `Permission denied`.

## Solution

`superpowers` stops being an [[Announced Flow]] and becomes an ordinary Catalog
Item: twelve vendored skills, a declared chain, declared mount roles, a declared
invocation model, and a per-flow document. `addyosmani` stays announced.

A flow now describes its own shape. It declares the ordered entries of its
[[Flow Chain]], including the one position where it offers a choice, and it
declares which of its own steps play the `build`, `test`, and `review` roles. A
mounted Enhancement names a role rather than a skill, so the same Design
Reference attaches correctly to whichever flow the user picked. Because
superpowers forks at its fourth position, a role resolves to a set of steps and
`build` covers both branches — a user reaches their selected enhancements down
either one.

The generated text renders from those declarations rather than from prose. A
project's `AGENTS.md` states its own chain and its own [[Flow Invocation]] and
never the other flow's, and it states that the [[Setup Step]] is user-invoked
even where everything after it is not. Each flow gets one human-facing document
under `docs/agents/`, and superpowers' is the first that must explain a choice
inside a chain.

The two flows' `description` strings become selection criteria, on the two axes
that are traceable to something dev-ready ships and guards. One string per flow
serves both the interactive row and the Generation Skill's trigger line, because
two separately worded descriptions of one fact are how two surfaces drift.

The executable bit travels. A vendored pin declares which of its source paths
are executable and generation applies that mode after writing the bytes, so the
flow's first step and its subagent branch actually run.

## User Stories

1. As a developer starting a project, I want the Engineering Flow question to
   offer two real answers, so that the first question dev-ready asks me is a
   choice rather than an announcement.
2. As a developer choosing between two flows, I want each row to tell me what
   working with it feels like, so that I can decide without reading two upstream
   repositories.
3. As a developer who wants to start every step myself, I want a criterion that
   says so plainly, so that I pick `mattpocock` on purpose rather than by
   accepting the default.
4. As a developer who wants the agent to drive, I want a criterion that says the
   agent starts each step on its own, so that I know what I am agreeing to.
5. As a developer who cares whether work is split across subagents, I want that
   difference stated in the row, so that I do not discover it mid-implementation.
6. As a developer running `dev-ready init --yes --flow superpowers`, I want a
   project holding exactly that flow's twelve skills, so that my project is not
   carrying a second method's skills alongside them.
7. As a developer running `--flow mattpocock`, I want none of superpowers'
   skills, so that the reverse holds too and a flow's paths are never both
   written into one project.
8. As a developer, I want `--flow superpowers` to stop exiting 2, so that the
   flag matches the menu.
9. As a developer, I want `--flow addyosmani` to keep exiting 2 saying it is not
   yet available, so that an announced flow is still distinguishable from a
   typo.
10. As a developer, I want `--flow spec-loop` to keep exiting 2 naming the
    rename, so that the v0.10 identifier keeps its migration message.
11. As a developer, I want an unknown `--flow` id to exit 2 listing the valid
    ids, so that the list I am shown includes `superpowers` once it ships.
12. As a developer accepting every default, I want `mattpocock` unchanged as the
    Default Set's flow, so that `--yes` produces what it produced in v0.11.
13. As a developer selecting Design References with `superpowers`, I want them
    referenced from a step that flow actually has, so that my selection is not
    silently dropped.
14. As a developer taking either branch of superpowers' fork, I want my selected
    enhancements referenced from the branch I took, so that the choice inside
    the chain does not decide whether my selections appear.
15. As a developer selecting `webapp-testing` with `superpowers`, I want it
    attached to that flow's test step, so that the reminder arrives when I am
    writing tests.
16. As a developer selecting `react-doctor` or `security-audit` with
    `superpowers`, I want them attached to that flow's review step, so that the
    reminder arrives when review happens.
17. As an agent working in a generated project, I want `AGENTS.md` to state my
    project's own chain, so that I do not follow a chain belonging to a method
    this project did not select.
18. As an agent in a `superpowers` project, I want `AGENTS.md` not to tell me my
    steps are user-invoked, so that I do not wait to be asked for something I am
    supposed to start.
19. As an agent in a `mattpocock` project, I want `AGENTS.md` to keep telling me
    its steps are user-invoked, so that v0.11's correct statement survives.
20. As an agent in a `superpowers` project, I want to be told that the setup step
    is user-invoked even though the rest are not, so that I do not run project
    configuration unprompted.
21. As an agent in a `superpowers` project, I want to know where plans and design
    documents belong, so that I do not invent a location the shipped skills
    contradict.
22. As a developer reading `docs/agents/superpowers.md`, I want the chain
    explained including its fork, so that I understand I am choosing between two
    ways to execute a plan rather than skipping a step.
23. As a developer reading either per-flow document, I want to know the flow need
    not finish in one session, so that stopping at an accepted plan is not a
    failed run.
24. As a developer running the superpowers flow on macOS or Linux, I want its
    scripts to be executable, so that the commands its skills issue actually run.
25. As a developer on Windows, I want the per-flow document to say what depends
    on my shell, so that a failure there is explained rather than mysterious.
26. As a developer, I want `brainstorming`'s runtime state directory ignored by
    git, so that session scratch state does not enter my history.
27. As a developer, I want my plans and design documents *not* ignored, so that
    the durable output of the flow is committed.
28. As a developer generating with `--agents none`, I want the flow to behave
    exactly as it does with an Agent Target selected, minus the links, so that
    the two features stay independent.
29. As a maintainer, I want a flow declaring `user` while shipping a
    model-invokable chain entry to fail the build, so that the invocation field
    is guarded rather than commented.
30. As a maintainer, I want a flow declaring `model` while shipping any step that
    declares the flag to fail the build, so that upstream adding the flag is
    caught at the pin bump.
31. As a maintainer, I want a step id with no matching path to fail at load time,
    so that a typo is a manifest error rather than a user's generation failure.
32. As a maintainer, I want a role a flow does not declare to fail at load time,
    so that a mounted item can never name a part no flow plays.
33. As a maintainer, I want a role resolving to a step the flow does not ship to
    fail at load time, so that a typo in the role map is caught where it is
    written.
34. As a maintainer, I want `vendored-drift` green with the new entry, so that
    the twelve skills stay byte-identical to the pinned commit.
35. As a maintainer, I want the notices check green with twelve new `LICENSE`
    destinations, so that FR-41's notice propagation covers the new flow.
36. As a maintainer bumping the `obra/superpowers` pin, I want a changed file
    mode to be visible, so that the executable declaration cannot silently go
    stale behind a content-only comparison.
37. As a maintainer bumping a pin that touches a step named in a `description`, I
    want the spec to say I must re-read that step, so that a guarded claim does
    not quietly become false.
38. As a maintainer, I want the Generation Skill's contract test to pass at the
    end of this phase, so that no phase boundary is crossed with a red suite.
39. As a maintainer, I want the Generation Skill to stop stating a chain, so that
    the third flow does not require editing the same sentence again.
40. As a maintainer, I want `docs/cli-spec.md` corrected everywhere it says one
    flow exists, so that the command interface document matches the command.
41. As a maintainer, I want the two cli-spec lines about the Default Set left
    alone, so that a careful reader does not "fix" a statement that is still
    true.
42. As a maintainer writing tests, I want a whole-catalog selection helper that
    can be built around either flow, so that overlay coverage is not permanently
    pinned to the default.
43. As a reviewer, I want acceptance criteria that cannot pass while the flow
    fails at its first step, so that the release gate measures something a user
    would recognise.

## Implementation Decisions

### Vendoring and provenance

A new `vendored` entry pins `obra/superpowers` at commit
`b36e0829c6d0140e93cfef2ca599b1b07d4a7797`, licence MIT. Re-resolve and
re-record at sync time if upstream has moved, and re-measure the counts below if
it has. Measured 2026-08-20 at that commit: fourteen skills, fifty-one files,
369,641 bytes; the curated twelve are thirty-eight files and 245,095 bytes.

The entry declares twenty-four paths, matching the `mattpocock/skills` entry in
shape: twelve skill directories, plus twelve copies of the repository-root
`LICENSE`, one into each vendored skill directory, which is how FR-41 propagates
an MIT notice. `scripts/sync_vendored.py` performs the sync and `vendored-drift`
holds the result byte-identical.

The two excluded skills are excluded on the standard `mattpocock` already sets —
dev-ready vendors twelve of that project's thirty-five. `using-superpowers` is
installation metadata, teaching an agent to locate superpowers across other
products, a question a dev-ready project answers through its Agent Target
selection. `writing-skills` is skill authoring rather than project building, and
is the heaviest single skill at 107,377 bytes, 29% of the upstream total. A
skill ships whole or not at all, because FR-16 compares directories byte for
byte, so `systematic-debugging` brings its own fixtures and `brainstorming`
brings its scripts.

The curated twelve are `brainstorming`, `dispatching-parallel-agents`,
`executing-plans`, `finishing-a-development-branch`, `receiving-code-review`,
`requesting-code-review`, `subagent-driven-development`, `systematic-debugging`,
`test-driven-development`, `using-git-worktrees`, `verification-before-completion`,
and `writing-plans`.

### `superpowers` becomes a Catalog Item

Its `status` entry is removed, so the loader stops partitioning it into
`announced_loops`, and it gains the fields every development-loop item carries.
`addyosmani` keeps its `status` and stays announced.

Three consumers change as a consequence rather than by separate decision: the
interactive flow prompt gains one selectable row and loses one disabled row; the
`--flow` error path that says *not yet available* stops matching `superpowers`
and keeps matching `addyosmani`; and the error listing valid ids starts
including it.

### The flow declares its chain, its roles, and its invocation

A development-loop Catalog Item gains three fields, validated by the loader.

**`invocation`** takes exactly two values, `user` and `model`. `mattpocock`
declares `user`; `superpowers` declares `model`. The field records what upstream
already states and asserts nothing new — dev-ready cannot change either, because
FR-16 holds vendored files byte-identical.

**`chain`** is the ordered [[Flow Chain]]. An entry is a step id, or a list of
step ids where the flow offers a choice at that position. Every entry must name
a declared step. `setup-project` is **not** a chain entry: it is unconditional
non-catalog infrastructure under ADR-026 and rendering prepends it to every
chain, so listing it would put one fact in two places.

`mattpocock` declares five entries: `grill-with-docs`, `to-spec`, `to-tickets`,
`implement`, `improve-codebase-architecture`.

`superpowers` declares seven, the fourth of which is a choice:

```json
"chain": [
  "brainstorming",
  "using-git-worktrees",
  "writing-plans",
  ["subagent-driven-development", "executing-plans"],
  "test-driven-development",
  "requesting-code-review",
  "finishing-a-development-branch"
]
```

Its four remaining steps — `dispatching-parallel-agents`,
`receiving-code-review`, `systematic-debugging`, `verification-before-completion`
— are tools a step reaches for, exactly as `tdd` and `code-review` are for
`mattpocock`.

**`roles`** maps a role name to the set of that flow's own steps which play it.
`mattpocock` maps `build → [implement]`, `test → [tdd]`, `review →
[code-review]`. `superpowers` maps `build → [subagent-driven-development,
executing-plans]`, `test → [test-driven-development]`, `review →
[requesting-code-review]`.

### A mounted Enhancement names a role

`mount` stops naming a skill and starts naming a role. Seventy-four Design
References move from `implement` to `build` through one line in
`scripts/sync_design_references.py` and a regeneration. Four skills are edited by
hand: `frontend-design` to `build`, `webapp-testing` to `test`, and
`react-doctor` and `security-audit` to `review`.

Because a role resolves to a set, the grouping that decides where mounted
guidance is written emits one destination per resolved step. `build` therefore
writes into both branches of superpowers' fork. The duplication is in the
repository, not in the user's session: a user takes one branch. That grouping now
needs the resolved flow as an input, since a role cannot be resolved without
knowing which flow was selected — this reaches both generation and the upgrade
path that already consumes the same grouping.

### Loader validation

Four rules, all at load time, all flow-independent.

1. Every role a mounted item names is declared by every flow. This is the
   strength today's rule has, restated in role space.
2. Every role a flow declares resolves to steps that flow actually ships. New,
   and it is what turns a typo in the role map into a manifest error rather than
   an overlay error in a user's terminal.
3. Every `chain` entry names a declared step of its own flow.
4. Every step id has a `paths` entry whose destination leaf equals it. **One
   direction only.** `mattpocock` declares one path that is not a step, and
   `superpowers` declares twelve whose leaf is `LICENSE`. Verified 2026-08-20
   that this rule passes today's data unchanged, and verified that its absence is
   real: appending a nonexistent step id to `mattpocock` loads without complaint
   today.

Rule 4 is what ADR-024 assumed already existed when it rested the second
recommendation axis on `steps`. Without it that axis is unguarded.

### The frontmatter guard becomes data-driven and asymmetric

The guard reads the manifest instead of a hardcoded name list, and asserts a
different thing for each invocation model:

- `invocation: user` — every **chain entry** declares `disable-model-invocation:
  true`.
- `invocation: model` — **no shipped step** declares it.

The rule is asymmetric because a symmetric one fails on
`setup-matt-pocock-skills`, which declares the flag and is not a chain entry:
`setup-project` reaches it and nothing follows it. Each half is separately true
and each half catches the drift that can actually happen — upstream removing the
flag from a chain entry, or upstream adding it to a superpowers skill. The
`setup-project` template keeps its own separate assertion.

### Generated text renders from the declarations

The chain sentence in the generated `AGENTS.md` renders from `chain` and
`invocation` together. It states the selected flow's own entries, marks the
position where the flow offers a choice, and **describes the head separately**:
`setup-project` declares `disable-model-invocation: true` and heads every chain,
so a `superpowers` project's chain is a user-invoked head followed by
model-invoked entries.

Each flow keeps an authored guidance entry for what is not derivable — its
convention paragraph and its `setup-project` contribution. `superpowers`
contributes nothing to `setup-project`, because it ships no setup skill and has
no convention to configure; the template is adjusted so an empty contribution
does not leave a doubled blank line. A flow with no guidance entry remains a
generation error rather than a silent omission.

`docs/agents/superpowers.md` is written as this flow's human-facing document,
from upstream's own declared chain, and is the first per-flow document that must
explain a choice inside a chain. It carries what automation cannot: that the flow
need not finish in one session, what the fork is choosing between, and where the
executable-bit guarantee stops on Windows.

### Where a superpowers project puts its work

dev-ready supplies a convention only where the flow's own skills decline to
choose one. `mattpocock` declines, which is why dev-ready binds it to a local
Markdown tracker under `.scratch/`. `superpowers` does not decline: its
`writing-plans` fixes plans at `docs/superpowers/plans/`, and its
`brainstorming` fixes design documents at `docs/superpowers/specs/`. Giving it
the `.scratch/` convention would contradict the skills shipped beside it.

Its `AGENTS.md` therefore names upstream's two paths rather than inventing a
third. That is a claim about upstream, permitted under ADR-023 because
`vendored-drift` holds both files fixed at the pin: if upstream moves a path, the
drift job fails and the sentence is updated at bump time. The tracker and domain
convention documents remain `mattpocock`'s and ship only with it.

### The two descriptions become selection criteria

One string per flow, serving both the interactive row — rendered as
`"{display_name} — {description}"` — and the Generation Skill's trigger line.
The criteria rest on exactly two axes, because only two are traceable to
something dev-ready ships and guards: who invokes the method, from `invocation`;
and whether work is split across subagents, from the declared `chain` and the
paths its entries resolve to.

- `mattpocock`: *You start each step yourself, and the work stays in one
  session.*
- `superpowers`: *The agent starts each step on its own, and implementation can
  be split across fresh subagents.*

"can be" is deliberate: the subagent branch is one side of the fork, not the only
path. `mattpocock`'s shipped v0.11 description changes, which is user-visible and
belongs in Phase 3's CHANGELOG.

Nothing further is said. A claim about upstream's features has no drift guard and
goes quietly false.

### Executable content

The vendored pin declares which of its source paths are executable, and
generation applies that mode after writing the bytes. Six paths in the curated
twelve carry mode `100755` upstream: `brainstorming/scripts/start-server.sh`,
`brainstorming/scripts/stop-server.sh`,
`subagent-driven-development/scripts/review-package`,
`subagent-driven-development/scripts/sdd-workspace`,
`subagent-driven-development/scripts/task-brief`, and
`systematic-debugging/find-polluter.sh`.

No heuristic decides this. "Anything under `scripts/`" would also mark
`frame-template.html`, `helper.js`, and `server.cjs`, which upstream leaves at
`100644`.

The declaration is necessary because the fact lives on a source path inside
`obra/superpowers` while the write happens at a destination path inside the
user's project, and nothing carries information between those path spaces today.
It is also necessary because neither the repository nor the wheel can supply it:
every file under `templates/` is recorded `100644`, the maintainer's machine has
`core.fileMode=false`, and generation's only write sets no mode at all.

The guarantee stops at Windows, where setting an executable bit does nothing
useful and the result depends on the user's shell. The per-flow document says so
rather than implying the fix is universal.

`brainstorming`'s runtime state directory, `.superpowers/`, gains a `.gitignore`
entry under FR-38's prune-and-replace authority. `docs/superpowers/` is never
ignored — it holds the plans and design documents the flow expects to be
committed.

### Surfaces that state a single flow

Nine locations state or imply that one flow exists. The Generation Skill's
contract test compares **identifier lists** only, so it forces exactly one of
these edits; `docs/cli-spec.md` has no test at all. All nine are corrected in
this phase.

In `skills/dev-ready/SKILL.md`: the Engineering Flows bullet list gains a
`superpowers` row and both criteria are rewritten; the paragraph saying
`superpowers` cannot be selected keeps only the `addyosmani` case; the quoted
`valid ids` list is updated; the sentence stating one universal chain is
**deleted**, not duplicated, and points at the per-flow document instead; and the
sentence saying every generated project resolves `mattpocock` becomes a statement
about the default.

In `docs/cli-spec.md`: the line saying Dev has one Engineering Flow option; the
sentence saying `--flow` remains data-driven *if* the manifest adds another flow;
the failure list, which loses its `superpowers` example and keeps the announced
case for `addyosmani`; and the interactive-flow step saying only `mattpocock` is
selectable.

In `tests/unit/test_generate_skill.py`: the assertion that the skill text
contains the exact string `Engineering Flow 'superpowers' is not yet available`.

**Two lines are deliberately left unchanged**, because the Default Set does not
move in v0.12: `--flow`'s documented default, and the sentence describing what
accepting every default produces.

### Selection resolution

The CLI selection path is correct as it stands and needs no change. Verified by
argument vector on 2026-08-20: `--categories all --flow mattpocock` resolves
exactly one flow and leaks no other loop id into the selection, because the
Category resolution already subtracts every development-loop id before adding the
resolved flow back.

The whole-catalog helper is a different matter. It hardcodes the Default Set's
flow, and it has **no production caller** — it is a test fixture, used at seven
sites. Left alone it would silently pin overlay coverage to `mattpocock` forever,
so it gains the flow as an input. This corrects the v0.12 plan, which described
the same helper as a CLI defect reachable through `--categories all --flow
superpowers`; that argument vector does not reach it.

## Testing Decisions

A good test here asserts what a generated project contains and what the CLI
reports, not which helper computed it. Tests assert the resolved selection, the
files on disk and their modes, the text of generated documents, and the exit
codes and messages a user sees. They do not assert private call order, the
internals of the role resolver, or which function appended a sentence.

**No new seam is introduced.** Every assertion lands on a seam that already
exists, which is the point: this phase changes what flows through the system, not
where the system can be observed.

1. **`load_manifest`** is the validation seam. It proves the catalog loads with
   two selectable flows and one announced flow, and that each of the four new
   rules rejects its own violation: a mounted role no flow declares, a role
   resolving to an unshipped step, a chain entry that is not a step, and a step
   with no matching path. Each rejection is asserted against a deliberately
   malformed in-memory manifest, never against the shipped one. Prior art is the
   existing manifest validation suite, including its announced-flow partition
   test.
2. **`generate_project`** is the primary generation seam. Tests generate into
   `tmp_path` and assert: `--flow superpowers` writes that flow's twelve skills
   and none of `mattpocock`'s, and the reverse; mounted enhancements appear under
   both branches of the fork and under the correct single step for `test` and
   `review`; the six declared paths are executable and the four ordinary program
   files are not; `docs/agents/superpowers.md` is present only when that flow is
   selected; the generated `AGENTS.md` states the selected flow's chain and
   invocation and states them differently for each flow; and a `superpowers`
   project's `AGENTS.md` does not claim its steps are user-invoked while a
   `mattpocock` project's still does. Prior art is the existing overlay
   happy-path, mounted-enhancement, and flow-guidance coverage.
3. **`build_answers` by argument vector** is the CLI seam. It proves `--flow
   superpowers` no longer exits 2, `--flow addyosmani` still exits 2 saying it is
   not yet available, `--flow spec-loop` still exits 2 naming the rename, an
   unknown id exits 2 listing both valid ids, and `--categories all --flow
   superpowers` resolves exactly one flow with no leakage. Prior art is the
   existing flow-failure parametrisation and the selection resolution suite.
4. **The frontmatter guard** reads the manifest and asserts the asymmetric rule
   for every declared flow. It is asserted to **fail** against a deliberately
   mismatched declaration — a `user` flow whose chain contains a model-invokable
   step, and a `model` flow shipping a step that declares the flag — because a
   guard never seen to fail is not known to guard anything. The separate
   `setup-project` assertion stays.
5. **The Generation Skill contract test** proves the documented identifiers match
   the live catalog with two flows present, and that the skill text no longer
   contains a chain or the retired not-yet-available string. It must pass at the
   end of this phase without any Phase 3 edit.
6. **Maintainer tooling** covers the new pin: the vendored drift check is green
   with the new entry, and the notices check is green with twelve new `LICENSE`
   destinations. The drift check also compares the declared executable paths, so
   an upstream mode change is visible to a content comparison that would
   otherwise miss it. Prior art is the existing sync and notices suites.

Unit tests use `tmp_path`, perform no network access, and never depend on a
developer's global tools, home directory, or system locale. **No test assumes an
executable bit is observable**: the mode assertions are skipped where the
platform cannot represent them, in the same spirit as the existing rule that a
POSIX-symlink assertion on Windows proves nothing about a user.

The end-to-end and network-marked suites are unchanged by this phase. The N−1
upgrade gate keeps the baseline Phase 1 advanced to `0.11.0`.

## Out of Scope

- The third Engineering Flow, `addyosmani`, which stays an Announced Flow with
  its `status` entry intact (FR-48, v0.13).
- `i-have-adhd` and the Token Optimize additions (FR-49, v0.13).
- `headroom` and `graphify` — recorded candidates, neither scheduled.
- FR-27's second base template (v1.0).
- Any stamp change. Every field added here is manifest data; a phase that
  believes it needs version 6 has found an error in this spec and must stop.
- Any `--skill-delivery` flag, `copy` mode, delivery prompt, or platform
  conditional fallback. ADR-025 is superseded in full.
- Adding a spec-to-behaviour test for `docs/cli-spec.md`. Its complete absence of
  automated coverage is recorded here as a known risk and deliberately left open:
  closing it is its own piece of work, and this phase is already larger than the
  plan estimated.
- Every README and the CHANGELOG. All documentation of the shipped surface
  belongs to Phase 3, including `mattpocock`'s changed description.
- Editing any vendored file. FR-16 holds them byte-identical, which is exactly
  why `invocation` is manifest data rather than frontmatter.
- The v0.10.1 Spec Loop escape-hatch leftover, still deferred and still carrying
  no ADR.

## Further Notes

The v0.12 plan's sequencing rationale — that FR-46 landing first would make
FR-47's addition data-only — is wrong, and the plan carries a dated amendment
saying so. FR-46 did remove the Pointer Stub churn it promised to remove; the
four structural facts above were never data. `to-tickets` owns the internal
ordering of the larger footprint.

Two of ADR-024's supporting sentences were found false during the grill and are
corrected in place: the guard it specified fails on the day it is written, and
the steps-to-paths validation it relies on does not exist. Its conclusions are
untouched. A reader who arrives at that correction should not infer that more
moved than did — the Default Set, the default flow, and the curation standard are
all unchanged.

One obligation does not fit in a test and is recorded here instead. A pin bump
that touches a step named in a `description` requires re-reading that step. The
drift guard proves the file has not changed since a person last read it; it
cannot prove what the file means. That is the strongest guarantee available under
ADR-023, and it depends on this sentence rather than on a reviewer's attention.

Selecting `superpowers` means an agent may create branches, commit, and merge
without being asked: `using-git-worktrees` creates worktrees, `brainstorming`
commits its design document, and `finishing-a-development-branch` merges and
cleans up. This follows from `invocation: model` and is not a separate property,
but it is the concrete form the abstraction takes for a user, and
`docs/agents/superpowers.md` says it in those terms.

Superpowers' `brainstorming` can start a local HTTP server from a vendored Node
file. It is opt-in per session — offered just-in-time, only on approval, and
never offered when no visual question arises — and Node is required only on that
path. It remains the first time dev-ready places program code it did not write
into a user's repository, which is why ADR-030 states the widening rather than
leaving it to be inferred from a file list.
