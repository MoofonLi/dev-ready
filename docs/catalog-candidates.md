# Catalog Candidates & Deferred Decisions

Status: Recorded 2026-07-21. CEO decisions — preserved for future versions.
This file is the backlog for content/features not yet in manifest.json.
Nothing here appears in THIRD_PARTY_NOTICES.md until actually integrated
(NOTICES lists shipped content only; FR-18 CI enforces sync with the manifest).

Flow: candidate here → integrated (manifest.json catalog item + NOTICES entry
if third-party) → removed from this file.

---

## Third-party candidates

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

### D-1. CLI language selection (i18n)

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

---

## Init flow (agreed shape, v0.3 baseline + preserved decisions)

1. `uvx dev-ready init my-app`
2. [D-1, deferred] choose CLI language
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
6. Generate → verify → stamp (`.dev-ready.json` records language, template,
   items, pins)

Catalog schema additions implied (fold into FR-14 while the CLI contract is
open): item `category`, per-category `exclusive: bool`, and later
`templates: [...]` applicability (D-2) and localized descriptions (D-1).