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
- A named Engineering Flow, chosen first, from two selectable methods:
  `mattpocock`: “A user-driven Engineering Flow whose steps stay in one working session.”
  or `superpowers`: “A model-driven Engineering Flow whose implementation can fan out across fresh subagents.”
- A lean Default Set: that Engineering Flow plus the project’s own architecture
  and requirements skeletons. Every Enhancement is off by default.
- A setup step in every project, so the login, email, and error reporting can
  be configured without reading `.env` by hand.
- Optional Enhancements selected through Dev, Security, Quality, Design, and
  Token Optimize Categories. A selected Enhancement adds its guidance inside the
  loop step that acts on it.
- An `AGENTS.md` that is the project’s standards source: its stack, the exact
  test, lint, format, and type-check commands, and the rules no tool enforces.
- Optional Agent Targets. dev-ready declares one for every coding agent that its
  pinned reference list gives a project-level directory of its own, held to that
  list by CI. Each selected target receives one Skill Link per skill — machine-local
  and excluded from version control. A cloned project needs one
  `uvx dev-ready upgrade` before its agent sees anything.
- Project-level `.mcp.json` only when a selected Enhancement needs it.
- A generated `.env` of per-project random secrets that git ignores, and a
  project that tells you its default administrator login and where that password
  lives.
- A `.dev-ready.json` stamp recording immutable Base Provenance and current
  Overlay Currency.

## The development workflow you get

Every project is built around a named Engineering Flow. `setup-project`
configures the login and email first, then the agent grills the request against
the project’s own architecture and requirements documents, writes a durable spec
you approve, cuts it into tracer-bullet tickets with declared file footprints,
and implements one ticket at a time test-first, ending in a review against both
the project’s standards and the spec. Each step leaves a committed artifact
behind. Full description:
<https://github.com/MoofonLi/dev-ready#the-development-workflow-you-get>.

## Requirements

- Python 3.12 or newer
- git
- Network access to github.com during generation
- A filesystem that can hold links, unless no Agent Target is selected
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

Interactive `init` asks the Engineering Flow first, then each optional
Category, then Agent Targets. Enter through all of them gives the Default Set.
`--yes` accepts the lean Default Set. Use `--categories all` for every
Enhancement. Category selection accepts `all`, `none`, or comma-separated
identifiers through `--categories`, `--dev`, `--security`, `--quality`,
`--design`, and `--token-optimize`; `--flow` names the mandatory Engineering
Flow (`mattpocock` or `superpowers`) and `--agents` independently selects Agent
Targets. `--development-loop` is a permanently accepted alias for `--flow`. `--agents` defaults to `claude`,
as does `--yes`; `--agents all` selects every declared target.

| Category | Enhancement identifiers |
|---|---|
| Dev | none currently; the Engineering Flow is always generated |
| Security | `security-audit` |
| Quality | `react-doctor`, `webapp-testing` |
| Design | comma-separated ids, `all`, or `none` (e.g. `frontend-design`, `design-stripe`, `design-linear`) |
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
- v0.12 overview: <https://github.com/MoofonLi/dev-ready/blob/main/docs/version_overview/v0.12-overview.md>

## License

MIT. Generated projects include third-party content; see
[THIRD_PARTY_NOTICES.md](https://github.com/MoofonLi/dev-ready/blob/main/THIRD_PARTY_NOTICES.md).
