# FR-36 — Selection Reach and Overlay-Infrastructure Corrections

Status: Accepted by Moofon (2026-08-02)

Version: v0.10

Phase: unassigned (the v0.10 version plan is not yet cut)

Governing decisions: ADR-004, ADR-008, ADR-010, ADR-012 (amended by ADR-018), ADR-014, ADR-016, ADR-017, ADR-018 (with its two 2026-08-02 amendments)

## Problem Statement

v0.9 built a Category-first selection model and then put it behind a door that
the default path never opens.

**The menu is unreachable by anyone accepting defaults.** After offering the
Default Set, dev-ready asks a second question — whether to add Enhancements —
and that question defaults to no. A user who presses Enter through the prompts
therefore never sees a Category, never sees an item, and never learns the
catalog exists. The selection model is fully implemented and invisible to
exactly the user a guided path is for. Someone who wants only one design
reference has no way to discover that they can ask for one.

**Declining the default silently removes the project's own documentation.** The
architecture and requirements skeletons are written only when the user selects
something from the documentation grouping, and the only things in that grouping
are two opinionated visual design references. A user who takes the custom path
and wants no Stripe- or Linear-flavoured style guide receives no
`architecture` or `requirements` skeleton either, and the rules file quietly
drops its instruction to read the architecture document before structural
changes. Two facts with nothing to do with each other are controlled by one
switch, and the failure is silent: nothing reports the absence.

**One catalog entry is a choice with no wrong answer.** The post-generation
setup Enhancement is presented as a selectable item named as though it were a
group. It contains one vendored skill, configures two conventions, and is
marked so that it never loads into context on its own — an unselected copy
would have cost disk and nothing else. Offering it as a decision spends the
user's attention on a question whose answers do not differ in any way they can
observe, and its name invites a question — what is inside it? — whose only
honest answer is "nothing, it is the skill."

**The loop's Execution step was shipped and never announced.** v0.9's headline
change added the implement step precisely because the advertised cycle had a
missing middle. The step is vendored into every project. The generated rules
file — the one document every agent session loads, and the only place the loop
is described end to end — still names the pre-v0.9 chain and omits it. An agent
following the written guidance skips from ticket dispatch straight to
test-writing, which is the failure ADR-018 existed to fix. A skill on disk that
the guidance does not name is a skill that does not run.

## Solution

Accepting the default now leads into the menu rather than around it. The second
confirmation is removed: a user who accepts the Default Set is shown the
Categories immediately, with nothing pre-selected, and a single keystroke
carries them past it. The lean outcome is preserved and the catalog stops being
a secret. Declining the Default Set continues to open the same selection, so
both paths converge on one menu instead of two.

The project's own architecture and requirements skeletons stop being
selectable. They become Overlay Infrastructure — written unconditionally,
alongside the rules file, the project README, and the Spec Loop — and the
switch that used to gate them is deleted rather than repurposed. The reasoning
is the mandatory loop's own, applied one level down: the loop exists to produce
durable architecture and requirements documents, and a mandatory process may
not have optional outputs. The design references remain Enhancements, selected
on their own merits, which is what they always were.

The setup Enhancement stops being a selection and joins the always-generated
loop. It remains what it has always been — a way to change conventions that
already work — and generated content still never instructs a user to run it.
Its retirement carries one obligation: the generation-time substitution that
rewrote the loop's guidance when the Enhancement was absent must be deleted
with it, because that substitution keys on an identifier that will no longer
exist and would otherwise rewrite accurate references on every generation.

The generated loop guidance names every step it ships, implement included, so
the described cycle and the delivered cycle are the same cycle. The same
description is written up for prospective users: the repository README gains a
development-workflow section covering the loop a generated project receives —
what each step does and what it produces — aimed at someone deciding whether to
adopt dev-ready, rather than restating the internal process the repository's
own rules file already owns.

## User Stories

