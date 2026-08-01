# Changelog

All notable changes to dev-ready are documented here.

## [0.9.0] — 2026-08-01

### Breaking changes

- **A default project is now lean.** Accepting every prompt default, or running
  `dev-ready init PROJECT --yes` without selection flags, produces the mandatory
  Spec Loop plus the project’s `architecture` and `requirements` documentation
  skeletons. It no longer selects every catalog item. To select everything
  currently available in v0.9, use `--categories all`; this is not the old item
  set because v0.9 adds and retires content, as detailed below.
- **The generated multi-agent scaffold is gone.** Fresh projects no longer
  contain the Handoff Protocol’s Protocol Configuration, seven-role guidance,
  review-gate templates, ticket scaffold, or execution-report skeleton. This
  retirement applies to generated projects only (ADR-020); it did not itself
  change this repository’s development process. ADR-021 independently retired
  the repository’s internal Handoff Protocol four days later. No replacement
  scaffold is generated.
- **Automation using the previous selection interface now stops with exit 2.**
  The old Component-shaped flags are rejected instead of being ignored or
  guessed at. Update scripts as follows:

  Component intent has no one-to-one Category translation: Categories cross
  the former write-location groups. Always pass `--categories` with the exact
  optional Categories the script wants, then pass each matching per-Category
  flag with the exact identifiers to keep. Omitting `--categories` while using
  a per-Category flag selects every other Category, so it is not a safe
  migration. Rebuild the desired item set with this map:

  | Item or former identifier | Category | v0.9 per-Category selection |
  |---|---|---|
  | `setup-all` (new) | Dev | `--dev setup-all` |
  | `security-audit` | Security | `--security security-audit` |
  | `react-doctor` | Quality | `--quality react-doctor` |
  | `webapp-testing` | Quality | `--quality webapp-testing` |
  | `frontend-design` | Design | `--design frontend-design` |
  | former docs-component Stripe reference | Design | `--design design-stripe` |
  | former docs-component Linear reference | Design | `--design design-linear` |
  | `caveman` | Token Optimize | `--token-optimize caveman` |
  | `code-memory` | Token Optimize | `--token-optimize code-memory` |
  | `spec-loop`, `tdd`, `diagnosing-bugs`, `code-review` | Dev structure | Remove the identifier; these are structural parts of the mandatory `spec-loop` development loop |
  | `project-orientation` | Retired | Remove the identifier; the item was retired with no replacement |
  | `mcp-config` | Infrastructure | Remove the identifier; `.mcp.json` is generated automatically when a selected Enhancement needs it |

  For example, “security audit only” is
  `--categories security --security security-audit`; “React Doctor plus code
  memory” is `--categories quality,token-optimize --quality react-doctor
  --token-optimize code-memory`. Dev does not need to appear in `--categories`
  unless `setup-all` is wanted; the development loop is always resolved.

  Common negative-flag migrations depend on what the script kept alongside the
  omitted Component:

  - To preserve the intent of selecting everything currently available, use
    `--categories all`. The resulting set is intentionally different: it adds
    the new `setup-all` Enhancement and cannot restore retired content.
  - To translate the former all-on selection while omitting only MCP and not
    adding `setup-all`, use `--categories security,quality,design,token-optimize
    --token-optimize caveman`. Use `--token-optimize none` only when both Token
    Optimize Enhancements should be absent.
  - To translate the former all-on selection while omitting the document
    templates, keeping the Design skill, and not adding `setup-all`, use
    `--categories security,quality,design,token-optimize --design
    frontend-design`. Use `--design none` only when every optional Design
    Enhancement should be absent. The Default Set’s project-owned architecture
    and requirements skeletons remain on the default path.
  - There is no equivalent that removes every skill: the Spec Loop is mandatory.
    To preserve the former default non-skill content after `--skills none` or
    `--no-skills`, use `--categories design,token-optimize --design
    design-stripe,design-linear --token-optimize code-memory`. If the old script
    also disabled docs or MCP, remove that Category from the list. The project’s
    architecture and requirements skeletons are part of the lean Default Set,
    not independently selectable Enhancements; on an explicit selection path
    they are written when selected Design document references require the docs
    surface.
  - Remove `--no-handoff` and `--no-agents`; the generated Handoff Protocol no
    longer exists.

  `--agents` is still the independent Agent Target selector. Its identifiers
  and `all`/`none` behavior are unchanged.

### Added

- Category-first selection across Dev, Security, Quality, Design, and Token
  Optimize. The interactive flow and non-interactive flags use the same
  manifest-declared Category and item identifiers.
- A mandatory, named `spec-loop` development loop in every project and every
  fresh stamp. The loop now includes the previously missing `implement` step.
- An opt-in `setup-all` Dev Enhancement for changing Spec Loop tracker and
  documentation conventions after generation.
- Individually selectable Stripe- and Linear-inspired design references.

### Changed

- Fresh project stamps use version 5 and record Categories plus the resolved
  development-loop identifier alongside Enhancements, Agent Targets, pins, and
  the managed-file inventory.
- `.mcp.json` is infrastructure: it is generated when a selected Enhancement
  needs project-level MCP configuration and omitted otherwise.
- The former ten-item catalog cap is replaced by a size limit on the Default
  Set. Optional Enhancements are unbounded and off by default.

### Removed

- The generated Handoff Protocol, its Component, and its two flags.
- The `project-orientation` catalog item, whose guidance duplicated the
  auto-loaded root rules.
- Independent selection of `spec-loop`, `tdd`, `diagnosing-bugs`, and
  `code-review`; these are structural parts of the mandatory development loop.
- `mcp-config` as a selectable catalog item.

### Upgrade from v0.8

Run `dev-ready upgrade PATH` with v0.9; no new selection input is required.
Upgrade advances a version 4 stamp to version 5, derives Categories from the
recorded items, records the mandatory Spec Loop, and adds the loop to projects
that previously declined it.

The same transaction deletes untouched obsolete Handoff Protocol files,
`project-orientation` content and Pointer Stubs, and an unneeded base MCP
configuration. A user-edited obsolete file is preserved byte-for-byte and
reported as divergence. `--dry-run` reports every planned write and deletion
without mutation; failure restores writes and deletions together; a repeated
successful upgrade plans no further changes. Base Provenance and upstream
application content remain unchanged.

[0.9.0]: https://github.com/MoofonLi/dev-ready/releases/tag/v0.9.0
