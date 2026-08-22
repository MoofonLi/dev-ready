# CLI Specification — dev-ready

Status: v0.11 released contract (v0.11.0). This replaces the REST
`api-spec.yaml` from the original bootstrap plan: dev-ready is a CLI tool with
no HTTP API. (Generated projects expose their own OpenAPI docs via FastAPI.)

## Commands

### `dev-ready init [PROJECT_NAME]`

Generate a new project.

| Flag | Type | Default | Description |
|---|---|---|---|
| `--yes` / `-y` | bool | false | Accept the lean Default Set, no prompts |
| `--dir PATH` | path | `./PROJECT_NAME` | Target directory (must not exist or be empty) |
| `--categories IDS` | string | Default Set | Category selection: comma-separated ids, `all`, or `none` |
| `--flow ID` | string | `mattpocock` | Mandatory Engineering Flow single-select; `--development-loop` is a permanently accepted alias |
| `--dev IDS` | string | Default Set when unnamed; `all` when named | Dev Enhancements: none currently; accepts `all` or `none`; the Engineering Flow is mandatory |
| `--security IDS` | string | Default Set when unnamed; `all` when named | Security items: `security-audit`, `all`, or `none` |
| `--quality IDS` | string | Default Set when unnamed; `all` when named | Quality items: `react-doctor`, `webapp-testing`, `all`, or `none` |
| `--design IDS` | string | Default Set when unnamed; `all` when named | Design items: comma-separated ids, `all`, or `none` |
| `--token-optimize IDS` | string | Default Set when unnamed; `all` when named | Token Optimize items: `caveman`, `code-memory`, `all`, or `none` |
| `--agents IDS` | string | `claude` | Agent Target selection: comma-separated identifiers, `all`, or `none` |

The Category identifiers accepted by `--categories` are `dev`, `security`,
`quality`, `design`, and `token-optimize`. If `--categories` is omitted, an
unnamed Category resolves to the Default Set and a per-Category flag replaces
the Default Set answer for only its named Category. A per-Category flag
conflicts with an explicit `--categories` value that omits that Category. The
explicit `--categories all` selection still selects every Category, and naming
a Category without its item flag still selects all items in that Category.

Dev is mandatory and currently offers two Engineering Flow options: `mattpocock`
(the default) and `superpowers`. It is resolved for every generation, including
`--categories none` and `--dev none`. Dev currently has no selectable Enhancements,
so both `--dev all` and `--dev none` select no optional items. `--flow` is the
structural single-select and remains data-driven as the manifest adds flows;
`--development-loop` is a permanently accepted alias. Engineering Flow ids are
never Dev Enhancement ids.

Unknown Category ids, unknown item ids, empty comma-separated selections, and
conflicting Category/item flags fail before generation with an
invalid-arguments error (exit 2). Unknown errors list the valid identifiers.
Unknown Agent Target identifiers in `--agents` follow the same exit-2 policy.
Engineering Flow failures also exit 2 and distinguish these cases:

- `spec-loop` supplied to `--flow` or `--development-loop` says that the id was
  renamed to `mattpocock`.
- An announced but unreleased Flow, such as `addyosmani`, says that it is not
  yet available.
- Any other unrecognised Flow id says that the Engineering Flow id is unknown.

The former selectable loop identifiers are retired. Supplying any of them to
`--dev` fails with an invalid-arguments error (exit 2) naming the mandatory
Engineering Flow as their replacement, without naming which flow:

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
the lean Default Set: the `mattpocock` Engineering Flow with no Enhancements.
Independently of that selection, every project receives the `architecture` and
`requirements` documentation skeletons as generation infrastructure. Use the
explicit whole-catalog selection `--categories all` to select every
Enhancement.

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

When the selection projects Skill Links, verify materializes the complete
projected set with the production writer, inspects it, and removes those
temporary links before finalize. Finalize recreates the same links after the
atomic rename. A filesystem that cannot hold the required link kind fails
verify (exit 5) with the attempted path, the operating-system cause, and a
different-location remedy. A link failure after the rename restores the
destination exactly and exits 4; a restoration failure keeps exit 4 and adds a
manual-recovery warning. An explicit `--agents none` project projects no links
and performs no capability probe. There is no fifth public stage and no new
exit code.

### `dev-ready check [PATH]`

Inspect an existing generated project directory against its `.dev-ready.json`
stamp and the running CLI manifest. Read-only operation: it never creates a
temporary Skill Link, never probes filesystem capability, and never repairs
the project. Missing, stale, wrong, or unresolvable Skill Links and incorrect
or obsolete nested ignore-anchor files are drift (exit 7).

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
preserved and reported. Skill Links are derived state and are never inventoried;
`upgrade` creates missing links, repairs incorrect or broken ones, retires
trusted stale links named by an unmodified nested `.gitignore`, and retires
eligible legacy Pointer Stubs in the same transaction that writes Canonical
Content and each nested Git safety-anchor `.gitignore`. The stamp stays at
version 5. A real plan that creates or repairs a link probes link support
inside the project before the first persistent mutation; dry run and `check`
never probe. Capability or transactional failure exits 9 after restoring the
pre-upgrade tree. Dry run reports the complete plan without mutation,
failure rolls writes, deletions, anchors, and links back together, and
repeating a successful upgrade plans no further changes. Exit codes: 0 success;
6 invalid or missing stamp; 8 pre-v3 stamp cannot be upgraded; 9 upgrade
failure after rollback.

### `dev-ready --version` / `dev-ready --help`

Standard version and help output.

## Interactive Prompt Flow (default `init` path)

This flow applies only to `init`. `check` and `upgrade` are non-interactive by
construction and dispatch directly to their respective operations.

1. Project name (if not given as argument)
2. Engineering Flow single-selection (`mattpocock` by default, or `superpowers`).
   Announced Flows are shown with a `Not yet available` explanation and cannot
   be selected.
3. Security item selection
4. Quality item selection
5. Design item selection
6. Token Optimize item selection
7. Agent Target selection (described multi-select, Claude Code on by default;
   plain Enter accepts Claude Code only)
8. Confirmation summary naming the resolved Engineering Flow, Categories,
   Catalog Items, and Agent Targets before writing anything

The four optional Category questions are always asked on an unresolved
interactive content path, in the order above, with nothing pre-selected. Each
multi-select says that Space selects, Enter continues, and typing filters the
list. There is no Default Set question, no Category pre-filter, and no combined
item list.

A Category flag, per-Category item flag, or Flow flag resolves the catalog
selection non-interactively, so the Engineering Flow and four Category questions
are skipped; the Agent Target takes its documented `claude` default unless
`--agents` also supplies it. An Agent Target flag answers only the Agent Target
question: the Engineering Flow and all four Category questions are still asked.
An omitted project name is still prompted for, and confirmation still occurs.

All answers collect into a single `Answers` model shared with the flag-based path.

Declining the confirmation, or cancelling any prompt (Ctrl-C), prints `aborted: nothing was written` to stderr and exits 1 — nothing has been written at that point by construction. `--yes` bypasses every prompt in this flow, including confirmation. A non-TTY stdin with missing inputs and no `--yes` fails fast with an invalid-arguments error (exit 2) instead of hanging.
An Agent Target flag by itself still leaves the Engineering Flow and Category
answers missing, so that invocation also exits 2 on a non-TTY stdin unless
`--yes` supplies the Default Set.

**Windows compatibility:** interactive prompts are tested against Windows Terminal. Legacy `cmd.exe` may render the checkbox prompt incorrectly (missing VT/ANSI support). In environments where terminal support is uncertain, use `--yes`, optionally with explicit selection flags, instead of relying on prompts.
