# AGENTS.md — dev-ready

Rules for all AI agents working in this repo, whichever model or tool fills each role.
This file is the single source of truth for agent rules; `CLAUDE.md` imports it for Claude Code.

## What this project is

dev-ready is a Python CLI (`uvx dev-ready`) that scaffolds FastAPI projects pre-configured for AI-assisted development: base template from fastapi/full-stack-fastapi-template at a manifest-pinned commit, plus Canonical Content for coding agents, optional Agent Target Pointer Stubs and MCP configuration, and design docs.

Current phase: v0.11 is released (`v0.11.0` — see the v0.11 overview). It
shipped `setup-project` (FR-39), the full Design Reference set (FR-40), MIT
notice propagation (FR-41), Engineering Flow selection and the interactive
rework (FR-42), corrected Flow Chain guidance (FR-43), CLI presentation
(FR-44), and Claude/Codex plugin distribution (FR-45) — governed by ADR-024,
ADR-026, and ADR-027. The stamp stayed at version 5. v0.12 (FR-46 Skill Links
under ADR-028, FR-47 `superpowers`) and v0.13 (FR-48
`addyosmani/agent-skills`, FR-49 Token Optimize additions) follow. v1.0 remains
gated on the real-users evidence defined in `docs/version-plan.md`, which the
2026-08-09 amendment narrowed to Branch A alone. Per-version plans live in
`docs/handoff/<version>/<version>-plan.md`; the domain glossary is `CONTEXT.md`.

**Process note:** v0.9 stopped *generating* the Handoff Protocol into user projects (ADR-020), and ADR-021 retires it here too — this repo now develops on the Spec Loop and nothing else. See "How this repo is developed" below.

The v0.11 release surface is fixed: the development method is an Engineering
Flow, asked first and named `mattpocock`; `setup-project` is unconditional
infrastructure at the head of every chain; all 74 Design References are
ordinary catalog items; MIT notices travel with the copied skills; the
repository root is the Claude and Codex plugin; and a flag answers only its
own question. The stamp stays at version 5 — nothing in v0.11 added, removed,
or re-typed a recorded field. Pointer Stubs remain the delivery mechanism in
shipped code; ADR-028 retires them in v0.12 in favour of one Skill Link per
skill, with no copy mode and no new stamp field. ADR-025, which chose between
two delivery modes, is superseded in full and was never implemented.

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
- English everywhere dev-ready authors, speaks, or generates — CLI output, composed project content, source, tests, and every document under `docs/` (ADR-016). Byte-identical vendored third-party snapshots retain their upstream language because translating them would break provenance; this is not a localized surface. There is no localized runtime: never add `--lang`, `DEV_READY_LANG`, locale detection, or a message catalog.
- `README.zh-TW.md` is the single exception and the only Chinese file authored by this repo. It is a **focused overview, not a translation of `README.md`**: update it when the product facts it states change (what dev-ready is, what it produces, requirements, how to install and run it once, the lifecycle commands' guarantees). Do **not** sync it for new flags, exit codes, development setup, or English wording changes — it deliberately carries none of those and points to the English README instead. Adding authored Chinese anywhere else requires amending ADR-016.

## How this repo is developed (ADR-021; paths ADR-011)

Development runs the **Spec Loop** — four steps, nothing more:

```
grill-with-docs  →  to-spec  →  to-tickets  →  implement
   (interrogate)     (decide)    (dispatch)    (build + review)
```

Steps are named by their process skill in `.agents/skills/` — agents that support skill invocation trigger them directly; any other agent follows the SKILL.md as written instructions.

1. **`grill-with-docs`** — interrogate the phase's scope against `docs/requirements.md`, the version plan, and the binding ADRs. Anything settled that outlives the phase gets written down (a new ADR, a `CONTEXT.md` term).
2. **`to-spec`** — a spec at `docs/specs/<version>/fr-NN-<slug>.md`. **Durable and committed**: it is the only record of the phase that survives it, and what the code is reviewed against. Moofon accepts it before the next step.
3. **`to-tickets`** — tracer-bullet tickets at `docs/handoff/<version>/phase-N/tickets/<NN>-<slug>.md`, each declaring blocked-by edges, a file footprint, a `parallel-safe` marker, and a Conventional Commit message. Gitignored working files. A ticket carries its own standing-rules header, so one ticket file is enough to run it cold.
4. **`implement`** — one frontier ticket at a time, TDD, inside the declared footprint, ending with a `code-review` pass. **Review lives inside this step**; there are no separate gate documents.

**Sequential by default.** Tickets marked `parallel-safe: yes` may run in parallel, each session in its own git worktree, delivering a diff Moofon applies in order.

**No phase document set is generated** (ADR-021): no `03`–`07` briefs, no `reports/`, no execution report, no `problems.md`. A hard bug means STOP and report it in the session — don't grind.

### Roles

Three hats, worn rather than assigned — one session may wear all three in sequence, and no role binds to a model or tool:

| Hat | Does |
|---|---|
| Tech Lead | Grilling, decisions/ADRs, version plans, specs, ticket breakdown |
| Engineer | Implements one ticket at a time, TDD, inside the ticket's footprint |
| Reviewer | The `code-review` pass at the end of a ticket — Standards axis + Spec axis |

Moofon (human) sets goals, accepts specs, approves ticket breakdowns, and is the only one who authorizes git.

### Git authority

**No agent runs state-changing git without Moofon's explicit permission for that specific action, asked for at the moment it is due** — no `commit`, `push`, `branch`, `merge`, `reset`. Permission for one action is not permission for the next. Read-only git (`status`, `diff`, `log`) is always fine. Leave work in the working tree and say what is ready to commit, with the Conventional Commit message you'd use. Releases are no exception (ADR-021 removed the old `07-release` git exemption).

## Process skills

Repeatable workflows live in `.agents/skills/` (open Agent Skills format; `.claude/skills/` holds pointer stubs for Claude Code discovery). The set is curated to the Spec Loop — do not add skills outside it without a decision:

- The loop: `grill-with-docs` (drives `grilling` + `domain-modeling`) → `to-spec` → `to-tickets` → `implement`
- Inside `implement`: `tdd`, `code-review`, `diagnosing-bugs`, `resolving-merge-conflicts`
- Version level: `planning` (cut a version into phases → `docs/handoff/<version>/<version>-plan.md`), `release` (bump, verify, commit, tag, PyPI)
- Architecture hygiene: `codebase-design`, `improve-codebase-architecture`
