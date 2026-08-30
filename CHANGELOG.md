# Changelog

All notable changes to dev-ready are documented here.

## [0.13.0] — 2026-08-30

### Added

- **A third development method is selectable, and none is marked "coming soon"
  any more.** Its steps are started by the agent itself, and its chain runs from
  a written specification through planning, incremental implementation,
  test-first work, and review, ending at shipping rather than at a finished
  branch. Twenty steps come with it, so work headed for production can reach
  security hardening, performance, and instrumentation beside the build ones.
  All three offered methods are now available.
- **A new Token Optimize item** that keeps agent answers structured and
  scannable. The Category description widened to match what it now holds:
  reducing context use, keeping output legible, and improving codebase recall.

### Changed

- **`init` accepts a destination that already has content.** Generation used to
  refuse anything but an absent or empty directory. It now writes into an
  occupied one, and **never touches, moves, or removes content that was there
  first**. Exit 4 covers a new case: one or more top-level entries in the
  destination colliding with entries the new project would create. The failure
  state is always a set of whole entries, never a half-written file, and any
  entry that could not be put back is named. An absent or empty destination is
  unchanged — it still finalizes with a single atomic rename.
- **Choosing a development method now shows criteria, not just a description.**
  Each method carries the situations it suits, and the one-line description
  became a short menu label. Both existing methods' descriptions are rewritten a
  second time in two versions as a result.
- **The pre-generation confirmation, the method comparison, and the generation
  report are coloured.** v0.11 ruled the report plain text; that ruling is
  superseded. These three screens are the only coloured surfaces — prompts,
  progress, `check`, `upgrade`, and errors are unchanged. Colour is dropped
  whenever `NO_COLOR` is set or output is not a terminal, and every screen stays
  fully legible without it.
- **`rich` is a new runtime dependency**, required by those three screens.

### Fixed

- **`check` no longer reports a project's own `.git` directory as a problem.**
  Running `git init` in a generated project and then `check` told you an
  upstream change had leaked template-repository files and to stop using the
  pin. Nothing was wrong. The rule that forbids those paths belongs to
  generation, which still enforces it; `check` and `upgrade` no longer apply it
  to projects you have since put under version control.

### Upgrade from v0.12

Run `dev-ready upgrade PATH` with v0.13. **No new selection input is required**
and the stamp stays at version 5 — the third method and the new Token Optimize
item are available to select, not applied to existing projects.

## [0.12.0] — 2026-08-22

### Breaking changes

- **Agent skill directories are now links, not files, and they are excluded
  from version control.** A cloned project needs one `uvx dev-ready upgrade`
  before its agent sees anything.
- **A filesystem that cannot hold links can no longer receive a project with a
  selected Agent Target**, where v0.11 could. An explicit `--agents none`
  project is unaffected.
- **An existing project with a selected Agent Target on such a filesystem can
  no longer be upgraded.** The attempt exits 9, rolls back completely, and
  leaves the project on v0.11 until it is moved somewhere links work.

### Added

- A second development method is selectable. Its steps are started by the
  agent itself. A project using it keeps its plans under
  `docs/superpowers/plans/` and its design documents under
  `docs/superpowers/specs/`. Executable files arrive executable on macOS and
  Linux; on Windows, execution depends on the shell.

### Changed

- The first method's description is rewritten as a selection criterion. The
  new wording is what the interactive prompt shows.

### Upgrade from v0.11

Run `dev-ready upgrade PATH` with v0.12; no new selection input is required,
and the stamp stays at version 5.

The old pointer files at each selected Agent Target are retired once and
replaced by links. A hand-edited pointer file is preserved and reported; its
link is not created until that directory is empty.

`--dry-run` reports the complete plan without mutation; a failure restores
writes, deletions, and links together; a repeated successful upgrade plans no
further changes. Base Provenance and upstream application content remain
unchanged.

## [0.11.0] — 2026-08-18

### Breaking changes

- **`--flow spec-loop` and `--development-loop spec-loop` now exit 2.** The
  development-loop identifier was renamed to `mattpocock`. The error names the
  new value. `--flow` is the documented spelling; `--development-loop` remains
  a permanently accepted alias. Existing project stamps that record `spec-loop`
  still resolve through the alias and upgrade without editing.
