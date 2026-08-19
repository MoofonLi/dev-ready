# FR-46 — Skill Links replace Pointer Stubs

Status: Accepted by Moofon (2026-08-19)

Version: v0.12

Phase: 1 (the whole phase; FR-46 is its only requirement)

Governing decisions: **ADR-028** (one [[Skill Link]] per skill, no copy mode,
and no [[Pointer Stub]]) governs the feature. ADR-002 (pinned generation),
ADR-004 (all-or-nothing generation), ADR-009 (provenance), ADR-011 (canonical
paths), ADR-014 (truthful overlay lifecycle state), ADR-015 (the [[Agent Target]]
map and [[Canonical Content]]), ADR-016 (English authored surfaces), ADR-019
(the drift-guarded Agent Target Map), ADR-021 (the Spec Loop), ADR-026
(`setup-project` is unconditional infrastructure collected before projection),
and ADR-027 (the repository root is a shipping surface) remain binding.
ADR-025 is superseded in full and implements nothing.

---

## Problem Statement

dev-ready writes every selected skill once as Canonical Content and then exposes
it to each selected Agent Target through a generated Pointer Stub. The stub is a
second instruction file that tells an agent where the real skill lives. It is
not the real skill, so delivery depends on each agent interpreting the pointer
convention correctly, and every skill earns one extra managed file per target.
The unconditional `setup-project` skill carries the same cost even though it is
not a Catalog Item.

The replacement first proposed for v0.12 was a user choice between links and
copies. Measurement invalidated that design. A Windows junction works without
Developer Mode or elevation, Claude Code discovers skills through both junctions
and POSIX symbolic links, and creating the largest projected set is fast enough
for generation. A copy mode would therefore preserve duplicate content, add a
prompt and flag, and make the same dev-ready version produce two materially
different project layouts without buying a needed compatibility path.

Links introduce lifecycle problems that ordinary generated files do not have.
Git follows a Windows junction and stages duplicate blobs unless the link is
ignored. A junction contains an absolute target and breaks when a project moves.
A fresh clone contains neither ignored symbolic links nor ignored junctions.
An existing v0.11 project already has real directories at the desired link paths,
and a directly upgraded v0.3 project may hold complete copied skills there. Some
of those files may have been edited by the user. A missing, stale, redirected,
or broken link is derived state and cannot safely be treated like an inventoried
file, while a user-controlled link in a parent path must never be traversed.

Generation also writes to a staging directory and atomically renames it into
place. A Windows junction cannot target Canonical Content before that content
exists and cannot be created in staging with the final destination as its target.
Creating links only after the rename introduces a failure point after the
nominal atomic commit. Unless verification, finalization, upgrade, rollback,
inspection, and Git exclusion share one explicit contract, v0.12 could leave a
half-generated project, expose duplicate skill content to Git, delete edited
legacy content, or stamp a transaction that did not finish.

## Solution

Every selected Agent Target receives one Skill Link per canonical skill. On
macOS and Linux the link is a relative directory symbolic link. On Windows it is
an elevation-free directory junction. Each link resolves directly to the
corresponding real skill directory under Canonical Content. There is no copy
mode, Pointer Stub, prompt, flag, fallback, or new stamp field.

Each Agent Target's real skills directory contains a generated nested
`.gitignore` that names its machine-local links and tells a collaborator to run
`uvx dev-ready upgrade` after cloning. That managed file is both the Git safety
gate for current links and the ownership anchor from which a later release can
identify stale derived links. The links themselves are never committed and
never inventoried. A freshly cloned project retains Canonical Content and the
anchor, and one upgrade reconstructs the links.

Generation proves the complete projected link set during verification by using
the production link writer inside staging, inspecting the result, and removing
the temporary links. Finalize atomically renames staging into place and then
recreates the same links against their final targets. A link failure restores
the exact pre-generation target state. Projects selecting no Agent Target
project no links, perform no link capability probe, and continue to work on a
filesystem without link support.

Inspection provides one classification of Canonical Content, target containers,
anchors, and links for both `check` and `upgrade`. `check` remains read-only and
reports drift. `upgrade` reconstructs missing links, repairs wrong or broken
managed links, safely retires untouched v3–v5 agent-local artifacts, preserves
anything modified or user-authored, and removes stale links only when an
unmodified anchor proves their names. Its transaction writes Canonical Content
and Git protection before links and writes the stamp last. Every failure rolls
all affected path kinds back to their exact starting states.

