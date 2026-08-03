# FR-32 — Mount Points

Status: Accepted (2026-08-03) — Moofon authorized dispatch to `to-tickets` in-session, after the grilling that settled every decision below

Version: v0.10

Phase: 2

Governing decisions: ADR-008, ADR-009, ADR-010, ADR-014, ADR-015, ADR-016, ADR-017, ADR-018 (with its two 2026-08-02 amendments and its 2026-08-03 amendment)

## Problem Statement

A generated project's Enhancements and its development loop do not know about
each other.

**The right guidance arrives at the wrong moment, or not at all.** A user who
selects `react-doctor` gets a skill that explains how to health-check a React
frontend. A user who selects `security-audit` gets a skill that hunts
exploitable vulnerabilities. Both are discoverable — a Pointer Stub at each
Agent Target's native path means the agent loads their names and descriptions
every session. What neither is, is *present at the moment it matters*. The
`code-review` step runs a two-axis review — Standards and Spec — and neither
axis is security, and neither axis is frontend health. The agent has to notice,
unprompted, that two items in a flat list of skill descriptions apply to the
work it is doing right now. That is exactly the failure ADR-018 named when it
rejected listing Enhancement guidance in a table in the rules file: the
instruction is not in the file the agent is executing at the moment it matters.

**Two Catalog Items are written into projects and referenced by nothing at
all.** `design-stripe` and `design-linear` place a DESIGN.md reference under
`docs/`. Nothing in the generated overlay mentions either path — not the rules
file, not any skill, not the project README. A user selects a visual reference,
receives the file, and no agent will ever open it unless the user names it by
hand. For a Catalog Item that is a document rather than a skill, there is no
Pointer Stub and therefore no discovery path whatsoever. The item is delivered
and inert.

**ADR-018 opened this arc in v0.9 and left it open.** It gave Enhancements a
declared attachment point as the reason the Spec Loop became mandatory
infrastructure in the first place — the loop is the spine that guidance attaches
to. The spine shipped. Nothing attaches to it.

## Solution

An Enhancement may name one Spec Loop step as its **Mount Point**. When that
Enhancement is selected, dev-ready appends a short, machine-delimited block to
the mounted step's skill, naming the Enhancement, describing it in the same
words the catalog already uses, and pointing at where its content landed. An
agent reaching `code-review` reads, in that file, that a security audit and a
frontend health check are available and where they are.

Selecting nothing leaves every loop skill byte-identical to its vendored
snapshot. The block appears only when a mounting Enhancement is selected, and it
is regenerated wholesale on every generation and every `upgrade`, so it never
drifts and never duplicates.

The declaration is one identifier per item. The block's text is derived from
catalog data the item already carries, so a new mount is one line of manifest
and no new prose to maintain. A mount is optional, and four of the eight
Enhancements declare none — an Enhancement whose guidance applies at every step,
or at no particular step, is better served by the discovery that already works
than by an interruption at an arbitrary one.

v0.10 declares six mounts:

| Enhancement | Mount Point | Why that step |
|---|---|---|
| `react-doctor` | `code-review` | ADR-018 names this one; examining a diff is `code-review`'s entire job |
| `security-audit` | `code-review` | Security is neither of the two axes `code-review` runs |
| `webapp-testing` | `tdd` | `tdd` is the step that writes tests; this drives a browser to run them |
| `frontend-design` | `implement` | UI is written at `implement`; no lower step builds it |
| `design-stripe` | `implement` | Consulted while a component is written, not while a spec is drafted |
| `design-linear` | `implement` | As above |

`caveman` and `code-memory` declare none: token discipline applies at every
step, and an MCP server is already a tool in the agent's hands.

## User Stories

1. As a developer generating a project with `security-audit`, I want the
   `code-review` step to tell me a security audit is available, so that the
   review I run covers an axis its two built-in axes do not.
2. As a developer generating a project with `react-doctor`, I want the
   `code-review` step to name it, so that frontend health is checked when a
   frontend diff is being reviewed rather than whenever I happen to remember.
3. As a developer generating a project with `design-linear`, I want the
   `implement` step to point at `docs/design-linear.md`, so that the reference I
   deliberately selected is opened while I am choosing a palette rather than
   sitting unread in a directory.
4. As a developer generating a project with `webapp-testing`, I want the `tdd`
   step to name it, so that when the thing under test is a web UI I know what
   drives it.
