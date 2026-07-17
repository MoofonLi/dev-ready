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
- Amended by ADR-005: the tarball download is replaced by Copier; the pinning, staging, and all-or-nothing guarantees are unchanged.

### ADR-004: Interactive prompts with a non-interactive escape hatch

- Status: Accepted
- Context: Good first-run UX needs prompts; CI and scripted use cannot answer prompts.
- Decision: Interactive by default; `--yes` plus explicit flags cover every prompt.
- Consequences: All prompt logic must route through a single answers model so both paths share one code path.

### ADR-005: Consume upstream via Copier, superseding the tarball fetch (v0.1.3)

- Status: Accepted (2026-07-14), amends ADR-003; amended (2026-07-17): `.copier/` and `.copier-answers.yml` are now removed from generated output by `generate` after the template's `_tasks` complete (`e096aaf`). The "enables `copier update`" consequence below is thereby retired — Copier metadata is generator machinery, not user-project content, and the supported upgrade path is `dev-ready upgrade` (FR-22, v0.6). This prune is code-level (not the manifest `prune` list) by necessity: `.copier-answers.yml` is produced by Copier itself after generation, so exclude/prune-at-fetch cannot remove it.
- Context: v0.1 downloaded the upstream as a raw tarball. Real-world use showed two gaps: (1) the template's own copier.yml questions (project_name, stack_name, secret_key, postgres_password, first_superuser_password) were never answered, so every generated project shipped the upstream "changethis" placeholder secrets and default project name in `.env`; (2) the template's `_exclude` list was ignored. Copier is the upstream template's officially supported consumption path.
- Decision: `fetch` runs `copier.run_copy(https://github.com/<repo>.git, staging, data=..., vcs_ref=<pinned commit>, defaults=True, unsafe=True, quiet=True)`. `generate` builds the template data from Answers, generating per-project secrets (`secrets.token_urlsafe`) that the template's `_tasks` write into the project's `.env`. Everything else — manifest pin, staging directory, all-or-nothing finalize, weekly bump CI — is unchanged. The tarball download/extract modules and their tests are removed.
- Consequences:
  - Generated projects get correct names and unique secrets. (Originally they also carried `.copier/.copier-answers.yml` to enable `copier update`; retired by the 2026-07-17 amendment above.)
  - New runtime dependency (copier, which brings jinja2/pydantic/plumbum) and a new host requirement: git must be installed (Copier clones; checked up front, mapped to FetchError/exit 3).
  - `unsafe=True` executes the template's `_tasks` (`.copier/update_dotenv.py`) at generation time. Accepted because the executed code is pinned to a CI-verified commit (ADR-002), never floating "latest".
  - Template question names are coupled to the pinned commit; an upstream rename is caught by the bump PR's generate-and-verify job, not by end users.
  - Unwanted template-repo metadata files (upstream `.github/` workflows, SECURITY.md, release-notes.md) are NOT excluded by the template's `_exclude`; a manifest-driven prune list remains future work (now ADR-006, v0.2).

### ADR-006: Manifest-driven prune list, separate from exclude (v0.2)

- Status: Accepted (2026-07-16)
- Context: A real generation (my-app, v0.1.3) contains upstream repo-maintenance files that are useless or misleading in a user project: upstream deploy/issue-triage workflows, CONTRIBUTING.md, release-notes.md, README screenshots (`img/`), release tooling, and a dead cookiecutter-era hook. Additionally, the template defines its own `_exclude`, which REPLACES Copier's DEFAULT_EXCLUDE — this is how `.git` and `copier.yml` leaked into v0.1.3 output. The full audited list is in requirements.md FR-7.
- Decision: `manifest.json` gains a `prune` key next to `exclude`, with identical validation (relative paths, no `..`). Both are merged into Copier's `exclude=` parameter at fetch time. The split is semantic, for bump-review clarity: `exclude` = broken-by-design, generation fails or output is corrupted without it (dangling symlinks, `.git`, `copier.yml`); `prune` = generates fine but does not belong in a user project (curated, revisited at bump time). JSON has no comments, so the two keys ARE the documentation.
- Consequences: One trivial loader/model change; no new fetch logic. The weekly bump PR reviews both lists against the new upstream commit. `verify_project` gains a forbidden-paths check (FR-9) as the enforcement backstop: if upstream restructures and a pruned/excluded path reappears, CI fails at bump time, never at the user's machine... with one caveat — verify runs at generation time too, so users are equally protected.

### ADR-007: Multi-agent development team and handoff protocol (v0.2)

