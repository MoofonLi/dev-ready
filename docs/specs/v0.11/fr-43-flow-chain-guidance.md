# FR-43 — Flow Chain guidance, corrected

Status: Draft (2026-08-15)

Version: v0.11

Phase: 2 (shared with FR-39, which has its own spec and its own acceptance set)

Governing decisions: **ADR-026** (as amended 2026-08-15) places the chain
guidance in the per-flow table FR-39 defines; ADR-023 (a generated statement of
an upstream fact needs a drift guard), ADR-024 (Engineering Flow spine), ADR-016
(language), ADR-021 (process), and the module boundaries in
`docs/architecture.md` are binding. ADR-025 targets v0.12 and nothing here
implements it.

---

## Problem Statement

**The generated guidance misdescribes the skills shipped beside it.** A
generated project's rules file carries one sentence naming the development
chain, and that sentence is wrong in three separate ways.

*It presents the chain as compulsory.* It calls the loop "one end-to-end method"
and prints an unbroken sequence, implying that every change walks the whole
thing. Nothing enforces that, and nothing could: the chain's steps are all
user-invoked. Skipping is already the mechanism's default, and the sentence
describes a discipline the tooling neither has nor wants.

*It turns tools into phases.* It lists `tdd` and `code-review` as peers of
`implement`, when the vendored `implement` skill invokes both of them itself.
A reader following the sentence literally runs three steps where the flow
defines one, and — worse — may treat testing and review as stages that come
*after* implementation rather than as things implementation is made of.

*It omits the step that now comes first.* FR-39 adds a run-once
[[Setup Step]] at the head of every chain. A sentence that starts at
`grill-with-docs` sends a user with an unconfigured project into feature work.

This is generated documentation misdescribing generated content — the same class
of defect FR-36(e) corrected, and it is worth the same treatment.

**FR-43's own stated premise is also wrong, and correcting it strengthens the
conclusion.** The requirement claims that *every* vendored step declares
`disable-model-invocation: true`. Measured at the pinned commit on 2026-08-14,
**6 of the 12 do**. But the six that declare it are exactly the chain entries,
and the six that do not are exactly the tools a step reaches for. Upstream draws
the same line this requirement draws, and drew it first. The premise needed
correcting; the argument built on it survives intact and better evidenced.

**The section is named after the method, not after what the user chose.** The
generated heading reads `## Spec Loop`. The glossary reserves *Spec Loop* for
the method and *[[Engineering Flow]]* for the thing a user selects and the
project records. From v0.11 a project has a named flow chosen from a menu, so a
heading naming the abstract method tells the reader nothing about their own
project.

**There is nowhere for a human to read what the flow actually is.** The rules
file is agent-facing and must stay short. It has room for the chain, the fact
that steps are user-invoked, and one skip criterion — and no room for why the
flow is shaped this way, what each step is for, or the reassurance that a flow
need not be completed in one sitting. A developer wanting that today has to read
twelve vendored skill files and infer it.

## Solution

One corrected sentence, one renamed section, one concrete skip criterion, and
one new human-facing document per flow.

The generated rules file gains a **`## Engineering Flow`** section — named for
what the user chose, not for the method behind it — stating the corrected
six-entry chain, that every step is user-invoked, and a single skip criterion
sharp enough to act on. It stays short, because it is loaded into an agent's
context on every task.

The corrected chain is:

**`setup-project` → `grill-with-docs` → `to-spec` → `to-tickets` → `implement`
→ `improve-codebase-architecture`**

with `tdd`, `code-review`, `diagnosing-bugs`, `codebase-design`, and
`domain-modeling` named as **what a step reaches for**, not as steps.

The skip criterion is **observable behaviour**: start at `implement` when the
change adds no behaviour a user can observe — a rename, a formatting fix, a
dependency bump, a test for behaviour that already works — and start at
`setup-project` or `grill-with-docs` for everything else. One rule, no gap.

A new **`docs/agents/<flow-id>.md`**, written only when that flow is selected,
carries the human-facing explanation: what each step is for, why a flow need not
complete in one session, and when to start partway along.

