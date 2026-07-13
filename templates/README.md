# templates — overlay assets

Files here are copied (with light templating: project name, options) onto the fetched base template during Stage 2 of generation.

Planned layout:

```
templates/
├── claude/      CLAUDE.md template + Claude Code skills for generated projects
├── mcp/         MCP server configuration (.mcp.json template)
└── docs/        design-doc templates (architecture, requirements skeletons)
```

Empty during bootstrap; populated in Phase 2. Security note: user input must never be interpolated into agent instruction files unescaped (see .bob/security.md).