## User Stories

1. As a user generating a project, I want each selected agent to discover the
   real canonical skill, so that skill delivery does not depend on interpreting
   a generated pointer document.
2. As a user, I want each skill stored once, so that agent compatibility does not
   duplicate the content I review and commit.
3. As a user, I want `setup-project` exposed to every selected Agent Target just
   like selectable skills, so that the unconditional first chain step is never
   the only undiscoverable one.
4. As a macOS or Linux user, I want relative symbolic links, so that moving my
   project does not break agent skill discovery.
5. As a Windows user, I want junctions that require neither Developer Mode nor
   elevation, so that normal project generation works from an ordinary shell.
6. As a user, I want no skill-delivery question or flag, so that generating a
   project does not ask me to choose an implementation mechanism.
7. As a user, I want no silent fallback to copies, so that identical inputs do
   not produce different project shapes on different machines.
8. As a user selecting multiple Agent Targets, I want each target to receive the
   same structurally derived skill set, so that lifecycle commands cannot
   disagree about which skills should be reachable.
9. As a user selecting no Agent Target, I want generation to require no link
   support, so that an unused filesystem capability cannot reject my project.
10. As a user generating on a filesystem without the required link support, I
    want failure before output is committed, so that I am not left with an
    unusable partial project.
11. As that user, I want the error to name the attempted path, underlying cause,
    and different-location remedy, so that I know how to proceed without a copy
    fallback.
12. As a user, I want `init` to retain its four-stage presentation, so that this
    internal delivery change does not add a new public workflow stage.
13. As a user whose destination did not exist before generation, I want any
    finalize failure to leave it absent, so that a failed command leaves no
    project-shaped debris.
14. As a user whose destination began as an empty directory, I want any finalize
    failure to restore that empty directory, so that rollback preserves the
    exact state I supplied.
15. As a user, I want a failed restoration to retain the documented exit class
    and print a manual-recovery warning, so that cleanup trouble is visible and
    diagnosable.
16. As a Git user, I want `git add -A` to stage Canonical Content once and no
    linked copy, so that Windows junction traversal cannot duplicate every skill
    in my repository.
17. As a Git user, I want the project root `.gitignore` left untouched, so that
    delivery does not rewrite a file I normally own.
18. As a collaborator cloning a generated repository, I want an explicit
    bootstrap command, so that an empty machine-local agent directory is an
    explained state rather than a mystery.
19. As a collaborator after cloning, I want one `upgrade` to recreate every
    selected Agent Target's links, so that no regeneration or remembered setup
    choice is required.
20. As a user running `check`, I want a missing, stale, wrong, or unresolvable
    Skill Link reported as drift, so that agent discovery failures are visible.
21. As a user running `check`, I want Canonical Content drift and Skill Link
    drift reported separately, so that the root cause is not hidden behind the
    derived symptom.
22. As a user running `check`, I want it to remain strictly read-only, so that
    diagnosis never repairs or probes my filesystem.
23. As a user moving a project on Windows, I want `upgrade` to rebuild junctions
    against the new absolute location, so that the move is recoverable with one
    lifecycle command.
24. As a user whose correct links already exist, I want `upgrade` to leave them
    untouched, so that a healthy project is an idempotent no-op.
25. As a user whose expected path contains a wrong, broken, indirect, or
    outside-project link, I want only that link object replaced, so that dev-ready
    never follows it into another location.
26. As a user who placed a real file or real directory at an expected link path,
    I want it preserved and reported as a conflict, so that repair never deletes
    user-owned content.
27. As a v0.11 user with untouched Pointer Stubs, I want them retired and
    replaced by links in one upgrade, so that the new delivery mechanism needs
    no manual cleanup.
28. As a v0.11 user who edited a Pointer Stub, I want it preserved and reported
    as divergence, so that a delivery migration does not erase my work.
29. As a user whose untouched stub directory also contains my own files, I want
    only the managed stub removed and my files preserved, so that clean managed
    content does not transfer ownership of its siblings.
30. As a user whose recorded stub is already missing from an otherwise empty
    managed directory, I want the empty scaffold retired and its link created,
    so that an earlier manual deletion does not permanently block conversion.