- Status: Accepted (2026-07-16); amended (2026-07-16): handoffs live under `handoff/<version>/phaseN/` and are gitignored — they are working artifacts of the dev process, not repo content. "Committed" in the original decision is replaced by "on-disk": agents still start from a written document, never from chat history; only source code and docs are committed.
- Context: dev-ready is developed by one human with several AI agents. v0.1 used a loose Architect -> Engineer -> reviewers flow. Adding Antigravity (Gemini) as a code-writing agent requires explicit roles and explicit handoff artifacts, or agents duplicate work and burn tokens re-deriving context.
- Decision: fixed roles, communicating only through on-disk markdown handoffs under `handoff/<version>/`:
  - CEO (Moofon): sets goals, approves plans, merges.
  - Tech Lead (Claude Fable 5, Cowork): talks with the CEO; writes decisions, plans, and handoff documents ONLY — never writes or edits code.
  - Senior Engineer (Claude Opus 4.8): reads the tech lead's phase plan, breaks it into implementation tasks with acceptance criteria (a handoff for the junior), reviews the junior's code for logic and architecture, and personally fixes hard bugs the junior escalates.
  - Junior Engineer (Gemini 3.1 Pro, Antigravity): implements the senior's tasks in the working tree — writes most of the code, but NEVER runs state-changing git (no commit/branch/push; only the CEO commits, after all reviews pass). On completion ALWAYS writes an execution report (md). On a hard bug or an unimplementable task: STOP generating code (do not thrash tokens), log the bug in `reports/problems.md` (where, what happened, suspected cause), and move to the next task. The presence of `problems.md` blocks the phase on the senior; the senior deletes it when all bugs are fixed, or marks it ESCALATED-TO-CEO if unfixable.
  - IBM Bob (QA / Security / SRE): unchanged; reviewer expectations stay in `.bob/qa.md`, `.bob/security.md`, `.bob/sre.md`.
- Handoff artifacts per phase, under `handoff/<version>/phaseN/`: `01-opus-plan.md` (tech lead's brief to the senior; the senior writes his task breakdown + implementation details into 02's designated section), `02-gemini-implementation.md` (the single file the junior receives: working rules from the tech lead + the senior's task breakdown), `03-opus-review.md` (senior's review brief: entry check on `reports/problems.md` — if present, fix mode from problems.md + 02; if absent, review the branch, and write problems.md for any non-trivial finding), `04-bob-qa.md`, `05-bob-security.md`, `06-bob-sre.md`. The junior's outputs go to `handoff/<version>/phaseN/reports/` (`execution-report.md` always; `problems.md` when hard bugs exist).
- Consequences: Every agent starts from a written on-disk document, not from chat history; token spend concentrates in the cheapest capable agent (junior writes most code, senior only reviews and unblocks); the tech lead's no-code rule keeps decisions and implementation auditable separately. FR-10 ships the same scaffold to generated projects as an optional overlay component, so dev-ready users get this workflow for free.

### ADR-008: Two third-party integration modes — vendor vs pinned dependency (v0.3+)

- Status: Accepted (2026-07-17); amended (2026-07-18): CEO decision — the product promise is "one command, Day-1 ready", so no integration may require a manual install step. The originally proposed "reference mode" (config + user installs the tool themselves) is replaced by **pinned-dependency mode**, which delivers zero-setup UX while still redistributing nothing.
- Context: The roadmap (docs/version-plan.md) integrates external tools and skill content: codebase-memory-mcp, react-doctor, caveman, mattpocock/skills, cloudflare/security-audit-skill, awesome-design-md, anthropics/skills, andrej-karpathy-skills. Some have restrictive or unclear licenses (react-doctor: Modified MIT with Commons Clause-style terms; anthropics document-processing skills: source-available, no productization; karpathy-skills: no LICENSE file). Shipping third-party content inside the wheel is redistribution and carries license obligations regardless of dev-ready being open source and non-commercial — redistribution rules do not depend on commercial intent. Full binary vendoring was evaluated and rejected as infeasible: 5 platform binaries × tens of MB exceeds PyPI project size limits, forces a dev-ready re-release per upstream binary patch, and makes dev-ready the redistributor of executables it did not build.
- Decision: every integration is classified by content type into exactly one mode.
  - **Vendor mode** — all *text content* that is legally redistributable: a curated subset of upstream content snapshotted into `src/dev_ready/templates/`, pinned in the manifest `vendored` section (ADR-009) with license and provenance, listed in THIRD_PARTY_NOTICES, with NOTICE propagation for Apache 2.0 content. Vendor everything that can legally be vendored.
  - **Pinned-dependency mode** — *executable tools*: dev-ready writes pinned launcher/dependency entries into the generated project. `.mcp.json` launches `uvx codebase-memory-mcp==<pin>` (published on npm and PyPI; every dev-ready user has uv per NFR-3); `react-doctor@<exact-pin>` is a devDependency in the generated frontend `package.json`, materialized by the `npm install` the user runs anyway. Zero manual steps; the exact pinned version arrives via official channels on first use; a dependency declaration is not redistribution, so restrictive terms (Commons Clause) are not triggered.
