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
| `--no-agents` | bool | false | Skip the agent-team handoff scaffold overlay (`docs/handoffs/`) |

Exit codes: 0 success; 1 unexpected error or user abort; 2 invalid arguments; 3 network/fetch failure; 4 target directory conflict; 5 generated project failed verification.

### `dev-ready --version` / `dev-ready --help`

Standard version and help output.

## Interactive Prompt Flow (default path)

1. Project name (if not given as argument)
2. Overlay component selection (skills / MCP / docs / agents — multi-select, all on by default; skipped entirely if any `--no-skills`/`--no-mcp`/`--no-docs`/`--no-agents` flag was passed)
3. Confirmation summary before writing anything

All answers collect into a single `Answers` model shared with the flag-based path.

Declining the confirmation, or cancelling any prompt (Ctrl-C), prints `aborted: nothing was written` to stderr and exits 1 — nothing has been written at that point by construction. `--yes` bypasses every prompt in this flow, including confirmation. A non-TTY stdin with missing inputs and no `--yes` fails fast with an invalid-arguments error (exit 2) instead of hanging.

**Windows compatibility:** interactive prompts are tested against Windows Terminal. Legacy `cmd.exe` may render the checkbox prompt incorrectly (missing VT/ANSI support). In environments where terminal support is uncertain, use `--yes` with explicit `--no-skills`/`--no-mcp`/`--no-docs`/`--no-agents` flags instead of relying on prompts.

## Planned (see docs/version-plan.md)

- v0.3 (FR-14, ADR-010) — item-level selection inside `skills` and `mcp`:
  - `--skills <ids|all|none>` and `--mcp <ids|all|none>` (comma-separated item ids, e.g. `--skills react-doctor,caveman`). Unknown ids exit 2 listing valid ids.
  - `--no-skills` / `--no-mcp` become aliases for `--skills none` / `--mcp none` (backward compatible).
  - Interactive flow gains a second-level multi-select per chosen component, all items on by default (plain Enter reproduces current behavior). `--yes` alone still selects everything.
  - `docs` and `agents` remain boolean flags (single-item components).
- v0.6 — `dev-ready check` (validate an existing generated project against its `.dev-ready.json` stamp and the manifest) and `dev-ready upgrade` (re-apply overlay-managed files only).
