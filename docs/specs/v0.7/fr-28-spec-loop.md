# FR-28 — Spec Loop Bundle and Methodology Layering

Status: Accepted (2026-07-25)

Version: v0.7

Phase: 2

Governing decisions: ADR-002, ADR-008, ADR-009, ADR-010, ADR-012, ADR-013, ADR-014

## Problem Statement

The catalog provides execution-oriented skills but not the complete planning and dispatch loop advertised by the project. Installing only the four headline skills would still leave cross-skill dependencies and tracker configuration missing. At the same time, the loop must work without the Handoff Protocol, layer cleanly when agents are selected, respect the documentation component, preserve explicit selections across upgrade, and stay within the accepted catalog cap.

## Solution

Add one explicit `spec-loop` catalog item backed by the complete, manifest-pinned dependency closure of the four advertised steps: grill-with-docs, to-spec, to-tickets, and improve-codebase-architecture. Selecting it deterministically resolves the existing TDD, diagnosis, and code-review catalog items, materializes all required vendored assets and a role-neutral local tracker configuration, and records the resolved selection. Generated guidance follows a three-axis matrix over agents, Spec Loop, and documentation, adding role mapping only when both methodologies are selected.

## User Stories

1. As a user, I want to select the full Spec Loop as one catalog item, so that I do not need to understand its internal dependency graph.
2. As a user, I want all four advertised planning and improvement steps to be present, so that the documented loop is executable rather than aspirational.
3. As a user, I want every companion skill and support file required by those steps, so that cross-skill invocations never fail because of an incomplete bundle.
4. As a user, I want the bundle sourced from one exact repository commit, so that generation is reproducible and never depends on upstream latest.
5. As a user, I want selecting `spec-loop` to include TDD, diagnosis, and code review automatically, so that the execution half of the loop is complete.
6. As a user, I want automatic requirements shown in the resolved selection, so that generation is transparent about what will be installed.
7. As a user, I want the resolved selection recorded in the generation stamp, so that check and upgrade can reproduce it later.
8. As a user, I want existing execution skills to remain independently selectable, so that v0.7 does not break existing catalog choices.
9. As a user explicitly selecting no skills, I want no skills installed, so that dependency resolution does not override an explicit `none` choice.
10. As a user upgrading a v0.6 project, I want my stamped selection preserved, so that a new default does not silently add methodology or requirements.
11. As a user selecting the Spec Loop without agents, I want role-neutral guidance and tracker configuration, so that the loop works for one person or agent.
12. As a user selecting agents without the Spec Loop, I want only Handoff Protocol guidance, so that unselected skills are never referenced.
13. As a user selecting both, I want the four process layers mapped to stable protocol roles, so that planning, dispatch, execution, and verification fit together.
14. As a user selecting documentation, I want generated guidance to link to the architecture document, so that agents can find binding module boundaries.
15. As a user selecting documentation without agents, I want no role-specific maintenance language, so that a role system is not implied.
16. As a Tech Lead using both documentation and agents, I want architecture maintenance assigned through the protocol, so that ownership is explicit.
17. As an agent invoking domain modeling, I want required tracker and domain configuration available, so that I am not redirected to a missing setup skill.
18. As a user, I want domain terminology created only when needed, so that generation does not pre-create an empty root glossary.
19. As a maintainer, I want dependency identifiers validated within their component, so that malformed relationships fail before generation.
20. As a maintainer, I want self-dependencies and cycles rejected, so that selection resolution always terminates.
21. As a maintainer, I want transitive resolution deterministic, so that prompts, reports, stamps, verification, and upgrades agree on one item set.
22. As a maintainer, I want vendored drift checked against the exact pin, so that upstream changes cannot enter unnoticed.
23. As a maintainer, I want third-party notices synchronized with the shipped subset, so that attribution and licensing remain accurate.
24. As a maintainer, I want the catalog to remain at exactly ten items, so that FR-28 consumes the final reserved slot without hidden companion entries.
25. As a user running verification, I want missing selected assets and unexpected deselected assets detected, so that a project cannot claim a selection it does not contain.
26. As a user running check after an overlay upgrade, I want Base Provenance preserved and Overlay Currency current, so that lifecycle state stays truthful.

