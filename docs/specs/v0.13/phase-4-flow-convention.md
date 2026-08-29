# Phase 4 — Flow Convention and Setup Contribution leave Python

Status: **Accepted** by Moofon (2026-08-29), by dispatching `to-tickets`
against it (ADR-021).

Version: v0.13

Phase: 4 (first deepening; this phase carries no FR)

Governing decisions: **ADR-024** (adding an Engineering Flow is a data change
plus assets), as amended through 2026-08-25; **ADR-029** (a flow declares its
own shape), as amended **2026-08-29** (the leftover `_FLOW_GUIDANCE` dict
leaves Python). **ADR-026** (`setup-project` is unconditional infrastructure,
and the three template trees it split stay split). ADR-002, ADR-010, ADR-016,
ADR-018, ADR-021, and ADR-023 remain binding. The stamp stays at version 5.

Source: the `improve-codebase-architecture` scan and grilling of 2026-08-29.
Fourteen decisions were settled there; the two that outlive this deepening are
already recorded (`CONTEXT.md`'s [[Flow Convention]] and [[Setup Contribution]]
entries, and ADR-029's 2026-08-29 amendment). The rest are below.

This document is the first of at most two deepenings Phase 4 may land. The
selection-model deepening is not in scope here and is not specified here.

---

## Problem Statement

A maintainer adding a third [[Engineering Flow]] does everything ADR-024 said
was enough — a catalog entry, vendored skills, the per-flow explainer — and
generation crashes:

> flow guidance is missing: addyosmani

The crash is not a missing skill and not a malformed catalog. Overlay keeps a
second catalog of authored prose, a Python dict keyed by flow id, and treats a
valid loop with no entry as an overlay fault. The chain sentence already renders
from `chain` and `invocation`. What the dict still holds is two optional
paragraphs: the [[Flow Convention]] concatenated into `AGENTS.md`, and the
[[Setup Contribution]] interpolated into the [[Setup Step]].

ADR-029 moved the structurally constrained half into the manifest and recorded
the rest as leftover. Phase 5 adds a flow. Leaving the dict in place means that
phase edits Python to introduce an id, which is the property ADR-024 exists to
buy and the code does not deliver.

A user generating `mattpocock` or `superpowers` must see the same `AGENTS.md`
and the same Setup Step they see today. This deepening changes where those
paragraphs live, not what they say.

## Solution

The two leftover paragraphs become optional catalog source paths on the
development-loop [[Catalog Item]]. Overlay reads each declared file as literal
markdown and fills the tokens it already fills. It never copies those files into
the generated project.

A flow that omits a field has empty extras: `AGENTS.md` is the Engineering Flow
heading plus the chain sentence, and the Setup Step is the shared interview
with no flow section. A flow that declares a path whose file is missing fails
at generation the way any other missing overlay asset fails. An empty string is
not an omission — it is `ManifestError`.

Python still composes the heading and the chain sentence from catalog data.
The files contain only the extra prose. Adding an Engineering Flow is then a
data change plus assets, with no Python edit.

## User Stories

### Adding a flow

1. As a maintainer adding a third [[Engineering Flow]], I want generation to
   succeed once the catalog entry and its assets exist, so that I do not also
   edit overlay Python to name the new id.
2. As that maintainer, I want a flow that needs no extra paragraphs to generate
   with only the chain sentence in `AGENTS.md`, so that optional extras are
   actually optional.
3. As that maintainer, I want a flow that needs a [[Flow Convention]] to
   declare a source path and drop a markdown file, so that the paragraph is
   data plus an asset rather than a Python string.
4. As that maintainer, I want a flow that needs a [[Setup Contribution]] to
   declare a second source path the same way, so that the Setup Step extra is
   the same kind of thing as the convention, not a special case.
5. As that maintainer, I want omitting the Setup Contribution to be simply not
   declaring the field — as `superpowers` does today — so that I do not keep an
   empty file to mean "none".
6. As that maintainer, I want a declared path whose file is missing to fail at
   generation naming a missing overlay asset, so that a typo is loud and is not
   the old "flow guidance is missing" crash.
7. As that maintainer, I want an empty-string field to be rejected when the
   manifest loads, so that "present but blank" cannot mean omission.
8. As a Phase 5 implementer, I want `addyosmani` to need no overlay Python
   change, so that this deepening is the one that makes that phase cheaper.

### Generated output

9. As a developer generating with `mattpocock`, I want `AGENTS.md`'s
   Engineering Flow section byte-identical to today's, so that a refactor of
   where the paragraph lives is not a rewrite of what my agent reads.
10. As that developer, I want the Setup Step to still offer issue-tracker and
    domain conventions and still hand off to `setup-matt-pocock-skills`, so
    that the [[Setup Contribution]] is the same interview it is today.
11. As a developer generating with `superpowers`, I want `AGENTS.md` to still
    name `docs/superpowers/plans/` and `docs/superpowers/specs/`, so that the
    one-sentence convention survives the move out of Python.
12. As that developer, I want the Setup Step to gain no flow section, so that
    omitting the [[Setup Contribution]] stays empty rather than growing a stub.
13. As a developer, I want no new file under `docs/agents/` or anywhere else in
    the generated tree, so that overlay-only assets stay overlay-only.
14. As a developer running `upgrade` on a project generated before this
    deepening, I want managed overlay files to stay byte-identical for the same
    selection, so that a refactor is not an overlay rewrite.

### Catalog rules

15. As a maintainer, I want an Enhancement that declares `convention` or
    `setup_contribution` to fail at load, so that those fields cannot drift
    onto items that are not flows.
16. As a maintainer, I want an [[Announced Flow]] that declares either field to
    fail at load, so that a placeholder cannot carry materialized extras.
17. As a maintainer, I want a declared source path to use the same path dialect
    as other catalog sources, so that a traversal-shaped value is rejected
    before overlay reads it.
18. As overlay rendering, I want to find the selected flow through the catalog's
    loop collection, so that "which Engineering Flow is this?" is asked one way.

### What does not change for a user

19. As a developer choosing an Engineering Flow, I want the menu, the
    comparison, `--flow`, and the stamp field unchanged, so that this deepening
    is invisible on the selection spine.
20. As a developer, I want the stamp to stay at version 5, so that no project
    is migrated for paragraphs the stamp never recorded.
21. As a developer, I want `check` and `upgrade` to keep resolving a recorded
    flow the way they do today, so that lifecycle commands do not grow a
    second reader of these extras.
22. As a reader of the per-flow explainer under `docs/agents/`, I want that
    document unchanged, so that the human page and `AGENTS.md` can still carry
    overlapping prose rather than this phase collapsing them.

### Maintainers navigating the module

23. As a future architecture review, I want no Python dict keyed by flow id
    left in overlay, so that this leftover is not re-suggested as unpaid.
24. As that review, I want the extras not extracted into a new module that only
    reads two files, so that the deepening is the catalog-plus-assets seam and
    not a shallow pass-through.

## Implementation Decisions

### The extras are optional catalog source paths, not a Python table

A development-loop Catalog Item gains two optional fields:

- `convention` — non-empty source path of the [[Flow Convention]]
- `setup_contribution` — non-empty source path of the [[Setup Contribution]]

Omitted means empty extras. Present must be a non-empty string in the catalog
source-path dialect; an empty string is `ManifestError`. Enhancements are
forbidden from declaring either field, as they already are from `invocation`,
`chain`, `choose_when`, and `roles`. Announced Flows are forbidden from
declaring them as materialized content, as they already are from `chain`,
`choose_when`, `paths`, and the rest of that list.

The fields are not recorded in the stamp. They are overlay rendering inputs,
like `chain` and `invocation`, not Overlay Currency.

### Overlay reads, never copies

Overlay resolves each declared path against the package templates root, reads
the file as UTF-8, and uses the bytes as the extra prose. The files are literal
markdown: no `{{token}}` substitution, so a brace in the paragraph is not an
unresolved marker. A declared path whose resource is missing is `OverlayError`
at generation, the same class as any other missing overlay asset. The message
names a missing asset, not a missing flow-id key.

The files are not `paths` entries and have no destination. A generated project
does not gain a file because a flow declared extras.

### Python still composes the chain; files hold only extras

The Engineering Flow section of `AGENTS.md` remains: heading, chain sentence
rendered from `chain` and `invocation`, then the Flow Convention if present.
The Setup Step token remains the Setup Contribution if present, else empty.
`superpowers` declares `convention` and omits `setup_contribution`.
`mattpocock` declares both. The shipped strings move verbatim, so existing
byte-identity tests stay the specification of the paragraphs.

A selected flow is looked up on the catalog's loop collection, not by scanning
the skills component as if a flow were an ordinary skill.

### One overlay-only root, not a fourth copy of ADR-026's split

The assets live in an overlay-only package root, one directory per flow id,
outside vendored skills, flow-copied project docs, and original skills. Nothing
in that root is a `paths` destination. The grilling named this root
`templates/flows/<id>/`; implement against that name.

Do not extract a new module to hold the read. Overlay rendering already
composes these tokens; deleting the dict deepens that module. A new module
whose interface is "read two optional files" fails the deletion test.

### Architecture table

The overlay module's responsibility already includes templating of names and
values. This deepening adds: catalog-declared Flow Convention and Setup
Contribution are overlay-interpolated assets, never destination writes. The
module-boundary row is corrected in the same change so the table matches the
code.

## Testing Decisions

A good test here asserts what overlay writes for a resolved selection, and what
the loader accepts or refuses. It does not assert that a Python dict is gone,
that a private helper ran, or that a file exists on disk except as the cause of
an observable overlay result. The existing suite is the specification of
shipped bytes: those tests are not edited to accommodate the refactor. A test
that has to change is evidence the deepening changed behaviour, except the two
tests that currently pin the crash this deepening removes.

Two seams, both already in use. Unit tests only: `tmp_path`, no network.

### Overlay content — `tests/unit/test_overlay.py`

The highest seam: `build_overlay_content` for a resolved selection. Prior art
is the exact-body assertion on `mattpocock`'s Engineering Flow section, the
`superpowers` convention sentence, the empty Setup Contribution, and the two
tests that today raise `OverlayError` matching `flow guidance is missing`.

Cases:

- shipped `mattpocock` — `AGENTS.md` Engineering Flow section and Setup Step
  injection unchanged;
- shipped `superpowers` — convention sentence present, Setup Step gains no
  flow section, and no new generated path appears;
- a fixture loop that declares `chain` and `invocation` and neither extra —
  `build_overlay_content` succeeds; `AGENTS.md` contains the heading and the
  chain sentence and does not contain a convention paragraph; the Setup Step
  contains no flow section. The fixture is an in-memory catalog or a
  `parse_manifest` document, **not** a third flow in the shipped manifest;
- a fixture loop that declares `convention` pointing at a missing resource —
  `OverlayError` naming a missing overlay asset, not a missing flow-id key;
- the two existing crash tests are replaced by the fixture cases above, not
  kept as characterizations of the dict.

The fixture-flow case is the phase's acceptance line: a flow can be added with
its catalog fields and assets and no Python edit.

### Manifest load — `tests/unit/test_manifest.py`

Catalog well-formedness at `parse_manifest`. Prior art is the Announced Flow
materialization ban and the enhancement-forbidden loop fields.

Cases:

- `mattpocock` and `superpowers` load with the new fields present or omitted as
  specified above;
- an Enhancement declaring `convention` or `setup_contribution` is
  `ManifestError`;
- an Announced Flow declaring either is `ManifestError`;
- an empty-string `convention` or `setup_contribution` is `ManifestError`;
- a traversal-shaped source path is `ManifestError`, at the same dialect the
  other catalog sources already use.

### What is not a seam

No new test file keyed on the deleted dict. No assertion that a particular
Python name is absent. `check` and `upgrade` are not extended: they do not
read these fields. No network-marked job: shipped-byte identity is already
covered by the overlay unit tests, and Phase 5's vendored-drift job is not
this deepening's.

## Out of Scope

- **The selection-model deepening** (Phase 4's second candidate). Specified and
  grilled after this one lands.
- **Any user-visible change** to generated `AGENTS.md`, the Setup Step, the
  per-flow explainer, `.gitignore`, the flow menu, `--flow`, or the stamp.
- **Collapsing the Flow Convention into `docs/agents/<id>.md`.** That would
  change `AGENTS.md`. Overlapping prose between the two surfaces stays.
- **`issue_tracker_configuration`.** Already a template token consumed only by
  the mattpocock issue-tracker template.
- **Making `.superpowers/` in the generated root ignore file depend on the
  selected flow.** Conditionalising it changes `mattpocock` projects.
- **Prose fields on the Catalog Item**, a Python dict retained with missing-key
  mapped to empty, or a filename convention with no manifest field. Rejected in
  grilling and recorded in ADR-029's 2026-08-29 amendment.
- **A new overlay module** whose only job is reading the two files.
- **A stamp version bump**, and any recording of these fields.
- **Any README change.** Phase 6 owns both READMEs.
- **FR-48 / `addyosmani`.** Phase 5 adds that flow against this seam; this
  deepening does not vendor it, describe it, or retire the Announced Flow.
- **Loader existence checks for overlay assets.** Declared-but-missing is an
  overlay error, matching other catalog sources.

## Further Notes

**No new ADR.** ADR-029's 2026-08-29 amendment records the leftover this
deepening pays. `CONTEXT.md` already defines [[Flow Convention]] and
[[Setup Contribution]].

**Phase 4 may land at most two deepenings.** This is the first. If this spec
is accepted and implemented, the selection-model grilling opens next; it is
not in this document.

**The existing suite is the specification of shipped bytes.** A test that must
be edited to accommodate the move, other than the two crash tests this
deepening retires, is a behaviour change: stop.

## Acceptance

- a fixture Engineering Flow that declares `chain` and `invocation` and neither
  extra generates; `AGENTS.md` carries the chain sentence and no convention
  paragraph;
- `mattpocock` and `superpowers` generated overlay bytes are unchanged for a
  fixed selection;
- adding those extras for a flow is a catalog field plus a file under the
  overlay-only root, with no overlay Python edit naming the flow id;
- a declared extra whose file is missing is `OverlayError` for a missing
  overlay asset;
- the stamp is untouched;
- `docs/architecture.md`'s overlay row matches the code after the change.
