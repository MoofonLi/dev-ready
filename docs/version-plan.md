# Version Plan — dev-ready v0.3 → v0.9 (+ post-v0.9 roadmap)

Status: Accepted (2026-07-17). Decided by CEO + Tech Lead as the final pre-agreed roadmap.
Amended 2026-07-24 (afternoon): v0.7 scope expanded — see "2026-07-24 (PM) amendment" below.
Close-out 2026-07-26: v0.7 is released — `v0.7.0` is tagged and published to PyPI. Distribution-rider evidence (skills.sh install proof, launch post URL, README issue entry point) is recorded separately against the v1.0 real-users gate.
Amended 2026-07-26: v0.8 scope, ordering, and decisions settled — see "2026-07-26 amendment" below (ADR-015, ADR-016).
Amended 2026-07-26 (later the same day): FR-25 (CLI i18n) withdrawn before implementation and D-3 rejected. v0.8 is FR-26 only — see "FR-25 — withdrawn" in the amendment.
Close-out 2026-07-27: v0.8 is released. FR-26 is shipped in `v0.8.0`, which is tagged and published to PyPI; Phase 4 documentation, review, release, and distribution verification are complete. FR-25 remains withdrawn settled history.
Amended 2026-07-27: v0.9 and v0.10 added between v0.8 and v1.0 — see "2026-07-27 amendment" at the end of this document (ADR-017, ADR-018, ADR-019). v1.0 is unchanged.
Close-out 2026-08-01: v0.9 is released. FR-30, FR-31, and FR-35 are shipped in `v0.9.0`; the Category selection model, lean Default Set, and generated Handoff Protocol retirement are complete. ADR-020 changed generated projects only; ADR-021 separately retired this repository's internal Handoff Protocol.
Close-out 2026-08-09: v0.10 is released. FR-32, FR-33, FR-34, FR-36, FR-37, and FR-38 are shipped in `v0.10.0`; Mount Points, the derived and drift-guarded Agent Target Map, the interview-driven generation skill, the selection-reach and overlay-infrastructure corrections, the generated project's own stack and standards source, and the secret-hygiene repairs are complete. The stamp stayed at version 5, so there was no migration phase. v0.11 (FR-39, FR-40, FR-41) is next.
Close-out 2026-08-18: v0.11 is released. FR-39, FR-40, FR-41, FR-42, FR-43, FR-44, and FR-45 are shipped in `v0.11.0`; the Engineering Flow, `setup-project`, the full Design Reference set, MIT notice propagation, CLI presentation, and Claude/Codex plugin distribution are complete. The stamp stayed at version 5. v0.12 (FR-46, FR-47) is next.
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
| v0.10 (DONE; v0.10.0 released) | FR-32 Mount Points, FR-33 Agent Target Map, FR-34 interview-driven generation skill, FR-36 selection reach and overlay-infrastructure corrections (added 2026-08-02), FR-37 stack and standards sources (added 2026-08-03), FR-38 secret hygiene and credential disclosure (added 2026-08-04) | Assembly and reach, downstream of v0.9's contract; the stamp stayed at version 5, and the only user-facing breaks are the `--agents` default and the retired `setup-all` identifier |
| v0.11 (added 2026-08-04; FR-41 added 2026-08-09) | FR-39 `setup-project`, FR-40 the full awesome-design-md set as Design References, FR-41 MIT notice propagation into generated projects | Setup and design reach: FR-39 closes the gap v0.10 left at the head of the generated loop, and FR-41 repairs a notice gap v0.10's own THIRD_PARTY_NOTICES made explicit |
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

**Corrected 2026-08-03** — the counts above were a planning-time estimate and
were superseded when the pin was measured during the Phase 3 grilling. The
shipped figures are recorded once, in
`docs/version_overview/v0.10-overview.md`; the property CI actually enforces is
that the manifest declares a target for every agent the pinned source gives a
project-level skills directory other than `.agents/skills`.

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

