# Version Plan — dev-ready v0.3 → v0.6

Status: Accepted (2026-07-17). Decided by CEO + Tech Lead as the final pre-agreed roadmap.
Numbering continues from requirements.md (FR-1..FR-10 shipped in v0.1/v0.2).

## End goal

`uvx dev-ready init my-app` produces, in one command, a full-stack FastAPI + React
project that is AI-assisted-development-ready on day one:

- **Context**: a tuned CLAUDE.md (project commands, guardrails, agent roles) and
  design-doc templates.
- **Tools**: MCP servers pre-configured (`.mcp.json`), starting with codebase memory.
- **Capabilities**: a curated set of Claude Code skills (token discipline, security
  audit, React quality, engineering practice) — individually selectable.
- **Quality gates**: skills that teach the agent to run linters/analyzers
  (react-doctor) and audits before claiming work is done.
- **Collaboration protocol**: the multi-agent handoff scaffold (`docs/handoffs/`,
  ADR-007).

The user composes their project freely: component-level choice (skills / mcp /
docs / agents) plus item-level choice inside skills and mcp (e.g. react-doctor
without codebase-memory) — see FR-14 / ADR-010. Everything the generator itself
materializes is pinned to CI-verified commits (ADR-002); nothing is fetched
"latest" at generation time.

## Integration modes (see ADR-008, amended 2026-07-18)

CEO decision: the product's core promise is "one command, Day-1 ready" — nothing
dev-ready sets up may require a manual install step, and everything is pinned.
Two mechanisms deliver this, chosen by content type — not by preference:

| Mode | Used for | What ships | How Day-1 works |
|---|---|---|---|
| **Vendor** | All text content: skills, CLAUDE.md guidance, design-doc templates, handoff templates | Snapshot committed into `src/dev_ready/templates/`, pinned in the manifest `vendored` section (ADR-009), THIRD_PARTY_NOTICES + NOTICE propagation | The files are simply there after `init` |
| **Pinned dependency** | Executable tools (MCP server binaries, npm CLI tools) | Pinned launcher/dependency entries in generated config: `.mcp.json` launches `uvx codebase-memory-mcp==<pin>`; `react-doctor@<pin>` is a devDependency in the frontend `package.json` | The package manager the user already runs (uv for the agent, `npm install` for the frontend) materializes the exact pinned version on first use — zero manual steps |

Direct binary vendoring into the dev-ready wheel was evaluated and rejected as
*infeasible*, not merely undesirable: 5 platform binaries × tens of MB exceeds
PyPI's default 100 MB project limits, forces a dev-ready re-release for every
upstream binary patch, and makes us the redistributor of executables we did not
build. The pinned-dependency mechanism achieves the identical user experience
(zero setup, exact pinned version, updated only via dev-ready releases) through
official channels.

Pinning philosophy: the *generation-time* rule (never fetch latest, ADR-002) is
unchanged — dev-ready materializes only pinned content. Pinned-dependency tools
are fetched by the user's package manager at first use, at the exact version
dev-ready pinned in the generated config; version changes arrive only through
dev-ready pin bumps, same as everything else.

Legal boundary (independent of any UX decision): content whose license prohibits
redistribution is never vendored, open-source project or not — redistribution
rules apply regardless of commercial intent. anthropics document-processing
skills (source-available) are permanently excluded; react-doctor's *source* is
never copied (a devDependency declaration is not redistribution, so its Commons
Clause-style terms are not triggered); karpathy-skills is vendorable on the basis
of the MIT declaration in its README (see Curation principles).

## Curation principles

- Every vendored skill must answer "what does the user lose if we drop it?" — no
  answer, no inclusion. Hard cap: **10 skills** in the skill catalog.
- The cap governs the *catalog*; the user picks any subset of it per project
  (FR-14), so catalog discipline is about maintenance cost and default quality,
  not about forcing content on users.
- Subsets, not whole repos: vendor only the files that earn their context-window cost
  in a generated project.
- Vendor everything that can legally be vendored; never vendor anything that is
  not clearly licensed for redistribution. Permanently excluded:
  anthropics/skills document-processing skills (source-available, prohibits
  productization); react-doctor source (Modified MIT/Commons Clause — pinned
  devDependency + wrapper skill instead, see FR-13).
