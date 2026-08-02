# Catalog Candidates & Deferred Decisions

Status: Recorded 2026-07-21. CEO decisions — preserved for future versions.
This file is the backlog for content/features not yet in manifest.json.
Nothing here appears in THIRD_PARTY_NOTICES.md until actually integrated
(NOTICES lists shipped content only; FR-18 CI enforces sync with the manifest).

Flow: candidate here → integrated (manifest.json catalog item + NOTICES entry
if third-party) → removed from this file.

---

## Third-party candidates

### GitHub MCP server (github/github-mcp-server)

- Decided 2026-08-02 (grilling, Moofon): **a selectable Catalog Item, not
  always-written infrastructure.** "Every project gets it, no menu line" was
  proposed and rejected — see the three blockers below, any one of which is
  paid by users who did not ask for it.
- Integration mode: pinned dependency with an `inject: mcp-server` effect, the
  same shape as `code-memory` (ADR-008). No source is vendored, so no NOTICES
  entry.
- Category: undecided. `dev` fits the loop's tracker story; a case exists for
  `token-optimize` being the wrong home given the server's context weight.
- Blockers to resolve before it ships:
  1. **No `uvx`/`npx` launcher.** Upstream offers Docker
     (`ghcr.io/github/github-mcp-server`) or the remote endpoint
     `https://api.githubcopilot.com/mcp/`. Docker contradicts the README's
     "Docker only to run the generated project, not to generate it"; the
     remote endpoint is a hosted service.
  2. **ADR-002.** An untagged image is `latest` by another name — a digest
     must be pinned in the manifest. The remote endpoint cannot be pinned at
     all, which is the stronger argument against choosing it.
  3. **Auth and context weight.** It needs `GITHUB_PERSONAL_ACCESS_TOKEN`, so
     a user without one meets a failing server on first agent session; and its
     tool surface (issues, PRs, code search, actions) is charged to every
     session's context, the version-plan's first recorded risk. This is
     exactly the cost `code-memory` is opt-in to avoid imposing.
- Note: this item does not talk to `setup-matt-pocock-skills`. MCP config is
  written at generation time; the skill runs later and writes only Markdown. A
  skill that edited `.mcp.json` would mark it user-modified and exclude it from
  `upgrade` forever (ADR-014, ADR-018).

### headroom (headroomlabs-ai/headroom)

- Status: **deferred, not rejected** (2026-08-02, Moofon). Blocked on FR-32
  Mount Points landing and on first-party measurement — see below.
- License: Apache-2.0. Pinned-dependency mode redistributes nothing, so no
  THIRD_PARTY_NOTICES entry is required. Distributed as `headroom-ai` on PyPI
  and npm, and as `ghcr.io/chopratejas/headroom` — verify at integration time
  that the image owner and the `headroomlabs-ai` org are the same party.
- Category: `token-optimize`. Not mutually exclusive with `caveman`: caveman
  changes how the agent writes, headroom compresses what it reads.
- **The measured reason for deferral.** Headroom has three modes and only one
  is reachable by a tool that writes project files:
  - `headroom mcp serve` — exposes `headroom_compress`, `headroom_retrieve`,
    `headroom_stats`. Configurable in `.mcp.json` exactly like `code-memory`.
  - `headroom wrap <agent>` — starts a local proxy, redirects the agent's API
    traffic through it, and installs Serena. Machine-level, not a project
    file; dev-ready cannot configure it and should not try.
  - library / proxy — irrelevant to a generated project.

  The advertised "15-20% fewer tokens for coding agents" belongs to *wrap*
  mode. MCP mode compresses nothing on its own: an MCP server cannot intercept
  the host's other tool results, so it only compresses what the agent
  deliberately hands it. Shipping MCP mode alone bills every session for three
  tool definitions in exchange for a call the agent may never make — plausibly
  net negative for the metric the Category is named after.
- What would unblock it: a Mount Point (FR-32) that tells a loop skill *when*
  to call `headroom_compress` — `diagnosing-bugs` before reading a large log is
  the obvious first candidate — plus a first-party measurement of real savings.
  Headroom would then be FR-32's first non-`react-doctor` customer, which is a
  reason to sequence it **after** FR-32 ships rather than alongside it.
- Conflict to handle if it ships: `headroom learn` writes to `CLAUDE.md` when
  `CLAUDE.local.md` is not used. dev-ready writes `CLAUDE.md` as a managed
  one-line `@AGENTS.md` Pointer Stub; an append marks it user-modified and
  excludes it from `upgrade` permanently.
- Live alternative to reconsider: if measurement shows the value is
  overwhelmingly in wrap mode, the honest outcome is a recommendation in the
  generated README rather than a catalog item — dev-ready would be installing
  the mode that does not deliver the benefit.

### graphify (Graphify-Labs/graphify)

- License: MIT. PyPI package name is `graphifyy` (double y) — the `graphify`
  command lives inside it; `uvx --from graphifyy graphify` is required, plain
  `uvx graphify` fails.
- Integration mode: pinned dependency (executable CLI + git hook), same as
  code-memory / react-doctor per ADR-008. Plus an original wrapper skill as
  the catalog item. Do NOT vendor the source.
