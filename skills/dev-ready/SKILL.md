---
name: dev-ready
description: Scaffold a new AI-development-ready FastAPI project with `dev-ready init`. Use when the user asks to start, initialize, generate, or scaffold a FastAPI full-stack project and wants safe non-interactive Category, Catalog Item, and Agent Target selection.
---

# Initialize a dev-ready project

Use `uvx dev-ready init` only for creating a new project. Do not use it to modify an existing project.

Install this repository skill directly with the cross-agent skills CLI:

```shell
npx skills add MoofonLi/dev-ready --skill dev-ready
```

The installed skill source is `skills/dev-ready/SKILL.md`.

## 1. Resolve the destination safely

Choose a valid project name using letters, digits, `.`, `_`, or `-`, starting with a letter or digit. Resolve the exact `--dir` path before running anything.

Inspect the destination first. If it exists and is non-empty, stop and ask the user to choose another destination or resolve the existing content themselves. Do not delete, empty, overwrite, or automatically retry into a non-empty target.

## 2. Choose Categories, items, and Agent Targets

Always use `--yes` for agent-driven, non-interactive generation.

With no selection flags, `--yes` accepts the lean Default Set: the mandatory
Spec Loop with no optional Enhancements. Every project also receives
architecture and requirements skeletons as generation infrastructure. Select
user-facing Categories with `--categories IDS`. Narrow Enhancements within
each selected Category with `--dev`, `--security`, `--quality`, `--design`, or
`--token-optimize`. Choose the mandatory loop with `--development-loop ID` if
the manifest offers more than one. Select native Agent Target configuration
independently with `--agents IDS`.

Every selection flag accepts:

- `all` selects every current Enhancement on that flag.
- `none` selects no Category, item, or Agent Target on that flag.
- A comma-separated list selects those ids. Do not add spaces inside the list.

Current Category ids: `dev`, `security`, `quality`, `design`, `token-optimize`.

Current development loop ids: `spec-loop` (mandatory; select on the structural
`--development-loop` axis, not as a `--dev` Enhancement).

Current dev item ids: (none).

Current security item ids: `security-audit`.

Current quality item ids: `react-doctor`, `webapp-testing`.

Current design item ids: `frontend-design`, `design-stripe`, `design-linear`.

Current token-optimize item ids: `caveman`, `code-memory`.

Current Agent Target ids: `adal`, `aider-desk`, `astrbot`, `augment`, `autohand-code`, `bob`, `claude`, `codearts-agent`, `codebuddy`, `codemaker`, `codestudio`, `command-code`, `continue`, `cortex`, `crush`, `devin`, `droid`, `eve`, `forgecode`, `goose`, `grok`, `hermes-agent`, `iflow-cli`, `inference-sh`, `jazz`, `junie`, `kilo`, `kimchi`, `kiro-cli`, `kode`, `lingma`, `mcpjam`, `minimax-code`, `mistral-vibe`, `moxby`, `mux`, `neovate`, `ona`, `openclaw`, `openhands`, `pi`, `pochi`, `qoder`, `qoder-cn`, `qwen-code`, `reasonix`, `roo`, `rovodev`, `tabnine-cli`, `terramind`, `tinycloud`, `trae`, `trae-cn`, `windsurf`, `zcode`, `zencoder`, `zenflow`.

Every generated project resolves `spec-loop`; `--categories none` and
`--dev none` decline Enhancements without removing it. The former selectable
ids `spec-loop`, `tdd`, `diagnosing-bugs`, `code-review`, and `setup-all` now
exit 2 when passed to `--dev`, because their content is part of the mandatory
Dev development loop. Treat the resolved selection shown in the report and
stamp as authoritative.

Unknown Category ids, unknown item ids, unknown Agent Target ids, and conflicting
flags are exit 2 failures; surface the error instead of guessing a replacement.
For example, `--design design-stripe` conflicts with `--categories dev` because
Design was not selected.

The Component-shaped flags `--skills`, `--mcp`, `--no-skills`, `--no-mcp`, and
`--no-docs` were removed. Use the Category flags instead. `--no-handoff` and
`--no-agents` were also removed because dev-ready no longer generates the
Handoff Protocol. Passing any removed flag exits 2; do not retry with an alias.

## 3. Form one command

Lean Default Set:

```shell
uvx dev-ready init my-app --yes --dir ./my-app
```

Explicit whole-catalog selection:

```shell
uvx dev-ready init full-app --yes --categories all --agents all --dir ./full-app
```

No optional components:

```shell
uvx dev-ready init minimal-app --yes --categories none --agents none --dir ./minimal-app
```

Mixed Enhancement selection:

```shell
uvx dev-ready init focused-app --yes --development-loop spec-loop --categories dev,design,token-optimize --dev none --design frontend-design,design-stripe --token-optimize code-memory --agents claude --dir ./focused-app
```

Run exactly one selected command. Do not invent flags for language, overwriting, or cleanup.

## 4. Handle the result

Treat only exit 0 as success. Every nonzero exit is a failure:

- exit 1: abort or unexpected generation error;
- exit 2: invalid arguments, unknown item id, or conflicting flags;
- exit 3: network, Git, or pinned-template fetch failure;
- exit 4: target conflict, including an existing non-empty target;
- exit 5: generated project failed verification.

Report the command, exit code, and error text. Do not hide the failure, weaken the selection, or retry destructively.

After exit 0, verify that the requested target exists, contains `.dev-ready.json`, and matches the final generation report. Check representative selected outputs when relevant, such as `docs/architecture.md`, `.claude/skills/to-spec/SKILL.md`, or `.mcp.json`. Only then report generation as successful and present the CLI's next steps.
