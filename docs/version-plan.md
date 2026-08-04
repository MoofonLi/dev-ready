# Version Plan — dev-ready v0.3 → v0.9 (+ post-v0.9 roadmap)

Status: Accepted (2026-07-17). Decided by CEO + Tech Lead as the final pre-agreed roadmap.
Amended 2026-07-24 (afternoon): v0.7 scope expanded — see "2026-07-24 (PM) amendment" below.
Close-out 2026-07-26: v0.7 is released — `v0.7.0` is tagged and published to PyPI. Distribution-rider evidence (skills.sh install proof, launch post URL, README issue entry point) is recorded separately against the v1.0 real-users gate.
Amended 2026-07-26: v0.8 scope, ordering, and decisions settled — see "2026-07-26 amendment" below (ADR-015, ADR-016).
Amended 2026-07-26 (later the same day): FR-25 (CLI i18n) withdrawn before implementation and D-3 rejected. v0.8 is FR-26 only — see "FR-25 — withdrawn" in the amendment.
Close-out 2026-07-27: v0.8 is released. FR-26 is shipped in `v0.8.0`, which is tagged and published to PyPI; Phase 4 documentation, review, release, and distribution verification are complete. FR-25 remains withdrawn settled history.
Amended 2026-07-27: v0.9 and v0.10 added between v0.8 and v1.0 — see "2026-07-27 amendment" at the end of this document (ADR-017, ADR-018, ADR-019). v1.0 is unchanged.
Close-out 2026-08-01: v0.9 is released. FR-30, FR-31, and FR-35 are shipped in `v0.9.0`; the Category selection model, lean Default Set, and generated Handoff Protocol retirement are complete. ADR-020 changed generated projects only; ADR-021 separately retired this repository's internal Handoff Protocol.
Numbering continues from requirements.md (FR-1..FR-10 shipped in v0.1/v0.2).

## End goal

`uvx dev-ready init my-app` produces, in one command, a full-stack FastAPI + React
project that is AI-assisted-development-ready on day one:

- **Context**: canonical `AGENTS.md` project instructions, the mandatory Spec
  Loop, optional Agent Target Pointer Stubs, and design-document templates.
- **Tools**: selected MCP servers are pre-configured in `.mcp.json`, starting
  with codebase memory; projects that select none omit the file.
- **Capabilities**: a curated set of coding-agent Enhancements (token discipline,
  security audit, React quality, engineering practice) selected by Category.
- **Quality gates**: skills that teach the agent to run linters/analyzers
  (react-doctor) and audits before claiming work is done.
- **Development method**: one mandatory Spec Loop, with optional Enhancements
  around it (ADR-018). Generated projects no longer receive the Handoff Protocol
  (ADR-020); ADR-021 retired that internal practice separately.

The user composes Enhancements by Category while Component remains an internal
write-location grouping; Agent Targets are selected independently — see
FR-30 / ADR-017. Everything the generator itself
materializes is pinned to CI-verified commits (ADR-002); nothing is fetched
"latest" at generation time.

## Integration modes (see ADR-008, amended 2026-07-18)

CEO decision: the product's core promise is "one command, Day-1 ready" — nothing
dev-ready sets up may require a manual install step, and everything is pinned.
Two mechanisms deliver this, chosen by content type — not by preference:

| Mode | Used for | What ships | How Day-1 works |
|---|---|---|---|
| **Vendor** | Redistributable text content: skills, canonical rules, and design-document templates | Snapshot committed into `src/dev_ready/templates/`, pinned in the manifest `vendored` section (ADR-009), THIRD_PARTY_NOTICES + NOTICE propagation | The files are simply there after `init` |
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
  answer, no inclusion. The former ten-item catalog cap is retired in v0.9.
- The **Default Set** is limited to three declared entries: one development loop
  plus the project's two documentation skeletons. Enhancements remain unbounded
  and off by default; the limit protects the lean default path without closing
  the catalog (FR-31, ADR-018).
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
Scope deliberately conservative: overlay-managed whole files only, including
transactional retirement of obsolete managed files, never upstream application
code — that path was closed when `.copier/` was pruned
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
reserved here (FR-28..FR-29 added by the 2026-07-24 PM amendment below);
requirements.md gains the full entries when each version's development starts
(same flow as v0.3–v0.6).

### D-1. Mechanism/policy separation for the agent-team workflow (FR-23)

The tech-lead → senior → junior → QA/Security/SRE handoff loop shipped in FR-10
encodes one specific team (Fable/Opus/Gemini/Bob). That lineup is a *policy* —
one team's choice — and model names churn fast; hardcoding either into the
overlay guarantees staleness. dev-ready's durable product is the *mechanism*:
role definitions, handoff document templates, folder structure, and loop rules
(hard-bug escalation, report obligations, who commits).