## Implementation Decisions

- `spec-loop` is one explicit skills-catalog compatibility identifier. Its shipped assets include the complete pinned closure needed by the four advertised steps, not four separately selectable new items.
- The existing source-repository entry and pin are reused. A second pin for the same upstream repository is forbidden.
- At the audited pin, the closure includes the companion grilling, domain-modeling, and codebase-design skills plus every support file referenced inside the selected trees. Implementation must re-walk invocations and relative references instead of relying only on remembered directory names.
- The catalog item declares requirements on the existing `tdd`, `diagnosing-bugs`, and `code-review` identifiers. Those items remain independently selectable for compatibility.
- Requirements must refer to existing identifiers in the same component. Missing identifiers, self-dependencies, and dependency cycles invalidate the manifest.
- Resolution is deterministic and transitive. It occurs before answers are finalized and the same resolved set drives user reporting, rendering, verification, stamping, check, and upgrade.
- An explicit `none` selection has an empty closure. A v0.6 stamp retains its recorded selection during upgrade and does not inherit a new default.
- The bundle ships original role-neutral tracker and domain configuration so the upstream skills can operate without a separate setup step.
- With agents deselected, the tracker remains local and role-neutral. With agents selected, its artifact locations align with the process-v2 specs and ticket handoffs.
- Generated guidance follows three independent axes: agents controls Handoff Protocol assets and prose; resolved Spec Loop selection controls loop assets and neutral guidance; documentation controls the architecture link.
- The combined agents-plus-loop case adds the ADR-012 layer mapping: planning by `tech_lead`, dispatch by `senior_engineer`, execution by `junior_engineer`, and verification by the three reviewer roles.
- No rendered section may reference an unselected asset. Role language appears only when agents are selected.
- The existing generated architecture document remains the durable architecture artifact. It includes a system overview, module boundaries, and dependency rules; no duplicate template is introduced.
- Generation does not create a root domain glossary. The selected domain-modeling skill may create one lazily when a real term is resolved.
- Vendored synchronization and notices checks remain the authoritative provenance and licensing gates for all newly included upstream assets.
- Overlay upgrade preserves Base Provenance, advances Overlay Currency, and maintains the exact resolved selection already recorded by the project.

## Testing Decisions

- The highest feature seam is selection resolution followed by complete overlay rendering and project verification. Tests assert the resolved item set and user-visible assets rather than private recursion mechanics.
- Manifest-focused tests cover valid transitive requirements, deterministic ordering, missing identifiers, cross-component references, self-dependencies, and multi-item cycles.
- Rendering tests cover the full three-axis matrix over agents, resolved Spec Loop, and documentation, including all-off, all-on, and mixed selections.
- Bundle tests assert the complete expected asset closure, required tracker/domain configuration, exact ten-item catalog count, and automatic inclusion of the three existing requirements.
- Stamp, check, and upgrade tests prove that resolved selections are recorded and reproduced, while old stamped selections do not acquire new defaults.
- Verification tests remove one selected asset and add one deselected asset to prove both failure directions at the project boundary.
- Provenance tests use the existing vendored synchronization and notices checks. Unit tests do not contact the upstream repository.
- Tests prove that generation does not create a root glossary and that no rendered guidance points to an absent protocol, skill, tracker, or architecture document.
- Existing manifest, overlay, synchronization, notices, verification, check, and upgrade suites provide the prior art and remain offline with temporary-directory isolation.

## Out of Scope

- A second methodology preset or another catalog item for companion skills.
- A second pin for the same upstream skills repository.
- An interactive tracker setup phase or invocation of an upstream setup skill.
- Pre-creating a root domain glossary.
- Multiple handoff presets, internationalization, render targets, or a plugin ecosystem.
- Changing upstream skill behavior beyond the original configuration and integration needed to make the pinned bundle usable.
- Installing the FR-24 repository distribution skill into generated projects.

## Further Notes

The `spec-loop` identifier and its dependency semantics become a compatibility surface once released. FR-23 owns the Handoff Protocol schema; this spec owns methodology assets, selection closure, and conditional layering. Both are reviewed together in Phase 2 because they share generated instruction rendering.
