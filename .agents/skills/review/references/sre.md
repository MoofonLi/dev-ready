# SRE / Reliability Reviewer

Role: reliability review. dev-ready has no servers, so "SRE" here means CLI operational quality plus the reliability of generated projects and CI automation.

## Responsibilities

- Observability: CLI output is clear at each stage (prompt, fetch, overlay, verify); `--verbose` flag planned; errors state what failed and what to do next.
- Logging: no silent failures; network errors map to exit code 3 with actionable messages (docs/cli-spec.md).
- Health check: e2e verification confirms the generated project's health endpoint responds — this is the release gate.
- Rollback: generation is all-or-nothing — never leave a partial project directory on failure (write to temp, move on success). Release rollback = yank on PyPI + revert tag.
- Scalability review: n/a for runtime; applies to maintenance — weekly upstream-bump automation must stay green without manual babysitting (ADR-002).

## Checklist per PR

1. Can this change leave a partial/corrupt generated project on failure?
2. Are new failure modes reported with clear messages and correct exit codes?
3. Does this add manual maintenance work that should be automated in CI instead?
