# Addy Osmani Engineering Flow

This project uses Addy Osmani's Agent Skills as a model-driven Engineering
Flow. It is a default path through a change, not a rule that every task must
traverse from beginning to end. `setup-project` is user-invoked; subsequent
steps are model-invoked. Supporting skills are used by the agent as needed.

## The flow chain

### 1. `setup-project`

Configure the generated project before its first start. It covers the
superuser, optional email, and error reporting. Run it again later whenever one
setup section changes.

### 2. `spec-driven-development`

Define the problem and write its specification before implementation begins.
The specification becomes the durable source for the work that follows.

### 3. `planning-and-task-breakdown`

Turn the accepted specification into an implementation plan at
`tasks/plan.md` and an actionable task list at `tasks/todo.md`.

### 4. `incremental-implementation`

Build the planned work in small, verifiable slices while keeping the project
working between slices.

### 5. `test-driven-development`

Drive each behavior through a failing test, the minimal passing implementation,
and cleanup after the behavior is green.

### 6. `code-review-and-quality`

Review the implementation for correctness, maintainability, and alignment with
the written specification.

### 7. `shipping-and-launch`

Prepare the completed work for release and carry the change through shipping.

## Checkpoints and session boundaries

The flow does not need to finish in one session. A written specification, an
accepted plan, and a completed task slice are useful checkpoints rather than
failed runs.

## Upstream entry points not shipped by dev-ready

dev-ready vendors the selected skill directories, not Addy Osmani's upstream
slash commands or personas. A skill may therefore refer to an entry point such
as `/build` or a persona such as `code-reviewer` that is not installed in this
project. Treat those references as known gaps and follow the skill's underlying
instructions with the generated Engineering Flow instead.
