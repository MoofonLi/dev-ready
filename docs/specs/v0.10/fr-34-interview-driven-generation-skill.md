# FR-34 — Interview-Driven Generation Skill

Status: Accepted by Moofon (2026-08-05)

Version: v0.10

Phase: 4

Governing decisions: ADR-004, ADR-010, ADR-011, ADR-016, ADR-017, ADR-018,
ADR-019 (as amended 2026-08-03 and 2026-08-04), ADR-021

## Problem Statement

The [[Generation Skill]] is a lookup table for a vocabulary its reader does not
have.

A developer installs it so they can say "start me a FastAPI project" and have
their agent do the rest. What the agent finds is a flag reference: five
[[Category]] identifiers, eight [[Enhancement]] identifiers, 57 [[Agent Target]]
identifiers, and no statement anywhere of what any of them is for. `react-doctor`
and `security-audit` are self-describing; `caveman` and `code-memory` are not,
and those two are precisely the ones no description of a product implies.

So the agent has two moves, and both are bad. It can ask the user to name
identifiers — pushing dev-ready's internal vocabulary onto someone who installed
the skill to avoid learning it. Or it can take the [[Default Set]] and say
nothing, in which case the entire catalog exists but is never reached. v0.9 spent
a version making selection speak the user's language rather than the
implementation's ([[Category]] over [[Component]], ADR-017); the skill still
hands the model a table and expects it to have opinions.

**The file is ordered against its own purpose.** It opens with destination
resolution and flag semantics and never once asks what the user is building. A
model reads a document top to bottom; this one puts the machine interface before
the problem, and then the composition step has nothing to compose from except
whatever the user happened to volunteer.

**A user of a standard-compliant agent is told nothing, and absence reads as
rejection.** The skill lists 57 [[Agent Target]] identifiers and does not list
the 19 [[Standard-Compliant Agent]]s at all. A Cursor user searches the list,
does not find themselves, and concludes dev-ready does not support their agent —
when in fact Cursor reads [[Canonical Content]] directly and needs no
[[Pointer Stub]] at all. That is the exact misreading ADR-019 exists to prevent,
and its 2026-08-03 amendment discharged the obligation in the selection prompt
and the generation report. The interview is a third surface, and it is the
earliest: it runs before the CLI is invoked, so it is the first place a user can
form the wrong belief and the cheapest place to prevent it.

## Solution

The [[Generation Skill]] becomes an interview. The agent asks what the user is
building, maps the answer onto Categories and [[Catalog Item]]s, and composes one
command. Mapping a described need onto a selection is what a model does well and
what CLI branching does badly, which is the whole reason this work exists (D-2,
FR-34).

**One opening question, then only what is genuinely missing.** The agent asks
what the user is building and how they work with coding agents, then asks at most
three follow-ups — only for what that answer left ambiguous. The cap is not
cosmetic: "what are you building" reaches Design, Quality and Security by
inference, but it cannot reach Token Optimize, because that Category is about how
the user works rather than what they produce. Without a follow-up those two items
are unreachable; with an uncapped questionnaire the skill becomes the CLI
branching it was written to replace.

**Then a proposal, not an execution.** The agent presents one command with a
one-line reason per selected item and waits. The reasons are what let a user
correct a wrong inference before a directory exists rather than after.

**The interview replaces the CLI's prompts; it never chains into them.** The
command is always driven with `--yes`. Two interviews for one selection is a
defect, and the CLI's own prompts cannot run in a non-TTY session anyway — that
path fails fast with exit 2 by design (ADR-004).

**Every identifier gains a trigger.** Each [[Catalog Item]] is documented as its
id plus what, in the user's own words, should select it. This is written for the
mapping job rather than copied from the manifest: a manifest description's reader
is a person scanning a checkbox list, and it carries provenance text that tells a
model nothing about when to choose the item.

**The standard-compliant agents are named.** The skill lists them, and states
what their presence on that list means — that the agent reads
`.agents/skills/` directly and needs no target. A user who names one is told
that, never met with silence and never quietly dropped from the composed command.

