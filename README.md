# dev-ready

[![CI](https://github.com/MoofonLi/dev-ready/actions/workflows/ci.yml/badge.svg)](https://github.com/MoofonLi/dev-ready/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/dev-ready)](https://pypi.org/project/dev-ready/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

繁體中文導覽：[README.zh-TW.md](README.zh-TW.md)

Scaffold a production-grade, AI-development-ready FastAPI + React project in one command:

```bash
uvx dev-ready init my-app
```

![A recorded interactive `dev-ready init`: Engineering Flow comparison, Category prompts, confirmation, progress stages, and the generation report.](docs/assets/demo.gif)

## What a generated project receives

| Layer | Contents |
|---|---|
| Base | Every generated project is FastAPI, React, PostgreSQL, and Docker Compose at a pinned commit of [fastapi/full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template). |
| Canonical Content | `AGENTS.md` and skills under `.agents/skills/`. Standard-compliant agents read those paths directly. |
| Engineering Flow | One named method, chosen first: `mattpocock`, `superpowers`, or `addyosmani`. `--yes` selects `mattpocock`. |
| Enhancements | Optional items by Category — Dev, Security, Quality, Design, Token Optimize. The Default Set selects none. |
| Agent Targets | Skill Links at each selected agent's native path, plus a `.dev-ready.json` stamp. Links are machine-local; `upgrade` recreates them. |

## Quickstart

```bash
uvx dev-ready init my-app
cd my-app
```

Then ask your coding agent to run `/setup-project` before the first start.

## Engineering Flows

Interactive `init` shows this comparison, then Category prompts, a confirmation, fetch → overlay → verify → finalize, and a report.

**Matt Pocock's skills** — A user-driven Engineering Flow whose steps stay in one working session.

- Choose this flow when you want to start each `chain` entry yourself.
- Choose it when the work's shape needs `grill-with-docs`, `grilling`, or `domain-modeling` before specification.
- Choose it when one session should carry the work through `to-spec`, `to-tickets`, and `implement`.

**Superpowers** — A model-driven Engineering Flow whose implementation can fan out across fresh subagents.

- Choose this flow when its model-driven `invocation` should start each chain entry after setup.
- Choose it when implementation should fan out through `subagent-driven-development` or `executing-plans`.
- Choose it when `verification-before-completion` should run before work is declared complete.

**Addy Osmani's Agent Skills** — A model-driven Engineering Flow spanning specification, implementation, production readiness, and shipping.

- Choose this flow when `spec-driven-development` should produce a written spec before any code exists.
- Choose it when the work runs to production and wants `security-and-hardening`, `performance-optimization`, and `observability-and-instrumentation` beside the build steps.
- Choose it when its `chain` should end at `shipping-and-launch` rather than at a finished branch.

## Requirements

Python 3.12+, git, network to github.com during generation, and a filesystem that can hold links unless no Agent Target is selected. Docker is only needed to run the generated project.

## Install the agent skill

```bash
npx skills add MoofonLi/dev-ready --skill dev-ready
```

The source is [skills/dev-ready/SKILL.md](skills/dev-ready/SKILL.md). Inspect discoverable skills first:

```bash
npx skills add MoofonLi/dev-ready --list
```

Then ask your agent: “Scaffold a FastAPI project with dev-ready named my-app.” Also as a plugin: `/plugin marketplace add MoofonLi/dev-ready` then `/plugin install dev-ready@dev-ready`, or `codex plugin marketplace add MoofonLi/dev-ready`. Problems: [open an issue](https://github.com/MoofonLi/dev-ready/issues).

## Development

```bash
uv sync --dev
uv run pytest
uv run ruff check .
```

See [AGENTS.md](AGENTS.md). Full CLI contract: [docs/cli-spec.md](docs/cli-spec.md). Previous version: [v0.12 overview](docs/version_overview/v0.12-overview.md).

## License

MIT — see [LICENSE](LICENSE). Generated projects include third-party content; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
