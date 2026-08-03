# FR-33 — Agent Target Map

Status: Accepted by Moofon (2026-08-03)

Version: v0.10

Phase: 3

Governing decisions: ADR-002, ADR-004, ADR-009, ADR-010, ADR-014, ADR-015 (as amended 2026-07-27), ADR-016, ADR-017, ADR-018, ADR-019 (with its 2026-08-03 amendment)

## Problem Statement

dev-ready writes one canonical copy of every skill at the open-standard
location and then renders each selected Agent Target's native layout on top of
it. That machinery is complete and correct. It is fed by a table with two rows.

**Most agents are served by a table that does not mention them.** Measured
against the reference installer at the pinned commit, 76 agents are declared.
Nineteen read the open-standard location and need nothing from dev-ready beyond
what it already writes. The remaining **fifty-seven read a directory of their
own** — and dev-ready knows about two of them. A user of the other fifty-five
receives a project containing every skill they asked for, written to a path
their agent will never look at. Nothing fails, nothing is reported, and the
project simply does not work the way it appears to.

**The gap is data, and hand-filling it is the wrong instrument.** ADR-015 wrote
the hazard down when the table had two rows: per-agent paths are transcribed
from a moving upstream table with no byte-equality guard, so every declared
target must be re-verified by hand at bump time. That was a manageable debt at
two entries. At fifty-seven it is not a debt but a defect generator: a
mistyped directory writes a Pointer Stub somewhere no agent reads, produces no
error, and is caught by nothing.

**Absence is read as non-support, and dev-ready never corrects it.** The
nineteen standard-compliant agents are the ones dev-ready serves best — they
need no selection, no stub, and no configuration. A user of Cursor, Codex,
GitHub Copilot or Zed who looks for their agent finds no mention of it anywhere
in the tool and reasonably concludes it is unsupported. This is the exact
misreading that motivated ADR-019, and it gets worse, not better, once
fifty-seven other agents are listed by name and theirs still is not.

**The Agent Target default was inherited, not designed.** An absent selection
flag resolves to every declared target, and the interactive prompt pre-selects
every choice. With a two-row table that is invisible. With fifty-seven, a
default project — twelve loop skills, no Enhancements — grows from twenty-four
Pointer Stub files to **six hundred and eighty-four**, in a directory tree the
user did not ask for and mostly cannot use. The behaviour was never chosen; it
was the only sensible reading of "all" when "all" meant two.

**Two of the fifty-seven directories are shared, and the overlay treats that as
fatal.** Three project directories are each claimed by two agents. Selecting
both members of such a pair asks the overlay to write one destination twice,
which its collision check correctly refuses — so the naive enlargement makes
the all-targets selection abort, three times over, on a guard that is doing its
job.

## Solution

The Agent Target Map stops being written by a person. A maintainer script reads
the reference installer's machine-readable agent list at a manifest-pinned
commit and generates the map; a continuous-integration job re-runs the
derivation against that same pinned source and fails on any divergence. This is
the byte-equality drift mechanism dev-ready already applies to vendored skill
content, applied to a second kind of content — and it retires the
re-verify-by-hand obligation ADR-015 accepted rather than carrying it
fifty-seven-fold.

The reference installer joins the manifest's provenance section at a pinned
commit with its MIT grant, recorded in the third-party notices like every other
external source. It contributes no files: dev-ready derives data from it, it
does not vendor its code.

Agents that read the open-standard location are derived too, as a second list,
and are **never** Agent Targets — a target pointing at the canonical location
would write a Pointer Stub onto the very content it points to. That list exists
to be said out loud. The selection prompt and the generation report both name
those agents, so a user of one of them learns that their agent is fully
supported and needs no selection, rather than inferring the opposite from
silence. The generation report matters as much as the prompt, because the
non-interactive path never shows a prompt and its users are the likeliest to
draw the wrong conclusion.