## User Stories

1. As a developer who has never read dev-ready's documentation, I want to
   describe my project in my own words and receive a working command, so that I
   do not have to learn a selection vocabulary to use a scaffolding tool.
2. As a developer, I want to be asked what I am building before I am shown any
   flag, so that the tool starts from my problem rather than from its interface.
3. As a developer building a React frontend, I want the frontend-oriented items
   selected without my knowing they exist, so that the catalog reaches me.
4. As a developer who mentioned payments and user accounts, I want the security
   auditing item proposed, so that a relevant Enhancement is not missed because I
   did not know its name.
5. As a developer who never mentions context budget, I want to be asked about it
   once, because nothing I say about my product implies whether I want it.
6. As a developer, I do not want to answer seven questions to scaffold a project;
   I want a short interview that stops as soon as it knows enough.
7. As a developer, I want to see one proposed command with a reason for each
   selection, so that I can correct a wrong inference before anything is written.
8. As a developer who disagrees with one item in the proposal, I want to say so
   in plain language and get a corrected command, rather than being handed the
   flag reference and left to edit it.
9. As a developer who already described everything in my first message, I do not
   want to be asked again, because being re-interrogated about what I just said
   is the failure mode of every skill like this.
10. As a developer who says "just get me started", I want the [[Default Set]] and
    a note saying so, rather than an interview I did not ask for.
11. As an agent running with no human in the loop, I want a documented fallback
    to the Default Set with `--yes`, so that I neither hang nor invent answers.
12. As a developer, I want to be told afterwards what was assumed on my behalf,
    so that a fallback is visible rather than silent.
13. As a Cursor user, I want to be told that my agent reads the project's skills
    directly and needs no target, so that I do not conclude dev-ready does not
    support me.
14. As a developer whose teammate uses a different agent, I want to name both and
    have the command cover both, so that the project works for the whole team.
15. As a developer who names an agent that needs a target, I want its identifier
    resolved for me, because I do not know dev-ready's 57 identifiers and should
    not have to.
16. As a solo Claude Code user, I want `claude` chosen without being asked, so
    that the common case costs no questions.
17. As a developer, I want the composed command to be non-interactive, so that it
    runs identically whether my agent has a terminal or not.
18. As a developer, I want the destination resolved and inspected before anything
    runs, and a non-empty target to stop the agent rather than be cleared.
19. As a developer whose generation failed, I want the command, the exit code, and
    the error surfaced verbatim, so that the failure is not hidden behind a retry
    with a weaker selection.
20. As a developer with an existing generated project, I want to be told that
    `check` and `upgrade` are the commands for it, so that my agent does not point
    `init` at a directory that already has my work in it.
21. As a maintainer, I want every worked example in the skill to parse and resolve
    against the live catalog, so that a documented example can never be one the
    CLI rejects.
22. As a maintainer, I want a new manifest item to break the build until someone
    writes its trigger line, so that the mapping cannot silently fall behind the
    catalog.
23. As a maintainer, I want the standard-compliant agent list held to the manifest
    the same way, so that an upstream agent moving between the two lists is
    caught rather than quietly wrong.
24. As a maintainer, I want an automated assertion that the file still leads with
    the interview, so that a future edit cannot quietly restore the reference-first
    ordering this work exists to remove.
25. As a maintainer, I want the skill to remain outside the catalog and outside
    the generated overlay, so that a generated project never carries the tool that
    generates projects.

## Implementation Decisions

**One file.** The skill stays a single `SKILL.md`. Progressive disclosure into
reference files was measured and rejected: the whole file is roughly 1.4k tokens
and the 76 agent identifiers are roughly 225 of them, so a split saves about 15%
of an already small file, costs a hop the agent may decline to take, and adds a
second path the contract test must guard. The mapping step needs the catalog in
context to work at all, so the data an agent would fetch is data it always needs.

**Section order is load-bearing, not stylistic.** The interview comes first, the
mapping and composition next, and the identifier reference, flag semantics and
result handling after. A model reads in order; leading with the machine interface
is what produced the current behaviour.

