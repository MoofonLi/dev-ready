# ADR-031: `init` may generate into an occupied directory when nothing collides at the top level

- Status: **Accepted** (2026-08-23, CEO Moofon), from the `grill-with-docs` session of 2026-08-22/23. Targets v0.13 (FR-53). Narrows the all-or-nothing guarantee `init` has carried since ADR-002, and rescopes the forbidden-path rule `inspection.py` applies.
- Context: `init` refuses any destination that exists and is not empty (`generate.py:353-364`, exit 4). Measured against how a project is actually started, that refusal fires on the ordinary case rather than the dangerous one: a developer who has already run `mkdir my-app && cd my-app && git init` owns a destination that is non-empty by exactly one entry, and dev-ready tells them to remove or rename it. The empty-destination case already works — `_validate_target_dir` returns `True` for an existing empty directory and finalize restores it on failure — so the gap is narrow and is entirely about content that was there first.

  A second defect was found in the same session and is inseparable from the first. `.git` is listed in `inspection.py`'s `FORBIDDEN_PATHS`, the loop applying it is ungated (`inspection.py:143-153`), and `check` runs `inspect_project` through `ProjectExpectation.lifecycle` (`check.py:49-54`). **A generated project that its owner then puts under version control fails `check` with exit 7**, and the message tells them an upstream change broke the pin and to file an issue against dev-ready. Confirmed on 2026-08-22 by calling `inspect_project` against a directory whose only entry is `.git`. The rule is right about the tree it was written for — a `.git` in *staging* means upstream's own repository leaked through Copier — and wrong about every tree after the move. Merging into a destination the user has already initialized would make the false verdict the normal outcome, so the two cannot ship apart.
- Decision:
  - **A destination that already holds content is accepted when no top-level entry of the destination shares a name with a top-level entry dev-ready is about to create.** The comparison is at the top level only.
  - **Any collision is exit 4 and names every colliding entry.** dev-ready never overwrites, merges into, or backs up an entry that was there first.
  - **Finalize into an occupied destination is a bounded sequence of same-filesystem renames of top-level entries**, replacing the single rename used for an empty or absent destination. On failure the entries already moved are moved back; if restoration itself fails, the error names exactly which entries remain in the user's directory. dev-ready moves only what it created and never touches pre-existing content, including while restoring.
  - **`--dir .` is the spelling**, and the project name defaults to the destination directory's name when the positional argument is omitted. A directory name that is not a valid project name is prompted for interactively and is exit 2 otherwise; it is never silently rewritten into a valid one.
  - **The forbidden-path rule applies to generation-time verification only.** `check` stops applying it. The leak it guards against is created at fetch and cannot appear later, so the guard belongs where the leak does.
- Considered options:
  - **Comparing collisions file by file through the whole tree** — rejected. It would splice a generated `backend/` or `frontend/` into an existing directory of the same name, producing a tree neither dev-ready nor the user designed, and its error message would list deep paths instead of the names the user sees with `ls`. Top-level comparison refuses that case by construction and costs only the destination that holds an unrelated `docs/`.
  - **A `--here` flag** — rejected as a second spelling of `--dir .`. The v0.12 surface statement holds that a flag answers only its own question; two spellings of one question means every document must choose which to teach. The discoverability the flag would have bought is bought instead by `--help` naming `.` explicitly.
  - **Leaving what was moved in place and only reporting it** — rejected by the CEO. It is the more conservative rule about acting inside a directory the user owns, and it produces debris the user cannot separate from their own content.
  - **Preserving the single atomic rename by moving the user's existing entries into staging first** — rejected. It reaches the same end state with the user's own content inside the failure window, which is the one thing this decision is careful not to risk.
  - **Removing the forbidden-path rule entirely** — rejected. It is a real guard: an upstream or Copier change that begins leaving `.git` behind would otherwise copy the template repository's whole history into every generated project with nothing to notice.