Concretely: generated projects carry the Handoff Protocol as config
(`docs/handoffs/protocol.yaml` — renamed from the provisional `workflow.yaml`
on 2026-07-24, ADR-012: "workflow" is reserved for GitHub Actions files)
declaring seven stable roles as data —
`{id, title, model, responsibilities, never_does}` — plus the handoff sequence
and loop rules. The generated file is authoritative at runtime: Handoff
templates and CLAUDE.md name stable role ids and point to it instead of copying
editable titles or models. Two design rules:

- **Roles decoupled from models**: ids are `ceo`, `tech_lead`,
  `senior_engineer`, `junior_engineer`, `qa_reviewer`, `security_reviewer`, and
  `sre_reviewer`; the model is a nullable editable field on the role. Swapping
  next year's model is a one-line generated-config edit, not a template rewrite.
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

Distribution: in this repo at `skills/dev-ready/SKILL.md`, a standard location
directly discoverable/installable by the open Agent Skills CLI — **not** inside
generated projects (a generated project has no reason to regenerate itself).
The 2026-07-25 contract requires no Claude plugin metadata or registry
submission; skills.sh discovery is fed by CLI installation telemetry.
Precondition: the FR-14 flag contract is stable (v0.3 shipped). Cost: one
SKILL.md plus docs — smallest FR on this list.

### D-3. CLI internationalization — English + Traditional Chinese (FR-25) — REJECTED (2026-07-26)

**Status: Rejected.** Specced, then withdrawn before any implementation began.
FR-25's number is permanently retired. The scope line D-3 established —
generated project content stays English permanently because its consumer is a
model — survives the rejection and is now recorded in ADR-016.

Rejected because the need was misidentified. The pain is **discovery, not
runtime comprehension**: a Traditional Chinese speaker who cannot tell what
dev-ready is from its README never reaches a prompt or an error message in the
first place. Three facts made the cost indefensible once that was clear:

- **No demand evidence.** The v1.0 real-users gate is still open — dev-ready has
  no attributable external users — so this was localization for a hypothesis.
- **The runtime surface is small.** `init` is run once per project by a
  developer who reads English code all day. The number of sentences a user
  actually reads is far smaller than the 88 raise sites the refactor touched.
- **The cost was entirely front-loaded.** ~88 raise sites plus restructuring
  `check`/`upgrade` return types had to land before a single translated word.

Addressed instead at the documentation level: a focused `README.zh-TW.md`
(ADR-016). Reopening this needs **new evidence** — an external, non-maintainer
user asking for a localized CLI — not another round of the same reasoning.

One defect FR-25 would have fixed in passing remains open: `check` builds one
list of English sentences and serves it as both the human report and the
`--json` payload. That is a machine-interface problem rather than an i18n one
and can be raised on its own merits.

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

**Stack selected (2026-07-24, CEO):** the second template is a standalone
full-stack **Next.js** template; Vue is permanently out. It enters the manifest
as its own registry entry via the non-Copier strategies below
(`wrapped-generator` for `create-next-app`, or `degit-style` for a community
starter — concrete base pinned at implementation time, per this section's
original rule). A hybrid "FastAPI backend + Next.js frontend" variant was
rejected: maintaining the splice against upstream is a fork (violates ADR-001
and the solo-maintainer budget). Timing unchanged: v1.0, all hard gates below
still apply.

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
| v0.7 (DONE; v0.7.0 released) | FR-23 Handoff Protocol config, FR-28 Spec Loop, FR-24 generate skill, FR-29 progress reporting | FR-23×FR-28 share the generated rules surface; FR-29 landed before FR-25, which was subsequently withdrawn (D-3 rejected) |
| v0.8 (DONE; v0.8.0 released) | FR-26 multi-agent render targets | Canonical Content, Agent Target Pointer Stubs, stamp v4, and the v0.7 migration are complete; FR-25 remains withdrawn and Traditional Chinese is served by repository documentation instead |
| v0.9 (DONE; v0.9.0 released) | FR-30 Category-first selection, FR-31 Spec Loop always generated + Default Set, FR-35 retire the generated Handoff Protocol | Category selection, the lean Default Set, stamp v5, and the v0.8 migration are complete; ADR-020 changed generated projects only, while ADR-021 separately retired the internal protocol |
| v0.10 (added 2026-07-27) | FR-32 Mount Points, FR-33 Agent Target Map, FR-34 interview-driven generation skill, FR-36 selection reach and overlay-infrastructure corrections (added 2026-08-02) | Assembly and reach, all non-breaking, and all downstream of v0.9's contract |
| v1.0 | FR-27 second template (Next.js — selected 2026-07-24, see D-5); Web UI decision revisited | Platform step; gated on real-user feedback and the D-5 hard gates |

