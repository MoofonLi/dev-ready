# FR-42 — Engineering Flow Selection and the Interactive Rework

Status: Accepted by Moofon (2026-08-13)

Version: v0.11

Phase: 1 (shared with FR-44, which has its own spec and its own acceptance set)

Governing decisions: ADR-004, ADR-010, ADR-011, ADR-012 (as amended 2026-08-12),
ADR-014, ADR-016, ADR-017 (as amended 2026-08-12 and 2026-08-13), ADR-018 (with
its 2026-08-02 and 2026-08-03 amendments), ADR-021, ADR-024 (as amended
2026-08-13)

## Problem Statement

dev-ready asks a user how their project should be built, and almost none of the
asking works.

**The question that decides a project's development method has never been
asked.** The prompt that offers the Engineering Flow returns early whenever the
catalog declares one flow, and the catalog has always declared one. Every
project ever generated received a development method its owner was never shown
and cannot name. This is the question that matters most and it is the one
question the tool has never put to anyone.

**The first question in the flow changes nothing.** Accepting or declining the
Default Set produces byte-identical selections, because the Default Set declares
no Enhancements and there is one flow to resolve. A user weighs an answer,
answers it, and the two answers are the same answer. Worse, the two branches
*look* different — one says "defaults", the other opens a menu — so the user
believes a choice was made.

**One row of the Category menu is an option whose selection cannot matter.** Dev
is offered among the checkboxes and then added whether or not it was checked. It
holds no Enhancement; its only member is the flow itself, settled elsewhere. A
user who unchecks it gets it anyway, and nothing tells them so.

**A single flag silently selects the entire catalog and asks nothing.**
Measured against the shipped catalog of nine items: naming an Agent Target
selects all nine; naming one Security item selects all nine; naming the flow
selects all nine. In every case no prompt is asked at all. A user who narrows
one Category receives everything; a user who names their coding agent is never
shown a Category. The next phase in this version vendors the full design
reference set, at which point that same one-flag command selects over a hundred
items.

**The identifier that names a flow does not distinguish flows.** `spec-loop`
describes a property that every scheduled flow candidate shares — they are all
spec-driven — so as a name for *which* flow it discriminates nothing. Two more
flows are scheduled, and the identifier is in the flag contract and in every
project record, which makes it more expensive to change with each release.

Underneath four of these sits one shape: **a question that is presented as a
choice and is not one.** The flow question is skipped, the Default Set question
has one outcome, the Dev row has one outcome, and the flag path asks nothing
while appearing to accept a narrowing instruction.

## Solution

The Engineering Flow becomes the first question, asked of everyone, including
when the catalog offers exactly one flow. At n=1 its job is disclosure rather
than choice: a user who is never shown their project's development method does
not know their project has one. The flows scheduled but not yet shipped are
listed in that menu, marked as not yet available and genuinely unselectable, so
the axis reads as plural before the second flow exists.

The Default Set stops being a question and becomes what it is: the resolution
the non-interactive path uses. The Dev row leaves the Category menu, because the
Engineering Flow question *is* the Dev Category asked under its own name. The
remaining four Categories are walked one at a time, in a fixed order, nothing
pre-selected, and declining one is pressing Enter on it. This costs a minimal
user three keystrokes and guarantees every user is shown every Category once —
the outcome the previous version's correction was created to produce, arriving
one level up.

A flag answers only its own question. A Category nobody named resolves to the
Default Set rather than to everything, so narrowing one Category narrows the
selection instead of widening it past recognition. Naming an Agent Target
answers the Agent Target question and nothing else, so the flow and the four
Category questions are still asked; only the question the flag answered is
skipped.

The flow's identifier is renamed after its source, which is the axis that
distinguishes flows. Existing projects continue to resolve the retired
identifier from their project record forever — a record states a fact about a
project that already exists and cannot be re-typed. A user who types the retired
identifier on the command line is told it was renamed, because a typed value can
be corrected once and a silent acceptance would keep the dead name in
circulation indefinitely.