**FR-40** takes the whole `awesome-design-md` set. Two of 74 is arbitrary
curation of content whose only purpose is choosing between directions.
(*Corrected 2026-08-16 in the v0.11 Phase 3 grilling: this paragraph said 103,
a planning-time figure. Measured at the pinned commit, `design-md/` holds 147
markdown files — 74 `DESIGN.md` documents and 73 `README.md` stubs.*) The
delivery question was settled by measurement rather than by instinct: markdown
compresses to a measured 29.2%, so the whole set costs roughly 600 KB in the
wheel — taking it from 204 KB to about 803 KB, roughly 4% of the ~15 MB
dependency tree `uvx` already installs — and that price buys every existing
mechanism working unchanged. Generation-time
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

---

## 2026-08-09 amendment — the real-users gate has one live branch, and FR-41 (CEO-confirmed, Moofon)

Produced by the `grill-with-docs` session on v0.10 Phase 6, the release phase.
Two findings outlive that phase. Neither changes v0.10's scope.

### Branch B of the real-users gate is structurally blocked

The v0.7 release rider defined the gate as two independent branches: three
attributable external identities, **or** strictly increasing adjusted PyPI
downloads across four complete UTC weeks with maintainer and CI invocations
conservatively subtracted. It also stated the failure condition plainly — *"If
CI noise cannot be bounded, the download branch cannot satisfy the gate."*

That condition is met, and by this repository's own design. The permanent
`upgrade-from-release` CI job installs `dev-ready==<N-1>` from PyPI on every push
and every pull request, so a meaningful share of the download aggregate is
traffic dev-ready generates about itself, and PyPI's series cannot separate it.
v0.9's overview recorded the consequence per week as "not computable" and v0.10
would have recorded the same table again.

The noise is not *unboundable in principle* — workflow-run counts are queryable
through the GitHub API, and the installs per run are a constant this repository
controls, so a conservative upper bound is available for roughly half an hour of
release-day work. That work was weighed at v0.10 and declined: the raw series was
already non-monotonic at v0.9 (730 falling to 669), so the expected outcome of
computing the bound is a *definite no* rather than a pass.

**Recorded consequence: v1.0's real-users gate is decided by Branch A alone**
until someone chooses to bound the noise, and releases stop re-deriving the
Branch B table. A version overview states the raw weekly totals it can observe,
names this amendment, and moves on. Reopening Branch B needs the bound computed,
not another release's worth of "not computable" rows.

This is a narrowing of an evidence rule, not of the gate itself: three
independent external non-maintainer identities remains exactly what it was, and
FR-27 still may not start before it passes.

### FR-41 — MIT notice propagation into generated projects

The 2026-08-03 licensing observation above is promoted from recorded to
scheduled, and lands in v0.11. The two Apache-2.0 skills carry their
`LICENSE.txt` into every generated project; the twelve MIT `mattpocock/skills`
loop skills carry no copyright or permission notice at all, while MIT's terms
require the notice to travel with copies.

What changed is not the facts but their standing. v0.10 is the first version
whose own `THIRD_PARTY_NOTICES.md` states that the copies written into a
generated project may be modified and are therefore derived works, and FR-32 now
injects dev-ready's own text into those same files at generation time. A
discrepancy the repository documents about itself is no longer one it can leave
unscheduled.

It did not land in v0.10 because the release phase carries no feature work: a
vendored LICENSE is a new managed path, a stamp-inventory change, and drift-guard
coverage. It is small, and it is not a release-day edit.

No legal conclusion is drawn, here or in any user-facing document. The
obligation, if it is one, predates v0.10 by three versions; what this amendment
fixes is that nobody owned it.

---

## 2026-08-12 amendment — v0.11 expanded, v0.12 and v0.13 defined (CEO-confirmed, Moofon)

Produced by a `grill-with-docs` session run against the shipped v0.10.1 selection
path and against the reference installer's source at its pinned commit, rather
than against either project's documentation. That method is why four of the eight
new requirements are defects and why two proposals reversed direction mid-session.
**v1.0 is unchanged** — FR-27, the same D-5 hard gates, and the Branch A-only
evidence rule the 2026-08-09 amendment left in place. Decision records: ADR-024,
ADR-025, plus amendments to ADR-003, ADR-012, ADR-015, and ADR-017.