**2026-07-24 — v0.6 close-out re-confirmation (CEO-confirmed, Moofon):**
At v0.6 close the proposed post-v0.6 sequencing is confirmed unchanged — v0.7 =
FR-23 (workflow config) + FR-24 (generate skill); v0.8 = FR-25 (CLI i18n) +
FR-26 (multi-agent render targets); v1.0 = FR-27 (second template) + Web UI
decision. No amendment. Ratified by the CEO (Moofon) on 2026-07-24; the v0.6.0
release commit may proceed.

---

## 2026-07-24 (PM) amendment — v0.7 scope expansion (CEO-confirmed, Moofon)

Decided in the post-close-out grilling session of 2026-07-24; **supersedes the
same-day close-out confirmation above** for v0.7 scope only. v0.8 and v1.0 are
unchanged. Core decision record: ADR-012.

### v0.7 — Methodology + polish (FR-23, FR-28, FR-24, FR-29)

FR-28. **Spec Loop bundle + methodology layering (ADR-012).** A single new
catalog item `spec-loop` (a *bundle*, one explicit selection unit) vendors the
complete pinned asset/dependency closure of the four advertised missing steps
of the within-session development loop from mattpocock/skills (grill-with-docs,
to-spec, to-tickets, improve-codebase-architecture). It requires and
automatically resolves the existing tdd/diagnosing-bugs/code-review items,
whose compatibility ids remain independently selectable. The bundle also
supplies the role-neutral tracker/domain configuration expected by the upstream
skills, switching to process-v2 paths when Handoff Protocol is selected.
Catalog lands at 10/10. Three sub-deliverables:
- **Four-phase integration section** in generated CLAUDE.md, rendered **only**
  when both `agents` and `spec-loop` are selected: Planning (Lead:
  grill/to-spec) → Dispatch (Senior: to-tickets + handoff) → Execution (Junior:
  tdd/code-review) → Verification (QA/Security/SRE gates). Conditional
  rendering is an acceptance criterion: selecting only one side must produce
  no reference to the other side's skills.
- **`architecture.md` template** in the `docs` component (system overview /
  module boundaries / dependency rules skeleton), maintained by the Tech Lead
  role, linked from CLAUDE.md. The generator does not pre-create a root
  `CONTEXT.md` (single-entry-point rule, ADR-012); a selected domain-modeling
  skill may later create a glossary lazily when the user resolves terms.
- FR-23's config file is `docs/handoffs/protocol.yaml` (see D-1 as amended).
  FR-23 and FR-28 modify the same CLAUDE.md agent-roles surface and are
  designed together — this coupling is why FR-28 lives in v0.7.
  Together they adopt the process-v2 artifact model in generated projects:
  durable specs, per-ticket dispatch, one-ticket execution, and `03`–`06`
  gates; active phase working files are ignored.

FR-29. **Progress reporting for `init`.** Staged status lines on stderr
(`[1/4] Fetching base template (commit <pin>)…` → `done (12.3s)`), covering
fetch → overlay → verify → finalize. TTY gets a spinner; non-TTY degrades to plain
lines. No fabricated percentages (git clone has no trustworthy progress
fraction) and **zero new dependencies**: `cli` passes a progress callback into
`generate()`; lower modules never touch the terminal (module-boundary table
unchanged). Finalize stages beside the target and uses a same-filesystem atomic
rename, removing the existing cross-device partial-copy window. Sequenced before
FR-25 so the i18n message catalog is created over the final string set — FR-25
was subsequently withdrawn (D-3 rejected), which changes nothing about FR-29.

### v0.7 entry condition — cross-version upgrade E2E

Before any v0.7 feature work merges, CI gains a permanent job: install the
released `dev-ready==0.6.0` from PyPI, generate a project, then run the working
tree's `check` + `upgrade --dry-run` + `upgrade` against it and assert the
results. This is the first real exercise of FR-22's core promise (an old
project receiving a newer overlay) — it must exist before v0.7 ships, and it
remains as the standing N-1 → N regression test thereafter. (This CI job
installs from the network; it is CI tooling, not `src/dev_ready/`, so the
fetch-only network boundary does not apply.)

ADR-014 clarifies the lifecycle assertion: overlay-only upgrade preserves the
stamp's immutable Base Provenance while advancing Overlay Currency. A newer
manifest base pin is advisory because `upgrade` never materializes upstream
application changes; it must not be written into the stamp as false provenance.

### v0.7 release rider — distribution + a decidable real-users gate

*(v0.8 scope is amended at the end of this document — see "2026-07-26 amendment".)*