## User Stories

1. As a developer reading my project's rules file, I want the chain to name the
   steps my project actually has, so that the documentation and the installed
   skills agree.
2. As a developer, I want the setup step named first, so that I configure the
   project before I start building in it.
3. As a developer, I want to be told the chain is a default path rather than a
   rule, so that I do not run a five-step process to fix a typo.
4. As a developer, I want one concrete criterion for starting partway along, so
   that "use judgement" is not the only guidance I am given.
5. As a developer, I want testing and review presented as part of
   implementation, so that I do not treat them as optional stages that come
   afterwards.
6. As a developer, I want the tools a step reaches for named separately from the
   steps, so that I know which things I invoke and which things invoke
   themselves.
7. As an agent loading the project's rules, I want the chain stated in a few
   lines, so that orientation does not consume the context budget for the task.
8. As an agent, I want to be told the steps are user-invoked, so that I do not
   start a grilling session the user did not ask for.
9. As a developer, I want the section named after the flow I chose, so that the
   heading tells me something about my project.
10. As a developer new to the flow, I want a document that explains each step in
    plain terms, so that I can decide how to use it without reading twelve skill
    files.
11. As a developer, I want to be told a flow need not finish in one session, so
    that stopping after the spec feels like a checkpoint rather than a failure.
12. As a developer who chose one flow, I want no document describing a flow I
    did not choose, so that my project does not carry instructions for something
    it does not have.
13. As a developer, I want the human explainer separate from the agent-facing
    rules file, so that neither is compromised to serve the other's audience.
14. As a maintainer, I want the chain sentence authored rather than derived from
    skill metadata, so that it states an order rather than a set.
15. As a maintainer, I want the chain guidance stored per flow, so that the
    second flow supplies its own chain instead of forcing a conditional into
    shared code.
16. As a maintainer, I want a test to fail if an upstream bump changes which
    skills are user-invoked, so that the generated claim cannot quietly become
    false.
17. As a maintainer, I want the exact generated bytes asserted, so that a
    well-meant rewording is a deliberate change rather than an accident.
18. As a reader of this repository, I want the difference between the product's
    chain and this repository's own process recorded, so that the mismatch reads
    as a decision rather than as drift.

## Implementation Decisions

- **The chain guidance is one column of the per-flow table FR-39 defines**,
  keyed by flow id, inside the overlay rendering module. FR-39 owns the table's
  structure and its hand-off column; this spec owns the chain column's content.
  A selected flow with no entry raises an overlay error rather than rendering an
  empty section.
- **The chain is authored, not derived.** Deriving it from which skills declare
  `disable-model-invocation: true` was considered and rejected even though the
  sets match exactly at the current pin: frontmatter yields a *set*, and a chain
  needs an *order*. The match is used as corroborating evidence and as the basis
  for the guard below, never as the source.
- **Six entries, and five named tools.** The chain is `setup-project` →
  `grill-with-docs` → `to-spec` → `to-tickets` → `implement` →
  `improve-codebase-architecture`. `tdd`, `code-review`, `diagnosing-bugs`,
  `codebase-design`, and `domain-modeling` are named as what a step reaches for.
  `setup-project` is a chain entry despite being in no flow's `steps` — it is
  written unconditionally as project infrastructure (ADR-026), and the chain
  describes the project's flow, not the flow item's path list.
- **The skip criterion is observable behaviour**, one rule with no gap.
  Change-size and existing-spec formulations were both rejected: size measures
  diff rather than decision content, and a typo fix has no spec to check for.
- **The generated section is renamed `## Engineering Flow`**, and the template
  token and its rendering helper are renamed with it. The glossary reserves
  *Spec Loop* for the method and *Engineering Flow* for what a user chooses;
  the generated heading follows the glossary.
- **The rules file states that every chain step is user-invoked**, which the
  ADR-023 guard below is what makes safe to say.
