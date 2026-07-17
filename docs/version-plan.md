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

## Integration modes (see ADR-008)

Every third-party integration is classified into exactly one of two modes. This
classification drives license work, maintenance cost, and where the content lives:

| Mode | What ships | Redistribution? | License work | Examples |
|---|---|---|---|---|
| **Reference** | Config entries or original wrapper-skill text that point at the tool's official distribution channel (npm, binary release). The user installs/executes it themselves. | No | None | codebase-memory-mcp (`.mcp.json` entry), react-doctor (wrapper skill running `npx`) |
| **Vendor** | A snapshot of upstream content committed into `src/dev_ready/templates/`, pinned in the manifest `vendored` section with provenance. | Yes | Per-repo license review, THIRD_PARTY_NOTICES, NOTICE propagation for Apache 2.0 | caveman, mattpocock/skills subset, cloudflare/security-audit-skill, awesome-design-md, anthropics/skills examples |

Pinning philosophy: the *generation-time* rule (never fetch latest, ADR-002) is
unchanged and applies to everything dev-ready materializes. Reference-mode tools are
executed later, by the user's own choice, from the official channel — that version
risk is the user's, and wrapper skills mitigate it by recommending a pinned major
(e.g. `npx react-doctor@1`).

## Curation principles

- Every vendored skill must answer "what does the user lose if we drop it?" — no
  answer, no inclusion. Hard cap: **10 skills** in the skill catalog.
- The cap governs the *catalog*; the user picks any subset of it per project
  (FR-14), so catalog discipline is about maintenance cost and default quality,
  not about forcing content on users.
- Subsets, not whole repos: vendor only the files that earn their context-window cost
  in a generated project.
- Never vendor anything that is not clearly licensed for redistribution. Currently
  permanently excluded: anthropics/skills document-processing skills
  (source-available, prohibits productization); react-doctor source (Modified
  MIT/Commons Clause — wrapper skill instead); multica-ai/andrej-karpathy-skills
  until upstream adds a LICENSE file.
- Solo-maintainer budget: base-template bump stays weekly; vendored pins bump
  **monthly** (skill text churns slowly; review load must stay bounded).

---

## v0.3 — Reference integrations + stamp + item-level selection

Low-risk, no redistribution, no new license work. Ships value fast and lays two
foundations the rest of the roadmap depends on: the generation stamp (v0.6 needs
it) and item-level selection (the growing catalog needs it — building it now means
the CLI contract changes once, not twice).

FR-11. **Generation stamp.** `generate` writes `.dev-ready.json` at the root of every
generated project: dev-ready version, selected components *and selected items per
component* (FR-14), upstream pin (repo + commit), and — from v0.4 on — vendored
pins. Without this, projects generated before v0.6 can never be `check`ed or
`upgrade`d. Schema is versioned (`stamp_version: 1`). verify treats its presence as
a required path.

FR-12. **Codebase-memory MCP item.** The `mcp` component gains a `code-memory` item:
a `codebase-memory` server entry in the generated `.mcp.json`
(DeusData/codebase-memory-mcp, MIT). Reference mode: we ship configuration only;
the generated README/CLAUDE.md documents the one-line install from the official
release channel, and states plainly that the entry is inert until the user installs
the binary.

FR-13. **react-doctor wrapper skill.** An *original* skill (our own text, no vendored
code) — item id `react-doctor` in the `skills` component — that teaches the agent
when and how to run `npx react-doctor@<pinned-major>` on the frontend and how to
act on its findings. This sidesteps the Commons Clause question entirely: no
redistribution occurs.

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
- Open the LICENSE issue on multica-ai/andrej-karpathy-skills now (zero cost; the
  clock on v0.5 eligibility starts today).

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

FR-20. **Karpathy guardrails content** — *conditional on upstream license
resolution* (issue opened in v0.3). If resolved: fold the CLAUDE.md guardrail
guidance into our generated CLAUDE.md template with attribution. If unresolved by
v0.5 planning: drop from scope without renumbering.

(The formerly planned "skill-selection UX review" is retired: FR-14 resolved it in
v0.3 by decision, not deferral.)

## v0.6 — Lifecycle commands

FR-21. **`dev-ready check`.** Reads `.dev-ready.json` (FR-11) from an existing
project, compares against the running CLI's manifest: which dev-ready version
generated it, which components and items, whether pins are behind, whether
required/forbidden paths still hold. Read-only, exit codes mirror verify semantics.

FR-22. **`dev-ready upgrade`.** Re-applies a newer overlay onto an existing project.
Scope deliberately conservative: overlay-managed files only (skills, mcp config,
handoff templates, CLAUDE.md sections we own — per the stamp's item selection),
never upstream application code — that path was closed when `.copier/` was pruned
(ADR-005 amendment). Conflict rule: never overwrite user-modified files silently;
report and skip. Requires FR-21's stamp reading plus a recorded file inventory
(added to the stamp in this version).

Explicitly still out of scope after v0.6: additional base templates, Web UI
companion (decisions deferred, unchanged from requirements.md).

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
  bumps and reference mode being the default choice where viable.
- **Upstream license changes** (react-doctor terms, anthropics/skills terms) —
  reference mode limits exposure; vendored pins mean a license change upstream
  never retroactively affects an already-released dev-ready version, but bump PRs
  must re-check the license file on every bump (added to the bump-PR checklist).