### The interactive selection path was largely theatre

Three findings, all from reading `src/dev_ready/prompts/collect.py` against what
FR-30 and FR-31 designed:

- `_prompt_development_loop` returns early when the catalog declares one loop
  (`:258`). **The loop question has never been asked in any released version.**
- Both branches of `Use the Default Set?` (`:69-85`) produce byte-identical
  selections — `default_set.enhancements` is empty and one loop exists. **The
  first question in the flow changes nothing.**
- `dev` is offered among the five Category checkboxes and then force-added
  whether or not it was checked (`:186-197`), in a Category holding no
  Enhancement. **An option whose selection has no effect.**

FR-36 corrected this class of defect in v0.10 by grilling the shipped v0.9
surface. Repeating that exercise one version later found three more, which
argues for making it a standing pre-release step rather than a thing that
happens when someone thinks of it.

### `spec-loop` is renamed `mattpocock`, and the recommendation that lost

The session recommended keeping the id and changing only its display title:
the loop's twelve skills are `mattpocock/skills` verbatim, so the name is
accurate, while FR-39's `setup-project` and FR-32's injection are making the
content a blend, so an author-shaped id would drift toward false.

That was overruled by a better argument. **An id's job in a multi-flow catalog
is to say which flow**, and all three scheduled candidates are spec-driven —
`spec-loop` states the property they share, so it discriminates nothing. The
accuracy defence only established that the name was not a lie; it never
established that it was useful. The rename also costs less now than it ever
will again: the v1.0 real-users gate is unmet, so no external project needs
migrating. ADR-012 recorded this exact cost in v0.7 and it is being paid on
purpose, with a permanent `spec-loop` to `mattpocock` alias and no stamp version
change.

### Pointer Stubs are retired, and the cheaper half lost

ADR-015 rejected symlinks twice. One of its three mechanics is measurably wrong:
a Windows **junction** requires no elevation, and the reference installer creates
exactly that (`installer.ts:255-256`). Reading `add.ts:770-800` also showed the
convention is an explicit `InstallMode = 'symlink' | 'copy'` prompt, not a
default.

The session recommended adopting **`copy` only**. That remains the cheaper half
by a wide margin — copies are more entries in the same path-to-bytes mapping
`apply_overlay` already writes and `content_inventory` already hashes, needing
no new write primitive, no second inventory shape, and no change to the
traversal guard at `upgrade.py:33-42`, which refuses any path crossing a symlink
and would otherwise refuse dev-ready's own managed files. The CEO chose to offer
both modes, because the convention being adopted offers both. ADR-025 records
the design that makes `symlink` safe: the mode is an explicit recorded input
rather than a detected fallback (so NFR-1 holds), and links are excluded from
the stamp inventory (so the traversal guard never meets one).

The costs ADR-015 recorded are carried forward rather than dismissed. A junction
has **no git representation at all**, and its target is absolute, so a
`symlink`-mode project's agent directories are machine-local and break on move.
`copy` is therefore the non-interactive default, and the report states the
consequence when `symlink` is chosen.

### npx was rejected as a channel; the complaint underneath it was not

Proposed on two grounds — easier installation, and plainer-looking screens than
Node-ecosystem installers. The first is rejected: every route to `npx dev-ready`
adds a prerequisite, discards ADR-005's Copier foundation, or fails NFR-2. The
second is real and has nothing to do with npx — the polish belongs to
`@clack/prompts`, not to the launcher — so it becomes FR-44 and ships with the
prompt rewrite it shares a surface with.

Kept distinct, because the two were conflated once and will be again:
`npx skills add MoofonLi/dev-ready --skill dev-ready` publishes nothing to npm.
It runs the cross-agent installer, which fetches the Generation Skill from this
repository's GitHub source. Rejecting npx as dev-ready's distribution channel
says nothing about it.

### Discovery is the binding constraint on v1.0, so storefronts are worth a small FR

