# tests

| Tier | Scope | Speed |
|---|---|---|
| `unit/` | Single module, no network, no filesystem outside tmp_path | fast, run on every commit |
| `integration/` | Module combinations: fetch+manifest against recorded fixtures, overlay onto a fixture base | medium, run in PR CI |
| `e2e/` | Full real-network generation and cross-release lifecycle scenarios | slow, run in dedicated PR CI jobs and weekly upstream-bump |

Conventions: pytest, files named `test_*.py`, no network in unit tests (integration uses recorded fixtures where possible). Network tests are deselected by default and invoked explicitly with `pytest -m network`; `test_upgrade_from_release.py` permanently pins the reviewed N-1 release rather than resolving `latest`.
