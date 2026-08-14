---
name: dev-ready
description: Scaffold a new AI-development-ready FastAPI project with `dev-ready init`. Use when the user asks to start, initialize, generate, or scaffold a FastAPI full-stack project and wants safe non-interactive Category, Catalog Item, and Agent Target selection.
---

# Initialize a dev-ready project

Use `uvx dev-ready init` only for creating a new project. Do not use it to modify an existing project.

## Interview

Start with one opening question: ask the developer what they are building and
how they work with coding agents.
Ask at most three follow-up questions, and only about choices the answer left
ambiguous. Do not use a fixed questionnaire for every Category. Infer relevant
Categories and items from the developer's words, and ask about context-saving
preferences when the project description cannot determine Token Optimize.

If the developer already described the project and agent choices, do not ask
them to repeat that information. Present one proposed command with one-line
reasons for every selected Category, item, development loop, and Agent Target.
Hold the proposal for approval and revise it in plain language if the developer
disagrees with a selection.

The approved command is always non-interactive and always includes `--yes`.
The interview replaces dev-ready's own prompts; do not compose a command that
will ask a second set of selection questions. With no human in the loop, use
the Default Set with `--yes` and report what was assumed.

Resolve named agents before proposing the command. An Agent Target goes into
`--agents`. A standard-compliant agent reads the project's `.agents/skills/`
directory directly, so it needs no Agent Target; tell the developer that rather
than silently dropping it. If an agent is in neither list, say that it is
unknown and do not guess a near-miss identifier. If no agent is named, use the
default `claude`; if two agents are named, include both matching targets.

Install this repository skill directly with the cross-agent skills CLI:

```shell
npx skills add MoofonLi/dev-ready --skill dev-ready
```

The installed skill source is `skills/dev-ready/SKILL.md`.

## Resolve the destination safely

Choose a valid project name using letters, digits, `.`, `_`, or `-`, starting with a letter or digit. Resolve the exact `--dir` path before running anything.

Inspect the destination first. If it exists and is non-empty, stop and ask the user to choose another destination or resolve the existing content themselves. Do not delete, empty, overwrite, or automatically retry into a non-empty target.

## Map the interview to the catalog

Use the developer's words to choose from these authored triggers. The id at the
start of each line is the value to place in the corresponding selection flag.

### Categories

- `dev`: You want planning, implementation, and review practices.
- `security`: You need help finding and reducing security risks.
- `quality`: You want stronger testing and implementation review.
- `design`: You care about polished interfaces and design systems.
- `token-optimize`: You want to reduce context use or improve codebase recall.

### Development loops

- `mattpocock`: You want a staged workflow that starts with a written spec and ends with implementation and review.

### dev items

- (none)

### security items

- `security-audit`: You handle accounts, payments, personal data, or other sensitive behavior.

### quality items

- `react-doctor`: You are building or changing a React frontend and want automated React health checks.
- `webapp-testing`: You need browser-level tests for the web app.

### design items

- `frontend-design`: You want a distinctive, polished frontend rather than a generic interface.
- `design-stripe`: You are building a Stripe-style product or want Stripe's design language as a reference.
- `design-linear`: You are building a Linear-style product or want Linear's design language as a reference.

### token-optimize items

- `caveman`: You want short, token-conscious agent responses.
- `code-memory`: You want the agent to preserve and retrieve concise codebase context.

### Agent Targets

- `adal`: You use Adal as your coding agent.
- `aider-desk`: You use Aider Desk as your coding agent.
- `astrbot`: You use AstrBot as your coding agent.
- `augment`: You use Augment as your coding agent.
- `autohand-code`: You use Autohand Code as your coding agent.
- `bob`: You use Bob as your coding agent.
- `claude`: You use Claude Code as your coding agent.
- `codearts-agent`: You use CodeArts Agent as your coding agent.
- `codebuddy`: You use CodeBuddy as your coding agent.
- `codemaker`: You use CodeMaker as your coding agent.
- `codestudio`: You use CodeStudio as your coding agent.
- `command-code`: You use Command Code as your coding agent.
- `continue`: You use Continue as your coding agent.
- `cortex`: You use Cortex as your coding agent.
- `crush`: You use Crush as your coding agent.
- `devin`: You use Devin as your coding agent.
- `droid`: You use Droid as your coding agent.
- `eve`: You use Eve as your coding agent.
- `forgecode`: You use ForgeCode as your coding agent.
- `goose`: You use Goose as your coding agent.
- `grok`: You use Grok as your coding agent.
- `hermes-agent`: You use Hermes Agent as your coding agent.
- `iflow-cli`: You use iFlow CLI as your coding agent.
- `inference-sh`: You use Inference.sh as your coding agent.
- `jazz`: You use Jazz as your coding agent.
- `junie`: You use Junie as your coding agent.
- `kilo`: You use Kilo as your coding agent.
- `kimchi`: You use Kimchi as your coding agent.
- `kiro-cli`: You use Kiro CLI as your coding agent.
- `kode`: You use Kode as your coding agent.
- `lingma`: You use Lingma as your coding agent.
- `mcpjam`: You use MCPJam as your coding agent.
- `minimax-code`: You use MiniMax Code as your coding agent.
- `mistral-vibe`: You use Mistral Vibe as your coding agent.
- `moxby`: You use Moxby as your coding agent.
- `mux`: You use Mux as your coding agent.
- `neovate`: You use Neovate as your coding agent.
- `ona`: You use Ona as your coding agent.
- `openclaw`: You use OpenClaw as your coding agent.
- `openhands`: You use OpenHands as your coding agent.
- `pi`: You use Pi as your coding agent.
- `pochi`: You use Pochi as your coding agent.
- `qoder`: You use Qoder as your coding agent.
- `qoder-cn`: You use Qoder CN as your coding agent.
- `qwen-code`: You use Qwen Code as your coding agent.
- `reasonix`: You use Reasonix as your coding agent.
- `roo`: You use Roo as your coding agent.
- `rovodev`: You use Rovo Dev as your coding agent.
- `tabnine-cli`: You use Tabnine CLI as your coding agent.
- `terramind`: You use Terramind as your coding agent.
- `tinycloud`: You use TinyCloud as your coding agent.
- `trae`: You use Trae as your coding agent.
- `trae-cn`: You use Trae CN as your coding agent.
- `windsurf`: You use Windsurf as your coding agent.
- `zcode`: You use ZCode as your coding agent.
- `zencoder`: You use Zencoder as your coding agent.
- `zenflow`: You use Zenflow as your coding agent.

