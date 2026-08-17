---
name: release
description: Release a new version of the dev-ready repo (MoofonLi/dev-ready) end to end - bump version, verify locally, write the version overview, commit in stages, push, wait for CI, tag and publish to PyPI. Use whenever a dev-ready version is to be released, published, shipped, or tagged - e.g. "release v0.3.0", "ship it", "tag the release", "push to PyPI", "this phase is done, release it" - or to bump the version, re-tag after a failed CI run, or write the version overview before release.
---

# dev-ready Release Workflow

Ship a dev-ready version from finished code to a published PyPI release. Follow the steps in order; each step gates the next. Moofon runs the terminal commands unless he has explicitly asked otherwise - the default job is to prepare everything, verify state, and hand him the exact commands.

This skill is the single source of truth for the release process. Release is the one place where state-changing git is unavoidable, and it carries no standing exemption (ADR-021): every `git commit`, `git push`, and `git tag` below needs Moofon's explicit permission for that specific action, asked for at the moment it is due.

Repo layout facts this workflow depends on: version lives in FOUR files — `src/dev_ready/__init__.py` (`__version__`), `pyproject.toml` (`version`), `.claude-plugin/plugin.json` (`version`), and `.codex-plugin/plugin.json` (`version`); `release.yml` refuses to publish if the pushed tag does not match `pyproject.toml`; handoff working files live in `docs/handoff/<version>/phase-N/` (gitignored - never commit them, ADR-011); Conventional Commits are mandatory.

## Step 0 - Determine the version

The version comes from the user ("release v0.3.0" means `0.3.0`). If the user did not state one, ask - never guess. Then sanity-check it:

- It must be greater than the current `version` in `pyproject.toml`.
- Cross-check against `docs/handoff/<version-minor>/` (e.g. releasing 0.3.x, expect `docs/handoff/v0.3/`) and `docs/handoff/v0.3/v0.3-plan.md` to confirm which phase(s) this release covers.

## Step 1 - Bump the version in four files

Update to the release version, keeping all four in sync:

1. `src/dev_ready/__init__.py`: `__version__ = "X.Y.Z"`
2. `pyproject.toml`: `version = "X.Y.Z"`
3. `.claude-plugin/plugin.json`: `"version": "X.Y.Z"`
4. `.codex-plugin/plugin.json`: `"version": "X.Y.Z"`

The package's two version strings must be identical: the CLI prints `__version__`, while the wheel and the release-workflow guard read `pyproject.toml`. A mismatch ships a CLI that reports the wrong version. The two plugin manifests carry the same string; they are not additional sources of truth. Leaving a manifest behind pins every installed plugin user to the version they first installed, with no error and no symptom.

## Step 2 - Local verification

Run in the dev-ready repo root:

```
uv sync --dev
uv run pytest
uv run ruff check .
```

`uv sync` also refreshes `uv.lock` with the new version - include `uv.lock` in the version commit later.

Then the integration/e2e tests (excluded by default via the `not network` marker; they hit the real GitHub upstream):

```
uv run pytest -m network
```

Every command must pass before continuing. If anything fails, stop the release: fix it through the Spec Loop (ADR-021), and restart from this step. Do not "release now, fix later" - the release pipeline publishes to PyPI, which cannot be unpublished.

## Step 3 - Write the version overview

Only after all tests pass. `docs/version_overview/<version>-overview.md` is the durable, committed record of what the version ships, and it is the **only** per-version document this process produces: ADR-021 retired the gitignored per-phase `reports/` overviews along with the rest of the phase document set (see its 2026-08-09 amendment). Never write `docs/handoff/<version>/reports/` - that path is retired.

Reconstruct the version from: the phase sections of `docs/handoff/<version>/<version>-plan.md`, the accepted specs in `docs/specs/<version>/`, the ticket files under `docs/handoff/<version>/phase-N/tickets/`, and `git log` since the previous release tag. Follow the shape the existing overviews already use (`docs/version_overview/v0.9-overview.md` is the reference):

