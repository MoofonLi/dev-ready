# Releasing dev-ready

The release procedure lives in the `release` process skill
(`.agents/skills/release/SKILL.md`). That skill is the source of truth for
which files hold the version, which verification commands must pass, how
commits are staged, and when to tag. Do not copy the steps here — a second
copy will drift.

## One-time setup: PyPI Trusted Publisher

`release.yml` publishes via [PyPI trusted publishing](https://docs.pypi.org/trusted-publishers/) — no API token or password is stored in this repo. Before the first release, a maintainer with access to the `dev-ready` project on PyPI must configure it once:

1. Sign in to PyPI and go to the `dev-ready` project's **Publishing** settings (or, for a brand-new project, [pypi.org/manage/account/publishing](https://pypi.org/manage/account/publishing/) to pre-register it).
2. Add a new trusted publisher with:
   - **Owner:** this repository's GitHub org/user
   - **Repository name:** this repo's name
   - **Workflow name:** `release.yml`
   - **Environment name:** `pypi` — the publish job runs with `environment: pypi` (see `release.yml`). Leaving this blank still works (a blank publisher-side environment accepts a token from *any* environment), but naming it `pypi` is what actually restricts publishing to that environment, so set it.
3. Save. No further action is needed — `pypa/gh-action-pypi-publish` in `release.yml` requests a short-lived OIDC token from GitHub Actions at publish time and PyPI verifies it against this configuration.

This is a one-time setup per PyPI project. It does not need to be repeated for future releases.

### GitHub Environment (`pypi`)

The publish job declares `environment: pypi`. GitHub auto-creates the environment on first use, so nothing is strictly required up front. For real protection, pre-create it under the repo's **Settings → Environments** before the first tagged release and add a deployment branch/tag rule limiting it to `v*` tags (and optionally required reviewers). This pairs with the PyPI-side `pypi` environment above so only the release workflow, on a version tag, can publish.
