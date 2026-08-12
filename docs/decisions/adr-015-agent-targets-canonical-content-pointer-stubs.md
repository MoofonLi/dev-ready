# ADR-015: Agent Targets render as Pointer Stubs over one Canonical Content copy

- Status: **Accepted** (2026-07-26, CEO Moofon). Implements FR-26 (v0.8); amends ADR-010 (adds a selection dimension) and ADR-014 (extends obsolete-file retirement to a layout migration). **Partly superseded by [ADR-025](adr-025-skill-delivery-mode.md) (2026-08-12): the Canonical Content decision stands unchanged and ADR-025 depends on it, but Pointer Stubs are retired in favour of a user-selected Skill Delivery Mode — `symlink` or `copy`. See the 2026-08-12 note below before citing the symlink rejections.**
- Context: The overlay renders for Claude Code only — `CLAUDE.md`, `.claude/skills/`, `.mcp.json`. FR-26 (D-4) adds user-selected coding agents as a second selection axis. The ecosystem has since converged: the Agent Skills standard location is `.agents/skills/`, and the reference installer (`vercel-labs/skills`, which distributes mattpocock/skills) maps 70+ agents to paths — most standard-compliant harnesses (Cursor, Cline, Zed, OpenCode, Codex) read `.agents/skills/` directly, while a minority use uniquely-named directories (Claude Code `.claude/skills/`, Windsurf `.windsurf/skills/`). That installer offers symlinks-to-a-canonical-copy or per-agent copies. This repo already solved the same problem for itself in ADR-011: authoritative skills in `.agents/skills/`, thin discovery stubs in `.claude/skills/`.
- Decision: productize the ADR-011 pattern.
  - **Canonical Content** is always written, independent of selection: skills at `.agents/skills/<id>/`, project rules at `AGENTS.md`. Every Agent Target reads the same bytes.
  - **Agent Targets** are selected per project (`--agents claude,windsurf`) and declared as manifest data (`agent_targets: {id: {skills_dir, rules_file, mcp_file}}`), so adding an agent is a data change — the FR-14 catalog-as-data principle applied to a second axis. v0.8 declares only the two verified deviators, Claude Code and Windsurf; standard-compliant harnesses need no entry because `.agents/skills/` already serves them.
  - Per-target artifacts are **Pointer Stubs**, never symlinks and never content copies. `CLAUDE.md` becomes `@AGENTS.md`.
  - `mcp_file` is nullable and populated for Claude Code (`.mcp.json`) only in v0.8. Windsurf's MCP config is user-global, and dev-ready never writes outside the project directory; the report states this rather than skipping silently.
  - The `agents` **component** is renamed `handoff` (it always meant the Handoff Protocol scaffold, never a coding agent); `--no-agents` survives one version as a deprecated alias.
  - `upgrade` migrates v3-stamp projects: Agent Targets are inferred as `["claude"]`, content moves to `.agents/`, and the old `.claude/` paths retire through ADR-014's existing obsolete-file machinery — unmodified files deleted transactionally and replaced by stubs, user-edited files preserved with their stub write skipped and both reported.
- Considered options:
  - **Symlinks to a canonical copy** (the installer's own recommendation) — rejected: `apply_overlay` refuses symlink destinations by construction, the stamp inventory hashes file bytes, and symlinks require developer mode on Windows. Generated projects must stay portable.
  - **A full content copy per agent** — rejected: N copies of every skill in the stamp inventory, N places for user edits to diverge, and N reconciliations per upgrade.
  - **`CLAUDE.md` stays canonical with `AGENTS.md` as the stub** — rejected: every non-Claude target would be redirected into a Claude-branded file by the very FR meant to decouple them.
  - **Freezing layout at generation time** (legacy projects keep `.claude/` content forever) — rejected: it makes a one-version migration into permanent dual-layout support across overlay, inspection, verify, and upgrade.
- Status update (2026-07-27): symlinks were re-examined in the v0.9 grilling session and **rejected again**; see the amendment below. Agent Target path data is extended and drift-guarded by ADR-019.
- Consequences: One content copy means an upgrade touches one file per skill regardless of how many agents are selected. Stubs cost one indirection hop the agent must follow — the same cost this repo already lives with. The v3→v4 stamp migration carries both the new `agent_targets` field and the `agents`→`handoff` component rename, so the rename rides a migration already being paid for. A user who edited a skill before upgrading ends with divergent content (their edit at the Claude path, canonical at `.agents/`); this is reported, not silently reconciled. Per-agent path maps are transcribed from a moving upstream table with no FR-16-style byte-equality drift guard, so each declared target must be re-verified at bump time.

## 2026-07-27 amendment — symlinks re-examined and rejected again

Raised in the v0.9 grilling session on the grounds that the reference installer
recommends symlinks. Re-rejected. Recorded here because the question is
recurrent and the original entry stated the mechanics without stating why the
upstream recommendation does not transfer.

The installer symlinks each agent's directory to a canonical copy held **outside
the project**, so one cached copy serves many existing repositories — that is
what the recommendation buys. dev-ready *generates* a project whose Canonical
Content already lives inside it, so a link from `.claude/skills/x` to
`../../.agents/skills/x` deduplicates nothing that a Pointer Stub does not
already deduplicate, while costing portability.

Three findings settled it beyond the original three mechanics:

- **The indirection cost is smaller than this ADR implied.** Stubs preserve the
  canonical YAML frontmatter, so an agent sees each skill's name and
  description during discovery and pays one extra read only for skills it
  decides to use.
- **A symlink degrades worse than a stub when it degrades.** Cloned on Windows
  without `core.symlinks` and developer mode, a symlink becomes a plain file
  containing a path — a broken stub with no explanation. A Pointer Stub is
  valid markdown that says what to read instead.
- **A platform-conditional hybrid violates NFR-1.** Falling back to stubs where
  links are unavailable makes one dev-ready version produce different output on
  different machines, and forces the stamp inventory, verify, and upgrade to
  carry two shapes.

Reopening this needs a change in the underlying facts — Windows symlinks
without elevation, or a generated-project layout where the canonical copy is
genuinely external — not another appeal to the installer's recommendation.

## 2026-08-12 note — the first of those facts changed; see ADR-025

The condition this amendment set for reopening was met, on the first clause.
**Windows junctions require no elevation**, and the reference installer creates
them for exactly this purpose (`installer.ts:255-256`). The mechanic stated
above — "symlinks require developer mode on Windows" — is wrong for directory
links and should not be cited again.

The second clause was *not* met: a generated project's Canonical Content is
still inside it, so a link still deduplicates nothing. [ADR-025](adr-025-skill-delivery-mode.md)
therefore does not overturn the deduplication reasoning; it retires Pointer
Stubs on a different basis, and offers `symlink` as a user-selected mode
alongside `copy` rather than as the default.

Two findings from this amendment are **carried forward into ADR-025 as costs,
not as reversals**: a link degrades badly across `git clone` (worse than stated
here — a Windows junction has no git representation at all), and a
platform-conditional hybrid violates NFR-1. ADR-025 answers the second by making
the mode an explicit recorded input rather than a detected fallback, and the
first by defaulting to `copy` and reporting the consequence when `symlink` is
chosen.
