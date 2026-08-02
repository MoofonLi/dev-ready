# ADR-018: The Spec Loop is always generated; the catalog cap becomes a Default Set limit

- Status: **Accepted** (2026-07-27, CEO Moofon). Targets v0.9 (spine, Default Set, cap retirement) and v0.10 (Mount Point injection); amends ADR-012 (the bundle stops being optional and stops counting against a cap) and the version-plan curation principles.
- Status update (2026-08-02): the documentation skeletons leave the Default Set and become always-written infrastructure; see the amendment below. The Default Set is now the Spec Loop alone.
- Context: ADR-012 shipped the Spec Loop as one optional catalog item among ten, deliberately preferring "preset, not framework" while dev-ready had no external users. Two facts have changed. The four-layer loop is now the only part of dev-ready with real usage evidence — this repository has run two full versions through it — and an audit for v0.9 found the shipped bundle is incomplete: `implement`, the loop's entire Execution step and the skill that invokes `tdd` and `code-review`, was never vendored, so generated projects advertise a cycle whose middle is missing. Separately the ten-item cap has stopped measuring the thing it was created to bound. Context bloat is the version-plan's first recorded risk, but the cap counts items, not bytes, so a 50 KB skill and a 2 KB skill consume the same budget and the cap was fully consumed by v0.7 with no relationship to how heavy a generated project actually is.
- Decision:
  - **The Spec Loop is always generated and cannot be declined.** It gains `implement` and a `setup-all` step. The ids of the three items it required (`tdd`, `diagnosing-bugs`, `code-review`) leave the selectable catalog, as does the bundle id that used to make the loop optional.
  - **It is modelled as a mandatory single-select, not as an unnamed constant.** The Dev Category holds exactly one option today — the Matt Pocock loop — and a project must have one. This keeps the loop visible where a user looks for it, records *which* loop a project uses in the stamp, and makes a second loop a data addition rather than a schema migration. It deliberately reopens the "preset, not framework" deferral of ADR-012's D-1 to the minimum extent that costs nothing: a single-valued field today, not a preset ecosystem.
  - **The ten-item cap is retired.** The optional catalog is unbounded; the limit moves to the **Default Set** — the Spec Loop plus the Enhancements declared on-by-default — which is what a user who changes nothing actually pays for.
  - **The Default Set is deliberately small**: the Spec Loop and the project's own documentation skeletons. Every Enhancement is off by default, including the reference design-document templates, which are opinionated style references rather than structure. `--yes` therefore produces a lean project, and the whole catalog is reachable with an explicit "everything" selection.
  - **`project-orientation` is removed from the product.** Its entire content directs the agent to read the root rules file and the design documents, and states where the backend and frontend live — facts the root rules file already carries and that is auto-loaded. It fails the curation principle's own test: a user loses nothing by omitting it. Removal, not recategorization.
  - **Enhancements declare a Mount Point** — the Spec Loop skill their guidance is injected into. `react-doctor` mounts on `code-review`, not on `implement`: `implement` coordinates and delegates, so guidance attached there would sit one level above the step that acts on it. Injection is a third catalog effect kind alongside the existing MCP-server and npm-dev-dependency effects, applied at generation time into a delimited, regenerable block.
  - **Nothing rewrites a skill at runtime.** Spec Loop skills are vendored snapshots under the FR-16 drift guard; a runtime edit would mark the file user-modified and permanently exclude it from `upgrade`. `setup-all` is an opt-in Enhancement that configures a project after generation, never a prerequisite for it: `init` writes working defaults (local-markdown tracker, default domain-doc locations) so the one-command Day-1 promise holds untouched.
- Considered options:
  - **Keeping the Spec Loop optional and merely default-on** — rejected: it preserves a selection nobody should make (half a methodology) while still consuming a cap slot, and Mount Points would have to degrade gracefully when their target is absent.
  - **Making the loop an unnamed constant with no Category and no stamp entry** — rejected after being specified that way: it hides the loop from the menu where users look for it, and it guarantees a schema migration the day a second loop is added, because there would be no field recording which loop a project has.
  - **Locking the whole catalog into a mandatory workflow** — rejected: a user who wants only `caveman` and `security-audit` is legitimate, and with the v1.0 real-users gate still open those users are the likeliest source of the evidence that gate requires.
  - **Replacing the cap with a measured context budget** — a better instrument, and still the right one later; rejected for now because it requires choosing and defending a byte threshold before there is any usage data to calibrate against, while a Default Set limit bounds the same risk by counting what a default install ships.
  - **Listing Enhancement guidance in a table in the generated `AGENTS.md` instead of injecting it** — rejected: the instruction would not be present in the file the agent is executing at the moment it matters.
