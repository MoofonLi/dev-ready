# Requirements — dev-ready

Status: Draft v0.1 (2026-07-13); v0.2 scope added (2026-07-16)

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

KEEP even though they look upstream-ish: `development.md`, `deployment.md` (genuinely useful to the user), `.pre-commit-config.yaml`, root `package.json`/`bun.lock` (bun workspace wiring), `.copier/` (enables `copier update`), `.gitattributes`, `.agents/` and `.claude/` skill content not already excluded.

FR-8. Project README. Because FR-7 prunes the upstream `README.md`, the overlay writes a project-specific `README.md` (templated with the project name, brief stack summary, and the same commands as CLAUDE.md). The overlay's no-overwrite rule is preserved: prune removes the upstream file first, so there is no collision.

FR-9. Leak guard in verify. `verify_project` gains a forbidden-paths check (at minimum `.git`, `copier.yml`, `copier.yaml`) so a future upstream or Copier behavior change that reintroduces the v0.1.3 `.git`/`copier.yml` leak fails generation loudly — in CI at bump time, before it ever reaches users.

FR-10. Agent-team overlay (optional component, alongside skills/mcp/docs). Generated projects can include a multi-agent handoff scaffold: a `docs/handoffs/` directory with role and handoff templates (tech lead -> senior engineer -> junior engineer -> QA/Security/SRE, see ADR-007), and an agent-roles section in the generated CLAUDE.md. Selected like the other components (`--no-agents` flag, checkbox in the interactive flow).

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

1. v0.1: single template, interactive init, pinned manifest, three CI workflows (upstream bump, PR validation, release). DONE (v0.1.3 + pending v0.1.4 fixes: `.git`/`copier.yml` exclude, bump-PR token, CLAUDE.md template corrections).
2. v0.2: prune list (FR-7), project README (FR-8), verify leak guard (FR-9), agent-team overlay (FR-10). Component selection matrix shipped in v0.1 (skills/mcp/docs flags); v0.2 adds the fourth component. See docs/v0.2-plan.md for phases.
3. v0.x: `dev-ready check` / `dev-ready upgrade` commands; additional base templates; possible Web UI companion (decision deferred).

## Pre-start Checklist (carried from planning)

- [ ] Package name availability on PyPI (`dev-ready`)
- [ ] License verification for redistributing upstream snapshots (upstream is MIT — confirm attribution requirements)
- [ ] Confirm upstream health check endpoint used for post-generation verification
