# Releasing dev-ready

## One-time setup: PyPI Trusted Publisher

`release.yml` publishes via [PyPI trusted publishing](https://docs.pypi.org/trusted-publishers/) — no API token or password is stored in this repo. Before the first release, a maintainer with access to the `dev-ready` project on PyPI must configure it once:

1. Sign in to PyPI and go to the `dev-ready` project's **Publishing** settings (or, for a brand-new project, [pypi.org/manage/account/publishing](https://pypi.org/manage/account/publishing/) to pre-register it).
2. Add a new trusted publisher with:
   - **Owner:** this repository's GitHub org/user
   - **Repository name:** this repo's name
   - **Workflow name:** `release.yml`
   - **Environment name:** leave blank (the workflow does not use a GitHub Environment)
3. Save. No further action is needed — `pypa/gh-action-pypi-publish` in `release.yml` requests a short-lived OIDC token from GitHub Actions at publish time and PyPI verifies it against this configuration.

This is a one-time setup per PyPI project. It does not need to be repeated for future releases.

## Cutting a release

1. Bump the version in `pyproject.toml` (`[project].version`).
2. Commit the bump (Conventional Commits, e.g. `chore: release v0.2.0`).
3. Tag the commit `vX.Y.Z`, matching the `pyproject.toml` version exactly:
   ```
   git tag v0.2.0
   git push origin v0.2.0
   ```
4. Pushing the tag triggers `release.yml`, which:
   - verifies the tag version matches `pyproject.toml` (fails fast on mismatch)
   - builds sdist + wheel with `uv build`
   - installs the built wheel into a scratch venv and runs `dev-ready --version` as a smoke test
   - publishes to PyPI via trusted publishing

No manual `twine upload` or token management is required or supported.
