# FR-23 — Configurable Handoff Protocol

Status: Accepted (2026-07-25)

Version: v0.7

Phase: 2

Governing decisions: ADR-007, ADR-010, ADR-011, ADR-012, ADR-013, ADR-014

## Problem Statement

Generated projects currently communicate a fixed multi-agent process through prose and legacy phase documents. Role assignments cannot be changed in one authoritative place, model names risk becoming behavioral rules, and the old planning and implementation handoffs do not match the accepted process-v2 split between durable specs, ticket dispatch, execution reports, and review gates. Users need a protocol that is configurable as data while preserving stable responsibilities and safe upgrade behavior.

## Solution

Generate one authoritative Handoff Protocol Configuration for projects that select the agents component. It defines seven stable role identifiers, editable titles and nullable model assignments, responsibilities, prohibitions, sequence, escalation, reporting, and commit authority. Generated guidance refers to the configuration instead of duplicating editable values. Fresh projects use durable specs and ticket-based phase work; upgrades retire untouched legacy managed files transactionally while preserving user-modified copies.

## User Stories

1. As a project owner, I want one authoritative protocol configuration, so that changing a role assignment does not require hunting through generated prose.
2. As a project owner, I want seven distinct stable role identifiers, so that planning, execution, and the three independent review concerns remain unambiguous.
3. As a project owner, I want role titles to be editable data, so that I can adapt terminology without changing the protocol's behavioral identity.
4. As a project owner, I want model assignments to be editable and nullable, so that a role can be human, unassigned, or filled by any suitable agent.
5. As a project owner, I want behavior bound to role identifiers rather than model names, so that changing tools does not silently change responsibilities.
6. As a Tech Lead, I want my planning and architectural responsibilities stated explicitly, so that the phase enters dispatch with accepted decisions.
7. As a Senior Engineer, I want ticket dispatch and spec-review duties stated explicitly, so that implementation remains traceable to the accepted spec.
8. As a Junior Engineer, I want one-ticket-at-a-time scope and stop rules stated explicitly, so that I do not work beyond the declared footprint or grind on hard blockers.
9. As a QA reviewer, I want an independent gate and artifact, so that functional quality findings remain visible and attributable.
10. As a Security reviewer, I want an independent gate and artifact, so that security findings cannot be conflated with general QA.
11. As an SRE reviewer, I want an independent gate and artifact, so that operability and failure behavior receive a dedicated review.
12. As a CEO, I want commit and merge authority stated explicitly, so that agents do not perform state-changing Git actions outside the release exception.
13. As an agent entering a generated project, I want the handoff order and stop/escalation rules available in the protocol, so that I can act correctly without relying on chat history.
14. As a contributor, I want specs to be durable and commit-worthy, so that the code can be reviewed against an accepted product contract.
15. As a contributor, I want active ticket, gate, and report files ignored, so that working coordination documents do not enter project history accidentally.
16. As a contributor, I want the reusable phase scaffold and protocol retained, so that new phases can be opened consistently.
17. As a user generating without the agents component, I want no Handoff Protocol assets or prose, so that deselected methodology does not leak into my project.
18. As a user upgrading from v0.6, I want untouched obsolete managed handoff files removed, so that the generated methodology does not present conflicting processes.
19. As a user who edited an obsolete handoff file, I want it preserved and reported, so that migration never deletes my work.
20. As a user previewing an upgrade, I want planned deletions shown without mutation, so that I understand the migration before accepting it.
21. As a user recovering from a failed upgrade, I want additions, updates, and deletions rolled back together, so that the project returns to its original state.
22. As a maintainer, I want only one default role topology, so that v0.7 establishes a clear contract without prematurely creating a preset ecosystem.

## Implementation Decisions

- The Protocol Configuration is the sole runtime authority for role titles, model assignments, responsibilities, prohibitions, sequence, escalation, reporting, and commit rules.
- The public role identifiers are `ceo`, `tech_lead`, `senior_engineer`, `junior_engineer`, `qa_reviewer`, `security_reviewer`, and `sre_reviewer`.
- Each role record carries a title, nullable model, responsibilities, and prohibited actions. A null model means human or deliberately unassigned and never changes protocol behavior.
- Generated instructions, the handoff README, phase scaffolds, and review gates refer to stable role identifiers and the authoritative configuration. They do not copy editable titles or model values.
- The generated process follows ADR-013: durable feature specs, per-ticket dispatch, one ticket at a time, execution reports, Senior review, and separate QA, Security, and SRE gates.
- Fresh projects do not receive active legacy planning and implementation documents. The reusable phase scaffold contains tickets and review/report structure for process v2.
- Active numeric phase directories are ignored locally while the protocol, README, reusable phase scaffold, and specs remain durable.
- Handoff assets and guidance are conditional on the agents component. The overlay renderer receives resolved answers as input and does not load manifest policy itself.
- When documentation and agents are both selected, the protocol assigns architecture-document maintenance to `tech_lead`. Documentation without agents contains no role language.
- Upgrade retires an obsolete managed file only when its current hash matches the previously recorded inventory. Modified obsolete files are preserved and reported.
- Deletions participate in dry-run reporting, backup, rollback, final reporting, and idempotence with the same transactional guarantee as additions and updates.
- Only one built-in topology ships in v0.7. The configuration is editable after generation, but there is no preset registry, plugin system, or interactive team designer.

## Testing Decisions

- The primary generation seam is complete overlay rendering from resolved answers. Tests inspect the user-visible output tree and rendered content rather than individual template helper calls.
- The migration seam is the public upgrade operation over a stamped temporary project. Tests cover clean obsolete deletion, modified-obsolete preservation, dry-run reporting, rollback, and a repeated no-op upgrade.
- The protocol schema is tested for all seven stable identifiers, required fields, nullable model behavior, handoff order, and explicit stop, escalation, report, and commit rules.
- Rendered outputs are checked to ensure editable titles and model values occur only in the Protocol Configuration and no unresolved template tokens remain.
- Selection tests cover agents on and off, documentation with and without agents, and the shared matrix with the Spec Loop described by FR-28.
- Ignore behavior is tested at the generated-project boundary: numeric phase work is ignored, while protocol, scaffold, and specs remain trackable.
- Unit tests use only temporary directories and no network. Existing overlay, upgrade, check, and verification tests provide the prior art.

## Out of Scope

- Multiple built-in team presets, a preset registry, or plugin mechanics.
- Binding behavior to a particular model or vendor.
- Changing the CEO's Git authority or the scoped release exception.
- Shipping the Spec Loop assets themselves; FR-28 owns that catalog contract.
- Creating active project phases during initial generation.
- Internationalization, additional render targets, or a web-based protocol editor.

## Further Notes

FR-23 and FR-28 are implemented in the same phase because they share generated instruction surfaces. They remain separate specs so protocol configuration and catalog dependency behavior can be reviewed independently. The canonical generated configuration is `docs/handoffs/protocol.yaml`; stable role identifiers are part of the compatibility surface once released.
