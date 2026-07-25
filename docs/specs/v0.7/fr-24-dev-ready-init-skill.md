# FR-24 — AI-Invokable dev-ready Init Skill

Status: Accepted (2026-07-25)

Version: v0.7

Phase: 3

Governing decisions: ADR-008, ADR-009, ADR-010, ADR-013

## Problem Statement

The `dev-ready init` command already provides a stable machine interface, but coding agents do not have a concise, installable instruction package that explains when to use it, how to form safe non-interactive commands, how catalog choices work, and how to respond to errors. Without that package, agents may guess unsupported flags, confuse catalog identifiers, hide failures, or retry destructively into an existing target.

## Solution

Ship one original Agent Skill in the repository that teaches an agent to invoke `dev-ready init` safely through its stable CLI contract. The skill is directly installable from the repository with the open Agent Skills CLI, documents default, none, and mixed selections, and requires success verification. It is a distribution asset for dev-ready itself and is never a generated overlay asset or catalog item.

## User Stories

1. As a user working through a coding agent, I want the agent to recognize when project initialization is appropriate, so that it invokes dev-ready only for relevant tasks.
2. As a user, I want the agent to ask for or infer a safe project name and target, so that generated output lands where intended.
3. As a user, I want the agent to use non-interactive mode correctly, so that automation does not hang waiting for prompts.
4. As a user, I want the agent to distinguish default selection from explicit all, none, and comma-separated item identifiers, so that the generated project matches my intent.
5. As a user, I want examples based only on identifiers that exist in the current catalog, so that copied commands remain valid.
6. As a user, I want component flags and item selections explained together, so that the agent does not request items from a disabled component.
7. As a user, I want aliases and conflict rules explained, so that the agent can interpret the stable machine interface accurately.
8. As a user, I want unknown identifiers surfaced as failures, so that a typo cannot silently change the generated methodology.
9. As a user, I want nonzero exit codes treated as failures, so that the agent never reports success after a rejected or incomplete generation.
10. As a user, I want an existing or non-empty target handled conservatively, so that the agent does not overwrite or destructively retry into my files.
11. As a user, I want the agent to verify successful output, so that it confirms the intended project and generation report exist before continuing.
12. As a user, I want documented exit-code meaning available to the agent, so that fetch, generation, target, and verification failures can be reported clearly.
13. As a user, I want the skill installable directly from the public repository, so that no proprietary plugin mechanism is required.
14. As a user discovering skills through the ecosystem, I want valid name and description metadata, so that the skill can be found and selected for relevant prompts.
15. As a generated-project owner, I want this distribution skill absent from my project, so that repository tooling is not confused with selected overlay methodology.
16. As a maintainer, I want the README, package-facing README, skill, catalog, and CLI examples to agree, so that the public contract has no stale variants.
17. As a maintainer, I want a visible issue-reporting path, so that users can report installation or invocation problems after release.
18. As a CEO, I want public installation and promotion delayed until release gates pass, so that external telemetry points to the final reviewed artifact.

## Implementation Decisions

- The deliverable is one original Agent Skill named `dev-ready`, stored in the repository's standard skills layout and described by the required `name` and `description` frontmatter.
- It is a repository distribution asset, not a generated template, manifest catalog item, vendored third-party skill, wheel overlay asset, or stamp entry.
- The skill teaches the stable FR-14 machine interface: project and target naming, non-interactive operation, component choices, skills and MCP item identifiers, aliases, selection keywords, conflict handling, exit codes, success verification, and existing-target safety.
- Command examples use only currently valid CLI flags and current manifest identifiers. They do not promise planned internationalization or render-target options.
- The skill treats every nonzero exit status as failure. It reports the failure and does not mask it with an automatic destructive retry.
- A target conflict or non-empty destination requires the user to choose a different destination or explicitly resolve the existing content outside the skill's automation.
- The canonical install command is `npx skills add MoofonLi/dev-ready --skill dev-ready` unless implementation-time verification finds that the official CLI contract changed.
- Direct repository and local installation are the supported distribution mechanisms. Claude plugin metadata, a registry submission manifest, and a plugin framework are not required.
- Public documentation provides the canonical install command, discovery guidance, one concise agent-driven example, and a visible issue-reporting link.
- Implementation must re-check the current open Agent Skills and skills CLI contracts before finalizing metadata or commands; contract changes are recorded rather than guessed.
- Public installation, skills.sh telemetry seeding, and the launch post are release-phase external actions, not implementation-phase side effects.

## Testing Decisions

- The primary seam is the repository skill artifact as consumed by a standards-aware parser and command-contract validator. Tests treat its metadata and instructions as the public product.
- Tests validate required frontmatter, canonical skill identity, discoverable layout, and the absence of invented required metadata.
- Command examples are checked against the current CLI option vocabulary and catalog identifiers where practical, including default or all, none, and mixed selections.
- Tests assert that the skill explains invalid identifiers, conflicting flags, target conflicts, nonzero exits, verification, and non-destructive failure handling.
- A complete generation test asserts that neither the output tree nor its managed-file inventory contains the repository distribution skill.
- Documentation tests or focused assertions keep both README variants, the skill, and the canonical install command synchronized.
- Local CLI discovery or installation may be used as a verification gate when the required tool is available, but unit tests do not depend on global installations, a home directory, or network access.
- Existing CLI parser and generation-report tests provide prior art for validating examples against product behavior.

## Out of Scope

- Adding the skill to the generated overlay or manifest catalog.
- Vendoring the skill as third-party content.
- Claude plugin metadata or a general plugin framework unless the verified open standard makes it mandatory.
- Inventing a skills registry submission process.
- Seeding public telemetry, waiting for third-party indexing, or publishing a launch post before the release phase.
- Adding FR-25 internationalization flags, FR-26 render targets, or other future CLI behavior.
- Automatically deleting, emptying, or overwriting an existing target.

## Further Notes

The intended durable source is `skills/dev-ready/SKILL.md`. skills.sh discovery is expected to follow installation telemetry and may lag the release; delayed third-party indexing is a post-release verification item, not a reason to roll back an otherwise valid package release.
