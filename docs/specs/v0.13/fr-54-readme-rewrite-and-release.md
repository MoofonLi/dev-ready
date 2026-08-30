# Phase 6 — README rewrite, and the release (FR-54)

Status: **Accepted** by Moofon (2026-08-30), by dispatching `to-tickets`
against it (ADR-021).

Version: v0.13

Phase: 6 (final)

Governing decisions: **ADR-023** (upstream facts under a pinned-commit drift
guard), as amended **2026-08-23** (the guard covers every surface dev-ready
speaks on) and **2026-08-30** (a [[Recorded Capture]] is outside the guard, and
nothing may rest on it alone); **ADR-016** (language boundary), whose single
zh-TW exception this phase is the only one permitted to touch; **ADR-021** (the
Spec Loop, and no state-changing git without Moofon's explicit permission for
that specific action); **ADR-003** (presentation), which defines the
[[Static Screen]] the capture records. ADR-002, ADR-024, ADR-029, ADR-031 and
the rest of the binding set remain in force and are untouched here.

---

## Problem Statement

A developer who lands on `README.md` cannot tell what dev-ready does. The file
is 304 lines and 12.5 KB with no image, and it opens on a 60-line wall of
bullets before showing a single thing the tool produces. The one command that
matters is on line 13, above the wall; everything a reader would use to decide
"is this for me" is below it.

It is also a second copy of a contract it does not own. The flag table, the
exit-code table, and the `upgrade` semantics are all in `docs/cli-spec.md`
already, restated here with nothing checking that the two agree. Two of this
version's earlier phases changed that contract — `--dir` now accepts an occupied
destination and exit 4 gained a collision case — and the README would have gone
silently false at both, exactly as seven statements in `skills/dev-ready/SKILL.md`
and `docs/cli-spec.md` went false in a single day during v0.12.

Two more claims in it are already false as of Phase 5: it says there are two
selectable Engineering Flows and that `addyosmani` is "announced as coming
soon", in a version that ships `addyosmani` as the third selectable flow.

`README-pypi.md` carries the same duplication independently — its own flag
table, its own exit-code line — so shedding it in one file and keeping it in the
other ships the defect and a fix for it in the same release.

`README.zh-TW.md` states how the tool is run once, which FR-53 changed, and
states that one flow is marked coming soon, which FR-48 changed. Under ADR-016
those are precisely the conditions that permit touching it at all.

And v0.13 has nothing recorded, no version overview, no CHANGELOG entries, and
four version files still reading `0.12.0`. Nothing ships until that is true.

## Solution

`README.md` becomes a page a reader can finish: one sentence, the command, a
[[Recorded Capture]] of the real CLI, a five-row table of what a project
receives, a three-line quickstart, the three-flow comparison rendering the
manifest's `choose_when`, and links out for everything `docs/cli-spec.md`
already owns. Roughly 90 lines, under a hard ceiling of 100 asserted by test.

The capture is **recorded, never drawn**. A committed VHS tape replays a real
interactive `dev-ready init` — the flow comparison, the Category prompts, the
confirmation screen, the progress stages, and the report — so the image is
regenerable at a pin bump and is the CLI rather than someone's idea of it. Under
ADR-023's 2026-08-30 amendment it carries no load-bearing claim: every fact it
shows is also stated in guarded text on the same page, so deleting the image
would cost the README a picture and not a fact.

`README-pypi.md` gets the same cut, so the duplication leaves the repository
rather than moving within it.

`README.zh-TW.md` keeps its shape — it is already a 79-line focused overview —
and receives the capture, the corrected run-once fact, and the corrected flow
count. It gains nothing the English file is shedding.

Then the version ships: CHANGELOG entries, the v0.13 overview, the doc status
sweep, the four-file bump to `0.13.0`, and the `release` skill run end to end
with Moofon holding git authority throughout.

## User Stories

1. As a developer who found dev-ready in a search result, I want to see what the
   tool produces within the first screenful, so that I can decide whether to
   keep reading without parsing 60 lines of bullets first.