The D-5 hard gate "real users on the FastAPI template" is now **defined**:
signals from at least three independent external, non-maintainer identities
(one identity counts once), **or** strictly increasing adjusted PyPI downloads
across four complete UTC weeks with raw totals, known maintainer/CI invocations,
and the conservative subtraction recorded. If CI noise cannot be bounded, the
download branch cannot satisfy the gate. The v1.0
go/no-go reads this checklist, not a feeling. To give the gate a chance to
ever pass, the v0.7 release includes three distribution actions (~1 day, no
new FR): prove the FR-24 skill installs from the public repository and seed
skills.sh discovery telemetry; one launch post
(Show HN / r/FastAPI / X); a clear "report an issue" entry point in the README.

---

## 2026-07-26 amendment — v0.8 scope, ordering, and decisions (CEO-confirmed, Moofon)

Decided in the `grill-with-docs` session of 2026-07-26 and amended by a second
session the same day. Amends D-3 and D-4 for v0.8 only; v1.0 is unchanged.
Decision records: ADR-015, ADR-016. Accepted spec:
`docs/specs/v0.8/fr-26-agent-targets.md`.

**v0.8 ships FR-26 alone.** The first session sequenced FR-26 before FR-25 so
the i18n catalog would be built once over the final string set; the second
session withdrew FR-25 entirely, which makes the ordering question moot.

### FR-26 — Agent Targets (D-4 as amended, ADR-015)

The ecosystem settled the mechanism question. The Agent Skills standard
location is `.agents/skills/`, and the reference installer (`vercel-labs/skills`,
which distributes mattpocock/skills) maps 70+ agents to paths: most
standard-compliant harnesses (Cursor, Cline, Zed, OpenCode, Codex) read
`.agents/skills/` directly, while a minority use uniquely-named directories.
dev-ready therefore productizes the pattern it already applies to itself under
ADR-011:

- **Canonical Content is always written** — skills at `.agents/skills/`, rules
  at `AGENTS.md`. Standard-compliant harnesses need no declared target.
- **Agent Targets are selected** (`--agents claude,windsurf`) and declared as
  manifest data (`skills_dir`, nullable `rules_file`, nullable `mcp_file`), so
  adding an agent is a data change. v0.8 declares the two verified deviators.
- **Per-target artifacts are Pointer Stubs**, never symlinks (generation
  refuses link destinations, the inventory hashes bytes, and Windows requires
  elevated permissions) and never content copies. `CLAUDE.md` becomes
  `@AGENTS.md`.
- **MCP is rendered only where a project-level config exists** — Claude Code in
  v0.8. Windsurf's is user-global and dev-ready never writes outside the target
  project; the report says so rather than skipping silently.
- **The `agents` component is renamed `handoff`** — it always meant the Handoff
  Protocol scaffold, never a coding agent. `--no-agents` survives one version as
  a deprecated alias.
- **Stamp advances to version 4**, recording Agent Targets as Overlay Currency.
  `upgrade` infers `["claude"]` for pre-v0.8 projects and migrates through
  ADR-014's obsolete-file rules; the rename rides the same migration.

Declared per-agent paths are transcribed from a moving external ecosystem with
no FR-16-style byte-equality guard, so each must be re-verified at
implementation and at every bump.

### FR-25 — withdrawn (D-3 rejected, ADR-016)

FR-25 was specced and accepted earlier the same day, then withdrawn before any
code was written. The full rationale is recorded under D-3 above; in short, the
need was discovery rather than runtime comprehension, dev-ready has no
attributable external users yet, and the entire cost landed before the first
translated word. The spec is not retained — D-3 carries the reasoning, which is
the part worth keeping.

What survives the withdrawal is the language boundary itself, now ADR-016:
everything dev-ready emits and everything it generates stays English; Chinese
exists only as repository documentation aimed at external readers. That rule is
load-bearing precisely because the repository now contains a Chinese README, so
the question "should this file be translated too?" has a written answer.

### Accepted consequence

v0.8 carries one structural refactor — FR-26's layout migration — plus one
stamp migration. The permanent N-1 lifecycle gate is extended to assert the
layout migration, not only content currency. Withdrawing FR-25 cost nothing
already built: no i18n code was ever written, and FR-26 never depended on it.

---

## 2026-07-27 amendment — v0.9 and v0.10 scope (CEO-confirmed, Moofon)

Decided in the `grill-with-docs` session of 2026-07-27, the first planning pass
after the v0.8 release. Adds two versions between v0.8 and v1.0; **v1.0 is
unchanged** (FR-27 second template, Web UI decision, the same D-5 hard gates and
the same real-users checklist). Decision records: ADR-017, ADR-018, ADR-019,
plus a symlink amendment to ADR-015. FR numbering resumes at FR-30 (FR-25 is
permanently retired; FR-27 stays reserved for v1.0).

### The shape of the change