With Branch B structurally blocked (2026-08-09) the gate is three attributable
external identities and nothing else, which makes discovery the only lever left.
Both ecosystems accept a thin manifest over an existing directory —
`.claude-plugin/plugin.json` and `.codex-plugin/plugin.json` — and Codex
discovers skills by the `skills/<name>/SKILL.md` layout this repository already
has, so FR-45 duplicates no content. An in-session claim that Codex has no
plugin format was **wrong** and is corrected here: it was inferred from the
pinned `vercel-labs/skills` source, which knows only `.claude-plugin/`, and that
proves what one installer consumes, not what an ecosystem offers. Codex's plugin
system postdates that reasoning.

> **Corrected 2026-08-17 (ADR-027).** The paragraph above calls a manifest a
> storefront. It is not one, and that conflation is what made v0.11's Phase 4
> plan ship files nobody could install from. See the 2026-08-17 amendment at the
> end of this document.

### Flow recommendation is blocked on there being flows to recommend

A comparison of the three frameworks was offered as material for a skill that
would recommend one. It cannot precede the second flow, and it does not become a
new skill: FR-34's interview already questions the user, maps answers onto a
selection, and composes `--development-loop`, and its own rules forbid composing
a command that asks a second set of selection questions. It is written as
**selection criteria** rather than as a comparison — vendored content is held to
upstream by FR-16's byte-equality guard, while a claim about a project dev-ready
does not ship has no guard and goes quietly false when that project changes.

### Provenance results

Checked against ADR-009's standard during the session. `obra/superpowers` (MIT),
`addyosmani/agent-skills` (MIT), and `ayghri/i-have-adhd` (MIT) all resolve to a
single identity with a verified license and are schedulable; `i-have-adhd`
needed the check, because four repositories share that name and one carries no
license at all. `headroomlabs-ai/headroom` is Apache-2.0 and resolves cleanly,
but it is **not a skill** — it is a library, proxy, and MCP server — and it
carries the profile that disqualified Graphify: a documented flow that wraps the
agent session and installs Serena, and Codex instructions requiring an absolute
binary path dev-ready cannot write. FR-49 states the conditions it must clear;
until then it is a candidate, not a schedule entry.

### headroom — gate measured, two conditions failed (2026-08-12)

FR-49's gate was written in this session and closed in it, against
`headroom-ai==0.34.0`, by installing and running the thing rather than by
reading its README. Three of five conditions pass: it launches under `uvx`, it
needs no API key, and it has real standalone value with no proxy — 54% token
reduction on JSON, 26% on log lines, and `headroom_retrieve` returning the exact
original by hash from a **fresh process**, which the `--help` text had implied
required the proxy.

Two fail. It writes `~/.headroom/` on any invocation, including `--help`, and
running the MCP server fills it with a SQLite store of the **original content**
of everything compressed plus a persistent `install_id` and two JSONL logs; the
store is relocatable by environment variable but `~/.headroom` itself is
hardcoded. And `BEACON_DEFAULT_ON = True` — anonymous session telemetry uploads
to a third-party endpoint **by default**, fail-open by the code's own
description, though `DO_NOT_TRACK` and `HEADROOM_BEACON=off` both stop it.

The second failure was not in the gate and is the more important one, because it
generalises: **a pinned-dependency item lands in every generated project's
`.mcp.json`, so dev-ready would be the reason a user transmits anything.** That
is the shape of failure FR-38 spent a version repairing — dev-ready doing
something on a user's behalf and not saying so. "No outbound telemetry on by
default" therefore joins the standard for pinned-dependency candidates, and
`code-memory` should be measured against it too, since it never was.

Also recorded because it narrows the item's value even if the gate is later
reopened: headroom returns **code unchanged** (`router:protected:recent_code`)
and **file listings unchanged** (`router:noop`). Its wins are on structured data
and logs, not on the file contents a coding agent reads most.

headroom stays a candidate on the same footing as Graphify. Reopening needs the
store fully relocatable and telemetry defaulting off, or a deliberate decision to
ship a hardened `.mcp.json` entry with disclosure in the generation report —
which would leave dev-ready maintaining an opt-out against a moving upstream with
no FR-16-style guard.

### Accepted against recommendation

