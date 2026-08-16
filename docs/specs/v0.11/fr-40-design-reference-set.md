# FR-40 — The full awesome-design-md set as Design References

Status: Accepted by Moofon (2026-08-16)

Version: v0.11

Phase: 3 (shared with FR-41, which has its own spec and its own acceptance set)

Governing decisions: **ADR-019** (as amended 2026-08-16) sets the derivation
standard this spec applies to a second source, including a script owning a
section of a human-readable file, template-composed values where the loader
requires one, and declared exception tables. **ADR-018** (as amended
2026-08-16) settles that a mounted block renders by Component. ADR-002 (nothing
resolves "latest"), ADR-008 (integration modes), ADR-009 (vendored provenance),
ADR-010 (item-level selection), ADR-014 (truthful overlay lifecycle),
ADR-016 (language), ADR-017 as amended (Category-first selection), ADR-021
(process), and the module boundaries in `docs/architecture.md` are binding.
ADR-025 targets v0.12 and nothing here implements it.

---

## Problem Statement

**dev-ready ships two design directions and calls it a catalog.** The pinned
`VoltAgent/awesome-design-md` repository holds 74 `DESIGN.md` documents. Two of
them — Stripe and Linear — are vendored. The other 72 are not, and nothing
about the pair explains why those two.

For every other Category this curation is defensible, because the items are
tools and a maintainer can argue that one tool is better than another for a
FastAPI project. A Design Reference is not a tool. It is a visual direction,
and its entire value is that the user picks the one they want. A user building
a developer-tools product wants Vercel or Warp. A user building a consumer
banking app wants Revolut or Wise. A user building an editorial site wants The
Verge. dev-ready offers them Stripe or Linear, and the honest answer to "why
only these two" is that somebody had to stop somewhere.

The gap is worse than a missing item, because the user cannot route around it.
There is no flag that fetches a design document, no documented path to add one,
and no way to discover that the other 72 exist. A user who knows the upstream
repository can copy a document in by hand, but that file is then outside the
overlay, absent from the stamp inventory, and — by the ADR-014 rules — a file
`upgrade` has no record of.

**The two documents that do ship carry a second, quieter problem.** Their
descriptions were hand-written to distinguish them: one names a "polished light
interface system", the other a "polished dark product interface system". That
distinction only exists because there are two items. It cannot survive to 74
without a person writing 74 such sentences, which is the transcription risk
ADR-019 exists to remove.

## Solution

**Vendor all 74 documents as ordinary `design` Category Catalog Items, and
derive every field a person would otherwise type.**

A maintainer script reads the pinned commit's directory listing and each brand's
`README.md` heading, and writes both the catalog entries and the block of the
Generation Skill that teaches those identifiers. Nothing about the selection
model changes: Design References stay multi-select, `--design all` and
`--design design-stripe,design-linear` behave exactly as they did in v0.10, and
`docs/design-stripe.md` and `docs/design-linear.md` keep their identifiers and
their destinations, so no existing project is disturbed.

Two consequences of scale are handled rather than absorbed. The Generation
Skill enumerates all 74 identifiers, because no dev-ready command lists the
catalog and an agent that guesses an identifier gets exit 2 — but the script
writes that block, so no person maintains it. And the mounted block injected
into the Engineering Flow's `implement` skill collapses to a single line for
Design References, because 74 individual bullets would be 94% of that file
while telling an agent nothing it can act on.

## User Stories

1. As a developer building a consumer fintech product, I want to select a
   Revolut or Wise design direction, so that my agent builds against a visual
   system that matches the product I am actually building.
2. As a developer building a developer-tools product, I want to select Vercel,
   Warp, or Raycast, so that my interface reads as native to the audience it
   serves.
3. As a developer building an editorial site, I want to select The Verge, so
   that my agent does not default to a SaaS dashboard aesthetic.
4. As a developer who wants a retro direction, I want to select Dell (1996) or
   Nintendo.com (2001), so that a deliberate period aesthetic is a supported
   choice rather than something I fight the tool to get.
5. As a developer who already generated a project with `design-stripe`, I want
   my identifier to keep working, so that this version does not strand my
   project.
6. As a developer who selected both shipped references, I want `upgrade` to run
   without conflict, so that growing the catalog costs me nothing.
7. As a developer with a marketing site and a dashboard, I want to select two
   different directions, so that I can apply one to each surface.
8. As a developer who selected more than one reference, I want dev-ready to
   stay out of deciding which governs which surface, so that the mapping stays
   mine to record in my own architecture document.
9. As a developer running the interactive flow, I want the Design list to be
   filterable by typing, so that 74 rows is a menu rather than a wall.
10. As a developer running the interactive flow, I want each row to fit one
    terminal line, so that the list stays scannable.
