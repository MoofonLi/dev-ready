---
name: planning
description: Cut a dev-ready version into an ordered set of implementation phases and write the version plan (docs/handoff/<version>/<version>-plan.md) that the handoff skill consumes. Use when starting a new version, breaking a version's FRs into phases, or writing/updating a <version>-plan.md - e.g. "plan v0.4", "break v0.4 into phases", "start the v0.4 plan".
---

# dev-ready Version Planner

Produce `docs/handoff/<version>/<version>-plan.md`: the Tech Lead's authoritative
breakdown of a version into ordered phases. This file is the source of truth the
`handoff` skill reads when generating each phase's document set, so it must name
concrete FRs, ADRs, `src/dev_ready/...` paths, and acceptance criteria — not
intentions. The Tech Lead writes it and never writes code (ADR-007).

`docs/handoff/` is gitignored (ADR-011) — the plan is a working artifact, not a
committed repo doc. The committed roadmap it draws from is `docs/version-plan.md`.

## Inputs to read first

1. `docs/version-plan.md` — the roadmap: which FRs belong to this version, the
   end goal, integration modes, curation principles.
2. `docs/requirements.md` — the exact FR text for every FR this version claims;
   copy the FR numbers, do not paraphrase scope.
3. `docs/architecture.md` + `docs/decisions/` — the ADRs this version implements
   or is bound by; Module Boundary and Dependency Rules the phases must respect.
4. `docs/cli-spec.md` — current vs planned flags/exit codes this version changes.
5. `pyproject.toml` — the current baseline version (the plan states it explicitly).
6. The previous version's plan under `docs/handoff/<prev>/` — for format and for
   what was deferred into this version.

## How to cut phases

- One phase = one coherent, independently reviewable slice that leaves `main`
  releasable-in-principle (tests green), sized to a focused evening. The CEO has
  limited time; prefer fewer, cohesive phases over many thin ones.
- Order by dependency: foundational infrastructure (models, catalog, flags)
  before the features that consume it. Later phases may depend on earlier ones;
  never the reverse.
- Exactly one phase per version ships the release, and it is the LAST phase. Its
  section must say so and name the version bump (e.g. "bump 0.2.2 → 0.3.0"); this
  is what tells the `handoff` skill to emit `07-release.md` for that phase
  and nothing else (07 grants scoped git authority — never on a non-release
  phase).
- State cross-phase couplings explicitly as "do NOT do X here — phase N owns it",
  so each generated handoff can carry the exclusion.

## What each phase section must contain

Per phase (see the v0.3 plan for the reference shape):

- A title line `## Phase <N> — <summary> (FR-…)` and, if done, a `— COMPLETED
  <date>` marker with a pointer to its execution report.
- The concrete change surface: catalog/manifest entries, `src/dev_ready/...`
  files touched, overlay/verify behavior, with the SENIOR-VERIFIES markers for
  anything that must be checked against a real registry/API at implementation
  time (name the intent, not an unverified string).
- Tests expected (tiers, tmp_path/no-network constraint).
- Acceptance criteria: concrete, checkable generation outcomes.

## Standing constraints block

End the plan with a "Standing constraints (binding for every phase)" section:
the hard rules from `AGENTS.md` restated for this version (pins only in
`manifest.json`, network only in `fetch/`, all-or-nothing generation, no-network
unit tests, Conventional Commits, agents never run state-changing git except the
07-release exemption), any "no new runtime dependencies" rule, module-boundary
discipline, explicit out-of-scope items deferred to later versions, and the
four-command phase-end verification (`uv sync --dev` → `uv run pytest` →
`uv run ruff check .` → `uv run pytest -m network`).

## Finish

- Header: `Status: Accepted (<date>). Written by the Tech Lead (ADR-007). Source
  of truth for phase handoff generation.` plus the scope line (FR range + ADRs)
  and the ship-as/baseline line.
- Tell the CEO the next step: for each phase in order, run the `handoff` skill to
  generate `docs/handoff/<version>/phase-<N>/`, starting with Phase 1.