31. As a user upgrading directly from v0.3 full agent-local skill copies, I want
    a wholly untouched directory retired as one cohort, so that every recorded
    companion file moves to the link model together.
32. As that user, I want one modified or unrecorded file to preserve the entire
    skill directory, so that `SKILL.md` is never separated from user-owned
    scripts, references, or assets.
33. As a user with one blocked legacy skill, I want unrelated safe skills to
    convert, so that one conflict does not prevent all useful progress.
34. As a user in a partially converted target, I want the nested ignore file to
    name only actual links, so that a preserved real directory is never hidden
    from Git.
35. As that user, I want `check` to continue reporting the incomplete desired
    projection, so that partial conversion cannot look clean.
36. As that user after resolving the blocker, I want a later `upgrade` to expand
    the anchor and create the remaining link transactionally, so that conversion
    converges without regeneration.
37. As a user with an identical unrecorded nested ignore file, I want dev-ready
    to adopt it, so that matching safe state does not become a needless conflict.
38. As a user with a modified nested ignore file, I want it preserved and all
    link changes beneath it blocked, so that dev-ready never claims Git safety it
    cannot establish.
39. As a user whose recorded nested ignore file went missing, I want it restored
    transactionally and called out in the report, so that existing junctions do
    not remain exposed to Git.
40. As a user, I want that missing-file exception limited to the safety anchor,
    so that ordinary missing managed files retain ADR-014's preservation rules.
41. As a user upgrading after a skill or Agent Target path is removed, I want
    trusted stale links retired, so that derived machine-local state does not
    accumulate forever.
42. As a user with a modified old anchor, I want stale links preserved for manual
    reconciliation, so that dev-ready cannot infer ownership from edited
    evidence.
43. As a user with a real path occupying a stale link name, I want it preserved,
    so that stale-link cleanup removes only link objects.
44. As a user whose Canonical Content is missing or unsafe, I want that skill's
    legacy delivery left in place, so that `upgrade` never replaces a working
    artifact with a link to unready content.
45. As a user who edited Canonical Content, I want it treated as valid and
    preserved, so that link readiness does not require reverting my skill.
46. As a user whose Agent Target skills container or parent is itself redirected,
    I want the entire target preserved without traversal, so that dev-ready does
    not mutate a user-controlled destination.
47. As a user previewing an upgrade, I want the complete create, repair, restore,
    retirement, and conflict plan without mutation or a capability probe, so
    that dry run remains strictly observational.
48. As a user applying an upgrade that needs link writes, I want capability
    checked before persistent mutation, so that an unsupported filesystem does
    not trigger a transaction that can never finish.
49. As a user reading an upgrade report, I want Skill Links created and Skill
    Links repaired reported separately, so that bootstrap and correction are
    distinguishable.
50. As a user reading a dry-run report, I want those actions phrased as “would
    create”, “would repair”, and “would restore”, so that planned and completed
    work cannot be confused.
51. As a user whose upgrade only changes links, I want it counted as real work,
    so that the report never says “No changes were needed” after repairing my
    project.
52. As a user repeating a successful upgrade, I want zero planned changes, so
    that the lifecycle operation is demonstrably idempotent.
53. As a user, I want the project stamp written only after every content, anchor,
    retirement, and link step succeeds, so that it acts as the transaction's
    commit marker.
54. As a user, I want any upgrade failure to restore files, directories, links,
    anchors, and the stamp exactly, so that all-or-nothing applies to every new
    path type.
55. As a maintainer, I want one structural skill-name projection shared by
    generation, verification, inspection, and upgrade, so that non-catalog
    canonical skills need no hardcoded exception.
56. As a maintainer, I want one production link writer used by verification,
    finalization, and upgrade, so that the capability test cannot pass through a
    weaker code path than the real write.
57. As a maintainer, I want links treated as derived state outside the stamp
    inventory, so that the traversal guard does not reject dev-ready's own
    managed delivery artifacts.
58. As a maintainer, I want the existing N−1 gate to start from the real v0.11.0
    package, so that conversion is proven against what users actually received.
59. As a maintainer, I want Windows lifecycle CI to exercise junctions, Git
    exclusion, and moved-project repair, so that Ubuntu-only success cannot hide
    the platform's distinct behavior.
