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
5. Open a PR with a `chore:` Conventional Commit (e.g. `chore: bump react-doctor pin to X.Y.Z`).

## Long-term

Extending `upstream-bump.yml` (or a sibling workflow) to also check registries for catalog
item pins and open bump PRs is the preferred permanent fix — tracked as future work
(candidate for the v0.4+ vendoring/sync machinery, ADR-008/FR-15+). Until that lands,
this document is the maintenance surface.
