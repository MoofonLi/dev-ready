# Requirements — dev-ready

Status: Draft v0.1 (2026-07-13); v0.2 scope added (2026-07-16); v0.3+ scope agreed (2026-07-17, see docs/version-plan.md)

## Problem Statement

Starting a production-grade FastAPI project that is ready for AI-assisted development requires assembling many pieces by hand: the base template, Claude Code configuration (CLAUDE.md, skills), MCP server setup, and design documentation. dev-ready is a CLI, run via `uvx dev-ready`, that scaffolds all of this in one command.

## Functional Requirements

FR-1. The user can run `uvx dev-ready` (or `uvx dev-ready init <project-name>`) to generate a new project in a target directory.

FR-2. Generation uses a two-stage approach:
- Stage 1: fetch the upstream base template (fastapi/full-stack-fastapi-template) at the exact commit pinned in `manifest.json`.
- Stage 2: apply the dev-ready overlay on top: CLAUDE.md, Claude Code skills, MCP server configuration, and design-doc templates.

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

FR-8. Project README. Because FR-7 prunes the upstream `README.md`, the overlay writes a project-specific `README.md` (templated with the project name, brief stack summary, and the same commands as CLAUDE.md). The overlay's no-overwrite rule is preserved: prune removes the upstream file first, so there is no collision.

FR-9. Leak guard in verify. `verify_project` gains a forbidden-paths check (at minimum `.git`, `copier.yml`, `copier.yaml`) so a future upstream or Copier behavior change that reintroduces the v0.1.3 `.git`/`copier.yml` leak fails generation loudly — in CI at bump time, before it ever reaches users.

FR-10. Agent-team overlay (optional component, alongside skills/mcp/docs). Generated projects can include a multi-agent handoff scaffold: a `docs/handoffs/` directory with role and handoff templates (tech lead -> senior engineer -> junior engineer -> QA/Security/SRE, see ADR-007), and an agent-roles section in the generated CLAUDE.md. Selected like the other components (`--no-agents` flag, checkbox in the interactive flow).

## Functional Requirements — v0.3 and beyond

Agreed 2026-07-17. Full detail, rationale, and per-version grouping live in
[version-plan.md](version-plan.md); summary index here for numbering continuity:

- FR-11 (v0.3). Generation stamp: `.dev-ready.json` written into every generated project (version, components + selected items, pins) — the prerequisite for FR-21/FR-22.
- FR-12 (v0.3). Codebase-memory MCP item in the `mcp` component: `.mcp.json` entry launching `uvx codebase-memory-mcp==<pin>` — zero manual install, pin in manifest (pinned-dependency mode, ADR-008).
- FR-13 (v0.3). react-doctor item in the `skills` component: pinned devDependency + package script in the generated frontend `package.json`, plus an original wrapper skill; no source redistribution (ADR-008).
- FR-14 (v0.3). Item-level component selection (ADR-010): users pick individual items inside `skills` and `mcp` (e.g. react-doctor without code-memory) — second-level interactive multi-select (all on by default) plus `--skills <ids|all|none>` / `--mcp <ids|all|none>` list flags; item catalog lives in `manifest.json` as data.
- FR-15 (v0.4). Manifest `vendored` section: provenance pins (repo, commit, license, paths) for all vendored content.
- FR-16 (v0.4). Vendored snapshot sync tooling + CI byte-equality drift guard + monthly vendored-bump workflow.
- FR-17 (v0.4). MIT-wave vendoring (curated subsets, each a catalog item): caveman, mattpocock/skills, cloudflare/security-audit-skill, awesome-design-md.
- FR-18 (v0.4). THIRD_PARTY_NOTICES ↔ manifest `vendored` sync check in CI.
- FR-19 (v0.5). anthropics/skills Apache 2.0 example subset with NOTICE propagation (document-processing skills permanently excluded).
- FR-20 (v0.5). Karpathy guardrails content in generated CLAUDE.md — MIT per the upstream README declaration (no standalone LICENSE file; pinned commit preserves the grant), with attribution in NOTICES.
- FR-21 (v0.6). `dev-ready check`: read-only validation of an existing project against its stamp and the CLI's manifest.
- FR-22 (v0.6). `dev-ready upgrade`: re-apply overlay-managed files only (per the stamp's item selection); never touches upstream application code; never silently overwrites user edits.

## Non-functional Requirements

NFR-1. Reproducibility: two runs of the same dev-ready version produce identical output (modulo user inputs).

NFR-2. Maintainability: designed for a solo maintainer. Upstream tracking is automated (weekly CI bump PR); no fork of upstream is maintained.

NFR-3. Distribution: installable and runnable via `uvx` with zero prior setup beyond uv itself. Python >= 3.12.

NFR-4. Offline behavior: fail fast with a clear message when the network is unavailable; never generate a partial project.

NFR-5. Cross-platform: macOS, Linux, Windows.

## Out of Scope (current phase)

- Web UI companion (deferred, see roadmap)
- Support for base templates other than fastapi/full-stack-fastapi-template
- Post-generation project upgrade/migration commands

## Future Roadmap

1. v0.1: single template, interactive init, pinned manifest, three CI workflows (upstream bump, PR validation, release). DONE (v0.1.4).
2. v0.2: prune list (FR-7), project README (FR-8), verify leak guard (FR-9), agent-team overlay (FR-10). DONE (v0.2.2).
3. v0.3: pinned tool integrations + selection — generation stamp (FR-11), codebase-memory MCP (FR-12), react-doctor (FR-13), item-level selection (FR-14). See [version-plan.md](version-plan.md).
4. v0.4: vendoring infrastructure + MIT wave (FR-15..FR-18).
5. v0.5: Apache wave + pending items (FR-19, FR-20).
6. v0.6: lifecycle commands — `check` / `upgrade` (FR-21, FR-22).
7. Beyond: additional base templates; possible Web UI companion (decisions deferred).

## Pre-start Checklist (carried from planning)

- [ ] Package name availability on PyPI (`dev-ready`)
- [ ] License verification for redistributing upstream snapshots (upstream is MIT — confirm attribution requirements)
- [ ] Confirm upstream health check endpoint used for post-generation verification