1. As a first-time user, I want the Categories to appear after I accept the defaults, so that I learn the catalog exists without having to decline something first.
2. As a first-time user, I want a single keystroke to carry me past the Category menu, so that accepting defaults stays as fast as it was.
3. As a user who wants one design reference, I want to reach it from the default path, so that I do not have to decline the Default Set to find out it is available.
4. As a user who declines the Default Set, I want my project's architecture and requirements skeletons anyway, so that choosing no visual style guide does not cost me my own documentation.
5. As a user who selects no Category at all, I want a project that still has the loop and the documents the loop writes into, so that the minimum project is coherent rather than merely small.
6. As a user reading the generated rules file, I want it to point at the architecture document, so that the instruction and the file it names are either both present or both absent — never mismatched.
7. As an agent working in a generated project, I want the loop guidance to name the implement step, so that I run the step that drives test-first development instead of skipping to the tests.
8. As an agent following the loop, I want the described chain to match the installed skills, so that I never look for a step that is absent or miss one that is present.
9. As a user, I want the post-generation setup skill present without having chosen it, so that I am not asked a question whose answers I cannot tell apart.
10. As a user, I want the loop's skills to keep their accurate references to the setup skill, so that guidance never tells me a skill is missing when it is installed.
11. As a user who liked the old behaviour, I want the setup skill to remain something I run deliberately, so that generation still produces a working project with no manual step.
12. As a CI pipeline, I want the non-interactive flag to keep accepting the Default Set with no selection flags, so that the pinned-bump validation job keeps working unchanged.
13. As a scripted caller, I want the Category and item flags to behave exactly as before for every identifier that still exists, so that only the retired identifier changes my command.
14. As a scripted caller passing the retired setup identifier, I want a clear invalid-argument failure naming why it is gone, so that I can fix my command without reading a changelog.
15. As an agent driving generation, I want the distributed generation skill's documented identifiers to match the live catalog, so that I never compose a command containing an identifier the CLI rejects.
16. As a user upgrading a v0.9 project, I want the retired setup identifier in my project record to be migrated rather than rejected, so that my project upgrades without manual editing.
17. As a user upgrading a project that never selected the setup Enhancement, I want the skill to arrive as part of the loop, so that upgrade delivers the same content as fresh generation.
18. As a user upgrading, I want the architecture and requirements skeletons to arrive if my project lacks them, so that the correction reaches existing projects and not only new ones.
19. As a user who edited a managed file, I want upgrade to preserve my edit and report the divergence, so that none of these corrections overwrite my work.
20. As a user running the read-only inspection command, I want it to report the corrected expectations, so that inspection and upgrade agree about what a current project should contain.
21. As a prospective user reading the README, I want the development workflow described step by step, so that I can judge what I would be adopting before running anything.
22. As a prospective user, I want the README's workflow section to describe the loop my generated project receives, so that I am not reading about how dev-ready itself is maintained.
23. As a Traditional Chinese reader, I want the overview README corrected where it describes what a default project contains, so that its product facts stay true.
24. As a Traditional Chinese reader, I want that README to stay an overview, so that it does not accumulate flags and exit codes it deliberately omits.
25. As a maintainer, I want the deleted selection field to be gone from the core selection model rather than left inert, so that no future change re-derives a meaning for it.
26. As a maintainer, I want the CLI contract document to describe the prompt sequence that actually runs, so that the published contract is not a description of the previous version.
27. As a maintainer, I want the cross-release lifecycle gate to run from the v0.9 release artifact, so that the setup identifier's migration is proven against a real published project rather than a fixture.

## Implementation Decisions

**Prompt collection.** The Enhancement confirmation is removed from the
interactive sequence. Accepting the Default Set resolves the development loop
from the manifest as it does today, then proceeds directly to Category
selection and item selection, layering whatever is chosen onto the Default Set.
Declining continues to run the same selection, preceded by the development-loop
single-select when the manifest offers more than one loop. The two paths differ
only in their starting selection, not in the questions asked. Agent Target
selection and the pre-write confirmation summary are unchanged.