- Consequences: Both v0.3 tools integrate with zero license work and zero-setup Day-1 UX. Vendor-mode infrastructure (sync tooling, drift guard, NOTICES automation) is built once, properly, in v0.4. Scope note on ADR-002: "never fetch latest" governs what dev-ready materializes at generation time; pinned-dependency tools are fetched by the user's package manager at first use *at the exact version dev-ready pinned* — version changes arrive only through dev-ready pin bumps, preserving the reproducibility guarantee. Legal boundary independent of UX: content whose license prohibits redistribution is never vendored (anthropics document-processing skills permanently excluded; karpathy-skills accepted as MIT per its README declaration — no standalone LICENSE file, but the pinned commit preserves the grant as evidence).

### ADR-009: Manifest `vendored` section with enforced provenance (v0.4)

- Status: Proposed (2026-07-17), implemented in v0.4 (FR-15/FR-16/FR-18)
- Context: Vendored snapshots rot silently: once files are copied in, nothing ties them to their origin, and "this is repo X at commit Y" becomes an unverifiable claim. The upstream base template solved this with a manifest pin plus CI verification (ADR-002); vendored content needs the same discipline.
- Decision: `manifest.json` gains `vendored: [{repo, commit, license, paths: [{src, dest}]}]`, validated as strictly as the upstream pin. `scripts/sync_vendored.py` re-materializes snapshots from pins; CI enforces byte-equality between the committed snapshot and `repo@commit` (drift = build failure). A monthly bump workflow (deliberately slower than the weekly base-template bump — skill text churns slowly, solo-maintainer review budget is finite) opens vendored-pin PRs; each bump PR re-checks the upstream LICENSE file. THIRD_PARTY_NOTICES must stay in sync with this section, enforced in CI.
- Consequences: Provenance is enforced, not asserted. Adding a vendored repo has a fixed, known cost (pin entry + snapshot + NOTICES entry, all CI-checked). The generation stamp (FR-11) records vendored pins, giving `dev-ready check`/`upgrade` (v0.6) an accurate basis.

### ADR-010: Item-level component selection with a data-driven catalog (v0.3)

- Status: Accepted (2026-07-17)
- Context: The `skills` and `mcp` components stop being monolithic in v0.3: they contain independent items (react-doctor, code-memory; later caveman, security-audit, mattpocock subset, anthropics examples). Users must be able to compose freely — e.g. react-doctor without code-memory. One boolean flag per item (`--no-react-doctor`, `--no-code-memory`, ...) explodes the CLI surface with every catalog addition and was rejected.
- Decision: two-level selection.
  - Level 1 (unchanged): the four components skills / mcp / docs / agents, existing flags and checkbox.
  - Level 2 (new, `skills` and `mcp` only): interactive flow shows a second multi-select listing the chosen component's items, all on by default — pressing Enter reproduces today's behavior exactly. Non-interactive: list flags `--skills <ids|all|none>` and `--mcp <ids|all|none>` (comma-separated ids); `--no-skills`/`--no-mcp` remain as aliases for `none`; `--yes` alone still selects everything. Unknown ids exit 2 listing valid ids.
  - The item catalog is data in `manifest.json` (id, description, integration mode per ADR-008, license, source paths). Prompts, overlay, and verify all render from the catalog: adding a skill is a data entry plus assets, never CLI code. `docs` and `agents` remain boolean — each is a single item.
  - The Answers model (ADR-004) carries item sets; the generation stamp (FR-11) records the exact selection, which `dev-ready upgrade` (FR-22) later relies on.
- Consequences: The CLI contract changes once (v0.3) and then absorbs catalog growth as data. Test surface for selection combinations is bounded by catalog-driven generation (one code path) with CI covering all-on, all-off, and a mixed selection. verify checks that exactly the selected items are present.

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

## Dependency Rules

- Direction: `cli` -> `prompts`/`manifest`/`fetch`/`overlay`/`report`/`verify`. Lower modules never import `cli`.
- `fetch`, `overlay`, and `verify` are independent of each other; only `generate` (called only by `cli`) sequences them.
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
