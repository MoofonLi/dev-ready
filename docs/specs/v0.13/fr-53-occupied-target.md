# FR-53 — Generation into an Occupied Target, and the forbidden-path rescope

Status: **Accepted** by Moofon (2026-08-29), by dispatching `to-tickets`
against it (ADR-021).

Version: v0.13

Phase: 3 (the whole phase; FR-53 is its only requirement)

Governing decision: **ADR-031** (`init` may generate into an occupied directory
when nothing collides at the top level), as amended **2026-08-29** — the
occupied failure window includes the post-move link step and its recovery must
be entry-wise, the collision comparison reads staging's own top level, `--dir`
resolves at the `cli` boundary, and the forbidden-path rescope covers all five
paths. **ADR-002** (pinned upstream, all-or-nothing generation) is the guarantee
this phase narrows in exactly one direction. **ADR-028** (Skill Links) owns the
post-move link step whose failure path this phase repairs. ADR-004
(non-interactive escape hatch), ADR-005, ADR-011, ADR-014, ADR-016, ADR-017,
ADR-019, ADR-021, ADR-022, ADR-023, ADR-024, ADR-026, ADR-027, ADR-029 and
ADR-030 remain binding. FR-51 shipped in Phase 2, so every screen this phase
touches is already in the frameless Static Screen idiom.

No new ADR is written for this phase — see Further Notes.

## Problem Statement

A developer starting a project does not start from nothing. They run
`mkdir my-app && cd my-app && git init`, or they clone the empty repository
they just created, or they have already opened the folder in their coding agent.
Then they run `dev-ready init`, and dev-ready refuses:

> target directory /Users/…/my-app is not empty — remove or rename it and retry.

The refusal fires on the ordinary case rather than the dangerous one. The
destination is non-empty by exactly one entry — `.git` — that dev-ready has no
intention of touching. The remedy dev-ready offers ("remove or rename it") is
advice to delete a repository. The developer's actual workaround is to generate
into a sibling directory and move the contents back by hand, which is precisely
the merge dev-ready refused to perform, done less safely.

A second defect compounds it, and was found in the same session. `.git` is
listed in `inspection.py`'s `FORBIDDEN_PATHS`, the loop applying it is ungated,
and `check` runs that inspection through `ProjectExpectation.lifecycle`. **A
developer who generates a project and then puts it under version control — the
first thing anyone does — fails `check` with exit 7**, and the message tells
them an upstream change reintroduced a template-repo leak and to file an issue
against dev-ready. Confirmed by direct call on 2026-08-22 against a directory
whose only entry is `.git`. This is a live defect in v0.12.0. It was offered as
a standalone v0.12.1 patch and declined (Moofon, 2026-08-23): accepting an
[[Occupied Target]] makes the false verdict the *normal* outcome rather than an
edge case, so the two ship together.

Neither problem is about safety. dev-ready is right to refuse to overwrite what
a user owns. It is wrong about what "occupied" implies.

## Solution

`init` accepts a destination that already holds content when **no top-level
entry of the destination shares a name with a top-level entry dev-ready is
about to create**. Comparison is at the top level only, and the entry set is
read from the fully assembled staging tree rather than predicted.

Any collision is exit 4 and names every colliding entry. dev-ready never
overwrites, merges into, or backs up an entry that was there first. A
destination that already holds `backend/` is refused rather than spliced.

`--dir .` is the spelling; no flag is added. The project name defaults to the
destination directory's name when the positional argument is omitted.

Into an absent or empty destination, generation is unchanged: one atomic
rename, and the destination is left exactly as it was found on any failure.
Into an [[Occupied Target]] it becomes a bounded sequence of atomic per-entry
moves. On failure, the entries dev-ready moved are moved back; if restoration
itself fails, the error names exactly which entries remain. **dev-ready moves
only what it created, including while restoring, and including after a Skill
Link failure** — the half of the failure window ADR-031 originally missed.

And `check` stops applying the forbidden-path rule, which belongs to
generation-time verification alone. `dev-ready check` on a generated project
under git exits 0.

## User Stories

### The destination

1. As a developer who has run `mkdir my-app && cd my-app && git init`, I want
   `dev-ready init --dir .` to succeed, so that I do not have to choose between
   deleting my repository and scaffolding somewhere else.