**The mapping table is the identifier list.** Each item appears once, as its id
plus its trigger, and there is no second bare list. This is what keeps the
existing "documented ids equal catalog ids" assertion load-bearing: a manifest
item added with no trigger line fails the build, so the mapping cannot drift
behind the catalog without someone noticing. A separate list would leave the
triggers unguarded, which is the failure this arrangement is chosen to prevent.

**Triggers are authored, not copied.** They describe what the user might say, not
what the item contains. Byte-copying manifest descriptions was rejected: their
audience is a person reading a selection prompt, and at least one of them ends in
vendoring and licence text that is irrelevant to choosing it.

**Agent Targets are asked about, and the standard-compliant list is answered
from.** Naming an agent resolves to one of three outcomes, all of which the skill
states: it is an [[Agent Target]] and its identifier goes into `--agents`; it is a
[[Standard-Compliant Agent]] and the user is told it needs no target and why; or
it is unknown to both lists and the user is told that plainly rather than having a
near-miss identifier guessed for them. Absent an answer, the target resolves to
`claude`, which is already the CLI's default (ADR-019, 2026-08-03 amendment).

**The composed command is always non-interactive.** `--yes` is stated as an
invariant of the composition step, not as one option among several. This is the
one place the skill names a flag before the reference section, and it is
deliberate: a model that has just been told this is an interview skill is exactly
the model that might otherwise reach for the CLI's own prompts.

**Two rules govern when the interview does not run.** Do not ask what the user
has already said — if the opening message described the project, go straight to
the proposal. And if nobody answers, or the session has no human in it, generate
the Default Set with `--yes` and report what was assumed. The second rule keeps
the ADR-004 escape hatch reachable from inside the skill; the first is what stops
the interview from being an obstacle to a user who was already specific.

**Worked examples become answer-and-command pairs.** Each example leads with a
sentence a user might plausibly say and follows it with the command derived from
it. This teaches the mapping, which bare commands do not. The three coverage
cases the contract already requires — whole catalog, nothing at all, and a mixed
per-Category selection — are preserved as the sentences that produce them.

**Examples stay on one line.** The contract test extracts them by line and splits
them with shell-word semantics, where a trailing backslash is an escape rather
than a continuation. A wrapped example would break extraction, and the extractor
is not being changed to accommodate formatting.

**Scope stays at `init`, plus one pointer.** The skill gains a single statement
that it creates new projects only, that `check` and `upgrade` are the commands for
an existing generated project, and that `init` must never be aimed at one. Full
lifecycle coverage would require teaching drift-report interpretation and four
more exit codes — a document of its own, and scope FR-34 does not carry.

**The safety half survives unchanged.** Destination resolution, the refusal to
clear or retry into a non-empty target, the exit-code table, and post-generation
verification against the stamp are not weakened by the rewrite. They are what
makes the skill safe to hand a machine, and the interview changes what is
selected, never what is done with the result.

**Distribution is unchanged.** This repository, installable through the open
Agent Skills ecosystem, outside the generated overlay and outside the manifest
catalog, with no Claude plugin metadata (FR-24, D-2). The skill is English like
everything else dev-ready writes (ADR-016).

**No manifest change, no stamp change, no CLI change.** Nothing here adds a
Category, an item, a flag, or a recorded field, and the stamp stays at version 5
as the v0.10 plan requires. The skill is documentation about a contract that
Phases 1 through 3 already finished changing.

## Testing Decisions

A good test here asserts what the file promises a reader, not how it is worded.
**This spec opens no new seam.** All three seams the phase needs already exist in
`tests/unit/test_generate_skill.py`, which is both the prior art and the only
test file this phase touches.

**Identifier and example correctness, through the real parser and the real
manifest loader.** The existing assertions carry over unchanged in intent: every
documented Category, item, development-loop and Agent Target identifier equals the
live catalog's; every worked example parses through the genuine argument parser
and resolves through the genuine answer builder; every retired identifier still
fails with the expected error. These already prove two of the phase's three
acceptance criteria, which is why the phase adds so little.

