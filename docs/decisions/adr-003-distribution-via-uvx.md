# ADR-003: Distribution via uvx (Python), superseding npx plan

- Status: Accepted (2026-07-13)
- Context: The original plan was a Node CLI (`npx create-ai-stack`, degit + @clack/prompts). The project has since moved to a Python implementation named dev-ready, matching the maintainer's primary stack (Python) and the target audience (FastAPI developers who already have uv).
- Decision: Pure Python CLI, `uvx dev-ready`. Node-specific choices are replaced: degit -> GitHub tarball download at pinned commit; @clack/prompts -> questionary (or equivalent); npm publish -> PyPI publish.
- Consequences: Single-language repo; one less runtime assumption for the target audience. The npx name `create-ai-stack` is abandoned.
- Amended by ADR-005: the tarball download is replaced by Copier; the pinning, staging, and all-or-nothing guarantees are unchanged.

## 2026-08-12 amendment — npx re-proposed and rejected again; the real complaint is separated from it

Raised in the `grill-with-docs` session of 2026-08-12 on two stated grounds: that
`npx` would be easier to install, and that the uvx CLI's own screens look plain
next to installers people meet in the Node ecosystem. Recorded because the
question returns, and because the two grounds have nothing to do with each other.

**As a distribution channel, rejected.** dev-ready is Python, and every route to
`npx dev-ready` is worse than what exists: rewriting in TypeScript discards the
Copier foundation ADR-005 chose; an npm wrapper that shells out to uvx makes the
user install Node *and* uv, adding a prerequisite rather than removing one; and
bundling a runtime fails the solo-maintainer budget (NFR-2). NFR-3's promise is
"runnable via uvx with zero prior setup beyond uv itself" — no npx route gets
closer to it.

**The presentation complaint is real and is not about npx.** What reads as
polished in `npx skills add` is `@clack/prompts` — framed boxes, grouped
headings, colour — not the fact that npx launched it. That is terminal
rendering, reachable from Python through questionary styling and the existing
report layer, with no change to distribution and no new runtime. It is scheduled
as its own requirement (FR-44) rather than left attached to a channel that
cannot deliver it.

**Not affected by this rejection:** `npx skills add MoofonLi/dev-ready --skill
dev-ready`. That command runs the cross-agent skills installer, which fetches
the [[Generation Skill]] from this repository's GitHub source. No npm package is
published and no registry receives a submission; npx is only how that installer
is launched. Rejecting npx as dev-ready's distribution channel says nothing
about it.
