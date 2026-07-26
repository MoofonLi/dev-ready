# AGENTS.md — dev-ready

Rules for all AI agents working in this repo, whichever model or tool fills each role.
This file is the single source of truth for agent rules; `CLAUDE.md` imports it for Claude Code.

## What this project is

dev-ready is a Python CLI (`uvx dev-ready`) that scaffolds FastAPI projects pre-configured for AI-assisted development: base template from fastapi/full-stack-fastapi-template at a manifest-pinned commit, plus Canonical Content for coding agents, optional Agent Target Pointer Stubs, MCP config, and design docs.

Current phase: v0.8 is released. FR-26 is implemented, `v0.8.0` is tagged and published to PyPI, and Phase 4 documentation, review, release, and distribution verification are complete. Roadmap in `docs/version-plan.md`; per-version plans in `docs/handoff/<version>/<version>-plan.md`. Domain glossary: `CONTEXT.md`.

The v0.8 release surface is fixed: Canonical Content is always written to
`.agents/skills/` and `AGENTS.md`; manifest-declared Agent Targets render Pointer
Stubs selected by `--agents`; the Handoff Protocol component is named `handoff`
with `--no-agents` retained as a deprecated alias for one version; stamp version
4 records Agent Targets; and upgrades from v0.7 infer Claude Code, preserve
edited obsolete files, and migrate untouched content transactionally.

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
- English everywhere dev-ready speaks or generates — CLI output, generated project content, source, tests, and every document under `docs/` (ADR-016). There is no localized runtime: never add `--lang`, `DEV_READY_LANG`, locale detection, or a message catalog.
- `README.zh-TW.md` is the single exception and the only Chinese file in the repo. It is a **focused overview, not a translation of `README.md`**: update it when the product facts it states change (what dev-ready is, what it produces, requirements, how to install and run it once, the lifecycle commands' guarantees). Do **not** sync it for new flags, exit codes, development setup, or English wording changes — it deliberately carries none of those and points to the English README instead. Adding a Chinese file anywhere else requires amending ADR-016.

## Multi-agent workflow (ADR-007; paths ADR-011; process v2 ADR-013)

Roles are fixed; the model or tool filling each role is not. Agents communicate ONLY through on-disk documents — never assume chat context from another agent. Two document classes: **specs** in `docs/specs/<version>/` (durable, committed) and **phase working files** in `docs/handoff/<version>/phase-N/` (gitignored, never committed; code is committed normally).

| Role | Does | Never does |
|---|---|---|
| CEO | Sets goals, accepts specs, approves ticket breakdowns, applies diffs + commits, merges | — |
| Tech Lead | Decisions, version plans, drives the Planning layer | Write or edit code |
| Senior Engineer | Dispatch layer (ticket breakdown), code review vs spec (logic + architecture), fixes escalated hard bugs | Write code the Junior can handle |
| Junior Engineer | Execution layer: one ticket at a time, TDD, inside the ticket's declared file footprint; execution report per phase | Run state-changing git (commit/branch/push — only the CEO commits, after reviews); work outside the ticket footprint; keep grinding on a hard bug (STOP, log it in `reports/problems.md`, move to next unblocked ticket) |
| Reviewer (QA / Security / SRE) | Three review passes per `.agents/skills/review/references/{qa,security,sre}.md` | Modify code; commit |

The CEO is Moofon (human). The other roles are filled by AI agents, assigned per task and swappable — no model name is binding anywhere in this repo.

### The four-layer phase loop (ADR-013)

Each phase from the version plan runs through four layers. Steps are named by their process skill in `.agents/skills/` — agents that support skill invocation trigger them directly; any other agent follows the SKILL.md as written instructions:

1. **Planning** (Tech Lead / Senior): `grill-with-docs` (interrogate requirements against the codebase and docs) → `to-spec` → a spec at `docs/specs/<version>/fr-NN-<slug>.md`, accepted by the CEO. The spec is the durable record code is reviewed against — it replaces the old `01-plan.md`.
2. **Dispatch** (Senior): `to-tickets` → tracer-bullet tickets in `docs/handoff/<version>/phase-N/tickets/`, each declaring blocked-by edges, a file footprint, and a `parallel-safe` marker. Replaces the old `02-implementation.md`.
3. **Execution** (Junior): `implement` (+ `tdd`, `code-review`, `diagnosing-bugs` within bounds) on one frontier ticket at a time. **Sequential by default**; tickets marked `parallel-safe: yes` may run in parallel, each Junior in its own git worktree, delivering a diff the CEO applies and commits in order.
4. **Verification** (Senior + Reviewer): `03-review.md` (Senior, vs the spec) → `04-qa-review.md` / `05-security-review.md` / `06-sre-review.md` gates (+ `07-release.md` on release phases only — the one scoped git-authority exemption). Fail → back to the Junior with a new red test.

Phase working files: `tickets/`, `03`–`06` (+ `07` release phases only); Junior outputs in `reports/`. Filenames name the role/step, never the model.

## Process skills

Repeatable workflows live in `.agents/skills/` (open Agent Skills format; `.claude/skills/` holds pointer stubs for Claude Code discovery). The set is curated to the four-layer loop — do not add skills outside it without a decision:

- Version level: `planning` (cut a version into phases → `docs/handoff/<version>/<version>-plan.md`), `release` (bump, verify, commit, tag, PyPI), `handoff` (generate a phase's gate docs 03–07 + reports scaffold)
- Planning layer: `grill-with-docs` (drives `grilling` + `domain-modeling`), `to-spec`
- Dispatch layer: `to-tickets`
- Execution layer: `implement`, `tdd`, `code-review`, `diagnosing-bugs`, `resolving-merge-conflicts`
- Architecture hygiene: `codebase-design`, `improve-codebase-architecture`
- Verification layer: `review` (QA / Security / SRE passes)
