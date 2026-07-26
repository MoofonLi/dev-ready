# FR-26 — Multi-Agent Render Targets

Status: Accepted by CEO (2026-07-26)

Version: v0.8

Phase: unassigned (the v0.8 version plan is not yet cut)

Governing decisions: ADR-002, ADR-004, ADR-010, ADR-011, ADR-014, ADR-015

## Problem Statement

A generated project configures exactly one coding agent. Skills, project rules, and MCP configuration are written only where Claude Code looks for them, so a user working in Cursor, Codex, Windsurf, or any other harness receives a project whose entire agent configuration is invisible to the tool they actually use. The content itself is portable — the Agent Skills format is a standard — but the discovery locations and configuration formats are not. Today the only remedies are to hand-copy files into a second location and maintain both, or to abandon the overlay. Teams whose members use different agents cannot share one generated project without one member losing the benefit dev-ready exists to deliver.

## Solution

Generate the overlay once at the open-standard location and point every selected agent at it. Canonical Content — skills and project rules — is always written, independent of selection, so a standard-compliant harness needs nothing else. Users additionally select Agent Targets: coding agents that read from a uniquely-named directory instead. Each selected Agent Target receives Pointer Stubs at its native paths that identify each item and direct the agent to the Canonical Content. The set of Agent Targets and their paths is manifest data, so supporting another agent is a data change rather than a code change. Existing projects migrate to the same layout through the upgrade path, preserving any file the user has edited.

## User Stories

1. As a user of a standard-compliant agent, I want the overlay written at the open-standard location by default, so that my agent discovers it with no selection or configuration on my part.
2. As a Cursor, Codex, Cline, Zed, or OpenCode user, I want a generated project to work without naming my agent at all, so that I am not blocked by an incomplete target list.
3. As a Claude Code user, I want my agent's native directories populated, so that upgrading to this version does not degrade the experience I already have.
4. As a Windsurf user, I want my agent's uniquely-named skills directory populated, so that I get the same discovery my colleagues get.
5. As a member of a mixed-tool team, I want one generated project to serve several agents at once, so that we do not maintain divergent copies of the same guidance.
6. As a user, I want to select my agents non-interactively by identifier, so that I can script generation and drive it from another agent.
7. As a user, I want to select my agents interactively from a described list, so that I can choose without memorizing identifiers.
8. As a user, I want an unknown agent identifier rejected immediately with the valid identifiers listed, so that a typo fails before anything is written.
9. As a user, I want each item's guidance stored exactly once, so that editing it updates every agent's view of it at the same time.
10. As a user, I want per-agent files to be ordinary files rather than links, so that my project remains portable across platforms and filesystems that do not support links.
11. As a user, I want a Pointer Stub to carry the item's name and description, so that my agent can decide whether to load an item before following the pointer.
12. As a user, I want project rules written at the standard location, so that every agent that reads that standard receives the same rules.
13. As a Claude Code user, I want my agent's rules file to reference the canonical rules, so that there is exactly one authoritative copy to edit.
14. As a user, I want MCP configuration written for agents that support a project-level configuration, so that selected servers are available without manual setup.
15. As a user of an agent whose MCP configuration is user-global, I want to be told plainly that I must configure it myself, so that I am not left assuming it was done.
16. As a user, I want the report to state what each selected agent received, so that I can confirm the outcome without exploring the tree.
17. As a user upgrading an existing project, I want it migrated to the shared layout, so that I gain multi-agent support without regenerating.
18. As a user upgrading, I want files I edited to be preserved rather than replaced by a pointer, so that migration never discards my work.
19. As a user upgrading, I want any divergence created by that preservation reported, so that I can reconcile it deliberately.
20. As a user upgrading, I want untouched superseded files removed in the same transaction that adds their replacements, so that the project never carries two conflicting copies.
21. As a user previewing an upgrade, I want the full migration shown without mutation, so that I can review a structural change before accepting it.
22. As a user whose upgrade fails, I want additions, replacements, and deletions rolled back together, so that the project returns to its original state.
23. As a user upgrading a project generated before Agent Targets existed, I want my agent inferred rather than being asked to re-specify it, so that the upgrade needs no new input.
24. As a user, I want my selected agents recorded in the project stamp, so that later commands know what the project is expected to contain.
25. As a user, I want verification to check the paths implied by my selection, so that a partially written project fails generation rather than being delivered broken.
26. As a user who selects no additional agents, I want no agent-specific directories created, so that deselected content does not appear in my project.
27. As a maintainer, I want the agent list and its paths held as data, so that adding an agent does not require touching generation logic.
28. As a maintainer, I want the component that generates the Handoff Protocol scaffold named for what it produces, so that it is not confused with agent selection.
29. As an existing user, I want the previous component flag to keep working for a version, so that my scripts do not break without warning.
30. As a maintainer, I want one authoritative rendering shared by generation and upgrade, so that the two paths cannot diverge.

## Implementation Decisions

