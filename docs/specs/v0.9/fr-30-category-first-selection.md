# FR-30 — Category-First Selection

Status: Accepted by CEO (2026-07-27)

Version: v0.9

Phase: unassigned (the v0.9 version plan is not yet cut)

Governing decisions: ADR-002, ADR-004, ADR-009, ADR-010 (amended by ADR-017), ADR-014, ADR-015, ADR-017

## Problem Statement

A user choosing what their project should contain is asked to choose along an axis that exists for the generator's benefit, not theirs. Components group overlay content by where its files are written — skills in one place, MCP configuration in another, documentation templates in a third — and that grouping is presented as the first question the tool asks. It does not match how anyone reasons about the choice.

Three consequences follow. First, the groupings a user actually wants cannot be expressed: someone setting up for design work wants both the frontend-design methodology skill and the reference design-document templates, and those live in different Components; someone worried about token cost wants both a token-discipline skill and a codebase-memory server, and those also live in different Components. There is no way to ask for either group.

Second, two Components were modelled as single on/off switches and therefore never received item-level selection at all. The two vendored design-document templates have been present but unselectable since they were added — a user can take both or neither, and cannot see that a choice exists.

Third, pure infrastructure leaked into the list of things a user picks. The base MCP configuration file is presented as a selectable item, although it is not a capability: it is the empty container every MCP server writes into. A user who deselects it while selecting a server has made a selection the tool offers and the interface accepts, and generation then fails — behaviour currently pinned by a test asserting the failure is expected.

## Solution

Category replaces Component as the axis a user selects along. A user picks among Dev, Security, Quality, Design, and Token Optimize, and within each Category picks individual items. Each Catalog Item declares exactly one Category as manifest data, so a Category can hold items whose files are written to entirely different places — a design Category containing both a skill and a document template is expressible because the Category no longer implies a write location.

Component survives, unchanged, as the internal grouping that decides where a selected item's files land. It is never presented, never prompted for, and never named in a user-facing flag. Every stage downstream of selection continues to consume the selection exactly as it does today, so the change is confined to the two adapters that build a selection and to the record written into the project.

Infrastructure stops being a choice. The base MCP configuration is generated when a selected item needs it and omitted when none does, which repairs the selection that fails today. The design-document templates become individually selectable under the Design Category, closing a gap that has been open for several versions.

The project stamp advances to record Categories alongside the resolved item set, and existing projects migrate without being asked for new input.

## User Stories

1. As a user, I want to choose what my project contains by the kind of work it supports, so that I do not have to learn how the generator organizes its own files before I can answer.
2. As a user setting up for design work, I want one Category that offers both the design methodology skill and the reference design-document templates, so that a single choice covers the concern I actually have.
3. As a user worried about token cost, I want one Category that offers both the token-discipline skill and the codebase-memory server, so that I am not required to know that one is a skill and the other is a server.
4. As a user, I want each Category to carry a description, so that I can tell what a Category is for without opening the items inside it.
5. As a user, I want each item inside a Category to carry a description that answers what I lose by omitting it, so that I can decide without research.
6. As a user, I want to select individual items within a Category, so that choosing a Category does not force everything in it on me.
7. As a user, I want to select whole Categories at once, so that I can accept a Category's contents without stepping through every item.
8. As a user, I want to decline a Category entirely, so that nothing from a concern I do not have appears in my project.
9. As a user, I want to select Categories and items non-interactively, so that I can script generation and drive it from an agent.
10. As a user, I want an unknown Category name rejected immediately with the valid names listed, so that a typo fails before anything is written.
11. As a user, I want an unknown item identifier rejected immediately with the valid identifiers listed, so that I am not left guessing what I mistyped.
12. As a user, I want conflicting selection flags rejected as invalid arguments, so that the tool never silently picks one of two contradictory instructions.
13. As a user, I want my selection resolved and shown to me before anything is written, so that I can abort on seeing something I did not intend.
14. As a user, I want the confirmation summary to name Categories and items, so that what I confirm is described in the same vocabulary I chose in.
15. As a user, I want the post-generation report to state what was written per Category, so that I can confirm the outcome without exploring the tree.
16. As a user, I want the base MCP configuration created automatically when a selected item needs it, so that I never have to know that a container file exists.
17. As a user, I want no MCP configuration created when nothing needs it, so that my project carries no empty scaffolding.
18. As a user, I want a selection that the interface accepts to always generate successfully, so that a valid-looking choice never fails partway.
19. As a user, I want the reference design-document templates offered individually, so that I can take the one whose style matches my project and leave the other.
20. As a user, I want the Category that names my project's development loop to require an answer rather than offering none, so that I cannot end up with a project that has no process at all.
21. As a user, I want Agent Target selection to stay a separate question from Category selection, so that what my project contains and which agents can read it remain independent decisions.
22. As a user, I want my selected Categories recorded in the project stamp, so that later inspection knows what the project was asked to contain.
23. As a user, I want inspection to report drift against the Categories I selected, so that a report describes my project in the terms I chose it in.
24. As a user upgrading an existing project, I want my previous selection carried forward without being asked to restate it, so that the upgrade needs no new input.
25. As a user upgrading, I want my previously selected items mapped to the Categories they now belong to, so that nothing I chose is silently dropped.
26. As a user upgrading, I want the migration to commit all at once or not at all, so that a failure never leaves a project describing itself two ways.
27. As a user previewing an upgrade, I want the full migration shown without mutation, so that I can review a record format change before accepting it.
28. As a user of an older project, I want the previous stamp formats to remain readable, so that inspection keeps working on projects I have not upgraded.
29. As an existing scripted user, I want the removal of the previous selection flags to fail loudly with a message naming what replaced them, so that I discover the change at the first run rather than through wrong output.
30. As a maintainer, I want each item's Category held as manifest data, so that recategorizing an item is a data change rather than a code change.
31. As a maintainer, I want an item with a missing or unknown Category to fail at manifest load, so that a data mistake cannot reach a user as a broken menu.
32. As a maintainer, I want the stages after selection to consume the selection unchanged, so that this change cannot introduce divergence between generation, verification, inspection, and upgrade.