## User Stories

1. As a first-time user, I want to be asked which Engineering Flow my project uses, so that I know my project has a development method and can name it.
2. As a first-time user, I want that question asked even though there is only one answer, so that the flow is disclosed to me rather than assumed on my behalf.
3. As a user evaluating dev-ready, I want the flow's display name to read as a name rather than as an identifier, so that the menu tells me whose method I am adopting.
4. As a user, I want to see that more flows are coming, so that I understand the choice is a real axis and not a formality.
5. As a user, I want an unreleased flow to be impossible to select rather than selectable-and-then-rejected, so that the menu never offers me something it will refuse.
6. As a user, I want the unreleased entries to carry no version number, so that the menu does not make a promise the roadmap can break.
7. As a user pressing Enter through every prompt, I want exactly the Default Set, so that the fastest path stays the leanest path.
8. As a user pressing Enter through every prompt, I want to have been shown all four optional Categories on the way, so that I learn what exists without having to decline anything first.
9. As a user, I want each Category presented on its own, so that I can consider one kind of Enhancement at a time instead of reading one flat list.
10. As a user, I want nothing pre-selected in a Category, so that pressing Enter declines rather than accepts.
11. As a user who wants one Security item, I want to be asked about Quality, Design, and Token Optimize too, so that choosing something in one Category does not hide the others.
12. As a user, I want no question about which Categories to enter, so that I am not asked the same axis twice.
13. As a user, I want the pre-write confirmation to name the Engineering Flow I chose, so that I can see the most important answer before anything is written.
14. As a user, I want to be able to cancel at any prompt and have nothing written, so that abandoning the interview costs me nothing.
15. As a scripted caller, I want the non-interactive flag with no other flags to keep producing the Default Set, so that existing automation is unaffected.
16. As a scripted caller narrowing one Category, I want the Categories I did not name to resolve to the Default Set, so that asking for less gives me less.
17. As a scripted caller, I want the explicit whole-catalog selection to keep selecting everything, so that there is still one way to ask for all of it.
18. As a scripted caller naming a Category without naming its items, I want all of that Category's items, so that the shorthand I already use keeps working.
19. As a user naming only my coding agent, I want to still be asked the flow and the Category questions, so that naming my agent does not silently choose my project's contents.
20. As a user naming my coding agent, I want the Agent Target question skipped, so that I am not asked something I already answered on the command line.
21. As a scripted caller, I want the flow flag to have a name that matches what the prompt calls it, so that one concept has one word.
22. As a scripted caller with an existing command, I want the previous flag spelling to keep working forever, so that renaming the concept does not break anything I already wrote.
23. As a scripted caller typing the retired flow identifier, I want a failure that names the new identifier, so that I can fix my command without reading a changelog.
24. As a scripted caller typing an unreleased flow, I want a failure that says it is not yet available, so that I can tell it apart from a typo.
25. As a scripted caller typing a nonexistent flow, I want a failure that says the identifier is unknown, so that I can tell it apart from an unreleased one.
26. As a scripted caller passing the retired identifier as a Dev Enhancement, I want the existing retired-identifier failure, so that the two meanings of that string stay distinguishable.
27. As a user with a project generated by the previous release, I want it to upgrade without editing anything by hand, so that the rename costs me nothing.
28. As a user with such a project, I want the read-only inspection command to report it as clean, so that a rename in the tool is not reported as drift in my project.
29. As a user upgrading such a project, I want its record to come out naming the new identifier, so that the record and the tool agree from then on.
30. As a user who edited a managed file, I want upgrade to preserve my edit and report it, so that none of this overwrites my work.
31. As a maintainer, I want an unreleased flow to be unreachable by construction rather than by careful coding, so that no future change can leak one into a real project.
32. As a maintainer, I want the manifest to keep loading when unreleased flows are declared, so that announcing a flow cannot break the CLI.
33. As a maintainer, I want the retired-identifier resolution to live in exactly one place, so that the rule cannot drift between the commands that apply it.
34. As a maintainer, I want an all-Enter interactive run and the non-interactive default to produce identical project records, so that the two default paths cannot diverge.
35. As a maintainer, I want the cross-release gate to run from the previous release artifact, so that the rename is proven against a real published project rather than a fixture.
36. As a maintainer, I want the published CLI contract document to describe the prompts and defaults that actually run, so that the contract is not a description of the previous version.
37. As a maintainer, I want adding the next flow to be a data change plus assets, so that the second flow costs what this decision was made to make it cost.