- Canonical Content is written for every project regardless of Agent Target selection: skills at the open Agent Skills standard directory, and project rules as the standard root rules file. Standard-compliant harnesses are served entirely by it and require no declared Agent Target.
- Agent Targets are declared in the manifest as data. Each record carries an identifier, a description for selection prompts, a skills directory, a nullable rules file, and a nullable MCP configuration file. Nullable fields mean the agent needs no artifact of that kind.
- This version declares the two verified agents whose layouts deviate from the standard. The declared paths are transcribed from a moving external ecosystem and must be re-verified when the spec is implemented and at each pin bump; no byte-equality guard exists for them.
- Per-target artifacts are Pointer Stubs: ordinary files carrying the item's name and description and directing the agent to the Canonical Content. They are never symbolic links, because generation refuses link destinations by construction, the stamp inventory hashes file bytes, and links require elevated permissions on some supported platforms. They are never duplicates of the content.
- Selection follows the established item-selection contract: a comma-separated list of identifiers, `all`, or `none`, resolved before confirmation, rendering, reporting, verification, and stamping. Unknown identifiers fail as invalid arguments and list the valid identifiers. Interactive selection presents the described list with all entries enabled by default.
- MCP configuration is rendered only for an Agent Target that declares a project-level configuration file. An agent whose configuration is user-global receives none, and the report states that it must be configured manually. Generation never writes outside the target project directory.
- All Agent Target output is produced by the single authoritative overlay-rendering operation already shared by generation and upgrade. No second rendering path exists, so migration, the stamp inventory, drift reporting, and verification inherit the same result by construction.
- The resolved answers model carries the selected Agent Targets. The overlay renderer receives resolved answers and does not consult manifest policy itself.
- The project stamp advances a version. It records the selected Agent Targets as Overlay Currency. The upstream repository and commit remain immutable Base Provenance, unchanged by this feature.
- The component that generates the Handoff Protocol scaffold is renamed to match what it produces, freeing the agent vocabulary for Agent Target selection. The previous flag remains accepted as a deprecated alias for one version. The rename travels in the same stamp migration as Agent Targets, so only one migration occurs.
- Upgrading a project stamped before Agent Targets existed infers Claude Code as its sole Agent Target, because no other layout was generable. Superseded per-agent content retires through the existing obsolete-file rules: a file whose bytes still match the recorded inventory is deleted transactionally and replaced by its Pointer Stub, while a user-modified file is preserved, its stub write skipped, and both facts reported.
- Verification checks the paths implied by the recorded selection, including Canonical Content and each selected Agent Target's required artifacts.

## Testing Decisions

- A good test here asserts the user-visible output tree and rendered content, not the internal helpers that produced them. Tests state what a user would find in a generated project and what a report would tell them.
- The primary seam is the existing authoritative overlay-rendering operation, exercised through resolved answers. Because generation and upgrade both consume it, correctness is asserted once at that seam rather than separately per command. No new seam is introduced.
- Rendering tests cover: Canonical Content present with no Agent Target selected; each declared Agent Target selected alone; both selected together; and stub content carrying the correct item name and description while remaining distinct from the canonical bytes.
- Stub tests assert that no output path is a symbolic link and that canonical content appears exactly once regardless of how many Agent Targets are selected.
- Selection tests cover identifier lists, `all`, `none`, unknown identifiers, and the deprecated component alias, at the same seam as the existing item-selection tests.
- The migration seam is the public upgrade operation over a stamped temporary project. Tests cover clean supersession, modified-file preservation with the stub skipped and both reported, dry-run reporting of the full migration, rollback, and a repeated upgrade producing no further change.
- Stamp tests cover the version advance, recorded Agent Targets, inference for a pre-feature stamp, the component rename, and the immutability of Base Provenance across the migration.
- Verification tests cover a project missing Canonical Content and a project missing a selected Agent Target's artifacts.
- The permanent N-1 lifecycle gate is extended to assert the layout migration, not only content currency.
- Unit tests use temporary directories only and perform no network access. Existing overlay, upgrade, stamp, inspection, and prompt tests are the prior art for all of the above.

## Out of Scope

- Localization of any string introduced here; FR-25 owns the message catalog and follows this work.
- Declaring every agent the external installer supports, or importing its mapping table wholesale.
- Per-agent MCP configuration for agents whose configuration is user-global, and any write outside the target project directory.
- Symbolic-link or per-agent full-copy installation modes.
- Per-agent variation in item content. Agent Targets change where guidance is discovered, never what it says.
- Stack-aware or template-aware target behavior; that arrives with the second base template.
- A preset or registry mechanism for user-defined agents beyond editing the generated project.

## Further Notes

The Canonical Content plus Pointer Stub arrangement is the pattern this repository already applies to itself under ADR-011, where authoritative skills live at the standard location and thin discovery stubs sit at the Claude Code path. FR-26 productizes that arrangement rather than inventing one.

Agent Target identifiers become a compatibility surface once released: they appear in flags, in prompts, and in the stamp. The set of declared agents may grow as data, but an identifier that has shipped cannot be renamed without a migration.

This spec must be implemented before FR-25 in the same version. FR-26 introduces new user-facing strings — the selection flag and prompt, per-agent report lines, and verification messages — and FR-25's message catalog is built once over the final string set, following the sequencing precedent set when FR-29 preceded FR-25.