2. As that developer, I want the project to be named `my-app` without my typing
   it again, so that the directory I already named is the name dev-ready uses.
3. As a developer whose destination is empty, I want generation to behave
   exactly as it did before, so that a version upgrade changes nothing I relied
   on.
4. As a developer whose destination does not exist, I want dev-ready to create
   it and to leave nothing behind if generation fails, so that the guarantee I
   was given still holds.
5. As a developer whose destination holds an unrelated `notes/` directory, I
   want generation to proceed and `notes/` to be untouched, so that dev-ready
   only claims what it wrote.
6. As a developer whose destination holds a `README.md`, I want dev-ready to
   stop and name `README.md`, so that I know exactly which file is in the way.
7. As a developer whose destination holds several colliding entries, I want all
   of them named at once, so that I do not resolve them one failed run at a
   time.
8. As a developer whose destination holds a `docs/` directory whose contents are
   entirely unrelated to dev-ready's, I want dev-ready to refuse rather than
   merge into it, so that I never end up with a tree neither of us designed.
9. As a developer whose destination holds `.claude/` because I have been using
   Claude Code in this folder, I want to be told that `.claude` collides and
   what to do about it, so that I am not left guessing why a hidden directory
   blocked generation.
10. As a developer on macOS whose destination holds `Readme.md`, I want
    dev-ready to treat that as a collision with `README.md`, so that a
    case-insensitive filesystem does not silently overwrite my file.
11. As a developer whose destination is a file rather than a directory, I want
    the existing refusal unchanged, so that a typo in `--dir` is still caught.
12. As a developer, I want the pre-generation confirmation to tell me the
    destination already holds content and how much, so that I approve the run
    knowing what is there.

### Learning early

13. As a developer answering the interactive interview, I want a collision that
    dev-ready can already see to stop the run before any network call, so that
    I do not answer seven questions and wait through a fetch to be told
    `.claude` was in the way.
14. As a developer running `--yes`, I want the same early check, so that a
    scripted run fails fast for the same reason.
15. As a developer, I want the early check never to be the *reason* generation
    succeeds — I want the real check to run on the assembled tree — so that a
    gap in what dev-ready can predict never becomes a file it overwrites.

### Failure and recovery

16. As a developer whose generation fails part-way through moving entries into
    my occupied directory, I want everything dev-ready moved to be moved back,
    so that my directory is as I left it.
17. As that developer, I want my own pre-existing entries never to be moved,
    removed, or backed up — not even as part of recovery — so that dev-ready's
    failure cannot cost me anything.
18. As that developer, if restoration itself fails, I want the error to name
    every entry that remains, so that I can clean up by hand with a complete
    list rather than by comparing directories.
19. As a developer on a filesystem where Skill Link creation fails after the
    move succeeded, I want my pre-existing content to survive, so that a link
    failure is not data loss.
20. As a developer, I want a failure to leave whole entries or nothing —
    never a half-written file — so that anything left behind is recognisable
    and removable.
21. As a developer whose destination gains a colliding entry *during*
    generation, I want the run to fail with exit 4 and nothing moved, so that a
    race with my editor cannot overwrite a file.

### Naming

22. As a developer running `dev-ready init --dir .` in `my-app/`, I want the
    project named `my-app`, so that the obvious default is the one I get.
23. As a developer running `dev-ready init --dir ./My App`, I want to be
    prompted for a valid name rather than have one invented, so that dev-ready
    never silently renames my project.
24. As a scripted caller in that situation, I want exit 2 with a clear message,
    so that my CI fails loudly instead of producing a project under a name I
    did not choose.
25. As a developer who passes both a name and `--dir`, I want the name I passed
    to win, so that the explicit argument is never overridden by a default.
26. As a developer who passes neither, I want today's behaviour unchanged, so
    that `dev-ready init` alone does not suddenly start targeting my current
    directory.

### `check` under version control

27. As a developer who generated a project and ran `git init` in it, I want
    `dev-ready check` to exit 0, so that dev-ready does not report a defect in
    itself for something I did correctly.
28. As that developer, I want `check` to keep reporting every other kind of
    drift exactly as before, so that narrowing one rule does not blunt the
    command.