Unreleased flows are **listed in the menu** marked `(coming soon)`, which the
session argued against and the CEO decided. The cost is named rather than
hidden: `status` is a third catalog state that prompts, every selection flag,
and the Generation Skill's trigger list must each handle, for entries nobody can
select, and every such entry must be removed as its flow ships or the menu
accumulates promises. Placeholder text carries no version number — a shipped
menu that names v0.12 starts lying the moment the roadmap moves.

### Sequencing

| Version | Contents | Rationale |
|---|---|---|
| v0.11 | FR-39, FR-40, FR-41, **FR-42** Engineering Flow selection and interactive rework, **FR-43** Flow Chain guidance, **FR-44** CLI presentation, **FR-45** plugin manifests | FR-42/43/44 rewrite one surface — the prompts and the generated loop guidance — so splitting them edits the same files twice. FR-39 puts `setup-project` at the head of the chain FR-43 describes; apart, that sentence is written twice. FR-45 is thin and serves the only live branch of the v1.0 gate |
| v0.12 | **FR-46** Skill Delivery Mode, **FR-47** `superpowers` + flow recommendation | FR-46 takes a version largely to itself for FR-26's reason: write path, stamp inventory, `verify`, `upgrade`, and a migration off Pointer Stubs |
| v0.13 | **FR-48** `addyosmani/agent-skills`, **FR-49** Token Optimize additions | The third flow retires the last `status` placeholder; FR-49's second item is gated and may not ship with its first |
| v1.0 | FR-27 second template; Web UI decision revisited | Unchanged. Still gated on Branch A |

---

## 2026-08-13 amendment — v0.11 Phase 1 grilling: FR-42 scope, FR-44 definition, `--flow` (CEO-confirmed, Moofon)

Produced by the `grill-with-docs` session on v0.11 Phase 1, run against
`src/dev_ready/` at v0.10.1 and against measured output rather than against the
phase plan. **v0.12, v0.13, and v1.0 are unchanged**, as is FR-39, FR-40, FR-41,
FR-43, and FR-45. Decision records: amendments to ADR-017, ADR-018, and ADR-024;
a new `CONTEXT.md` term, [[Announced Flow]].

Two of the four findings below are defects the plan would have shipped, and both
were found the same way the 2026-08-04 and 2026-08-12 sessions found theirs — by
reading and running the code instead of the document about it.

### The plan's `(coming soon)` declaration does not load

v0.11's plan says to declare `superpowers` and `addyosmani` with no `paths` and
no `steps`. Three loader validations reject that, and the third is not a menu
problem: ADR-018's mount rule requires every mounted Enhancement's mount to name
a step of *every* declared loop, so a step-less loop fails all six declared
mounts and `load_default_manifest()` raises before any command runs. dev-ready
would not start at all.

`status` therefore stays a manifest field and the loader **partitions on it**,
into a collection the selection machinery structurally cannot reach. An
Announced Flow is consequently not a Catalog Item — see the ADR-024 amendment of
this date for the reasoning and for the two alternatives rejected.

### FR-42 gains a fourth defect: flag reach

FR-42 was scoped to three shipped defects in `prompts/collect.py`. A fourth, of
the same class and on the same surface, sits in `prompts/answers.py`. Measured
against the shipped v0.10.1 catalog: `--agents windsurf` selects **all nine
items and asks no question**; so do `--security security-audit` and
`--development-loop mattpocock`. A user who narrows one Category receives the
whole catalog; a user who names an Agent Target is never shown a Category.

FR-40 turns this from surprising into serious in the very next phase:
`--security security-audit` would select **110 items** once the full
`awesome-design-md` set is vendored.

The rule adopted is **a flag answers only its own question** — unmentioned
Categories resolve to the Default Set, and `--agents` stops suppressing the
prompt flow (ADR-017, as amended this date). It is in FR-42 rather than in a new
FR because Phase 1 rewrites both functions anyway; scheduling it separately
means editing `answers.py` and `collect.py` twice. It costs one more
breaking-change line and a rewrite of the default column in `docs/cli-spec.md`.

### FR-44 gets a definition, and it is narrower than "presentation"

