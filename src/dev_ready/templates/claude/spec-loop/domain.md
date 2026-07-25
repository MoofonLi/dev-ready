# Domain documentation

Before exploring a codebase, read a root `CONTEXT.md` or `CONTEXT-MAP.md` when present, plus relevant architecture decisions. Proceed silently when these files do not exist.

Use glossary terms consistently in specs, tickets, tests, and architecture proposals. Surface conflicts with recorded decisions instead of overriding them silently.

Do not create an empty glossary during project generation. The `domain-modeling` skill creates `CONTEXT.md` lazily when the first real domain term is resolved.