- multica-ai/andrej-karpathy-skills: no standalone LICENSE file, but the README
  declares "License MIT" — a valid grant from the copyright holder (verified
  2026-07-18). Vendorable; the NOTICES entry cites "MIT, per README at
  <pinned commit>", and the pinned commit permanently preserves the grant as
  evidence. Asking upstream for a formal LICENSE file is a nice-to-have, no
  longer a blocker.
- Solo-maintainer budget: base-template bump stays weekly; vendored pins bump
  **monthly** (skill text churns slowly; review load must stay bounded).

---

## v0.3 — Pinned tool integrations + stamp + item-level selection

Low-risk, no redistribution, no new license work. Ships value fast and lays two
foundations the rest of the roadmap depends on: the generation stamp (v0.6 needs
it) and item-level selection (the growing catalog needs it — building it now means
the CLI contract changes once, not twice).

FR-11. **Generation stamp.** `generate` writes `.dev-ready.json` at the root of every
generated project: dev-ready version, selected components *and selected items per
component* (FR-14), upstream pin (repo + commit), and — from v0.4 on — vendored
pins. Projects generated before v0.3 have no stamp and cannot be `check`ed or
`upgrade`d; version-1 and version-2 stamps remain checkable but cannot be
upgraded. Schema is versioned (`stamp_version: 1`). verify treats its presence as
a required path.

FR-12. **Codebase-memory MCP item.** The `mcp` component gains a `code-memory` item:
a server entry in the generated `.mcp.json` launching the tool via a pinned
package-manager command (DeusData/codebase-memory-mcp, MIT — published on npm and
PyPI; `uvx codebase-memory-mcp==<pin>` preferred since every dev-ready user has uv;
exact package name and channel verified by the senior engineer at implementation).
Zero manual install: the agent's first MCP connection materializes the exact pinned
version. The pin lives in `manifest.json` and is recorded in the stamp; updates
arrive only through dev-ready pin bumps.

FR-13. **react-doctor integration.** Two pieces, no source redistribution:
(1) `react-doctor@<exact-pin>` is added as a devDependency (plus a package script)
to the generated frontend `package.json` — it arrives with the `npm install` the
user runs anyway, Day-1 seamless; (2) an *original* wrapper skill — item id
`react-doctor` in the `skills` component — teaches the agent when to run it on the
frontend and how to act on its findings. The Commons Clause question never
triggers: a dependency declaration is not redistribution.

FR-14. **Item-level component selection (ADR-010).** Users select individual items
inside the `skills` and `mcp` components — e.g. react-doctor without code-memory:
- **Interactive**: after the component checkbox, a second-level multi-select lists
  the items of each chosen component, all on by default (pressing Enter preserves
  today's behavior exactly).
- **Non-interactive**: list flags `--skills <ids|all|none>` and `--mcp <ids|all|none>`
  (comma-separated ids). `--no-skills` / `--no-mcp` remain as aliases for `none`.
  `--yes` alone still means "everything on". Unknown ids exit 2 with the valid-id list.
- **Item catalog as data**: each item (id, description, integration mode, license,
  source paths) is declared in `manifest.json`; prompts and overlay both render
  from the catalog, so adding a future skill is a data change plus assets, not CLI
  code. `docs` and `agents` stay boolean — they are single items.
- verify checks that exactly the selected items are present in the output; the
  stamp (FR-11) records the selection.

Carry-overs / pre-work in v0.3:
- Align docs with the `.copier` prune shipped in `e096aaf` (ADR-005 amendment;
  v0.2-overview KEEP-set correction; FR-7 KEEP list) — done alongside this plan.
- Add `.copier` and `.copier-answers.yml` to `FORBIDDEN_PATHS` in verify (the leak
  guard should enforce what generate now prunes).
- (Optional, nice-to-have) Ask multica-ai/andrej-karpathy-skills upstream for a
  formal LICENSE file; the README's MIT declaration already suffices (verified
  2026-07-18, no longer blocking FR-20).
