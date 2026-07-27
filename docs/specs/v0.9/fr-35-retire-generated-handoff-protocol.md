# FR-35 — Retire the Handoff Protocol from Generated Projects

Status: Accepted by CEO (2026-07-27)

Version: v0.9

Phase: unassigned (the v0.9 version plan is not yet cut)

Governing decisions: ADR-007 (scoped to internal process), ADR-010, ADR-014, ADR-016, ADR-017, ADR-018, ADR-020

## Problem Statement

A generated project can receive a scaffold for a seven-role, four-layer multi-agent development process: a configuration declaring role identifiers, responsibilities, prohibitions, and model assignments, plus four review-gate templates, a ticket directory, an execution-report skeleton, and a readme explaining the sequence.

It is, in substance, dev-ready's own development process shipped to users on the assumption that other teams want it, and three things make that assumption look wrong. It presumes a team of agents rather than one developer working with one agent, which is what an ordinary user of a FastAPI scaffold has. It arrives before it is wanted: a user generating their first project receives seven role definitions and four review gates governing work that does not exist yet, and process delivered ahead of the work it governs is process a user deletes. And it competes for attention in the same generated instruction surface with the within-session development loop, which is the thing that has earned its place.

The evidence for it is this repository's own use, and that is not evidence that a *generated* project needs it — dev-ready develops dev-ready and keeps its process whether or not the overlay ships one.

Meanwhile the cost is continuous. The scaffold carries a configuration schema, seven role records, six templates, their rendering, their conditional interaction with the development loop, and a share of every stamp migration and obsolete-file pass the project ever performs.

## Solution

Stop generating it. Generated projects receive no protocol configuration, no review-gate templates, no ticket directory, and no execution-report skeleton, and the selectable unit that produced them is removed along with its Component and its flag.

dev-ready's own process is untouched. The role definitions in this repository's agent rules, its four-layer loop, and its per-version working directories continue exactly as they are. What ends is productization, not practice.

Existing projects are migrated rather than stranded. The generated files retire through the established obsolete-file rules in the same transaction as this version's other retirements: untouched files are deleted, files the user edited are kept with their deletion skipped, and both outcomes are reported. Nothing smaller stands in for the removed capability — no reduced scaffold, no optional preset, no documentation stub.

## User Stories

1. As a user generating a project, I want no multi-agent process scaffolding I did not ask for, so that my new project contains only what it needs to start.
2. As a solo developer, I want no seven-role configuration to read past, so that the instruction surface my agent loads is about my project rather than about a team I do not have.
3. As a user, I want the development loop to be the only process my generated project describes, so that there is no ambiguity about which one governs.
4. As a user, I want the selection surface to stop offering the scaffold, so that I am not asked to decide about something that no longer exists.
5. As a user, I want the previous flag that controlled it to fail with an explanation rather than being silently ignored, so that an existing script tells me the capability is gone.
6. As a user, I want the post-generation report to describe only what was written, so that it never mentions a capability that was removed.
7. As a user upgrading an existing project, I want the scaffold's files removed, so that I do not carry content nothing maintains.
8. As a user upgrading, I want files I edited to be kept rather than deleted, so that removing a feature never destroys work I did inside it.
9. As a user upgrading, I want every preserved file reported, so that I can decide deliberately whether to keep or delete each one.
10. As a user upgrading, I want the removal to commit in the same transaction as the version's other changes, so that a failure never leaves a project half-migrated.
11. As a user upgrading, I want a failure to restore the deleted files along with everything else, so that a rollback is complete.
12. As a user previewing an upgrade, I want every planned deletion listed before anything is removed, so that I can see what I am about to lose.
13. As a user who never selected the scaffold, I want the upgrade to be a no-op in this respect, so that I am not shown removals that do not apply to me.
14. As a user of an older project, I want its record to remain readable after the capability is gone, so that inspection keeps working on a project I have not upgraded.
15. As a user, I want documentation to stop describing the capability, so that I am not told about something the tool no longer does.
16. As a user reading the Chinese overview, I want it to describe what dev-ready produces accurately, so that the product facts it carries stay true.
17. As a maintainer, I want the scaffold's templates removed from the package, so that the wheel stops carrying content nothing generates.
18. As a maintainer, I want the conditional rendering between the scaffold and the development loop removed, so that generation, verification, and future migrations lose a combinatorial case.
19. As a maintainer, I want verification to stop expecting the scaffold's paths, so that its required-path set matches what is actually produced.
20. As a maintainer, I want this repository's own process left untouched, so that removing a product surface does not disturb how the project is built.

## Implementation Decisions