- Status update (2026-08-29): amended below — the occupied failure window includes the post-move link step and its recovery must be entry-wise, the collision comparison reads staging's own top level, `--dir` resolves at the `cli` boundary, and the forbidden-path rescope covers all five paths.
- Consequences: the all-or-nothing guarantee weakens in exactly one direction and must now be stated in two parts wherever it is claimed. Into an absent or empty destination it is unchanged — one atomic rename, target untouched on any failure. Into an occupied destination it becomes best-effort restoration over a sequence of atomic per-entry renames, so the failure state is always a set of whole entries and never a half-written file, and it can in principle be non-empty. `docs/cli-spec.md`'s `--dir` row ("must not exist or be empty") and `README.md` both change. `check` loses a verdict it should never have given; the generated project's own `README.md` is unaffected because it never mentioned the rule.

---

## 2026-08-29 amendment — the failure window includes the link step, the comparison is staging's own top level, and `--dir` resolves at the boundary

Decided in the `grill-with-docs` session of 2026-08-29 on v0.13 Phase 3, run
against the code this decision names rather than against the decision. Three
corrections; the decision itself is unchanged.

### The occupied failure window includes the link step, and today's recovery there destroys user content

This ADR describes rollback only for the move sequence. Skill Links are created
*after* the move (`generate.py:265-305`, the ADR-028 ordering), so the occupied
failure window has two halves, and the recovery for the second half is
`shutil.rmtree(target_dir)` followed by `target_dir.mkdir()`
(`generate.py:306-323`). That is correct for an absent or empty destination and
is **data loss into an Occupied Target**: it deletes content that was there
first, which is the one thing this decision exists to make impossible. It
becomes a defect the moment `_validate_target_dir` stops refusing non-empty
destinations, so it is part of this decision rather than an implementation
detail.

A link failure into an Occupied Target restores **entry-wise**: remove the links
created so far, then move back only the top-level entries dev-ready moved in,
leaving pre-existing entries untouched. Restoration failure reports exactly what
remains, as it does in the first half of the window. The `restore_empty_target`
boolean carried through `_finalize_project` cannot express this — the
destination's state at entry is a three-way distinction (absent, empty,
occupied), classified once by `_validate_target_dir` and carried as one value.

### The comparison is staging's own top level, and `.claude/` is the case that proves the rule

The set dev-ready is "about to create" is **selection-dependent** — `openclaw`
mounts `skills/`, `eve` mounts `agent/`, `astrbot` mounts `data/` — so it is read
from staging's own top-level entries after pruning, never from a list computed
in parallel with the overlay. A projection that can disagree with what was
staged is a second source of truth for the one comparison that must not be
wrong.

The strongest case against top-level-only comparison is a destination that
already holds `.claude/` — a developer who has been running Claude Code in the
folder they now want to scaffold. dev-ready creates `.claude/skills/.gitignore`
(ADR-028's anchor) and `CLAUDE.md`, so that destination is exit 4. **This is
accepted and no per-entry exception is added.** An exception for `.claude/` is
file-by-file merging under another name, into precisely the directory whose
ownership ADR-028 made dev-ready's; the rejection recorded above applies
unchanged. The error carries the remedy instead: move the entry aside, generate,
merge it back.

### `--dir` resolves at the CLI boundary, which is what makes `--dir .` safe

`--dir .` parses to an unresolved `Path(".")`, whose `.parent` is itself and
whose `.name` is empty. Staging is created with `dir=target_dir.parent`
(`generate.py:366-378`), so the spelling this decision chose would create
staging **inside the destination**, where it becomes a top-level entry of the
directory being classified; and the project-name default has no directory name
to read. `--dir` therefore resolves to an absolute path at the `cli` boundary,
making `Answers.target_dir` absolute on every path — it already is whenever
`--dir` is omitted. Staging is created beside the resolved destination, the
comparison sees only real entries, and the name default reads a real name.

### The forbidden-path rescope stands, and gains a second reason

`check` stops applying **all five** `FORBIDDEN_PATHS`, not only `.git`. Splitting
the tuple to keep the Copier four under `check` was considered and rejected: an
Occupied Target may legitimately hold any of them, and after the move dev-ready
cannot distinguish its own leak from content that was there first. Keeping the
Copier entries would reproduce the exact false verdict this decision removes —
"an upstream/Copier change reintroduced a template-repo leak; file an issue
against dev-ready" — against a user who owns the file.
