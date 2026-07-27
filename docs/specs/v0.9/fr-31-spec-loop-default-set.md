# FR-31 — Spec Loop Always Generated, Default Set Replaces the Catalog Cap

Status: Accepted by CEO (2026-07-27)

Version: v0.9

Phase: unassigned (the v0.9 version plan is not yet cut)

Governing decisions: ADR-002, ADR-004, ADR-008, ADR-009, ADR-010, ADR-012 (amended by ADR-018), ADR-014, ADR-016, ADR-017, ADR-018

## Problem Statement

dev-ready ships a development loop and then makes it optional, incomplete, and hard to receive.

It is optional in a way that has no good answer. The Spec Loop is presented as one selectable item beside a token-discipline skill and a security auditor, so a user is asked whether they want a methodology in the same breath as whether they want a linter wrapper. A user who declines it gets a project scaffolded for AI-assisted development with no development process in it, which is the one thing the product exists to supply.

It is incomplete. The loop dev-ready advertises runs grill, spec, tickets, implement, review, and architecture cleanup, and the step that ties the middle together was never shipped. The implement skill — the step that reads a ticket, drives test-first development, and then invokes review — is absent from the vendored content. A generated project therefore describes a cycle, names its steps, and cannot execute the one in the middle. This has been true since the loop was introduced.

It is hard to receive because accepting every default currently means accepting everything. A user who answers nothing gets every catalog item, so the fastest path through the tool is also the heaviest project it can produce. The constraint meant to bound this counts items rather than weight: a large skill and a small one consume the same budget, the ten-item allowance was fully consumed two versions ago, and the number it enforces has no relationship to what a generated project actually costs to carry.

## Solution

The Spec Loop stops being something a project can go without. Every generated project has one, and it gains the missing implement step so the cycle it describes can be executed end to end. It is modelled as the single option in a mandatory Dev Category rather than as an unnamed constant: a project must have a loop, there is exactly one to have, and the project record says which. That framing keeps the loop visible where a user looks for it and makes a second loop a data addition rather than a record-format migration. The identifiers of the items the loop previously required leave the selectable catalog while remaining readable in existing project records.

Around it, the catalog becomes a set of Enhancements — optional additions a user reaches for deliberately. The ten-item cap is retired, because the number of things available to a user who goes looking is not what causes bloat. The limit moves to the Default Set: what a user receives when they accept every default. That set is deliberately small — the Spec Loop and the project's own documentation skeletons — and everything else ships off by default, reachable with an explicit selection. The reference design-document templates are Enhancements rather than defaults: they are opinionated style references, not structure.

Two items leave the product entirely. The project-orientation skill is removed: its whole content directs the agent to read the root rules file and states where the backend and frontend live, and the root rules file is auto-loaded and already says so, so a user loses nothing by its absence. The Handoff Protocol scaffold is removed by a separate FR in the same version.

Configuration that the loop needs is written at generation time with working defaults, so nothing manual stands between generation and a usable project. A user who wants to change those defaults selects the setup Enhancement, which configures the project after generation through an interactive session rather than at generation time.

## User Stories

