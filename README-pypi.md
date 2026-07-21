# dev-ready

Scaffold a production-grade, AI-development-ready FastAPI + React project in one command:

```bash
uvx dev-ready init my-app
```

The upstream template is pinned to a CI-verified commit (never an untested "latest"), and generation is all-or-nothing — if any step fails, your target directory is never touched.

## What you get

A generated project based on [fastapi/full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template) (FastAPI, React, SQLModel, PostgreSQL, Docker Compose), plus an AI tooling overlay so it works well with coding agents out of the box:

- `CLAUDE.md` — project instructions for Claude Code
- Claude Code skills (e.g. project orientation)
- MCP server configuration (`mcp.json`)
- Design-doc templates (`architecture.md`, `requirements.md`)
- Agent-team handoff scaffold (`docs/handoffs/` — a document-driven multi-agent workflow: Tech Lead → Senior → Junior → QA/Security/SRE)
- Generation stamp — every generated project gets a `.dev-ready.json` recording the dev-ready version, selected components/items, and pinned upstream commit
- Pinned tool integrations — optional, selectable MCP and skill items: a codebase-memory MCP server (`uvx codebase-memory-mcp`) and a `react-doctor` frontend wrapper skill + devDependency
- item-level selection — pick individual items inside the skills and MCP components, not just the whole component

Every generated project also gets its own `README.md` (the upstream template's repo README and other repo-maintenance files — `CONTRIBUTING.md`, release notes, deploy workflows, screenshots — are pruned, so nothing template-repo-specific leaks into your project).

## Requirements

- Python >= 3.12 (uv can install this for you automatically)
- git (Copier fetches the pinned template via git)
- Network access to github.com (to fetch the pinned template snapshot)
- Docker is **not** required to generate a project — only to run the generated one

## Installation

No install needed with [uv](https://docs.astral.sh/uv/) (any recent version):

```bash
uvx dev-ready init my-app
```

Or install with pip (requires Python >= 3.12):

```bash
pip install dev-ready
dev-ready init my-app
```

## Usage

```bash
# Interactive: prompts for anything not given on the command line
uvx dev-ready init

# Non-interactive: accept all defaults, no prompts
uvx dev-ready init my-app --yes

# Options
uvx dev-ready init my-app \
  --dir path/to/target \    # default: ./my-app
  --skills <ids|all|none> \ # choose individual skills (default: all)
  --mcp <ids|all|none> \    # choose individual MCP servers (default: all)
  --no-skills \             # skip the Claude Code skills overlay
  --no-mcp \                # skip the MCP configuration overlay
  --no-docs \               # skip the design-doc templates
  --no-agents               # skip the agent-team handoff scaffold
```

Then follow the printed next steps (typically `docker compose watch` inside the generated project).

Exit codes: 0 success; 1 unexpected error or user abort; 2 argument error; 3 network/fetch failure; 4 target directory conflict; 5 structural verification failure.

## How it works

The CLI ships with a lockfile (`manifest.json`) pinning the upstream template commit. Generation fetches that exact snapshot, applies the overlay with variable substitution, verifies the result structurally — all inside a staging directory — and only then moves it into the target. The pin is kept current by a weekly CI job that opens bump PRs, each validated by actually generating and booting a project with Docker Compose.

## Links

- Source & issues: <https://github.com/MoofonLi/dev-ready>
- CLI spec, architecture, and ADRs: <https://github.com/MoofonLi/dev-ready/tree/main/docs>

## License

MIT. Generated projects include content derived from fastapi/full-stack-fastapi-template (MIT); see [THIRD_PARTY_NOTICES.md](https://github.com/MoofonLi/dev-ready/blob/main/THIRD_PARTY_NOTICES.md).
