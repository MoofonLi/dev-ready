# ADR-009: Manifest `vendored` section with enforced provenance (v0.4)

- Status: Proposed (2026-07-17), implemented in v0.4 (FR-15/FR-16/FR-18)
- Context: Vendored snapshots rot silently: once files are copied in, nothing ties them to their origin, and "this is repo X at commit Y" becomes an unverifiable claim. The upstream base template solved this with a manifest pin plus CI verification (ADR-002); vendored content needs the same discipline.
- Decision: `manifest.json` gains `vendored: [{repo, commit, license, paths: [{src, dest}]}]`, validated as strictly as the upstream pin. `scripts/sync_vendored.py` re-materializes snapshots from pins; CI enforces byte-equality between the committed snapshot and `repo@commit` (drift = build failure). A monthly bump workflow (deliberately slower than the weekly base-template bump — skill text churns slowly, solo-maintainer review budget is finite) opens vendored-pin PRs; each bump PR re-checks the upstream LICENSE file. THIRD_PARTY_NOTICES must stay in sync with this section, enforced in CI.
- Consequences: Provenance is enforced, not asserted. Adding a vendored repo has a fixed, known cost (pin entry + snapshot + NOTICES entry, all CI-checked). The generation stamp (FR-11) records vendored pins, giving `dev-ready check`/`upgrade` (v0.6) an accurate basis.

## 2026-08-16 amendment — a notice travels with the copy, for every license

Settled in the v0.11 Phase 3 grilling. This ADR made provenance verifiable
*inside this repository* and stopped there. It says nothing about what reaches
the user's project, and the gap that left is measurable.

**Four vendored repositories copy files into generated projects and none of
them carries a notice.** Measured against the shipped manifest:
`mattpocock/skills` (12 skill directories), `JuliusBrussee/caveman` (1),
`cloudflare/security-audit-skill` (1), and `VoltAgent/awesome-design-md`
(2 documents today, 74 after FR-40). All four are MIT. The two Apache-2.0
skills from `anthropics/skills` do carry `LICENSE.txt`, but only because
upstream keeps that file inside the skill directory and the directory copy
picks it up — not because anything in dev-ready arranges it.

**FR-41 named only `mattpocock/skills`, and that scope does not survive
its own reasoning.** The stated ground is that the notice travels with the
copy. That ground is identical for the other three. Worse, the phase that
would have fixed one of four is the same phase that takes the largest
unfixed source from 2 files to 74. The scope becomes all four.

**The check becomes license-symmetric, and per repository where the
destinations are loose files.** `scripts/check_notices_sync.py` today runs a
rule for `Apache-2.0` alone, once per declared path, expecting each path to be
a directory holding a file whose name starts with `license`. Three of the four
MIT sources fit that shape. `awesome-design-md` does not: its destinations are
74 files named `design-*.md`, each of which would fail the per-path rule. So
the rule drops the license-string condition and runs per repository when a
repository's destinations are files rather than directories.

**Delivery reuses the directory copy and adds one conditional write.** For the
three directory-shaped sources the upstream `LICENSE` is vendored into each
snapshot directory — 14 additional `paths` entries and no code, because
`build_overlay_content`'s `collect` already recurses into directories. The
design references have no directory to ride in, so one notice is written to
`docs/design-md-LICENSE.md` when the selection contains any item declaring
that `vendored_repo`. Writing it unconditionally was rejected: a project that
selected no design reference would carry a notice for content it never
received, and a reviewer would rightly ask why.

- **Considered: one aggregate notices file in the generated project** —
  rejected. It would name sources the project never received unless it were
  made selection-aware, at which point it is the conditional write above with
  more machinery; and it abandons the mechanism FR-41 explicitly chose.
- **Considered: a `notice` field on each vendored entry**, written once per
  repository — rejected for this version. It is the tidier shape and it would
  remove the 12 duplicate copies under `mattpocock/skills`, but it costs a
  manifest field, loader validation, and new overlay code, against 14 lines of
  data and none.

Consequences: the same ~1 KB notice appears 12 times under
`src/dev_ready/templates/claude/skills/` and 12 times in a generated project,
which is duplication accepted deliberately in exchange for no new mechanism.
A future vendored repository cannot be added without a notice reaching the
project, because CI now fails on its absence regardless of license. No legal
conclusion is drawn here or in any user-facing document.