- The Handoff Protocol scaffold is removed from the overlay in full: the protocol configuration, the four review-gate templates, the ticket directory placeholder, the execution-report skeleton, the readme, and the ignore file. The assets are deleted from the package rather than retained unreferenced.
- The selectable unit that produced them is removed, along with its Component and its selection flag. The flag is rejected as an invalid argument with a message stating the capability was removed, rather than accepted and ignored — a script that passes it is expressing an intent the tool can no longer satisfy, and silently continuing would produce a project its author did not ask for.
- The deprecated alias retained for one version when the unit was last renamed is removed at the same time. It exists only to reach a capability that no longer exists.
- Conditional rendering between the scaffold and the development loop is deleted rather than reduced. With one side gone the conditional has one branch, and the loop's guidance is rendered unconditionally.
- Verification stops treating the scaffold's paths as required. The removal is not a partial-generation failure; it is an absence by design.
- The project record no longer carries the scaffold's inclusion state for newly generated projects. Older records that carry it remain readable, so inspection continues to work on projects that have not been upgraded.
- Upgrade retires the generated files through the established obsolete-file rules, in the same transaction as this version's other retirements. An untouched file is deleted; a file the user modified is preserved and its deletion skipped; both outcomes are reported. Writes and deletions commit together or roll back together, and the preview path reports every planned deletion without mutating anything.
- A project that never selected the scaffold produces no removal entries, so its upgrade report is not padded with inapplicable lines.
- Provenance and attribution are unaffected: the scaffold was original content, so no third-party notice changes.
- Documentation stops describing the capability across the requirements index, the version plan, the command specification, and the README pair. The Chinese overview is updated because what dev-ready produces is exactly the class of product fact it carries; it gains no flags and no exit codes.
- This repository's own process is explicitly out of the change. Its agent rules, role definitions, per-version working directories, and review gates are untouched, and the decision that established them remains in force scoped to internal practice.

## Testing Decisions

- A good test here asserts absence in the output and completeness in the migration. Absence is asserted on the generated tree, not by checking that a code branch was not taken. Completeness is asserted by generating with an older layout, upgrading, and inspecting the result.
- Overlay application is tested at its existing seam: for every selection, including one that would previously have included the scaffold, none of its paths appear in the written set. Prior art is the existing suite asserting written paths per selection.
- The flag surface is tested at the canonical generation-intent seam. Prior art is the existing rejection cases for unknown identifiers and conflicting flags; the new cases assert that the removed flag and its deprecated alias are both rejected with a message naming the removal.
- Upgrade is tested at its existing seam across three starting points: a project that included the scaffold and never touched it, a project that included it and edited one of its files, and a project that never included it. These assert deletion, preservation with a report entry, and a no-op respectively. Prior art is the existing obsolete-file coverage introduced for the previous layout migration, which already asserts the preserve-and-report path.
- Rollback is tested by forcing a failure mid-transaction and asserting that deleted files are restored alongside reverted writes. Prior art is the existing all-or-nothing upgrade coverage.
- The preview path is tested by asserting that the planned deletions are reported and that the project is byte-identical afterwards.
- Record compatibility is tested at the stamp seam: an older record carrying the scaffold's inclusion state still loads and still inspects.
- Verification is tested by asserting that a generated project without the scaffold passes, which is the inverse of the current required-path assertion.
- The permanent N-1 lifecycle gate is extended to cover the removal: generate with the previous released version including the scaffold, upgrade with the working tree, and assert the files are gone and the record is current.
- Unit tests use no network and no filesystem outside the per-test temporary directory.

## Out of Scope

- Any change to this repository's own development process, its role definitions, or its per-version working directories. The governing decision remains in force for internal practice.
- A replacement scaffold of any size. No reduced two-role variant, no optional preset, and no documentation stub is introduced. If real demand appears it should shape whatever answers it, rather than being guessed at now.
- Category-first selection and the stamp advancing to version 5, specified in FR-30.
- The development loop becoming mandatory, the Default Set, and the removal of the project-orientation skill, specified in FR-31. That FR's obsolete-file pass and this one are the same mechanism exercised on different content.
- Any localized runtime surface. The Chinese overview is repository documentation, not a runtime surface.

## Further Notes

This retires two shipped requirements, one of which was the headline work of a version, and that is the strongest argument against doing it. The counter-argument is that the headline work made the configuration excellent without establishing that a generated project should have one, and quality of execution is not evidence of demand.

Doing it in this version rather than later is a cost decision. This version already builds a record migration and an obsolete-file pass for other retirements, so the removal adds entries to machinery already being paid for. Deferring it means building the same machinery twice.

The removal is not cheap to reverse. Restoring it would mean re-authoring six templates, the configuration schema, and the conditional interaction with the development loop. That is the accepted price of narrowing what the product claims to do.