## Implementation Decisions

**Cross-release baseline, first.** The end-to-end gate's baseline constant
advances to the previous release before any other work in this phase, as its own
unit of work, and stays one explicit reviewed constant. The released artifact it
installs must exist on the package index; a local build or a "latest" resolution
is never substituted. This ordering is deliberate: the gate is what proves the
retired-identifier resolution against a project a real released version
generated, and it must be measuring the right baseline before that resolution is
written.

**The flow identifier is renamed after its source.** The change reaches the
manifest catalog entry, the manifest Default Set, the overlay guard that decides
whether flow guidance is rendered, the retired-identifier failure message that
names the mandatory flow, and the template source directory that supplies the
flow's own configuration documents. The destination those documents are written
to is unchanged, so generated output is byte-identical apart from the guidance
the rename is meant to change. The source directory is renamed rather than left
alone because the next phase requires the per-flow document to be resolved *by
flow identifier* rather than by a hardcoded mapping, which a directory named
after the retired identifier cannot satisfy.

**The loader's retired-identifier exemption is deleted, not renamed.** It exists
only so the live catalog may declare an identifier that also appears in the
retired set. After the rename nothing declares the retired identifier, so the
exemption can never fire; renaming the string inside it is worse than deleting
it, because the new identifier is not a retired identifier at all. The retired
identifier itself stays in the retired set and keeps failing as a Dev
Enhancement identifier.

**Retired-identifier resolution is scoped to project records and lives in one
place.** The record-resolution module — already documented as the only place a
project record is resolved against the current catalog, and the only place
record-migration rules live — maps the retired identifier to the current one for
both the recorded skill set and the recorded flow field. The upgrade command
stops validating the raw record field against the catalog and validates the
resolved record instead, which restores that documented invariant rather than
adding a second copy of the rule. Without this, every project generated by the
previous release fails upgrade outright, and inspection silently stops examining
the flow's skills.

**Two modules reach around that seam, not one** — corrected during
implementation, after code review found the second. The upgrade command
validates the raw recorded flow field against the catalog. The inspection
command resolves its structural expectations through the resolved record and then
reads the raw record for its per-item pin comparison, so it reports the renamed
identifier as a removed catalog item on a project with nothing wrong with it.
Both stop. The resolution module grows the ability to answer *which items, with
which recorded pins, in identifiers the current catalog knows*, and inspection
consumes that rather than mapping identifiers itself — a consumer that takes the
identifiers from the seam and the rest from the raw record is exactly how one
rule acquires a second implementation, and then a third.

The command line is explicitly *not* covered: a typed retired identifier fails
with a message naming the current identifier. Four failures on the selection
surface must be mutually distinguishable — retired flow identifier, unreleased
flow, unknown flow identifier, and retired Dev Enhancement identifier — and this
is an acceptance criterion rather than an implementation detail, because two of
them concern the same string on two different flags.

**The flow flag gains a second spelling.** Both spellings are option strings on
one argument with one destination, both permanently accepted, and the shorter
one matching the concept's name is the documented spelling. The project record's
field name is unchanged: the record format does not advance in this version and
the field is not user-facing.