5. As a developer who accepts the Default Set and selects nothing else, I want
   every loop skill to be exactly its upstream text, so that I carry no
   dev-ready-authored guidance I did not ask for.
6. As a developer who selected both `react-doctor` and `security-audit`, I want
   one block listing both, so that `code-review` gains one section rather than
   two competing ones.
7. As a developer who has not edited a mounted skill, I want `dev-ready upgrade`
   to replace its block with the current one, so that improvements to mounted
   guidance reach me the same way every other managed file does.
8. As a developer who has edited a mounted skill, I want `upgrade` to preserve
   my edit and tell me it diverged, so that the guarantee ADR-014 makes for
   every other managed file holds here too.
9. As a developer who runs `dev-ready check` immediately after generating, I
   want no file reported as modified, so that a mounted skill is not
   misclassified as my own edit before I have touched anything.
10. As a developer who regenerates a project with the same selection, I want
    byte-identical output, so that NFR-1's reproducibility guarantee is not
    weakened by injected content.
11. As a maintainer adding a Catalog Item, I want a mount to be one identifier,
    so that declaring one costs no bespoke prose and cannot drift from the
    item's own description.
12. As a maintainer adding a Catalog Item that fits no single step, I want to
    omit the mount, so that I am not forced to invent an attachment point that
    will interrupt an agent at the wrong moment.
13. As a maintainer who mistypes a mount target, I want manifest loading to
    fail, so that a typo is not a silent absence of guidance.
14. As a maintainer adding a second development loop that lacks a mounted step,
    I want manifest loading to fail in front of me, so that the question "what
    does a user of this loop who selects that Enhancement get?" is answered
    before it reaches a user.
15. As a maintainer, I want the vendored byte-equality drift guard to keep
    passing untouched, so that mounting does not weaken the FR-16 provenance
    check.
16. As a maintainer, I want `THIRD_PARTY_NOTICES.md` to describe what is
    distributed rather than how the code works, so that it does not silently
    become false the next time the mechanism changes.
17. As a reviewer of this repository, I want the rule about where content
    transformation happens to be written in the architecture document, so that
    the next feature that writes into a managed file does not rediscover it
    through a broken `upgrade`.

## Implementation Decisions

### Injection happens inside the overlay's whole-file rendering, not as a catalog effect

The v0.10 plan and `docs/version-plan.md` both originally described this as a
third catalog effect kind. **That is wrong and following it produces a defect
with no error message.** Catalog effects apply after the overlay writes its
files, and the stamp inventory is computed from the overlay's rendered content
*before* they run. An effect-shaped mount therefore records a hash that can
never match the file it describes: `upgrade` classifies a mounted skill as
user-modified from the moment it is generated and skips it forever.
`classify_shared_targets` compounds it, since every effect target is treated as
a shared file that `upgrade` deliberately does not touch — the mounted skill is
excluded twice, for two unrelated reasons.

Mounting is therefore a transformation of overlay content, applied where every
other managed byte is produced. `catalog_effects` is not modified by this phase.
The general rule this rests on is recorded in `docs/architecture.md`: content
dev-ready owns is transformed inside the overlay's whole-file rendering; only
content it does not own is mutated after the write.

Ordering inside that rendering: the block is appended after all selected item
paths have been collected and before Pointer Stubs are projected, so exactly one
place mutates a mounted skill's bytes. Stub rendering reads only the canonical
file's YAML frontmatter, so stubs are unaffected either way — the ordering is
chosen for a single mutation point, not because the output would differ.

### The declaration is a single manifest identifier

A Catalog Item gains an optional `mount` field holding one development-loop step
id. It is a plain string on the item model, alongside `category`, rather than a
wrapper type: the mount carries exactly one value, and a single-field record
would be ceremony. Should a mount ever need a second field, promoting the string
to a record is contained to the loader and the one render site.

The manifest loader validates, raising the existing manifest error type:

1. `mount`, if present, is a non-empty string.
2. `mount` is not declared on a development-loop item — a loop cannot mount on
   itself.
3. `mount` names a step of **every** declared development loop, not merely one
   of them. This is the strict reading chosen deliberately: a second loop that
   lacks a mounted step fails at manifest load, in front of the maintainer
   adding the loop, rather than degrading silently in front of a user who picked
   that loop. ADR-018 rejected optional loops partly to avoid needing graceful
   degradation here; this validation is what keeps that true when a second loop
   arrives.
4. An item declaring a `mount` declares **exactly one** path. The block points at
   where the item's content landed, and an item with zero or several
   destinations has no single answer.

