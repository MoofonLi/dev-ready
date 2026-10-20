# Pin Maintenance — pinned tool integrations

All version pins live in `src/dev_ready/manifest.json` only (ADR-002). Two kinds exist:

| Pin | Auto-bumped? | How it updates |
|---|---|---|
| `base_template` (upstream FastAPI template commit) | Yes — `upstream-bump.yml` opens a weekly PR | CI-gated, no manual action |
| Catalog item pins (`components.*.items[].pin`, e.g. `code-memory`, `react-doctor`) | **No** | Manual review, checklist below |

Catalog item pins are NOT covered by `upstream-bump.yml`. They rot silently: when the
pinned tool publishes a new release (feature, compatibility, or security fix), dev-ready
keeps shipping the old pin until a human updates the manifest.

## Review cadence

- **Quarterly**, and additionally
- **Immediately** when a security advisory is published for a pinned package.

## Checklist per review

1. List current pins: `grep -n '"pin"' src/dev_ready/manifest.json` and note each item's
   id and channel (PyPI for `code-memory` → `codebase-memory-mcp`; npm for `react-doctor`).
2. Check the registry for the latest version of each package
   (`https://pypi.org/pypi/<name>/json`, `https://registry.npmjs.org/<name>`).
3. If a newer version exists: read its changelog for breaking changes, update the `pin`
   value in `src/dev_ready/manifest.json` (nowhere else), and run the full verification
   suite: `uv sync --dev` → `uv run pytest` → `uv run ruff check .` → `uv run pytest -m network`.
4. Real-run check: one generation into a scratch directory outside the repo with `--yes`;
   confirm the new pin appears in the generated `.mcp.json` / `frontend/package.json` and
   the `.dev-ready.json` stamp; delete the scratch directory.
5. Consider re-recording the README capture. The committed tape is
   `docs/assets/demo.tape`; its output is `docs/assets/demo.gif`. Replay the
   tape with VHS rather than reconstructing a recording setup. A stale image
   is an accepted cost (ADR-023, 2026-08-30 amendment) — re-record when the
   interactive CLI surface the capture shows has changed, not on every pin
   bump.
6. Open a PR with a `chore:` Conventional Commit (e.g. `chore: bump react-doctor pin to X.Y.Z`).

## Base-template compatibility boundary (2026-10-21)

PR #9 is a maintenance bump within the existing generation contract: the
selected upstream commit must still declare Copier questions and execute its
`.env` task, and Compose must run `prestart` before the backend starts.
The manifest selects the last commit before upstream's
[explicit database-setup change](https://github.com/fastapi/full-stack-fastapi-template/commit/9d541082a3c1b3d529b40e7dc59857f15c5fc216).
It preserves per-project names and secrets and automatic initialization.

Upstream subsequently
[removed Copier generation](https://github.com/fastapi/full-stack-fastapi-template/commit/af791805aceab6e74db98edcc27b6f26722f326b).
Copier can copy that tree without applying any answers, leaving the upstream
project name and placeholder secrets. Passing structural verification alone
therefore does not establish compatibility. The real-generation E2E suite
checks names and fresh secrets across two projects in addition to the stack
facts and Docker health gates.

Moofon chose to keep this repair within the maintenance surface. Supporting
the newer generation and explicit-initialization contract is deferred to a
separate version, with an amendment to ADR-005 and an accepted spec before
implementation. Scheduled bumps may still propose newer commits; they must
pass the existing verification gates before merge. Do not relax those gates
to admit a commit beyond this boundary.

## Long-term

Extending `upstream-bump.yml` (or a sibling workflow) to also check registries for catalog
item pins and open bump PRs is the preferred permanent fix — tracked as future work
(candidate for the v0.4+ vendoring/sync machinery, ADR-008/FR-15+). Until that lands,
this document is the maintenance surface.
