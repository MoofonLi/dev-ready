# FR-45 — Plugin distribution for Claude Code and Codex

Status: Accepted by Moofon (2026-08-17)

Version: v0.11

Phase: 4 (the whole phase; FR-45 is its only requirement)

Governing decisions: **ADR-027** (the repository is the plugin — a manifest
describes, a catalog publishes, a directory sells) governs the shape. ADR-003 as
amended 2026-08-12 (distribution via `uvx`, and npx rejected as a channel),
ADR-009 (vendored provenance), ADR-011 (paths, and the gitignored handoff tree),
ADR-015 (Agent Targets, and the standing exposure of transcribed external
paths), ADR-016 (language), ADR-021 (process), and ADR-024 as amended 2026-08-13
(`--flow` is the documented spelling; an [[Announced Flow]] is partitioned out of
the catalog) are binding. ADR-025 targets v0.12 and nothing here implements it.

---

## Problem Statement

**dev-ready cannot be found by anyone who has not already been told about it.**

The [[Generation Skill]] installs today through the cross-agent installer,
`npx skills add MoofonLi/dev-ready --skill dev-ready`, which reaches Claude,
Codex, and roughly seventy other agents from this repository's own source. That
command works, and it is the documented primary channel. But every route to it
begins with someone already knowing the string `MoofonLi/dev-ready`.

That gap is now the binding constraint on the project. The 2026-08-09 amendment
left the v1.0 real-users gate deciding on Branch A alone — three attributable
signals from independent external non-maintainer identities — so being found by
strangers is the only currency left, and there is currently no surface on which a
stranger could encounter dev-ready at all.

**The requirement as originally written does not close that gap, because it
collapses three different artifacts into one word.** FR-45 specified two files,
`.claude-plugin/plugin.json` and `.codex-plugin/plugin.json`, and called them
storefronts. Measured against both published specifications on 2026-08-17:

- A [[Plugin Manifest]] describes one plugin to one ecosystem. It publishes
  nothing and reaches nobody.
- A [[Marketplace Catalog]] is what an install command actually fetches. Claude
  Code's `/plugin marketplace add owner/repo` reads a catalog at the repository
  root; Codex's `codex plugin marketplace add owner/repo` reads one at a fixed
  path inside the repository. **Neither command has any other entry point into a
  repository.**
- A [[Plugin Directory]] is the browsable storefront the requirement is justified
  by, and it is entered only by submission and review.

A repository holding manifests alone therefore offers **no install command in
either ecosystem**. Shipping the original two files would have produced a phase
whose acceptance criteria passed and whose users could still do nothing, and
Phase 5's by-hand install verification could not have passed.

**A second belief, held during grilling, was also wrong and is corrected here
before it reaches any shipped document.** dev-ready ships one skill and no MCP
server, and it was claimed that this structurally excludes it from Codex's public
directory. Codex's submission specification says the opposite: a plugin may
contain skills, an MCP server, or both, and the requirements that made the
exclusion look real — a production server URL, domain verification, tool
annotations — are each conditional on the plugin containing MCP. A skills-only
plugin qualifies for both public directories.

## Solution

**dev-ready publishes itself as one plugin whose source is the repository
itself**, through two marketplace catalogs, and then submits that plugin to two
public directories by hand after the release is tagged.

From a user's point of view, three things become true.

*A Claude Code user who knows the name can install by name.* They add the
repository as a marketplace and install the plugin from it. The skill they get is
the same `SKILL.md` the cross-agent installer delivers, because both resolve to
one directory. Nothing is duplicated and nothing is forked.

*A Codex user gets the same thing through their own command*, against the same
repository and the same skill directory.

*A user who has never heard of dev-ready can eventually find it*, because the
plugin is submitted to Anthropic's community directory and to the universal
directory ChatGPT and Codex share. That last part is not a file. It is a form,
filled in by Moofon after the version is tagged, and it is the only part of this
requirement a repository cannot deliver on its own.

The cross-agent installer is unchanged and remains the documented primary
channel. Removing it would strand every agent without a storefront, which is most
of the seventy it reaches.