- **A flag answers only its own question.** On v0.10.1, `--security
  security-audit` (and `--agents windsurf`, and `--development-loop
  mattpocock`) selected every catalog item and asked nothing. Those invocations
  now select the Default Set plus the named answer. `--yes` alone and
  `--categories all` are unchanged. A non-TTY `init` given only `--agents` and
  no `--yes` now exits 2.

### Added

- A project’s development method is now chosen and named. Interactive `init`
  asks the Engineering Flow first — even while only one is selectable — and
  lists two coming-soon entries the cursor cannot land on.
- Every optional Category is now shown to every interactive user. Pressing
  Enter through them still produces the lean Default Set, identical to `--yes`.
- A generated project can be configured without reading `.env` by hand.
  `setup-project` is written into every project and is the first next step the
  generation report prints.
- Seventy-four Design References are selectable, as ordinary Design Category
  items. `--design design-stripe,design-linear` still behaves as it did.
- The MIT copyright notice now travels with the copied skills, matching the
  Apache skills that already carried theirs.
- The Generation Skill installs as a Claude Code plugin and a Codex plugin
  from this repository, in addition to the existing
  `npx skills add MoofonLi/dev-ready --skill dev-ready` channel.

### Changed

- Interactive prompts share one style. Announced Flows render as dimmed,
  unselectable rows.
- The generation report is a counted summary rather than a comma-joined wall
  of paths. It stays plain text with no colour.
- A docs-only Design selection collapses to one line in `implement/SKILL.md`.
  The two shipped Design Reference descriptions no longer distinguish
  light-versus-dark. An existing project sees both on upgrade if that file was
  not edited.
- Generated loop guidance is named `## Engineering Flow`, starts at
  `setup-project`, and no longer lists `tdd` and `code-review` as peer steps of
  `implement`.

### Upgrade from v0.10

Run `dev-ready upgrade PATH` with v0.11; no new selection input is required,
and the stamp stays at version 5. The old loop name `spec-loop` resolves to
`mattpocock`.

What arrives as new managed files: the `setup-project` skill (and a Pointer
Stub at each selected Agent Target), the MIT notice files beside the copied
skills, and — when any Design Reference is selected — `docs/design-md-LICENSE.md`.
An untouched `AGENTS.md` is replaced with the Engineering Flow section.

If the project selected the two shipped Design References and nobody edited
`implement/SKILL.md`, that file is replaced too: the mounted block becomes one
docs line, and the two descriptions lose their light-versus-dark wording.

There is no v0.10-style hole. Every new path is a managed file, so `upgrade`
adds it. Edited files stay edited under the ordinary rule. `--dry-run` reports
every planned write and deletion without mutation; a failure restores writes
and deletions together; a repeated successful upgrade plans no further
changes. Base Provenance and upstream application content remain unchanged.

## [0.10.1] — 2026-08-11

### Fixed

- **Interactive `dev-ready init` works again.** In 0.10.0 it could not get past
  its own prompts: the first multi-select raised
  `ValueError: Cannot use j/k keys with prefix filter search`, because
  type-to-filter was enabled without disabling the j/k movement keys that
  questionary refuses to combine with it. Every interactive run hit this — the
  Category prompt, the item prompt, and the Agent Target prompt alike. Arrow
  keys still move the selection; j/k now type into the filter, which is what
  enabling the filter was for. `--yes` and the fully-flagged non-interactive
  paths were never affected.
- **The Category item prompt no longer crashes on an empty list.** Accepting the
  Default Set and adding no Category leaves only `dev`, whose sole item is the
  development loop itself — so the item prompt had nothing to offer and
  questionary raised `AttributeError: 'InquirerControl' object has no attribute
  'pointed_at'`. The prompt is now omitted when the chosen Categories offer no
  item outside the development loop: there is nothing to choose between, and a
  checkbox over an empty list is not a question. This sat directly behind the
  first crash on the default path and would have surfaced the moment it was
  fixed.

No selection, flag, exit code, stamp version, or generated file changed. A
default interactive run produces exactly the Default Set with the `claude` Agent
Target, as before.

## [0.10.0] — 2026-08-09

### Breaking changes

- **An absent `--agents` no longer means every agent.** It used to resolve to
  every declared Agent Target; it now resolves to `claude`, and `--yes` does the
  same. Scripts that relied on the old default must name the targets they want.
