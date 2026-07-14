# Third-Party Notices

dev-ready does not vendor or redistribute any third-party source code in
its PyPI package. The only third-party component involved in what it
produces is:

## fastapi/full-stack-fastapi-template

- License: MIT
- Source: https://github.com/fastapi/full-stack-fastapi-template

dev-ready does not ship a copy of this template. At generation time
(`dev-ready init`), the CLI downloads a snapshot of this repository at the
exact commit pinned in `src/dev_ready/manifest.json` (see ADR-002,
`docs/architecture.md`) directly onto the end user's machine. The
upstream `LICENSE` file is part of that snapshot and arrives inside every
generated project unmodified.

---

Everything else dev-ready writes into a generated project — `CLAUDE.md`,
the Claude Code skills overlay, MCP configuration, and design-doc
templates under `src/dev_ready/templates/` — is original to this project
and is not derived from a third-party source.

Runtime Python dependencies (e.g. `questionary`) are ordinary PyPI
packages resolved by the installer at install time; they are not vendored
into this package and each carries its own license via its own PyPI
distribution.
