# ADR-016: Language boundary — English everywhere dev-ready speaks, Chinese only in outward-facing repository documentation

- Status: **Accepted** (2026-07-26, CEO Moofon). Replaces the CLI-localization ADR issued under this number earlier the same day, withdrawn with FR-25 before either was committed. Records the scope line D-3 reserved for an ADR; closes D-1 in `docs/catalog-candidates.md` as rejected.
- Context: FR-25 would have localized the CLI into Traditional Chinese. It was specced and accepted, then withdrawn the same day once the underlying need was re-examined. The need is **discovery** — a Traditional Chinese speaker deciding whether dev-ready is worth using — not runtime comprehension: someone who cannot tell what the tool does from its README never reaches a prompt or an error message. dev-ready also has no attributable external users yet (the v1.0 real-users gate is still open), so localizing ~88 raise sites was work for a hypothesis. Withdrawing FR-25 removes the feature but leaves open a question FR-25 had answered as a side effect. With a Chinese README about to enter the repository, which files may be Chinese and which may not? Unwritten, that question gets re-decided per file by every future contributor and agent, and the CLI drifts into partial translation one string at a time.
- Decision:
  - **Everything dev-ready emits is English.** Prompts, progress stages, reports, `--help`, and every error message. There is no `--lang`, no `DEV_READY_LANG`, no locale detection, and the stamp records no language.
  - **Everything dev-ready generates is English.** Generated project content — `AGENTS.md`, `CLAUDE.md`, skills, design docs, handoff templates — has a model as its consumer, and English is what models parse most reliably. This is the scope line D-3 established, and the one part of D-3 that survives its rejection.
  - **Source, tests, and internal documentation are English.** `docs/`, `CONTEXT.md`, `AGENTS.md`, decision records, specs, tickets, and commit messages are the maintainer's and the agents' working surface.
  - **Chinese exists in exactly one place: repository documentation addressed to external readers.** Today that is `README.zh-TW.md`. It is a focused overview — what dev-ready is, what it produces, how to run it once — not a translation of `README.md`, and it points to the English README for complete reference.
  - **A Chinese file anywhere else requires amending this record.** The boundary is the decision; case-by-case judgement is precisely what this record exists to prevent.
- Considered options:
  - **Localizing the CLI (FR-25 as specced)** — rejected: ~88 raise sites plus restructuring `check` and `upgrade` return types, paid in full before the first translated word, for a user base that has not yet appeared. Full rationale under D-3 in `docs/version-plan.md`.
  - **A complete Traditional Chinese translation of `README.md`** — rejected: 172 lines that must track the English original forever with no drift guard available, and a stale translation misinforms where no translation merely omits. The sections that would drift fastest (flags, exit codes, development setup) are the ones a committed user reads in English anyway.
  - **One bilingual `README.md`** — rejected: never drifts, but every English reader pays for the Chinese section on arrival, and it does not match the existing README's register.
  - **A CI check comparing the two READMEs** — rejected: the Chinese README is deliberately not equivalent to the English one, so any mechanical comparison measures the wrong thing and manufactures false failures.
  - **No written boundary, decided per file** — rejected: this repository runs on agents that read `AGENTS.md` and these records rather than session history. An unwritten rule is not a rule.
- Consequences: Traditional Chinese speakers are served at the point the evidence says they need it, and nowhere else. `README.zh-TW.md` becomes a maintained artifact, so `AGENTS.md` carries the rule that it tracks product facts rather than English wording — ordinary README edits therefore create no translation debt. Reopening CLI localization requires new evidence, specifically an external non-maintainer user asking for it, rather than a repetition of the original reasoning. One defect FR-25 would have fixed incidentally remains open: `check` builds one list of English sentences and serves it as both the human report and the `--json` payload. That is a machine-interface problem, it is now decoupled from any language question, and it can be raised on its own merits.

## 2026-08-16 amendment — byte-identical vendored content keeps upstream language

FR-40 vendors all 74 design documents from the pinned
`VoltAgent/awesome-design-md` commit under ADR-009's byte-equality drift guard.
One upstream file, `design-md/raycast/DESIGN.md`, contains the Chinese YAML key
`属于:`. The pinned Git object and dev-ready's snapshot have identical SHA-256
hashes, so the original boundary and the vendoring contract cannot both hold
literally: translating the key breaks provenance, while omitting the document
breaks the derived full-set contract.

**Byte-identical vendored third-party content is therefore outside the authored
language boundary.** When a pinned upstream snapshot contains non-English text,
dev-ready preserves those bytes unmodified. Everything dev-ready authors,
composes, renders, or adapts remains English, including manifest metadata,
Generation Skill guidance, mounted guidance, CLI output, source, tests, and
internal documentation. `README.zh-TW.md` remains the only Chinese file authored
by this repository.

- **Considered: translate or normalize the vendored file** — rejected. It would
  make the committed snapshot differ from the pinned source and defeat the
  ADR-009 drift guard.
- **Considered: omit Raycast from the derived set** — rejected. FR-40's set is
  derived rather than curated; silently dropping one source recreates the
  curation problem the requirement removes.
- **Considered: bump the pin to seek a corrected upstream file** — rejected.
  FR-40 explicitly leaves the pin unchanged, and a future upstream correction
  is not evidence available at this pinned commit.

Consequences: language review distinguishes repository-authored text from
verbatim vendored snapshots. This is not permission to introduce localized
runtime or generated guidance, and it creates no second Chinese documentation
surface.
