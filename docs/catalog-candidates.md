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

- Status: **deferred, not rejected** (2026-08-02, Moofon). Both original
  blockers are now closed — FR-32 shipped in v0.10, and the first-party
  measurement was run on 2026-08-12 — but **the measurement surfaced two new
  blockers that outrank the old ones**, so it stays deferred. See "Measured
  2026-08-12" below.
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

#### Measured 2026-08-12 — `headroom-ai==0.34.0`, installed and run

Run against the real package rather than its README, in a directory with no
`*_API_KEY` and no `HEADROOM_*` variable set. Five conditions; three pass.

- **Launches clean.** `uvx --from "headroom-ai[mcp]==0.34.0" headroom mcp serve`
  completes an MCP handshake. The `mcp` extra declares only four dependencies
  (`mcp`, `httpx`, `starlette`, `uvicorn`), but the base pulls ~69 packages and
  ~65 MB — `litellm` alone is 23 MB, and it drags in `openai`, `tokenizers`, and
  `hf-xet`.
- **No API key.** Confirmed for `--help`, `mcp status`, `mcp serve`, and every
  `tools/call`.
- **Standalone value exists, and is better than the 2026-08-02 note assumed.**
  With no proxy running, `headroom_compress` saved 54% of tokens on a 120-record
  JSON payload and 26% on 400 log lines, and `headroom_retrieve` returned the
  byte-exact original by hash — both in-session and from a **fresh process**
  (`source: "local"`). The `mcp --help` text says the MCP server fetches
  originals *from the proxy*; it falls back to a local store, so compression is
  reversible without the proxy.
- **NEW BLOCKER — writes outside the project.** Running `--help` alone creates
  `~/.headroom/update_check.json`. Running the server grows that directory to
  379 KB: `ccr_store.db` (SQLite, holding the **original content** of everything
  compressed), `config/install_id`, `savings_events.jsonl`, `session_stats.jsonl`.
  `HEADROOM_CCR_SQLITE_PATH` relocates the database and `HEADROOM_WORKSPACE_DIR`
  the workspace, but `~/.headroom` is hardcoded in `cache/ttl_observations.py`.
  dev-ready never writes outside the target project; here it would be the reason
  something else does.
- **NEW BLOCKER — outbound telemetry on by default.** `BEACON_DEFAULT_ON = True`
  (`headroom/telemetry/beacon.py:56`), and `is_beacon_enabled()` returns `True`
  in a clean environment, uploading anonymous session aggregates to
  `https://headroom-beacon.headroom-beacon.workers.dev/v1/logs`. It is built
  responsibly — `DO_NOT_TRACK`, `HEADROOM_OFFLINE`, and `HEADROOM_BEACON=off`
  all disable it, and the payload is counts, not content — but the default is on
  and the code documents itself as fail-open, so an unrecognised value uploads.
  A pinned-dependency item lands in **every** generated project's `.mcp.json`,
  which would make dev-ready the reason a user transmits anything. That is the
  shape of failure FR-38 spent a version repairing.
- **The 2026-08-02 net-cost argument survives the measurement and is still the
  deepest objection.** The tool works when called; nothing here shows the agent
  calls it. Three tool definitions cost every session unconditionally, while the
  saving is conditional on the agent choosing to route content through them —
  and the measurement adds that headroom returns **code unchanged**
  (`router:protected:recent_code`) and **file listings unchanged**
  (`router:noop`). Its wins are on structured data and logs, not on what a
  coding agent reads most. A Mount Point pointing `diagnosing-bugs` at a large
  log remains the strongest shape, and it is now the *only* remaining argument
  for shipping it.
- **What would unblock it now:** the store fully relocatable inside the project
  and telemetry defaulting off — or an accepted decision to ship a hardened
  `.mcp.json` entry (`HEADROOM_BEACON=off`, relocated store, the store path
  gitignored) with explicit disclosure in the generation report. That second
  route leaves dev-ready maintaining an opt-out against a moving upstream with no
  FR-16-style guard: a rename upstream turns transmission back on silently.