- Consequences: `--yes` changes meaning — a published interface, so it needs a CHANGELOG entry, a README correction, and coverage in the N-1 lifecycle gate. Five ids (`spec-loop`, `tdd`, `diagnosing-bugs`, `code-review`, `project-orientation`) leave the selectable catalog while remaining in existing stamps, so the v4→v5 migration must map or retire them rather than reject them; `project-orientation` additionally retires its generated file through ADR-014's obsolete-file rules. Generated Spec Loop skills stop being byte-identical to their upstream snapshots once an Enhancement mounts, so THIRD_PARTY_NOTICES must describe them as derived rather than verbatim. Retiring a numeric cap removes a constraint that twice forced a real curation decision; the Default Set limit only protects users who accept defaults, and nothing now bounds a user who selects everything.

---

## 2026-08-02 amendment — documentation skeletons become infrastructure

This ADR defined the Default Set as "the Spec Loop and the project's own
documentation skeletons." Implementation gated those skeletons on the same
boolean that governs the `docs` Component, whose only catalog items are the
`design-stripe` and `design-linear` visual references. The consequence, found
by inspection during the v0.10 grilling: a user who declines the Default Set
and selects no design reference receives no `docs/architecture.md` and no
`docs/requirements.md`, and the generated `AGENTS.md` loses its pointer to
them. The project's own architecture document was reachable only through an
unrelated opinionated style reference.

`docs/architecture.md` and `docs/requirements.md` are therefore **always
written**, alongside `AGENTS.md` and the Spec Loop, and are not selectable.
The Default Set becomes the Spec Loop alone.

The reasoning is this ADR's own, applied one level down: the Spec Loop is
mandatory because a project must have a development loop, and `grill-with-docs`
→ `to-spec` exists to produce durable architecture and requirements documents.
A mandatory process may not have optional outputs. The `architecture` and
`requirements` ids in `default_set.documentation` named no catalog item and
were never selectable in the first place; they are removed rather than
promoted.

- **Considered: promoting them to real catalog items** under Dev — rejected.
  It preserves a selection nobody should make: a project that runs the Spec
  Loop but declines the files the loop writes into.
- **Considered: leaving the coupling and documenting it** — rejected. The
  coupling is not defensible in a sentence, which is the test for whether it
  should exist.

Consequences: every generated project gains two files it could previously
lack, so the managed-file inventory and the `upgrade` path must treat them as
unconditional. Nothing bounds the Default Set below the Spec Loop any more,
which is intended — the limit was always about what a defaulting user pays
for, and two empty skeletons are the floor, not the budget.

---

## 2026-08-02 amendment — `setup-all` retires into the Spec Loop

This ADR made post-generation configuration an opt-in Enhancement under Dev,
with the id `setup-all`. Two observations in the v0.10 grilling retire it as a
selectable item.

The name misleads. It sets up neither "all" nor a group: it is a one-to-one
label for a single vendored skill directory, `setup-matt-pocock-skills`, and it
configures exactly two things — where issues live and where domain docs live.
Read as a container it invites the question "what is inside `setup-all`?", to
which the answer is "nothing, it *is* the skill." A name that provokes a
question with no answer is a defect, and this one did so in practice.

The separation also bought less than it cost. The skill carries
`disable-model-invocation: true`, so an unselected-but-present copy costs disk,
not context — the reason to keep it off a project no longer applies. Its
`triage-labels.md` seed can never fire, because dev-ready ships no `triage`
skill.

**The `setup-all` id is removed from the selectable catalog and the skill joins
the always-generated Spec Loop.** This ADR's "never a prerequisite" rule is
unchanged and is what makes the merge safe: `init` still writes working
defaults, generated content still never instructs a user to run it, and the
skill still only *changes* a configuration that already works.

- **Considered: renaming the id** (`setup-conventions`) — rejected as
  insufficient. It makes the description honest but leaves a selection whose
  only outcomes are "a skill you may never run is on disk" and "it isn't."
- **Considered: removing the skill from the product** under the curation test
  that removed `project-orientation` — rejected. Unlike `project-orientation`,
  it does something the user cannot trivially do themselves: it knows the
  shape of a GitHub or GitLab tracker configuration the loop skills expect.

Consequences: `setup-all` joins the ids that leave the selectable catalog while
remaining in v5 stamps, so the migration maps or retires it as it does the
others. Dev holds no Enhancement at all now — `--dev` accepts only `none` or an
empty selection until a Dev Enhancement exists again.