### Standard-compliant agents

These agents read the project's `.agents/skills/` directory directly, where
Canonical Content already lives, so they need no Agent Target:

- `amp`: You use Amp.
- `antigravity`: You use Antigravity.
- `antigravity-cli`: You use Antigravity CLI.
- `cline`: You use Cline.
- `codex`: You use Codex.
- `cursor`: You use Cursor.
- `deepagents`: You use Deep Agents.
- `dexto`: You use Dexto.
- `firebender`: You use Firebender.
- `gemini-cli`: You use Gemini CLI.
- `github-copilot`: You use GitHub Copilot.
- `kimi-code-cli`: You use Kimi Code CLI.
- `loaf`: You use Loaf.
- `opencode`: You use OpenCode.
- `replit`: You use Replit.
- `warp`: You use Warp.
- `zed`: You use Zed.
- `promptscript`: You use PromptScript.
- `universal`: You use a standard-compliant agent with a project skills directory.

Always use `--yes` for agent-driven, non-interactive generation.

With no selection flags, `--yes` accepts the lean Default Set: the mandatory
Spec Loop with no optional Enhancements. Every project also receives
architecture and requirements skeletons as generation infrastructure. Select
user-facing Categories with `--categories IDS`. Narrow Enhancements within
each selected Category with `--dev`, `--security`, `--quality`, `--design`, or
`--token-optimize`. Choose the mandatory loop with `--development-loop ID` if
the manifest offers more than one. Select native Agent Target configuration
independently with `--agents IDS`.

Every selection flag accepts:

- `all` selects every current Enhancement on that flag.
- `none` selects no Category, item, or Agent Target on that flag.
- A comma-separated list selects those ids. Do not add spaces inside the list.

Every generated project resolves `mattpocock`; `--categories none` and
`--dev none` decline Enhancements without removing it. The former selectable
ids `spec-loop`, `tdd`, `diagnosing-bugs`, `code-review`, and `setup-all` now
exit 2 when passed to `--dev`, because their content is part of the mandatory
Dev development loop. Treat the resolved selection shown in the report and
stamp as authoritative.

Unknown Category ids, unknown item ids, unknown Agent Target ids, and conflicting
flags are exit 2 failures; surface the error instead of guessing a replacement.
For example, `--design design-stripe` conflicts with `--categories dev` because
Design was not selected.

The Component-shaped flags `--skills`, `--mcp`, `--no-skills`, `--no-mcp`, and
`--no-docs` were removed. Use the Category flags instead. `--no-handoff` and
`--no-agents` were also removed because dev-ready no longer generates the
Handoff Protocol. Passing any removed flag exits 2; do not retry with an alias.

## Form one command

After the developer approves the proposal, run exactly one command. Keep each
worked example as a one-line answer followed by the command it produces.

A developer says, "I want a lean FastAPI app with the mandatory workflow."
```shell
uvx dev-ready init my-app --yes --dir ./my-app
```

A developer says, "I want every available Category, Enhancement, and Agent Target."

```shell
uvx dev-ready init full-app --yes --categories all --agents all --dir ./full-app
```

A developer says, "I want the mandatory workflow and infrastructure, with no optional Categories, Enhancements, or Agent Targets."

```shell
uvx dev-ready init minimal-app --yes --categories none --agents none --dir ./minimal-app
```

A developer says, "I am building a polished design-focused app and want token-conscious agents with Claude."

```shell
uvx dev-ready init focused-app --yes --development-loop mattpocock --categories dev,design,token-optimize --dev none --design frontend-design,design-stripe --token-optimize code-memory --agents claude --dir ./focused-app
```

Run exactly one selected command. Do not invent flags for language, overwriting, or cleanup.

This skill creates new projects only. For an existing generated project, use
`check` or `upgrade`; `init` must never be aimed at a generated project.

## Handle the result

Treat only exit 0 as success. Every nonzero exit is a failure:

- exit 1: abort or unexpected generation error;
- exit 2: invalid arguments, unknown item id, or conflicting flags;
- exit 3: network, Git, or pinned-template fetch failure;
- exit 4: target conflict, including an existing non-empty target;
- exit 5: generated project failed verification.

Report the command, exit code, and error text. Do not hide the failure, weaken the selection, or retry destructively.

After exit 0, verify that the requested target exists, contains `.dev-ready.json`, and matches the final generation report. Check representative selected outputs when relevant, such as `docs/architecture.md`, `.claude/skills/to-spec/SKILL.md`, or `.mcp.json`. Only then report generation as successful and present the CLI's next steps.
