# Matt Pocock Engineering Flow

This project uses a Spec Loop assembled from Matt Pocock's engineering skills.
It is a default path through a change, not a rule that every task must traverse
from beginning to end. The steps are user-invoked; a step may use supporting
tools internally without turning those tools into more steps.

## The six steps

### 1. `setup-project`

Configure the generated project before its first start. It covers the
superuser, optional email and error reporting, and this flow's tracker and
domain conventions. Run it again later when one setup section changes.

### 2. `grill-with-docs`

Interrogate a feature, plan, or design before committing to a solution. This is
where unclear requirements, trade-offs, domain terms, and decisions are made
explicit and recorded when they need to outlive the conversation.

### 3. `to-spec`

Turn the settled conversation into the durable specification for the change.
The spec says what to build and why, and is accepted before implementation is
split into work.

### 4. `to-tickets`

Cut the accepted spec into tracer-bullet tickets. Each ticket delivers a
vertical behavior slice, declares its blockers and file footprint, and is small
enough to implement and review coherently.

### 5. `implement`

Build one frontier ticket with red-green TDD at the agreed public seams, then
run the repository's complete verification loop. Review is part of this step,
not a later phase; `tdd`, `code-review`, and `diagnosing-bugs` are tools the step
may reach for.

### 6. `improve-codebase-architecture`

After behavior is correct, look for a focused opportunity to deepen module
boundaries, improve testability, or make the design easier for people and agents
to navigate. `codebase-design` and `domain-modeling` support this work.

## Checkpoints and where to start

The flow does not need to finish in one session. An accepted spec and an
approved ticket set are useful checkpoints; stopping there is not a failed run.

Start at `implement` when the change adds no behaviour a user can observe — for
example, a rename, formatting fix, dependency bump, or a test for behaviour that
already works. For everything else, start at `setup-project` when project
configuration is still needed; otherwise start at `grill-with-docs`. That
grilling step confirms even an apparently settled direction against the
project's requirements and records any decision that must endure.