Every agent with its own directory gets its own entry, including both members
of a shared-directory pair, so a user finds the agent they actually run rather
than a near-neighbour someone chose on their behalf. Writing the same
destination twice is prevented where the mapping from targets to paths already
lives, not by relaxing the overlay's collision check — that check is a real
guard against a real class of bug and stays exactly as strict as it is.

The default becomes a decision. An absent selection flag, the non-interactive
flag, and the interactive prompt all resolve to Claude Code — the only target
with a rules file and an MCP configuration, and already the fallback the
selection model falls back to when it has no catalog. Asking for every target
remains available and keeps its meaning; it is simply no longer what a user gets
without asking. The prompt pre-selects the same single target on both the
default and the custom branch, so the two routes that mean "give me the
defaults" continue to produce the same project.

The per-target description field is deleted rather than derived. Fifty of the
fifty-seven upstream display names are the identifier re-spelled, and the
destination directory carries the recognition the rest need. A field that
cannot be checked and mostly repeats its own key is the transcription risk in
miniature, and the honest fix is to not have it.

## User Stories

1. As a user of any of the fifty-seven agents with their own skills directory, I want Pointer Stubs written where my agent looks, so that the skills dev-ready installed are the skills my agent can actually run.
2. As a user of one of those agents, I want to find my agent by its own name in the selection list, so that I do not have to know which other agent happens to share my directory.
3. As a Qoder-CN user, I want to select `qoder-cn` rather than `qoder`, so that the tool reflects the product I actually run.
4. As a user who selects both agents of a shared-directory pair, I want one stub tree and a successful generation, so that a detail of upstream's data model is not my problem.
5. As a Cursor user, I want the tool to tell me my agent is already supported, so that I do not conclude from its absence that it is not.
6. As a Codex or GitHub Copilot user, I want that statement where I will actually see it, so that it reaches me whether I answered prompts or passed flags.
7. As a user of the non-interactive path, I want the generation report to name the standard-compliant agents, so that the one route with no prompts is not the one route with no explanation.
8. As a user who reads that note and tries to select a standard-compliant agent anyway, I want to be told specifically why it is not selectable, so that I learn the reason instead of reading a rejection.
9. As a user, I want a default project to contain artifacts for one agent rather than fifty-seven, so that generation produces a project I can read.
10. As a user accepting all defaults, I want a working Claude Code project, so that the documented quick path keeps working as documented.
11. As a user pressing Enter through every prompt, I want the same project the non-interactive flag would have produced, so that the two ways of accepting defaults do not disagree.
12. As a user who wants every target, I want the all-targets selection to still mean every declared target, so that the capability I had is not removed along with the default I did not want.
13. As a user who wants no native agent configuration at all, I want to select none and still receive Canonical Content, so that the standard-compliant agents I use are served with nothing extra written.
14. As a user choosing among fifty-seven entries, I want to type to narrow the list, so that finding my agent does not mean scrolling past fifty-six others.
15. As a user reading the selection list, I want each entry to show where it writes, so that I can recognise my agent by its directory when its identifier is unfamiliar.
16. As a user, I want nothing written outside the project directory, so that generating a project never touches my home directory or my global agent configuration.
17. As a user of an agent whose upstream entry names a global directory, I want that path discarded rather than honoured, so that a data field dev-ready parses cannot become a write it should not make.
18. As a user upgrading a project stamped with the two previously declared targets, I want it to resolve and upgrade unchanged, so that enlarging the map costs existing projects nothing.
19. As a user upgrading, I want my Claude Code project to keep the identifier it was stamped with, so that a rename upstream does not orphan the artifacts already in my project.
20. As a user whose selected agent leaves the upstream list one day, I want the existing removed-target reporting to tell me, so that the disappearance is visible rather than silent.
21. As a scripted caller, I want an unrecognised agent identifier to fail with a clear exit code, so that a typo stops the pipeline rather than silently producing a project missing a target.
22. As a scripted caller, I want that failure message to stay readable, so that a rejected identifier does not print fifty-seven valid ones at me.
23. As a continuous-integration pipeline, I want the non-interactive flag to keep producing a working project with no selection flags, so that the existing validation job keeps working unchanged.
24. As a maintainer, I want the agent map generated rather than typed, so that no entry in it depends on my having transcribed a path correctly.
25. As a maintainer, I want continuous integration to fail when the map and the pinned source disagree, so that drift is caught by a machine rather than by a user whose stubs went to the wrong directory.
26. As a maintainer, I want the derivation to break loudly when upstream changes the shape of its agent list, so that a refactor upstream produces an error rather than a corrupted map.
27. As a maintainer, I want the derivation to break loudly if the upstream identifier dev-ready renames ever disappears, so that a rename becomes a build failure rather than a silently dropped target.
28. As a maintainer, I want the derivation exercised offline against a fixture, so that the logic is covered by the ordinary test run and not only when the network job succeeds.
29. As a maintainer, I want the source the map derives from recorded with its commit and licence, so that the provenance rule holds for derived data as it does for copied files.
30. As a maintainer, I want no upstream file committed into this repository, so that the tree written into user projects does not acquire a TypeScript file and the published package does not ship one.
31. As a maintainer, I want the pinned source bumped through the existing monthly workflow, so that this map is maintained by the process that already maintains every other pin.
32. As a maintainer, I want a target that would write onto the canonical location rejected by construction, so that no upstream change can turn the canonical content into a pointer to itself.
33. As a maintainer, I want the overlay's destination-collision check left as strict as it is, so that the guard that caught this class of bug keeps catching the next one.