29. As a developer whose Occupied Target happened to contain a `copier.yml` of
    my own, I want `check` not to accuse dev-ready's pin of leaking a template
    repository, so that content I own is never read as dev-ready's fault.
30. As a maintainer, I want `verify` to keep rejecting a `.git` or a Copier
    artefact in staging, so that a genuine upstream leak still fails the run
    and the weekly bump PR.

### Documentation

31. As a developer reading `--help`, I want `.` named explicitly as a `--dir`
    value, so that I discover the spelling without a flag existing to teach it.
32. As a developer reading `docs/cli-spec.md`, I want the `--dir` row and the
    exit-4 description to describe what dev-ready now does, so that the
    contract document is not a version behind.
33. As an AI agent following the [[Generation Skill]], I want the destination
    safety rules to stop telling me a non-empty destination is refused, so that
    I do not talk a developer out of a run that would have worked.
34. As a reader of the repo's own `AGENTS.md`, I want the all-or-nothing rule
    stated in both its parts, so that an agent implementing here does not
    enforce a guarantee that no longer holds absolutely.

## Implementation Decisions

### The destination has three states, classified once

`_validate_target_dir`'s boolean return and the `restore_empty_target` boolean
threaded through finalize cannot express this phase. Both are replaced by one
value describing the destination as found: **absent**, **empty**, or
**occupied**, carrying the occupied case's pre-existing top-level names.

Classification happens once, in `generate`, before staging is created, and the
resulting value is what finalize and every recovery path read. A recovery path
that re-derives the destination's state from the filesystem after having already
moved things into it will read the wrong answer; carrying the value forbids
that by construction.

A destination that exists and is not a directory keeps today's refusal
unchanged.

### `--dir` resolves at the `cli` boundary

`--dir` resolves to an absolute path when parsed, so `Answers.target_dir` is
absolute on every path. It already is whenever `--dir` is omitted
(`Path.cwd() / name`), so the only behaviour change is for an explicitly-passed
relative path, which today is carried and displayed as typed.

This is not cosmetic. `--dir .` parses to a `Path` whose `.parent` is itself and
whose `.name` is empty, and staging is created in the destination's parent — so
without resolution the spelling ADR-031 chose would create staging **inside**
the destination, where it becomes a top-level entry of the directory being
classified, and the name default would have no directory name to read.

Consequences that follow and are accepted: the confirmation screen and the
generation report display the resolved absolute path; and the report's first
next step (`cd <destination>`) is **suppressed, with the remaining steps
renumbered, when the destination is the current working directory**, because
`cd .` is a null instruction and FR-51 just spent a phase on exactly this class
of defect.

### Collision comparison reads the assembled tree

The set of top-level entries dev-ready creates is **selection-dependent** —
Agent Targets mount `skills/`, `agent/` and `data/` at the top level among
others — so the authoritative comparison reads **staging's own top-level entries
after `_prune_empty_dirs`**, at finalize, after `verify` and before the first
move. A projection computed in parallel with the overlay would be a second
source of truth for the one comparison that must not be wrong.

Comparison is name equality at the top level, **case-folded where the
destination's filesystem is case-insensitive** and case-sensitive otherwise.
An undetected `Readme.md`/`README.md` pair is a clobber, not a cosmetic miss.

Collision is `TargetDirectoryError` (exit 4). One message names every colliding
entry, sorted, and carries the remedy — move the entry aside and merge it back
after generation. It does not suggest deletion.

**No per-entry exception is added, including for `.claude/`.** A destination
already holding `.claude/` is the most likely Occupied Target after `.git` and
is refused. An exception there is file-by-file merging under another name, into
precisely the directory ADR-028 made dev-ready's to own. Recorded in ADR-031's
2026-08-29 amendment so it is not re-litigated per ticket.

### The advisory preflight, and what it is not

`generate` exposes a preflight over `(answers, catalog)` that `cli` calls once —
after answers are resolved, before the confirmation screen, on both the
interactive and `--yes` paths. It classifies the destination and compares the
destination's top-level entries against the **overlay-projected** top-level
names. A collision raises exit 4 **before fetch**; it does not warn and
continue.

It lives on `generate`, not `cli`, because the module boundary table forbids
`cli` from containing generation logic; `projected_skill_link_pairs` is the
precedent for a projection `generate` consumes before the thing exists.