- CI hygiene: `ci.yml` gains `paths-ignore` for `docs/**`, root-level `*.md`, and
  `.bob/**` so documentation-only pushes/PRs skip the heavy jobs. Must NOT use
  `**.md` — markdown under `src/dev_ready/templates/` is functional wheel content
  and must keep triggering CI. `release.yml` and `upstream-bump.yml` unchanged.
  Revisit with `dorny/paths-filter` if branch protection with required checks is
  ever enabled (skipped workflows leave required checks pending).

## v0.4 — Vendoring infrastructure + MIT wave

The version where redistribution machinery is built properly, once, before any
volume of vendored content arrives. New skills land as catalog items (FR-14), so
no CLI changes are needed here.

FR-15. **Manifest `vendored` section.** `manifest.json` gains
`vendored: [{repo, commit, license, paths: [{src, dest}]}]` with the same validation
rigor as the upstream pin (40-hex commit, path rules). This is the single source of
provenance truth, cross-referenced by catalog items whose mode is `vendor`.

FR-16. **Snapshot sync + drift guard.** `scripts/sync_vendored.py` (CI/maintainer
tool, not shipped in the wheel) re-materializes snapshots from `repo@commit`. CI
gains a drift check: snapshot bytes must equal upstream at the pinned commit, or the
build fails — provenance that isn't enforced is fiction. A **monthly** bump workflow
(mirroring `upstream-bump.yml`) opens PRs for vendored pins.

FR-17. **MIT wave vendoring** (all clean MIT, curated subsets, each a catalog item):
- `JuliusBrussee/caveman` — token-discipline skill.
- `mattpocock/skills` — selected engineering-practice skills (subset chosen at
  implementation time against the 10-skill catalog cap).
- `cloudflare/security-audit-skill` — multi-phase security audit skill.
- `VoltAgent/awesome-design-md` — 1–2 DESIGN.md templates into the `docs` component.

FR-18. **THIRD_PARTY_NOTICES automation.** A CI check that `THIRD_PARTY_NOTICES.md`
and the manifest `vendored` section are in sync (every vendored repo listed with
license and commit; no orphan entries). The stamp (FR-11) starts recording vendored
pins.

## v0.5 — Apache wave + pending items

FR-19. **anthropics/skills example subset.** Vendor selected Apache 2.0 example
skills as catalog items. Apache requires NOTICE propagation: the NOTICE content
ships in the generated project alongside the skills, and the NOTICES machinery
(FR-18) is extended for Apache attribution. Document-processing skills
(docx/pdf/pptx/xlsx) remain permanently excluded (source-available terms).

FR-20. **Karpathy guardrails content.** Fold the multica-ai/andrej-karpathy-skills
CLAUDE.md guardrail guidance into our generated CLAUDE.md template with
attribution. License basis: MIT as declared in the upstream README (no standalone
LICENSE file; the pinned commit preserves the README grant as evidence — see
Curation principles). NOTICES entry cites the README declaration.

(The formerly planned "skill-selection UX review" is retired: FR-14 resolved it in
v0.3 by decision, not deferral.)

## v0.6 — Lifecycle commands

FR-21. **`dev-ready check`.** Reads `.dev-ready.json` (FR-11) from an existing
project, compares against the running CLI's manifest: which dev-ready version
generated it, which components and items, whether pins are behind, whether
required/forbidden paths still hold. It is read-only and exits 0 when clean, 6
for a missing or invalid stamp, and 7 when drift is detected.

