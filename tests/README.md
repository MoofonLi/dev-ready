# tests

| Tier | Scope | Speed |
|---|---|---|
| `unit/` | Single module, no network, no filesystem outside tmp_path | fast, run on every commit |
| `integration/` | Module combinations: fetch+manifest against recorded fixtures, overlay onto a fixture base | medium, run in PR CI |
| `e2e/` | Full real-network generation and cross-release lifecycle scenarios | slow, run in dedicated PR CI jobs and weekly upstream-bump |

Conventions: pytest, files named `test_*.py`, no network in unit tests (integration uses recorded fixtures where possible). Network tests are deselected by default and invoked explicitly with `pytest -m network`; `test_upgrade_from_release.py` permanently pins the reviewed N-1 release rather than resolving `latest`. CI has six jobs. The five Ubuntu jobs keep their existing purposes. The sixth,
`windows-lifecycle`, runs the full offline suite plus `tests/e2e/test_init_real.py`
and `tests/e2e/test_upgrade_from_release.py` on Windows so native junctions,
a real `git add -A` exclusion check, v0.11 Pointer Stub conversion, and
moved-project junction repair are exercised. The test suite never calls Git
from inside `src/dev_ready`.

## Adapters to third-party libraries are tested against the real library

Where a module exists to adapt a third-party library to one of our interfaces — `prompts/_questionary_asker.py` behind `Asker` is the current example — **at least one test must drive it through the real library**, not a monkeypatched stand-in. A test that patches the library out and asserts on the arguments we passed can only confirm we passed them; it cannot confirm the library accepts them, and it goes on passing while the adapter is broken for every user. That is exactly how `use_search_filter=True` shipped in v0.10.0 without `use_jk_keys=False`, crashing every interactive `init`.

Fakes injected at *our own* seams stay correct and preferred — most of `test_prompts.py` injects a `FakeAsker` and should. The rule applies only at the outermost boundary, where our arguments cross into code we do not own.

Terminal adapters stay in `unit/`: drive prompt_toolkit over `create_pipe_input()` with a `DummyOutput()` inside `create_app_session()`, which needs no console, touches no network or disk, and runs headless in CI in well under a second. That includes driving one whole `prompts` flow — `collect_answers` down through the real adapter — because `unit/test_prompts.py` already takes the `prompts` package as its unit, and a flow the user actually walks is the only shape that catches a crash *between* two prompts. See the `QuestionaryAsker` section of `unit/test_prompts.py`.