60. As a maintainer, I want no new runtime dependency, so that link delivery does
    not enlarge the installation surface.

## Implementation Decisions

### Projection and delivery shape

- **One Skill Link is projected for every direct canonical skill entry.** The
  authoritative name set is derived structurally from every direct
  `.agents/skills/<name>/SKILL.md` entry in desired overlay content after
  unconditional infrastructure has been collected. Catalog Item identifiers are
  not an input. This includes `setup-project` without a special case.
- The Agent Target projection owns the pure path calculations: the link path for
  a target and skill, the target's nested ignore-anchor path, and the skill names
  extracted from desired content. Generation, verification, inspection,
  `check`, and `upgrade` consume that projection rather than building local name
  lists. The projection module performs no filesystem I/O.
- Pointer Stub rendering is removed. No `SKILL.md` is written beneath an Agent
  Target skills directory by new generation. Canonical Content remains
  unconditional, real directory content under `.agents/skills/` and remains the
  only committed skill copy.
- POSIX writes a directory symlink whose stored target is the exact calculated
  relative path to its corresponding canonical skill. Windows writes a directory
  junction whose stored target is the exact current absolute canonical path,
  using CPython's `_winapi.CreateJunction`. Windows does not call `os.symlink`
  and therefore requires neither Developer Mode nor elevation.
- One filesystem-writing entry point owns creating, classifying, removing, and
  restoring Skill Link objects. It distinguishes symbolic links, junctions, real
  files, and real directories without following a link being classified. The
  platform mechanism is private to that writer and does not leak into projection
  or lifecycle policy.
- A link is correct only when all of the following hold: it occupies the exact
  projected path; it has the platform's required link kind; its stored target is
  exactly the calculated relative POSIX target or current absolute Windows
  target; that target is the corresponding canonical skill rather than another
  link; and the canonical directory and `SKILL.md` are real, safe paths inside
  the project. An indirect chain, alternate spelling, wrong skill, broken target,
  outside-project target, or other link kind is drift even when resolution
  happens to reach equivalent bytes.
- The Agent Target skills directory remains a real directory. If it or any path
  component leading to it is a symbolic link or junction, inspection reports one
  whole-target conflict. Upgrade preserves the redirection and performs no
  anchor, legacy-content, or Skill Link operation beneath it, even when it
  currently resolves inside the project.
- There is no copy mode, Pointer Stub compatibility mode, delivery selection,
  CLI flag, prompt, environment variable, or platform-conditional fallback.
  There is therefore no new recorded field and the stamp remains version 5.

### Git exclusion and clone bootstrap

- Desired overlay content includes one managed `.gitignore` inside every
  selected Agent Target skills directory that projects at least one link. Its
  stable English rendering contains two comment lines identifying the links as
  machine-local and naming `uvx dev-ready upgrade` as the restore command,
  followed by one sorted, directory-rooted entry per link name. The project root
  `.gitignore` remains byte-identical to v0.11.
- The nested `.gitignore` is ordinary overlay content: generation writes it and
  the stamp inventories its exact bytes. A Skill Link is derived state and never
  enters the inventory.
- Ignore coverage is a precondition for changing links in a target directory.
  Upgrade may proceed only when it will transactionally write the exact anchor,
  the existing managed anchor already has the required exact bytes for the
  post-transaction link state, or an identical unrecorded file can be adopted.
  It does not parse Git ignore semantics and does not invoke Git at runtime.
- A differing nested `.gitignore` is preserved and reported as a conflict. It
  blocks every link creation, repair, stale-link retirement, and legacy-content
  retirement in that target directory. No link is changed behind that conflict.
- A recorded-but-missing nested `.gitignore` is the one narrow exception to the
  ordinary missing managed-file rule. Upgrade restores the exact state-aware
  bytes transactionally and reports the restoration in both real and dry-run
  output. An unsafe or non-directory parent remains a whole-target conflict.
  The exception does not apply to any ordinary overlay file.
- During partial conversion, the anchor lists only link objects that will
  actually exist after that transaction and never a preserved real directory.
  Those exact state-aware bytes become the new inventory entry. Inspection still
  compares the target against the fully desired projection, so `check` reports
  drift until a later upgrade can expand the anchor and create the remaining
  links in one transaction.
