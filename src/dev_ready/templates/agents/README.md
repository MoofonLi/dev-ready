# Handoff Protocol

`protocol.yaml` is the sole runtime authority for role configuration, responsibilities, prohibitions, handoff order, escalation, reporting, and commit authority. Always read it before acting in a protocol role. Prose in this scaffold uses stable role ids; editable titles and model assignments live only in the Protocol Configuration.

## Process-v2 artifacts

- Accepted feature specs are durable under `docs/specs/`.
- Dispatch publishes one tracer-bullet file per ticket under an active phase's `tickets/` directory. Each ticket declares blockers, a file footprint, and whether it is parallel-safe.
- Execution works one frontier ticket at a time and records evidence in `reports/execution-report.md`. A hard blocker is recorded in `reports/problems.md` and escalated according to `protocol.yaml`.
- Verification runs `03-review.md`, `04-qa-review.md`, `05-security-review.md`, and `06-sre-review.md` in order.

Copy `phase-N/` to open an active `phase-<number>/`. Active numeric phase directories are ignored by this directory's `.gitignore`; the Protocol Configuration, this README, the reusable scaffold, and specs remain durable.
