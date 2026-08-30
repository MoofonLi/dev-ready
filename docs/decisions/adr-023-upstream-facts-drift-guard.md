# ADR-023: Generated content may state facts about upstream only under a pinned-commit drift guard

- Status: **Accepted** (2026-08-05, Moofon). Targets v0.10 and every version after it; generalizes the divergence check FR-38 designed for one file, and binds FR-37 and every later FR that writes an upstream fact into a generated project.
- Context: FR-37 puts the upstream template's tooling into the generated `AGENTS.md` — test runner, linter, formatter, type checkers, and how to run each — so the vendored `code-review` skill's Standards axis has something to resolve to and an implementing agent knows what it is judged by. FR-37's own justification says a single pinned base template (ADR-001, ADR-002) makes the stack "a constant". That is only half true: the pin is a constant *at a moment*, and CI proposes a new one every Monday. Measured against the current pin, upstream has already moved the frontend from npm to Bun and added a **second** backend type checker (`ty`) beside `mypy` — both changes that would silently falsify prose written a month earlier. The shipped v0.9.0 template demonstrates the failure mode rather than predicting it: it tells every generated project to run `npm install`, in a repository that ships `bun.lock` and no npm lockfile, and no test fails. A fact dev-ready asserts about a tree it does not control is a maintenance liability the moment nothing checks it, and wrong instructions are worse for an agent than absent ones — absent instructions make it look, wrong ones make it act.
- Decision: **every factual claim about the upstream template that dev-ready writes into a generated project is mechanically checked against the manifest-pinned commit in CI.** Three rules fix how.
  - **Where the claim's *subject* survives pruning, the check compares in place.** `generate-and-verify` already generates a real project against the pin on every PR, including the weekly upstream-bump PR. The upstream files FR-37's claims are about — `backend/pyproject.toml`, `frontend/package.json`, `backend/scripts/*.sh`, `frontend/components.json`, `bun.lock` — are all present in that project, so the check is a stdlib script run against a tree already on disk. No fetch, no fixture of upstream, no new job.
  - **Where the subject is pruned, the check must resolve the pinned commit and read upstream itself.** This is FR-38's case and the reason it looks more expensive: pruning is applied as a Copier exclude at fetch time, so upstream's root `.gitignore` is never generated at all and there is nothing in the project to compare against. The two shapes are not a style choice; which one applies is decided by the prune list, and reading this record is how a future FR avoids re-deriving that.
  - **Claims are stated at tool-identity granularity, never at version granularity.** `ruff`, `biome`, `playwright`, `alembic` change identity rarely; their version constraints change weekly and are already readable in the files the agent has. A version in generated prose is a second copy of a fact with no owner.
- Considered options:
  - **No guard; rely on human review of the bump PR** — rejected. The bump PR is opened by a scheduled job with a generated body, and the thing that would need noticing is a dependency-group line in a diff nobody is reading for that. This is the mechanism that produced the `npm` defect in the first place, so choosing it again is choosing the same outcome.
  - **Deriving the section from upstream at generation time** — rejected. ADR-002 forbids resolving anything but the pinned commit at generation time, and a project generated offline from the wheel has no upstream to read. It would also make the rendered `AGENTS.md` vary with something other than the user's selection, which `check` and `upgrade` would then have to reason about.
  - **Deriving the section at build time into the template** — rejected as premature rather than wrong. It removes the prose but adds a generator, a committed derived artifact, and a second drift surface between them, to save editing a handful of lines at a cadence measured in months. If the tooling ever becomes per-template (FR-27), this is the option to reopen.
  - **Stating nothing about upstream and pointing at the upstream files instead** — rejected. It is one hop an agent may not take, and the argument recorded in FR-37 for putting the stack in `AGENTS.md` rather than in a separate document applies with equal force to putting it in `backend/pyproject.toml`.
- Consequences: dev-ready accepts a standing obligation it did not have before — the generated project's documentation is now something CI can fail on. That is the point: the class of defect this closes is silent, so the guard has to be the thing that is not. The check is network-marked by inheritance (it runs inside a job that already generates against the pin) and never runs in the offline unit suite; the comparison logic itself is unit-tested offline against a fixture tree, per the FR-16 and ADR-019 pattern this repeats. Every future FR that writes an upstream fact into generated content pays for the guard in the same phase that adds the fact, and an FR that cannot state its claim in a mechanically checkable form has found a claim it should not be making. The rule transfers unchanged to a second base template (FR-27), because it is stated in terms of the pinned commit rather than of this template's contents.

---

## 2026-08-23 amendment — the guard covers every surface dev-ready speaks on, not only generated projects

Decided in the `grill-with-docs` session of 2026-08-22/23 opening v0.13, run
against the shipped v0.12.0 CLI and the installed Generation Skill rather than
against this decision. The rule is unchanged in substance; its scope was too
narrow by exactly one word.

