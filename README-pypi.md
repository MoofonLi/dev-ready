# dev-ready

繁體中文導覽：<https://github.com/MoofonLi/dev-ready/blob/main/README.zh-TW.md>

Scaffold a production-grade, AI-development-ready FastAPI + React project in one command:

```bash
uvx dev-ready init my-app
```

The upstream template is pinned to a CI-verified commit (never an untested "latest"), and generation is all-or-nothing — if any step fails, your target directory is never touched.

## What you get

A generated project based on [fastapi/full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template) (FastAPI, React, SQLModel, PostgreSQL, Docker Compose), plus an AI tooling overlay so it works well with coding agents out of the box:

- `CLAUDE.md` — project instructions for Claude Code, including Karpathy-derived development guardrails (MIT, per the upstream README)
- Claude Code skills — a 10/10 catalog selectable at generation time:
  - **project-orientation** (built-in) — codebase orientation helper
  - **react-doctor** (pinned devDependency) — frontend dependency health checks
  - **caveman** (vendored, MIT) — token-discipline communication mode
  - **tdd** (vendored, MIT) — test-driven development loop
  - **diagnosing-bugs** (vendored, MIT) — diagnosis loop for hard bugs
  - **code-review** (vendored, MIT) — review against coding standards and spec
  - **spec-loop** (vendored, MIT) — planning, durable specs, tracer-bullet
    tickets, TDD, review, diagnosis, and architecture improvement; selecting it
    automatically resolves `tdd`, `diagnosing-bugs`, and `code-review`
  - **security-audit** (vendored, MIT) — multi-phase security audit
  - **webapp-testing** (vendored, Apache-2.0) — browser-automation end-to-end testing
  - **frontend-design** (vendored, Apache-2.0) — frontend UI design methodology
- MCP server configuration (`.mcp.json`)
- Design-doc templates (`docs/architecture.md`, `docs/requirements.md`)
- Configurable Handoff Protocol (`docs/handoffs/`) with one authoritative
  Protocol Configuration, `protocol.yaml`, for seven stable roles, editable
  titles/model assignments, handoff order, escalation, review gates, and commit
  authority
- Generation stamp — every generated project gets a `.dev-ready.json`
  recording immutable Base Provenance, current Overlay Currency, selected
  components/items and pins, and the managed overlay inventory
- Pinned tool integrations — optional, selectable MCP and skill items: a codebase-memory MCP server (`uvx codebase-memory-mcp`) and a `react-doctor` frontend wrapper skill + devDependency
- Item-level selection — pick individual skills (including vendored ones) and MCP items; vendored skills include their upstream provenance in `.dev-ready.json`

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

### Install the agent skill

Install the repository's cross-agent skill directly:

```bash
npx skills add MoofonLi/dev-ready --skill dev-ready
```

The source is
[`skills/dev-ready/SKILL.md`](https://github.com/MoofonLi/dev-ready/blob/main/skills/dev-ready/SKILL.md).
To inspect the repository's discoverable skills before installing, run
`npx skills add MoofonLi/dev-ready --list`.

Then ask your agent: "Scaffold a FastAPI project with dev-ready named my-app."
The skill will inspect the destination, resolve component selections, run one
non-interactive initialization command, and verify the generated stamp.

For installation or generation problems, open an issue at
<https://github.com/MoofonLi/dev-ready/issues>.

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

```bash
# Inspect a generated project against its stamp and the current CLI (read-only)
uvx dev-ready check path/to/project
uvx dev-ready check path/to/project --json  # machine-readable report

# Re-apply managed overlay files to an existing project (never touches app code)
uvx dev-ready upgrade path/to/project
uvx dev-ready upgrade path/to/project --dry-run  # preview; writes nothing
```

`check` is read-only and offline. `upgrade` preserves immutable Base Provenance
and upstream application content while advancing Overlay Currency. It
re-applies only unmodified overlay-managed whole files, removes untouched
obsolete managed files, preserves user-modified files, and rolls the complete
plan back on failure. Both commands default to the current directory when
`PATH` is omitted.

Then follow the printed next steps (typically `docker compose watch` inside the generated project).

During `init`, stderr reports fetch → overlay → verify → finalize progress: a
spinner on a TTY and stable plain lines when redirected. Stdout retains the
final report. Finalization uses a same-filesystem atomic directory rename, so a
failure never exposes a partial target.

Exit codes: 0 success; 1 unexpected error or user abort; 2 argument error; 3 network/fetch failure; 4 target directory conflict; 5 structural verification failure; 6 stamp missing or invalid; 7 drift detected; 8 upgrade not supported (pre-v3 stamp; projects generated before v0.6); 9 upgrade failed (rolled back).

## How it works

The CLI ships with a lockfile (`manifest.json`) pinning the upstream template commit. Generation fetches that exact snapshot, applies the overlay with variable substitution, verifies the result structurally — all inside staging beside the destination — and only then commits it with one atomic directory rename. The pin is kept current by a weekly CI job that opens bump PRs, each validated by actually generating and booting a project with Docker Compose.

## Links

- Source & issues: <https://github.com/MoofonLi/dev-ready>
- CLI spec, architecture, and ADRs: <https://github.com/MoofonLi/dev-ready/tree/main/docs>

## License

MIT. Generated projects include content derived from fastapi/full-stack-fastapi-template (MIT); see [THIRD_PARTY_NOTICES.md](https://github.com/MoofonLi/dev-ready/blob/main/THIRD_PARTY_NOTICES.md).
