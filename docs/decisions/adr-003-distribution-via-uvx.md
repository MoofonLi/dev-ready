# ADR-003: Distribution via uvx (Python), superseding npx plan

- Status: Accepted (2026-07-13)
- Context: The original plan was a Node CLI (`npx create-ai-stack`, degit + @clack/prompts). The project has since moved to a Python implementation named dev-ready, matching the maintainer's primary stack (Python) and the target audience (FastAPI developers who already have uv).
- Decision: Pure Python CLI, `uvx dev-ready`. Node-specific choices are replaced: degit -> GitHub tarball download at pinned commit; @clack/prompts -> questionary (or equivalent); npm publish -> PyPI publish.
- Consequences: Single-language repo; one less runtime assumption for the target audience. The npx name `create-ai-stack` is abandoned.
- Amended by ADR-005: the tarball download is replaced by Copier; the pinning, staging, and all-or-nothing guarantees are unchanged.