## Implementation Decisions

**Derived data, and what is derived.** Two structures come from the pinned
upstream agent list: the Agent Target Map, containing every agent whose
project-level skills directory is not the canonical location, and a second list
naming the agents whose directory *is* the canonical location. Only the skills
directory is derived per target. Rules-file and MCP-file paths have no upstream
source and remain hand-declared, populated for Claude Code alone. Global skill
directories are parsed and discarded — dev-ready writes only inside the target
project directory.

**The canonical location is excluded by construction, not by policy.** An agent
whose declared directory is the canonical skills root cannot be an Agent Target,
because its Pointer Stub path is the path Canonical Content already occupies.
The derivation partitions on exactly that condition, so the exclusion is a
property of the data rather than a rule someone must remember.

**Target identity is the agent identifier.** Every agent with its own directory
is declared, including both members of the three shared-directory pairs.
Collapsing a pair would require choosing which of two products to name, which
is the curated-subset judgment ADR-019 already refused.

**Duplicate destinations are resolved in the projection.** The module that maps
selected targets onto native paths becomes unique-by-destination-path: selecting
overlapping targets yields each destination once. This is the module that
already owns the target-to-path mapping and the only place that knows two
targets can collide. The overlay's destination-collision check is not relaxed,
because it guards a genuine invariant for every other write.

**One identifier is renamed, and the rename is declared.** Upstream's identifier
for Claude Code differs from the one dev-ready has used since v0.8, which is
recorded in every stamped project and in the selection flag contract. The
derivation carries one declared identifier rename and **fails** if the upstream
identifier it renames is absent. Deriving identifiers verbatim would make every
existing project report its target as removed and orphan the artifacts already
written at that target's paths, with no record migration available to repair it.
The other previously declared target matches upstream already.

**The per-target description is removed.** The field becomes nullable and
derived targets carry none. The selection prompt and the generation report
compose their lines from the identifier and the paths a target actually writes,
both of which are already available where those lines are rendered. This is a
schema change to the manifest's agent-target entries and reaches the generation
report, which reads the field today.

**Provenance without vendoring.** The reference installer is declared in the
manifest's vendored-provenance section with its repository, pinned commit and
MIT grant, and **no file paths** — a shape the provenance model already permits.
The third-party notices gain a corresponding section stating that this source
supplies derived data and that no files are copied from it. Committing a
snapshot was rejected: every vendored destination is required to resolve inside
the template tree that is written into user projects, so a snapshot would mean
either relaxing that constraint or publishing a TypeScript file inside the
Python package.

