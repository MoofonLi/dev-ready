# ADR-008: Two third-party integration modes — vendor vs pinned dependency (v0.3+)

- Status: Accepted (2026-07-17); amended (2026-07-18): CEO decision — the product promise is "one command, Day-1 ready", so no integration may require a manual install step. The originally proposed "reference mode" (config + user installs the tool themselves) is replaced by **pinned-dependency mode**, which delivers zero-setup UX while still redistributing nothing.
- Context: The roadmap (docs/version-plan.md) integrates external tools and skill content: codebase-memory-mcp, react-doctor, caveman, mattpocock/skills, cloudflare/security-audit-skill, awesome-design-md, anthropics/skills, andrej-karpathy-skills. Some have restrictive or unclear licenses (react-doctor: Modified MIT with Commons Clause-style terms; anthropics document-processing skills: source-available, no productization; karpathy-skills: no LICENSE file). Shipping third-party content inside the wheel is redistribution and carries license obligations regardless of dev-ready being open source and non-commercial — redistribution rules do not depend on commercial intent. Full binary vendoring was evaluated and rejected as infeasible: 5 platform binaries × tens of MB exceeds PyPI project size limits, forces a dev-ready re-release per upstream binary patch, and makes dev-ready the redistributor of executables it did not build.
- Decision: every integration is classified by content type into exactly one mode.
  - **Vendor mode** — all *text content* that is legally redistributable: a curated subset of upstream content snapshotted into `src/dev_ready/templates/`, pinned in the manifest `vendored` section (ADR-009) with license and provenance, listed in THIRD_PARTY_NOTICES, with NOTICE propagation for Apache 2.0 content. Vendor everything that can legally be vendored.
  - **Pinned-dependency mode** — *executable tools*: dev-ready writes pinned launcher/dependency entries into the generated project. `.mcp.json` launches `uvx codebase-memory-mcp==<pin>` (published on npm and PyPI; every dev-ready user has uv per NFR-3); `react-doctor@<exact-pin>` is a devDependency in the generated frontend `package.json`, materialized by the `npm install` the user runs anyway. Zero manual steps; the exact pinned version arrives via official channels on first use; a dependency declaration is not redistribution, so restrictive terms (Commons Clause) are not triggered.
- Consequences: Both v0.3 tools integrate with zero license work and zero-setup Day-1 UX. Vendor-mode infrastructure (sync tooling, drift guard, NOTICES automation) is built once, properly, in v0.4. Scope note on ADR-002: "never fetch latest" governs what dev-ready materializes at generation time; pinned-dependency tools are fetched by the user's package manager at first use *at the exact version dev-ready pinned* — version changes arrive only through dev-ready pin bumps, preserving the reproducibility guarantee. Legal boundary independent of UX: content whose license prohibits redistribution is never vendored (anthropics document-processing skills permanently excluded; karpathy-skills accepted as MIT per its README declaration — no standalone LICENSE file, but the pinned commit preserves the grant as evidence).

---

## 2026-08-30 amendment — vendor mode vendors skills; commands and personas are not an asset class

Decided in the v0.13 Phase 5 `grill-with-docs` session, after reading
`addyosmani/agent-skills` at `d2c37ef6225dd8726cdd369a8030307f48592d26`. The two
modes are unchanged. What this amendment settles is a boundary the first two
Engineering Flows never tested.

### An upstream ships more than skills

`mattpocock/skills` and `obra/superpowers` are skill packs: the reusable unit is
a `SKILL.md` directory, and vendoring a curated subset of them delivers the
whole method. `addyosmani/agent-skills` is not shaped that way. Measured
2026-08-30, it ships three composable layers — 25 skills in `skills/`, nine
slash commands in `commands/*.toml` and `.claude/commands/*.md`, and four
personas in `agents/*.md` — and its own `AGENTS.md` names the commands as "the
orchestration layer" and the personas as roles a command fans out to.

dev-ready has one materialization path for authored agent content: a skill
directory written to `.agents/skills/`, surfaced to each selected
[[Agent Target]] by a [[Skill Link]] (ADR-028). It has no concept of a slash
command or a persona, in the manifest, in the overlay, or in the Agent Target
Map.

### The decision

**Vendor mode vendors skills. An upstream's slash commands, personas,
subagent definitions, hooks, and plugin manifests are not vendored**, whatever
the upstream's own layout calls them. Adding a second authored asset class is a
decision on its own evidence, not a side effect of vendoring a pack that happens
to ship one.

Two consequences are accepted rather than mitigated:

- **A vendored skill may reference an entry point the generated project does
  not have.** Several `addyosmani` skills name `/build`, `/review`, or the
  `code-reviewer` persona. FR-16 holds vendored files byte-identical, so dev-ready
  cannot edit the reference out, and it does not try.
- **Curation carries the residue.** A skill whose *mechanism* is the missing
  layer is excluded rather than shipped broken —
  `constraint-driven-development`, whose process is four command-keyed gates, is
  cut on this ground. A skill that merely mentions a command, or that names a
  fallback when the persona is absent, ships. Where residue remains, the
  flow's `docs/agents/<flow-id>.md` says so.

- **Considered: vendoring the commands and personas too** — rejected for this
  phase, not forever. It needs a manifest asset class, a destination convention
  per Agent Target, a Skill Link analogue, and a drift guard; that is a version's
  worth of work priced against evidence no user has asked for yet.
- **Considered: excluding every skill that names a command or persona** —
  rejected. It cuts working skills for a cosmetic reference and would leave the
  flow too thin to be a flow.

Consequences: the curated ratio is no longer a property of the upstream's size
alone — a pack whose value sits in a layer dev-ready cannot ship is curated
harder. The rule is stated in terms of asset class rather than of repository, so
the next upstream is measured against it without a new decision.