FR-22. **`dev-ready upgrade`.** Re-applies a newer overlay onto an existing project.
Scope deliberately conservative: overlay-managed whole files only (skills,
handoff templates, CLAUDE.md sections we own — per the stamp's item selection),
never upstream application code — that path was closed when `.copier/` was pruned
(ADR-005 amendment). Conflict rule: never overwrite user-modified files silently;
report and skip. Requires FR-21's stamp reading plus a recorded file inventory
(added to the stamp in this version).
Shared injection targets are reported and left unchanged.

Explicitly still out of scope after v0.6: additional base templates, Web UI
companion — now planned in detail; see "Post-v0.6 roadmap" below.

---

## Generated project — target end state (v0.6, everything selected)

```
my-app/
├── .dev-ready.json          # stamp: version, components+items, pins (FR-11)
├── CLAUDE.md                # commands, guardrails (FR-20), agent roles (FR-10)
├── README.md                # project-specific (FR-8)
├── .mcp.json                # code-memory + future MCP items (FR-12)
├── .claude/skills/          # user-selected subset of the <=10-item catalog:
│                            #   caveman, security-audit, react-doctor wrapper,
│                            #   mattpocock subset, anthropics examples (+NOTICE)
├── docs/
│   ├── design/DESIGN.md     # awesome-design-md template (FR-17)
│   └── handoffs/            # multi-agent protocol scaffold (FR-10, ADR-007)
├── backend/                 # upstream FastAPI app (pruned, FR-7)
├── frontend/                # upstream React app
├── compose.yml, .env        # per-project secrets (ADR-005)
└── .github/workflows/       # only the user's own test workflows (FR-7)
```

No `.git`, no `copier.yml`, no `.copier/`, no upstream repo-maintenance files —
enforced by exclude + prune + the verify leak guard.

## Risks (accepted, tracked)

- **Context bloat** in generated projects — mitigated by the 10-item catalog cap,
  subset-only vendoring, and item-level opt-out (FR-14); revisited every version.
- **Vendored drift / provenance rot** — mitigated by FR-16's byte-equality CI check.
- **Selection-matrix test surface** — item combinations grow the test space;
  mitigated by catalog-driven generation (one code path, items as data) and CI
  testing all-on, all-off, and one representative mixed selection.
- **Solo-maintainer review load** — mitigated by monthly (not weekly) vendored
  bumps and by pinned-dependency integration for executables (no snapshot to
  maintain, just a version pin).
- **Upstream license changes** (react-doctor terms, anthropics/skills terms) —
  pinned-dependency mode limits exposure; vendored pins mean a license change upstream
  never retroactively affects an already-released dev-ready version, but bump PRs
  must re-check the license file on every bump (added to the bump-PR checklist).

---

## Post-v0.6 roadmap — Decisions of 2026-07-19

Status: Directions **Accepted** (CEO + Tech Lead, final architecture session,
2026-07-19). The v0.3–v0.6 scope above is **unchanged** — nothing in this
section may pull work forward into those versions. The decisions and mechanisms
below are settled; the version assignments (v0.7 / v0.8 / v1.0) are a proposed
sequencing to be re-confirmed at v0.6 close. FR numbering FR-23..FR-27 is
reserved here; requirements.md gains the full entries when each version's
development starts (same flow as v0.3–v0.6).

### D-1. Mechanism/policy separation for the agent-team workflow (FR-23)

The tech-lead → senior → junior → QA/Security/SRE handoff loop shipped in FR-10
encodes one specific team (Fable/Opus/Gemini/Bob). That lineup is a *policy* —
one team's choice — and model names churn fast; hardcoding either into the
overlay guarantees staleness. dev-ready's durable product is the *mechanism*:
role definitions, handoff document templates, folder structure, and loop rules
(hard-bug escalation, report obligations, who commits).

Concretely: generated projects carry a workflow config
(`docs/handoffs/workflow.yaml`) declaring roles as data —
`{id, title, model, responsibilities, never_does}` — plus the handoff sequence
and loop rules. Handoff templates and the CLAUDE.md agent-roles section render
role names and models from this config, never from literals. Two design rules:

- **Roles decoupled from models**: roles are `planner` / `implementer` /
  `reviewer`-style ids; the model is an editable field on the role. Swapping
  next year's model is a one-line config edit, not a template rewrite.
- **Preset, not framework**: the current loop ships as the single default
  preset. A preset ecosystem (multiple built-in loops, community sharing,
  plugin mechanics) is explicitly deferred until real users ask for it —
  abstractions built before a second user exists usually abstract the wrong
  thing.

### D-2. AI-invokable generation — the "generate" skill (FR-24)

The non-interactive surface built in FR-3/FR-14 (`--yes`, `--skills`, `--mcp`,
item ids, exit codes) is already a machine interface. FR-24 ships an *original*
skill that teaches a coding agent when and how to drive
`uvx dev-ready init` with the right flags — so a user can tell their agent
"start a new project with X and Y" and the agent composes the command itself.

Distribution: in this repo, laid out to be installable via the Agent Skills
ecosystem (skills.sh) and/or as a Claude Code plugin — **not** inside generated
projects (a generated project has no reason to regenerate itself).
Precondition: the FR-14 flag contract is stable (v0.3 shipped). Cost: one
SKILL.md plus docs — smallest FR on this list.

### D-3. CLI internationalization — English + Traditional Chinese (FR-25)

Scope decided precisely: i18n covers the **CLI surface only** — interactive
prompts, progress/result messages, errors, `--help` text. Generated project
content (CLAUDE.md, skills, design docs, handoff templates) stays English
permanently: its consumer is the agent, and English is what models parse most
reliably. This scope line is the decision; revisiting it requires a new ADR.

Mechanics: default language English; `zh-TW` selected via `--lang`, then
`DEV_READY_LANG`, then locale detection (precedence in that order). Messages
live in a catalog (single lookup layer, no scattered literals), so adding a
locale later is a data change. Accepted cost: every user-facing string is
maintained twice; a new FR's messages must land in both locales in the same PR
(CI check compares catalog keys across locales).

### D-4. Multi-coding-agent output targets (FR-26)

Today the overlay renders for Claude Code only (`.claude/skills/`, `CLAUDE.md`,
`.mcp.json`). The Agent Skills / AGENTS.md standards make skill *content*
portable; what varies per agent (Codex, Cursor, other standard-compliant
harnesses) is output paths and config format. FR-26 adds a **render target**
dimension to the overlay: the user picks target agent(s) — Claude Code remains
the default — and the same catalog items render into each target's layout;
verify checks per-target required paths. This mirrors the skills.sh installer
UX ("pick skills, pick agents") without changing what the catalog is.

Risk accepted: these standards are still moving. The exact target list and
per-target layouts are pinned at implementation time, not now.

### D-5. Multi-template — second stack (FR-27, v1.x)

Confirmed: still the last thing. Mechanism decided now so v0.x work does not
paint us into a corner: templates become **registry entries** in the manifest —
`{id, source, fetch_strategy, pinned_ref, overlay_set, smoke_test}` — and the
fetch layer grows a strategy interface (`copier-native` | `degit-style` |
`wrapped-generator`, for ecosystems like Next.js/Vue whose starters are not
Copier templates). ADR-002 (pins only, never latest) and the `fetch/` network
boundary apply to every strategy. Overlay content becomes stack-aware:
CLAUDE.md guidance and quality-gate skills are per-stack, not shared.

Hard gates before starting FR-27: v0.6 shipped; real users on the FastAPI
template; explicit acceptance that each template roughly doubles CI, license,
and overlay maintenance (solo-maintainer budget). One template done well beats
two half-done.

### D-6. Web UI — deferred, mechanism noted

No new FR. Recorded insight: FR-14's catalog-as-data means a future Web UI is
just another renderer of the same catalog, with the non-interactive CLI as its
execution backend — the architecture already supports it. Revisit after FR-24
and FR-26 have proven the catalog contract against real consumers.

### D-7. Selection UX with per-item descriptions — already covered

No new work. The skills.sh-style experience ("pick items, each with a
description, then pick agents") is exactly FR-14 (+ FR-26 for the agent axis);
the catalog's `description` field is the contract. Quality bar recorded: every
catalog item's description must answer "what does the user lose by omitting
it?" — the same test as the curation principle.

### Proposed sequencing (re-confirm at v0.6 close)

| Version | Contents | Rationale |
|---|---|---|
| v0.7 | FR-23 workflow config, FR-24 generate skill | Cheap, self-contained; deepens the existing agents/skills story with no new external surface |
| v0.8 | FR-25 CLI i18n, FR-26 multi-agent render targets | Widens the audience once content and catalog are stable |
| v1.0 | FR-27 second template; Web UI decision revisited | Platform step; gated on real-user feedback and the D-5 hard gates |

**2026-07-24 — v0.6 close-out re-confirmation (CEO-confirmed, Moofon):**
At v0.6 close the proposed post-v0.6 sequencing is confirmed unchanged — v0.7 =
FR-23 (workflow config) + FR-24 (generate skill); v0.8 = FR-25 (CLI i18n) +
FR-26 (multi-agent render targets); v1.0 = FR-27 (second template) + Web UI
decision. No amendment. Ratified by the CEO (Moofon) on 2026-07-24; the v0.6.0
release commit may proceed.
