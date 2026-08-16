# FR-41 — MIT notice propagation into generated projects

Status: Accepted by Moofon (2026-08-16)

Version: v0.11

Phase: 3 (shared with FR-40, which has its own spec and its own acceptance set)

Governing decisions: **ADR-009** (as amended 2026-08-16) extends vendored
provenance past this repository's boundary into the generated project, sets the
scope at every vendored source whose content is copied, and makes the sync
check license-symmetric and per-repository for loose-file destinations.
ADR-008 (integration modes), ADR-014 (truthful overlay lifecycle), ADR-015
(Canonical Content and Pointer Stubs), ADR-016 (language), ADR-021 (process),
and the module boundaries in `docs/architecture.md` are binding. ADR-025
targets v0.12 and nothing here implements it.

---

## Problem Statement

**Content is copied into user projects without the notice its source ships
with.** Four vendored repositories place files inside every project that
selects them, and none of the four carries a copyright or permission notice
along with those files:

- the Engineering Flow's twelve skill directories, from `mattpocock/skills`
- the token-discipline skill, from `JuliusBrussee/caveman`
- the security audit skill, from `cloudflare/security-audit-skill`
- the Design References, from `VoltAgent/awesome-design-md` — two documents
  today, 74 once FR-40 lands

All four are MIT. The two Apache-2.0 skills do carry their licence file into
every project that selects them, but only because upstream happens to keep that
file inside the skill directory and dev-ready's directory copy picks it up.
Nothing in dev-ready arranges it, and nothing checks that it happened for any
licence other than Apache-2.0.

**The gap is old, but this version is the one that makes it uncomfortable.**
v0.10 was the first release whose own third-party notices file states that
copies written into a generated project may be modified and are therefore
derived works, and the same release began injecting dev-ready's own text into
those files through Mount Points. A user reading their generated project sees
twelve skill directories with no indication of where they came from or what
terms they arrived under.

**The scheduled repair was scoped to one of the four, and its own reasoning
does not support that.** FR-41 named `mattpocock/skills` alone. The stated
ground is that the notice travels with the copy — a ground that does not
distinguish one MIT source from another. The scoping is harder to defend given
where it lands: this is the phase that takes the largest unfixed source from
two files to 74.

**Nothing would catch the next omission either.** The notices sync check runs
a licence-file rule for Apache-2.0 and for nothing else, so a future MIT source
can be vendored with no notice and CI will pass.

## Solution

**Every vendored source whose content reaches a generated project carries its
notice there, and CI enforces it for every licence.**

For the three sources whose destinations are directories, the upstream notice
file is vendored into each snapshot directory. The existing directory copy then
carries it into the project with no new mechanism, which is precisely how the
two Apache skills already work. For the Design References, whose destinations
are loose documents with no directory to travel in, a single notice is written
alongside them whenever the selection contains any item from that source.

The notices sync check drops its licence-string condition so the same rule
applies to every source, and runs per repository rather than per path where a
source vendors loose files.

No legal conclusion is drawn here, in the generated project, or in any
user-facing document.

## User Stories

1. As a developer receiving twelve Engineering Flow skills, I want each to
   carry the notice from its source, so that I can see what terms the content
   arrived under.
2. As a developer who selected the token-discipline skill, I want its notice
   present, so that its source is not the only one left unattributed.
3. As a developer who selected the security audit skill, I want its notice
   present, for the same reason.
4. As a developer who selected any Design Reference, I want a notice written
   beside those documents, so that the largest body of copied content is not
   the one with no attribution.
5. As a developer who selected no Design Reference, I want no design notice in
   my project, so that my project does not carry attribution for content it
   never received.
6. As a developer generating with the leanest possible selection, I want the
   Engineering Flow's notice present anyway, because the flow is mandatory and
   its content is always copied.
7. As a developer, I want the notice to be the upstream file unmodified, so
   that it is a copy rather than dev-ready's summary of one.
8. As a developer redistributing my generated project, I want the attribution
   already in place, so that I am not repairing it myself later.
9. As a developer reading my project, I want notices to sit beside the content
   they cover, so that I can tell which notice applies to what.
10. As a developer running `upgrade`, I want notice files treated as managed
    content, so that they are maintained rather than classified obsolete and
    deleted.
11. As a developer, I want the notice files recorded in my project's stamp
    inventory, so that drift in them is detectable like any other managed file.
12. As a developer, I want no legal advice from dev-ready, so that the tool
    states facts about provenance and leaves conclusions to me.
13. As a maintainer, I want CI to fail if any vendored source's notice is
    missing, regardless of licence, so that the next omission cannot ship.
14. As a maintainer, I want the check to handle a source whose destinations are
    loose files, so that the Design References are covered by the same rule
    rather than exempted from it.
15. As a maintainer adding a future vendored source, I want the notice
    requirement enforced automatically, so that I cannot forget it.
16. As a maintainer, I want the notice files covered by the existing drift
    guard, so that they are byte-checked against the pinned commit like every
    other vendored file.
17. As a maintainer, I want the repository's own third-party notices document
    to list the new paths, so that the two records stay in agreement.
18. As a maintainer, I want the notice delivery to need no new overlay
    mechanism for the three directory-shaped sources, so that the change is
    data rather than code wherever that is possible.
19. As a maintainer, I want the pins left alone, so that this repair does not
    smuggle in an upstream content bump.
20. As a reviewer, I want the duplication this creates stated up front, so that
    twelve copies of one file is a recorded decision rather than something I
    discover in the diff.
21. As a reviewer, I want to know why the tidier per-source design was not
    taken, so that the cheaper choice is visible as a choice.

## Implementation Decisions