Validation lives with the existing catalog-relationship checks, which already
hold the loop-versus-item invariants.

### The block is derived, not authored

The block's text comes from data the item already carries: its id, its
description, and the destination of its single declared path. No new asset kind,
no markdown escaped into a JSON string, and no per-mount prose that can drift
from the description an agent sees in the skill listing.

Rendered shape, appended to the mounted skill's content:

```
<!-- dev-ready:mounted-enhancements:start -->
## Mounted enhancements

When running this skill, also apply the enhancements selected for this project.

- **<item id>** — <item description> See `<path dest>`.
<!-- dev-ready:mounted-enhancements:end -->
```

- **One block per mounted skill**, listing every selected Enhancement mounted
  there. The heading is meaningful once.
- **Entries sorted by item id**, not by manifest declaration order. Manifest
  array order currently never reaches file *content* anywhere — it affects write
  order only, and the inventory is sorted — and this would be the first place it
  did. Under declaration order, inserting an item in the middle of the JSON
  array would rewrite the mounted skill in every existing project and surface as
  a change on their next `upgrade`, for no semantic reason.
- **Appended at end of file**, separated by one blank line, with the file
  normalized to exactly one trailing newline before the block. The vendored
  snapshot cannot carry an anchor: it is compared byte-for-byte against the
  pinned upstream clone, so a placeholder inside it would be permanent drift.
  End-of-file is the only position that preserves the skill's own reading order;
  the block's own first line tells the agent it applies to the skill above it.
- **HTML comments as delimiters** — invisible when the markdown renders,
  unambiguous to a machine, and stable across releases. No version or timestamp
  goes inside them; either would churn the block on every release and produce
  spurious `upgrade` diffs.

### Idempotence is a property of the design, not code to write

dev-ready never reads a generated skill back. Generation renders into a fresh
staging directory, and `upgrade` replaces whole files. There is consequently no
path on which a second block could be appended to a file that already has one,
and **no parser, no marker search, and no re-injection guard is to be written**.
The delimiters exist for human readers and for tooling that does not exist yet.

This makes the phase materially smaller than the v0.10 plan first assumed, and
that reduction is deliberate rather than an oversight: an implementation that
adds re-injection logic has built a mechanism for a call that cannot occur.

### `upgrade` and `check` need no changes

Both behaviours the acceptance criteria name follow from injecting before the
inventory is computed. An untouched mounted skill hashes to its recorded value,
differs from the newly rendered content, and is upgraded. An edited one fails
the hash comparison, is preserved, and is reported. `check` does not read the
inventory at all. The stamp stays at version 5: nothing here adds, removes, or
re-types a recorded field, since the mount is derived from a selection the stamp
already records.

These are asserted, not implemented.

### A missing mount target is a generation-time error

If a mounted step's skill file is absent from the rendered content, the overlay
raises its existing error type rather than skipping silently. With a mandatory
loop and validation 3 above, this can only fire on a manifest defect — most
plausibly a loop that declares a step in its `steps` list without declaring a
path that writes it. Silence there would mean an Enhancement the user explicitly
selected losing its guidance with no signal.

### `THIRD_PARTY_NOTICES.md` states licensing facts, not mechanisms

The `mattpocock/skills` section is rewritten to say that copies written into a
generated project may be modified by dev-ready and are therefore derived works,
while the snapshots in this repository remain byte-checked against the pinned
commit. It names no mechanism.

This is the durable form. The file currently carries two false sentences, and
both went false the same way — they described an implementation that then
changed. One describes a setup-command substitution deleted in Phase 1; the
other lists `project-orientation`, removed in v0.9. Both are deleted in this
phase. The notices sync check reads only repo, commit, license, and Apache-2.0
LICENSE presence, so it cannot see prose and did not catch either.

Two provenance checks were verified against their implementations rather than
assumed:

- The **vendored drift guard** compares only manifest-declared vendored paths
  against a clone of the pinned commit. Templates are not modified by mounting —
  the transformation applies to rendered bytes in memory — so the guard is
  unaffected.
- All six mount targets are MIT `mattpocock/skills` content. No Apache-2.0 file
  is modified, so no NOTICE-propagation obligation is triggered by this phase.

## Testing Decisions

A good test here asserts what a generated project contains, not how the overlay
arrived at it. Every seam used already exists; this phase introduces none.

**Manifest loading** (`load_manifest` against fixture manifests, beside the
existing catalog-relationship tests):

