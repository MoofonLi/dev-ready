# Superpowers Engineering Flow

This project uses Jesse Vincent's (Obra's) Superpowers Engineering Flow. It is a
default path through a change, not a rule that every task must traverse from
beginning to end. `setup-project` is user-invoked; subsequent steps are
model-invoked. Supporting tools and skills are invoked by the agent as needed.

## The flow chain

### 1. `setup-project`

Configure the generated project before its first start. It covers the superuser,
optional email, and error reporting. Run it again later whenever one setup
section changes.

### 2. `brainstorming`

Explore and refine ideas before writing code. Design documents produced by this
step live under `docs/superpowers/specs/`.

### 3. `using-git-worktrees`

Create and manage isolated Git worktrees for safe, branch-isolated development.

### 4. `writing-plans`

Break the design into an actionable, structured implementation plan. Plans
produced by this step live under `docs/superpowers/plans/`.

### 5. Execution choice: `subagent-driven-development` or `executing-plans`

Choose how to execute the written plan:

- **`subagent-driven-development`**: Split the plan across fresh subagents,
  executing tasks in parallel worktrees with separate review and verification passes.
- **`executing-plans`**: Execute the plan step-by-step in the current session.

This fork is a choice between two execution styles, not a skipped step.

### 6. `test-driven-development`

Implement plan items using test-driven development (red-green-refactor) at agreed seams.

### 7. `requesting-code-review`

Request and receive automated code review on the implementation before finishing the branch.
`receiving-code-review` handles review feedback.

### 8. `finishing-a-development-branch`

Verify, clean up, and integrate the completed branch. `verification-before-completion`
ensures all tests pass and invariants hold.

## Checkpoints and session boundaries

The flow does not need to finish in one session. An accepted design in
`docs/superpowers/specs/` or a structured plan in `docs/superpowers/plans/` is a
durable checkpoint; stopping after planning is a successful session.

## Platform notes

On macOS and Linux, dev-ready ensures scripts within this flow are marked executable.
On Windows, file execution depends on the configured shell environment (such as WSL, Git Bash, or PowerShell).