**The derivation script and its seam.** A maintainer script joins the existing
sync scripts, following their established shape: run it to regenerate, run it
with a check flag to verify. Its core is **one pure function taking the upstream
source text and returning both derived structures**. Cloning at the pinned
commit and comparing against the manifest sit above that function and are
exercised only by the network-marked job; the function itself is exercised
offline. The function raises rather than returns a partial result on any
unexpected upstream shape: a missing agent object, a non-literal or absent
skills directory, or the absence of the renamed identifier.

**Selection defaults.** An absent selection flag and the non-interactive flag
both resolve to Claude Code rather than to every declared target. The
all-targets and no-targets values keep their existing meanings. This is a
user-facing contract change and is recorded as such in the command-interface
document and in the release notes.

**Prompt behaviour.** The interactive Agent Target prompt pre-selects Claude
Code on both the default-accepting and the custom branch. FR-31 established
that an interactive user pressing Enter receives the same project as the
non-interactive flag, and that parity outranks symmetry with FR-36's
nothing-pre-selected rule, which exists to stop a single keystroke from
selecting an entire catalog rather than to forbid a default of one.

**Prompt presentation.** Type-to-filter is enabled on multi-select prompts
inside the single module permitted to touch the terminal library, which already
supports it at the pinned version. The prompt-asker protocol and its test double
are unchanged, because how a prompt is presented is terminal policy and belongs
in the module that owns terminal policy. The prompt's instruction text carries
the standard-compliant-agent statement.

**Rejection messages at the new scale.** The unknown-identifier failure
currently prints every valid identifier. At fifty-seven that is unreadable, so
the message stops enumerating them and directs the reader to the selection
prompt instead. A rejected identifier that names a **standard-compliant** agent
is a distinct case and gets a distinct message: that agent reads the canonical
location, needs no target, and is already supported. It remains an
invalid-argument failure rather than a silent no-op, because succeeding would
leave the user believing they had selected something.

**Manifest validation.** The loader accepts the enlarged target set and a null
description, and parses the standard-compliant list as a second declared
structure alongside it. The identifier pattern already accepts every upstream
identifier at the pinned commit; this was verified rather than assumed.

## Testing Decisions

A good test here asserts what a user, a caller, or a maintainer can observe: the
files present in a generated project and their paths, the questions asked and
what they pre-select, the exit code and message for a rejected flag, the lines
of the generation report, and whether the derivation refuses bad input. The
enlargement of a data table is not itself worth asserting fifty-seven times —
coverage takes a representative sample plus every edge the grilling identified.

**The derivation** is tested against fixture strings representing the upstream
source, offline, with no filesystem access beyond a temporary directory. This is
the phase's only new seam. Prior art: the existing vendored-sync and
notices-sync script tests, which load maintainer scripts by explicit path and
test their pure functions directly. Coverage: a well-formed fixture yields both
lists with the expected partition; a fixture whose agent object is missing,
whose skills directory is absent or not a literal, or which lacks the renamed
identifier, raises rather than returning a partial map.

**The projection** is tested through the existing target-projection module.
Prior art: its current tests construct synthetic targets and assert the paths
they produce. New coverage: two targets sharing a skills directory yield each
destination once, and targets with distinct directories are unaffected.

**Generated content** is tested through the overlay application entry point
against a temporary directory. Prior art: the existing overlay tests assert
Pointer Stub paths, rules-file pointers and MCP retargeting. New coverage: a
sample of newly declared targets produces stubs at their native paths and
nothing else; selecting both members of a shared-directory pair generates
successfully and produces one stub tree; nothing is written outside the project
directory.

**Prompt sequence** is tested through the answer-collection entry point with an
injected asker. Prior art: the existing prompt tests drive the full sequence and
assert both the questions asked and the resolved selection. New coverage: Claude
Code is pre-selected on both branches, an unchanged prompt yields exactly that
target, and the instruction text names the standard-compliant agents.