**Catalog Items gain a display name and a status.** The display name is
presentation only and falls back to the identifier when absent. The status field
has exactly one legal value and marks a flow announced but not shipped.

**The loader partitions on status, and this is a correctness requirement rather
than a structuring preference.** An entry carrying a status is parsed into a
separate announced-flows collection on the catalog and never enters the
component tuples, so every derived view — all items, item identifiers by
component, the component split, the identifiers in a Category, and the declared
flow identifiers — structurally cannot see it. Exactly two consumers read the
announced-flows collection: the flow prompt, and the failure path for a flow
flag naming one.

Declaring such an entry as an ordinary flow instead does not degrade gracefully;
it stops the tool. A flow declares its steps, an item declares the paths or
effects it materializes, and every mounted Enhancement's mount must name a step
of *every* declared flow — a strictness ADR-018 adopted deliberately so that
adding a flow which lacks a mounted step fails in front of the maintainer. An
announced flow has no steps and materializes nothing, so declaring it as a flow
fails all six declared mounts, and the bundled manifest then fails to load
before any command runs. Partitioning removes the entry from the population
those rules quantify over, which is why ADR-018's rule needs no exemption and is
recorded as unchanged.

The alternative — declaring them as ordinary flows and exempting them at each
site that consumes the declared-flow identifiers — is rejected on failure mode
rather than on effort: a missed exemption does not fail loudly, it generates a
project whose declared flow materializes nothing.

**The prompt protocol gains an unselectable-choice parameter on its
single-select operation.** This keeps the property at the injectable seam where
it can be asserted, rather than inside the concrete terminal implementation
where it cannot. An announced flow is rendered as a row the cursor skips, so
"cannot be selected" is literally true rather than enforced by rejecting an
answer the user was allowed to give. Every test double implementing the protocol
updates with it.

**The interactive sequence is rebuilt.** It becomes: project name, Engineering
Flow, then the four optional Categories in a fixed order each with its own item
list, then Agent Targets, then the pre-write confirmation. The Default Set
question and the branch it gated are deleted, since both branches produce
identical selections. The Category checkbox is deleted in full rather than
having its Dev row removed, because with no preceding filter there is nothing
for it to ask. The combined flat item list is replaced by the per-Category walk.
The single-flow early return is removed from the flow prompt.

The Dev Category identifier is unchanged in the manifest, in the Category flag,
and in every project record. Only the checkbox loses a row that could not
matter.

**Selected Categories are derived from the selected items.** With the Category
checkbox gone there is no answer to record, and nothing reads the recorded
Category list — the record-resolution module always re-derives it. Deriving also
makes an all-Enter interactive run and the non-interactive default produce
byte-identical project records, which is the parity the Default Set was
introduced to guarantee.

**A flag answers only its own question.** Two changes to the flag-to-intent
mapping. A Category unmentioned both by the Category flag and by its own item
flag resolves to the Default Set rather than to every item; the explicit
whole-catalog selection is unchanged, and a Category named without an item flag
still means all of that Category's items. And the Agent Target flag stops
marking the whole selection resolved, because it answers a different question:
which agent's native layout receives pointer artifacts, not what the project
contains.

That second change requires the partially-answered intent type to be able to
carry an Agent Target answer while leaving the catalog selection unanswered; it
is currently all-or-nothing. The consequence is named rather than discovered: a
non-interactive invocation given only the Agent Target flag and no
accept-defaults flag now fails asking for an interactive terminal, where it
previously succeeded by selecting everything. This repository's own continuous
integration passes only the accept-defaults flag and is unaffected, and the
real-users gate is unmet, so no external caller exists to break.

**The published CLI contract document is corrected** for the prompt sequence,
the documented flow-flag spelling with the older spelling noted as accepted, and
the default column of every per-Category flag — the documented default of "every
Category when another selection flag is supplied" is exactly the behaviour this
work removes. README material is not written here; the documentation phase owns
it. The distributed generation skill is not edited here; the phase that adds the
plugin manifests owns that file, so it is corrected once against settled text.