- **`--agents all` keeps its meaning, but its meaning grew.** v0.9 declared 2
  Agent Targets, so `--agents all` wrote roughly 24 Pointer Stub files. v0.10
  declares 57, so the same flag now writes roughly 684. To keep v0.9’s output
  exactly, pass `--agents claude,windsurf` instead.
- **`--dev setup-all` now exits 2.** The identifier is retired: the skill it
  named is part of the always-generated development loop, so every project
  receives it and nothing selects it. Remove the flag; a project stamp that
  records the identifier still upgrades without manual editing.

### Added

- Enhancement guidance now appears inside the development-loop step that acts on
  it. Selecting the security audit or the React quality check adds guidance to
  the project’s code-review step, the web-app testing Enhancement adds it to the
  testing step, and the design references add it to the implementation step. A
  project that selects none of them gets loop skills identical to before.
- Every generated project states its own tech stack, the exact commands to test,
  lint, format, and type-check both halves of it, and that its `AGENTS.md` is
  the project’s standards source — including rules no tool can enforce, such as
  which files are generated rather than hand-edited. This is true even for a
  project that selects nothing at all.
- A generated project ignores `.env` and `.env*` from the first commit, so the
  random secrets dev-ready itself writes into `.env` do not land in git history.
- The generation report and the generated `README.md` now name the default
  administrator login and where its password lives, together with the reason it
  is urgent: the backend creates that user only when it is absent, so changing
  the password after the first start changes the file and not the login.
- Far more coding agents can find the generated guidance. dev-ready now declares
  a target for every agent that its pinned reference list gives a project-level
  directory of its own, and a CI job fails when the two diverge. Agents that
  read the standard location were already supported and still need no target;
  they are named in the prompt and in the generation report.
- The deployment workflows are part of a generated project again. They were
  written by upstream for downstream users, and the deployment guide dev-ready
  keeps is about how to use them.

### Changed

- The AI-invokable generation skill is an interview. It asks what you are
  building, maps the answer onto the catalog, and proposes one command with a
  reason for each selection instead of asking you to choose flags.
- Accepting the defaults now leads straight to the Enhancement menu. The
  confirmation step that stood in front of it is gone, and pressing Enter
  through the menus still produces the same lean project as `--yes`.
- Every project receives its `architecture` and `requirements` documentation
  skeletons, whichever Categories are selected. They are part of what dev-ready
  always writes rather than something that can be declined by accident.
- The generated project’s development-loop guidance names its execution step,
  which was generated but never mentioned.
- The generated `BACKEND_CORS_ORIGINS` no longer allows a third party’s
  hostname.

### Removed

- The opt-in setup Enhancement as a selectable item. Its skill is now part of
  the always-generated development loop.
- The confirmation prompt that asked whether to add Enhancements to the defaults.

### Upgrade from v0.9

Run `dev-ready upgrade PATH` with v0.10; no new selection input is required, and
the stamp stays at version 5.

**The `.env` fix does not reach your existing project — this is the one thing to
check.** An untouched `README.md` is replaced, because it has been an
overlay-managed file since v0.2, so the credential disclosure does arrive. Your
root `.gitignore` is a different case: a project generated before v0.10 carries
upstream’s own copy at that path, a file dev-ready never wrote and has no record
of, and dev-ready does not replace a file it did not write. `upgrade` reports it
under `Skipped (user-modified)` and moves on.

**Do this by hand:** add `.env` and `.env*` to the project’s root `.gitignore`.
Adding the pattern does not remove an `.env` that is already committed — a secret
that has been pushed has to be rotated, not ignored.

That skipped line is the overlay lifecycle rule working, not failing. dev-ready
reports what it did not touch rather than overwriting user-owned files, which is
why the same run cannot silently discard your own edits either.

A stamp that records the retired setup identifier migrates rather than being
refused, and a project that never selected that Enhancement receives the skill
anyway as part of the loop. A loop skill you edited survives untouched and is
reported as divergent. `--dry-run` reports every planned write and deletion
without mutation; a failure restores writes and deletions together; a repeated
successful upgrade plans no further changes. Base Provenance and upstream
application content remain unchanged.

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

[0.10.0]: https://github.com/MoofonLi/dev-ready/releases/tag/v0.10.0
[0.9.0]: https://github.com/MoofonLi/dev-ready/releases/tag/v0.9.0