This ADR binds "every factual claim about the upstream template that dev-ready
writes **into a generated project**". Read literally — and it was implemented
literally — the Generation Skill, `README.md`, `README.zh-TW.md`, and the CLI's
own screens are outside it. They are not outside the failure mode. The 2026-08-22
amendment to the version plan already records seven statements in
`skills/dev-ready/SKILL.md` and `docs/cli-spec.md` going false in a single day
with nothing to catch them, and `tests/unit/test_generate_skill.py` compares
identifier lists only, so prose was and is unguarded there.

**The subject of the guard becomes the claim, not its destination.** Every
factual claim about the upstream template that dev-ready states to a user —
in generated content, in the Generation Skill, in either README, in `--help`,
or in a CLI screen — is mechanically checked against the manifest-pinned commit.
The three rules that fix *how* are unchanged: compare in place where the
subject survives pruning, resolve the pinned commit where it does not, and state
claims at tool-identity granularity.

The claim this amendment exists to admit is the one FR-52 needs: **every
dev-ready project is FastAPI + React + PostgreSQL + Docker Compose.** It is true
of the pin, it is the fact whose absence let the Generation Skill ask a
developer what stack they wanted and then ask whether their frontend was React,
and it is checkable in place — `frontend/package.json` survives pruning and
declares `react`. Without this amendment the most useful sentence the interview
can carry is the one the guard has no jurisdiction over.

- **Considered: guarding generated content only and stating the skill's version
  loosely** ("typically React") — rejected. Hedged prose is what an agent
  reasons from; it produced the defect being repaired, and it cannot be tested
  at all, so it converts a checkable claim into an uncheckable one to avoid
  writing the check.
- **Considered: a new ADR rather than an amendment** — rejected. Two decisions
  stating one rule at two scopes is the second-source failure this repository
  keeps paying for.

Consequences: the standing obligation this ADR accepted widens to authored
surfaces, which are edited more often and by hand. An FR that writes an upstream
fact onto any of them pays for its guard in the same phase, and the
"a claim that cannot be stated in mechanically checkable form is a claim that
should not be made" test now applies to the README and the skill as well.

---

## 2026-08-30 amendment — a Recorded Capture is outside the guard, and nothing may rest on it alone

Decided in the `grill-with-docs` session opening v0.13 Phase 6, which puts a
terminal image at the top of `README.md` and `README.zh-TW.md` (FR-54).

The 2026-08-23 amendment made the subject of this guard the claim rather than
its destination: every factual claim about the upstream template that dev-ready
states to a user — including in either README — is mechanically checked against
the pinned commit. FR-54 introduces the first surface that cannot satisfy that
rule. **A recorded terminal image is a claim no test can read.** It shows the
flow menu, the confirmation screen, and the generation report as they were on
the day it was recorded, and every one of those can go false at the next pin
bump, catalog change, or presentation edit with nothing failing.

The honest options were to guard it or to bound it. Guarding it means
regenerating the capture in CI, which needs network, a real clone, a TTY, and a
recorder binary in the job, and commits a regenerated binary on a weekly
cadence — a churning artifact whose diffs no reviewer can read, which is a worse
guard than none because it looks like one. So this amendment bounds it instead.

**A Recorded Capture is recorded, never drawn, and carries no load-bearing
claim.** Three rules:

- **The tape is the artifact; the image is its output.** A committed tape that
  replays the real CLI is what makes the image regenerable at a pin bump. A
  hand-authored screenshot or a drawn mockup is precisely the artifact this ADR
  exists to prevent and may not be substituted, including as a fallback when
  recording is inconvenient.
- **Every fact the capture shows must also be stated in guarded text on the same
  page.** The image illustrates; it never informs alone. A README whose only
  statement of a fact is inside the picture has made an unguarded claim, and the
  fact belongs in prose the existing assertions can resolve against the manifest.
- **Regeneration is a human step, recorded as one.** It is not run in CI and not
  run weekly. `docs/pin-maintenance.md` and the `release` skill name re-recording
  as a step to consider; a stale capture is a known and accepted cost, bounded by
  the rule above to being stale *decoration* rather than a stale *claim*.

- **Considered: regenerating the capture in `generate-and-verify`** — rejected
  for the churn and reviewability reasons above.
- **Considered: no image at all, keeping every README surface guarded** —
  rejected. FR-54 exists because a 305-line wall of bullets does not show a
  reader what the tool does, and the three Static Screens v0.13 built are the
  answer. Refusing the image to preserve a clean guard record optimizes the
  wrong thing.
- **Considered: a new ADR** — rejected on the same ground the 2026-08-23
  amendment rejected it.

Consequences: this ADR now has a named exception, and naming it is the point —
a future reader who finds an unchecked image at the top of the most
drift-guarded document set in the repository would otherwise reasonably conclude
the guard had been forgotten. The exception is narrow: it covers the capture and
nothing else on the page, and the "state it in guarded text too" rule means the
capture can always be deleted without the README losing a fact.
