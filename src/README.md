# src/dev_ready — module responsibilities

| Module | Responsibility |
|---|---|
| `cli.py` | Argument parsing, command dispatch, exit codes. No generation logic. |
| `prompts/` | Interactive + flag-based answer collection into a single Answers model. |
| `fetch/` | Download upstream snapshot at the manifest-pinned commit. Only module with network access. |
| `overlay/` | Apply dev-ready files onto the fetched base. Local file ops only. |
| `manifest/` | Load/validate manifest.json. Single source of truth for pins. |
| `report/` | Post-generation summary and next steps. Read-only. |

Dependency direction: `cli` depends on everything else; nothing imports `cli`. `fetch` and `overlay` are independent of each other. Full rules in `docs/architecture.md`.
