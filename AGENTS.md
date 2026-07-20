# AGENTS.md — dev-ready

Rules for all AI agents working in this repo, whichever model or tool fills each role.
This file is the single source of truth for agent rules; `CLAUDE.md` imports it for Claude Code.

## What this project is

dev-ready is a Python CLI (`uvx dev-ready`) that scaffolds FastAPI projects pre-configured for AI-assisted development: base template from fastapi/full-stack-fastapi-template at a manifest-pinned commit, plus an overlay of CLAUDE.md, Claude Code skills, MCP config, and design docs.

Current phase: v0.3 in progress (phase 1 completed) — roadmap in `docs/version-plan.md`; per-version plans in `docs/handoff/<version>/<version>-plan.md`.

## Read before writing code

1. `docs/requirements.md` — what to build and what is out of scope
2. `docs/architecture.md` — system overview, module boundaries, dependency rules (binding, not suggestions)
3. `docs/decisions/` — ADRs, one file each (binding, valid across phases)
4. `docs/cli-spec.md` — command interface and exit codes

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

## Multi-agent workflow (ADR-007, paths amended by ADR-011)

Roles are fixed; the model or tool filling each role is not. Agents communicate ONLY through on-disk handoff documents in `docs/handoff/<version>/phase-N/` (gitignored — handoffs are working files, never committed; code is committed normally) — never assume chat context from another agent.

| Role | Does | Never does |
|---|---|---|
| CEO | Sets goals, approves plans, merges | — |
| Tech Lead | Decisions, plans, handoff docs | Write or edit code |
| Senior Engineer | Task breakdown for the Junior, code review (logic + architecture), fixes escalated hard bugs | Write code the Junior can handle |
| Junior Engineer | Implements tasks in the working tree — writes most of the code; execution report per phase | Run state-changing git (commit/branch/push — only the CEO commits, after reviews); keep grinding on a hard bug (STOP, log it in `reports/problems.md`, move to next task) |
| Reviewer (QA / Security / SRE) | Three review passes per `.agents/skills/review/references/{qa,security,sre}.md` | Modify code; commit |

The CEO is Moofon (human). The other roles are filled by AI agents, assigned per task and swappable — no model name is binding anywhere in this repo. The Reviewer role was previously run by IBM Bob but is not tied to it.

Handoff files per phase: `01-plan.md`, `02-implementation.md`, `03-review.md`, `04-qa-review.md`, `05-security-review.md`, `06-sre-review.md` (+ `07-release.md` for release phases only); Junior outputs in `reports/`. Filenames name the role/step, never the model — the number and role are what bind; any capable model may fill each role.

## Process skills

Repeatable workflows live in `.agents/skills/` (open Agent Skills format; `.claude/skills/` holds pointer stubs for Claude Code discovery):

- `.agents/skills/planning/` — how to cut a version into phases (produces `docs/handoff/<version>/<version>-plan.md`)
- `.agents/skills/handoff/` — how to generate the per-phase handoff document set
- `.agents/skills/release/` — how to ship a version (bump, verify, commit, tag, PyPI)