**The identifier collector changes shape, and that is the only mechanical
consequence of the mapping decision.** It currently matches a single
`Current <label> ids:` line. With one line per item it collects the backticked
identifiers under the relevant heading instead. Same seam, same assertion, same
failure when the catalog gains an item.

**Standard-compliant agents gain the same guard as targets.** The skill's
documented standard-compliant list must equal the manifest's. Without this the
newly added list is the one piece of catalog data in the file with nothing
holding it to the catalog, and an agent moving between the two upstream lists at a
pin bump would leave the skill quietly wrong — the failure ADR-019 exists to make
impossible.

**Interview ordering, as two assertions at the existing text seam.** First, the
first `##` section of the body is the interview. Second, no selection flag —
`--categories`, the five per-Category item flags, `--agents`, `--development-loop`
— appears before it. `--yes` and `--dir` are deliberately exempt, because the
interview section itself must state the non-interactive invariant; a naive "no
flags before the interview" assertion would fail on the correct file, which is
why it is not written that way. Together these are the only automated evidence for
"the skill asks about the project before naming any flag", and without them the
phase's central claim has none.

**The not-in-catalog assertion stays.** The skill must not appear in the catalog,
in generated overlay content, or in the stamp inventory. It is unaffected by this
rewrite and is exactly the property a rewrite might accidentally break.

**Installation and public-documentation synchronisation stay as they are.** The
install command appears exactly once in the skill and once in each README. This
phase does not edit either README — Phase 6 owns all README work — so these
assertions are expected to pass untouched, and a failure means this phase strayed
outside its footprint.

Unit tests use `tmp_path` where they touch the filesystem at all, make no network
calls, and read only files inside the repository.

## Out of Scope

- **`check` and `upgrade` coverage.** One pointer line, no exit codes 6 through 9,
  no drift-report interpretation. FR-34 is the interview-driven *generation*
  skill.
- **Any change to the CLI.** No catalog-listing flag, no machine-readable
  identifier dump, no new prompt. `init --help` enumerates no item identifiers
  today and this spec does not change that; the skill carries the catalog instead.
- **All README work.** `README.md`, `README-pypi.md` and `README.zh-TW.md` belong
  to Phase 6, including the supported-agent count and the development-workflow
  section.
- **Manifest, stamp, and selection-surface changes.** No Category, no item, no
  flag, no recorded field, and no stamp version bump.
- **A second distributed skill.** The repository distributes exactly one
  [[Generation Skill]], which is why the glossary term is singular.
- **Claude plugin metadata or registry submission.** Settled by the 2026-07-25
  contract recorded at D-2 and unchanged here.
- **Splitting the skill into reference files.** Measured and rejected above;
  reopening it needs a file materially larger than 1.4k tokens.
- **Re-litigating the questionnaire shape.** A fixed per-Category question list
  is the CLI branching FR-34 and `docs/version-plan.md` explicitly reject;
  choosing it later means amending both.

## Further Notes

The phase ships nothing on its own — no user of dev-ready sees a difference until
they install or update the skill — and it must not absorb release work. That is
also why it is cheap: Phases 1 through 3 finished moving the contract, so this
phase changes one document and the test that guards it.

One thing the grilling produced that is worth keeping visible. `dev-ready check`
and `dev-ready upgrade` are documented only in *this repository's* README. A
generated project's own README never mentions them, so a developer holding a
generated project has no in-project pointer to its own lifecycle commands. That
is not FR-34's to fix — this spec adds the pointer to the skill, which reaches
only users whose agent has the skill installed — but the underlying gap belongs to
whoever next owns the generated README, and Phase 6 is the nearest owner.

The measurement that settled the file-layout question is worth recording because
it reversed the recommendation it was gathered to support. Progressive disclosure
is the default instinct for an Agent Skill, and it is the right instinct for the
vendored skills this project ships, several of which carry four or more reference
files. It is the wrong one here purely because of size, and the number — 225
tokens of identifiers inside a 1.4k-token file — is the whole argument. If the
catalog grows by an order of magnitude, the decision should be re-measured rather
than re-argued.