FR-44 shipped into the plan as "restyle the prompts and the generation report"
with no acceptance criterion. Its origin narrows it: the 2026-08-12 amendment
records the complaint as being about the **prompt screens**, and that "the
polish belongs to `@clack/prompts`, not to the launcher."

FR-44 is therefore: a unified `questionary` style across every prompt, with an
Announced Flow rendered as a disabled row; and a **re-laid-out generation
report**, in plain text. The report is not colourised. `render_report` is a pure
function and terminal policy belongs to `cli`, so report colour would mean a new
permanent policy surface — TTY detection plus a `NO_COLOR` convention, threaded
down — bought for very little.

The report's measured defect is real and is what FR-44 fixes there: the
`overlay:` line joins every written path with commas onto **one line**, which is
**2,398 characters for the leanest possible project** (58 paths) and **39,089
characters** for `--categories all --agents all` (989 paths), before FR-40 adds
101 more documents.

### `--flow`

ADR-024 renamed the concept to Engineering Flow and renamed its value, leaving
the flag reading `--development-loop`: one concept, three names. `--flow` joins
it as a second option string on the same argparse argument — both permanently
accepted, `--flow` documented. The plan's "no other identifier is renamed in
this version" constraint is deliberately relaxed for this one case only, because
the change breaks nothing, costs nothing, and is cheapest now while the
real-users gate is unmet. The stamp field stays `development_loop`.

### Corrections carried into the spec rather than into a decision

- The loader special case at `manifest/loader.py:133` is **deleted, not
  renamed**. It exists only so the live catalog may declare an id that is also
  in `RETIRED_LOOP_ITEM_IDS`; after the rename nothing declares `spec-loop`, and
  renaming the string to `mattpocock` is worse than dead — `mattpocock` is not a
  retired id at all.
- `prompts/answers.py:359` hardcodes `'spec-loop'` as the name of the mandatory
  loop inside the retired-Enhancement error and must change. The same string
  then produces two different errors on two different flags, which is correct
  and is an acceptance criterion, not an accident.
- `ProjectSelection.categories` is derived from the selected items once the
  Category checkbox is deleted. Nothing reads the stamp's `categories` field —
  `recorded` always re-derives it — and deriving makes an all-Enter interactive
  run and `--yes` produce byte-identical stamps, which is the parity FR-31 asked
  for.
- The plan's VERIFY note about `initially_selected=()` on a single-item checkbox
  is closed: `_questionary_asker.py` sets `checked=choice in initially_selected`
  and nothing else can check a row. The v0.10 note it descends from described
  the state *before* that parameter existed. It stays as a test assertion, not
  as an open risk.
- `templates/claude/spec-loop/` is renamed to `templates/claude/mattpocock/`.
  This is not cosmetic: FR-43 requires the per-flow document to be **keyed on
  the flow id, not hardcoded**, which a source directory named after the retired
  id cannot satisfy. Generated output is unchanged — the destination stays
  `docs/agents`. Whether those three configuration files are per-flow or shared
  infrastructure is deliberately **not** decided here; v0.12 decides it after
  reading `superpowers`, per this plan's own rule about abstracting before a
  second user exists.
- The `--dev` flag is kept although it can only ever resolve to an empty set. It
  is in the published contract, and removing it would be a second breaking
  change bought for tidiness.
- Prerequisite verified: `dev-ready 0.10.1` is published on PyPI, so Phase 1's
  N-1 baseline rollover has its artifact. The most valuable new assertion in the
  phase is that a project generated by the released 0.10.1 — recording
  `spec-loop` — upgrades cleanly and comes out recording `mattpocock`.

### "One phase owns one file" fails wherever a test binds that file (found in implementation)

Found while implementing Phase 1's rename, and corrected mid-phase. The plan gave
Phase 4 sole ownership of `skills/dev-ready/SKILL.md` so it would be corrected
once against settled text. That optimization is unavailable: the Generation
Skill's contract test cross-checks the file's documented identifiers against the
live catalog, which makes the file a **dependency of the catalog rather than a
description of it**. Renaming the identifier in Phase 1 and correcting the file in
Phase 4 leaves the suite red across three phases, which no ticket's standing rules
and no phase's exit gate permit.