**Prompt default state.** The multi-select prompt currently pre-selects every
choice, and the asker protocol offers no way to say otherwise, so "shown the
Categories with nothing pre-selected" is not expressible today. Without this,
removing the Enhancement confirmation would produce the opposite of its
purpose: a user pressing Enter would receive the entire catalog rather than the
lean default. The protocol therefore gains an explicit initial-state parameter
on its multi-select operation, with **no default value**, so every call site
must state which behaviour it wants. Category and item selection ask for
nothing pre-selected. Agent Target selection keeps everything pre-selected,
which is right while the map is small and becomes a decision to revisit when
FR-33 enlarges it — the parameter is what makes that decision visible rather
than inherited.

This also corrects a defect the shipped custom path already has: declining the
Default Set and pressing Enter throughout currently yields every Category and
every item, so the fastest route through the tool still produces the heaviest
project — the outcome FR-31 retired the catalog cap to prevent.

**Selection model.** The boolean recording documentation inclusion is deleted
from the canonical selection type. Inclusion of the documentation grouping is
derived from whether any of its items are selected, matching how the skills and
MCP groupings already behave, so the type stops being able to express a
contradiction between the boolean and the item set. Every construction path —
interactive, flag-driven, Default Set, and project-record reconstruction —
loses the parameter rather than passing a constant.

**Overlay infrastructure.** The documentation skeletons move to unconditional
resolution. The helper that returned them conditionally loses its parameter and
collapses into the overlay content builder, because a function whose result no
longer varies is not a seam. The rules-file guidance pointing at the
architecture document becomes unconditional for the same reason.

**Catalog data.** The setup Enhancement's identifier is removed from the
manifest catalog and its vendored path moves into the development loop's own
path list and step list. The vendored provenance entry is untouched: the same
upstream repository, commit, and source path continue to supply the same bytes
to the same destination, so the byte-equality drift guard and the third-party
notices remain correct without modification.

**Retired-identifier migration.** The identifier joins the existing retired-set
constant, which already produces both the flag-level rejection and the
project-record migration behaviour. The existing rejection message states that
the named identifiers are now part of the mandatory development loop; that
sentence is true of this identifier, so the message is reused rather than
special-cased.

**Generation-time substitution.** The substitution table and the function that
applies it are deleted outright. Their guard tests for the presence of the
retired identifier in the selection, so leaving them in place after the
identifier is removed would invert their behaviour — rewriting on every
generation the references that are now always accurate. This is a deletion, not
a rewrite: the vendored wording is correct as written once the skill is always
present.

**Generated loop guidance.** The chain in the rules-file guidance is corrected
to name the implement step in its execution position, between ticket dispatch
and the steps implement delegates to. The delegated steps continue to be named,
because agents invoke them directly for narrow tasks.

**Project-record compatibility.** Deleting the selection boolean reaches the
project record, which persists the same flag, so the two are separated rather
than deleted together. The record keeps parsing the flag, because a project
stamped before the record began listing individual documentation items has no
other way to say what it received. Writing the flag becomes derived from
whether any documentation item is selected, which narrows its meaning to "a
design reference was chosen" for every record written from now on. No record
version bump is needed: the key remains present with the same type, and the
only consumer that still reads it — reconstruction of pre-item-listing records
— is unaffected by the narrowing, because records from that era predate
individually selectable documentation items entirely.

**Structural inspection.** The check that a project has a documentation
directory stops being conditional on the recorded selection and becomes
unconditional, matching the skeletons' new status as infrastructure. A project
that has lost its documentation directory is now drift regardless of what it
selected, which is a strengthening the previous coupling made impossible to
express.

**Documentation.** The CLI contract's prompt-sequence description, the README's
flag table and workflow material, and the distributed generation skill's
documented identifiers and examples are brought into agreement with the above.
The Traditional Chinese overview is edited only where its stated product facts
change — specifically its description of what a project receives by default —
and gains nothing else.

## Testing Decisions