Alongside the distribution files, the Generation Skill itself is brought current
for the last time in this version: it teaches the `--flow` spelling, names the
two [[Announced Flow]] entries and what happens when an agent asks for one, and
describes the six-entry chain a generated project receives.

## User Stories

1. As a Claude Code user who read about dev-ready, I want to add the repository
   as a marketplace and install the plugin by name, so that I do not have to
   clone anything or learn a second installer.
2. As a Codex user, I want the same install path through my own agent's command,
   so that my choice of agent does not decide whether the tool is available to
   me.
3. As a developer who has never heard of dev-ready, I want it to appear in the
   plugin directory I already browse, so that I can find it without being told
   about it first.
4. As a user who installed through the plugin, I want the skill to be the same
   one the cross-agent installer delivers, so that documentation written for one
   channel is true for the other.
5. As a user of an agent neither ecosystem covers, I want the cross-agent
   installer to keep working exactly as it does, so that the new channels cost me
   nothing.
6. As a user who installed the plugin, I want it to contribute one skill and
   nothing else, so that adding it does not quietly give a repository I do not
   maintain the ability to run hooks or executables in my sessions.
7. As a user who installed an earlier version, I want a new dev-ready release to
   reach me, so that I am not silently pinned to the version I first installed.
8. As a maintainer, I want a forgotten version bump in a distribution file to
   fail the test suite, so that I find out at commit time rather than from a user
   who never received an update.
9. As a maintainer, I want a new top-level directory that would ship to every
   installed user to fail the test suite, so that I learn the repository root is
   a shipping surface at the moment I make it one, not afterwards.
10. As a maintainer, I want a change to the Codex catalog file to run CI, so that
    the guard protecting it is not blind to it.
11. As a maintainer, I want the two public names fixed deliberately and recorded,
    so that nobody renames them casually once installs exist.
12. As a maintainer, I want the submission test cases committed and derived from
    the skill, so that a resubmission for a later version does not start from
    nothing.
13. As a maintainer, I want a test to parse every command in those cases, so that
    a case naming a stale flag fails here rather than in someone else's review
    queue.
14. As a maintainer, I want the release procedure to name every file holding the
    version, so that the bump list and reality do not drift.
15. As a maintainer, I want the version to ship even if an external review has not
    finished, so that a release date is never handed to another organization.
16. As an agent installing dev-ready for a developer, I want the skill to teach
    one spelling of the Engineering Flow flag, so that I compose one command
    rather than choosing between synonyms.
17. As an agent, I want to know that two Engineering Flows are announced but
    unavailable, so that I do not compose a command that exits 2 and then guess a
    replacement.
18. As an agent, I want to know the exact failure message for each rejected flow
    value, so that I can report the cause instead of retrying.
19. As a developer being interviewed by the skill, I want to be told what
    development chain my project will receive, so that I know what I am choosing
    before the command runs.
20. As a future maintainer reading the repository cold, I want a decision record
    explaining why there are four distribution files and why the repository root
    is the plugin, so that I do not "simplify" it back to two.

## Implementation Decisions

### The distribution files

- **Four files, at the repository root.** Two manifests and two catalogs, one
  pair per ecosystem. All four resolve to the existing, unchanged
  `skills/dev-ready/` directory. **Neither manifest may fork the skill**, and no
  second copy of it may exist anywhere in the repository — a property the
  existing contract test already asserts from the other direction, by proving the
  skill is neither a [[Catalog Item]] nor part of a generated project's overlay.
- **Both catalogs declare the repository root as the plugin's source.** This is
  the decision everything else follows from. It is what allows one skill
  directory to serve every channel, and it is documented in both ecosystems as a
  supported pattern for a repository that publishes exactly one plugin.
- **The Codex source path resolves against the repository root, not against the
  catalog's own directory.** This was verified against a shipped third-party
  repository rather than inferred from prose, because getting it wrong produces a
  catalog that parses and installs nothing.