Phase 1 therefore corrects exactly the three identifier facts the test binds — the
development-loop mapping entry, the worked example's flow value, and the sentence
naming the resolved flow. The retired-identifier sentence keeps naming
`spec-loop`, which is still a retired Enhancement id. Phase 4 still owns the rest:
flag spellings, the announced flows and their failure behaviour, and the chain.

**The general rule, which outlives this version: file ownership follows test
binding.** A phase may reserve a file only while no test ties it to code another
phase changes.

### The same trap is in Phase 3, and it is larger

The same contract test requires the skill's per-Category item list to equal
**exactly** the catalog's items for that Category. FR-40 takes the design
Category from 3 items to roughly 104. Taken literally, Phase 3 must add ~101
hand-written trigger sentences to the one file whose entire purpose is to stay
small enough for an external agent to load — which is the context-bloat risk this
plan lists first, arriving in the artifact least able to absorb it.

Recorded, not decided: Phase 3's own `grill-with-docs` resolves it. The shape of
the choice is already visible — either the skill enumerates every design
reference, or the contract test stops demanding equality for a Category whose
membership is derived rather than curated, in which case what the skill must
teach instead (the `all` selection, and where the full list is obtainable) has to
be specified. Deciding it now, three phases early and without FR-40's measured
document count, would be deciding it on an estimate.

**Resolved 2026-08-16 in the Phase 3 `grill-with-docs`: the skill enumerates,
and the derivation script writes the section.** Withholding the decision was the
right call, because the estimate was wrong in both directions. The catalog goes
to **74**, not ~104, so the burden is **72 lines rather than ~101**, taking
`skills/dev-ready/SKILL.md` from 11,939 to roughly 17,000 bytes. And the
exemption turned out to have nowhere to point: `init`, `check`, and `upgrade`
are the entire CLI, so **no command enumerates the catalog**, while an unknown
item id exits 2 — leaving an offline agent to guess ids like `design-theverge`,
`design-bmw-m`, and `design-dell-1996` from a brand name. The context-bloat
objection is answered instead by ownership: the derivation script writes that
section as well as `manifest.json`, so no one hand-maintains 72 lines and a pin
bump cannot leave the contract test red (ADR-019, 2026-08-16 amendment). This
also names a standing weakness in the older `sync_agent_targets.py`, which
writes only `manifest.json` and leaves 57 Agent Target lines hand-maintained
behind the same test; repairing that is not v0.11 work.

---

## 2026-08-17 amendment — v0.11 Phase 4 grilling: FR-45 is distribution, not two files (CEO-confirmed, Moofon)

Produced by the `grill-with-docs` session on v0.11 Phase 4, run against the two
published plugin specifications and against a shipped third-party repository
rather than against the phase plan. **v0.12, v0.13, and v1.0 are unchanged**, as
are FR-39 through FR-44. Decision record: the new **ADR-027**; three `CONTEXT.md`
terms — [[Plugin Manifest]], [[Marketplace Catalog]], [[Plugin Directory]].

Like the 2026-08-04, 2026-08-12, 2026-08-13, and 2026-08-16 sessions before it,
this one found a defect the plan would have shipped, and found it the same way —
by reading the specification instead of the document about it.

### A manifest describes; a catalog publishes; a directory sells

FR-45 and the phase plan both use "manifest" and "storefront" as if they named
one thing. They name three, and only the third is discovery.

A **plugin manifest** describes one plugin to one ecosystem and reaches nobody.
A **marketplace catalog** is what an install command actually fetches:
`/plugin marketplace add owner/repo` reads `.claude-plugin/marketplace.json` at
the repository root, and `codex plugin marketplace add owner/repo` reads
`$REPO_ROOT/.agents/plugins/marketplace.json`. Neither command has any other way
into a repository. A **plugin directory** is the browsable storefront FR-45 is
justified by, and it is entered only by submission and review.