dev-ready has been a catalog of parts: ADR-010 promised free composition and
treated every item as peer. From v0.9 it becomes **an opinionated development
loop with enhancements around it** — a half-turn, not a full one. The Spec Loop
becomes the structure every generated project has; the catalog stays freely
composable but is presented, selected, and reasoned about along Categories that
match how a user thinks rather than how the overlay writes files.

The half-turn is deliberate. The Spec Loop is the only part of dev-ready with
real usage evidence — this repository has run v0.7 and v0.8 through it, and
since ADR-021 runs on it alone — which is why it earns the default. Locking the catalog shut is what was
rejected: a user who wants only `caveman` and `security-audit` is legitimate,
and with the v1.0 real-users gate still open those users are the likeliest
source of the evidence the gate demands.

### v0.9 — Selection model (FR-30, FR-31, FR-35) — DONE (v0.9.0 released)

One theme: **how a user chooses, and what they get by default.** Every breaking
change lands together so an upgrading user pays once.

FR-30. **Category-first selection (ADR-017).** Category — Dev, Security,
Quality, Design, Token Optimize — replaces Component as the user-facing axis;
Component survives only as the internal grouping deciding where files are
written. Dev is a mandatory single-select holding the development loop; the
other four are multi-select. Categories are named for what they hold at
release: "Ops" was rejected because its only member is browser end-to-end
testing, which is quality assurance. Adding a Category later is free; renaming
one breaks every stamped project.
`--skills` / `--mcp` / `--no-docs` / `--no-handoff` are replaced by a
Category-shaped contract, the interactive flow is rebuilt against it, and the
stamp advances to version 5 recording Categories with the resolved item set.
Two defects close as consequences: `mcp-config` stops being a selectable item
and becomes infrastructure generated when something needs it — repairing the
selection that fails today — and the two awesome-design-md DESIGN.md templates
become individually selectable, closing a gap open since v0.4 because `docs`
was modelled as a boolean component.

FR-31. **Spec Loop always generated; Default Set replaces the catalog cap
(ADR-018).** The Spec Loop stops being optional. It is modelled as the single
option of the mandatory Dev Category rather than as an unnamed constant, so the
loop stays visible in the menu and the stamp records which loop a project uses
— making a second loop a data addition rather than a record-format migration.
This reopens ADR-012's "preset, not framework" deferral to the minimum degree
that costs nothing. The loop gains `implement` — audited as never vendored, so
the loop dev-ready advertises has been missing its Execution step since v0.7 —
and an opt-in `setup-all` Enhancement for post-generation configuration. `init`
writes working defaults (local-markdown tracker, default domain-doc locations)
so nothing manual stands between `init` and a usable project. The ten-item cap
is retired; the limit moves to the **Default Set**, which is deliberately
small: the Spec Loop and the project's own documentation skeletons. Everything
else ships off by default, reference design-document templates included.
`project-orientation` is removed from the product: its whole content tells the
agent to read the auto-loaded root rules file, so it fails the curation
principle's own test.

FR-35. **Retire the Handoff Protocol from generated projects (ADR-020).** The
seven-role, four-layer scaffold — protocol configuration, four gate templates,
ticket directory, execution-report skeleton — is removed from the overlay along
with its Component, its flag, and the deprecated alias kept from v0.8. It
presumes a team of agents where an ordinary user has one, and it arrives before
the work it governs exists. **This FR touches only what is generated** — it does
not change how this repo develops. (That changed separately: ADR-021 retires the
Handoff Protocol as internal practice too, leaving the Spec Loop and
`docs/handoff/<version>/` working files.) Existing projects
retire the files through ADR-014's obsolete-file rules in the same transaction
as the version's other retirements; edited files are preserved and reported.
Nothing replaces it — no reduced scaffold, no preset, no stub.

**Accepted cost.** `--yes` changes meaning — a published interface — and needs
a CHANGELOG entry, a README correction, and N-1 lifecycle-gate coverage. Five
ids (`spec-loop`, `tdd`, `diagnosing-bugs`, `code-review`,
`project-orientation`) leave the selectable catalog while remaining in v4
stamps, so the migration maps or retires them rather than rejecting them. Two
shipped FRs (FR-10, FR-23) are retired, one of them a version's headline work;
that is a deliberate scope reduction and it is not cheap to reverse. The N-1
gate must assert the v4 to v5 stamp migration and both retirement passes
alongside content currency, as the v3 to v4 gate did in v0.8.

### v0.10 — Assembly and reach (FR-32, FR-33, FR-34)

One theme: **once selected, how content is assembled and who can read it.**
Nothing here is breaking.

FR-32. **Mount Points (ADR-018).** Every Enhancement declares the Spec Loop
skill its guidance is injected into, as manifest data. `react-doctor` mounts on
`code-review`, not on `implement`: `implement` coordinates and delegates, so
guidance attached there sits one level above the step that acts on it.
Injection is a third catalog effect kind beside the existing MCP-server and
npm-dev-dependency effects, applied at generation into a delimited, regenerable
block. Nothing edits a skill at runtime — a runtime edit marks the file
user-modified and permanently excludes it from `upgrade`.