2. As that same developer, I want a recorded terminal image near the top, so
   that I can see the actual interface before installing anything.
3. As a developer evaluating dev-ready, I want the capture to be of the real
   CLI, so that what I see is what I will get rather than a designer's mockup.
4. As a developer choosing an Engineering Flow, I want the three flows compared
   with the criteria that distinguish them, so that I can pick one before
   running the tool rather than at a prompt I have not prepared for.
5. As that developer, I want those criteria to be the same strings the CLI shows
   me, so that the README and the prompt cannot disagree.
6. As a developer who reads `README.md` and then `docs/cli-spec.md`, I want the
   flag table to exist in exactly one of them, so that I never have to work out
   which copy is current.
7. As a developer who needs an exit code, I want one authoritative table, so
   that a script I write against it does not break when the two copies drift.
8. As a developer who wants to try dev-ready immediately, I want a three-line
   quickstart, so that I can generate a project without reading the rest.
9. As a developer, I want to know what a generated project actually contains
   before I generate one, so that I can tell whether the overlay is worth it.
10. As a developer on Windows or an unusual filesystem, I want the requirements
    stated, so that I find out about the link requirement before generation
    fails rather than after.
11. As a potential contributor, I want the development commands to survive the
    cut, so that I can run the suite without opening a second document.
12. As a reader who wants the full contract, I want a clear link to it, so that
    the shortened README costs me one click and not a search.
13. As a Chinese-reading developer, I want the zh-TW overview to say how the
    tool is run today, so that I do not learn `--dir .` from the English file.
14. As a Chinese-reading developer, I want the zh-TW page to say three flows are
    selectable, so that it does not tell me one is coming soon after it arrived.
15. As a Chinese-reading developer, I want the same capture, so that I see the
    interface without switching languages for it.
16. As a Chinese-reading developer, I want the zh-TW page to stay a short
    overview, so that it does not become a second flag reference I must trust.
17. As someone who installs from PyPI, I want the project page to match the
    repository README, so that the two do not describe different tools.
18. As a maintainer, I want the flow criteria in both READMEs asserted against
    the manifest, so that a manifest edit fails the build instead of silently
    falsifying published prose.
19. As a maintainer, I want the READMEs' stack sentence checked against a real
    generated tree at the pin, so that an upstream framework change fails CI
    instead of shipping.
20. As a maintainer, I want a test to fail if a flag table or an exit-code table
    reappears in a README, so that the duplication cannot grow back quietly.
21. As a maintainer, I want a test to fail if `README.md` exceeds 100 lines, so
    that the file cannot creep back to 300 one helpful paragraph at a time.
22. As a maintainer, I want the tape committed, so that the next person to
    re-record does not have to reconstruct the recording setup.
23. As a maintainer, I want the capture's regeneration named as a human step in
    `docs/pin-maintenance.md` and the `release` skill, so that a stale image is
    a known cost rather than a discovery.
24. As a reviewer, I want the ADR to say plainly that the capture is unguarded,
    so that finding an unchecked image in this repository does not read as an
    oversight.
25. As a user upgrading from v0.12, I want a CHANGELOG that names the third
    flow, so that I know a new selection exists.
26. As a user upgrading from v0.12, I want to read that `check` no longer
    reports `.git`, so that I know the false verdict I hit is fixed.
27. As a user upgrading from v0.12, I want `--dir` accepting an occupied
    destination recorded, so that I know the workflow that was refused now works.
28. As a user upgrading from v0.12, I want to know no new selection input is
    required and the stamp stays at version 5, so that I can upgrade without
    preparing answers.
29. As a user of the interactive CLI, I want the CHANGELOG to record that the
    plain-text report ruling was superseded, so that the colour I now see is
    documented rather than surprising.
30. As a user, I want the new runtime dependency recorded, so that a constrained
    environment is not surprised by it.
31. As a maintainer, I want the version overview written before the tag, so that
    the release has a durable record of what it shipped.
