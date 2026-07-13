# CLAUDE.md — dev-ready

Guidance for AI agents (Claude Code, GPT, IBM Bob) working in this repo.

## What this project is

dev-ready is a Python CLI (`uvx dev-ready`) that scaffolds FastAPI projects pre-configured for AI-assisted development: base template from fastapi/full-stack-fastapi-template at a manifest-pinned commit, plus an overlay of CLAUDE.md, Claude Code skills, MCP config, and design docs.

Current phase: bootstrap. Structure and docs exist; no business logic is implemented yet.

## Read before writing code

1. `docs/requirements.md` — what to build and what is out of scope
2. `docs/architecture.md` — ADRs, module boundaries, dependency rules (binding, not suggestions)
3. `docs/cli-spec.md` — command interface and exit codes

## Commands

- `uv sync --dev` — install
- `uv run dev-ready` — run CLI
- `uv run pytest` — tests
- `uv run ruff check .` — lint

## Hard rules

- Never fetch upstream "latest" at generation time; pins live in `src/dev_ready/manifest.json` only (ADR-002).
- Network calls only in `src/dev_ready/fetch/` (module boundary table in architecture.md).
- Generation must be all-or-nothing: no partial output directories on failure.
- Unit tests: no network, no filesystem outside tmp_path.
- Conventional Commits.

## Multi-agent workflow

Architect (design docs) -> Engineer (implement) -> QA (`.bob/qa.md`) -> Security (`.bob/security.md`) -> SRE/Release (`.bob/sre.md`). Reviewer expectations are defined in `.bob/`.