**Flag handling** is tested through the command-line entry point by argument
vector, asserting exit codes and messages. Prior art: the existing tests for
unknown and retired identifiers. New coverage: an absent flag resolves to Claude
Code, the all-targets and no-targets values keep their meanings, an unknown
identifier fails without enumerating the valid set, and a standard-compliant
identifier fails with its own message.

**The generation report** is tested through the existing report-rendering seam.
Prior art: its current tests assert the per-target artifact lines. New coverage:
the standard-compliant statement is present, and the target lines render
correctly with no description field.

**Manifest validation** is tested through the loader. Prior art: the existing
agent-target validation tests. New coverage: the enlarged set loads, a null
description is accepted, and the second derived list parses.

**Record compatibility** is tested through the record-resolution type and the
upgrade entry point. Prior art: the existing tests for previously declared
targets. New coverage: a project stamped with the two v0.8 identifiers resolves
and upgrades with no target reported as removed.

**Divergence between the manifest and the pinned upstream** is verified by a
network-marked continuous-integration job, not by a unit test. It stays behind
the existing network marker and never runs in the offline suite.

## Out of Scope

- Detecting which agents are installed on the user's machine. Upstream carries
  an installation probe per agent; using it would read outside the project
  directory and make one dev-ready version produce different output on different
  machines.
- Accepting user-supplied agent directories through the selection flag. A path
  given at the command line cannot be validated, cannot be drift-checked, and
  cannot be carried meaningfully through inspection and upgrade.
- Deriving rules-file or MCP-file paths. Neither exists in the upstream source;
  both stay hand-declared, and only Claude Code declares them.
- Populating an MCP file for any additional target. Where an agent's MCP
  configuration is user-global, dev-ready reports that rather than writing it.
- Bumping the pinned reference-installer commit after this phase. Bumps arrive
  through the existing monthly vendored-pin workflow.
- Any record-version change. Nothing here adds, removes or re-types a recorded
  field; the set of valid target identifiers grows and the way they are stored
  does not change.
- Symbolic links, per-agent content copies, or any alternative to Pointer Stubs.
  Re-examined and re-rejected in the v0.9 grilling; reopening needs a change in
  the underlying platform facts.
- The interview-driven generation skill (FR-34), which must be written against
  the enlarged target set this phase produces, and the tech-stack additions to
  the generated rules file (FR-37).
- All README work, including the supported-agent count. The release phase owns
  every README change.

## Further Notes

The measurement in ADR-019 was taken on 2026-07-27 and had already moved by the
time this phase began: 75 agents became 76, and "fifty-six with a unique project
directory" turned out to conflate two different counts — fifty-seven agents
occupying fifty-four distinct directories. The 2026-08-03 amendment to ADR-019
records the corrected shape. The lesson is not that the number changed but that
a number written by hand went stale within a week, which is the same argument
for deriving the table that the table itself makes.

Two of this phase's decisions exist only because the enlargement turns a
harmless property into a failure. Selecting every target and pre-selecting every
choice were both correct at two rows; at fifty-seven the first aborts generation
on a shared directory and the second writes six hundred and eighty-four files
nobody asked for. Neither was a bug before. This is the recurring shape of the
phase: nothing here is broken, and several things stop working once the data is
honest.

The rejection-message change and the specific message for a standard-compliant
identifier were not settled in the grilling session; they follow from the
enlargement rather than from a decision, and are noted here so they can be
struck at acceptance if they are considered scope creep. Both are small, and
both address a failure a user meets at the moment they act on the very note this
phase adds.

The one thing this phase must not do is soften the overlay's
destination-collision check to accommodate shared directories. That check is
what surfaced the problem in the first place, and it guards every other write in
the overlay. The duplication is resolved where target paths are decided, before
the overlay ever sees two writes to one destination.
