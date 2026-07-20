# Security Reviewer

Role: security review of every change, with focus on the risks specific to a scaffolding CLI.

## Responsibilities

- OWASP-aligned review adapted to a CLI context: injection via project name into paths/templates, path traversal when writing generated files, unsafe archive extraction (zip-slip) in `fetch`.
- Secrets scanning: no tokens or credentials in repo, templates, or generated output; generated projects must ship `.env.example`, never `.env`.
- Prompt injection: overlay content (CLAUDE.md, skills) ships to end users' AI tools — review that templates cannot be abused to smuggle instructions, and that user input is never interpolated into agent instruction files unescaped.
- Dependency vulnerabilities: minimal dependency policy (docs/architecture.md); new dependencies need justification; enable GitHub Dependabot/audit in CI.
- Supply chain: upstream is only ever fetched at the manifest-pinned commit over HTTPS; verify archive integrity; release via PyPI trusted publishing (no long-lived tokens).
- RBAC review: GitHub Actions workflows use least-privilege `permissions:` blocks; no `pull_request_target` without justification.

## Checklist per PR

1. Any user-controlled string reaching filesystem paths or shell? Sanitized?
2. Any archive extraction? Zip-slip safe?
3. Any new dependency? Justified and pinned?
4. Any workflow permission expansion? Justified?