- An unmodified inventoried anchor is also ownership evidence for derived links
  whose skill or Agent Target path is no longer projected. Upgrade may remove
  only the anchor's named stale paths that are still symbolic links or junctions,
  then update or retire the anchor. A real path is preserved. A modified anchor
  preserves all associated stale links and reports manual reconciliation.
- The generated project README and generation report explain the machine-local
  link behavior and the post-clone `uvx dev-ready upgrade` command only when at
  least one Agent Target is selected. The nested anchor always carries the
  command because it is the artifact that remains after a clone. An
  `--agents none` project receives no link-specific guidance.

### Generation, verification, and finalization

- Generation retains four public stages: fetch, overlay, verify, and finalize.
  Link work is internal to verify and finalize and adds no fifth progress stage.
- When the selection projects links, verification calls the production writer
  to materialize the complete projected link set inside staging, inspects every
  link against the strict correctness contract, and removes all temporary link
  objects before finalize. Staging is beside the destination on the same
  filesystem, and its Canonical Content already exists, so this exercises both
  the real platform primitive and the full projection rather than a synthetic
  one-link capability check.
- When the selection projects no links, verification performs no link write or
  capability probe. All other structural verification remains unchanged.
- A filesystem capability failure during verification raises
  `VerificationError` and maps to exit 5. Its message names the attempted path,
  preserves the operating-system cause, and recommends a different destination
  location. A path collision or inconsistent projection also fails verification
  before finalization, but is described as invalid generated structure rather
  than misleadingly as unsupported filesystem capability.
- Finalize first performs the existing same-filesystem atomic rename and then
  recreates the same complete link projection at the final paths on every
  platform. Parent target directories are created as needed because pruning may
  have removed empty ones.
- If post-rename link creation fails, finalize removes any links it created and
  restores the destination exactly: a previously absent destination is absent,
  and a previously empty destination is empty. It raises
  `TargetDirectoryError`, which maps to exit 4. If exact restoration itself
  fails, the same exit code is retained and the error includes a manual-recovery
  warning naming the remaining path and cause. Verification failures remain exit
  5 because they occur before the finalize commit.

### Inspection and `check`

- Project inspection is the shared behavioral classification seam for `check`
  and upgrade planning. It derives desired links from recorded Agent Targets and
  desired overlay content, checks Canonical Content independently, recognizes
  both `Path.is_symlink()` and `Path.is_junction()`, and never follows a path
  that has already failed the real-path boundary.
- Inspection reports a missing link, stale link, wrong kind, wrong stored target,
  broken link, indirect link, outside-project link, unsafe canonical target, and
  incorrect or obsolete anchor as distinct actionable drift. A correct link is
  not reported merely because it is absent from the stamp inventory.
- `dev-ready check` remains strictly read-only: it creates no temporary link,
  performs no support probe, repairs nothing, and returns exit 7 whenever link
  or anchor drift is actionable. Its existing stamp error behavior is unchanged.

### Upgrade planning and conflict policy

- Upgrade completes discovery and classifies every current path before its first
  persistent mutation. It plans overlay-file changes, per-skill Canonical Content
  readiness, anchor state, legacy retirement, current and stale links, report
  groups, and the resulting inventory as one coherent desired transaction.
- If the actual non-dry-run plan creates or repairs at least one link, upgrade
  creates and removes one temporary production link inside the project before
  the transaction. That location shares the project's filesystem. Capability
  failure raises `UpgradeError` and exits 9 before any persistent change, naming
  the path, cause, and different-location remedy. A deletion-only plan performs
  no probe. Dry run and `check` never probe.
- A correct desired link is a no-op. A wrong, broken, outside-project, or
  otherwise incorrect symbolic link or junction is removed as a link object and
  recreated; neither removal nor backup follows its target. An ordinary file or
  real directory at that path is preserved and reported through the existing
  Conflict group.
- Canonical Content readiness is decided per skill against the planned
  post-transaction state. A real canonical directory and real `SKILL.md` that
  already exist, including user-modified managed content, are ready. Content
  scheduled for safe addition or upgrade in the same transaction is ready. A
  missing recorded file, unresolved collision, symlink or junction component,
  or unsafe path blocks that skill's link creation or repair and legacy
  retirement. Unrelated ready skills continue.
- Link and anchor conflicts preserve the existing upgrade exit behavior:
  successfully reporting preserved conflicts returns 0. `check` remains the
  command that returns 7 for unresolved drift.