- **Field sets are transcribed from the published specifications, not from
  memory.** Claude's manifest requires only a name; its catalog requires a name,
  an owner with a name, and a plugin list whose entries each carry a name and a
  source. Codex's manifest requires a name, a version, and a description, and
  takes its skills location as a **path** rather than a list. Codex's catalog
  carries a name, a display-name interface block, and plugin entries of name,
  source, installation and authentication policy, and category. Optional metadata
  — description, author, licence, repository, homepage, keywords — is filled in
  on both sides because it is what a directory shows a stranger, which is the
  whole point of the requirement.
- **The Claude catalog entry scopes its skills to the one skill directory.**
  With a repository-root source, the paths an entry lists become the complete set
  for that entry, so a directory added beside `dev-ready` in future cannot ship
  through this channel. This is the narrow, structural half of the root-content
  guard below; it covers skills alone and is not a substitute for the test.

### Naming

- **`dev-ready` names the plugin and the marketplace in both ecosystems.** One
  public identifier across the repository, the published package, the skill, the
  plugin, and the marketplace. The name clears both ecosystems' constraints: it
  is not reserved, and it satisfies the character rules the desktop client
  applies when it syncs marketplaces.
- **The resulting namespace doubling is accepted, not worked around.** Claude
  prefixes a plugin's skills with the plugin name, so the skill is invoked
  explicitly as `dev-ready:dev-ready`. Renaming the skill directory would remove
  the doubling and break `--skill dev-ready`, which is the documented install
  argument and is asserted against the skill and both READMEs by the existing
  contract test. The doubling is also cheap in practice: the skill declares no
  flag disabling model invocation, so it is normally selected from its
  description rather than typed.
- **Both names are effectively permanent.** A user may register only one
  marketplace per name, and renaming a published plugin requires a rename map in
  the catalog to carry existing installs. This is recorded in ADR-027 so the cost
  is visible before anyone proposes a tidier name.

### Guards — three exposures, three answers

- ***Schema drift* is genuinely unguardable and stays a by-hand
  re-verification.** Both formats belong to other organizations and change
  without notice. No local test can know that a required field appeared last
  week. This is the standing exposure ADR-015 recorded for agent paths before
  FR-33 closed it, and the honest answer is to re-read both specifications at
  every bump. The requirement's original wording said exactly this, and it is
  right — about this third of the problem.
- ***Version drift* is guarded, and it is the sharpest of the three.** Claude
  pins an installed plugin to its declared version string and delivers an update
  only when that string changes; Codex requires the field outright, so omitting
  it is not available. A stale manifest therefore strands every installed user on
  the version they first installed, with no error and no symptom. A test asserts
  each manifest's declared version equals the package's own version.
- ***Repository-root content* is guarded, and it is the most dangerous.** Because
  the plugin root is the repository root, a future top-level directory that
  either ecosystem treats as a plugin component would ship to every installed
  user without a word — and two of those component types, event hooks and an
  executables directory, ship behaviour rather than text. A test asserts the
  repository root holds no such component but the skills directory, and that the
  skills directory holds exactly `dev-ready`.
- **The release procedure changes from two version files to four.** The `release`
  process skill currently records that the version lives in exactly two files and
  bumps exactly those. That statement becomes false in this phase, and the skill
  is corrected with it. The test above is what makes a missed bump loud; the
  skill is what stops the miss happening.
- **No CI job runs the ecosystem's own validator.** It would need that
  ecosystem's CLI installed as a global tool, which the version's standing
  constraints forbid tests to depend on. It stays a by-hand step in Phase 5,
  alongside the two installs.

### CI reach

- **The workflow's path filter narrows from the whole agent-configuration tree to
  its skills subtree**, in both the pull-request and the push block. Codex fixes
  its catalog path inside a tree this repository already excluded from CI, so the
  version guard would be blind to one of the four files it guards and a change
  touching only that file would run no job at all. The filter's intent — edits to
  this repository's own process skills do not need the test suite — survives the
  narrowing intact. The Claude side needs no change: glob matching is by whole
  path segment, so the Claude plugin directory never matched the exclusion for
  the Claude configuration directory.

### The submission material

