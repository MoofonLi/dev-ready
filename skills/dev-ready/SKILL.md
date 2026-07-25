---
name: dev-ready
description: Scaffold a new AI-development-ready FastAPI project with `dev-ready init`. Use when the user asks to start, initialize, generate, or scaffold a FastAPI full-stack project and wants safe non-interactive component and catalog-item selection.
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

## 2. Choose components and items

Always use `--yes` for agent-driven, non-interactive generation.

Top-level components:

- Skills and MCP are item catalogs controlled by `--skills IDS` and `--mcp IDS`.
- Docs and the Handoff Protocol are enabled by default; disable them with `--no-docs` and `--no-agents`.
- `--no-skills` aliases `--skills none`; `--no-mcp` aliases `--mcp none`.

Selection values:

- Omitted or `all` selects every current item.
- `none` selects no item in that catalog.
- A comma-separated list selects those ids. Do not add spaces inside the list.

Current skills ids: `project-orientation`, `react-doctor`, `caveman`, `security-audit`, `tdd`, `diagnosing-bugs`, `code-review`, `spec-loop`, `webapp-testing`, `frontend-design`.

Current MCP ids: `mcp-config`, `code-memory`.

Selecting `spec-loop` automatically resolves `tdd`, `diagnosing-bugs`, and `code-review`. Treat the resolved selection shown in the report and stamp as authoritative.

Do not combine an alias with a conflicting explicit value, such as `--no-skills --skills spec-loop`. Unknown item ids and conflicting flags are exit 2 failures; surface the error instead of guessing a replacement.

## 3. Form one command

All/default selection:

```shell
uvx dev-ready init my-app --yes --skills all --mcp all --dir ./my-app
```

No optional components:

```shell
uvx dev-ready init minimal-app --yes --skills none --mcp none --no-docs --no-agents --dir ./minimal-app
```

Mixed standalone Spec Loop selection:

```shell
uvx dev-ready init focused-app --yes --skills spec-loop,frontend-design --mcp code-memory --no-agents --dir ./focused-app
```

Run exactly one selected command. Do not invent flags for language, render targets, overwriting, or cleanup.

## 4. Handle the result

Treat only exit 0 as success. Every nonzero exit is a failure:

- exit 1: abort or unexpected generation error;
- exit 2: invalid arguments, unknown item id, or conflicting flags;
- exit 3: network, Git, or pinned-template fetch failure;
- exit 4: target conflict, including an existing non-empty target;
- exit 5: generated project failed verification.

Report the command, exit code, and error text. Do not hide the failure, weaken the selection, or retry destructively.

After exit 0, verify that the requested target exists, contains `.dev-ready.json`, and matches the final generation report. Check representative selected outputs when relevant, such as `docs/handoffs/protocol.yaml`, `docs/architecture.md`, `.claude/skills/to-spec/SKILL.md`, or `.mcp.json`. Only then report generation as successful and present the CLI's next steps.
