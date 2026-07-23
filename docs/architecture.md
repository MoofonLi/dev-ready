# Architecture — dev-ready

Status: Draft v0.1 (2026-07-13)

## System Overview

dev-ready is a Python CLI distributed via PyPI and executed with `uvx dev-ready`. It generates FastAPI projects pre-configured for AI-assisted development using a two-stage pipeline:

```
uvx dev-ready init my-app
        |
        v
+-------------------+     +---------------------+     +------------------+
| 1. Prompt user    | --> | 2. Fetch upstream   | --> | 3. Apply overlay |
|    (questionary)  |     |    at pinned commit |     |    (CLAUDE.md,   |
|                   |     |    from manifest    |     |    skills, MCP,  |
|                   |     |    (Copier, no git  |     |    docs)         |
|                   |     |    history kept)    |     |                  |
+-------------------+     +---------------------+     +------------------+
                                                              |
                                                              v
                                                   +---------------------+
                                                   | 4. Post-gen checks  |
                                                   |    + next-steps     |
                                                   |    report           |
                                                   +---------------------+
```

## Architecture Decision Records

ADRs live in `docs/decisions/`, one file per decision (moved out of this file by ADR-011). They are binding across phases.

| ADR | Title | Status |
|---|---|---|
| [ADR-001](decisions/adr-001-two-stage-generation-no-fork.md) | Two-stage generation, no upstream fork | Accepted |
| [ADR-002](decisions/adr-002-manifest-pinned-upstream.md) | Manifest-pinned upstream with CI-gated bumps | Accepted |
| [ADR-003](decisions/adr-003-distribution-via-uvx.md) | Distribution via uvx (Python), superseding npx plan | Accepted (2026-07-13) |
| [ADR-004](decisions/adr-004-interactive-prompts-escape-hatch.md) | Interactive prompts with a non-interactive escape hatch | Accepted |
| [ADR-005](decisions/adr-005-consume-upstream-via-copier.md) | Consume upstream via Copier, superseding the tarball fetch (v0.1.3) | Accepted (2026-07-14), amends ADR-003 |
| [ADR-006](decisions/adr-006-manifest-prune-list.md) | Manifest-driven prune list, separate from exclude (v0.2) | Accepted (2026-07-16) |
| [ADR-007](decisions/adr-007-multi-agent-handoff-protocol.md) | Multi-agent development team and handoff protocol (v0.2) | Accepted (2026-07-16) |
| [ADR-008](decisions/adr-008-integration-modes-vendor-vs-pinned.md) | Two third-party integration modes — vendor vs pinned dependency (v0.3+) | Accepted (2026-07-17) |
| [ADR-009](decisions/adr-009-manifest-vendored-provenance.md) | Manifest `vendored` section with enforced provenance (v0.4) | Implemented |
| [ADR-010](decisions/adr-010-item-level-catalog-selection.md) | Item-level component selection with a data-driven catalog (v0.3) | Accepted (2026-07-17) |
| [ADR-011](decisions/adr-011-agent-config-restructure.md) | Standard agent-config layout: AGENTS.md, docs/decisions/, docs/handoff/, .agents/skills/ | Accepted (2026-07-20) |

## Module Boundary

| Module | Responsibility | Must not |
|---|---|---|
| `cli` | Argument parsing, command wiring, exit codes | contain generation logic |
| `prompts` | Interactive/non-interactive collection of user answers into one model | perform I/O other than terminal |
| `fetch` | Generate the upstream base via Copier at the manifest-pinned commit | know about overlay content |
| `overlay` | Apply dev-ready files onto the fetched base; templating of names/values | fetch anything from the network |
| `manifest` | Load/validate manifest.json; single source of truth for pins | be bypassed by other modules |
| `report` | Post-generation summary and next steps | mutate the generated project |
| `verify` | Cheap, offline, structural post-generation checks on the staging dir | perform network I/O, write to the project, or run the heavy FR-5 checks (docker build, health endpoint — those run in CI, see Deployment Architecture) |
| `stamp` | Load, parse, and validate `.dev-ready.json` project stamp | import `fetch` or perform network I/O |
| `check` | Offline, read-only structural drift inspection of generated project against manifest | import `fetch`, perform network I/O, or modify target project |
| `upgrade` | Offline re-apply of overlay-managed files onto an existing project; all-or-nothing | import `fetch`, perform network I/O, or touch upstream/non-overlay paths |


## Dependency Rules

