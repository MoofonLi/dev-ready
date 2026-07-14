# CLI Specification — dev-ready

Status: Draft v0.1. This replaces the REST `api-spec.yaml` from the original bootstrap plan: dev-ready is a CLI tool with no HTTP API. (Generated projects expose their own OpenAPI docs via FastAPI.)

## Commands

### `dev-ready init [PROJECT_NAME]`

Generate a new project.

| Flag | Type | Default | Description |
|---|---|---|---|
| `--yes` / `-y` | bool | false | Accept all defaults, no prompts |
| `--dir PATH` | path | `./PROJECT_NAME` | Target directory (must not exist or be empty) |
| `--no-skills` | bool | false | Skip Claude Code skills overlay |
| `--no-mcp` | bool | false | Skip MCP server configuration overlay |
| `--no-docs` | bool | false | Skip design-doc templates overlay |

Exit codes: 0 success; 1 unexpected error or user abort; 2 invalid arguments; 3 network/fetch failure; 4 target directory conflict.

### `dev-ready --version` / `dev-ready --help`

Standard version and help output.

## Interactive Prompt Flow (default path)

1. Project name (if not given as argument)
2. Overlay component selection (skills / MCP / docs — multi-select, all on by default; skipped entirely if any `--no-skills`/`--no-mcp`/`--no-docs` flag was passed)
3. Confirmation summary before writing anything

All answers collect into a single `Answers` model shared with the flag-based path.

Declining the confirmation, or cancelling any prompt (Ctrl-C), prints `aborted: nothing was written` to stderr and exits 1 — nothing has been written at that point by construction. `--yes` bypasses every prompt in this flow, including confirmation. A non-TTY stdin with missing inputs and no `--yes` fails fast with an invalid-arguments error (exit 2) instead of hanging.

## Planned (not in v0.1)

- `dev-ready check` — validate an existing generated project against the manifest
- `dev-ready upgrade` — re-apply a newer overlay to an existing project