### Supported-history conversion

- Upgrade recognizes obsolete agent-local artifacts from every supported direct
  origin, stamp versions 3, 4, and 5, by expected path plus the recorded
  inventory hash. Body-shape or pointer-text detection is never ownership
  evidence. Every successful origin finishes at stamp version 5.
- For the v4/v5 Pointer Stub shape, an untouched stub in an otherwise empty
  directory is deleted, the empty directory is removed, and the link is created.
  A missing recorded stub in an otherwise empty recorded scaffold permits the
  same directory retirement and conversion. A correct link already at the
  expected path is treated as completed conversion rather than rejected by the
  obsolete-path traversal guard. An incorrect link follows the normal link
  repair policy.
- An untouched Pointer Stub with user-authored siblings loses only the managed
  stub. The directory and siblings are preserved, its link cannot be created,
  the state-aware anchor does not ignore that real directory, and the blocker is
  reported. A modified stub is preserved and reported as divergence, and no link
  replaces its directory.
- A v3 full-copy skill directory is one preservation cohort. It is eligible for
  whole-directory retirement when every existing recorded file matches its
  inventory hash and no unrecorded entry exists; an already-missing recorded file
  does not block an otherwise clean cohort. Any modified recorded file or any
  unrecorded entry preserves the entire directory, including untouched recorded
  companions, and reports every reason conversion was blocked.
- Legacy retirement, stale-link retirement, directory removal, anchor update,
  and desired link creation occur inside the same transaction. No legacy content
  is retired unless both its Canonical Content and its target directory's Git
  safety gate are ready.

### Upgrade transaction and report

- The upgrade transaction has one dependency order. Discovery, conflict
  classification, and any required capability probe finish first. The
  transaction then backs up every path selected for replacement or removal
  before writing Canonical Content, writing exact state-aware anchors, retiring
  eligible legacy directories, and creating or repairing links. The stamp is
  written last as the transaction's commit marker.
- A failure at any boundary restores every affected file, directory, symbolic
  link, junction, nested anchor, and stamp to its exact pre-upgrade state. Backup
  and restoration rename link objects aside without traversing their targets.
  A rollback failure stays exit 9 and adds a manual-recovery warning with the
  affected path and cause.
- Upgrade reports overlay files independently from derived links. It adds
  separate `Skill Links created` and `Skill Links repaired` groups, uses “would
  create” and “would repair” in dry run, and calls a restored missing safety
  anchor out explicitly with “restored” or “would restore”. Non-link occupants
  remain in the existing Conflict group.
- The overlay-file summary continues to count inventoried overlay files only;
  links do not inflate it. A separate overall result includes link and anchor
  work, so a link-only bootstrap or repair never prints “No changes were needed”.
  After a successful run, a second run reports zero planned changes.
- Link paths never enter the stamp inventory. The exact post-transaction nested
  anchor bytes do enter it. No new field is added, removed, or retyped, and the
  stamp version remains 5 for new generation and all successful upgrades.

### Documentation, platform coverage, and release gate

- The command specification is corrected to describe finalization's link step,
  link-related verification failures under exit 5, post-rename target
  restoration under exit 4, upgrade link creation and repair under exit 9 on
  operational failure, and the fact that links are derived rather than
  inventoried. No new exit code is introduced.
- The real N−1 lifecycle baseline advances from 0.10.1 to the pinned released
  0.11.0 artifact before other Phase 1 implementation. The gate generates a real
  v0.11 project containing Pointer Stubs and upgrades it with the working tree.
  It never substitutes a local build or resolves “latest”.
- CI adds a sixth `windows-lifecycle` job. It runs the full offline suite plus
  real generation and the N−1 gate, asserts that Git stages Canonical Content
  once and no junction contents, confirms v0.11 artifacts become junctions, and
  confirms a project move followed by upgrade repairs them. Existing Ubuntu jobs
  remain unchanged.
- The private Windows API dependency is guarded by an explicit presence test.
  Link behavior is exercised through the native platform branch; tests skip the
  non-native branch rather than faking Windows junctions on POSIX or POSIX
  symbolic links on Windows.
- Repository README and release-note changes remain Phase 3 work. Phase 1 owns
  the generated README template and lifecycle/CLI documentation needed for the
  feature itself.

