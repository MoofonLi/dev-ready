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

Exit codes: 0 success; 1 unexpected error; 2 invalid arguments; 3 network/fetch failure; 4 target directory conflict.

### `dev-ready --version` / `dev-ready --help`

Standard version and help output.

## Interactive Prompt Flow (default path)

1. Project name (if not given as argument)
2. Overlay component selection (skills / MCP / docs — multi-select, all on by default)
3. Confirmation summary before writing anything

All answers collect into a single `Answers` model shared with the flag-based path.

## Planned (not in v0.1)

- `dev-ready check` — validate an existing generated project against the manifest
- `dev-ready upgrade` — re-apply a newer overlay to an existing project
