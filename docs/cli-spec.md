# CLI Specification — dev-ready

Status: Current for v0.10 development. This replaces the REST `api-spec.yaml` from the original bootstrap plan: dev-ready is a CLI tool with no HTTP API. (Generated projects expose their own OpenAPI docs via FastAPI.)

## Commands

### `dev-ready init [PROJECT_NAME]`

Generate a new project.

| Flag | Type | Default | Description |
|---|---|---|---|
| `--yes` / `-y` | bool | false | Accept the lean Default Set, no prompts |
| `--dir PATH` | path | `./PROJECT_NAME` | Target directory (must not exist or be empty) |
| `--categories IDS` | string | Default Set; `all` when another selection flag is supplied | Category selection: comma-separated ids, `all`, or `none` |
| `--development-loop ID` | string | `spec-loop` | Mandatory development-loop single-select; valid ids come from the manifest |
| `--dev IDS` | string | `all` when Dev is explicitly selected | Dev Enhancements: none currently; accepts `all` or `none`; the development loop is mandatory |
| `--security IDS` | string | `all` when Security is selected | Security items: `security-audit`, `all`, or `none` |
| `--quality IDS` | string | `all` when Quality is selected | Quality items: `react-doctor`, `webapp-testing`, `all`, or `none` |
| `--design IDS` | string | `all` when Design is selected | Design items: `frontend-design`, `design-stripe`, `design-linear`, `all`, or `none` |
| `--token-optimize IDS` | string | `all` when Token Optimize is selected | Token Optimize items: `caveman`, `code-memory`, `all`, or `none` |
| `--agents IDS` | string | `all` | Agent Target selection: comma-separated identifiers, `all`, or `none` |

The Category identifiers accepted by `--categories` are `dev`, `security`,
`quality`, `design`, and `token-optimize`. If `--categories` is omitted while
another selection flag is supplied, all Categories are selected and each
per-Category flag narrows only its named Category. A per-Category flag
conflicts with an explicit `--categories` value that omits that Category.

Dev is mandatory and currently has one development-loop option: `spec-loop`.
It is resolved for every generation, including `--categories none` and
`--dev none`. Dev currently has no selectable Enhancements, so both `--dev all`
and `--dev none` select no optional items. `--development-loop` is the
structural single-select and remains data-driven if the manifest adds another
loop; development-loop ids are never Dev Enhancement ids.

Unknown Category ids, unknown item ids, empty comma-separated selections, and
conflicting Category/item flags fail before generation with an
invalid-arguments error (exit 2). Unknown errors list the valid identifiers.
Unknown Agent Target identifiers in `--agents` follow the same exit-2 policy.

The former selectable loop identifiers are retired. Supplying any of them to
`--dev` fails with an invalid-arguments error (exit 2) naming the mandatory Dev
development loop, `spec-loop`, as its replacement:

| Retired identifier |
|---|
| `spec-loop` |
| `tdd` |
| `diagnosing-bugs` |
| `code-review` |
| `setup-all` |

The old Component-shaped flags are removed and always exit 2 with these
replacements named:

| Removed flag | Replacement named by the error |
|---|---|
| `--skills`, `--no-skills` | `--categories` and the per-Category item flags |
| `--mcp` | `--token-optimize code-memory` |
| `--no-mcp` | `--token-optimize none` |
| `--no-docs` | `--design none` |
| `--no-handoff`, `--no-agents` | No replacement; dev-ready no longer generates the Handoff Protocol |

Selections are resolved before confirmation, rendering, reporting,
verification, and stamping. The resolved development loop and Enhancement set
are shown to the user and recorded in `.dev-ready.json`. Explicit `none`
declines the named optional Enhancements; it never removes the development
loop.

Accepting every default, including `--yes` with no selection flags, produces
the lean Default Set: the Spec Loop with no Enhancements. Independently of that
selection, every project receives the `architecture` and `requirements`
documentation skeletons as generation infrastructure. Use the explicit
whole-catalog selection `--categories all` to select every Enhancement.

Exit codes: 0 success; 1 unexpected error or user abort; 2 invalid arguments; 3 network/fetch failure; 4 target directory conflict; 5 generated project failed verification; 6 stamp missing or unparseable/invalid; 7 drift detected; 8 upgrade not supported (pre-v3 stamp); 9 upgrade failed (rolled back).

#### Init progress output

`init` reports exactly four generation stages on stderr, in this order: fetch,
overlay, verify, and finalize. The fetch stage includes the manifest-pinned
upstream commit. A completed or failed stage includes elapsed time rounded to
two decimal places. Progress is observational: it does not change the final
report on stdout, command behavior, or the exit-code mapping above.

When stderr is a TTY, the active stage uses a standard-library spinner and the
renderer clears it before printing the terminal status. When stderr is
redirected or non-interactive, each stage emits stable plain lines without ANSI
escapes, carriage returns, or other animation controls. For example:

```text
[1/4] Fetching base template (commit <manifest-pin>)…
[1/4] Fetching base template done (1.23s)
```

