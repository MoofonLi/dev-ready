# CLAUDE.md — dev-ready

Guidance for AI agents (Claude, Gemini/Antigravity, IBM Bob) working in this repo.

## What this project is

dev-ready is a Python CLI (`uvx dev-ready`) that scaffolds FastAPI projects pre-configured for AI-assisted development: base template from fastapi/full-stack-fastapi-template at a manifest-pinned commit, plus an overlay of CLAUDE.md, Claude Code skills, MCP config, and design docs.

Current phase: v0.1 complete (v0.1.4 fixes pending release); v0.2 in progress — see `docs/v0.2-plan.md` and ADR-006/ADR-007 in `docs/architecture.md`.

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

## Multi-agent workflow (ADR-007)

Roles are fixed. Agents communicate ONLY through on-disk handoff documents in `handoff/<version>/phaseN/` (gitignored — handoffs are working files, never committed; code is committed normally) — never assume chat context from another agent.

| Role | Agent | Does | Never does |
|---|---|---|---|
| CEO | Moofon | Sets goals, approves plans, merges | — |
| Tech Lead | Claude Fable 5 (Cowork) | Decisions, plans, handoff docs | Write or edit code |
| Senior Engineer | Claude Opus 4.8 | Task breakdown for the junior, code review (logic + architecture), fixes escalated hard bugs | Write code the junior can handle |
| Junior Engineer | Gemini 3.1 Pro (Antigravity) | Implements tasks in the working tree — writes most of the code; execution report per phase | Run state-changing git (commit/branch/push — only the CEO commits, after reviews); keep grinding on a hard bug (STOP, log it in `reports/problems.md`, move to next task) |
| QA / Security / SRE | IBM Bob | Reviews per `.bob/qa.md`, `.bob/security.md`, `.bob/sre.md` | — |

Handoff files per phase: `01-opus-plan.md`, `02-gemini-implementation.md`, `03-opus-review.md`, `04-bob-qa.md`, `05-bob-security.md`, `06-bob-sre.md`; junior outputs in `reports/`.