- **The eight submission test cases are committed, and derived from the skill
  rather than invented.** Codex's submission requires at least five positive and
  three negative cases; a case is a user prompt paired with the behaviour a
  reviewer should observe. The positive cases come from the skill's worked
  examples and its interview rules. The negative cases come from refusals the
  skill already documents: aiming project creation at an existing project,
  a destination that exists and is not empty, and a retired flow value.
- **They live under the project's documentation, not beside the skill.** The
  cross-agent installer copies the whole skill folder into a user's skills
  directory, so a submission document placed there would ship to every install.
  The gitignored handoff tree is also excluded, because this document must
  survive the phase.
- **Submission is a human step taken after the release tag, and it is Phase 5's.**
  Claude's path is a form serving individual authors plus automated screening;
  Codex's additionally requires the submitter's individual identity verification
  and an organization role granting submission access. Claude pins an approved
  plugin to a commit and syncs its public catalog nightly, so submitting before
  the tag pins pre-release content. **Acceptance is that both submissions were
  made and their outcomes recorded — never that either was listed.** Neither
  organization states a review turnaround, and no version waits on another
  organization's queue.

### The Generation Skill, corrected once against settled text

- **The skill teaches `--flow` and mentions the older spelling nowhere.** ADR-024
  as amended made `--flow` the documented spelling and kept `--development-loop`
  permanently accepted; the alias stays documented for humans in the CLI
  specification. The skill composes commands for an agent, and it composes one
  spelling. Measured: the older spelling appears in **no generated project
  content** — only in the argument definition, the CLI specification, and the two
  READMEs, which Phase 5 owns.
- **The two Announced Flows are described in prose, never as entries in the
  flow mapping list.** The contract test binds that list by equality to the
  catalog's selectable flows, and an Announced Flow is deliberately not one — the
  loader partitions it out so the selection machinery cannot reach it. An entry
  for either in that list turns the suite red.
- **The skill teaches all three flow rejection outcomes and what to do about
  them**: the renamed value, the announced-but-unavailable value, and the unknown
  value. All three exit 2. The instruction is to surface the message and stop,
  which extends the rule the file already applies to unknown item ids rather than
  adding a new one.
- **The skill uses the glossary's user-facing vocabulary.** It currently calls
  the mandatory selection the *Spec Loop* and the *Dev development loop*. The
  glossary reserves *Spec Loop* for the method and [[Engineering Flow]] for what
  a user chooses, and ADR-024 made the flow question the user-facing form of the
  Dev Category. The skill's headings and prose follow the glossary.
- **The skill states the six-entry chain a generated project receives**, briefly,
  so the interviewing agent can tell a developer what they are choosing before
  the command runs. This is a sentence, not a section: the file is loaded by an
  external agent and context bloat is this project's first-listed risk.

## Testing Decisions

A good test here asserts what a stranger's machine receives, because every defect
in this requirement is of the same class: a file that parses, satisfies its own
schema, and delivers nothing. A test that checks the four files "are valid JSON"
would pass on the two-file version this spec exists to replace.

**One seam, and it already exists.** All of this work is tested through the
existing contract-test module for the repository-distributed Generation Skill.
That module's subject is how this repository distributes its one skill, and each
addition belongs to it: the manifests point at that skill, the root-content guard
protects what would ship beside it, the version guard keeps its distribution
current, and the submission cases describe its behaviour. No new test module and
no new seam are introduced. This is a deliberate judgement — the alternative,
a separate module for the distribution files, would split one subject across two
files and duplicate the manifest-loading fixture.

What that module asserts, added to what it already asserts:

1. **Resolution, not just validity.** All four files parse, and each declared
   skills location resolves to a directory containing the skill's own
   `SKILL.md`. Both catalogs' plugin sources resolve to the repository root.
2. **Version equality.** Each manifest's declared version equals the package's
   version. The test fails when either is left behind.
3. **Root content.** The repository root contains no directory or file either
   ecosystem treats as a plugin component, other than the skills directory, and
   that directory contains exactly `dev-ready`. The test fails when a component
   directory is added.
4. **The submission cases parse.** Every command in a positive case goes through
   the real argument parser and the real answer builder, reusing the loop the
   module already applies to the skill's worked examples. Negative cases describe
   refusals, have no command, and are not machine-checked.
