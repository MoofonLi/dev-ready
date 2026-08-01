# dev-ready

繁體中文導覽：<https://github.com/MoofonLi/dev-ready/blob/main/README.zh-TW.md>

Scaffold a production-grade, AI-development-ready FastAPI + React project in
one command:

```bash
uvx dev-ready init my-app
```

The upstream template is pinned to a CI-verified commit, never an untested
“latest.” Generation is all-or-nothing: failures never expose a partial target.

## What you get

A generated project based on
[fastapi/full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template)
(FastAPI, React, SQLModel, PostgreSQL, and Docker Compose), plus:

- Canonical project instructions in `AGENTS.md` and skills under
  `.agents/skills/`, readable directly by Cursor, Codex, Cline, Zed, OpenCode,
  and other standard-compliant agents.
- A mandatory Spec Loop covering grilling, durable specs, tracer-bullet tickets,
  implementation, TDD, diagnosis, two-axis review, and architecture cleanup.
- A lean Default Set: the Spec Loop plus the project’s own architecture and
  requirements skeletons. Every Enhancement is off by default.
- Optional Enhancements selected through Dev, Security, Quality, Design, and
  Token Optimize Categories.
- Optional Claude Code and Windsurf Agent Targets, rendered as Pointer Stubs
  over the one Canonical Content copy—not symbolic links or content copies.
- Project-level `.mcp.json` only when a selected Enhancement needs it.
- A `.dev-ready.json` stamp recording immutable Base Provenance and current
  Overlay Currency.

v0.9 no longer generates the Handoff Protocol’s seven-role multi-agent
scaffold, Protocol Configuration, gate templates, ticket scaffold, or execution
report. Generated projects use the Spec Loop without a second process layer.

## Requirements

- Python 3.12 or newer
- git
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

```bash
npx skills add MoofonLi/dev-ready --skill dev-ready
```

The source is
[skills/dev-ready/SKILL.md](https://github.com/MoofonLi/dev-ready/blob/main/skills/dev-ready/SKILL.md).
Inspect the repository’s discoverable skills before installing with:

```bash
npx skills add MoofonLi/dev-ready --list
```

The skill resolves Category selections, runs one non-interactive initialization
command, and verifies the generated stamp.

Then ask your agent: “Scaffold a FastAPI project with dev-ready named my-app.”

For installation or generation problems, [open an issue](https://github.com/MoofonLi/dev-ready/issues).

## Usage

```bash
uvx dev-ready init
uvx dev-ready init my-app --yes
uvx dev-ready init my-app --yes --categories dev,token-optimize --dev none --token-optimize caveman,code-memory --agents claude,windsurf
```

`--yes` accepts the lean Default Set. Use `--categories all` for every
Enhancement. Category selection accepts `all`, `none`, or comma-separated
identifiers through `--categories`, `--dev`, `--security`, `--quality`,
`--design`, and `--token-optimize`; `--development-loop` names the mandatory
loop and `--agents` independently selects Agent Targets.

| Category | Enhancement identifiers |
|---|---|
| Dev | `setup-all` |
| Security | `security-audit` |
| Quality | `react-doctor`, `webapp-testing` |
| Design | `frontend-design`, `design-stripe`, `design-linear` |
| Token Optimize | `caveman`, `code-memory` |

The previous Component-shaped flags (`--skills`, `--no-skills`, `--mcp`,
`--no-mcp`, and `--no-docs`) now exit 2 and name their Category-shaped
replacement. `--no-handoff` and `--no-agents` exit 2 because the generated
Handoff Protocol was removed.

```bash
uvx dev-ready check path/to/project
uvx dev-ready check path/to/project --json
uvx dev-ready upgrade path/to/project --dry-run
uvx dev-ready upgrade path/to/project
```

`check` is read-only and offline. `upgrade` preserves immutable Base Provenance
and upstream application content while advancing Overlay Currency. A v0.8
project migrates to stamp version 5 without new input: untouched retired managed
files are deleted transactionally, edited files are preserved and reported,
failures roll back, and a repeat upgrade is a no-op.

During `init`, stderr reports fetch → overlay → verify → finalize progress;
stdout retains the final report. Finalization uses a same-filesystem atomic
directory rename, so failure never exposes a partial target.

Exit codes: 0 success; 1 unexpected error or user abort; 2 invalid arguments; 3
network/fetch failure; 4 target conflict; 5 structural verification failure; 6
stamp missing or invalid; 7 drift detected; 8 pre-v3 upgrade unsupported; 9
upgrade failed and rolled back.

## Links

- Source and issues: <https://github.com/MoofonLi/dev-ready>
- CLI spec, architecture, and ADRs: <https://github.com/MoofonLi/dev-ready/tree/main/docs>
- v0.9 overview: <https://github.com/MoofonLi/dev-ready/blob/main/docs/version_overview/v0.9-overview.md>

## License

MIT. Generated projects include third-party content; see
[THIRD_PARTY_NOTICES.md](https://github.com/MoofonLi/dev-ready/blob/main/THIRD_PARTY_NOTICES.md).