1. As a user, I want every generated project to carry the development loop, so that the process the tool exists to deliver is not something I can accidentally decline.
2. As a user, I want to see which development loop my project uses while I am choosing, so that the structure I am getting is visible rather than implied.
3. As a user, I want my project record to name the loop it was built with, so that a future version adding a second loop knows which one I have.
4. As a user, I want the loop's implement step present, so that the cycle described in my project's rules can actually be run.
5. As a user, I want the implement step to drive test-first development and then invoke review, so that the steps connect without my having to orchestrate them.
6. As a user, I want the loop offered as a choice with one answer rather than hidden entirely, so that I understand what my project is built around.
7. As a user, I want accepting every default to produce a lean project, so that the fastest path through the tool is not also the heaviest result.
8. As a user, I want to see what the Default Set contains before I accept it, so that accepting defaults is an informed choice rather than a shrug.
9. As a user, I want everything outside the Default Set to be reachable with one explicit instruction, so that a heavier project is still one command away.
10. As a user, I want to add individual Enhancements to the Default Set, so that I can take a security auditor without taking everything else.
11. As a user, I want to decline every Enhancement, so that I can generate a project carrying only the loop and its supporting content.
12. As a user, I want the reference design-document templates offered rather than assumed, so that opinionated style references are something I opt into.
13. As a user, I want no skill whose only content tells me to read a file already loaded into the agent's context, so that nothing in my project costs attention without repaying it.
14. As a user, I want a generated project to work immediately without a configuration step, so that the one-command promise holds.
15. As a user, I want the loop's tracker and documentation locations written with working defaults, so that its skills do not refer me to a setup command that was never shipped.
16. As a user who wants different defaults, I want an optional setup Enhancement that configures the project interactively after generation, so that changing them does not require hand-editing files.
17. As a user who did not select that Enhancement, I want nothing in my project to instruct me to run it, so that I am never pointed at something I do not have.
18. As a user, I want the setup Enhancement to write only into files the generator manages, so that its output stays under the same lifecycle rules as everything else.
19. As a user, I want no part of my project rewritten at runtime by a skill, so that a later upgrade does not treat generated content as something I edited.
20. As a user, I want the report to distinguish what every project receives from what I selected, so that I can tell the structure from my additions.
21. As a user, I want verification to check the loop's presence, so that a project missing part of its structure fails generation rather than being delivered broken.
22. As a user upgrading a project that selected the loop, I want it carried forward, so that nothing I had is lost to the reclassification.
23. As a user upgrading a project that declined the loop, I want it added, so that the upgrade brings me to the same structure a new project would have.
24. As a user upgrading, I want the identifiers that left the catalog to be mapped rather than rejected, so that my existing record does not become unreadable.
25. As a user upgrading, I want a removed item's files retired rather than left behind, so that my project does not accumulate content nothing maintains.
26. As a user upgrading, I want files I edited to be preserved and reported, so that gaining the new structure never discards my work.
27. As a user upgrading, I want the whole change to commit at once or not at all, so that a failure never leaves a project half-restructured.
28. As a user previewing an upgrade, I want the full change shown without mutation, so that I can review a structural change before accepting it.
29. As a user, I want the implement step's content to come from the same pinned source as the rest of the loop, so that its provenance is recorded like everything else.
30. As a maintainer, I want the Default Set declared as manifest data, so that changing what a default project contains is a data change.
31. As a maintainer, I want the Default Set's size limit enforced at manifest load, so that shipped data cannot exceed the budget without failing first.
32. As a maintainer, I want the optional catalog to have no size limit, so that adding an Enhancement no longer requires evicting one.
33. As a maintainer, I want an Enhancement that duplicates a loop step rejected at load, so that the catalog cannot offer a user something the structure already provides.
34. As a maintainer, I want the retired identifiers to be unselectable, so that a script cannot ask for something that is no longer a choice.
35. As a maintainer, I want a second loop to be addable as manifest data, so that the decision to keep the loop named does not have to be paid for twice.
36. As a maintainer, I want the vendored drift guard to cover the newly added step, so that its bytes stay verifiable against the pinned source like the rest.
37. As a maintainer, I want attribution to describe generated loop content accurately, so that the notices stay true once content stops being a verbatim copy.

## Implementation Decisions

- The Spec Loop is written for every generated project. It is modelled as the sole option of the mandatory Dev Category rather than as an unnamed constant: the selection surface presents it, a project cannot decline it, and the resolved loop identifier is recorded in the project stamp. This costs one manifest field and one stamp field today and removes the record-format migration a second loop would otherwise force.
- The loop gains the implement step, vendored from the same pinned source as the rest of its content, with the source path added to the provenance record and covered by the existing byte-equality drift guard. The audit finding that it was never vendored is the direct cause of this addition.
- The bundle identifier that used to make the loop optional, and the identifiers of the three items it required, leave the selectable catalog. They remain readable in existing project records and are mapped during upgrade rather than rejected. Selecting them by identifier is an invalid-arguments failure naming what replaced them.
- The `project-orientation` skill is removed from the catalog and from the product. Its content directs the agent to read the root rules file and the design documents and states where backend and frontend code lives; the root rules file is auto-loaded and carries the same facts. It fails the curation principle's own test, so it is deleted rather than recategorized, and its generated file retires through the obsolete-file rules during upgrade.
- The Default Set is declared as manifest data: the Spec Loop and the project's own documentation skeletons. Every other Catalog Item is an Enhancement declared off by default, including the reference design-document templates, which are opinionated style references rather than project structure.
- Accepting all defaults yields the Default Set. The previous behaviour — accepting defaults yields every catalog item — is replaced. An explicit whole-catalog selection remains available and is the documented way to reach the old outcome.
- The ten-item catalog cap is retired. Its replacement is a limit on the Default Set's size, validated at manifest load so shipped data that exceeds it fails before reaching a user. The optional catalog is unbounded.
- Manifest load additionally validates that no Catalog Item duplicates a Spec Loop step, that no retired identifier appears as a selectable item, and that the Dev Category declares at least one loop. All are load-time errors.
- Generation writes the loop's tracker and documentation configuration with working defaults — a local file-based tracker and the established documentation locations — so no manual step separates generation from a usable project, and so the loop's skills never refer a user to a command that was not shipped.
- The setup capability ships as an ordinary Enhancement, selected like any other. It configures an existing project through an interactive session after generation. It is never a precondition for generation, and content it does not manage never instructs a user to run it.
- Nothing rewrites a Spec Loop skill at runtime. Loop content is vendored under the drift guard, and a runtime edit would mark the file user-modified and permanently exclude it from future upgrades. Configuration the setup Enhancement changes is written to the generator-managed configuration surface, not into skill content.
- Verification treats the loop's presence as a required path, so a project missing part of its structure fails generation rather than being delivered.
- The stamp records the resolved loop identifier alongside the resolved Enhancement selection. Upgrade adds the loop to a project that previously declined it, carries it forward for a project that selected it, maps the retired identifiers, and retires the removed skill's file — all in the same transaction. All planned writes and deletions commit together or roll back together, and user-edited files are preserved and reported rather than replaced or deleted.
- Attribution is corrected to describe generated loop content as derived rather than verbatim where generation composes it, keeping the notices accurate ahead of FR-32, which introduces injection into the same content.