- a mount naming a step of the only declared loop loads;
- a mount naming an unknown step is rejected;
- a mount naming a step present in one declared loop but absent from another is
  rejected — the fixture declares two loops, which the shipped manifest does not;
- a mount declared on a development-loop item is rejected;
- a mount on an item declaring zero paths, and on an item declaring two, is
  rejected;
- the shipped manifest loads and reports the six expected mounts.

**Rendered content** (`build_overlay_content`, the highest seam and the one the
existing overlay tests use):

- a selection including `react-doctor` puts a block in `code-review`'s skill
  containing the item id, its description, and its path destination;
- a selection including `react-doctor` and `security-audit` puts **one** block in
  `code-review`'s skill with both entries in id order;
- a selection with `design-linear` puts a block in `implement`'s skill pointing
  at the `docs/` destination — a Catalog Item that is not a skill;
- a selection with no mounting Enhancement leaves every loop skill byte-identical
  to its packaged template;
- two calls with the same selection return identical bytes;
- Pointer Stubs for a mounted skill are unchanged by the presence of a block.

**Generation and lifecycle** (`apply_overlay` and `upgrade_project` into
`tmp_path`, following the existing lifecycle tests):

- after `apply_overlay`, the stamp inventory hash recorded for a mounted skill
  equals the hash of the file on disk — the assertion that would have failed
  under the effect-shaped design;
- `upgrade` on an untouched generated project reports no change for the mounted
  skill;
- `upgrade` on a project whose mounted skill was edited preserves the edit and
  reports it as skipped and divergent;
- `upgrade` on a project generated before the block existed, with the skill
  untouched, upgrades it to the block-bearing content.

All unit tests use `tmp_path`, touch nothing outside it, and make no network
call. The vendored drift check and the notices sync check are unchanged and stay
network-marked where they already are.

## Out of Scope

- **Any change to `src/dev_ready/catalog_effects.py`.** The MCP-server and
  npm-dev-dependency kinds are untouched, and no third kind is added.
- **A stamp version bump.** The stamp stays at version 5 for all of v0.10.
- **Per-mount authored prose, or a `guidance` override on the mount field.** The
  derived block is the whole mechanism; an override is a data addition available
  later if a real case appears.
- **Mounting onto anything other than a development-loop step** — Enhancement to
  Enhancement, or onto the rules file, or onto a document.
- **Injecting anywhere other than end of file.** Anchored injection would
  require modifying a vendored snapshot and permanently breaking the drift
  guard.
- **Any runtime edit of a skill.** Injection is generation-time only (ADR-018).
- **Bumping the `mattpocock/skills` pin.** Phase 1 moved a path between catalog
  entries at the existing commit; v0.10 does not advance it.
- **The MIT license-notice question.** The twelve MIT loop skills carry no
  license notice into generated projects while the two Apache-2.0 skills carry
  theirs. This predates v0.10 and is recorded as an observation in
  `docs/version-plan.md`, not resolved here.
- **README work**, which Phase 6 owns entirely.

## Further Notes

**Why a wrong mount is worse than no mount.** Mounting adds nothing to
discoverability — ADR-015's Pointer Stubs already make every selected skill
loadable at each Agent Target's native path. What a mount buys is timing. It
follows that attaching an Enhancement to a step it does not serve is not a
harmless approximation: it interrupts at the wrong moment and dilutes the
attachments that are correct. This is why the field is optional and why four
Enhancements declare nothing. The reasoning is recorded in the 2026-08-03
amendment to ADR-018 so that it survives this phase.

**Why `implement` is a legitimate target despite ADR-018's wording.** That ADR
says guidance attached to `implement` "would sit one level above the step that
acts on it". The sentence is about `react-doctor`, which has a lower acting
step. The rule it serves is *mount at the step that acts on the guidance*, and
UI-building guidance has no lower step — `tdd` writes tests and `code-review`
examines diffs. The distinction is recorded in the same amendment; a reviewer
reading ADR-018 alone would otherwise read the three `implement` mounts as a
violation.

**An adjacent gap, deliberately not closed.** Nothing validates that a
development loop's declared `steps` each correspond to a declared path that
writes them. A step can be named and never materialize — which is close to the
v0.9 defect FR-36 corrected, where `implement` was vendored but never named. The
generation-time error above catches the mount-relevant half of it. Closing it
properly belongs with whatever adds the second development loop, since that is
the first time a loop's step list will be written by someone other than its
author.
