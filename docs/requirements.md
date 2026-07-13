# Requirements — dev-ready

Status: Draft v0.1 (2026-07-13)

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

1. v0.1: single template, interactive init, pinned manifest, three CI workflows (upstream bump, PR validation, release).
2. v0.2: overlay component selection matrix; non-interactive mode hardening.
3. v0.x: additional base templates; possible Web UI companion (decision deferred).

## Pre-start Checklist (carried from planning)

- [ ] Package name availability on PyPI (`dev-ready`)
- [ ] License verification for redistributing upstream snapshots (upstream is MIT — confirm attribution requirements)
- [ ] Confirm upstream health check endpoint used for post-generation verification
