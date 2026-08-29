# Phase 4 — Generation Intent leaves the terminal-input package

Status: **Accepted** by Moofon (2026-08-29), by dispatching `to-tickets`
against it (ADR-021).

Version: v0.13

Phase: 4 (second deepening; this phase carries no FR)

Governing decisions: **ADR-004** (interactive prompts with a non-interactive
escape hatch — flag and prompt adapters write one intent model);
**ADR-021** (the Spec Loop). The stamp stays at version 5. ADR-002, ADR-010,
ADR-016, ADR-017, ADR-018, and ADR-024 remain binding.

Source: the `improve-codebase-architecture` scan of 2026-08-29 and the grilling
that followed the Flow Convention deepening. Nine decisions were settled there;
the one that outlives this deepening is already recorded (`CONTEXT.md`'s
[[Generation Intent]] entry). The rest are below.

This is the second of at most two deepenings Phase 4 may land.

---

## Problem Statement

Eleven production modules import `prompts` in order to read catalog selection.
`prompts` is the terminal-input package: its architecture row forbids I/O other
than the terminal, and its docstring claims the `--yes` path never enters it.
Both are false. `--yes` resolves the whole selection through
`ProjectSelection.from_flags`, which lives there, and `recorded` depends on
`prompts` in the module table for a model that has nothing to do with a TTY.

The selection model itself is deep — requirement closure, Engineering Flow
policy, Category derivation sit behind `_from_items` — but the class interface
is twelve construction paths, including CLI flag parsing. Relocating that
surface unchanged fails the deletion test: complexity moves, it does not
concentrate.

A user generating or upgrading a project must see the same flags, the same
prompts, and the same overlay bytes. This deepening changes where intent lives
and which path constructs it, not what a selection means.

## Solution

[[Generation Intent]] becomes its own in-process module, peer to `prompts`.
It holds the resolved name, destination, catalog selection, and Agent Targets.
`prompts` keeps the Asker, collect, and flag-string parsing. overlay, generate,
inspection, recorded, and the other readers import intent, not the terminal
package.

Production construction is one path: resolved ids plus a catalog, with an
optional "Engineering Flow required" switch that `recorded` turns off for stamp
reconstruction. Flag parsing is an adapter in `prompts` that calls that path.
There is no long-term re-export from `prompts`.

## User Stories

1. As overlay rendering, I want to import Generation Intent without importing
   the terminal package, so that applying files does not depend on questionary.
2. As `recorded`, I want to resolve a stamp against the catalog without
   importing `prompts`, so that stamp migration does not sit inside terminal
   collection.
3. As `inspection`, I want to read a ProjectSelection without knowing how it
   was prompted, so that check and verify share one model.
4. As the `--yes` path, I want the same resolved intent I get today, so that
   a scripted run is unchanged.
5. As an interactive user, I want every prompt and confirmation unchanged, so
   that this deepening is invisible on the keyboard.
6. As a caller of `--flow`, `--categories`, and per-Category flags, I want the
   same acceptance and the same error text, so that flag parsing moving package
   is not a contract change.
7. As a maintainer adding a construction path, I want one place that closes
   `requires` and picks the Engineering Flow, so that a third constructor
   cannot silently skip those rules.
8. As `recorded`, I want a stamp without a development loop to reconstruct
   without adopting the Default Set at the intent seam — that adoption stays
   `recorded`'s migration policy — so that inspect-vs-upgrade still differ
   only in policy.
9. As a future architecture review, I want `prompts`' docstring to match the
   wiring, so that `--yes` is not described as never entering a package it
   still enters for collect.
10. As a developer, I want generated overlay bytes and the stamp unchanged, so
    that a module move is not a product change.

## Implementation Decisions

### One module, two types

`intent` holds `ProjectSelection`, `Answers`, `PartialAnswers`, and project-name
validation. `Answers` remains generation-run intent (name, destination,
selection). `ProjectSelection` remains the catalog slice. Forwarding properties
on `Answers` stay. The unused `handoff=` parameter on `from_items` stays.

`prompts` holds Asker, collect, confirmation, and flag-string adapters. It
imports `intent`. `intent` does not import `prompts`.

### One construction path

`from_items` is the production constructor. It gains an optional
`require_development_loop` keyword, defaulting to required. `recorded` calls it
with the switch off. `from_recorded_items` is removed as a public name.

`default_set` and `default_agent_targets` stay on the model. `empty`,
`optional_only`, and `all` may remain as convenience constructors. `from_flags`
and `agent_targets_from_flag` leave the class.

### Flag parsing is a prompts adapter

Flag-string resolution (`none` / `all`, retired ids, Announced Flow errors,
`--agents`) lives in `prompts` and returns a `ProjectSelection` by calling
`from_items`. `cli` calls those adapters, not methods on the model.

### Architecture table

Add `intent` to the module-boundary table. `prompts` collects Generation Intent
via the terminal and parses selection flags; it still must not perform I/O other
than the terminal. `recorded` depends on `manifest`, `stamp`, and `intent` —
not `prompts`. No new ADR.

### Imports

Production modules and tests that need the model import `intent`. `prompts`
does not re-export `Answers` or `ProjectSelection`. Test edits are import
lines and constructor names; assertions of flag and selection behaviour stay.

## Testing Decisions

A good test asserts observable selection and flag behaviour, and that
non-terminal modules no longer import `prompts` for the model. It does not
assert private helper names.

Seams already in use:

- `tests/unit/test_answers.py` — `from_items`, `default_set`, flag adapter
  behaviour (now through the prompts adapter), recorded reconstruction through
  `from_items` with the loop optional.
- `tests/unit/test_prompts.py` — collect and confirmation, still via fake Asker.
- `tests/unit/test_cli.py` — `--yes` and flag wiring.

Add at the intent seam: the model class does not expose `from_flags` or
`from_recorded_items`; `recorded` / `overlay` / `inspection` source does not
import `prompts`.

Existing flag-error strings and Default Set equality tests must pass unchanged
apart from the adapter's function name.

## Out of Scope

- Trimming `Answers` forwarding properties.
- inspection filling an empty loop from the Default Set.
- Changing `optional_only`'s default Agent Target.
- Removing `from_items(..., handoff=)`.
- The Skill Link apply loop.
- Any user-visible flag, prompt, overlay, or stamp change.
- A long-term re-export of the model from `prompts`.

## Further Notes

**No new ADR.** Architecture.md is the record.

**Phase 4 ends here** if this deepening lands: two deepenings, no more.

## Acceptance

- overlay, inspection, and recorded import Generation Intent without importing
  `prompts`;
- `ProjectSelection` has one production construction path from resolved ids;
  flag parsing is not a method on it;
- `--yes`, interactive collect, and flag errors behave as today;
- generated overlay bytes and the stamp are unchanged;
- `docs/architecture.md`'s module table matches the code.