- Category: `memory` — mutually exclusive with `code-memory`
  (DeusData/codebase-memory-mcp). User picks exactly one at init, with
  per-item descriptions rendered from the catalog so they can choose by
  scenario (code-memory: MCP knowledge-graph server, sub-ms queries, zero
  deps; graphify: skill + CLI, maps code/docs/PDF/media into a queryable
  graph, git-hook auto-rebuild, committable graphify-out/).
- Target: v0.4+ (after the memory category / exclusive-select mechanism
  lands with FR-14 in v0.3).
- Open items at integration time: verify `graphifyy` package name/channel on
  PyPI; decide whether `graphify-out/` guidance goes into the wrapper skill;
  NOTICES entry (MIT, pinned commit).

---

## Deferred product decisions (CEO: must keep, record and preserve)

### D-1. CLI language selection (i18n) — REJECTED (2026-07-26)

**Status: Rejected.** Scheduled into v0.8 as FR-25, specced, then withdrawn
before any implementation. FR-25's number is permanently retired. The full
rationale lives in D-3 of [version-plan.md](version-plan.md); the language rule
that survived is [ADR-016](decisions/adr-016-language-boundary.md).

The tech-lead note recorded below as "overruled" — that two locales of every
prompt and catalog description is a recurring cost against a solo-maintainer
budget — is the objection that ultimately carried. It is left exactly as
written rather than rewritten in hindsight.

Everything below is the original record, kept as history. It is no longer a
plan for anything.

- Decision: `init` will offer a UI-language choice (zh-TW / en) for prompts
  and item descriptions.
- Tech-lead note (recorded, overruled): recurring maintenance cost — every
  prompt and catalog description needs two locales; risk noted against the
  solo-maintainer budget.
- Design direction when implemented: locale strings live in the catalog data
  (manifest item `description` becomes `{en, zh-TW}`) and a small message
  table for fixed CLI strings — consistent with FR-14's "adding content is a
  data change, not CLI code".
- Also needs: `--lang <code>` flag for non-interactive mode; stamp
  (`.dev-ready.json`) records the chosen locale.
- Target: not in v0.3–v0.6 scope; schedule at roadmap review after v0.6.

### D-2. Next.js base template

- Decision: a second project type — user chooses React+FastAPI (current) or
  Next.js at init.
- Tech-lead note (recorded, overruled): doubles upstream maintenance (second
  pinned upstream, second weekly bump workflow, second docker smoke test);
  no official Copier-compatible Next.js template exists, so the fetch
  mechanism must be designed (options: adopt a community template and pin it,
  or maintain a minimal in-house template — decide via ADR when scheduled).
- Prep work that IS in scope now (cheap, architectural): restructure
  manifest `upstream.base_template` into an enumerable map
  (`upstream.base_templates: {fastapi-react: {...}}`) so a second template
  is a data addition later. Single entry for now; no behavior change.
- Ripple effects to scope in the ADR: react-doctor item only applies to
  React-based templates → catalog items need a `templates: [...]`
  applicability field; verify/stamp/upgrade must be template-aware.
- Target: post-v0.6; requires its own ADR before implementation.

### D-3. Generation progress/status indicator (CLI UX)

- Decision: Add step-based progress feedback / spinner during generation
  (fetch → overlay → verify → finalize).
- Motivation: Prevents the CLI from appearing frozen/stuck during multi-second
  template downloading, Copier rendering, overlay copying, and verification.
- Implementation note: Must check `sys.stdout.isatty()` and gracefully fallback
  to plain text log lines in non-interactive/CI environments.

---

## Init flow (agreed shape, v0.3 baseline + preserved decisions)

1. `uvx dev-ready init my-app`
2. ~~[D-1] choose CLI language~~ — D-1 rejected 2026-07-26; there is no language step
3. Project questions:
   - [D-2, deferred] template choice (fastapi-react | nextjs); fixed to
     fastapi-react until D-2 lands
   - project name and template variables (mapped to the upstream copier.yml
     questions — no parallel question set)
   - secrets: auto-generate high-entropy values via `secrets.token_urlsafe()`
     for template-defined secrets (secret_key, postgres, superuser);
     user may override human-memorable ones (superuser password). Never
     print or persist outside the generated `.env` (gitignored). No
     user-input-then-hash scheme — password hashing is app-runtime concern
     (template already uses passlib/bcrypt).
   - coding agents: multi-select (Claude Code / Codex / ...) → determines
     which config dirs materialize (`.claude/` vs `.agents/`, ADR-011)
4. Component selection (skills / mcp / docs / agents)
5. Item selection per component (FR-14), rendered by category:
   - memory (exclusive: pick one): code-memory | graphify [candidate]
   - dev/quality (multi): react-doctor, security-audit [v0.4], caveman
     [v0.4], ...
6. Generate (with step-based status/spinner feedback, D-3) → verify → stamp
   (`.dev-ready.json` records template, items, pins — never a language, D-1
   rejected)

Catalog schema additions implied (fold into FR-14 while the CLI contract is
open): item `category`, per-category `exclusive: bool`, and later
`templates: [...]` applicability (D-2). Localized descriptions are not coming —
D-1 rejected.