## Implementation Decisions

- Category is the user-facing selection axis and carries five values: Dev, Security, Quality, Design, and Token Optimize. Each is declared as manifest data with an identifier and a description used by prompts and help output. Dev is a mandatory single-select holding the development loop; the other four are multi-select and may be declined entirely.
- Categories are named for what they hold at release, not for what they might hold later. "Ops" was considered and rejected because its only member is browser end-to-end testing, which is quality assurance; it is named Quality. Adding a Category later is a new enumerated value with no migration, while renaming one breaks inspection and upgrade for every stamped project, so the asymmetry always favours naming narrowly now.
- Every Catalog Item declares exactly one Category. An item belonging plausibly to two is assigned by decision and the assignment is recorded; there is no mechanical rule and no multiple membership, because an item reachable from two places is an item a user can select twice and deselect once.
- Component remains in the manifest and in the generator as the grouping that determines where a selected item's content is written. It is removed from every user-facing surface: prompts, flags, help text, the confirmation summary, and the report.
- The canonical generation intent is unchanged in shape. It continues to expose the selected item set and inclusion state keyed by Component, and every stage downstream of it — overlay application, verification, reporting, inspection, and upgrade — consumes it exactly as before. Only the two adapters that construct it change: the flag adapter and the interactive prompt adapter.
- The non-interactive contract follows the established item-selection form: comma-separated identifiers, an all value, and a none value, with unknown identifiers and conflicting flags failing as invalid arguments that list what is valid. The previous Component-shaped flags are removed rather than aliased, and are rejected with a message naming their replacement — a silent alias would leave a script producing a different project than its author wrote.
- The base MCP configuration stops being a Catalog Item. It becomes infrastructure created when a selected item declares an effect that targets it, and omitted otherwise. The test that currently pins the failing selection as expected behaviour is replaced by one asserting that selection now succeeds.
- The reference design-document templates become individually selectable Catalog Items under the Design Category. The documentation Component stops being a single on/off switch, which is what prevented item selection for them.
- The Handoff Protocol scaffold is removed from the overlay by FR-35 in this version, so it needs no Category. Its Component and its selection flag disappear with it, which is why the flag set this FR replaces is smaller than the one v0.8 shipped.
- Agent Target selection is untouched. It remains an independent axis asked as its own question, and its identifiers, prompts, and stamp representation are unchanged by this FR.
- The stamp advances to version 5, recording selected Categories alongside the resolved item set that versions 3 and 4 already record. Versions 3 and 4 remain readable by inspection; version 4 stamps upgrade without new input by deriving each recorded item's Category from the running manifest. Versions 1 and 2 remain checkable and not upgradable, as before.
- Across an overlay-only upgrade the stamped upstream repository and commit remain immutable Base Provenance. Selected Categories join the dev-ready version, item pins, Agent Targets, and managed-file inventory as Overlay Currency that advances to the running CLI.
- Manifest load validates that every item declares a known Category and that every declared Category is non-empty. Both failures are load-time errors, so shipped data cannot reach a user as a menu with a missing or empty section.

