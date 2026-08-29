A step may reach for `tdd`, `code-review`, `diagnosing-bugs`, `codebase-design`, or `domain-modeling` as a tool; those tools are not additional chain entries.

Start at `implement` when the change adds no behaviour a user can observe — a rename, a formatting fix, a dependency bump, or a test for behaviour that already works. Start at `setup-project` or `grill-with-docs` for everything else.

Tracker and domain conventions are in `docs/agents/issue-tracker.md`, `docs/agents/triage-labels.md`, and `docs/agents/domain.md`. Follow those files when a skill asks where to publish specs or tickets; domain terminology is created lazily when a real term is resolved.