11. As a developer who wants no design reference, I want pressing Enter on the
    Design question to select none, so that a longer list does not change what
    declining costs me.
12. As a developer using an agent to compose my command, I want the agent to
    know every valid identifier, so that it does not invent `design-verge` and
    hand me an exit 2.
13. As a developer whose agent proposes a design reference, I want the proposal
    to name a brand I recognise, so that I can approve or reject it without
    opening the catalog.
14. As a developer who selects one design reference, I want my `implement`
    skill to name it, so that my agent knows the document exists while it is
    writing a component.
15. As a developer who selects many design references, I want the `implement`
    skill to stay mostly instructions, so that the guidance is not buried under
    a catalog listing.
16. As a developer running `--categories all`, I want a usable project rather
    than a skill file that is 94% listing, so that the documented "everything"
    example produces something I would actually use.
17. As a developer selecting `security-audit` alongside design references, I
    want its mounted guidance to read exactly as it does today, so that this
    change does not degrade an unrelated selection.
18. As a developer, I want an untouched design document to be treated as
    managed by `upgrade`, so that it is refreshed rather than deleted.
19. As a developer who edited a design document, I want `upgrade` to preserve
    my edit, so that my changes are not silently overwritten.
20. As a developer, I want `uvx dev-ready` to stay fast to install, so that a
    larger catalog does not become a slower tool.
21. As a maintainer, I want the 74 entries generated by a script, so that I
    never hand-type a catalog entry.
22. As a maintainer, I want the script to also write the Generation Skill's
    design block, so that a pin bump cannot leave the contract test red waiting
    for me to type lines.
23. As a maintainer, I want the script re-runnable with byte-identical output,
    so that I can prove the committed state matches the pinned commit.
24. As a maintainer, I want CI to fail on any drift between the pinned commit
    and what is committed, so that the catalog cannot rot silently.
25. As a maintainer, I want the derivation logic testable without the network,
    so that the unit suite stays offline.
26. As a maintainer, I want the script to fail loudly if upstream changes
    shape, so that I find out by a broken script rather than by corrupt data.
27. As a maintainer, I want every deviation from the derivation rule declared
    in a visible table, so that no exception is buried in a conditional.
28. As a maintainer, I want the identifier rule validated against the two
    identifiers already shipped, so that the rule is checked rather than
    asserted.
29. As a maintainer, I want the CI job count unchanged, so that the release
    acceptance list stays correct.
30. As a maintainer bumping the pin later, I want new brands to appear and
    removed brands to disappear by re-running one script, so that catalog
    growth is not a manual task.
31. As a reviewer, I want the wheel size change stated with its denominator, so
    that I can judge whether it matters.
32. As a reviewer, I want to know what the derived descriptions lose against
    the hand-written ones, so that the trade is visible rather than discovered.

## Implementation Decisions

**The document count is 74, and this is a measured figure.** At the pinned
commit, `design-md/` holds 147 markdown files: 74 `DESIGN.md` documents and 73
`README.md` stubs of roughly 210 bytes each. `slack` is the single brand with
no stub. Only `DESIGN.md` files are vendored; the stubs are read at derivation
time for their headings and are not copied. Every prior statement of 103 was a
planning-time estimate and has been corrected in `docs/requirements.md`,
`docs/version-plan.md`, and the version plan.

**Delivery is by vendoring, and the alternative is not merely worse but
destructive.** ADR-002 forbids resolving anything but the pinned commit, so
generation-time fetching would deliver identical bytes through a fourth
integration mode. Worse, an overlay path absent from the content builder is
classified obsolete by the ADR-014 rules, so an untouched design document would
be deleted on the next `upgrade`.

**Identifiers derive by cutting the brand slug at its first dot.** The manifest
identifier pattern forbids dots outright, so five slugs cannot be used as-is.
The rule is self-validating: it reproduces both shipped identifiers exactly
(`stripe` and `linear.app` yield `design-stripe` and `design-linear`) and
collides on none of the 74. One declared exception applies: `x.ai` would yield
a meaningless `design-x` and is overridden to `design-xai`. Deleting the dot
rather than cutting at it was rejected — it yields `design-linearapp`, breaking
an identifier recorded in shipped v5 stamps and forcing a second alias in the
version that already added one.

**Titles derive from the upstream README heading, with three declared
exceptions.** Each stub opens with a heading of the form
`# <Title> Inspired Design System Analysis`, which parses for all 73 that have
one. It beats a naive title-casing of the slug in 15 cases, and it beats it on
exactly the cases a user would notice: `ClickHouse`, `HashiCorp`, `IBM`,
`NVIDIA`, `xAI`, `Dell (1996)`, `Mistral AI`, `Together AI`, `OpenCode AI`,
`RunwayML`, `VoltAgent`, `Nintendo.com (2001)`, `HP`, `Linear`, and `BMW M`.
The three exceptions are `slack` (no stub exists), `bmw-m` (upstream writes
`Bmw-m`), and `theverge` (upstream writes `Theverge`).