**Corrected 2026-08-03** — see the amendment at the end of this document. The
mount is optional rather than universal, `implement` is a valid target, and the
"third catalog effect kind" sentence is wrong: injection happens inside the
overlay's whole-file rendering, because a catalog effect runs after the stamp
inventory is hashed.

FR-33. **Agent Target Map (ADR-019).** Measurement against `vercel-labs/skills`
`src/agents.ts` found that of 75 declared agents only 19 read `.agents/skills/`
at project level — **56 declare a unique project directory**. v0.8's two
declared targets are a data gap, not a capability gap. The map joins the
manifest `vendored` section at a pinned commit, a maintainer script derives
`agent_targets` from it, and CI fails on divergence — FR-16's mechanism applied
to a second kind of content, which closes the unmitigated risk ADR-015
recorded. Only `skills_dir` is derived; `rules_file` and `mcp_file` have no
upstream source and stay hand-declared.

FR-34. **Interview-driven generation skill.** FR-24's skill teaches an agent to
compose `dev-ready init` flags; it must be rewritten for FR-30's contract
regardless. It is rewritten as an interview: the agent questions the user about
what they are building, maps the answers to Categories and items, and then
composes the command. Mapping a described need onto a selection is what a model
does well and what CLI branching does badly. Distribution is unchanged — this
repository, outside the generated overlay (D-2).

FR-36. **Selection reach and overlay-infrastructure corrections** (added
2026-08-02 after grilling the shipped v0.9 surface; the two ADR-018 amendments
of that date carry the decisions). Every item is a defect in something v0.9
shipped, not new capability. The `Add Enhancements?` confirmation defaults to
`no`, so a user who accepts every default never reaches the item menu — the
Category-first selection FR-30 built is unreachable on the default path.
`docs/architecture.md` and `docs/requirements.md` are gated on the `docs`
Component, whose only items are two visual design references, so declining the
Default Set and taking no design reference silently drops the project's own
documentation skeletons; they become unconditional infrastructure. `setup-all`
retires into the always-generated loop, taking its generation-time text
substitution with it — that substitution is keyed on the id and would fire
wrongly once the id is gone. And the generated loop guidance is corrected to
name `implement`: v0.9 vendored it as the Execution step and then omitted it
from the only file every agent session reads, which is the failure mode ADR-018
created it to fix.

Sequencing note: (a)–(d) touch the same prompt, selection, and stamp-migration
surfaces as nothing else in v0.10, so FR-36 is independent of FR-32 and FR-33
and can run in parallel with either. FR-34 must land after it — an interview
skill that composes selection commands should be written against the corrected
contract, not the shipped one.

Also in v0.10: the README pair is refreshed for the Category model, the Default
Set, and the supported-agent count, and gains the detailed development-workflow
section this repository's README currently lacks — written for the *generated
project's* loop, the audience deciding whether to adopt dev-ready, rather than
restating the internal process AGENTS.md already owns. `README.zh-TW.md` is
updated only where the product facts it carries change — what dev-ready
produces and what the lifecycle commands guarantee — and gains none of the new
flags or exit codes (ADR-016). Its line describing the Default Set as "the Spec
Loop plus the project's own architecture and requirements skeletons" is one
such fact and does change.

## 2026-08-03 amendment — FR-32 correction, FR-37, and a licensing observation (CEO-confirmed, Moofon)

Written after grilling v0.10 Phase 2 against the code. Three outcomes.

**FR-32's mechanism above is wrong and is corrected.** The paragraph describing
injection as "a third catalog effect kind beside the existing MCP-server and
npm-dev-dependency effects" does not survive contact with the overlay. Catalog
effects run *after* the overlay writes its files, while the stamp inventory
hashes the rendered content *before* they run — so an effect-shaped mount
records a hash that can never match the mounted skill, and `upgrade` classifies
a file nobody edited as user-modified permanently. `classify_shared_targets`
excludes it again as a shared target. Injection therefore happens inside the
overlay's whole-file rendering; the declaration is manifest data validated by
the loader. Neither mistake raises anything at generation time, which is why the
rule is now recorded in `docs/architecture.md` rather than only in a spec. The
2026-08-03 amendment to ADR-018 carries the product half: a mount is optional,
it changes *when* an agent is reminded rather than whether it can find a skill,
and `implement` is a valid target for guidance that has no lower acting step.

