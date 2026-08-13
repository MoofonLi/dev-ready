# ADR-024: Engineering Flow is the user-facing selection spine, named after its source

- Status: **Accepted** (2026-08-12, CEO Moofon). Targets v0.11; amends ADR-017 (removes Dev from the presented Category set), amends ADR-018 (the Default Set stops being an interactive question), and renames the identifier ADR-012 froze.
- Context: v0.9 built a three-stage interactive selection — development loop, then Categories, then items — and the shipped v0.10.1 surface runs two stages, one of which does nothing. Measured against the code rather than the design:
  - `_prompt_development_loop` returns early when the catalog declares one loop (`collect.py:258`), so **the loop question has never been asked**. A user is never told what development method their project is getting.
  - Both branches of `Use the Default Set?` (`collect.py:69-85`) produce byte-identical selections, because `default_set.enhancements` is empty and only one loop exists. The first question in the flow **changes nothing**.
  - `dev` is listed among the five Category checkboxes and then force-added whether or not it was checked (`collect.py:186-197`), so it is an option whose selection has no effect. It also holds no Enhancement — the Dev Category's only member is the loop itself.
  - Every item across every selected Category is presented in **one flat checkbox** (`collect.py:213-228`), prefixed with its Category name, rather than one Category at a time.

  These are defects in what FR-30 and FR-31 shipped, of the same kind FR-36 corrected in v0.10, not gaps in the design. Separately, v0.12 and v0.13 will add second and third development loops, which makes the loop question a real choice and makes the identifier `spec-loop` — a description that fits all three candidates, since every one of them is spec-driven — useless as the thing that names *which*.
- Decision: the development loop becomes the **Engineering Flow**, asked first and named after its source.
  - **Engineering Flow is the first selection question**, asked even when the catalog declares one flow. Its job at n=1 is **disclosure, not choice**: the flow is the project's development method, and a user who is never shown it does not know their project has one.
  - **The item id `spec-loop` is renamed `mattpocock`**, with `superpowers` and `addyosmani` reserved for the flows scheduled in v0.12 and v0.13. Flows are named for their source because that is the axis that distinguishes them; `spec-loop` describes a property all three share. `upgrade` carries a `spec-loop` → `mattpocock` alias so existing v5 stamps resolve; **the stamp version does not advance**, because no field is added, removed, or re-typed.
  - **Catalog Items gain `title` and `status` fields.** `title` is the display name (`Matt Pocock's skills`), free of the id's constraints. `status` marks a flow announced but not yet shipped; such an entry is **listed in the interactive menu and rejected by the flags**, with an error that says it is not yet available rather than that it does not exist.
  - **Dev leaves the presented Category set.** The Engineering Flow question is the Dev Category, asked under its own name. `dev` remains a Category id in the manifest, the flag contract, and every stamp — nothing migrates — but it is not offered in a checkbox where selecting it cannot matter.
  - **The four optional Categories are walked one at a time**, in a fixed order, each with its own item checkbox. There is no preceding question about which Categories to enter: declining a Category is pressing Enter on it. This costs a minimal user three additional keystrokes and guarantees every user sees every Category once — the failure mode FR-36 was created to fix, arriving one level up.
  - **The Default Set stops being an interactive question** and remains exactly what ADR-018 needs it for: what `--yes` and the non-interactive path resolve to.