- Direction: `cli` -> `prompts`/`manifest`/`fetch`/`overlay`/`report`/`verify`. Lower modules never import `cli`.
- `fetch`, `overlay`, and `verify` are independent of each other; only `generate` (called only by `cli`) sequences them.
- `upgrade` (called only by `cli`) sequences `overlay` and `stamp` offline, analogous to `generate`.
- Runtime dependencies are kept minimal (current: questionary, copier — see ADR-005; rich optional). Every new dependency requires a note here.
- No module reads `manifest.json` directly except `manifest`.
- `scripts/` (CI-only maintainer tooling, e.g. `scripts/bump_upstream.py`) is not part of the wheel and is not subject to the `fetch/`-only network-call rule above, which governs `src/dev_ready` only.

### questionary (added phase 4)

The repo's first runtime dependency, sanctioned by the "target: questionary" line above. It renders the interactive project-name text prompt, the skills/MCP/docs multi-select, and the yes/no confirmation (ADR-004). The stdlib (`input()`) is insufficient: it has no multi-select/checkbox primitive and no cross-platform line editing (arrow-key navigation, cancel-on-Ctrl-C-without-traceback) — reimplementing that is exactly the kind of undifferentiated work a dependency should absorb. Import is confined to `src/dev_ready/prompts/_questionary_asker.py`, and only via a function-local import inside `prompts/collect.py::_default_asker`, so the `--yes` flag path (which never calls into `prompts` at all) never triggers it.

## Coding Standards

- Python >= 3.12, fully type-annotated public functions.
- Lint/format: ruff (rules configured in pyproject.toml). Tests: pytest.
- No business logic in `__init__.py`. No network calls outside `fetch`.
- Errors surface as typed exceptions caught only at the `cli` layer, mapped to exit codes and human-readable messages.
- Conventional Commits for all commits (feeds release automation).

## Deployment Architecture

dev-ready itself deploys as a PyPI package — there is no server component.

- Release: tag -> GitHub Actions builds sdist/wheel -> publish to PyPI (trusted publishing).
- CI workflows: `ci.yml` (lint, test, generate-and-verify on PRs), `upstream-bump.yml` (weekly pin bump PR), `release.yml` (publish on tag).
- Generated projects carry their own deployment story from upstream (Docker Compose); dev-ready does not modify it in v0.1.

## Sequence Diagrams

### 1. `init` happy path

```
user            cli          prompts        generate      fetch/overlay/verify   target_dir
 |               |               |               |                  |                |
 |--init-------->|               |               |                  |                |
 |               |--collect----->|               |                  |                |
 |               |<--Answers-----|               |                  |                |
 |               |--confirm----->|               |                  |                |
 |               |<--True--------|               |                  |                |
 |               |--generate(answers, pin)------->|                  |                |
 |               |               |               |--fetch_snapshot->staging           |
 |               |               |               |--apply_overlay-->staging           |
 |               |               |               |--verify_project->staging (checked) |
 |               |               |               |--move(staging)---------------->target_dir
 |               |<--written[]---------------------|                  |                |
 |               |--render_report(answers, pin, written)                              |
 |<--summary-----|               |               |                  |                |
```

### 2. Failure path — network error during fetch

```
user            cli          generate         fetch          target_dir     temp staging
 |--init-------->|               |               |                |               |
 |               |--generate---->|               |                |               |
 |               |               |--fetch_snapshot(pin, staging)-->|               |
 |               |               |               X FetchError      |               |
 |               |               |<--raises FetchError-------------|               |
 |               |               |--finally: rmtree(staging_root)------------------>| (removed)
 |               |<--FetchError (propagates, target_dir never touched)              |
 |<--"error: ..." (exit 3)                                                          |
```

Same shape for an `OverlayError` (collision/missing asset) or a `VerificationError`
(missing upstream path) raised later in the same `try` block: whichever step fails,
the `finally` cleans up the staging root and `target_dir` is never created or moved
into — see `generate()`, all-or-nothing by construction.

### 3. `upstream-bump.yml` workflow

```
cron (Mon 06:00 UTC)      upstream-bump.yml         manifest.json      ci.yml (PR trigger)
       |                          |                        |                    |
       |--trigger---------------->|                        |                    |
       |                          |--resolve_latest_commit(repo, ref)           |
       |                          |   (GitHub API, unauthenticated)             |
       |                          |--update_manifest(commit, verified_at)------>| (rewritten)
       |                          |--git diff? changed ---->|                    |
       |                          |--open/update PR (chore/upstream-bump)------>|
       |                          |                        |                    |
       |                          |                        |--PR opened-------->|--generate-and-verify job
       |                          |                        |                    |   (docker compose build/up,
       |                          |                        |                    |    health-check poll)
       |                          |                        |                    |--pass -> mergeable
       |                          |                        |                    |--fail -> PR stays red
```

Verification of the bumped pin is not duplicated in `upstream-bump.yml` — it is
entirely CI's `generate-and-verify` job, triggered by the PR (ADR-002).