Progress never prints percentages. A failed stage is identified once before
the normal typed error message. Temporary-staging cleanup failures are rendered
as separate `warning:` lines; they are not a fifth stage. Spinner cleanup runs
on success, expected errors, unexpected exceptions, keyboard interruption, and
termination represented by Python as process exit.

Staging is created beside the target and finalize commits it with one
same-filesystem atomic rename after revalidating the destination. There is no
cross-filesystem copy fallback: a finalize failure leaves no partial target and
restores an initially empty target directory.

### `dev-ready check [PATH]`

Inspect an existing generated project directory against its `.dev-ready.json` stamp and the running CLI manifest. Read-only operation.

| Flag | Type | Default | Description |
|---|---|---|---|
| `PATH` | path | `.` | Target project directory to check |
| `--json` | bool | false | Output report in JSON format |

Exit codes: 0 clean (no drift); 6 stamp missing or unparseable/invalid (including projects generated before v0.3); 7 drift detected.

### `dev-ready upgrade [PATH]`

Re-apply only overlay-managed whole-file content to an existing generated
project. It never touches upstream application code. User-modified files,
recorded-but-missing files, and shared injection targets are reported and left
unchanged; a currently managed file absent from both the project and its
inventory is added. All planned writes and deletions commit all-or-nothing.

| Flag | Type | Default | Description |
|---|---|---|---|
| `PATH` | path | `.` | Target project directory to upgrade |
| `--dry-run` | bool | false | Report planned changes without modifying the project |

Fresh projects use `stamp_version` 5. The record stores the selected Category
identifiers in the top-level `categories` list and the resolved loop identifier
in top-level `development_loop`, plus the project name, a managed-file
inventory, selected Agent Target identifiers in the top-level `agent_targets`
list, and the skills, MCP, and docs selection under `components`.
Fresh stamps no longer record Handoff Protocol inclusion. Stamp versions 1–5
remain readable, including version 3 and version 4 projects that do not carry
Categories; legacy version 4 `components.handoff` and version 3
`components.agents` entries are accepted for compatibility. Version 3 stamps
and version 4 stamps upgrade to version 5 without new input. The migration
derives Categories from recorded items, maps retired loop identifiers to the
mandatory development loop, and records that loop in the new stamp. Version 3
projects retain the existing Agent Target inference before reaching the same
version 5 result. Versions 1 and 2 remain checkable but cannot be upgraded.
Across an overlay-only upgrade, the stamped upstream
repository and commit are immutable Base Provenance; the dev-ready version,
Categories, resolved development loop, selected-item pins, selected Agent
Targets, and managed-file inventory are Overlay Currency and advance to the
running CLI. A newer manifest base pin is a non-blocking advisory because
`upgrade` does not rewrite upstream application content. Untouched obsolete
managed files are deleted transactionally; modified obsolete files are
preserved and reported. Dry run reports the complete plan without mutation,
failure rolls writes and deletions back together, and repeating a successful
upgrade plans no further changes. Exit codes: 0 success; 6 invalid or missing
stamp; 8 pre-v3 stamp cannot be upgraded; 9 upgrade failure after rollback.

### `dev-ready --version` / `dev-ready --help`

Standard version and help output.

## Interactive Prompt Flow (default `init` path)

This flow applies only to `init`. `check` and `upgrade` are non-interactive by
construction and dispatch directly to their respective operations.

1. Project name (if not given as argument)
2. Default Set offer, naming its resolved `spec-loop` development loop (yes by default)
3. If the Default Set is declined and the manifest offers multiple development loops, mandatory development-loop single-selection (the Default Set loop is listed first)
4. Category selection (`dev`, `security`, `quality`, `design`, and `token-optimize`; Dev remains selected because its development loop is mandatory); when the Default Set was accepted, the chosen Enhancements are layered onto it
5. Enhancement selection across the chosen Categories (Dev currently offers none; the loop is not an optional item)
6. Agent Target selection (described multi-select, all on by default; plain Enter accepts all targets)
7. Confirmation summary naming the resolved Categories, Catalog Items, and Agent Targets before writing anything

Steps 2–6 are skipped as a unit if any selection flag (`--development-loop`, `--categories`, any
per-Category item flag, or `--agents`) was passed. An omitted project name is
still prompted for, and confirmation still occurs.

All answers collect into a single `Answers` model shared with the flag-based path.

Declining the confirmation, or cancelling any prompt (Ctrl-C), prints `aborted: nothing was written` to stderr and exits 1 — nothing has been written at that point by construction. `--yes` bypasses every prompt in this flow, including confirmation. A non-TTY stdin with missing inputs and no `--yes` fails fast with an invalid-arguments error (exit 2) instead of hanging.

**Windows compatibility:** interactive prompts are tested against Windows Terminal. Legacy `cmd.exe` may render the checkbox prompt incorrectly (missing VT/ANSI support). In environments where terminal support is uncertain, use `--yes`, optionally with explicit selection flags, instead of relying on prompts.
