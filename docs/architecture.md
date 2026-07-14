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
|                   |     |    (tarball, no git |     |    docs)         |
|                   |     |    history)         |     |                  |
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

### ADR-001: Two-stage generation, no upstream fork

- Status: Accepted
- Context: We layer AI tooling on top of fastapi/full-stack-fastapi-template. Forking it creates a permanent merge liability against a fast-moving upstream.
- Decision: Never fork. Fetch upstream as a snapshot at a pinned commit, then apply our overlay files on top.
- Consequences: Upstream stays independent; our value-add is isolated in the overlay; upstream changes are absorbed via a controlled bump process (ADR-002).

### ADR-002: Manifest-pinned upstream with CI-gated bumps

- Status: Accepted
- Context: A "fetch latest at generation time" design was evaluated and rejected — it ships untested template/overlay combinations and transfers maintenance burden to users.
- Decision: `manifest.json` pins the exact upstream commit, acting as a lockfile. A weekly GitHub Actions workflow opens a PR bumping the pin; CI regenerates a project and verifies it before merge.
- Consequences: Every released version generates a tested combination. Maintenance is a scheduled, automated review task rather than user-facing breakage. The manifest ships inside the package (`src/dev_ready/manifest.json`) so an installed CLI always carries the pin it was released with.

### ADR-003: Distribution via uvx (Python), superseding npx plan

- Status: Accepted (2026-07-13)
- Context: The original plan was a Node CLI (`npx create-ai-stack`, degit + @clack/prompts). The project has since moved to a Python implementation named dev-ready, matching the maintainer's primary stack (Python) and the target audience (FastAPI developers who already have uv).
- Decision: Pure Python CLI, `uvx dev-ready`. Node-specific choices are replaced: degit -> GitHub tarball download at pinned commit; @clack/prompts -> questionary (or equivalent); npm publish -> PyPI publish.
- Consequences: Single-language repo; one less runtime assumption for the target audience. The npx name `create-ai-stack` is abandoned.

### ADR-004: Interactive prompts with a non-interactive escape hatch

- Status: Accepted
- Context: Good first-run UX needs prompts; CI and scripted use cannot answer prompts.
- Decision: Interactive by default; `--yes` plus explicit flags cover every prompt.
- Consequences: All prompt logic must route through a single answers model so both paths share one code path.

## Module Boundary

| Module | Responsibility | Must not |
|---|---|---|
| `cli` | Argument parsing, command wiring, exit codes | contain generation logic |
| `prompts` | Interactive/non-interactive collection of user answers into one model | perform I/O other than terminal |
| `fetch` | Download and verify upstream snapshot at the manifest-pinned commit | know about overlay content |
| `overlay` | Apply dev-ready files onto the fetched base; templating of names/values | fetch anything from the network |
| `manifest` | Load/validate manifest.json; single source of truth for pins | be bypassed by other modules |
| `report` | Post-generation summary and next steps | mutate the generated project |
| `verify` | Cheap, offline, structural post-generation checks on the staging dir | perform network I/O, write to the project, or run the heavy FR-5 checks (docker build, health endpoint — those run in CI, see Deployment Architecture) |

## Dependency Rules

- Direction: `cli` -> `prompts`/`manifest`/`fetch`/`overlay`/`report`/`verify`. Lower modules never import `cli`.
- `fetch`, `overlay`, and `verify` are independent of each other; only `generate` (called only by `cli`) sequences them.
- Runtime dependencies are kept minimal (target: questionary, httpx or stdlib urllib, rich optional). Every new dependency requires a note here.
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
