# ADR-010: Item-level component selection with a data-driven catalog (v0.3)

- Status: Accepted (2026-07-17)
- Context: The `skills` and `mcp` components stop being monolithic in v0.3: they contain independent items (react-doctor, code-memory; later caveman, security-audit, mattpocock subset, anthropics examples). Users must be able to compose freely — e.g. react-doctor without code-memory. One boolean flag per item (`--no-react-doctor`, `--no-code-memory`, ...) explodes the CLI surface with every catalog addition and was rejected.
- Decision: two-level selection.
  - Level 1 (unchanged): the four components skills / mcp / docs / agents, existing flags and checkbox.
  - Level 2 (new, `skills` and `mcp` only): interactive flow shows a second multi-select listing the chosen component's items, all on by default — pressing Enter reproduces today's behavior exactly. Non-interactive: list flags `--skills <ids|all|none>` and `--mcp <ids|all|none>` (comma-separated ids); `--no-skills`/`--no-mcp` remain as aliases for `none`; `--yes` alone still selects everything. Unknown ids exit 2 listing valid ids.
  - The item catalog is data in `manifest.json` (id, description, integration mode per ADR-008, license, source paths). Prompts, overlay, and verify all render from the catalog: adding a skill is a data entry plus assets, never CLI code. `docs` and `agents` remain boolean — each is a single item.
  - The Answers model (ADR-004) carries item sets; the generation stamp (FR-11) records the exact selection, which `dev-ready upgrade` (FR-22) later relies on.
- Consequences: The CLI contract changes once (v0.3) and then absorbs catalog growth as data. Test surface for selection combinations is bounded by catalog-driven generation (one code path) with CI covering all-on, all-off, and a mixed selection. verify checks that exactly the selected items are present.
