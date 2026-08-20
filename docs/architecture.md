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
| [ADR-007](decisions/adr-007-multi-agent-handoff-protocol.md) | Multi-agent development team and handoff protocol (v0.2) | Superseded by ADR-021 (2026-07-31) |
| [ADR-008](decisions/adr-008-integration-modes-vendor-vs-pinned.md) | Two third-party integration modes — vendor vs pinned dependency (v0.3+) | Accepted (2026-07-17) |
| [ADR-009](decisions/adr-009-manifest-vendored-provenance.md) | Manifest `vendored` section with enforced provenance (v0.4) | Implemented |
| [ADR-010](decisions/adr-010-item-level-catalog-selection.md) | Item-level component selection with a data-driven catalog (v0.3) | Accepted (2026-07-17) |
| [ADR-011](decisions/adr-011-agent-config-restructure.md) | Standard agent-config layout: AGENTS.md, docs/decisions/, docs/handoff/, .agents/skills/ | Accepted (2026-07-20), partly superseded by ADR-021 |
| [ADR-012](decisions/adr-012-spec-loop-bundle-and-methodology-layering.md) | Spec Loop as a single bundled catalog item, layered with the Handoff Protocol (v0.7) | Accepted (2026-07-24) |
| [ADR-013](decisions/adr-013-internal-process-v2-spec-loop-adoption.md) | Internal process v2 — the Spec Loop layered into the Handoff Protocol (amends ADR-007/011) | Accepted (2026-07-24), partly superseded by ADR-021 |
| [ADR-014](decisions/adr-014-truthful-overlay-lifecycle-state.md) | Separate immutable Base Provenance from Overlay Currency | Accepted (2026-07-25) |
| [ADR-015](decisions/adr-015-agent-targets-canonical-content-pointer-stubs.md) | Agent Targets render as Pointer Stubs over one Canonical Content copy (v0.8) | Accepted (2026-07-26) |
| [ADR-016](decisions/adr-016-language-boundary.md) | Language boundary — English on authored surfaces; byte-identical vendored snapshots retain upstream language (v0.8, amended v0.11) | Accepted (2026-07-26; amended 2026-08-16) |
| [ADR-017](decisions/adr-017-category-first-selection.md) | Category replaces Component as the user-facing selection axis (v0.9) | Accepted (2026-07-27) |
| [ADR-018](decisions/adr-018-spec-loop-spine-and-default-set.md) | Spec Loop always generated; catalog cap becomes a Default Set limit (v0.9) | Accepted (2026-07-27) |
| [ADR-019](decisions/adr-019-agent-target-map-drift-guard.md) | Agent Target Map derived from the reference installer and drift-guarded (v0.10) | Accepted (2026-07-27) |
| [ADR-020](decisions/adr-020-handoff-protocol-not-generated.md) | The Handoff Protocol is dev-ready's own process, not a generated artifact (v0.9) | Accepted (2026-07-27) |
| [ADR-021](decisions/adr-021-internal-process-v3-spec-loop-only.md) | Internal process v3 — the Spec Loop only, no generated gate documents (supersedes ADR-007's protocol) | Accepted (2026-07-31) |
| [ADR-022](decisions/adr-022-upstream-config-not-application-source.md) | dev-ready modifies upstream configuration, never upstream application source (v0.10+) | Accepted (2026-08-04) |
| [ADR-023](decisions/adr-023-upstream-facts-drift-guard.md) | Generated content may state facts about upstream only under a pinned-commit drift guard (v0.10+) | Accepted (2026-08-05) |
| [ADR-024](decisions/adr-024-engineering-flow-selection-spine.md) | Engineering Flow is the user-facing selection spine, named after its source (v0.11) | Accepted (2026-08-12), amends ADR-012/017/018 |
| [ADR-025](decisions/adr-025-skill-delivery-mode.md) | Agent Targets receive a chosen Skill Delivery Mode — symlink or copy — replacing Pointer Stubs (v0.12) | Superseded in full by ADR-028 (2026-08-18), before implementation |
| [ADR-026](decisions/adr-026-setup-project-is-project-infrastructure.md) | `setup-project` is unconditional project infrastructure, not a catalog item (v0.11) | Accepted (2026-08-14) |
| [ADR-027](decisions/adr-027-repository-is-the-plugin.md) | The repository root is the Claude and Codex plugin; manifests describe, catalogs publish, directories sell (v0.11) | Accepted (2026-08-17) |
| [ADR-028](decisions/adr-028-skill-links-replace-pointer-stubs.md) | Agent Targets receive one Skill Link per skill — no copy mode, no Pointer Stub (v0.12) | Accepted (2026-08-18), supersedes ADR-025 |

## Module Boundary

| Module | Responsibility | Must not |
|---|---|---|
| `cli` | Argument parsing, command wiring, exit codes | contain generation logic |
| `prompts` | Interactive/non-interactive collection of user answers into one model | perform I/O other than terminal |
| `fetch` | Generate the upstream base via Copier at the manifest-pinned commit | know about overlay content |
| `overlay` | Apply dev-ready files onto the fetched base; templating of names/values and Mount Point injection | fetch anything from the network |
| `manifest` | Load/validate manifest.json; single source of truth for pins. `ComponentCatalog` is the catalog interface every module takes — items, Categories, development loops, Agent Targets, Default Set | be bypassed by other modules |
| `agent_targets` | Project the selected Agent Targets onto their native paths: rules pointers, MCP config files, retargeted MCP items and effects, Skill Link paths, nested ignore-anchor paths, and skill names from desired Canonical Content paths (ADR-015, ADR-028) | import `prompts`, touch the filesystem, or perform network I/O |
| `skill_links` | Create and classify Skill Link objects: a relative directory symbolic link on POSIX, an elevation-free directory junction via `_winapi.CreateJunction` on Windows | import `prompts`, choose lifecycle policy, follow a link being classified, or perform network I/O |
| `recorded` | Resolve a loaded stamp into a selection over the current catalog, applying stamp-version migration once | choose CLI error/report policy, write to the project, or perform network I/O |
| `catalog_effects` | Validate, apply, and observe catalog-item injected effects through one local-project interface | read manifest.json, perform network I/O, choose CLI error/report policy, or touch overlay-managed content |
| `executable_modes` | Resolve selected manifest-declared executable paths and observe their modes through one read-only interface | write to the project, read manifest.json, perform network I/O, or choose CLI error/report policy |
| `report` | Post-generation summary and next steps | mutate the generated project |
| `inspection` | Read-only observation of generated-project structure shared by generation and lifecycle policies | perform network I/O, write to the project, or choose exit codes |
| `verify` | Map the first shared inspection issue to a generation-blocking error | perform network I/O, write to the project, or duplicate structural traversal |
| `stamp` | Load, parse, and validate `.dev-ready.json` project stamp | import `fetch` or perform network I/O |
| `check` | Compare stamp/current pins and render shared inspection issues as an offline drift report | import `fetch`, perform network I/O, modify target project, or import `verify` internals |
| `upgrade` | Offline re-apply of overlay-managed files onto an existing project; all-or-nothing | import `fetch`, perform network I/O, or touch upstream/non-overlay paths |


## Dependency Rules

- Direction: `cli` -> `prompts`/`manifest`/`fetch`/`overlay`/`report`/`verify`. Lower modules never import `cli`.
- `fetch`, `overlay`, and `verify` are independent of each other; only `generate` (called only by `cli`) sequences them. `overlay` and `verify` may depend on the neutral, read-only `executable_modes` resolver. `manifest`, `overlay`, `verify`, `check`, and `upgrade` may depend on `catalog_effects`; `verify` and `check` may depend on `inspection`.
- `upgrade` (called only by `cli`) sequences `overlay` and `stamp` offline, analogous to `generate`.
- `agent_targets` sits directly above `manifest` and depends on nothing else, so `overlay`, `inspection`, `upgrade` and the lifecycle test fixtures can all read one projection. **No module may restate the Agent Target layout** — where an Agent Target's rules pointer, MCP config, Skill Link or nested ignore-anchor goes is decided in `agent_targets` and nowhere else.
- `skill_links` sits beside `overlay` and `upgrade` as the only filesystem writer for Skill Link objects. It may be imported by `generate`, `verify`, `inspection`, `upgrade` and tests. It does not import `agent_targets` — callers pass the paths the projection already computed.
- `recorded` depends on `manifest`, `stamp` and `prompts`, and is the only place a stamp is resolved against the current catalog. `check` and `upgrade` read it and differ only in policy: `check` reports what was dropped, `upgrade` refuses. **Stamp-version migration rules live there once** — a new stamp version is one module's change.
- **Content dev-ready owns is transformed inside `build_overlay_content`; content it does not own is mutated after the write, by `catalog_effects`.** The stamp inventory hashes `build_overlay_content`'s output, so a transform applied after the write records a hash that can never match the file it describes, and `upgrade` then treats a file nobody edited as user-modified forever. `classify_shared_targets` compounds it by classifying every effect target as shared and excluding it a second time. Mount Point injection therefore happens inside `build_overlay_content` and is not a `CatalogEffect`. Neither failure raises anything — the wrong side of this line is silent until a user runs `upgrade`.
- Modules take `ComponentCatalog`, not the bare mapping it subclasses. Its Categories, Agent Targets, development loops and Default Set are part of the interface; reaching them with a defaulted `getattr` reintroduces a catalog shape the loader refuses to build.
- Runtime dependencies are kept minimal (current: questionary, copier — see ADR-005; rich optional). Every new dependency requires a note here. Dev-only: `prompt-toolkit`, pinned `>=3.0.29,<4` so tests can drive `_questionary_asker` headlessly over `create_pipe_input()`/`DummyOutput()`; questionary already pulls it in, but at `>=2.0,<4.0` — too loose for an API the tests call directly.
- No module reads `manifest.json` directly except `manifest`.
- `scripts/` (CI-only maintainer tooling, e.g. `scripts/bump_upstream.py`) is not part of the wheel and is not subject to the `fetch/`-only network-call rule above, which governs `src/dev_ready` only.

### Skill Link delivery (ADR-028)

`agent_targets` is the pure projection: Skill Link paths, nested ignore-anchor
paths, and skill names taken from desired Canonical Content. It performs no
filesystem I/O. `skill_links` is the only writer that creates, classifies, or
removes those link objects. `inspection` is the shared read-only classification
seam for Canonical Content, target containers, anchors, and links, consumed by
`verify` and `check`. When a selection projects links, `verify` materializes
the complete set in staging with the production writer, inspects it, and
removes those temporary links. Finalize then atomically renames staging into
place and recreates the same links against the final Canonical Content.
Each selected Agent Target skills directory receives a managed nested
`.gitignore` as the Git safety gate; the project root `.gitignore` is not
rewritten. `upgrade` writes Canonical Content, then exact state-aware nested
anchors, then retires eligible legacy directories and creates, repairs, or
retires links, and writes the stamp last.

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
- CI workflows: `ci.yml` (six jobs: `test`, `vendored-drift`, `agent-target-drift`, `upgrade-from-release`, `generate-and-verify`, and `windows-lifecycle`), `upstream-bump.yml` (weekly pin bump PR), `release.yml` (publish on tag). The `windows-lifecycle` job runs the offline suite plus real generation and the N−1 gate on Windows so junctions, Git exclusion, and moved-project repair are native.
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
 |               |               |               |--verify_project->staging (links probed, then removed) |
 |               |               |               |--rename(staging)---------------->target_dir
 |               |               |               |--create Skill Links------------->target_dir
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
