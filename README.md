# dev-ready

[![CI](https://github.com/MoofonLi/dev-ready/actions/workflows/ci.yml/badge.svg)](https://github.com/MoofonLi/dev-ready/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/dev-ready)](https://pypi.org/project/dev-ready/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Scaffold a production-grade, AI-development-ready FastAPI + React project in one command:

```bash
uvx dev-ready init my-app
```

No half-finished output, no untested "latest": the upstream template is pinned to a CI-verified commit, and generation is all-or-nothing — if any step fails, your target directory is never touched.

## What you get

A generated project based on [fastapi/full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template) (FastAPI, React, SQLModel, PostgreSQL, Docker Compose), plus an AI tooling overlay so it works well with coding agents out of the box:

- `CLAUDE.md` — project instructions for Claude Code
- Claude Code skills (e.g. project orientation)
- MCP server configuration (`mcp.json`)
- Design-doc templates (`architecture.md`, `requirements.md`)

## Requirements

- Python >= 3.12
- [uv](https://docs.astral.sh/uv/) (for `uvx`), or install with `pip install dev-ready`
- Network access to github.com (to fetch the pinned template snapshot)
- Docker is **not** required to generate a project — only to run the generated one

## Usage

```bash
# Interactive: prompts for anything not given on the command line
uvx dev-ready init

# Non-interactive: accept all defaults, no prompts
uvx dev-ready init my-app --yes

# Options
uvx dev-ready init my-app \
  --dir path/to/target \  # default: ./my-app
  --no-skills \           # skip the Claude Code skills overlay
  --no-mcp \              # skip the MCP configuration overlay
  --no-docs               # skip the design-doc templates
```

Then follow the printed next steps (typically `docker compose watch` inside the generated project).

### Exit codes

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | Unexpected error or user abort (`aborted: nothing was written`) |
| 2 | Argument error (including missing input in non-TTY environments) |
| 3 | Network / fetch failure |
| 4 | Target directory conflict |
| 5 | Generated output failed structural verification |

Full CLI contract: [docs/cli-spec.md](docs/cli-spec.md).

## How it works

1. **Prompt & confirm** — collect answers, show a summary before any network call or write (`--yes` skips this).
2. **Fetch** — download the upstream template as a tarball at the commit pinned in `src/dev_ready/manifest.json` (a lockfile shipped inside the wheel), safely extracted into a staging directory.
3. **Overlay** — apply the AI tooling files with template-variable substitution, still in staging.
4. **Verify** — structural checks against required paths (backend, frontend, compose files, ...).
5. **Finalize** — move staging into the target. This is the only step that touches the target.

The pin is kept current by a weekly GitHub Actions job that opens a bump PR; CI validates every PR by actually generating a project, building it with Docker Compose, and polling the health-check endpoint. A released CLI therefore always carries a pin it was tested with. Design details and ADRs: [docs/architecture.md](docs/architecture.md).

## Development

```bash
uv sync --dev
uv run dev-ready init demo --yes   # run the CLI
uv run pytest                      # unit tests (network tests excluded by default)
uv run pytest -m network           # integration tests against real GitHub
uv run ruff check .                # lint
```

Releases are tag-driven (`vX.Y.Z`) and published to PyPI via trusted publishing — see [docs/releasing.md](docs/releasing.md).

This repo is developed with a multi-agent workflow (Architect → Engineer → QA / Security / SRE review); agent instructions live in [CLAUDE.md](CLAUDE.md) and reviewer roles in `.bob/`.

## Roadmap

- `dev-ready check` — validate an existing project against the manifest
- `dev-ready upgrade` — re-apply a newer overlay to an existing project
- Additional base templates and curated third-party skill content

## License

MIT — see [LICENSE](LICENSE). Generated projects include content derived from fastapi/full-stack-fastapi-template (MIT); see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