32. As a maintainer, I want `AGENTS.md` and the requirements roadmap swept, so
    that they do not still claim v0.13 is planned after it releases.
33. As a maintainer, I want all four version files at `0.13.0`, so that the CLI,
    the wheel, and both plugin manifests report the same version.
34. As Moofon, I want every `commit`, `push`, and `tag` put to me at the moment
    it is due, so that no agent moves the repository's state on my behalf.
35. As Moofon, I want the network suite run before any tag is proposed, so that
    Phase 5's vendoring is exercised against the real upstream first.

## Implementation Decisions

### The capture

- **The tape drives a full interactive `init`.** It records the flow comparison,
  the Category prompts, the confirmation, the four progress stages, and the
  report. The alternative of a `--yes` run was rejected: it omits the flow
  comparison and the confirmation, which are two of the three [[Static Screen]]s
  v0.13 added `rich` for, leaving the capture showing the least distinctive
  part of the product.
- **VHS is the recorder.** It is not currently installed on the recording
  machine and must be (`ttyd` and `ffmpeg` come with it). The plan names VHS and
  offers a recorded SVG only as a *size* fallback; substituting the recorder
  before measuring the output would discard that choice unmeasured.
- **The tape lives at `docs/assets/demo.tape`, its output at
  `docs/assets/demo.gif`.** `docs/assets/` does not exist and is created here.
- **Size ceiling: 1 MB.** Above it, re-record as SVG. The "recorded, not drawn"
  rule survives the substitution; the format does not.
- **Recording needs network and a real clone**, and creates a real project on
  the recording machine. The tape removes its own output directory, and the
  recording is done by hand on macOS with network up.
- **No CI job regenerates it.** Rejected for the reasons in ADR-023's
  2026-08-30 amendment: a weekly-regenerated binary is a guard that cannot be
  reviewed, which is worse than a named exception.
- **Every fact the capture shows is also stated in guarded text on the same
  page**, per that amendment. This is a review criterion for the README, not
  only for the ADR.

### `README.md`

- Target roughly 90 lines; **hard ceiling 100, asserted**.
- **Survives:** badges and the zh-TW link; one sentence; the command; the
  capture; the five-row table; the three-line quickstart; the flow comparison;
  a one-line Requirements statement; the agent-skill install block; the
  development commands; links out; licence.
- **Leaves, to `docs/cli-spec.md`:** the flag table, the exit-code table, the
  `upgrade` semantics paragraph, the v0.8-migration paragraph, "How it works",
  and the Roadmap section.
- **The five rows are:** the base project (FastAPI + React + PostgreSQL +
  Docker Compose at a pinned commit); Canonical Content and `AGENTS.md`; the
  chosen Engineering Flow; optional Enhancements by Category; Agent Target
  [[Skill Link]]s and the `.dev-ready.json` stamp.
- **The flow comparison renders all three flows with all three `choose_when`
  clauses each.** Truncating to one clause per flow was rejected: it makes the
  README's criteria a subset the guard has to special-case, which is where drift
  starts.
- **The agent-skill install block cannot be shortened to two lines.** The
  existing guards require five distinct strings in *both* English READMEs — the
  `SKILL.md` path, the `--list` command, the `INSTALL_COMMAND` exactly once, the
  "Scaffold a FastAPI project with dev-ready" example, and the issues URL. The
  budget is ~10 lines and the cut is sized around it.
- The stack sentence is authored to match a new `ClaimFact` needle exactly.

### `README-pypi.md`

- **Receives the same cut.** This is a deliberate widening past the plan's
  "check `README-pypi.md` for consistency", authorized by Moofon on 2026-08-30.
  The plan's wording would leave the flag table and the exit-code line in the
  file most new users see first.
- Links stay absolute (PyPI cannot resolve repository-relative links), and the
  capture is referenced by its raw GitHub URL for the same reason. The v0.12
  overview link becomes the v0.13 one.

### `README.zh-TW.md`