So the two-file plan produced **no install path in either ecosystem**, and
Phase 5's by-hand install verification could not have passed. FR-45 ships four
files instead, both catalogs declaring the repository root as the plugin
(`"source": "./"`), which is what keeps one skill directory serving every
channel with no second copy. The Codex path semantics were checked against
`appwrite/codex-plugin` rather than inferred: its catalog sits at
`.agents/plugins/marketplace.json` and writes `"path": "./plugins/appwrite"`, so
a source path resolves against the repository root.

### A skills-only plugin qualifies for both public directories

An in-session claim that Codex's directory structurally excludes dev-ready was
**wrong** and is corrected here before it reached disk. Codex's submission page
states that "A plugin can contain skills, an MCP server, or both", and its
production-server URL, domain verification, and tool-annotation requirements are
each conditional on the plugin containing MCP. What does apply to a skills-only
submission is the submitter's individual identity verification in the OpenAI
Platform, an org role with `Apps Management` write access, and at least five
positive and three negative test cases.

Anthropic's path is cheaper — a Console form that serves individual authors, plus
the automated screening that `claude plugin validate` reproduces locally — but it
pins an approved plugin to a commit SHA and syncs its public catalog nightly.

Both submissions therefore run **after** the release tag, and **the acceptance
criterion is that they were made, not that either was listed.** Neither
organization states a review turnaround. Every other v0.11 criterion is something
the repository can prove; a queue in someone else's building is not, and a
version that waits on one has handed its release date away.

### The repository root becomes a shipping surface

This is the cost of the choice that avoids forking the skill. With the root
declared as the plugin, Claude and Codex read component directories from it, so a
future top-level `agents/`, `commands/`, `hooks/`, `bin/`, `monitors/`,
`.mcp.json`, `.lsp.json`, or `settings.json` would ship to every installed user
with no announcement — and `hooks/` and `bin/` ship executable behaviour, not
text. An offline guard test asserts the root holds none of them and that
`skills/` holds exactly `dev-ready`.

The subdirectory alternative was rejected for the reason FR-45 itself gives: the
only directory holding the skill is `skills/dev-ready/`, so its manifest would
ride into every user's skills directory through the cross-agent installer, which
copies the whole folder. Measured, the accepted cost is 4.8 MB across 366 tracked
files copied into `~/.claude/plugins/cache` once per installed version, against
the roughly 15 MB of runtime dependencies `uvx dev-ready` already installs.

### Two of the three exposures were never unguardable

The plan recorded FR-45's exposure as one thing — moving external specifications,
no FR-16-style guard, re-verify by hand at every bump. That is exactly right for
**schema drift** and wrong for the other two.

**Version drift** is guarded. Claude pins an installed plugin to the `version`
string and delivers an update only when it changes, and Codex requires the field,
so a stale manifest strands every installed user with no visible symptom. A test
asserts each manifest's `version` equals `dev_ready.__version__`, and the
`release` skill bumps four files rather than two.

**Repository-root content** is guarded, as above.

The general shape is worth keeping: "this comes from a moving external spec" is a
statement about *one* of the things a transcribed file can get wrong. Which
fields exist is theirs. Which values we wrote is ours.

### Recorded, not decided

- CI's `paths-ignore` narrows from `.agents/**` to `.agents/skills/**` in both
  event blocks, because Codex fixes its catalog path inside a tree this
  repository already ignored, and the new version guard would otherwise be blind
  to the one file it guards. `.claude-plugin/` needed no change — glob matching
  is by whole path segment, so it never matched `.claude/**`.
- The distributed skill teaches `--flow` and drops every mention of
  `--development-loop`, which stays a permanently accepted alias documented for
  humans in `docs/cli-spec.md`. Measured: the old spelling appears in no
  generated project content. This overrides the phase's own stale acceptance
  bullet, written before ADR-024's 2026-08-13 amendment.
- The public names are both `dev-ready`, and the resulting `/dev-ready:dev-ready`
  invocation is accepted rather than fixed by renaming `skills/dev-ready/` —
  that directory name is the documented `--skill` argument, asserted against both
  READMEs by the Generation Skill's contract test.
- No CI job runs `claude plugin validate .`; it needs the `claude` CLI as a global
  tool, which the standing constraints forbid tests to depend on. It joins the
  by-hand Phase 5 checks, which now number four.
