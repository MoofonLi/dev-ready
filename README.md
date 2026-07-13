# dev-ready

Scaffold a production-grade, AI-development-ready FastAPI project in one command:

```bash
uvx dev-ready init my-app
```

> Status: bootstrap phase. Repository structure and design docs are in place; the CLI is not yet implemented.

## What it generates

- Base: [fastapi/full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template) at a pinned, CI-verified commit (never untested "latest")
- Overlay: CLAUDE.md, Claude Code skills, MCP server configuration, and design-doc templates so the generated project is immediately workable with AI coding agents

## Tech stack

Python >= 3.12, uv/uvx for distribution, questionary for prompts, GitHub Actions for upstream tracking and releases. Design details and ADRs: [docs/architecture.md](docs/architecture.md).

## Development

```bash
uv sync --dev
uv run dev-ready     # run the CLI
uv run pytest        # tests
uv run ruff check .  # lint
```

## Development workflow (multi-agent)

This repo is developed with an AI-agent workflow: Architect -> Engineer -> QA -> Security -> Release. Agent instructions live in [CLAUDE.md](CLAUDE.md) and reviewer roles in [.bob/](.bob/).

## Repository layout

```
docs/         requirements, architecture (ADRs), CLI spec
src/dev_ready cli / prompts / fetch / overlay / manifest / report
templates/    overlay assets copied into generated projects
tests/        unit / integration / e2e
.bob/         IBM Bob reviewer role definitions (QA, Security, SRE)
.github/      CI, weekly upstream bump, release workflows

Upstream pins live in src/dev_ready/manifest.json (bundled with the package,
so a released CLI always carries the pin it was tested with).
```

## License

MIT — see [LICENSE](LICENSE). Generated projects include content derived from fastapi/full-stack-fastapi-template (MIT).
