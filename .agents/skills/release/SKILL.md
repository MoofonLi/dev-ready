---
name: release
description: Release a new version of the dev-ready repo (MoofonLi/dev-ready) end to end - bump version, verify locally, write the phase overview report, commit in stages, push, wait for CI, tag and publish to PyPI. Use whenever a dev-ready version is to be released, published, shipped, or tagged - e.g. "release v0.3.0", "ship it", "tag the release", "push to PyPI", "this phase is done, release it" - or to bump the version, re-tag after a failed CI run, or generate the phase overview report before release.
---

# dev-ready Release Workflow

Ship a dev-ready version from finished code to a published PyPI release. Follow the steps in order; each step gates the next. The CEO (Moofon) runs the terminal commands unless he has explicitly asked otherwise - the default job is to prepare everything, verify state, and hand him the exact commands.

This skill is the single source of truth for the release process. It is invoked either directly by the CEO, or by the Release Engineer (the Senior Engineer role) acting on `07-opus-release.md` at the close of a release phase (the one document that carries a scoped git-authority exemption, ADR-007/ADR-011).

Repo layout facts this workflow depends on: version lives in BOTH `src/dev_ready/__init__.py` (`__version__`) and `pyproject.toml` (`version`); `release.yml` refuses to publish if the pushed tag does not match `pyproject.toml`; handoff working files live in `docs/handoff/<version>/phase-N/` (gitignored - never commit them, ADR-011); Conventional Commits are mandatory.

## Step 0 - Determine the version

The version comes from the user ("release v0.3.0" means `0.3.0`). If the user did not state one, ask - never guess. Then sanity-check it:

- It must be greater than the current `version` in `pyproject.toml`.
- Cross-check against `docs/handoff/<version-minor>/` (e.g. releasing 0.3.x, expect `docs/handoff/v0.3/`) and `docs/handoff/v0.3/v0.3-plan.md` to confirm which phase(s) this release covers.

## Step 1 - Bump the version in two files

Update to the release version, keeping the two in sync:

1. `src/dev_ready/__init__.py`: `__version__ = "X.Y.Z"`
2. `pyproject.toml`: `version = "X.Y.Z"`

They must be identical: the CLI prints `__version__`, while the wheel and the release-workflow guard read `pyproject.toml`. A mismatch ships a CLI that reports the wrong version.

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

Every command must pass before continuing. If anything fails, stop the release: fix (or route the bug through the ADR-007 workflow - junior implements, senior reviews), and restart from this step. Do not "release now, fix later" - the release pipeline publishes to PyPI, which cannot be unpublished.

## Step 3 - Generate the phase overview report

Only after all tests pass. Read everything under `docs/handoff/<version>/phase-N/` for the phase(s) this release completes - the six handoff docs plus the junior's outputs in `reports/` (execution report, `problems.md`).

Write `docs/handoff/<version>/reports/phase-N-overview.md` (one per completed phase, e.g. `phase-1-overview.md`) with:

- **Scope**: which FRs/ADRs this phase implemented (cite requirements.md / architecture.md / decisions/ numbers)
- **What was built**: modules touched, behavior changes, from the execution report
- **Problems encountered**: from `problems.md` and escalations - what happened, how it was resolved, by whom (junior / senior)
- **Review outcomes**: verdicts from the senior review and the reviewer's QA / security / SRE passes
- **Test evidence**: unit / lint / integration results from Step 2

This file stays in the gitignored handoff tree - it is the CEO's record, not a repo doc. Show it to the user and get an explicit OK before moving on: this is the "confirm it's fine" gate.

## Step 4 - Staged commits

Group the working-tree changes into separate commits by Conventional Commit type, in this order (each commit should leave the tree in a working state):

1. `feat:` / `fix:` - implementation changes (one commit per coherent change, not per file)
2. `docs:` - documentation-only changes
3. `chore: bump version to X.Y.Z` - the two version files + `uv.lock`, always the last commit before tagging

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