- **No restructuring.** It is already a 79-line focused overview and is the file
  ADR-016 protects from becoming a translation.
- Three changes only: add the capture; correct the run-once product fact for
  `--dir .`; correct line 24's "兩套可選、一套標成即將推出" to three selectable
  flows with none announced.
- **It does not carry `choose_when`.** Quoting nine lines of English criteria is
  permitted by ADR-016 — they are not authored Chinese — but it would put
  untranslated English into the one file whose job is being readable in Chinese.
  The zh-TW surface list in the guard therefore stays empty.

### CHANGELOG

- **No Breaking changes section for 0.13.0.** Every item widens or fixes.
- Seven entries, none of which an earlier phase may write: FR-44's plain-text
  report ruling superseded; both flow descriptions rewritten a second time in
  two versions; `--dir` accepting an occupied destination and the new exit-4
  collision case; `check` no longer reporting `.git`; the third Engineering
  Flow and the retirement of the last `(coming soon)` row; the Token Optimize
  addition and its widened Category description; `rich` as a runtime dependency.
- `check` no longer reporting `.git` files goes under **Fixed**; `--dir`
  accepting an occupied destination under **Changed**.
- An **Upgrade from v0.12** section: no new selection input required, stamp
  stays at version 5.

### Release

- **Phase 5's remaining work is committed before this phase is dispatched.** As
  of writing, 8 staged and 5 unstaged files remain in the tree. The release
  skill's staging step must not be the first time a reviewer sees them.
- `docs/version_overview/v0.13-overview.md` is written and accepted before any
  commit, per the `release` skill's Step 3. The plan's Phase 6 bullets omit it;
  it is in scope.
- Doc status sweep: `AGENTS.md`'s "Current phase" line, and
  `docs/requirements.md`'s roadmap entry 13 from `PLANNED` to `DONE (v0.13.0)`.
- Bump `pyproject.toml`, `src/dev_ready/__init__.py`, `.claude-plugin/plugin.json`,
  and `.codex-plugin/plugin.json` to `0.13.0`, with `uv.lock`.
- `docs/pin-maintenance.md` and `.agents/skills/release/SKILL.md` gain
  re-recording the capture as a step to consider, per ADR-023's amendment.
- **Git authority is Moofon's throughout.** Every `commit`, `push`, and `tag` is
  asked for at the moment it is due; permission for one is not permission for
  the next. ADR-021 removed the release-phase exemption and this phase does not
  restore it.
- **`uv run pytest -m network` is run by Moofon before any tag is proposed.**
  Six tests are deselected by default and none of Phase 5's vendoring has been
  exercised against the real upstream.

## Testing Decisions

A good test here asserts a published document says what the manifest and the
pinned upstream say — external, observable agreement between two artifacts a
reader can see. It does not assert wording, section order, or how the README is
laid out; those are editorial and will change without a defect.

**Three existing seams; no new ones.** This is deliberate — every assertion this
phase needs is a row in a table that already exists.

1. **`REPEATED_FLOW_SURFACES` in `tests/unit/test_generate_skill.py`.** The
   `RepeatedFlowSurface` `NamedTuple` already carries a `choose_when` field, an
   optional `value_index`, and a `minimum_count`, and the parametrized test
   already resolves values off `CatalogItem`. Phase 6 adds rows for both English
   READMEs across all three flows and both fields, and **corrects** the four
   existing `description` counts — the `README.md` rows assert a count of 2
   today and the cut leaves one occurrence. The counts are corrected, not
   relaxed to "at least once": a minimum of 1 would stop catching a half-updated
   file, which is the case that actually occurs.
2. **`REPOSITORY_CLAIM_FACTS` in `scripts/check_stack_facts.py`.** Phase 1 built
   `claim_root="repository"` for `skills/dev-ready/SKILL.md` and it holds
   exactly one row. Phase 6 adds one `ClaimFact` per English README for the
   stack sentence, reusing the existing `STACK_FACTS` entries for FastAPI,
   React, PostgreSQL, and Docker Compose. Network-marked by inheritance: it runs
   inside `generate-and-verify`, which already generates a real project against
   the pin. The comparison logic stays unit-tested offline against a fixture
   tree in `tests/unit/test_check_stack_facts.py`, per the FR-16 and ADR-019
   pattern.