**Generalised from this measurement:** "no outbound telemetry enabled by
default" joins the admission standard for every pinned-dependency candidate.
`code-memory` shipped in v0.3 and has never been checked against it; that check
is owed.

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

### D-4. Audience-tiered Claude Code Output Styles, offered by `setup-project`

- Raised 2026-08-14 by Moofon, during the v0.11 Phase 2 `grill-with-docs`
  session, from [this walkthrough](https://www.youtube.com/watch?v=E8Bx9OlpmdM).
  **Deferred the same session, by Moofon, to be decided as its own FR.** It is
  not v0.11 scope and no Phase 2 ticket touches it.
- Decision to make later: whether `setup-project` (FR-39) offers a generated
  project a choice of Claude Code Output Style, written to the generated
  project's `.claude/output-styles/`.
- Proposed shape, recorded as raised:
  - Three audience tiers — **Beginner** (never drop a term, always explain it
    with a plain-language analogy; pause and warn in plain language before a
    destructive, costly, or environment-changing action); **Vibe Coder / PM**
    (ASD-STE100 register — short sentences, active voice, one word one meaning;
    common terms unexplained, deeper ones given a one-line gloss; lead with
    product impact; state a trade-off on every decision); **Senior Engineer**
    (minimal output — what changed and whether it works; mechanism only on
    request; any unconfirmed judgement call stated in the first line, never
    buried at the end).
  - A language axis — Traditional Chinese (Taiwan technical usage), English
    STE100, or bilingual (term in English, explanation in Chinese).
  - An optional per-project term map, so a project can fix its own vocabulary
    (for example `member` rather than `user`).
- **Verified 2026-08-14 against the Claude Code documentation** — check these
  again when this is scheduled, because the feature has already moved once:
  - Style files live at `.claude/output-styles/` (project), `~/.claude/output-styles/`
    (user), or a managed-policy directory. The file name is the style name
    unless frontmatter sets `name`.
  - The **active selection** is written to `.claude/settings.local.json` — the
    per-developer, per-machine file. Project-level files are therefore shared
    while the choice is not, unless dev-ready writes `outputStyle` into the
    checked-in `.claude/settings.json` and forces one style on every
    collaborator.
  - `keep-coding-instructions: true` must be set, or Claude Code's built-in
    software-engineering instructions are dropped along with the tone change.
    All three tiers change communication only, so all three need it.
  - The standalone `/output-style` command was deprecated in v2.1.73 and
    removed in v2.1.91. `/config` replaces it. Any generated document naming
    the old command is already wrong.
  - Plugins may ship an `output-styles/` directory, which is a second delivery
    route once FR-45 adds this repo's plugin manifests.
- **Two binding decisions must be reopened before this can be specced, and
  neither belongs inside a `setup-project` ticket:**
  - **[ADR-016](decisions/adr-016-language-boundary.md).** The language axis is
    locale selection over a message catalog, whatever it is called, and ADR-016
    forbids exactly that. See also D-1 above, which is the same axis, rejected
    in 2026-07-26 on solo-maintainer cost. The tier axis on its own is English
    content and touches ADR-016 not at all — the two axes are separable and
    should be decided separately.
  - **[ADR-015](decisions/adr-015-agent-targets-canonical-content-pointer-stubs.md).**
    An Output Style serves one Agent Target out of roughly seventy. It has no
    canonical form to hold in `.agents/skills/` and no equivalent to point at
    from any other agent, so a project generated with `--agents codex` would
    receive nothing. This would be dev-ready's first single-target content
    class. ADR-015 is already scheduled to reopen in v0.12 for
    [ADR-025](decisions/adr-025-skill-delivery-mode.md) / FR-46, which is the
    cheapest place to answer the question once for both features.
- Target: decide alongside FR-46 in v0.12. Nothing here is approved yet.

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