# tests

| Tier | Scope | Speed |
|---|---|---|
| `unit/` | Single module, no network, no filesystem outside tmp_path | fast, run on every commit |
| `integration/` | Module combinations: fetch+manifest against recorded fixtures, overlay onto a fixture base | medium, run in PR CI |
| `e2e/` | Full `dev-ready init --yes` run producing a real project; verify it boots and health check responds | slow, run in PR CI and weekly upstream-bump |

Conventions: pytest, files named `test_*.py`, no network in unit tests (integration uses recorded fixtures where possible).