3. **The README shape guards in `tests/unit/test_generate_skill.py`** —
   `test_skill_installation_and_public_docs_stay_synchronized` and
   `test_public_docs_explain_discovery_agent_use_and_support`. These already
   constrain what the cut must keep and must keep passing unchanged. Extend the
   same file with: `README.md` under 100 lines; the capture referenced from all
   three READMEs; no Markdown table whose header row names a flag or an exit
   code, in either English README; and `addyosmani` present with no "coming
   soon" string anywhere in any README.

**Asserted in both directions where it is cheap.** The line ceiling and the
absent-table assertions are one-directional by nature; the flow-string rows are
already two-directional because a manifest edit and a README edit both move the
comparison.

**Not tested:** the capture's contents. No test opens the image — that is the
exception ADR-023's 2026-08-30 amendment names, and the compensating control is
the rule that every fact it shows is also in guarded text.

**Prior art:** the `RepeatedFlowSurface` rows Phase 1 added for `SKILL.md`;
`tests/unit/test_check_stack_facts.py`'s existing repository-claim cases
(`test_repository_claim_with_upstream_evidence_is_clean` and its two failure
siblings); `tests/unit/test_adr_index.py` for a docs-shape guard.

**Phase-end verification, four commands, in order:** `uv sync --dev` →
`uv run pytest` → `uv run ruff check .` → `uv run pytest -m network`.

## Out of Scope

- **Regenerating the capture in CI.** Rejected in ADR-023's 2026-08-30
  amendment; a ticket proposing it has reopened a closed decision.
- **A hand-drawn or hand-screenshotted image**, including as a fallback when
  recording is inconvenient. The fallback is a recorded SVG.
- **Restructuring `README.zh-TW.md`**, or giving it flag tables, exit codes, or
  `choose_when`.
- **Any change to generation, `check`, `upgrade`, or the finalize transaction.**
  The plan binds Phase 6 not to touch the all-or-nothing guarantee at all.
- **Any manifest change.** `choose_when` and both new catalog entries are
  Phases 1 and 5's; Phase 6 only quotes them.
- **The stamp.** It stays at version 5. A ticket proposing version 6 has found
  something the plan got wrong and must stop and say so.
- **New runtime dependencies.** `rich` was the one authorized for this version.
- **A v0.12.1 patch** for the `.git` defect — offered and declined on
  2026-08-23; it ships here.
- **`headroomlabs-ai/headroom`**, a second base template (FR-27), a `--here`
  flag, and the v0.10.1 Spec Loop escape-hatch leftover — all deferred and
  untouched.

## Further Notes

**Two blockers before dispatch.** Phase 5 is only partly committed — 8 staged
and 5 unstaged files remain in the working tree. And `vhs` is not installed, so
the plan's VERIFY-AT-IMPLEMENTATION gate cannot pass as written. Neither is a
spec question; both are gates on `to-tickets`.

**The uncommitted work already on this branch for Phase 6's grilling:**
`CONTEXT.md` gained the [[Recorded Capture]] term and
`docs/decisions/adr-023-upstream-facts-drift-guard.md` gained the 2026-08-30
amendment. Suggested message: `docs(v0.13): amend ADR-023 for the Recorded
Capture exception`.

**Why the widening to `README-pypi.md` is not scope creep.** FR-54's stated
defect is "two copies with no drift guard". `README-pypi.md` is a third copy.
Fixing two and leaving one is not a smaller version of the fix; it is the same
defect with a smaller denominator.

**The line ceiling is the load-bearing assertion.** Everything else in this
phase can be re-derived by a careful reader of the plan. A README grows back one
reasonable paragraph at a time, and the only thing that has ever stopped it in
this repository is a number a test can compare against.
