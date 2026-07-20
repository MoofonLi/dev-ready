# ADR-004: Interactive prompts with a non-interactive escape hatch

- Status: Accepted
- Context: Good first-run UX needs prompts; CI and scripted use cannot answer prompts.
- Decision: Interactive by default; `--yes` plus explicit flags cover every prompt.
- Consequences: All prompt logic must route through a single answers model so both paths share one code path.
