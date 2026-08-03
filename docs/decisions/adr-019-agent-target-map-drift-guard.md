# ADR-019: The Agent Target Map is derived from the reference installer and drift-guarded

- Status: **Accepted** (2026-07-27, CEO Moofon). Targets v0.10; closes the maintenance risk ADR-015 recorded as accepted-and-unmitigated.
- Context: v0.8 declared two Agent Targets, Claude Code and Windsurf, on the understanding that most standard-compliant harnesses read `.agents/skills/` and need no entry. Measurement against the reference installer's own source (`vercel-labs/skills`, `src/agents.ts`, MIT) contradicts that: of 75 declared agents only 19 use `.agents/skills/` at the project level. **Fifty-six declare a unique project directory** — `.factory/skills`, `.forge/skills`, `.goose/skills`, `.grok/skills`, `.junie/skills`, `.kilocode/skills`, `.kiro/skills`, `.roo/skills`, `.openhands/skills`, `.qwen/skills` and more, including three that are not dotted at all (`skills`, `data/skills`, `agent/skills`). A user of any of those 56 gets Canonical Content with no discoverable entry point, and dev-ready appears to support two agents when the gap is a data gap, not a capability gap. ADR-015 anticipated the hazard of transcribing this table by hand — "no FR-16-style byte-equality drift guard, so each declared target must be re-verified at bump time" — and 2 entries becoming 56 makes hand-verification untenable for a solo maintainer. The premise behind that hazard has since changed: the map is machine-readable, and upstream maintains it with its own sync script and CI workflow.
- Decision: treat the agent map as vendored data, not as transcription.
  - **`vercel-labs/skills` joins the manifest `vendored` section** at a pinned 40-hex commit with its MIT grant, exactly like every other vendored source (ADR-009).
  - **A maintainer script derives `agent_targets` from `src/agents.ts` at that commit**, and CI fails on any divergence between the manifest and the pinned source — the FR-16 mechanism applied to a second kind of content. Bumps arrive through the existing monthly vendored-pin workflow.
  - **Only `skills_dir` is derived.** The upstream entries carry `skillsDir`, `globalSkillsDir` and an install probe, and nothing else; `rules_file` and `mcp_file` have no upstream source and remain hand-declared per target, populated for Claude Code alone today.
  - **Global paths are never rendered.** `globalSkillsDir` values point outside the project, and dev-ready writes only inside the target directory (ADR-015); they are parsed and discarded.
- Considered options:
  - **Transcribing all 56 by hand** — rejected: it multiplies the exact risk ADR-015 accepted by 28, and a wrong path writes a Pointer Stub into a directory no agent reads, with nothing to detect it.
  - **Declaring a curated subset of popular agents** — rejected: "popular" has no evidence behind it while dev-ready has zero attributable external users, so the subset would encode a guess and then quietly become the supported list.
  - **Accepting user-supplied paths via the selection flag** — rejected: a user who knows which directory their agent reads did not need dev-ready to write it, and paths supplied at the command line cannot be validated or carried through `check` and `upgrade`.
  - **Depending on the installer at runtime** — rejected: ADR-002 forbids fetching anything at generation time, and it is a Node CLI in a Python tool's hot path.
- Consequences: dev-ready gains a build-time dependency on the shape of a TypeScript object literal it does not control; an upstream refactor breaks the derivation script rather than silently corrupting data, which is the failure mode worth having, but it will break. `manifest.json` grows by roughly 56 entries and the Agent Target selection prompt becomes long enough to need presentation work. Agents that read `.agents/skills/` still need no entry and get no artifacts, so the selection surface must state that plainly or users will read absence as non-support — the misreading that motivated this ADR.

## 2026-08-03 amendment — what "derive the map" actually means

Settled in the v0.10 Phase 3 grilling, measured against `vercel-labs/skills`
at commit `1164afa5f0e21ebd01e6fc11249759353f494ad1`. The original entry stated
the intent correctly but left six mechanics open, and four of them turn out to
be load-bearing rather than incidental. The path this ADR named, `src/agents.ts`,
survived and every entry still carries a literal `skillsDir`.

**The measurement moved, and the shape of it matters more than the number.**
Upstream now declares **76** agents, not 75: **19** use `.agents/skills` and
**57** use something else. But those 57 occupy only **54 distinct directories** —
`.qoder/skills`, `.trae/skills` and `.zencoder/skills` are each claimed by two
agents (`qoder`/`qoder-cn`, `trae`/`trae-cn`, `zencoder`/`zenflow`). This ADR's
"fifty-six declare a unique project directory" conflated two different counts
and no future statement of it should.

**An Agent Target is keyed on the agent id, and the projection is
unique-by-destination-path.** All 57 are declared, so a Qoder-CN user finds
their own agent by name rather than someone else's. Collapsing the pairs at
derivation time was rejected: the script would have to pick a winner, which is
the curation judgment this ADR already refused. Deduplication therefore belongs
in `agent_targets.py`, which owns the target-to-path mapping — without it,
selecting both members of a pair writes one destination twice and generation
dies on the overlay collision check, which is a real guard and must not be
weakened to accommodate this.

**Standard-compliant agents are excluded by construction, not by policy.** A
target whose `skills_dir` is `.agents/skills` would place a Pointer Stub at the
exact path Canonical Content occupies — a fatal collision, not a no-op. The
derivation filters them, and the surface obligation this ADR recorded is
discharged by deriving them as a **second named list** and printing it in both
the selection prompt and the generation report. The report matters as much as
the prompt: a `--yes` user never sees a prompt and is the likeliest to conclude
their agent is unsupported.

**`claude` stays `claude`.** Upstream's id is `claude-code`; the manifest has
said `claude` since v0.8 and that identifier lives in every stamped project and
in the `--agents` contract. The derivation script carries one declared
id-rename and fails loudly if `claude-code` ever leaves upstream. Deriving ids
verbatim would orphan every existing project's `.claude/` artifacts, and no
stamp migration is available to repair it.

**`description` is dropped, not derived.** This ADR said only `skills_dir` is
derived, which is still true — but it left the required `description` field
implicitly hand-written, which for 57 entries is precisely the transcription
risk this ADR exists to remove. Measurement settled it: 50 of the 57 upstream
`displayName` values are the id re-spelled, and the destination directory
carries the remaining recognition (`kilo → .kilocode/skills`). The field becomes
nullable and derived targets carry none; the prompt and report compose their
lines from the id and the paths the target actually writes.

**The vendored entry is provenance-only.** It records repo, commit and the MIT
grant with no `paths`, which `VendoredPin` already permits. Committing a
snapshot of `agents.ts` would let the check run offline, but every vendored
destination is required to resolve inside `src/dev_ready/templates/` — the tree
written into user projects — so it would mean either relaxing that guard or
shipping TypeScript inside the wheel. The divergence check is network-marked
instead; the derivation function is unit-tested offline against a fixture,
including the upstream-shape-change failure.

**The Agent Target default changes, and it is a user-facing contract change.**
An absent `--agents` resolved to every declared target, which at 57 targets and
the Default Set's 12 skills means 684 Pointer Stub files instead of 24. It now
resolves to `claude` — the only target with a rules file and an MCP file, and
already the fallback in `ProjectSelection.optional_only()`. `--agents all` keeps
its meaning and stays available. The interactive prompt pre-selects `claude`
too, on both the Default Set and the custom branch: FR-31 made interactive-empty
and `--yes` produce the same project, and that parity is worth more than
symmetry with FR-36's pre-select-nothing rule, which exists to stop a plain
Enter from dumping the whole catalog — not to forbid a sane default of one.