**The preflight can rule a collision in, never out.** Before fetch, dev-ready
knows the overlay's top-level names exactly and upstream's only partially —
`REQUIRED_UPSTREAM_PATHS` is a required subset, and upstream also ships
top-level entries it does not list. So the preflight is a fast-fail on what
dev-ready authoritatively knows it writes, and finalize is the check that
decides. Silence from the preflight is not a guarantee, and the spec says so
rather than letting a reader infer completeness from its existence.

Rejected: putting upstream's full top-level entry set in the manifest under an
ADR-023 drift guard. It would make the preflight complete, and it adds manifest
surface plus a CI guard to the only deep-code phase in this version to save a
developer one wasted generation in the rarer case.

### Finalize into an Occupied Target

An absent or empty destination keeps today's path exactly: revalidate, one
`Path.rename` of the staging project directory onto the destination, and the
empty destination recreated on failure.

An Occupied Target takes a different path. Staging's top-level entries are moved
in **one at a time in a deterministic order**, each move an atomic
same-filesystem rename. Order is fixed rather than incidental, because the
debris named to a user after a failure depends on it.

On failure part-way through, the entries already moved are moved **back into
staging**, which the existing `finally` block then removes — they are
dev-ready's content and are meant to die with the staging root. Pre-existing
entries are never moved, removed, or backed up, in either direction.

If a move-back fails, the restore loop **continues past the failure** and
collects every entry it could not restore. One exit-4 message names them all. A
half-restored, half-reported directory is the worst available outcome and
aborting on the first restore failure produces exactly that.

### The Skill Link failure path is inside the window

ADR-028 creates Skill Links *after* the rename, so the occupied failure window
has two halves. Today's recovery for the second half removes the destination
tree wholesale and recreates it if it had been empty. That is correct for an
absent or empty destination and is **data loss** into an Occupied Target.

The occupied path therefore recovers entry-wise from a link failure too: remove
the links created so far, then move back only the top-level entries dev-ready
moved in. Restoration failure reports what remains, as in the first half. The
existing exit code (4) and the manual-recovery warning shape are unchanged.

This is a defect the phase creates the moment the non-empty refusal is lifted,
which is why it is scoped here and recorded in ADR-031 rather than left to a
reviewer to notice.

### Project name from the destination directory

When `--dir` is given and the positional project name is omitted, the name
defaults to the resolved destination directory's name. It applies **only** in
that combination: `dev-ready init` with no arguments keeps today's behaviour and
does not begin targeting the current directory.

The default is applied before the existing "project name is required" guards on
both the `--yes` and interactive paths, and in one place rather than two.

A derived name that is valid is used without prompting; the confirmation screen
already discloses it. A derived name that is not valid is prompted for
interactively and is exit 2 non-interactively. It is never silently rewritten
into a valid one — `_slugify` continues to derive only the Compose stack label
from the accepted project name, as it does today.

### The forbidden-path rescope

`ProjectExpectation` gains a field saying whether the forbidden-path rule
applies. `ProjectExpectation.generation` sets it; `ProjectExpectation.lifecycle`
does not. `inspection` keeps one traversal and one policy-free issue list;
`verify` and `check` continue to differ only in the expectation they pass.

**All five paths leave `check`, not only `.git`.** Splitting the tuple to keep
the Copier entries under `check` was considered and rejected: an Occupied Target
may legitimately hold any of them, and after the move dev-ready cannot
distinguish its own leak from content that was there first. Keeping them would
reproduce the same false verdict against a user who owns the file.

The guard loses nothing real. The leak it exists to catch is created at fetch
and cannot appear later, and `verify` runs against staging, which by
construction never contains a destination's `.git`.

### Confirmation and report

The pre-generation confirmation gains one line when the destination is occupied,
naming the destination and how many pre-existing entries will be left in place.
The generation report says nothing about what was left alone: the report
describes what dev-ready wrote.

Both screens are already in FR-51's Static Screen idiom, so this phase writes
its new lines in that idiom and adds no rendering machinery.

### Documents

`docs/cli-spec.md`: the `--dir` row stops reading "must not exist or be empty";
the exit-4 description gains the collision case; the finalize paragraph states
the guarantee in both its parts.