**Descriptions are composed from one template, because the field cannot be
dropped and no upstream source covers the set.** ADR-019's answer for Agent
Targets was to make the field nullable and derive nothing; that route is closed
here because the loader validates a catalog item's description as a non-empty
string, and re-typing a recorded field is forbidden in this version. No
upstream field covers all 74 either: the `DESIGN.md` YAML frontmatter carries a
usable description for only 64 of 74, and its values run to roughly 400
characters. The template is `"{Title}-inspired DESIGN.md reference."` and it is
short deliberately, because the description feeds two surfaces that both
multiply by the number selected — the interactive checkbox row and the mounted
block. Measured, the short form holds a checkbox row to 72 characters where a
longer one reached 143 and wrapped on an 80-column terminal.

**The accepted loss is stated rather than hidden.** The two shipped
descriptions distinguish a light interface system from a dark product interface
system. The template erases that distinction. This is accepted because the
brand name is the visual direction for a user choosing here, and because
deriving light-versus-dark from the frontmatter colour block would cover only
64 of 74 and would invent a heuristic upstream never promised.

**All 74 declare a mount on the Engineering Flow's implementation step, and the
injected block renders by Component.** Dropping the mount is not available:
ADR-018 records that for a Catalog Item under `docs`, the mount is the only
discovery path there is, so removing it produces 74 documents nothing in the
project references. But the implementation skill is 448 bytes, and per-item
rendering of every Design Reference appends 6,869 bytes — making the injected
block 93.9% of a file the agent loads on every implementation run, at roughly
1,750 tokens. A `docs` item therefore collapses its identifiers onto one line
pointing at the documentation directory, while a `skills` or `mcp` item keeps
its own bullet and its description. The same selection then costs 1,392 bytes.
Items mounting for timing rather than discovery — the security, quality, and
React health-check skills — render exactly as they do today. A count threshold
was rejected: the number would have no derivation, and Component is a
distinction ADR-018 already draws.

**This is not a pathological case.** `--categories all` is a worked example
inside the Generation Skill and is asserted by its contract test, so an agent
handed "I want everything" composes it by following dev-ready's own
instructions.

**The Generation Skill enumerates all 74 identifiers, and the derivation script
owns that block.** The contract test's equality assertion is kept unchanged.
Measured, the burden is 72 new lines, growing the skill from 11,939 to roughly
17,000 bytes, and the file already carries 57 formulaically-worded Agent Target
lines held equal by the same test. The deciding fact is that no dev-ready
command enumerates the catalog — `init`, `check`, and `upgrade` are the whole
CLI — so an exemption has nowhere to point an offline agent, while an unknown
identifier exits 2 and six real identifiers are not guessable from a brand
name. The script bounds the block by the same rule the contract test already
uses to locate it: from the design items heading to the next heading of equal
depth. It touches nothing else in the file, so the plugin-manifest work in
Phase 4 does not collide with it.

**The script's check mode joins the existing vendored-drift CI job as a fourth
step.** It does not become a sixth job, because the version's release
acceptance names exactly five. The script reads upstream headings and therefore
needs the network when it runs, which matches the Agent Target derivation
script and is maintainer tooling outside the runtime network boundary.

**Selection stays multi-select, and no surface mapping is invented.** Both
shipped references are already recorded together in existing v5 stamps, so
single-select would break the selection contract and strand those projects to
prevent a cost a user can only incur deliberately. Where more than one is
selected, which reference governs which surface is the user's to record in
their own project documents.

**The command-line specification stops enumerating design identifiers.** The
design flag's documentation follows the Agent Target flag, which already
declines to list 57 identifiers and says "comma-separated ids" instead.

**The stamp stays at version 5.** Growing the set of valid Design Reference
identifiers changes no recorded field, adds none, and re-types none.

**Wheel impact, measured.** The vendored total is 2,150,035 bytes at a measured
deflate ratio of 29.2%, so the wheel grows by roughly 600 KB, from 204 KB to
roughly 803 KB. The denominator matters: the runtime dependency tree
`uvx dev-ready` already installs runs to roughly 15 MB, so this is about a 4%
increase in what a user fetches. The 766 KB planning figure was for 103
documents.

## Testing Decisions

**A good test here asserts generated bytes and derived values, never the shape
of the code that produced them.** The catalog is data, the derivation is a pure
transformation, and the generated project is the product. All three are
observable from outside. No test reaches into the rendering helpers or asserts
that a particular function was called.

**Four seams, of which three already exist.** This is deliberate: the feature
adds 72 catalog entries and its correctness should mostly be demonstrated by
existing assertions continuing to hold.

