# dev-ready

[![CI](https://github.com/MoofonLi/dev-ready/actions/workflows/ci.yml/badge.svg)](https://github.com/MoofonLi/dev-ready/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/dev-ready)](https://pypi.org/project/dev-ready/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

繁體中文導覽：[README.zh-TW.md](README.zh-TW.md)

Scaffold a production-grade, AI-development-ready FastAPI + React project in
one command:

```bash
uvx dev-ready init my-app
```

The upstream template is pinned to a CI-verified commit, never an untested
“latest.” Generation is all-or-nothing: if any step fails, the target directory
is never exposed as a partial project.

## What you get

A generated project based on
[fastapi/full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template)
(FastAPI, React, SQLModel, PostgreSQL, and Docker Compose), plus an AI tooling
overlay:

- Canonical project instructions in `AGENTS.md` and Canonical Content under
  `.agents/skills/`. Cursor, Codex, Cline, Zed, OpenCode, and other
  standard-compliant agents read these locations without an Agent Target.
- One named Engineering Flow, chosen first. Today that is Matt Pocock’s; two
  more are announced as coming soon. The flow is the method the project is
  built around — grilling, durable specs, tracer-bullet tickets, implementation,
  TDD, diagnosis, two-axis review, and architecture cleanup.
- A lean Default Set: that Engineering Flow plus the project’s own
  `docs/architecture.md` and `docs/requirements.md` skeletons. Every Enhancement
  is off by default.
- A setup step in every project, so the login, email, and error reporting can
  be configured without reading `.env` by hand.
- Optional Enhancements selected by Category: Dev, Security, Quality, Design,
  and Token Optimize. The catalog includes security auditing, React analysis,
  browser testing, frontend-design guidance, design-system references, concise
  agent guidance, and codebase memory. A selected Enhancement adds its guidance
  inside the loop step that acts on it, so the agent meets it while doing the
  work rather than having to go looking.
- An `AGENTS.md` that is the project’s standards source: the stack it actually
  uses, the exact commands to test, lint, format, and type-check both halves of
  it, and the rules no tool enforces.
- Optional Agent Targets. dev-ready declares one for every coding agent that its
  pinned reference list gives a project-level directory of its own, and CI fails
  when the two diverge; the authoritative list is `agent_targets` in
  [`src/dev_ready/manifest.json`](src/dev_ready/manifest.json). Each selected
  target receives ordinary Pointer Stubs at its native discovery path; the stubs
  are neither symbolic links nor copies of Canonical Content.
- `.mcp.json` only when a selected Enhancement needs project-level MCP
  configuration.
- Secret hygiene from the first commit: the generated `.env` holds per-project
  random secrets and is ignored by git, and the project tells you its default
  administrator login and where that password lives.
- A `.dev-ready.json` stamp recording immutable Base Provenance and current
  Overlay Currency: Categories, development loop, Enhancements, Agent Targets,
  pins, and the managed-file inventory.

Every project also receives a project-specific `README.md`. Upstream
repository-maintenance files such as its contributing guide, release notes and
screenshots are pruned; the deployment workflows upstream wrote for downstream
users are kept.

## The development workflow you get

Every generated project is built around a named Engineering Flow, chosen first.
Today that is Matt Pocock’s; two more are announced as coming soon. The agent
reads the flow from `AGENTS.md` on the first turn of every session.

Before any feature work, **`setup-project`** configures the login, email, and
error reporting so nobody has to edit `.env` by hand.

Then four feature steps, each leaving something behind in your repository:

1. **`grill-with-docs`** — the agent interrogates what you are asking for
   against the project’s own `docs/architecture.md` and `docs/requirements.md`
   instead of starting to type. *Leaves behind:* anything settled that outlives
   the feature, written into those documents.
2. **`to-spec`** — a durable spec you approve before any code exists. *Leaves
   behind:* a committed document that is the only record of the work that
   survives it, and the thing the code is later reviewed against.
3. **`to-tickets`** — the spec is cut into tracer-bullet tickets, each declaring
   what blocks it, which files it may touch, and whether it is safe to run in
   parallel. *Leaves behind:* one file per ticket, wherever your tracker
   configuration says they live.
4. **`implement`** — one ticket at a time, test-first: a failing test, the
   smallest change that passes it, then cleanup. Diagnosis is an action inside
   this step when something breaks, and it ends with a two-axis review — does
   this follow the project’s documented standards, and does it do what the spec
   asked? *Leaves behind:* the change, its tests, and a review pass, inside the
   ticket’s declared footprint.

A change that adds no observable behaviour can start at `implement`; the
generated `AGENTS.md` and `docs/agents/mattpocock.md` carry the full chain.

Between features, `improve-codebase-architecture` is there for the structural
work that is nobody’s ticket.

## Requirements

- Python 3.12 or newer (uv can install it automatically)
- git (Copier fetches the pinned template with git)
- Network access to github.com during generation
- Docker only to run the generated project, not to generate it

## Installation

No installation is needed with [uv](https://docs.astral.sh/uv/):

```bash
uvx dev-ready init my-app
```

Or install with pip:

```bash
pip install dev-ready
dev-ready init my-app
```

### Install the agent skill

Install the repository’s cross-agent generation skill:

```bash
npx skills add MoofonLi/dev-ready --skill dev-ready
```

The source is [skills/dev-ready/SKILL.md](skills/dev-ready/SKILL.md). To inspect
the repository’s discoverable skills before installing, run:

```bash
npx skills add MoofonLi/dev-ready --list
```

Then ask your agent: “Scaffold a FastAPI project with dev-ready named my-app.”
The skill inspects the destination, resolves Category selections, runs one
non-interactive initialization command, and verifies the generated stamp.

Also as a plugin, for Claude Code and Codex:

```text
/plugin marketplace add MoofonLi/dev-ready
/plugin install dev-ready@dev-ready
```

```text
codex plugin marketplace add MoofonLi/dev-ready
```

After the Codex catalog is added, install `dev-ready` from it.

For installation or generation problems, [open an issue](https://github.com/MoofonLi/dev-ready/issues).

## Usage

Interactive initialization prompts for anything not supplied:

```bash
uvx dev-ready init
```

It asks the Engineering Flow first, then each optional Category, then Agent
Targets. Enter through all of them gives the Default Set.

Accept the lean Default Set without prompts:

```bash
uvx dev-ready init my-app --yes
```

Select explicit Categories and Enhancements:

```bash
uvx dev-ready init my-app --yes --categories dev,token-optimize --dev none --token-optimize caveman,code-memory --agents claude,windsurf
```

The Category flags are:

| Flag | Selects |
|---|---|
| `--categories` | `dev`, `security`, `quality`, `design`, `token-optimize`, `all`, or `none` |
| `--flow` | Mandatory Engineering Flow; currently `mattpocock` |
| `--dev` | Dev Enhancements; the Category currently offers none |
| `--security` | `security-audit` |
| `--quality` | `react-doctor`, `webapp-testing` |
| `--design` | comma-separated ids, `all`, or `none` (e.g. `frontend-design`, `design-stripe`, `design-linear`) |
| `--token-optimize` | `caveman`, `code-memory` |
| `--agents` | Agent Targets by identifier, `all`, or `none` |

`--development-loop` is a permanently accepted alias for `--flow`.

List flags accept `all`, `none`, or comma-separated identifiers. Dev remains
selected because every project has an Engineering Flow. Use
`--categories all` for the whole catalog; `--yes` by itself accepts only the
lean Default Set.

`--agents` defaults to `claude`, and so does `--yes`. `--agents all` selects
every declared target, which is a great many Pointer Stub files — name the
targets you want instead.

The previous Component-shaped flags (`--skills`, `--no-skills`, `--mcp`,
`--no-mcp`, and `--no-docs`) now exit 2 and name their Category-shaped
replacement. `--no-handoff` and `--no-agents` also exit 2 because the generated
Handoff Protocol was removed.

Inspect and upgrade generated projects:

```bash
uvx dev-ready check path/to/project
uvx dev-ready check path/to/project --json
uvx dev-ready upgrade path/to/project --dry-run
uvx dev-ready upgrade path/to/project
```

`check` is read-only and offline. `upgrade` preserves immutable Base Provenance
and upstream application content while advancing Overlay Currency. It replaces
only unmodified managed whole files, transactionally deletes untouched obsolete
files, preserves user-edited files with a divergence report, and rolls the
complete plan back on failure.

A v0.8 project upgrades without new input: its stamp advances to version 5,
Categories and the mandatory Engineering Flow are recorded, untouched retired
files are deleted, and edited retired files survive unchanged. A repeat upgrade
is a no-op.

### Exit codes

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | Unexpected error or user abort |
| 2 | Invalid arguments |
| 3 | Network or fetch failure |
| 4 | Target directory conflict |
| 5 | Generated output failed structural verification |
| 6 | Stamp missing or invalid |
| 7 | Drift detected by `check` |
| 8 | Upgrade unsupported for a pre-v3 stamp |
| 9 | Upgrade failed and was rolled back |

See the [full CLI contract](docs/cli-spec.md).

## How it works

1. Collect and confirm the project name, Engineering Flow, Enhancements, and
   Agent Targets. `--yes` skips prompts.
2. Fetch the upstream template at the commit pinned in
   `src/dev_ready/manifest.json` into staging beside the destination.
3. Apply the selected overlay with template-variable substitution.
4. Verify the upstream structure, Canonical Content, and mandatory Engineering
   Flow.
5. Revalidate the destination and finalize with one same-filesystem atomic
   directory rename.

During generation, stderr reports fetch → overlay → verify → finalize progress;
stdout retains the final report. Weekly upstream-pin pull requests are validated
by generating and booting a real project before merge.

## Development

```bash
uv sync --dev
uv run dev-ready init demo --yes
uv run pytest
uv run ruff check .
uv run pytest -m network
```

This repository is developed with the Spec Loop defined in [AGENTS.md](AGENTS.md):
grill with the durable docs, write an accepted spec, dispatch tracer-bullet
tickets, then implement test-first with code review. Releases are tag-driven
and published to PyPI through trusted publishing; see
[docs/releasing.md](docs/releasing.md).

## Roadmap

v0.11 shipped the Engineering Flow, the setup step, the full Design Reference
set, and plugin distribution. Next is delivery and a second flow. v1.0’s
second template remains gated on attributable evidence of real external use. See
the [v0.11 overview](docs/version_overview/v0.11-overview.md).

## License

MIT — see [LICENSE](LICENSE). Generated projects include third-party content;
see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
