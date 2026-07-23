# CLI Specification — dev-ready

Status: Draft v0.1. This replaces the REST `api-spec.yaml` from the original bootstrap plan: dev-ready is a CLI tool with no HTTP API. (Generated projects expose their own OpenAPI docs via FastAPI.)

## Commands

### `dev-ready init [PROJECT_NAME]`

Generate a new project.

| Flag | Type | Default | Description |
|---|---|---|---|
| `--yes` / `-y` | bool | false | Accept all defaults, no prompts |
| `--dir PATH` | path | `./PROJECT_NAME` | Target directory (must not exist or be empty) |
| `--skills IDS` | string | `all` | Item selection for skills: comma-separated ids, `all`, or `none` |
| `--mcp IDS` | string | `all` | Item selection for mcp: comma-separated ids, `all`, or `none` |
| `--no-skills` | bool | false | Skip Claude Code skills overlay (alias for `--skills none`) |
| `--no-mcp` | bool | false | Skip MCP server configuration overlay (alias for `--mcp none`) |
| `--no-docs` | bool | false | Skip design-doc templates overlay |
| `--no-agents` | bool | false | Skip the agent-team handoff scaffold overlay (`docs/handoffs/`) |

Unknown item ids in `--skills` or `--mcp` fail fast with an invalid-arguments error (exit 2) listing valid item ids. Conflicting flags (e.g. `--no-skills` with `--skills <id>`) exit 2.

Exit codes: 0 success; 1 unexpected error or user abort; 2 invalid arguments; 3 network/fetch failure; 4 target directory conflict; 5 generated project failed verification; 6 stamp missing or invalid; 7 drift detected.

### `dev-ready check [PATH]`

Inspect an existing generated project directory against its `.dev-ready.json` stamp and the running CLI manifest. Read-only operation.

| Flag | Type | Default | Description |
|---|---|---|---|
| `PATH` | path | `.` | Target project directory to check |
| `--json` | bool | false | Output report in JSON format |

Exit codes: 0 clean (no drift); 6 stamp missing or unparseable/invalid (including projects generated before v0.3); 7 drift detected.

### `dev-ready --version` / `dev-ready --help`

Standard version and help output.

## Interactive Prompt Flow (default path)

1. Project name (if not given as argument)
2. Level-1 component selection (skills / MCP / docs / agents — multi-select, all on by default)
3. Level-2 item selection for `skills` and `mcp` components chosen at level 1 (multi-select of component items, all on by default; plain Enter accepts all items)
4. Confirmation summary before writing anything

Skipped entirely if any component or item flag (`--skills`, `--mcp`, `--no-skills`, `--no-mcp`, `--no-docs`, `--no-agents`) was passed.

All answers collect into a single `Answers` model shared with the flag-based path.

Declining the confirmation, or cancelling any prompt (Ctrl-C), prints `aborted: nothing was written` to stderr and exits 1 — nothing has been written at that point by construction. `--yes` bypasses every prompt in this flow, including confirmation. A non-TTY stdin with missing inputs and no `--yes` fails fast with an invalid-arguments error (exit 2) instead of hanging.

**Windows compatibility:** interactive prompts are tested against Windows Terminal. Legacy `cmd.exe` may render the checkbox prompt incorrectly (missing VT/ANSI support). In environments where terminal support is uncertain, use `--yes` with explicit `--no-skills`/`--no-mcp`/`--no-docs`/`--no-agents` flags instead of relying on prompts.

## Planned (see docs/version-plan.md)

- v0.6 — `dev-ready upgrade` (re-apply overlay-managed files only).


