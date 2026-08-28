# FR-51 — CLI presentation, second pass

Status: **Accepted** by Moofon (2026-08-28), by dispatching `to-tickets`
against it (ADR-021).

Version: v0.13

Phase: 2 (the whole phase; FR-51 is its only requirement)

Governing decision: **ADR-003** (distribution via uvx), as amended 2026-08-12
(the presentation complaint is real and is separate from the distribution
channel) and amended **2026-08-23** (`rich` enters the runtime, the generation
report is colourised, and FR-44's plain-text ruling is reversed). **ADR-005**
(minimal runtime dependencies) is the posture this phase spends against, with
one dependency authorized for the whole version. ADR-004 (interactive prompts
with a non-interactive escape hatch), ADR-016 (English authored surfaces),
ADR-017 (Category-first selection), ADR-021 (the Spec Loop), ADR-024 (the
[[Engineering Flow]] is the user-facing selection spine, as amended 2026-08-23
and 2026-08-25), and ADR-029 (a flow declares its own shape) remain binding.
No new ADR is written for this phase — see Further Notes.

Source: the `grill-with-docs` session of 2026-08-28, run against the shipped
v0.12.0 report rendered from the real catalog, `src/dev_ready/report/render.py`,
`src/dev_ready/prompts/collect.py`, and `uv.lock`. Nine decisions were settled
there. The one that outlives this phase is already recorded — `CONTEXT.md`'s
[[Static Screen]] entry — together with a correction to FR-51's own text in
`docs/requirements.md`. The rest are below.

---

## Problem Statement

A developer runs `uvx dev-ready init`, waits through four generation stages, and
is handed twenty-nine lines of undifferentiated lowercase text. Somewhere in the
middle of it are the four things they must actually do next. Above those four
lines sits a single line naming nineteen coding agents they do not have to do
anything about.

This is the third complaint in the 2026-08-22 field report, and it is a repeat.
FR-44 shipped in v0.11 to fix exactly this surface. It re-laid out the report
and styled the questionary prompts, and it ruled **explicitly** that the report
would not be colourised — on the reasoning that `render_report` is a pure
function, that terminal policy belongs to `cli`, and that colour would mean
hand-authoring a permanent policy surface (TTY detection, a `NO_COLOR`
convention, terminal width, plain-text degradation) "bought for very little".

The reasoning was sound about the cost and wrong about the outcome. The CEO's
verdict on the shipped result was that the screens are still plain. Both halves
of the trade have since moved: `rich` carries the entire policy surface as
existing behaviour, so the cost FR-44 declined is no longer this project's to
pay, and the benefit is now measured rather than assumed.

Three separate defects are folded into that one verdict, and they are worth
separating because only one of them is about colour:

1. **Nothing is differentiated.** Headings, body text, paths, and commands are
   all lowercase, all flush, all the same weight. There is no visual entry point.
2. **The most important block is buried.** The next steps — the only part of the
   report that requires the reader to act — sit below the selection summary and
   below the nineteen-agent line. A reader scanning from the top hits the least
   actionable content first.
3. **The two static screens do not look like one tool.** The pre-generation
   confirmation says `Ready to generate:` in Title Case; the report says
   `next steps:` in lowercase. FR-50 is about to add a third such screen — the
   flow comparison above the [[Engineering Flow]] menu — and without a settled
   idiom this project would ship three screens in three styles.

There is also a latent correctness problem that only appears once `rich` is
introduced: `rich` interprets `[...]` in a string as console markup. Project
names are validated to letters, digits, `.`, `_`, and `-`, so they are safe. The
destination path is **not validated at all**. A user whose path contains a
square bracket would today see part of it silently swallowed, or the render
crash outright.

## Solution

Three screens — and only three — become [[Static Screen]]s rendered by `rich` in
one frameless idiom of whitespace and colour: the pre-generation confirmation,
the [[Engineering Flow]] comparison, and the generation report.

**Frameless is a decision, not an omission.** Framed boxes are the visible
signature of the `@clack/prompts` installers that prompted the original
complaint, and they were offered and declined: a box wraps badly on a narrow
terminal and survives a copy-paste worse than indentation does. The polish comes
from whitespace, heading weight, and colour.

**The report is re-ordered so the actionable block comes first.** After the
three identifying lines — project, location, upstream — the next steps appear
immediately, above the selection summary and the Agent Target summary that
currently push them into the middle. The credential disclosure and the overlay
summary follow. The credential disclosure's *facts* are FR-38's and do not
change; only its position and styling do.

**The nineteen [[Standard-Compliant Agent]]s collapse to a count and three
examples.** The line exists so a reader recognises their own agent and
understands they had nothing to select; a full enumeration serves that purpose
worse than `19 … (codex, cursor, gemini-cli, …)` does.

**Colour is a decoration, never a carrier of meaning.** Every distinction the
screens make survives with every escape sequence removed, because a user who
sets `NO_COLOR`, or who pipes `init` to a file, must not be handed back the
plain screen FR-44 shipped and this requirement exists to replace. That is why
the headings change case as well as weight: casing and blank lines survive the
strip, colour does not.

**`questionary` keeps every interactive prompt.** It owns keyboard handling,
cancellation, and the disabled row an [[Announced Flow]] needs. Two libraries,
one boundary each.

**Everything else stays plain text**: the four-stage progress renderer, `check`,
`upgrade`, and every error message. `check --json` must stay machine-readable
and error messages on stderr are routinely grepped.

## User Stories

1. As a developer who has just generated a project, I want the commands I must
   run next to be the first thing I see below the project's identity, so that I
   do not scan past a list of agents to find them.
2. As a developer reading the report on a colour terminal, I want section
   headings to stand out in weight and colour, so that I can find the block I
   need without reading every line.
3. As a developer who has piped `init` to a file, I want that file to contain no
   escape sequences, so that it is readable in an editor and diffable in a
   review.
4. As a developer who has piped `init` to a file, I want the file to contain
   every fact the terminal showed me, so that redirecting output never costs me
   information.
5. As a developer who sets `NO_COLOR` because I use a screen reader, I want the
   report to be as navigable without colour as with it, so that the section
   structure is not carried by something I cannot perceive.
6. As a developer on an 80-column terminal, I want the report to fit, so that
   nothing is truncated or wrapped into unreadable fragments.
7. As a developer on a very narrow terminal, I want the `cd` command and the
   destination path never to be wrapped, so that I can copy either one in a
   single selection.
8. As a developer whose project lives in a path containing a square bracket, I
   want that path printed exactly as it is, so that the location line is true
   and the command I copy actually works.
9. As a developer who has just been shown the pre-generation confirmation, I
   want it to look like the report that follows it, so that I recognise both as
   the same tool speaking.
10. As a developer choosing an [[Engineering Flow]] interactively, I want a
    comparison of the flows printed above the menu, so that I can make the
    choice the menu is asking me to make.
11. As a developer choosing an [[Engineering Flow]], I want that comparison to
    be the manifest's own [[Flow Selection Criteria]], so that what I read
    before choosing is the same text every other surface shows me.
12. As a developer who answered the flow question with a `--dev` flag, I do not
    want a comparison printed for a question I was never asked, so that the
    output contains nothing irrelevant to my run.
13. As a developer who uses Codex, I want to see my agent named in the report's
    examples, so that I understand no target selection was needed for it.
14. As a developer using an agent not among the three examples, I want the count
    and the trailing ellipsis to tell me the list is longer, so that I do not
    conclude my agent is unsupported.
15. As a developer reading the report, I want the credential disclosure to keep
    naming the password by key and never by value, so that no secret lands in my
    scrollback or my CI log.
16. As a developer scanning the report, I want a blank line between every major
    block, so that the structure is visible before I read a word.
17. As a maintainer, I want `render_report` to stay a pure function returning a
    string, so that it remains callable with no terminal present and the report
    tests keep needing no terminal.
18. As a maintainer, I want the TTY and `NO_COLOR` decision to be made in exactly
    one place, so that a second, divergent policy cannot appear later.
19. As a maintainer, I want the shared visual idiom to live in one module, so
    that three screens cannot drift into three styles.
20. As a maintainer, I want `rich`'s import confined to one module, so that the
    dependency's blast radius is a single file.
21. As a maintainer, I want the existing report tests to keep their call
    signatures, so that a presentation change does not require rewriting fifteen
    unrelated assertions.
22. As a maintainer, I want the default rendering mode to be plain text, so that
    any caller that forgets to pass a style gets the safe result rather than
    escape sequences.
23. As a maintainer, I want the `Asker` protocol left unchanged, so that a
    presentation change does not force both of its implementations to move.
24. As a maintainer, I want the four-stage progress renderer untouched, so that
    the one part of the terminal surface nobody complained about stays stable.
25. As a maintainer reading `docs/architecture.md`, I want the new module listed
    in the Module Boundary table with its prohibitions, so that a future change
    knows what may not go into it.
26. As a maintainer, I want the exact transitive cost of `rich` recorded, so that
    the dependency budget reflects four packages rather than one.
27. As a user of `dev-ready check`, I want its output to stay plain and its
    `--json` output to stay machine-readable, so that my scripts keep working.
28. As a user hitting an error, I want the message on stderr to stay plain text,
    so that grepping it and pasting it into an issue both still work.
29. As a reviewer, I want the report's block order asserted by a test, so that a
    later refactor cannot quietly bury the next steps again.
30. As a reviewer, I want a test proving the three named example agents still
    exist in the manifest, so that the report cannot name an agent dev-ready
    dropped.
31. As a reviewer, I want each static screen asserted twice — once with colour
    forced, once with `NO_COLOR` — so that the degraded path is specified rather
    than hoped for.

## Implementation Decisions

### 1. One new module owns the idiom, and it is the only module that imports `rich`

A new presentation module is added, holding the shared visual vocabulary and a
pure rendering primitive that takes structured blocks plus a colour-and-width
value and returns a string.

The alternative of widening the existing `report` module to own all three
screens is **structurally blocked, not merely worse**: `report` already imports
`Answers` from `prompts`, so having `prompts` import `report` for the
confirmation and comparison screens would create an import cycle. This was
checked in the source, not assumed.

The alternative of letting each of the three screens construct its own console
and constants was rejected because it produces three copies of an idiom whose
entire purpose is to be identical across three screens.

`docs/architecture.md`'s Module Boundary table gains a row for the new module.
Its prohibitions: it must not touch the filesystem, must not perform network
I/O, and must not decide terminal policy.

### 2. `render_report` stays pure, and no `Console` is ever threaded into `report`

`render_report` keeps returning a string and keeps performing no filesystem
access. It gains one keyword-only parameter carrying the resolved colour and
width, and constructs its own in-memory console internally from those primitive
values.

Passing a console object down into `report` is prohibited. That is the specific
line ADR-003's amendment draws to preserve FR-44's correct placement of terminal
policy, and a change that crosses it has traded the purity the amendment says
was preserved.

### 3. The colour and width decision is made once, at the `cli` boundary

`cli` resolves the terminal policy exactly once per run and passes the resulting
value down to each of the three screens. The renderers never read the
environment themselves.

**Mechanism versus decision.** The detection helper lives in the presentation
module and is called by `cli`. This keeps `rich`'s import confined to one file
while leaving the *decision* — when to detect, and what to hand to whom — at the
`cli` boundary where ADR-003 places it. A reviewer applying ADR-003's sentence
literally could read this as boundary drift, so it is recorded here as a
deliberate reading: `cli` decides, the presentation module supplies the
instrument.

### 4. The style parameter defaults to plain text

Every screen's style parameter has a default, and that default is uncoloured
with a fixed width. Two reasons: the fifteen existing `render_report` tests keep
their call signatures unchanged, and a caller that forgets the parameter gets
the safe result rather than escape sequences in an unexpected place.

### 5. The report's block order

The order becomes:

1. project name, location, upstream pin
2. **next steps**
3. selection summary (flow, documentation skeletons, enhancements) and Agent
   Target summary, including the collapsed standard-compliant-agent line
4. first-login credential disclosure
5. overlay summary

This is **not** what FR-51's original sentence said. That sentence — "next steps
move above the credential and inventory blocks" — described a state that was
already true in v0.12.0 and would have left the measured complaint unfixed. The
requirement text in `docs/requirements.md` has been corrected to say what the
measured complaint requires, with the superseded wording noted in place so the
next reader does not repeat the misreading. The existing ordering test is
rewritten rather than worked around.

### 6. The standard-compliant agent line collapses to a count and three examples

The three examples are `codex`, `cursor`, and `gemini-cli`: three different
vendors, high recognition, no two from the same product family. Taking the first
three alphabetically was rejected because it yields `amp`, `antigravity`,
`antigravity-cli` — two of which are the same product, leaving effectively two
examples.

The three ids are authored in the presentation of the report, **not** added to
the manifest as a `featured` field. A schema change for three cosmetic strings is
disproportionate. The falseness risk that authored prose carries in this
repository is closed by a test asserting each named id is still present in the
manifest's standard-compliant agent list, which fails the build if one is ever
dropped or renamed.

The line keeps a trailing ellipsis so a reader whose agent is not among the three
understands the list is longer.

### 7. Section headings change case as well as weight

Block headings become Title Case and are rendered bold and coloured. The
confirmation screen's existing `Ready to generate:` casing is what the report
adopts, rather than the confirmation dropping to the report's lowercase.

Casing is load-bearing, not cosmetic: colour is stripped whenever `NO_COLOR` is
set or stdout is not a terminal, so a design that differentiates by colour alone
degrades to precisely the undifferentiated lowercase screen this requirement
exists to replace.

### 8. Wrapping policy: paths and commands never wrap; prose does

Paths and commands are rendered with wrapping disabled; prose blocks wrap to the
resolved width. When stdout is not a terminal the width is a fixed 80 columns, so
redirected output is deterministic.

Wrapping everything was rejected because a broken `cd /long/path` defeats
copy-paste, which is the same objection that defeated framed boxes — the
objection cannot be honoured for frames and ignored for paths. Wrapping nothing
was rejected because the agent list would then run off a narrow terminal.

### 9. Every value that reaches `rich` is escaped

`rich` interprets `[...]` as console markup. Project names are validated to a
character set that excludes brackets, but destination paths are not validated at
all, and neither are catalog ids and Agent Target paths in the general case.
Every interpolated value passing through the presentation module is escaped, or
is passed in a way that suppresses markup interpretation. This is a correctness
requirement, not a hardening nicety: without it the location line can print a
path that is not the path.

### 10. The flow comparison is printed from the flow prompt, and the `Asker` protocol does not change

The comparison is rendered and printed immediately before the flow menu is
raised, from inside the flow prompt itself.

Printing it from `cli` before collection begins was rejected as **incorrect**,
not merely inelegant: the flow may already have been answered by a `--dev` flag,
in which case the user is never asked and a comparison would be printed for a
question that does not exist.

Extending the `Asker` protocol with a preamble argument was rejected because it
changes an interface both implementations must honour for the benefit of exactly
one caller.

The comparison renders every declared flow's [[Flow Selection Criteria]] and no
[[Announced Flow]]'s. The menu itself is unchanged: one row per flow, with
questionary's disabled row still carrying the Announced Flow.

### 11. Scope is three screens; everything else stays plain

The progress renderer, `check`, `upgrade`, and all error messages are untouched.
Error messages go to stderr and are routinely grepped; `check --json` must stay
machine-readable.

**A consequence to record honestly.** The v0.13 plan sequences FR-51 before
FR-53 partly on the ground that FR-53 "writes user-facing messages" that would
otherwise be authored in the old idiom and re-authored in the new one. Under this
scope decision, FR-53's collision and restoration messages are error messages and
inherit no `rich` idiom at all. What the ordering actually buys is that FR-53's
message *wording* is written once against a settled report layout — a real but
narrower benefit than the plan's sentence implies. The ordering stands; the
justification is corrected here.

### 12. `rich` costs four packages, not one

`rich` is absent from `uv.lock` entirely — it is not an existing transitive
dependency of `copier` or `questionary`. Adding it brings `rich` itself plus
`markdown-it-py`, `mdurl`, and `pygments`.

The version plan's authorization of "one new runtime dependency — `rich`" is
taken to cover its dependency tree. The `docs/architecture.md` dependency note
names all four packages explicitly, so the cost is stated rather than discovered
later. The bounded version range is resolved at implementation against what `uv`
actually installs on the project interpreter.

## Testing Decisions

**What makes a good test here.** These screens are external behaviour — they are
literally what the user sees — so assertions are made on rendered output, not on
how the renderer is structured. A test that asserts a console was constructed, or
that a particular style object was passed, is testing implementation. A test that
asserts the string a user would read is testing behaviour. Assert on *content and
order*, and on the *absence of escape sequences* in the plain path, rather than
on exact byte-for-byte screens, which would make every future wording change a
test change.

**Seams.** One new seam, four existing ones widened. This was checked against the
existing tests before being chosen.

- **New:** the presentation module's rendering primitive, called directly as a
  pure function. This is where the idiom itself is specified: heading treatment,
  block separation, no-wrap of paths and commands, wrapping of prose, and the
  guarantee that the uncoloured rendering contains no escape sequences.
- **Existing:** `render_report` called directly, as the fifteen current tests in
  `tests/unit/test_report.py` already do. Their signatures do not change.
- **Existing:** the confirmation screen, driven with an injected fake asker and
  captured from stdout — the pattern already used by the confirmation summary
  test in `tests/unit/test_prompts.py`.
- **Existing:** the flow comparison, driven through the same injected fake asker
  used by every interactive-collection test, with stdout captured. No new test
  entry point and no protocol change.
- **Existing:** `main(argv)` in `tests/unit/test_cli.py`, with the environment
  monkeypatched, for the end-to-end `NO_COLOR` and non-TTY paths.

**Prior art.** `tests/unit/test_report.py` already asserts block ordering by
comparing string indices, already asserts the absence of escape sequences, and
already holds an authored constant true against another surface by test — the
superuser-email agreement test is the exact pattern the three named example
agents follow. `tests/unit/test_cli.py` already asserts stable non-TTY progress
rendering, which is the pattern for the environment-driven cases.

**Required cases.**

- Every static screen rendered twice: once with colour forced, once with
  `NO_COLOR` set. The plain rendering is asserted to contain no escape sequence.
- The plain rendering is asserted to contain every fact the coloured one does, so
  that degradation costs no information.
- Report block order asserted explicitly, with next steps above the selection and
  Agent Target blocks.
- The collapsed agent line asserted to carry a count and to name no more than
  three agents.
- Each of the three named example agents asserted to be present in the manifest's
  standard-compliant agent list.
- A destination path containing a square bracket asserted to appear verbatim in
  the report.
- A path and a command asserted not to wrap at a narrow width; a prose block
  asserted to wrap at the same width.
- The flow comparison asserted to contain every declared flow's criteria and no
  [[Announced Flow]]'s.
- The flow comparison asserted **absent** when the flow was resolved by flag and
  the prompt never runs.
- `render_report` asserted to still be callable with no terminal present and to
  still perform no filesystem access.
- `init` asserted to still report exactly four progress stages.

**Constraints.** Unit tests only: no network, no filesystem outside `tmp_path`.

## Out of Scope

- **Framed boxes, panels, and borders.** Considered and declined in ADR-003's
  2026-08-23 amendment. A phase that adds one has reversed a recorded decision.
- **Colourising `check`, `upgrade`, error messages, or the progress renderer.**
- **Any change to `check --json`.**
- **Changing the `Asker` protocol** or replacing `questionary` for any
  interactive prompt.
- **Changing the credential disclosure's facts.** They are FR-38's; only their
  position and styling move.
- **Adding a manifest field** for featured agents, for flow ordering, or for
  anything else this phase renders.
- **Any README change.** Phase 6 owns `README.md`, `README.zh-TW.md`, and
  `README-pypi.md`, including the flow comparison the README will carry.
- **Any CHANGELOG entry.** Phase 6 owns the entry superseding FR-44's plain-text
  ruling.
- **Any second runtime dependency.** `rich` is the only one this version
  authorizes.
- **The stamp.** Nothing here adds, removes, or re-types a recorded field; the
  stamp stays at version 5.
- **Generation, verification, and finalize behaviour.** Untouched. The Occupied
  Target and the forbidden-path rescope are Phase 3's (ADR-031).
- **`--dir .` and the collision message.** Phase 3.
- **The third [[Engineering Flow]].** Phase 5. This phase renders whatever
  `choose_when` entries the manifest declares and asserts nothing about how many
  flows exist.

## Further Notes

**No new ADR.** Tested against the three conditions: the scope boundary of
decision 11 is already recorded in ADR-003's 2026-08-23 amendment, which names
the three screens `rich` owns; decision 1 is a module boundary and belongs in
`docs/architecture.md`'s table, which the phase updates; and the remaining
decisions are either cheap to reverse or follow directly from the amendment. The
one thing that outlives the phase and was not already written down is the
vocabulary, which is why [[Static Screen]] was added to `CONTEXT.md` instead.

**FR-51's own text was corrected during grilling.** The layout clause described a
condition that already held. The correction is in `docs/requirements.md` with the
superseded wording preserved in place. A reviewer comparing this spec against
FR-51 will find them in agreement; a reviewer comparing against the v0.13 plan's
Phase 2 bullet, which repeats the original wording, will find that bullet
superseded by decision 5.

**This is the second attempt at this surface in two versions.** FR-44 shipped
the same screens in `v0.11.0` on 2026-08-18 and was measured insufficient on
2026-08-22 — four days, and one release, later. The difference is not effort but
the dependency: FR-44
priced the policy surface as hand-authored work and correctly declined to build
it. Nothing in FR-44's reasoning was wrong; one of its inputs changed. This
should not be read as re-litigating FR-44, and the CHANGELOG entry Phase 6 writes
says the ruling was superseded rather than mistaken.

**Two TTY detection sites will coexist.** The progress renderer already performs
its own `isatty()` check on stderr and is explicitly out of scope. The new policy
resolution concerns stdout. They are different streams answering different
questions, so this is not the duplicated policy surface decision 3 exists to
prevent — but it is worth naming so a future reader does not mistake it for one.

**A verification owed at implementation.** Resolve the `rich` version range
against what `uv` actually installs on the project interpreter, and record the
installed transitive footprint before pinning the range. The plan requires this;
the four-package count above comes from reading `uv.lock`'s *absence* of `rich`
and from `rich`'s declared dependencies, not from an actual resolution.