`docs/architecture.md`: the `generate()` all-or-nothing note is stated in both
parts.

`skills/dev-ready/SKILL.md`: the destination safety rule stops claiming a
non-empty destination is refused, and the exit-4 line stops saying "including an
existing non-empty target". The skill is **not** given collision-detection logic
of its own — duplicating dev-ready's rule in prose that can go stale is the
exact failure FR-50 and FR-52 exist to fix.

`--help` for `--dir` names `.` explicitly. The name-default fact goes in the
spec's `--help` example rather than into the flag's one-line help; three facts
in one help line is one too many.

**No README changes.** Phase 6 owns every README and CHANGELOG edit, and FR-54's
rewrite absorbs this one.

The repo's own `AGENTS.md` hard rule was amended during `grill-with-docs`
(2026-08-29) and needs no further change here.

### The stamp stays at version 5

Nothing here adds, removes, or re-types a recorded field. An Occupied Target
leaves a tree indistinguishable from any other generated tree; pre-existing
entries are unmanaged files the inventory never claimed. `upgrade` needs no
change and gets none.

## Testing Decisions

A good test here asserts what a user or a calling command observes: the
destination's contents, the exit code, the error text's named entries, the
report's verdict. It does not assert how many renames happened or which private
helper ran. The one deliberate exception is the existing
`test_finalize_uses_directory_rename_without_copy_fallback`, which pins a
*guarantee* (no copy fallback) that has no other observable, and which this
phase must extend rather than weaken.

Five seams, four of them already in use. Unit tests only: `tmp_path`, no
network, no filesystem outside `tmp_path`.

### `generate()` — `tests/unit/test_generate.py`

The top seam for everything about the destination. Prior art is already here:
`fetch_snapshot` is monkeypatched to a fake, and
`test_finalize_failure_exposes_no_partial_target_and_restores_empty_state`
injects failure with `monkeypatch.setattr(Path, "rename", …)`. The same lever
drives a failure at a chosen point in the move sequence, and a second one drives
a failure of the move *back*.

Cases:

- absent destination — unchanged: single rename, and a failure leaves the
  destination absent;
- existing empty destination — unchanged: single rename, and a failure restores
  the empty directory;
- destination holding only `.git` — succeeds, and `.git` is untouched;
- destination holding a colliding `README.md` — exit 4, names `README.md`,
  nothing moved;
- destination holding several colliding entries — one error naming all of them;
- destination holding a non-colliding `notes/` — succeeds, `notes/` untouched
  and its contents unchanged;
- destination holding a `docs/` whose contents differ entirely — **collides**,
  because comparison is top-level;
- case-insensitive destination holding `Readme.md` — collides with `README.md`
  (skipped where the test filesystem is case-sensitive, detected rather than
  assumed from the platform);
- collision appearing during generation — exit 4 at finalize, nothing moved;
- mid-sequence move failure — every dev-ready entry gone, every pre-existing
  entry present and unchanged;
- mid-sequence move failure *plus* a failing move-back — exit 4 naming every
  unrestorable entry, and the restore loop asserted to have attempted all of
  them rather than stopping at the first;
- **Skill Link failure after a successful move into an Occupied Target** — the
  pre-existing entries survive, which is the assertion that would fail today;
- staging still adjacent to the destination, and still cleaned up, for the
  occupied case (extending the existing adjacency and no-leak tests).

### `inspect_project` — `tests/unit/test_inspection.py`

The forbidden-path rescope, asserted in both directions at the seam that owns
the rule: a tree containing `.git` produces no issue under the lifecycle
expectation and does produce one under the generation expectation. Repeated for
a Copier artefact, so "all five" is asserted rather than implied by `.git`
alone. `tests/unit/project_factory.py` builds the trees.

### `check_project` — `tests/unit/test_check.py`

The regression that motivated the fix, asserted as a verdict rather than as an
issue list: a generated project whose only extra entry is `.git` reports clean.
Paired with an assertion that an unrelated drift is still reported from the same
tree, so the narrowing is shown not to have blunted the command.

### `verify_project` — `tests/unit/test_verify.py`

`.git` in staging still fails generation with exit 5. This is the test that
stops a future simplification from deleting the rule instead of rescoping it.