**The scope is four sources, not one.** The reasoning FR-41 gives applies
identically to all four, and the phase that repairs one is the phase that grows
another thirty-seven-fold. The requirement has been corrected in
`docs/requirements.md` with the measurement attached.

**The upstream notice filename is `LICENSE`, with no extension.** This was
verified at the pinned commits rather than assumed; the version plan's
verification item explicitly warned against assuming it.

**The three directory-shaped sources use the existing directory copy.** The
upstream notice is vendored into each snapshot directory, adding fourteen path
entries to the manifest's vendored section and no code at all. The overlay's
content collector already recurses into directories and copies every file it
finds, which is exactly how the two Apache skills deliver their licence file
today. The drift guard covers the new files automatically, because it compares
whole directories for directory-shaped destinations.

**The Design References need one conditional write.** Their destinations are
loose documents, so there is no directory for a notice to travel in. A single
notice is written to a dedicated path in the project's documentation directory
when the selection contains any item declaring that source. Writing it
unconditionally was rejected: a project that selected no Design Reference would
carry attribution for content it never received, and a reviewer would rightly
ask what it was for.

**The notices sync check becomes licence-symmetric and per-repository for
loose-file sources.** Today the check runs its licence-file rule for Apache-2.0
only, once per declared path, and expects each path to be a directory holding a
file whose name begins with `license`. Three of the four MIT sources fit that
shape. The Design References do not: each of their destinations is a document
named for a brand, so a naive extension of the existing rule would produce
seventy-four failures on its first run. The licence-string condition is
therefore dropped, and the rule runs once per repository when a repository's
destinations are files rather than directories.

**The duplication is accepted deliberately.** The same notice of roughly one
kilobyte appears twelve times under the Engineering Flow's vendored snapshots
and twelve times in a generated project that receives them. This is the price
of using the existing mechanism, and it is paid knowingly.

**A per-source notice declaration was considered and deferred.** Declaring one
notice per vendored entry and writing it once per project is the tidier shape,
and it would remove the twelve duplicate copies. It was rejected for this
version because it costs a manifest field, loader validation, and new overlay
code, against fourteen lines of data and none — and because FR-41 explicitly
chose the mechanism already in use.

**An aggregate notices file in the generated project was considered and
rejected.** It would name sources the project never received unless it were
made selection-aware, at which point it is the conditional write above with
more machinery, and it abandons the mechanism the requirement chose.

**Pins are not bumped.** All four notices are vendored at the commits already
declared.

**The repository's own third-party notices document gains the new paths**, and
the sync check runs once at the end of the phase alongside FR-40's additions.

**The stamp stays at version 5.** A notice file is a new managed path and a new
inventory entry, which the existing schema already expresses; no field is
added, removed, or re-typed.

## Testing Decisions

**A good test here asserts what a generated project contains and what the check
reports, never how either is assembled.** Both are observable from outside.

**Two seams, both of which already exist.** No new seam is introduced by this
spec.

- **The overlay content builder** — covers notice presence per source. A
  project selecting the token-discipline skill carries its notice; the same for
  the security audit skill; the Engineering Flow's notices are present in the
  leanest possible selection, because the flow is mandatory. The design notice
  is present when any Design Reference is selected and, importantly, absent
  when none is — that negative assertion is the one that would catch a
  regression to unconditional writing. Prior art:
  `tests/unit/test_overlay.py`.
- **The notices sync check** — covers the symmetric rule and the
  per-repository behaviour. It asserts the check fails when any vendored
  source's notice is removed regardless of licence, and that a source whose
  destinations are loose files is evaluated once rather than once per file.
  The loose-file case is the regression test for the seventy-four-failure
  behaviour a naive extension would produce. Prior art:
  `tests/unit/test_notices_sync.py`.

**Upgrade classification is asserted with FR-40's coverage** rather than
duplicated here: a notice file is managed content, and the assertion that an
untouched managed file is refreshed rather than deleted is the same assertion.

**Every unit test runs offline, inside a temporary directory, and touches no
path outside it.** The vendored drift check remains the only place the new
files are compared against upstream, and it runs in the existing
network-enabled CI job.

## Out of Scope

- **The Design Reference set itself.** FR-40 shares this phase and has its own
  spec and acceptance set.
- **A per-source notice declaration in the manifest.** Considered and deferred
  above; it remains the tidier shape for a later version.
- **An aggregate third-party notices file inside generated projects.**
  Rejected above.
- **Any legal conclusion, in any document.** The repair is mechanical: the
  notice travels with the copy.
- **Bumping any vendored pin.** All notices are taken at the existing commits.
- **Changing how the Apache-2.0 skills deliver their licence file.** It already
  works and it stays as it is; the symmetric rule simply stops being the only
  rule that covers it.
- **Retroactive repair of already-generated projects** beyond what `upgrade`
  does with a new managed path.
- **A stamp version bump.**

## Further Notes

**This spec exists because the grilling session refused to accept the
requirement's scope at face value.** FR-41 was measured against the shipped
manifest rather than read, and the count came back four rather than one. The
requirement was not wrong about the mechanism or the reasoning — only about how
far its own reasoning reached.

**The check's shape is the more durable half of this change.** Adding three
notices fixes today's gap. Making the rule licence-blind means the next
vendored source cannot ship without one, which is the difference between
repairing an omission and removing the class of omission. The Apache-only
condition is exactly the kind of narrow guard that looks complete until someone
adds content under a different licence.

**The seventy-four-failure trap is worth remembering.** The existing check
iterates per declared path and assumes each path is a directory. That
assumption held for every source in the catalog until Design References began
vendoring loose documents. An implementation that extended the licence
condition without also changing the iteration would have failed immediately and
loudly — which is the good failure mode, but only because the destinations are
numerous. A source vendoring a single loose file would have failed once, in a
way far easier to misread as a missing notice rather than a wrong rule.