## Testing Decisions

A good test for FR-46 asserts the observable lifecycle state of a real temporary
project: which paths are real, which are links, exactly where those links point,
what Git would stage, what commands report, and whether failure returns the tree
to its starting state. Tests do not assert private transaction collections,
internal call order, or which helper appended a report entry. The dependency
order is tested by injected boundary failures and their externally visible
rollback, not by mocks asserting a sequence of function calls.

The accepted testing shape uses the highest existing lifecycle seams:

1. **The pure Agent Target projection** receives desired overlay paths and is
   the one narrow unit seam. It proves that every direct canonical `SKILL.md`
   yields exactly one name, nested assets do not create names, malformed or
   indirect paths do not participate, ordering is deterministic, and
   `setup-project` is present without a Catalog Item special case. Prior art is
   the existing projection suite for target paths and canonical skill names.
2. **`generate_project`** is the primary generation seam. Tests generate into
   `tmp_path` and assert real Canonical Content, platform-native links, exact
   targets, stable nested anchors, an untouched root ignore file, conditional
   clone guidance, four-stage output, and no agent-local `SKILL.md`. A selected
   multi-target project proves the full projection. `--agents none` proves the
   no-probe path. Injected verification and post-rename writer failures prove
   exit mapping and exact restoration for absent and initially empty targets.
   Prior art is the current happy-path, staging, typed-error, and finalize
   rollback coverage.
3. **`upgrade_project` and the public `check` behavior** are the primary
   lifecycle seams. Stamped v3, v4, and v5 fixtures cover correct, missing,
   broken, wrong-kind, wrong-target, indirect, outside-project, and real-path
   occupants; current and stale links; clean, missing, identical unrecorded, and
   modified anchors; ready, modified, missing, collided, and redirected
   Canonical Content; linked target containers; and complete and partial legacy
   conversion. Assertions cover the resulting filesystem, report groups, dry
   run, conflict preservation, exit behavior, drift, and a clean second run.
   Prior art is the existing upgrade preservation, obsolete-file, dry-run,
   idempotency, and rollback suite plus the shared `inspect_project` seam already
   consumed by verification and `check`.
4. **Transaction failures are injected through existing write boundaries** at
   backup, canonical write, anchor write, legacy retirement, link create/repair,
   and stamp write. Each case snapshots the project before the call and asserts
   exact restoration afterward, including the identity and target of link
   objects and empty-directory state. A conflict excluded during planning is
   asserted byte-identical after rollback. Prior art is the existing mid-commit,
   parent-creation, and post-obsolete-deletion rollback coverage.
5. **CLI wiring tests remain narrow.** They assert that verification capability
   failure maps to 5, post-rename finalization failure maps to 4, actionable
   `check` drift maps to 7, and upgrade capability or transactional failure maps
   to 9. They do not duplicate lifecycle matrices already covered at the public
   operation seams. Prior art is the existing typed-error mapping suite.
6. **The real v0.11.0 N−1 gate** generates through the released PyPI artifact,
   then checks, previews, upgrades, checks again, and repeats upgrade through the
   working tree. It proves real Pointer Stub retirement, link creation, preserved
   edited content, version-5 stability, and idempotency. This remains the one
   network-marked lifecycle test; unit tests perform no network access.
7. **The Windows lifecycle job** runs native junction behavior, a real Git index
   check, real generation, N−1 conversion, and move-and-repair. Equivalent POSIX
   link and Git behavior remains covered by the existing Ubuntu jobs. The Phase
   3 by-hand clone checks retain the one property automation cannot prove:
   discovery and invocation by the actual agent after clone bootstrap.

The matrix includes these boundary cases explicitly:

- full projected-link materialization succeeds during verification and leaves
  no temporary link behind before finalize;
- capability failure during verification leaves no output, while a structural
  collision is reported as a verification defect rather than as unsupported
  filesystem capability;
- finalize recreates the exact verified projection and restores both supported
  pre-generation destination states on failure;
- a correct link is a no-op, while a broken junction after a Windows project
  move is a repair;
- an incorrect link is renamed or removed as an object without reading or
  mutating its target;
- a real occupant, modified anchor, or redirected target container blocks the
  correct scope and is never traversed;
- a missing recorded anchor is restored in real and dry-run reports, while an
  ordinary missing recorded overlay file keeps the existing behavior;