- **`docs/agents/<flow-id>.md` needs no new mechanism.** The `mattpocock` flow
  already carries a dev-ready-original path whose destination is the generated
  `docs/agents` directory, so a document added to that source lands at
  `docs/agents/mattpocock.md` under that flow alone, and v0.12 adds its own file
  on its own path. Keying on the flow id is structural rather than coded.
- **The human document carries what the rules file cannot**: each step's
  purpose, that a flow need not complete in one session, and when to start at
  `implement`. Vague judgement guidance in an agent-loaded file is ignored;
  in a human-facing file it is the point.
- **The drift guard is an offline frontmatter test** (ADR-023), shared with
  FR-39 and specified there: the generated claim that the chain's steps are
  user-invoked is a statement about vendored content, so an upstream bump that
  changes that posture must fail the test suite rather than ship a generated
  rules file that lies.
- **The divergence from this repository's own process is recorded, not
  reconciled.** This repository's `AGENTS.md` describes four steps for itself and
  files `improve-codebase-architecture` under architecture hygiene. The
  product's chain is deliberately different — a generated project is being
  configured for the first time and this repository is not, and the sixth entry
  is guidance a new project benefits from more than a maintained one does.

## Testing Decisions

The same seams as FR-39, and no new ones. A good test here asserts the bytes a
generated project receives, because the whole defect class is generated prose
that contradicts generated content — a test that checks the guidance "mentions
the steps" would pass on the sentence being replaced.

1. **The overlay content builder / `apply_overlay`**:
   - The chain sentence's **exact bytes**, asserted on a generated rules file,
     including the six entries in order and the five tools named as tools.
   - The skip criterion's **exact bytes**.
   - The section heading is `## Engineering Flow` and no generated file contains
     a `## Spec Loop` heading.
   - The statement that steps are user-invoked is present.
   - `docs/agents/mattpocock.md` is present when that flow is selected, and no
     document for an unselected flow is written under any selection.
   - A selected flow absent from the table raises an overlay error, asserted
     through a synthetic catalog at this seam.
2. **The offline frontmatter guard**, specified in FR-39: the chain's vendored
   entries and the vendored configuration skill still declare
   `disable-model-invocation: true`, and removing the line from any one of them
   fails the test.

Prior art for exact-bytes assertions on generated guidance already exists in the
overlay suite, which asserts the generated README's and ignore file's contents
rather than their shape. All tests are unit tests, use `tmp_path`, and make no
network call.

## Out of Scope

- **The second flow's chain and document.** `superpowers` supplies its own table
  entry and its own explainer in v0.12.
- **Deriving the chain from frontmatter**, now or later. The measurement that
  makes derivation tempting is recorded as evidence and as a guard, and the
  decision against it is in ADR-026.
- **Changing which skills the flow vendors**, or their order in the manifest's
  `steps` list. The chain is generated prose about the project; `steps` is a
  path list for the catalog.
- **The dev-ready README's flow section.** FR-43 calls for one and Phase 5 owns
  all README work, written once over settled text.
- **This repository's own `AGENTS.md`.** The divergence is recorded, not
  removed.
- **Skill Delivery Mode.** ADR-025 targets v0.12.

## Further Notes

**The corrected premise is worth keeping in the record.** FR-43 was written on
the belief that all twelve vendored skills declare `disable-model-invocation:
true`. Six do. The reason this strengthens rather than weakens the requirement
is that the six are exactly the chain entries — `grill-with-docs`, `to-spec`,
`to-tickets`, `implement`, `improve-codebase-architecture`, and the vendored
configuration skill — and the six that do not are exactly the tools a step
reaches for. The distinction this requirement draws between steps and tools is
one upstream had already drawn in metadata; this spec makes it visible in the
generated text and holds it there with a test.

**Three audiences, three documents, and the split is the design.** The rules
file is short and agent-facing. The per-flow document is long and human-facing.
dev-ready's own README, in Phase 5, addresses someone who has not adopted
dev-ready at all. Collapsing any two of them produces a document that serves
neither audience — which is how the single sentence being corrected came to
carry a compulsory-sounding chain in a file that had no room to explain it.