### `main(argv)` — `tests/unit/test_cli.py`

Argument-level behaviour, with `generate` faked as the existing tests do:
`--dir .` resolves before anything reads it; name-from-directory for a valid and
an invalid directory name, interactively and not (exit 2 non-interactively); an
explicit positional name beating the default; `dev-ready init` with no arguments
behaving as before; and the preflight raising exit 4 before `fetch_snapshot` is
called, on both the `--yes` and interactive paths.

### `confirm_generation` — `tests/unit/test_prompts.py`

The occupied-destination disclosure line, through the injected `Asker` the
existing prompt tests already use.

### `render_report` — `tests/unit/test_report.py`

`cd` suppressed and steps renumbered when the destination is the cwd; present
and numbered from 1 otherwise. `render_report` stays pure and callable with no
terminal present (FR-51's constraint, unchanged).

### Skill assertions — `tests/unit/test_generate_skill.py`

The destination rule and the exit-4 line no longer claim a non-empty destination
is refused. Prior art is the assertion set FR-52 added, which exists because
prose on this file went false repeatedly.

### E2E

`tests/e2e/test_init_real.py` gains one network-marked case: generate into a
directory holding only `.git`, then run `check` on the result and assert exit 0.
It is the acceptance criterion end to end and the only place the real top-level
entry set is exercised. The N-1 cross-release gate is untouched.

## Out of Scope

- **Any README change.** Phase 6 owns `README.md` and `README.zh-TW.md`, and
  FR-54's rewrite absorbs this phase's.
- **A `--here` flag.** Rejected by ADR-031 as a second spelling of `--dir .`.
- **File-by-file or recursive collision comparison**, and any per-entry
  exception to top-level comparison, including for `.claude/`.
- **Merging, overwriting, or backing up a pre-existing entry**, under any flag.
- **`upgrade`.** Generating into an Occupied Target produces an ordinary
  generated tree beside unmanaged files; `upgrade` already handles that and gets
  no change.
- **A stamp version bump**, and any recording of occupancy or of pre-existing
  entries.
- **Making the preflight complete** by declaring upstream's top-level entry set
  in the manifest — considered and rejected above.
- **Removing the forbidden-path rule.** It is rescoped, not deleted.
- **Cross-filesystem support.** There is still no copy fallback; staging is
  still created beside the destination.
- **A fifth generation stage or a new exit code.**

## Further Notes

**No new ADR.** ADR-031 already governs this phase and was amended on 2026-08-29
with the four things the grilling found it had wrong or left open. `CONTEXT.md`
already defines [[Occupied Target]] and its entry is accurate as written.

**Two of this phase's decisions are corrections to ADR-031 itself**, not
elaborations of it, and a reviewer should treat them as binding: the link-step
failure path, and the all-five forbidden-path rescope. The first is data loss if
missed; the second reproduces the exact false verdict the phase exists to
remove.

**The guarantee is now stated in two parts everywhere it is claimed.** Into an
absent or empty destination it is unchanged and still tested. Into an Occupied
Target the failure state is always a set of whole entries and never a
half-written file, and it can in principle be non-empty. A document that states
only the first half is now wrong, which is why the repo's own `AGENTS.md`,
`docs/cli-spec.md`, and `docs/architecture.md` all change.

**This phase carries the version's only live defect.** The `check`-under-git
fix is not a refactor riding along with a feature; it is the reason a v0.12.1
was offered and declined. If the phase has to be cut down, that fix is the last
thing to go.

## Acceptance

- `mkdir app && cd app && git init && uvx dev-ready init --dir .` succeeds, and
  the project is named `app`;
- the same command in a directory containing `README.md` exits 4 and names
  `README.md`;
- the same command in a directory containing `.claude/` exits 4 and names
  `.claude`;
- `uvx dev-ready check` on a generated project under git exits 0;
- generation into an absent destination is still a single atomic rename, and a
  failure still leaves the destination absent;
- a failure part-way through an occupied-destination move — including a Skill
  Link failure after the move — leaves no dev-ready file behind and every
  pre-existing entry untouched, or names precisely those it could not remove;
- a collision dev-ready can predict is reported before any network call;
- `dev-ready init --help` names `.` as a `--dir` value.