- a partial conversion inventories and ignores only actual links, remains
  drifted, and converges after its blocker is removed;
- v4/v5 untouched, missing, modified, and sibling-bearing Pointer Stub
  directories follow their separate retirement rules;
- v3 clean, missing-recorded-file, modified, and extra-entry cohorts retire or
  preserve as a whole;
- removed skills and moved target paths retire only anchor-proven stale link
  objects, never real occupants;
- user-modified Canonical Content is ready, while missing or redirected content
  blocks only its own derived link;
- dry run and `check` are byte-identically read-only and perform no capability
  probe;
- a link-only real upgrade counts as change, and its immediate second run is a
  zero-change no-op;
- every successful path retains stamp version 5 and excludes link paths from its
  inventory.

All unit tests use `tmp_path`, perform no network access, touch no filesystem
outside the per-test project, and depend on no developer-global configuration.
Tests requiring the real Git executable or released package live in their
existing integration or end-to-end class rather than the unit suite.

## Out of Scope

- **Any copy delivery mode.** There is no copy fallback, compatibility flag,
  prompt, recorded selection, or platform-specific divergence in output policy.
- **Any stamp version bump or link inventory.** The stamp remains version 5;
  only the managed nested anchor is inventoried.
- **Changing Canonical Content.** Its location, one-copy rule, user-modification
  preservation, and Standard-Compliant Agent behavior remain as established by
  ADR-015 and ADR-026.
- **Replacing a whole Agent Target skills directory with one link.** Delivery is
  one link per skill so user-authored agent-local skills can coexist and be
  preserved.
- **Changing the Agent Target Map or adding an Agent Target.** The declared and
  drift-guarded target paths remain as shipped in v0.11.
- **Changing `CLAUDE.md`.** Its `@AGENTS.md` import remains untouched.
- **Automatically running upgrade after clone.** Ignored links are reconstructed
  only when the user or agent invokes the documented command; no Git hook,
  package-install hook, or background action is added.
- **Making an unsupported filesystem work.** Projects selecting Agent Targets
  require native link support. The supported remedy is a different project
  location; `--agents none` remains available when links are not needed.
- **FR-47 and the `superpowers` Engineering Flow.** Phase 2 adds its skills after
  this delivery mechanism is complete.
- **Repository README, changelog, version overview, and release edits.** Phase 3
  owns the single pass over settled v0.12 product text. The generated project
  README line is in scope here.
- **A new runtime dependency or a runtime dependency on Git.** Standard-library
  filesystem APIs implement links; Git is used only by integration and CI
  verification.
- **Localized runtime or generated content.** All authored and generated text is
  English under ADR-016.

## Further Notes

This is a breaking delivery change even though it adds no input and moves no
stamp field. Agent skill directories become machine-local, and a clone needs one
explicit upgrade before a selected agent can discover project skills. A
filesystem that accepted v0.11 Pointer Stubs can reject v0.12 when it cannot
create the required link kind. Both costs must be stated in the v0.12 changelog
and release overview in user terms.

The full-projection verification is deliberately stronger than a one-link
capability probe. On the measured Windows machine, creating and removing 972
junctions took about 1.3 seconds. That bounded cost is acceptable for proving the
actual projected names, targets, parent creation, and production writer before
the atomic rename. The same writer then repeats the operation during finalize;
the duplication is the price of preserving both honest verification and the
Windows absolute-target constraint.

The nested `.gitignore` has two jobs and that is why its preservation rules are
stricter than ordinary generated prose. It prevents Git from turning junctions
back into duplicate content today, and its recorded exact bytes are the only
ownership evidence available for removing derived links after the projection
changes tomorrow. Treating it as best-effort documentation would make both
guarantees false.

The stamp staying at version 5 is intentional, not a migration omission. Skill
Links are entirely reconstructable from already-recorded Agent Targets plus the
current structurally derived canonical skill set. Recording each link would add
redundant state and would collide with the traversal guard whose purpose is to
keep inventoried managed files on real paths.

Claude Code discovery through both a junction and a relative symbolic link was
verified by hand during the 2026-08-18 grilling. End-to-end invocation through a
junction and the post-clone experience on both Windows and POSIX remain Phase 3
release checks because only the actual agent can prove that final integration.