- **Header**: release version, `Status: Released`, and a scope line naming every FR and permanent gate the version covers
- **What the version ships**: one section per FR, written as outcomes a user sees, citing the governing ADRs
- **Upgrade from the previous version**: what `upgrade` migrates, what it preserves, and anything it cannot reach
- **v1.0 real-users gate evidence**: observations against the decidable checklist, recorded as evidence rather than as a readiness judgment
- **Deferred scope**: what this version deliberately does not ship

State deviations here rather than leaving them to the git log: anything the commits did that the accepted specs did not ask for, or asked for and did not get. Test evidence from Step 2 belongs in the session report to Moofon, not in this file.

Show it to Moofon and get an explicit OK before moving on: this is the "confirm it's fine" gate. Unlike the retired phase reports, this file is a repo document and ships in the `docs:` commit below.

## Step 4 - Doc status sweep, then staged commits

Before staging anything, sweep the doc status lines so they cannot rot (added 2026-07-24 after AGENTS.md was found still claiming "v0.3 in progress" at the v0.6.0 release):

- `AGENTS.md` "Current phase" line — set to the version being released (and the next version in planning, if decided).
- `docs/requirements.md` Future Roadmap — mark the released version DONE (vX.Y.Z).
- `docs/version_overview/<version>-overview.md` — written and accepted in Step 3, and says Released.

These belong in the `docs:` commit below.

Group the working-tree changes into separate commits by Conventional Commit type, in this order (each commit should leave the tree in a working state):

1. `feat:` / `fix:` - implementation changes (one commit per coherent change, not per file)
2. `docs:` - documentation-only changes
3. `chore: bump version to X.Y.Z` - the four version files + `uv.lock`, always the last commit before tagging

Never `git add .` blindly: check `git status` first and confirm nothing from `docs/handoff/` or scratch files is staged. If the user prefers, hand him the exact `git add <files>` + `git commit -m` command sequence instead of running it.

## Step 5 - Push and wait for CI green

```
git push
```

Both jobs on main must pass: `test` (lint + unit) and `generate-and-verify` (real generation + docker compose health check, takes several minutes). Watch with `gh run watch` if `gh` is available, otherwise the repo's Actions page. Do not tag until CI is green - the tag is what publishes.

## Step 6 - Tag and release

```
git tag vX.Y.Z
git push origin vX.Y.Z
```

`release.yml` then: verifies tag matches the pyproject version, builds, smoke-tests the wheel, publishes to PyPI (trusted publishing), and creates the GitHub Release.

Post-release check: `uvx dev-ready@X.Y.Z --version` reports the new version, and a scratch `uvx dev-ready@X.Y.Z init smoke-test --yes` generates a clean project (in particular: no `.git`, no `copier.yml` in the output).

## Troubleshooting

**CI fails after the tag was pushed** - fix the problem, commit it (back to Step 4/5), then move the tag to the fixed commit and re-push it to re-trigger the release pipeline:

```
git tag -d vX.Y.Z
git push origin :refs/tags/vX.Y.Z
git tag vX.Y.Z
git push origin vX.Y.Z
```

Only safe while the PyPI publish has NOT succeeded - PyPI rejects re-uploading a version that already published. If PyPI already has X.Y.Z, do not fight it: release X.Y.Z+1 instead.

**`fatal: Unable to create ... index.lock: File exists`** - a previous git process died (common after an editor/agent crash). Confirm no git process is actually running, then delete the leftover lock:

```
del .git\index.lock        (Windows)
rm -f .git/index.lock      (macOS/Linux)
```

**Tag/version mismatch error in release.yml** - the tag and `pyproject.toml` disagree. Fix the version files (Step 1), commit, and re-tag per the flow above.

**Release published to PyPI but no GitHub Release** - the last workflow step failed after publish. Do not re-tag (PyPI already has the version); create the GitHub Release manually: `gh release create vX.Y.Z --generate-notes`.