- Considered options:
  - **Engineering Flow as a new concept above the loop**, binding implied Categories and requiring a manifest key, a stamp field, and a v6 migration — rejected. No second flow has been read yet, so the shape such an abstraction would generalize over is unknown; ADR-012's "preset, not framework" and the version plan's "abstractions built before a second user exists usually abstract the wrong thing" both point the same way. Nothing here forecloses it: if superpowers turns out to imply Categories, the migration costs the same in v0.12 as it does now.
  - **Keeping the id `spec-loop` and changing only the display title** — recommended in session and withdrawn. It survives the accuracy test (the loop's twelve skills are `mattpocock/skills` verbatim) but fails the usefulness one: an id's job in a multi-flow catalog is to say which flow, and all three candidates are spec-driven. The rename is also cheapest now, with the v1.0 real-users gate still unmet and no external project to migrate.
  - **Omitting unreleased flows from the menu** — recommended in session and overruled by the CEO. The cost is real and is accepted deliberately: `status` is a third catalog state that the prompts, every selection flag, and the [[Generation Skill]]'s authored trigger list must each handle, for an entry that cannot be chosen. It is accepted to signal that the flow axis is plural before the second flow exists. Placeholder text says only `(coming soon)` — naming a version in shipped UI makes the menu lie the moment the roadmap moves.
  - **Keeping a "which Categories?" filter before the per-Category walk** — rejected: it asks the same axis twice, and a user who does not check Design never learns what Design holds.
- Consequences: The `--development-loop` flag contract changes value, and the FR-24/FR-34 Generation Skill, `docs/cli-spec.md`, and `README.md` change with it; `README.zh-TW.md` changes only if a product fact it states changes (ADR-016). The alias is permanent compatibility surface — `spec-loop` must resolve for as long as v5 stamps exist. `status` entries are dead weight by construction and must be removed as each flow ships, or the menu accumulates promises. Adding a fourth flow is now a data change plus assets, which is the property this decision exists to buy.
- Status update (2026-08-13): amended below — an [[Announced Flow]] is partitioned out of the catalog by the loader rather than carried as an ordinary Catalog Item, the alias is scoped to stamps, and `--flow` becomes the flag spelling.

---

## 2026-08-13 amendment — announced flows leave the catalog, the alias is stamp-scoped, `--flow`

Decided in the `grill-with-docs` session of 2026-08-13 on v0.11 Phase 1, run
against the code this decision names rather than against the decision. Three
corrections; the decision itself is unchanged.

### An Announced Flow is not a Catalog Item, and the loader is what makes that true

This ADR wrote "Catalog Items gain `title` and `status` fields", which reads as:
an announced flow is an ordinary item carrying one extra field. Taken literally
it does not load. A `status` entry declares no `steps`, and `manifest/loader.py`
requires a development loop to declare a non-empty `steps` list, requires every
item to define `paths` or `inject`, and — under ADR-018's deliberate strictness —
requires every mounted Enhancement's mount to name a step of *every* declared
loop. Declaring `superpowers` with no steps therefore fails all six mounted
Enhancements at load and `load_default_manifest()` raises before any command
runs. That is not a broken menu; it is a CLI that cannot start.

`status` stays a manifest field, and **the loader partitions on it**. An entry
carrying `status` is parsed into `ComponentCatalog.announced_loops` and never
enters the component tuples, so `all_items`, `item_ids`, `by_component`,
`ids_in_category`, and `development_loop_ids` cannot see it. Exactly two
consumers read `announced_loops`: the Engineering Flow prompt, and the error
path for a `--flow` value that names one.

- **Considered: declaring them as ordinary loops and exempting them** at each of
  the eight sites that consume `development_loop_ids` — rejected. A missed
  exemption does not fail loudly; it generates a project whose declared flow
  materializes nothing, in front of a user.
- **Considered: a separate top-level manifest key** — rejected as equally safe
  but more expensive later: shipping a flow would become a move between two
  manifest shapes rather than removing one field.

This is why an announced flow is not a [[Catalog Item]] in the glossary's sense:
a Catalog Item is individually selectable, and non-selectability is the whole
point of this one. ADR-018's "every declared development loop" rule is untouched
— an announced flow is not a declared loop.

The prompt makes such an entry genuinely unselectable rather than selectable-then-scolded:
the `Asker` protocol grows a disabled-choice parameter, which questionary
supports natively, so the cursor skips the row.

### The alias is scoped to stamps

This ADR wrote that "`upgrade` carries a `spec-loop` → `mattpocock` alias so
existing v5 stamps resolve." That scope is now explicit and exclusive: the alias
resolves values **read from a stamp**, and a typed `--flow spec-loop` exits 2
with a message naming `mattpocock`, distinguishable from both the unknown-id and
the not-yet-available errors. A stamp records a fact about a project that
already exists and cannot be re-typed; a command can. Absorbing the old value on
the flag path would make the CHANGELOG's one breaking-change entry describe a
break that did not happen, and would leave the retired name in circulation
indefinitely.

The alias lives in `recorded`, once. `docs/architecture.md` already states that
`recorded` is the only place a stamp is resolved against the current catalog and
that stamp-migration rules live there once; `upgrade` was reaching around it to
validate `stamp.development_loop` against the catalog directly, and that check
moves onto the resolved `RecordedProject`. Without the alias every v0.10 project
fails `upgrade` with exit 6, and `check` silently stops inspecting the twelve
loop skills the project actually has.

### `--flow` becomes the flag spelling

This ADR renamed the concept and its value while leaving the flag reading
`--development-loop`, which splits one concept across three names — prompt,
flag, and stamp field. `--flow` and `--development-loop` become two option
strings on one argparse argument, both permanently accepted, with `--flow`
documented. This costs nothing and breaks nothing, and it is cheapest now for
this ADR's own stated reason: the v1.0 real-users gate is unmet. The stamp field
stays `development_loop` — the stamp does not advance in v0.11 and the field is
not user-facing.
