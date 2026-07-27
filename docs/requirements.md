# Requirements — dev-ready

Status: v0.8 released (2026-07-27). FR-26 is shipped in v0.8.0; documentation,
review, release, and distribution verification are complete. Historical scope
and roadmap details are in docs/version-plan.md.

## Problem Statement

Starting a production-grade FastAPI project that is ready for AI-assisted development requires assembling many pieces by hand: the base template, Canonical Content (`AGENTS.md` and `.agents/skills/`), optional Agent Target discovery files, MCP server setup, and design documentation. dev-ready is a CLI, run via `uvx dev-ready`, that scaffolds all of this in one command.

## Functional Requirements

FR-1. The user can run `uvx dev-ready` (or `uvx dev-ready init <project-name>`) to generate a new project in a target directory.

FR-2. Generation uses a two-stage approach:
- Stage 1: fetch the upstream base template (fastapi/full-stack-fastapi-template) at the exact commit pinned in `manifest.json`.
- Stage 2: apply the dev-ready overlay on top: Canonical Content, selected Agent Target Pointer Stubs and configuration, MCP server configuration, and design-doc templates.

FR-3. The CLI prompts interactively for project name, and which optional overlay components to include. A non-interactive mode (`--yes` with defaults, flags for each choice) must exist for CI and scripted use.

FR-4. All upstream content is fetched at a pinned commit recorded in `manifest.json`. The CLI never fetches "latest" at generation time.

FR-5. The generated project must work immediately: dependencies resolvable, containers buildable, health check endpoint reachable, without manual fixes.

FR-6. The CLI reports clearly what was generated and what the user should do next.

## Functional Requirements — v0.2

FR-7. Prune upstream repo-maintenance files. The generated project must not contain files that only make sense inside the upstream template's own repository. A `prune` list in `manifest.json` (separate from `exclude` — see ADR-006) removes them at generation time. Initial list, audited against a real v0.1.3 generation:

- `.github/workflows/` repo-maintenance workflows: `deploy-production.yml`, `deploy-staging.yml` (reference upstream's own servers and secrets), `issue-manager.yml`, `labeler.yml`, `add-to-project.yml`, `latest-changes.yml`, `smokeshow.yml`, `detect-conflicts.yml`, `zizmor.yml`, `guard-dependencies.yml`, and the `.github/labeler.yml` config. KEEP the workflows that test the user's own app: `test-backend.yml`, `test-docker-compose.yml`, `playwright.yml`, `pre-commit.yml`, plus `dependabot.yml`.
- `CONTRIBUTING.md` (contributing to the template, not to the user's project)
- `release-notes.md` (upstream's release history)
- `img/` (upstream README screenshots and GitHub social-preview images, ~7 files)
- `scripts/add_latest_release_date.py` (upstream release tooling; other scripts stay)
- `hooks/post_gen_project.py` (dead file: cookiecutter-era hook, not referenced by the template's `copier.yml` — its `_tasks` only runs `.copier/update_dotenv.py`)
- `README.md` (upstream's template README; replaced per FR-8)

KEEP even though they look upstream-ish: `development.md`, `deployment.md` (genuinely useful to the user), `.pre-commit-config.yaml`, root `package.json`/`bun.lock` (bun workspace wiring), `.gitattributes`, `.agents/` and `.claude/` skill content not already excluded. (Amended 2026-07-17: `.copier/` and `.copier-answers.yml` were originally kept to enable `copier update`, but are now pruned by `generate` (`e096aaf`) — Copier metadata does not belong in an end-user project. The upgrade path is `dev-ready upgrade` (FR-22), not `copier update`. See the ADR-005 amendment.)

FR-8. Project README. Because FR-7 prunes the upstream `README.md`, the overlay writes a project-specific `README.md` (templated with the project name, brief stack summary, and the same commands as canonical `AGENTS.md`). The overlay's no-overwrite rule is preserved: prune removes the upstream file first, so there is no collision.

FR-9. Leak guard in verify. `verify_project` gains a forbidden-paths check (at minimum `.git`, `copier.yml`, `copier.yaml`) so a future upstream or Copier behavior change that reintroduces the v0.1.3 `.git`/`copier.yml` leak fails generation loudly — in CI at bump time, before it ever reaches users.

FR-10. Handoff Protocol overlay (optional component, alongside skills/mcp/docs). Generated projects can include a multi-agent handoff scaffold: a `docs/handoffs/` directory with role and handoff templates (tech lead -> senior engineer -> junior engineer -> QA/Security/SRE, see ADR-007), and an agent-roles section in canonical `AGENTS.md`. Selected like the other components (`--no-handoff`; the original `--no-agents` name is the deprecated alias described by FR-26). **Retired in v0.9 by FR-35 ([ADR-020](decisions/adr-020-handoff-protocol-not-generated.md))** — the scaffold is no longer generated. ADR-007 remains in force for this repository's own process.

## Functional Requirements — v0.3 and beyond

Agreed 2026-07-17. Full detail, rationale, and per-version grouping live in
[version-plan.md](version-plan.md); summary index here for numbering continuity:

- FR-11 (v0.3, shipped). Generation stamp: `.dev-ready.json` written into every generated project (version, components + selected items, pins) — the prerequisite for FR-21/FR-22.
- FR-12 (v0.3, shipped). Codebase-memory MCP item in the `mcp` component: `.mcp.json` entry launching `uvx codebase-memory-mcp==<pin>` — zero manual install, pin in manifest (pinned-dependency mode, ADR-008).
- FR-13 (v0.3, shipped). react-doctor item in the `skills` component: pinned devDependency + package script in the generated frontend `package.json`, plus an original wrapper skill; no source redistribution (ADR-008).
- FR-14 (v0.3, shipped). Item-level component selection (ADR-010): users pick individual items inside `skills` and `mcp` (e.g. react-doctor without code-memory) — second-level interactive multi-select (all on by default) plus `--skills <ids|all|none>` / `--mcp <ids|all|none>` list flags; item catalog lives in `manifest.json` as data.
- FR-15 (v0.4, shipped). Manifest `vendored` section: provenance pins (repo, commit, license, paths) for all vendored content.
- FR-16 (v0.4, shipped). Vendored snapshot sync tooling + CI byte-equality drift guard + monthly vendored-bump workflow.
- FR-17 (v0.4, shipped). MIT-wave vendoring (curated subsets, each a catalog item): caveman, mattpocock/skills, cloudflare/security-audit-skill, awesome-design-md.
- FR-18 (v0.4, shipped). THIRD_PARTY_NOTICES ↔ manifest `vendored` sync check in CI.
- FR-19 (v0.5, shipped). anthropics/skills Apache 2.0 example subset with NOTICE propagation (document-processing skills permanently excluded).
- FR-20 (v0.5, shipped). Karpathy guardrails content in generated canonical `AGENTS.md` — MIT per the upstream README declaration (no standalone LICENSE file; pinned commit preserves the grant), with attribution in NOTICES.
- FR-21 (v0.6, shipped). `dev-ready check`: read-only validation of an existing project against its stamp and the CLI's manifest.
- FR-22 (v0.6, shipped). `dev-ready upgrade`: re-apply overlay-managed whole files only (per the stamp's item selection); refuses pre-v3 stamps, never touches upstream application code, and never silently overwrites user edits.
- FR-23 (v0.7, shipped). Configurable Handoff Protocol: generated projects carry one default role topology in `docs/handoffs/protocol.yaml`. Seven stable role ids (`ceo`, `tech_lead`, `senior_engineer`, `junior_engineer`, `qa_reviewer`, `security_reviewer`, and `sre_reviewer`) own responsibilities, prohibitions, handoff order, and nullable/editable model assignments as data. The Protocol Configuration is authoritative at runtime; generated prose does not duplicate editable titles or models. With the Spec Loop it uses durable specs, per-ticket dispatch, one-ticket execution, and `03`–`06` gates; active numeric phase directories are ignored while the reusable scaffold and protocol remain durable. Multiple presets and plugin mechanics remain deferred. **Retired in v0.9 by FR-35 ([ADR-020](decisions/adr-020-handoff-protocol-not-generated.md))** — generated projects no longer carry a Protocol Configuration. This repository's own process, ADR-007 as scoped to internal practice, and ADR-013 are unaffected.
- FR-24 (v0.7, shipped). AI-invokable generation skill: the original `skills/dev-ready/SKILL.md` teaches agents to drive the stable `dev-ready init` machine interface safely. It is directly installable from this repository through the open Agent Skills ecosystem, remains outside the generated overlay and manifest catalog, and requires no Claude plugin metadata.
- FR-25 — withdrawn 2026-07-26 before implementation; the number is permanently retired and never reused. CLI internationalization was specced for v0.8 and cut once the underlying need was identified as discovery rather than runtime comprehension. The rationale is recorded in roadmap candidate D-3 in [version-plan.md](version-plan.md); the language rule that survived it is [ADR-016](decisions/adr-016-language-boundary.md).
- FR-26 (v0.8, shipped). Multi-agent render targets (ADR-015): Canonical Content — skills at the open Agent Skills standard directory and rules at `AGENTS.md` — is always written, so standard-compliant harnesses need no declared target. Users additionally select Agent Targets (`--agents`) for agents using uniquely-named directories; each receives Pointer Stubs, never symlinks and never content copies. The agent map is manifest data. The `agents` component is renamed `handoff` (`--no-agents` deprecated one version), the stamp advances to version 4 recording Agent Targets, and `upgrade` migrates existing projects through the ADR-014 obsolete-file rules. Spec: [fr-26-agent-targets.md](specs/v0.8/fr-26-agent-targets.md).
- FR-27 (v1.0, reserved). Post-v0.6 roadmap decision D-5 in [version-plan.md](version-plan.md); the full entry lands here when v1.0 development starts.
- FR-28 (v0.7, shipped). Spec Loop bundle (ADR-012): one explicit catalog selection, `spec-loop`, materializes the complete pinned dependency closure of the four advertised missing steps from mattpocock/skills, automatically resolves the existing `tdd`, `diagnosing-bugs`, and `code-review` items, and supplies the role-neutral tracker/domain configuration those upstream skills expect. It conditionally layers the loop into the Handoff Protocol, brings the existing `architecture.md` template under the `docs` component contract, and fills the skills catalog to 10/10.
- FR-29 (v0.7, shipped). Progress reporting for `init`: four typed stages on stderr (TTY spinner, plain non-TTY), no new dependencies, and an optional progress callback from `cli` into `generate()`. Finalization uses a same-filesystem atomic rename so a reported failure never exposes a partial target.
- FR-30 (v0.9, planned). Category-first selection ([ADR-017](decisions/adr-017-category-first-selection.md)): Category (Dev, Security, Quality, Design, Token Optimize) replaces Component as the user-facing axis, Component survives only as the internal write-location grouping, and the stamp advances to version 5. Dev is a mandatory single-select; the rest are multi-select. `mcp-config` becomes infrastructure rather than a selectable item, and the design-doc templates become individually selectable. Spec: [fr-30-category-first-selection.md](specs/v0.9/fr-30-category-first-selection.md).
- FR-31 (v0.9, planned). Spec Loop always generated; Default Set replaces the catalog cap ([ADR-018](decisions/adr-018-spec-loop-spine-and-default-set.md)): the loop becomes the single option of the mandatory Dev Category, gains the never-vendored `implement` step and an opt-in `setup-all` Enhancement, and the ten-item cap is retired in favour of a limit on what a user receives by default. `project-orientation` is removed from the product. Spec: [fr-31-spec-loop-default-set.md](specs/v0.9/fr-31-spec-loop-default-set.md).
- FR-35 (v0.9, planned). Retire the Handoff Protocol from generated projects ([ADR-020](decisions/adr-020-handoff-protocol-not-generated.md)): the scaffold, its Component, its flag, and the v0.8 deprecated alias are removed from the overlay, retiring FR-10 and FR-23 as product surface. ADR-007 is scoped to this repository's internal process rather than superseded; ADR-013 and `docs/handoff/<version>/` are unaffected. Existing projects retire the files through the ADR-014 obsolete-file rules with edited files preserved. Spec: [fr-35-retire-generated-handoff-protocol.md](specs/v0.9/fr-35-retire-generated-handoff-protocol.md).
- FR-32 (v0.10, planned). Mount Points ([ADR-018](decisions/adr-018-spec-loop-spine-and-default-set.md)): every Enhancement declares the Spec Loop skill its guidance is injected into, as a third catalog effect kind applied at generation time into a delimited, regenerable block.
- FR-33 (v0.10, planned). Agent Target Map ([ADR-019](decisions/adr-019-agent-target-map-drift-guard.md)): the 56 agents with unique project-level skill directories are derived from the reference installer's machine-readable list at a pinned commit and held to it by a CI drift check; `rules_file` and `mcp_file` stay hand-declared.
- FR-34 (v0.10, planned). Interview-driven generation skill: FR-24's skill is rewritten for FR-30's contract as an interview — the agent questions the user about what they are building, maps the answers to Categories and items, then composes the command. Distribution is unchanged (this repository, outside the generated overlay).

## Non-functional Requirements

NFR-1. Reproducibility: two runs of the same dev-ready version produce identical output (modulo user inputs).

NFR-2. Maintainability: designed for a solo maintainer. Upstream tracking is automated (weekly CI bump PR); no fork of upstream is maintained.

NFR-3. Distribution: installable and runnable via `uvx` with zero prior setup beyond uv itself. Python >= 3.12.

NFR-4. Offline behavior: fail fast with a clear message when the network is unavailable; never generate a partial project.

NFR-5. Cross-platform: macOS, Linux, Windows.

## Out of Scope (current phase)

- Web UI companion (deferred, see roadmap)
- Support for base templates other than fastapi/full-stack-fastapi-template

## Future Roadmap

1. v0.1: single template, interactive init, pinned manifest, three CI workflows (upstream bump, PR validation, release). DONE (v0.1.4).
2. v0.2: prune list (FR-7), project README (FR-8), verify leak guard (FR-9), agent-team overlay (FR-10). DONE (v0.2.2).
3. v0.3: pinned tool integrations + selection — generation stamp (FR-11), codebase-memory MCP (FR-12), react-doctor (FR-13), item-level selection (FR-14). See [version-plan.md](version-plan.md). DONE (v0.3.0).
4. v0.4: vendoring infrastructure + MIT wave (FR-15..FR-18). DONE (v0.4.0).
5. v0.5: Apache wave + karpathy guardrails (FR-19, FR-20). DONE (v0.5.0).
6. v0.6: lifecycle commands — `check` / `upgrade` (FR-21, FR-22). DONE (v0.6.0).
7. v0.7: Handoff Protocol config (FR-23), Spec Loop bundle (FR-28), generate skill (FR-24), progress reporting (FR-29). DONE — v0.7.0 tagged and published to PyPI.
8. v0.8: multi-agent render targets (FR-26). CLI i18n (FR-25) was withdrawn 2026-07-26 (D-3 rejected); Traditional Chinese is served by repository documentation instead. DONE — v0.8.0 tagged and published to PyPI.
9. v0.9: selection model — Category-first selection (FR-30), Spec Loop always generated + Default Set (FR-31), retire the generated Handoff Protocol (FR-35). PLANNED.
10. v0.10: assembly and reach — Mount Points (FR-32), Agent Target Map (FR-33), interview-driven generation skill (FR-34). PLANNED.
11. v1.0: second template — Next.js (FR-27, gated on the defined real-users checklist); Web UI decision revisited.

## Pre-start Checklist (carried from planning; closed out 2026-07-24)

- [x] Package name availability on PyPI (`dev-ready`) — confirmed in practice: v0.1.4 through v0.7.0 published under this name.
- [x] License verification for redistributing upstream snapshots — resolved by ADR-008 (integration modes), ADR-009 (manifest `vendored` provenance), and the THIRD_PARTY_NOTICES machinery (FR-18/FR-19).
- [x] Confirm upstream health check endpoint used for post-generation verification — in continuous use by CI's generate-and-verify job (health-check poll, ADR-002).