## Testing Decisions

A good test here asserts what a user or a caller can observe: which questions
were asked and in what order, which rows could be selected, the exit code and
message for a rejected flag, the resolved selection, the bytes of generated
guidance, and the outcome of upgrading a project a real released version
produced. Nothing here justifies reaching for an internal helper, and **no new
seam is introduced** — every change lands on a seam that already carries tests,
and the one protocol extension widens an existing seam rather than adding one.

**Prompt sequence and selectability** are tested through the answer-collection
entry point with an injected asker, the existing protocol that keeps prompts off
a real terminal. Prior art: the existing prompt tests already drive the full
sequence and assert both the questions asked and the resolved selection. New
coverage asserts the exact question order; that four Category prompts are issued
even when every one of them is declined; that the flow prompt is issued when the
catalog offers one selectable flow; that announced flows appear in that prompt's
choices and are marked unselectable; that nothing is pre-selected in a Category
prompt; and that an all-Enter run resolves to the Default Set.

**Flag handling, failure messages, and flag reach** are tested through the CLI
entry point by argument vector, asserting exit codes and messages. Prior art:
the existing CLI tests already assert invalid-argument exits for unknown and
retired identifiers. New coverage asserts that the four selection failures are
mutually distinguishable; that both flow-flag spellings reach the same
destination; that naming one Security item resolves to the Default Set plus that
item; that naming an Agent Target still reaches the prompts and skips only the
Agent Target question; that the explicit whole-catalog selection is unchanged;
and that the Dev Category identifier still parses and still resolves the flow.

**Catalog loading and the partition** are tested through both manifest entry
points — the bundled one and the parse-a-string one. Prior art: the existing
manifest tests use both. The single most valuable assertion in this group is a
regression that the **bundled** manifest still loads once announced flows are
declared, because the failure mode being guarded against is a CLI that cannot
start. Further coverage asserts that an announced flow appears in the
announced-flows collection and in none of the derived catalog views, that a
selectable entry materializing nothing is still rejected, and that declaring an
announced flow leaves every existing mount valid.

**Record resolution** is tested through the record-resolution type in both its
inspection and re-application views. Prior art: the tests for the identifiers
retired in earlier versions are the direct template. New coverage asserts that a
record naming the retired identifier resolves to the current flow in both views.

**Upgrade** is tested through the upgrade entry point against a constructed
project, asserting that a record naming the retired identifier upgrades and that
a record naming a genuinely unknown flow is still refused — the validation moved
between modules and must not have been weakened in transit.

**Inspection** is tested through the inspection entry point against a constructed
project whose record names the retired identifier, asserting that no removed-item
drift is reported for it, and that a record naming a genuinely absent item still
does report one. The negative half matters as much as the positive: the repair
must not turn the pin check into something that reports nothing.

The cross-release gate's allowed-drift list must **stop whitelisting removed-item
drift**, which is what let this defect pass unnoticed. It must **not** be
tightened to demand a clean pre-upgrade check: inspection reports overlay version
drift whenever the recorded version differs from the running one, so once the
release phase bumps the version an N-1 project legitimately reports drift, and a
gate demanding a clean result would fail in the release phase. The assertion is
about which drift may appear, never about the exit code.

**Generated guidance** is tested through the overlay content entry point,
asserting the rendered bytes for a selection resolving the renamed flow, and
their absence otherwise. Prior art: the existing overlay tests already assert
generated guidance byte-for-byte.

**Cross-release lifecycle** is tested by the existing end-to-end gate, advanced
to the previous release. It must assert that a project that release generated —
whose record names the retired identifier — upgrades without manual input, comes
out naming the current identifier, keeps its record format version, and that a
repeat upgrade is a no-op. This test requires network and stays behind the
existing marker; an environment without network reports it pending rather than
substituting an offline test.