5. **The skill's flag spelling and vocabulary.** The worked example uses `--flow`;
   the required-token list gains `--flow` and loses the older spelling; the
   interview-precedence test's flag list gains `--flow`. The flow mapping list
   still equals the catalog's selectable flows exactly, which is what proves the
   Announced Flows stayed out of it.

Prior art is the module itself: it already parses every documented command
through the real CLI, and already binds documented identifier sets to the live
catalog by equality. Both patterns are extended rather than invented. All tests
are unit tests, use temporary directories only, and make no network call.

Two acceptance criteria in this phase have **no automated assertion** and are
verified by hand in Phase 5: that the plugin installs through both ecosystems,
and that the ecosystem's own validator passes. This is stated plainly rather than
approximated with a weaker test.

## Out of Scope

- **The submissions themselves.** Both are Phase 5 steps taken by Moofon after
  the version is tagged. Phase 4 makes the repository submittable and writes the
  material a submission needs.
- **Being listed in either directory.** That is another organization's decision
  on another organization's schedule. No criterion in this version depends on it.
- **The READMEs.** Phase 5 owns all README work, including the plugin install
  paths, and writes it once over settled text. The Chinese overview gains no
  flags, no exit codes, and no chain detail.
- **Renaming the skill directory.** The namespace doubling is accepted; the
  directory name is the documented install argument.
- **Schema validation against a published JSON Schema.** The optional schema
  field is declared where an ecosystem supports it, for editors, but no test
  fetches or enforces it — that would be a network dependency guarding a document
  that changes without notice.
- **Any change to the cross-agent installer channel**, its command, or the pinned
  installer source.
- **Skill Delivery Mode.** ADR-025 is accepted and targets v0.12. Nothing here
  creates a symbolic link, a junction, or a per-agent content copy.
- **The generated project.** Nothing in this phase changes a byte any generated
  project receives. The distribution files describe this repository, not its
  output.
- **A second plugin.** The marketplace publishes exactly one.

## Further Notes

**The defect this phase found is the same shape as the ones the previous three
grilling sessions found, and the shape is worth naming.** In each case a planning
document described an external system accurately enough to sound right, and the
error only appeared when someone read the external system itself. Here the word
"storefront" did the damage: it is true of a directory, false of a manifest, and
the requirement used it for both. The general defence is the one this repository
already applies to upstream content — do not state a fact about someone else's
system without either measuring it or guarding it — and the part of this
requirement that cannot be guarded is exactly the part that must be re-measured
at every bump.

**The repository root becoming a shipping surface is a real cost, accepted for a
real reason.** The alternative was a subdirectory plugin, which fails on the one
property FR-45 requires: the only directory holding the skill is the skill's own,
so its manifest would ride into every user's skills directory through the
cross-agent installer, which copies the whole folder. Measured, the accepted cost
is 4.8 MB across 366 tracked files copied into the plugin cache once per
installed version, against roughly 15 MB of runtime dependencies the documented
install already pulls. The uncomfortable half of the cost is not the bytes; it is
that a future top-level directory ships silently, which is why the guard test
exists and why it is named in the version's standing constraints.

**Two of the three exposures were never unguardable, and the general lesson
generalises past this phase.** "This comes from a moving external specification"
is a statement about *one* of the things a transcribed file can get wrong. Which
fields exist is theirs; which values this repository wrote is its own. Version
drift and root content are both the second kind, and both are cheap to guard.

**The wrong claim about Codex is recorded rather than quietly dropped.** During
grilling it was asserted that a skills-only plugin structurally cannot enter
Codex's public directory, and Moofon challenged it against the published
specification. The claim was wrong: a plugin may contain skills, an MCP server,
or both, and the requirements that made the exclusion look real are conditional
on MCP. It reached no committed document. It is recorded here and in ADR-027
because the reasoning that produced it — inferring an ecosystem's capabilities
from what one installer consumes — is the same reasoning that produced the
earlier, also-wrong claim that Codex had no plugin format at all.