## Testing Decisions

- A good test here asserts what a generated or upgraded project contains and what a given selection resolves to. It does not assert which module wrote a file, the order of writes, or the internal shape of the selection object. The loop's presence is tested as an observable property of the output tree, not as a branch that was taken.
- The canonical generation intent is the primary seam and is an existing one. Prior art is the existing flag-resolution and requirement-resolution suite. New cases assert that accepting defaults yields the Default Set rather than the whole catalog, that an explicit whole-catalog selection still yields everything, that declining every Enhancement still yields the loop, that the resolved loop identifier is always present, and that a retired identifier is rejected with a message naming its replacement.
- Manifest loading is the second existing seam, and its validation suite already asserts both failure directions for every other rule. New cases assert that an over-budget Default Set fails, that an item duplicating a loop step fails, that a retired identifier declared as selectable fails, and that a Dev Category with no loop fails.
- Overlay application is tested at its existing seam by asserting the output tree: the loop's content is present for a selection that includes no Enhancements at all, and the implement step is present in every case. Prior art is the existing suite that asserts written paths for a given selection.
- The drift guard and the notices synchronization check are tested through their existing maintainer-script suites, extended for the newly vendored path. Prior art is the existing coverage asserting both directions — a missing entry fails and an orphan entry fails.
- Upgrade is tested at its existing seam across three starting points: a project that selected the loop, a project that declined it, and a project carrying the retired identifiers and the removed skill. Each asserts the resulting structure, the retirement of the removed skill's file, the preservation of an edited copy of that same file, and the reported divergence. A forced failure asserts a complete rollback of writes and deletions together, and the preview path asserts the same plan with nothing mutated.
- The permanent N-1 lifecycle gate is extended to assert that a project generated by the previous released version receives the loop through upgrade without losing its prior selection. This is CI tooling and is exempt from the network boundary governing the package itself.
- Generation-level coverage keeps its three-way shape — defaults accepted, everything selected, every Enhancement declined — with the loop asserted present in all three.
- Unit tests use no network and no filesystem outside the per-test temporary directory.

## Out of Scope

- Mount Points and the injection of Enhancement guidance into loop skills. That is FR-32 in v0.10. This FR establishes the fixed structure that FR-32 injects into; it performs no injection.
- Category-first selection, the removal of the previous selection flags, and the stamp advancing to version 5. Same version, separate spec: FR-30. The stamp change is specified there and is not restated here.
- Removing the Handoff Protocol scaffold from generated projects. Same version, separate spec: FR-35 (ADR-020). Its files retire through the same obsolete-file pass this FR uses, but the decision, its cost, and its migration cases belong there.
- Adding a second development loop. This FR makes that a data addition; it adds no second loop and defines no criteria for accepting one.
- Expanding the Agent Target Map, and rewriting the generation skill as an interview. Those are FR-33 and FR-34 in v0.10.
- A measured context budget. The Default Set size limit is the instrument for this version; a weight-based budget is a candidate for a later version once there is usage data to calibrate a threshold against.
- Any change to Canonical Content locations, Pointer Stubs, or Agent Targets.
- Adopting graphify or any other new third-party content. Evaluated and not adopted; the reasoning is recorded in the roadmap.
- Any localized runtime surface. ADR-016 is unchanged: everything this FR generates is English, because its consumer is a model.

## Further Notes

Modelling the loop as a named single-select rather than an unnamed constant was a late correction. The first draft made it invisible — no Category, no stamp entry — which was simpler and wrong in two ways: it hid the loop from the menu where users look for the thing their project is built around, and it guaranteed a record-format migration the day a second loop appeared, because nothing recorded which loop a project had. Naming it costs one manifest field and one stamp field now. It also reopens ADR-012's "preset, not framework" deferral to the smallest possible degree — a single-valued field, not a preset ecosystem — and that reopening is deliberate.

The implement step being absent is the finding that most justifies this FR's timing. It means the loop has been advertised in generated projects for two versions with its middle step missing, and no amount of selection UX work would have surfaced it — it is visible only by comparing the vendored source paths against the cycle the generated rules describe.

Retiring the numeric cap removes a constraint that twice forced a real curation decision, and nothing replaces that pressure for a user who selects everything. The Default Set limit protects the default path only. This is an accepted consequence rather than an oversight: the alternative instrument, a measured weight budget, needs a defensible threshold, and there is no usage data to derive one from while the real-users gate remains open.

The change to what accepting defaults produces is the most visible break in this version for anyone with existing automation. It should be stated in the changelog in terms of the outcome — a default project is now lean — rather than in terms of the flag, because a reader scanning for breakage will be looking for what their project now contains.
