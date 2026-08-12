# ADR-017: Category replaces Component as the user-facing selection axis

- Status: **Accepted** (2026-07-27, CEO Moofon). Targets v0.9; amends ADR-010 (replaces the axis item-level selection hangs off) and supersedes the component half of the FR-3/FR-14 CLI contract.
- Context: Users select along Components — `skills`, `mcp`, `docs`, `handoff` — because that is how the overlay files are grouped internally. That grouping is an implementation fact, not a user's mental model, and three symptoms have accumulated. (1) The groups a user actually reasons about cut across Components: a Design grouping wants both the `frontend-design` skill and the awesome-design-md DESIGN.md templates; a token-discipline grouping wants both the `caveman` skill and the `code-memory` MCP server. (2) `docs` and `handoff` never received item-level selection because they were modelled as single boolean Components, so the two vendored DESIGN.md templates have been unselectable since v0.4. (3) Pure infrastructure leaked into the catalogue of things a user picks: `mcp-config` is a selectable `mcp` item that merely creates the empty `.mcp.json` every other MCP item writes into, and deselecting it while selecting `code-memory` fails generation — behaviour currently pinned by `test_code_memory_without_mcp_config_raises_overlay_error`. A presentation-only fix was considered and rejected as insufficient: it leaves the flag surface, the stamp, and the infrastructure leak untouched.
- Decision: Category becomes the axis, Component becomes internal.
  - **Categories are the top-level selection**: Dev, Security, Quality, Design, Token Optimize. Each Catalog Item declares exactly one Category as manifest data — the FR-14 catalog-as-data principle applied to the axis itself.
  - **Dev is a mandatory single-select** holding the development loop (ADR-018); the other four are multi-select and may be declined entirely.
  - **Categories are named for what they hold today.** "Ops" was proposed and rejected: its only member is browser end-to-end testing, which is quality assurance, not operations. Naming a Category for content it might hold later is the one mistake that cannot be undone cheaply — a new Category is an added value with no migration, while renaming one breaks inspection and upgrade for every stamped project. Genuine deployment or CI content, if it ever arrives, gets an Ops Category then.
  - **Component survives only as a write-location grouping.** It decides where a selected item's files land and is never presented, prompted for, or named in a user-facing flag.
  - **`mcp-config` stops being a Catalog Item.** The base `.mcp.json` is infrastructure, generated automatically when any selected item needs it and absent when none do. The selection that fails today becomes valid.
  - **Design-doc templates become selectable items** under the Design Category, closing the v0.4 gap.
  - **The stamp advances to version 5**, recording Categories alongside the resolved item set; v4 stamps migrate without new input, and `check`/`upgrade` keep reading v3 and v4.
- Considered options:
  - **Category as a presentation layer over an unchanged contract** — rejected: it delivers the menu and nothing else. The flags stay Component-shaped, `docs` stays boolean, and `mcp-config` stays a selectable item, so all three symptoms survive.
  - **Category as a grouping inside `skills` only** — rejected: the two groupings that motivated the change, Design and Token Optimize, both need non-skill items, so this cannot express the requirement it exists to serve.
  - **Keeping both axes user-facing** — rejected: two overlapping vocabularies for one selection is exactly the ambiguity ADR-012 spent a decision removing from the word "workflow".
- Status update (2026-08-12): amended by [ADR-024](adr-024-engineering-flow-selection-spine.md) — Dev leaves the *presented* Category set (it becomes the Engineering Flow question, asked first and under its own name), the remaining four Categories are walked one at a time with no preceding filter, and the `token-optimize` description widens. See the amendment below; the axis decision itself is unchanged.
- Consequences: This is the largest CLI break since FR-14. `--skills`, `--mcp`, `--no-docs`, and `--no-handoff` are replaced; the FR-24 skill that composes those flags must be rewritten; the permanent N-1 lifecycle gate must assert the v4→v5 stamp migration as well as content currency. Category names enter the flag contract and the stamp, so renaming one later carries the same cost ADR-012 recorded for `spec-loop`. Assigning every item exactly one Category is a curation judgement with no mechanical check; `react-doctor` is the case worth recording, because it reads as a security concern and is not one — it is a React quality analyzer and belongs under Quality.

## 2026-08-12 amendment — Dev leaves the presented set; Categories are walked one at a time

Decided in the `grill-with-docs` session of 2026-08-12 (ADR-024). Category
remains the axis; what changes is how the axis is presented and one description.

**Dev is no longer offered in a checkbox.** This ADR made Dev "a mandatory
single-select", and the implementation listed it alongside the four optional
Categories and then force-added it whether or not it was checked
(`collect.py:186-197`) — an option whose selection has no effect. Dev also holds
no Enhancement: its only member is the development loop. It becomes the
**Engineering Flow** question, asked first and under its own name. The Category
id `dev` is unchanged in the manifest, the flag contract, and every stamp;
nothing migrates. Only the checkbox loses a row that could not matter.

**The "which Categories?" filter is removed.** The four optional Categories are
now walked in a fixed order, each with its own item list, and declining one is
pressing Enter on it. The filter asked the same axis twice, and it reproduced
one level up the failure FR-36 was created to fix: a user who did not check
Design never learned what Design held.

**`token-optimize` widens its description, and keeps its id.** The Category is
gaining `i-have-adhd`, whose value is that an agent's output stays legible
rather than that fewer tokens are spent — while `caveman`, already in the
Category, has always straddled both ("Token-discipline **and concise response
guidance**"). The id enters the flag contract and every stamp and is expensive
to change; the description enters neither and is free. So the description grows
to cover both halves and the id stays. A new Category was considered and
rejected: it would split two closely related items across two menus to fix a
wording problem.