**FR-37. Tech stack and standards sources in the generated `AGENTS.md`** (added
this session). The vendored `code-review` skill resolves its Standards axis by
looking for "anything in the repo that documents how code should be written,
such as `CODING_STANDARDS.md` or `CONTRIBUTING.md`" — and this manifest's prune
list removes upstream's `CONTRIBUTING.md`. A grep of the whole `templates/` tree
returns exactly one hit for `pytest`, `ruff`, or `mypy`: that line in
`code-review` asking for a file dev-ready itself deletes. So the Standards axis
of the review step every generated project ships has nothing to resolve to, and
falls back to the built-in smell baseline. The fix goes in `AGENTS.md`, which
already carries `## Stack` and `## Commands` and is the one file every session
loads; a per-skill copy would duplicate and drift, and a separate `tech-stack.md`
is one hop an agent may not take. This is not per-project customization: a
single pinned base template (ADR-001, ADR-002) makes the stack a constant until
FR-27 adds a second one, at which point this becomes a real decision rather than
a transcription.

**Licensing observation — recorded, not scheduled.** The two Apache-2.0 skills
carry their `LICENSE.txt` into every generated project. The twelve MIT
`mattpocock/skills` loop skills carry no license notice at all, while MIT's own
terms require the copyright and permission notice to travel with copies. This
predates v0.10 — it has been true since v0.7 — and FR-32 does not create it, but
FR-32 does make those files formally derived works, which puts it in view. No
legal conclusion is drawn here. Recorded so that the next person to look does
not have to rediscover that the two licenses are being treated differently.

### Considered and rejected in this session

- **Symlinks instead of Pointer Stubs** — re-examined on the reference
  installer's recommendation and rejected again; the reasoning is now recorded
  as a 2026-07-27 amendment to ADR-015 so the recurring question has a written
  answer.
- **A measured context budget instead of the item cap** — a better instrument
  and still the right one later, but it needs a defensible byte threshold and
  there is no usage data to calibrate one against. The Default Set limit bounds
  the same risk meanwhile (ADR-018).
- **Locking the catalog into a mandatory loop** — rejected; see the half-turn
  rationale above.
- **Everything in a single version** — rejected: two structural refactors
  landing on the same surfaces (CLI, stamp, overlay, verify, upgrade) is
  several times v0.8's workload for one solo maintainer, and the N-1 gate would
  have to assert two migrations at once.
- **Keeping the generated Handoff Protocol, defaulted off** — rejected: it
  preserves the whole maintenance surface (configuration schema, seven role
  records, six templates, their rendering, their conditional interaction with
  the Spec Loop, and their share of every future migration) to serve a
  selection nobody has been observed making. See ADR-020 for the alternatives,
  including a lighter two-role scaffold, which was rejected as a second
  unvalidated design.
- **`project-orientation` recategorized rather than removed** — rejected once
  its content was read: it directs the agent to the auto-loaded root rules file
  and repeats facts that file already carries. No Category makes an item worth
  its context cost.

### Graphify — evaluated, not adopted

Proposed for a token-optimization Category and **not adopted**. Three findings.
Its provenance does not meet ADR-009: the repository identity is inconsistent
between `Graphify-Labs/graphify` and the `safishamsi/graphify` path its own
install instructions use, branch references disagree (`v1` against `v8`), and
the license is stated as dual Apache-2.0/MIT without a single verified grant —
there is no 40-hex commit to pin against a license that has been checked. It
requires an LLM API key with no zero-key mode, and `graphify install` writes
into the user's home directory, which dev-ready never does; between them that
is three manual steps against the "no manual install step" rule in the
integration-modes table above. Finally the categorization does not hold: it
*spends* tokens on whole-project multimodal extraction to produce an
architecture report, where `code-memory` is the item that reduces per-query
cost.

Recorded here as a roadmap candidate rather than a rejection on merit — the
architecture-report output is genuinely useful. Reconsidering it needs a
resolved upstream identity, a pinnable commit carrying a verified license, and
a launch path that does not write outside the project.

---

## 2026-08-04 amendment — FR-38 into v0.10, v0.11 defined, ADR-022 (CEO-confirmed, Moofon)

Produced by a `grill-with-docs` session run against a project actually generated
with the released v0.9.0, rather than against the manifest. Everything below was
found by reading the generated tree. That method is the reason four of these are
defects rather than features, and it is worth repeating before each release.

### The prune list was wrong about two files

FR-7 has pruned `deploy-production.yml` and `deploy-staging.yml` since v0.2 on
the stated grounds that they "reference upstream's own servers and secrets."
Read at the pinned commit, `deploy-production.yml` opens with
`# Do not deploy in the main repository, only in user projects` and guards
itself with `if: github.repository_owner != 'fastapi'`. Upstream wrote both
**for downstream users**; they are the only two of the ten pruned workflows that
were. The remaining eight — `issue-manager`, `labeler`, `add-to-project`,
`latest-changes`, `smokeshow`, `detect-conflicts`, `zizmor`,
`guard-dependencies` — are genuinely upstream's own and stay pruned.