A good test here asserts what a user or a caller can observe: the questions
asked, the files present in a generated project, the bytes of generated
guidance, the exit code and message for a rejected flag, and the outcome of
upgrading a real released project. None of these changes justifies a test that
reaches for an internal helper, and no new seam is introduced — every change
lands on a seam that already carries tests.

**Prompt sequence** is tested through the answer-collection entry point with an
injected asker, the existing protocol that keeps prompts off a real terminal.
Prior art: the current prompt tests already drive the full sequence and assert
both the questions asked and the resolved selection. New coverage asserts that
accepting the Default Set reaches Category selection directly, that an empty
Category selection yields the Default Set unchanged, and that the declined path
still reaches the same selection.

**Generated content** is tested through the overlay application entry point
against a temporary directory, then by reading the resulting files. Prior art:
the existing overlay tests already assert the presence of the architecture
skeleton, the content of the rules file, and the one-line pointer files. New
coverage asserts the skeletons exist for a selection containing no
documentation items, that the loop guidance names the implement step, and that
the loop's skills retain their references to the setup skill.

**Flag handling and retirement** are tested through the CLI entry point by
argument vector, asserting exit codes and messages. Prior art: the existing CLI
tests already assert the invalid-argument exit for unknown and retired
identifiers. New coverage asserts the retired setup identifier is rejected with
the retired-identifier message and that the Dev Category accepts an empty
selection.

**Project-record migration** is tested through the record-resolution type in
both its inspection and re-application views, and through the upgrade entry
point against a constructed project. Prior art: the existing tests for the four
identifiers retired in v0.9 are the direct template.

**Cross-release lifecycle** is tested by the existing end-to-end gate, advanced
to run from the v0.9 release artifact. It must assert that a v0.9 project
carrying the setup identifier upgrades without manual input, that the skill
arrives through the loop, that the documentation skeletons arrive if absent,
and that a repeat upgrade is a no-op. This test requires network and stays
behind the existing marker.

**Distributed skill contract** needs no new test: the existing contract test
cross-checks the skill's documented identifiers against the live catalog and
will fail on the stale identifier as soon as the catalog changes. That failure
is the specification for the edit.

## Out of Scope

- Mount Points (FR-32), the Agent Target Map (FR-33), and the interview-driven
  generation skill (FR-34). FR-36 must land before FR-34, which should be
  written against the corrected contract.
- Adding a GitHub MCP catalog item and integrating headroom. Both were decided
  in the same session and are recorded as catalog candidates with open
  blockers; neither ships here.
- Forking the vendored setup skill, renaming its directory, or extending it to
  configure MCP servers. MCP configuration is written at generation time; a
  skill that edited it after generation would mark the file user-modified and
  exclude it from upgrade permanently.
- Changing what the non-interactive flag means, removing it, or removing the
  Default Set. The flag remains the escape hatch ADR-004 requires, and the
  Default Set remains the manifest-declared lean selection it resolves to.
- Any new Category, catalog item, or command-line flag. FR-36 removes one
  identifier and one prompt and adds neither.
- A measured context budget to replace the Default Set limit. Still deferred
  for want of calibration data.

## Further Notes

The four defects were found by grilling the shipped v0.9 surface rather than by
a bug report, and three of them share a shape: a value that means two things at
once. One boolean meant both "the user picked a design reference" and "write
the project's documentation skeletons." One identifier meant both "install a
skill" and "leave the loop's guidance as written." One prompt's default meant
both "keep it lean" and "hide the menu." Each correction separates the two
meanings rather than choosing between them.

The deletion of the generation-time substitution is the one place where doing
half the work is worse than doing none: removing the catalog identifier while
leaving the substitution in place would silently strip correct guidance from
every generated project, and no existing test would catch it, because the
substitution's current tests exercise the path where the identifier is absent —
which becomes the only path. The ticket that removes the identifier must remove
the substitution in the same change.

The Traditional Chinese overview currently describes the Default Set as the
Spec Loop plus the project's own architecture and requirements skeletons. That
is a product fact and it changes, so ADR-016's rule requires the edit. Nothing
else in that file changes.
