---
name: grill-with-docs
description: A relentless interview to sharpen a plan or design, which also creates docs (ADR's and glossary) as we go.
disable-model-invocation: true
---

Run a `/grilling` session, using the `/domain-modeling` skill.

## dev-ready conventions (ADR-021)

This is the first step of the internal Spec Loop — **grill-with-docs** → to-spec
→ to-tickets → implement — run wearing the Tech Lead hat.

Grill the phase's scope against what is already on disk, not against intuition:
the FRs in `docs/requirements.md`, the phase section of
`docs/handoff/<version>/<version>-plan.md`, the binding ADRs in
`docs/decisions/`, the module boundaries in `docs/architecture.md`, and the exit
codes in `docs/cli-spec.md`. Anything the interview settles that outlives the
phase belongs in a doc before you move on — a new ADR in `docs/decisions/`, a
term in `CONTEXT.md`. Everything else flows into the spec at the next step.
