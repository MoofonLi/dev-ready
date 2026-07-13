# templates — moved

Overlay assets used to live here but have moved to `src/dev_ready/templates/` so they ship as package data inside the wheel (`[tool.hatch.build.targets.wheel] packages = ["src/dev_ready"]` does not include this repo-root directory).

See `src/dev_ready/templates/` for the current layout:

```
src/dev_ready/templates/
├── claude/      CLAUDE.md template + .claude/skills/ starter skill for generated projects
├── mcp/         .mcp.json (minimal valid JSON, no credentials, safe defaults)
└── docs/        design-doc skeletons (architecture.md, requirements.md)
```

Assets are read via `importlib.resources.files("dev_ready")`, never via a path relative to `__file__` joined with the repo root — this directory is not guaranteed to exist for an installed `uvx dev-ready`.

Security note: user input must never be interpolated into agent instruction files unescaped (see `.bob/security.md`). Templating is exact-token replacement of `{{project_name}}` only, applied to files with a `.tmpl` suffix.
