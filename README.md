# dev-ready

[![CI](https://github.com/MoofonLi/dev-ready/actions/workflows/ci.yml/badge.svg)](https://github.com/MoofonLi/dev-ready/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/dev-ready)](https://pypi.org/project/dev-ready/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

繁體中文導覽：[README.zh-TW.md](README.zh-TW.md)

Scaffold a production-grade, AI-development-ready FastAPI + React project in one command:

```bash
uvx dev-ready init my-app
```

No half-finished output, no untested "latest": the upstream template is pinned to a CI-verified commit, and generation is all-or-nothing — if any step fails, your target directory is never touched.

## What you get

A generated project based on [fastapi/full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template) (FastAPI, React, SQLModel, PostgreSQL, Docker Compose), plus an AI tooling overlay so it works well with coding agents out of the box:

- Canonical project instructions in `AGENTS.md`, including Karpathy-derived
  development guardrails. Canonical skills are written once under
  `.agents/skills/`, so standard-compliant agents such as Cursor, Codex, Cline,
  Zed, and OpenCode need no Agent Target selection.
- A 10/10 skills catalog with item-level selection. The `spec-loop` bundle adds
  planning, durable specs, tracer-bullet tickets, TDD, review, diagnosis, and
  architecture improvement; selecting it automatically resolves `tdd`,
  `diagnosing-bugs`, and `code-review`.
- Optional Agent Targets for Claude Code and Windsurf. Selected targets receive
  ordinary Pointer Stub files at their native paths that direct them to the one
  Canonical Content copy; the stubs are neither symlinks nor content copies.
- MCP server configuration (`.mcp.json`), including the selectable pinned
  codebase-memory server
- Design-doc templates (`docs/architecture.md`, `docs/requirements.md`)
- A configurable Handoff Protocol under `docs/handoffs/`. Its Protocol
  Configuration, `protocol.yaml`, is the single runtime authority for seven
  stable roles, editable titles/model assignments, handoff order, escalation,
  review gates, and commit authority.
- A `.dev-ready.json` generation stamp recording Base Provenance, selected
  components/items and pins, and the managed overlay inventory

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

The source is [`skills/dev-ready/SKILL.md`](skills/dev-ready/SKILL.md). To
inspect the repository's discoverable skills before installing, run
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
  --dir path/to/target \
  --skills spec-loop,security-audit \
  --mcp code-memory \
  --agents claude,windsurf \
  --no-docs \
  --no-handoff
```

Use `all`, `none`, or comma-separated identifiers with `--skills`, `--mcp`, and
`--agents`. `--no-skills` and `--no-mcp` are aliases for `none`.
`--no-agents` remains a deprecated alias for `--no-handoff` for one version and
emits a warning. During generation, stderr
shows fetch → overlay → verify → finalize progress (a spinner on TTYs and stable
plain lines when redirected); stdout retains the final report.

```bash
# Inspect a generated project against its stamp (read-only and offline)
uvx dev-ready check path/to/project
uvx dev-ready check path/to/project --json

# Preview or apply an overlay-only, transactional upgrade
uvx dev-ready upgrade path/to/project --dry-run
uvx dev-ready upgrade path/to/project
```

`upgrade` preserves the project's immutable Base Provenance and upstream
application content while advancing Overlay Currency. It updates only
unmodified overlay-managed whole files, removes untouched obsolete managed
files, preserves user-modified files, and rolls back the complete plan on
failure. Upgrading a v0.7 project infers Claude Code, migrates untouched skills
to Canonical Content plus Pointer Stubs, and preserves edited files while
reporting any resulting divergence.

### Exit codes

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | Unexpected error or user abort (`aborted: nothing was written`) |
| 2 | Argument error (including missing input in non-TTY environments) |
| 3 | Network / fetch failure |
| 4 | Target directory conflict |
| 5 | Generated output failed structural verification |
| 6 | Stamp missing or invalid |
| 7 | Drift detected by `check` |
| 8 | Upgrade unsupported for a pre-v3 stamp |
| 9 | Upgrade failed and was rolled back |

Full CLI contract: [docs/cli-spec.md](docs/cli-spec.md).

## How it works

1. **Prompt & confirm** — collect answers, show a summary before any network call or write (`--yes` skips this).
2. **Fetch** — run [Copier](https://copier.readthedocs.io/) against the upstream template at the commit pinned in `src/dev_ready/manifest.json` (a lockfile shipped inside the wheel), into a staging directory. Your project name and freshly generated secrets are written into the project's `.env` — no upstream `changethis` placeholders.
3. **Overlay** — apply the AI tooling files with template-variable substitution, still in staging.
4. **Verify** — structural checks against required paths (backend, frontend, compose files, ...).
5. **Finalize** — revalidate the destination and commit staging with one
   same-filesystem atomic directory rename. A failed generation exposes no
   partial target.

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

This repo is developed with the document-driven Handoff Protocol and Spec Loop
defined in [AGENTS.md](AGENTS.md): durable specs, ticket dispatch, one-ticket
test-first execution, Senior review, and independent QA, Security, and SRE
gates.

## Roadmap

v0.8 ships multi-agent render targets. CLI internationalization was withdrawn
on 2026-07-26 — dev-ready's own output stays English, and Traditional Chinese
speakers are served by [README.zh-TW.md](README.zh-TW.md) instead
([ADR-016](docs/decisions/adr-016-language-boundary.md)). v1.0's second template
(Next.js) is gated on attributable external-user evidence or four strictly
increasing adjusted complete UTC weeks of PyPI downloads. See
[the v0.7 overview](docs/version_overview/v0.7-overview.md) for the decidable
gate and evidence fields.

## License

MIT — see [LICENSE](LICENSE). Generated projects include content derived from fastapi/full-stack-fastapi-template (MIT); see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