**Distributed skill contract** needs no new test here, but it does need an edit
here, and an earlier draft of this spec got that wrong. The existing contract
test cross-checks the skill's documented identifiers against the live catalog, so
it fails the moment the catalog is renamed. The draft called that failure "the
specification for the edit a later phase makes" — which describes a suite left
red across three phases, contradicting the rule that every ticket and every phase
ends on a green suite.

The correction: the contract test makes that file a **dependency of the catalog**
rather than a description of it, so the phase that renames the identifier is the
phase that must correct the identifier facts. Exactly three are corrected — the
development-loop mapping entry, the worked example's flow value, and the sentence
naming which flow every generated project resolves. The sentence listing retired
Enhancement identifiers keeps naming the retired identifier, because it is still
one. Everything else in that file — the flag spellings, the announced flows and
their failure behaviour, and the chain — is settled later and edited later.

The general rule this establishes, which matters beyond this spec: **"one phase
owns one file" is only sound while no test binds that file to code another phase
changes.** Where a test does bind them, ownership follows the binding.

## Out of Scope

- Skill Delivery Mode and the retirement of Pointer Stubs. Accepted as ADR-025
  and targeted at the next version; nothing here creates a symbolic link, a
  junction, or a per-agent content copy.
- The second and third Engineering Flows themselves. This work declares them as
  announced and unselectable and vendors nothing for them; no assets, no steps,
  no paths.
- Flow recommendation. It cannot precede a second flow, and when it arrives it
  belongs to the existing generation skill's interview rather than to a new
  skill.
- The setup step at the head of the flow chain, the corrected chain guidance,
  and the per-flow document. All are the next phase's work; this phase
  deliberately leaves the chain sentence alone so it is written once, with the
  setup step already in it.
- The full design reference set and the notice propagation. Later phase; this
  work must not assume either, though it must not make either harder — the
  per-Category walk is what the enlarged Design Category will be presented
  through.
- The plugin manifests, and every part of the distributed generation skill except
  the three identifier facts the contract test binds to the catalog. The flag
  spellings it teaches, the announced flows and their failure behaviour, and the
  chain it describes are all corrected in the phase that owns that file, against
  settled text.
- Advancing the project record format. Nothing here adds, removes, or re-types a
  recorded field. A value inside an unchanged field is renamed and resolved
  through a mapping; that is not a format change. Work that finds itself
  proposing a format bump has found an error in this spec and must stop and say
  so.
- Renaming any other identifier. One value is renamed deliberately and paid for
  with a permanent mapping; the flow flag gains a spelling rather than losing
  one; nothing else changes name.
- Any new Category, any new runtime dependency, and any localization. The
  language boundary is unchanged: everything emitted and everything generated
  stays English.

## Further Notes

Four of the five defects share the shape the previous version's correction also
found: **a question presented as a choice that is not one.** The flow question
is skipped, the Default Set question has a single outcome, the Dev row has a
single outcome, and the flag path accepts a narrowing instruction while asking
nothing and widening the result. Each is repaired by making the question real
rather than by removing it — except the Default Set question, which is removed,
because the honest version of it has no second answer.

Two findings in this spec were produced by running the code rather than reading
it, and both would have shipped otherwise. The flag-reach measurement is the one
that changes scope: nothing in the phase plan mentioned it, and the next phase's
vendoring turns it from a nine-item surprise into a hundred-item one. The
announced-flow finding is the one that changes correctness: the phase plan's own
wording, implemented literally, produces a CLI that cannot start, and it fails
at manifest load rather than at the menu, so no amount of prompt testing would
have caught it.

The cross-release gate is the only test in this phase that can prove the thing
this phase most needs proven. Every other assertion is made against a catalog
and a record this repository constructs; only the gate asserts against a record
a published release actually wrote. It is also the reason the baseline rollover
is sequenced first rather than folded in.