The consequence compounded quietly. dev-ready keeps `deployment.md`, and that
document spends its Continuous Deployment sections teaching how to use the two
workflows dev-ready had deleted. The documentation was never stale; the prune
list was wrong, and the mismatch read as a documentation defect for four
versions. Both files are restored under FR-38.

This also dissolved a proposal made in the same session for a `to-prod`
deployment skill. Its strongest justification was repairing that mismatch;
restoring the workflows repairs it at the source, and `deployment.md`'s 352
lines already cover the rest — Traefik's public network, secret generation, the
required environment variables, and the deployment command. A skill would have
become a second copy of an accurate document, free to drift. Rejected, with the
`.env.prod` convention it would have introduced: upstream uses a single `.env`,
so adopting `.env.prod` would be dev-ready inventing a convention it then has to
own, document, and ignore in git, for no gain over the file that exists.

### FR-38 lands in v0.10, not v0.11

Four defects, all in shipped v0.9.0, detailed at FR-38: `.env` ignored by no
`.gitignore` while dev-ready itself writes three random secrets into it; nothing
anywhere naming the superuser login or where its password is; upstream's
`localhost.tiangolo.com` in every project's CORS allowlist; and the prune-list
correction above. The first is the one that decides the version: dev-ready
generates a secret, tells the user nothing, and lets their first `git add .`
commit it. A version that ships new capability while leaving that in place has
its priorities backwards, and the v1.0 real-users gate wants exactly the users
this would burn.

`.gitignore` is repaired by prune-and-replace, the shape FR-7 and FR-8 already
established for `README.md`. No new mechanism was accepted for it: an injected
delimited block into upstream's own file was considered and rejected, because
FR-32's injection operates on files `build_overlay_content` produces and an
upstream file is not one of them.

### v0.11 is FR-39 and FR-40

**FR-39 `setup-project`** answers a question this repository had already
answered for itself and never carried into generated projects: the loop's chain
starts at `grill-with-docs` and never names the run-once setup step, so no agent
knows one exists. It is an always-generated first chain entry rather than a
Category or an Enhancement — a project whose owner cannot log in is not an
optional problem — which also means the stamp is untouched and no Category
identifier is added. Its interview is deliberately two questions and one gate:
it must stay the same order of magnitude as the vendored setup skill it
delegates to, because a run-once interview abandoned halfway is a project
configured never.

The values it refuses to ask for matter as much as the ones it asks. `DOMAIN`
was proposed and rejected on measurement: it is interpolated into Traefik
`Host()` router rules and into `VITE_API_URL`, a build argument baked into the
frontend bundle, so writing a real domain at setup time breaks local
development on day one and looks like a broken template rather than a wrong
answer. `SECRET_KEY` and `POSTGRES_PASSWORD` are shown and never asked for,
because a user-invented value is worse than `token_urlsafe(32)`.

**FR-40** takes the whole `awesome-design-md` set. Two of 103 is arbitrary
curation of content whose only purpose is choosing between directions. The
delivery question was settled by measurement rather than by instinct: markdown
compresses to about 30%, so the whole set costs roughly 766 KB in the wheel, and
that price buys every existing mechanism working unchanged. Generation-time
fetching was recommended in session and then withdrawn — ADR-002 forbids
resolving anything but the pinned commit, so it fetches identical bytes, and an
overlay path absent from `build_overlay_content` is classified obsolete by the
ADR-014 rules, which would **delete** an untouched design document on the next
`upgrade`. Single-select was also recommended and withdrawn: the two shipped
references are already multi-select and recorded together in v5 stamps, so it
would break the `--design` contract and strand those projects, to prevent a cost
a user has to opt into.

### ADR-022

The footer of every generated project links to FastAPI's GitHub, X, and
LinkedIn accounts and captions itself `Full Stack FastAPI Template`. Putting
dev-ready's own repository link there was proposed and rejected;
[ADR-022](decisions/adr-022-upstream-config-not-application-source.md) records
the boundary the rejection implies — dev-ready rewrites upstream configuration
and never edits upstream application source. The rule was already true in
practice and stated nowhere, and the alternatives are recorded because the
footer will be reported as a defect again.

### Accepted residue

`deployment.md` keeps roughly seven stale lines describing `LATEST_CHANGES` and
`SMOKESHOW_AUTH_KEY`, whose workflows are correctly pruned. Repairing them means
pruning and rewriting 352 otherwise-accurate lines. Recorded, not fixed.

Restoring the deploy workflows means a user who publishes a release before
setting up a self-hosted runner gets a job waiting on a runner label that does
not exist. That is upstream's behaviour for its intended audience and
`deployment.md` explains it.
