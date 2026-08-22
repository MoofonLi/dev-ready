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

---

## 2026-08-23 amendment — `rich` enters the runtime and the generation report is colourised, reversing FR-44's plain-text ruling

Decided in the `grill-with-docs` session of 2026-08-22/23 opening v0.13, run
against the shipped v0.12.0 screens. The 2026-08-12 amendment above stands in
full: npx is still rejected as a channel, and the presentation complaint is
still a separate, real requirement. What changes is the answer that requirement
was given.

FR-44 delivered questionary styling plus a re-laid-out report and ruled
explicitly that **the report is not colourised**, on this reasoning:
`render_report` is a pure function, terminal policy belongs to `cli`, and colour
would mean a new permanent policy surface — TTY detection plus a `NO_COLOR`
convention, threaded down — "bought for very little."

That reasoning priced building the policy surface by hand, and the CEO's
2026-08-22 verdict on the shipped result was that the screens are still plain.
Both halves of the trade have moved:

- **The cost is no longer ours to pay.** `rich` enters the runtime dependencies
  by CEO decision. It carries TTY detection, the `NO_COLOR` convention, terminal
  width, and graceful degradation to plain text as existing behaviour. FR-44's
  objection was to authoring that policy, not to colour.
- **The benefit was measured, not assumed.** The v0.12.0 report is 26 lines of
  undifferentiated lowercase text in which the four next steps — the only part a
  user must act on — sit in the middle, below a single line that names nineteen
  standard-compliant agents.

**The purity of `render_report` is preserved, not traded away.** It stays a pure
function of its arguments and returns a string; `rich` renders into that string,
and the TTY and `NO_COLOR` decisions stay at the `cli` boundary where FR-44
correctly placed them. The dependency rule in `docs/architecture.md` — which has
listed rich as "optional" since it was written — records the addition, as every
new runtime dependency must.

The chosen presentation is **whitespace and colour without frames**. Framed
boxes are what the 2026-08-12 amendment identified as the visible signature of
`@clack/prompts`, and they were offered and declined: a box wraps badly on a
narrow terminal and survives a copy-paste worse than indentation does. The same
frameless treatment applies to the flow comparison ADR-024's 2026-08-23
amendment puts above the Engineering Flow menu, so one CLI does not carry two
visual idioms.

`questionary` keeps every interactive prompt. It owns keyboard handling,
cancellation, and the disabled-row rendering an [[Announced Flow]] needs; `rich`
owns the static screens — the pre-generation confirmation, the flow comparison,
and the report. Two libraries with one boundary each, rather than one library
doing something it is not for.

Consequences: the runtime grows a third dependency, against NFR-2's
solo-maintainer budget and ADR-005's minimal-dependency posture — accepted
because the alternative is authoring and maintaining the same policy by hand.
FR-44's plain-text ruling is superseded and the CHANGELOG says so; a user who
pipes `init` to a file or sets `NO_COLOR` sees the plain text FR-44 shipped.