## Testing Decisions

- A good test here asserts the observable contract — what a given input selection produces, what is written into a generated tree, what the stamp records, and what an invalid input rejects. It does not assert internal call sequences, the shape of intermediate data, or which module performed a write. The strongest signal available is that the stages downstream of selection have no test changes at all: if overlay, verification, report, and inspection tests need editing, the Component-as-internal-grouping decision has not been honoured.
- The canonical generation intent is the primary seam, and it is an existing one. Prior art is the existing suite covering flag resolution, requirement resolution, unknown-identifier rejection, and conflicting-flag rejection; the new cases extend it with Category resolution, Category-level all and none, unknown Category names, and the rejection of the removed Component flags.
- Manifest loading is the second existing seam. Prior art is the existing validation suite, which already asserts both directions for pins, paths, effects, and Agent Targets. New cases assert that a missing Category, an unknown Category, and an empty Category each fail at load.
- The interactive flow is tested through the injected asker already used by the prompt suite, which drives the flow without a terminal. Prior art is the existing sequence covering component selection, item selection, and Agent Target selection; it is rewritten as Category selection followed by item selection, with the Agent Target step unchanged. Accepting every default with a plain confirmation must remain a single uninterrupted path.
- Stamp rendering and loading are tested at the existing seams. Prior art is the existing structural assertion on a rendered stamp and the existing version-tolerance cases; new cases assert that version 5 records Categories, that a version 4 stamp derives them on upgrade, and that versions 1 and 2 remain checkable and unupgradable.
- Upgrade is tested at its existing seam for the migration as a whole: a project generated against the previous format is upgraded, the resulting stamp is version 5 with Categories present, previously selected items survive, and a forced failure rolls the whole migration back. The preview path asserts the same plan is reported with nothing mutated.
- The permanent N-1 lifecycle gate is extended to assert this migration: install the previous released version from the index, generate, then run the working tree's inspection, preview, and upgrade against it and assert the version 5 stamp and the preserved selection. This is CI tooling and is exempt from the network boundary that governs the package itself.
- Generation-level coverage keeps the existing three-way shape — everything selected, nothing selected, and one representative mixed selection — restated in Category terms, plus one case that would have failed before: an MCP server selected with no explicit base configuration.
- Unit tests use no network and no filesystem outside the per-test temporary directory.

## Out of Scope

- Mount Points and the injection of Enhancement guidance into Spec Loop skills. That is FR-32 in v0.10 and depends on the Spec Loop being a fixed structure, which FR-31 establishes.
- The Spec Loop becoming always-generated, the Default Set, and the retirement of the catalog cap. Same version, separate spec: FR-31.
- Expanding the Agent Target Map. That is FR-33 in v0.10 and is independent of the selection axis.
- Rewriting the generation skill as an interview. That is FR-34 in v0.10 and depends on this FR's contract being settled first.
- Adding, removing, or re-vendoring any content. This FR changes how existing content is chosen, not what exists.
- Any change to Canonical Content locations, Pointer Stubs, or the symlink question. ADR-015 stands as amended.
- Any localized runtime surface. ADR-016 is unchanged: everything this FR emits is English.

## Further Notes

The Category assignment worth recording is react-doctor. It was initially proposed under Security, which reads plausibly and is wrong: it is a React quality analyzer with no security function. It belongs under Quality alongside the browser end-to-end testing skill, and both mount on the review step of the development loop, so the Category and the eventual Mount Point agree. Assignments are data and can be revised without code, but this one is worth stating because the wrong answer looked right.

Category names enter the flag contract and the stamp on release, which puts them under the same constraint recorded for earlier identifiers: renaming one later breaks inspection and upgrade for every project already stamped. They should be settled before implementation begins rather than during it.

Removing the previous flags rather than aliasing them is a deliberate departure from the precedent set when a component was last renamed, where a deprecated alias survived one version. That precedent applied to a rename with identical semantics. Here the semantics differ — the axis itself changed — so an alias would have to guess a Category-shaped intent from a Component-shaped instruction, and a wrong guess produces a project the script's author did not ask for.