- **The overlay content builder** — the existing highest seam for generated
  output, and the one the previous phase used. It covers the derived documents
  appearing for a given selection, the mounted block in each of its three
  shapes (a documentation-only selection collapsing to one line, a skills-only
  selection keeping per-item bullets, and a mixed selection carrying both), and
  the absence of any design document from a selection that declined the
  Category. The all-74 case is asserted by byte length rather than by content,
  so the test does not become a second copy of the catalog. Prior art:
  `tests/unit/test_overlay.py`.
- **The design-reference derivation function** — the one new seam, shaped to
  match the Agent Target script exactly. A pure function receives the upstream
  listing and headings and returns both the catalog entries and the rendered
  skill block; a writer applies them and takes the same check flag. The pure
  half carries every decision worth testing, so the whole derivation is tested
  offline against an inline fixture with no clone and no network. It covers all
  five dotted slugs including the overridden one, the two shipped identifiers
  being reproduced, the three title exceptions, template composition, rejection
  of an identifier outside the manifest pattern, and a loud failure when the
  upstream heading shape changes. Prior art:
  `tests/unit/test_sync_agent_targets.py`, whose eight failure-case tests are
  the model.
- **Manifest loading** — a regression that the bundled manifest still loads
  with the full derived set present, and that every derived identifier matches
  the manifest identifier pattern. Prior art: `tests/unit/test_manifest.py`.
- **Upgrade** — an untouched design document is classified managed rather than
  obsolete, and a modified one is preserved. Prior art:
  `tests/unit/test_upgrade.py`.

**The Generation Skill's contract test is not modified.** Its equality
assertion between the documented design identifiers and the catalog is the
strongest available check that the script wrote the block correctly, and it
already exists. A test that needed changing to accommodate this feature would
be evidence the feature broke the contract.

**A check-mode test asserts that a hand-edited skill block is detected**, so
the CI guard is demonstrated rather than assumed.

**Every unit test runs offline, inside a temporary directory, and touches no
path outside it.** The network appears only in the CI drift step.

## Out of Scope

- **MIT notice propagation.** FR-41 shares this phase and has its own spec and
  acceptance set.
- **Any mapping from a Design Reference to the surface it governs.** dev-ready
  records none and none is to be invented.
- **Making the design set single-select.** Rejected above.
- **A command that lists the catalog.** The absence of one is a deciding fact
  in this spec, but adding a fourth command is not this version's work.
- **Bumping the `VoltAgent/awesome-design-md` pin.** The set is derived at the
  existing commit.
- **Bringing the Agent Target derivation script up to the same standard.** It
  writes only the manifest and leaves 57 skill lines hand-maintained behind the
  same contract test. Recorded in ADR-019 as a standing weakness, not scheduled
  here.
- **Any change to Skill Delivery Mode.** Pointer Stubs remain the delivery
  mechanism for all of v0.11.
- **A stamp version bump.** Nothing here adds, removes, or re-types a recorded
  field.
- **Vendoring the upstream `README.md` stubs.** They are read at derivation
  time and not shipped.

## Further Notes

**The blocker this phase inherited was resolved in the opposite direction to
the one its framing suggested, and the reason is worth keeping.** The version
plan recorded, three phases early, that the Generation Skill would need roughly
101 hand-written trigger sentences and named this the context-bloat risk
arriving in the artifact least able to absorb it. Two measurements changed the
answer. The count was 74 rather than ~104, so the burden was 72 lines rather
than ~101. And the exemption — relaxing the contract test for a derived
Category — turned out to have nowhere to point, because dev-ready has no
command that enumerates its catalog. The context-bloat objection was answered
not by writing less but by moving the ownership: a script writes the block, so
no person maintains it and no pin bump can leave the suite red.

**Withholding that decision until it could be measured was correct.** Decided
at planning time on the estimate, it would have been decided on a figure that
was wrong by 40%.

**This phase is no longer "mostly mechanical", and that should be said
plainly.** The sequencing rationale in the version plan describes FR-40 and
FR-41 as a vendoring phase. The mounted-block rendering change is real code in
the overlay, and it exists because measurement found a 448-byte file about to
receive 6,869 bytes. Repairing a defect the phase itself creates, rather than
leaving it on the main branch for later phases, is the rule the previous phase
applied to the generation report's ordering.

**One inconsistency in ADR-018 was found and corrected while grounding this
decision.** Its 2026-08-03 amendment lists the two design references among four
Enhancements with "no honest moment" to mount, then mounts both four paragraphs
later. The shipped manifest follows the later statement, and the reconciling
sentence — that a documentation item mounts for discovery rather than for
behaviour — was already present. The earlier paragraph is now marked
superseded.
