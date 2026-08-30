---
name: dev-ready
description: Scaffold a new AI-development-ready FastAPI project with `dev-ready init`. Use when the user asks to start, initialize, generate, or scaffold a FastAPI full-stack project and wants safe non-interactive Category, Catalog Item, and Agent Target selection.
---

# Initialize a dev-ready project

Use `uvx dev-ready init` only for creating a new project. Do not use it to modify an existing project.

## Interview

A Must-Ask is an obligation to resolve, not to utter. If the developer already
answered one in their own words, do not ask them to repeat that information.
Resolve all seven below, and account for every Must-Ask out loud in the proposal.
This is an interview, not a fixed questionnaire.

### Fixed project facts

Declare these facts; never ask the developer to choose or confirm them. Every
dev-ready project uses FastAPI, React, PostgreSQL, and Docker Compose. Every
dev-ready project has a frontend. The frontend is React.

### Seven Must-Asks

Resolve these in order:

1. **Project name and destination** — Ask the developer for both the project
   name and destination, and repeat both in the proposed command.
2. **How much the developer wants to steer** — Select the Engineering Flow by
   matching their answer to the exact criteria in `Engineering Flows` below.
3. **Whether the project handles accounts, payments, or personal data** — Use
   the answer to decide whether to select `security-audit`.
4. **Whether automated React health checks or browser-level tests are wanted**
   — Resolve `react-doctor` and `webapp-testing` independently.
5. **Interface ambition, and which product's design language to reference** —
   Treat these as two independent sub-questions: the first resolves
   `frontend-design`; the second resolves a `design-<id>`. Neither answer
   implies the other. Match only a product name the developer states. An
   aesthetic without a named product is not a match: explain that, optionally
   offer a few named candidates, and never guess a near-miss identifier. When
   none matches, say "no matching Design Reference" out loud without dropping
   the interface-ambition answer.
6. **Whether context-saving behaviour is wanted** — Resolve the Token Optimize
   items `caveman` and `code-memory` from the answer.
7. **Which coding agents are in use** — Resolve the answer against the Agent
   Target and standard-compliant lists as described below.

Present one proposed command with one-line reasons for every selected Category,
item, Engineering Flow, and Agent Target. Hold the proposal for approval and
revise it in plain language if the developer disagrees with a selection.

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

Ask the developer for a valid project name using letters, digits, `.`, `_`, or
`-`, starting with a letter or digit, and for the exact destination. Repeat both
in the proposed command, including the resolved `--dir` path, before running
anything.

Inspect the destination first and disclose any content already there in the
proposal. Do not decide destination safety yourself: let dev-ready enforce
destination safety when it runs. Do not delete, empty, overwrite, or
automatically retry after a target conflict.

## Map the interview to the catalog

Use the developer's words to choose from these authored triggers. The id at the
start of each line is the value to place in the corresponding selection flag.

### Categories

- `dev`: You want planning, implementation, and review practices.
- `security`: You need help finding and reducing security risks.
- `quality`: You want stronger testing and implementation review.
- `design`: You care about polished interfaces and design systems.
- `token-optimize`: Tools that reduce agent context use, keep output legible, and improve codebase recall.

### Engineering Flows

- `mattpocock`: A user-driven Engineering Flow whose steps stay in one working session.
  - Choose this flow when you want to start each `chain` entry yourself.
  - Choose it when the work's shape needs `grill-with-docs`, `grilling`, or `domain-modeling` before specification.
  - Choose it when one session should carry the work through `to-spec`, `to-tickets`, and `implement`.
- `superpowers`: A model-driven Engineering Flow whose implementation can fan out across fresh subagents.
  - Choose this flow when its model-driven `invocation` should start each chain entry after setup.
  - Choose it when implementation should fan out through `subagent-driven-development` or `executing-plans`.
  - Choose it when `verification-before-completion` should run before work is declared complete.
- `addyosmani`: A model-driven Engineering Flow spanning specification, implementation, production readiness, and shipping.
  - Choose this flow when `spec-driven-development` should produce a written spec before any code exists.
  - Choose it when the work runs to production and wants `security-and-hardening`, `performance-optimization`, and `observability-and-instrumentation` beside the build steps.
  - Choose it when its `chain` should end at `shipping-and-launch` rather than at a finished branch.

`--flow spec-loop` exits 2 with `Engineering Flow id 'spec-loop' was renamed to 'mattpocock'`.
An unknown `--flow` id exits 2 with `unknown Engineering Flow id '<id>'; valid ids: ['addyosmani', 'mattpocock', 'superpowers']`.
Surface the failure and stop; do not guess a replacement.

### dev items

- (none)

### security items

- `security-audit`: You handle accounts, payments, personal data, or other sensitive behavior.

### quality items

- `react-doctor`: You want automated React health checks.
- `webapp-testing`: You want browser-level tests for the web app.

### design items

- `frontend-design`: You want a distinctive, polished frontend rather than a generic interface.
- `design-airbnb`: You want Airbnb's design language as a reference.
- `design-airtable`: You want Airtable's design language as a reference.
- `design-apple`: You want Apple's design language as a reference.
- `design-binance`: You want Binance's design language as a reference.
- `design-bmw`: You want Bmw's design language as a reference.
- `design-bmw-m`: You want BMW M's design language as a reference.
- `design-bugatti`: You want Bugatti's design language as a reference.
- `design-cal`: You want Cal's design language as a reference.
- `design-claude`: You want Claude's design language as a reference.
- `design-clay`: You want Clay's design language as a reference.
- `design-clickhouse`: You want ClickHouse's design language as a reference.
- `design-cohere`: You want Cohere's design language as a reference.
- `design-coinbase`: You want Coinbase's design language as a reference.
- `design-composio`: You want Composio's design language as a reference.
- `design-cursor`: You want Cursor's design language as a reference.
- `design-dell-1996`: You want Dell (1996)'s design language as a reference.
- `design-elevenlabs`: You want Elevenlabs's design language as a reference.
- `design-expo`: You want Expo's design language as a reference.
- `design-ferrari`: You want Ferrari's design language as a reference.
- `design-figma`: You want Figma's design language as a reference.
- `design-framer`: You want Framer's design language as a reference.
- `design-hashicorp`: You want HashiCorp's design language as a reference.
- `design-hp`: You want HP's design language as a reference.
- `design-ibm`: You want IBM's design language as a reference.
- `design-intercom`: You want Intercom's design language as a reference.
- `design-kraken`: You want Kraken's design language as a reference.
- `design-lamborghini`: You want Lamborghini's design language as a reference.
- `design-linear`: You want Linear's design language as a reference.
- `design-lovable`: You want Lovable's design language as a reference.
- `design-mastercard`: You want Mastercard's design language as a reference.
- `design-meta`: You want Meta's design language as a reference.
- `design-minimax`: You want Minimax's design language as a reference.
- `design-mintlify`: You want Mintlify's design language as a reference.
- `design-miro`: You want Miro's design language as a reference.
- `design-mistral`: You want Mistral AI's design language as a reference.
- `design-mongodb`: You want Mongodb's design language as a reference.
- `design-nike`: You want Nike's design language as a reference.
- `design-nintendo-2001`: You want Nintendo.com (2001)'s design language as a reference.
- `design-notion`: You want Notion's design language as a reference.
- `design-nvidia`: You want NVIDIA's design language as a reference.
- `design-ollama`: You want Ollama's design language as a reference.
- `design-opencode`: You want OpenCode AI's design language as a reference.
- `design-pinterest`: You want Pinterest's design language as a reference.
- `design-playstation`: You want Playstation's design language as a reference.
- `design-posthog`: You want Posthog's design language as a reference.
- `design-raycast`: You want Raycast's design language as a reference.
- `design-renault`: You want Renault's design language as a reference.
- `design-replicate`: You want Replicate's design language as a reference.
- `design-resend`: You want Resend's design language as a reference.
- `design-revolut`: You want Revolut's design language as a reference.
- `design-runwayml`: You want RunwayML's design language as a reference.
- `design-sanity`: You want Sanity's design language as a reference.
- `design-sentry`: You want Sentry's design language as a reference.
- `design-shopify`: You want Shopify's design language as a reference.
- `design-slack`: You want Slack's design language as a reference.
- `design-spacex`: You want Spacex's design language as a reference.
- `design-spotify`: You want Spotify's design language as a reference.
- `design-starbucks`: You want Starbucks's design language as a reference.
- `design-stripe`: You want Stripe's design language as a reference.
- `design-supabase`: You want Supabase's design language as a reference.
- `design-superhuman`: You want Superhuman's design language as a reference.
- `design-tesla`: You want Tesla's design language as a reference.
- `design-theverge`: You want The Verge's design language as a reference.
- `design-together`: You want Together AI's design language as a reference.
- `design-uber`: You want Uber's design language as a reference.
- `design-vercel`: You want Vercel's design language as a reference.
- `design-vodafone`: You want Vodafone's design language as a reference.
- `design-voltagent`: You want VoltAgent's design language as a reference.
- `design-warp`: You want Warp's design language as a reference.
- `design-webflow`: You want Webflow's design language as a reference.
- `design-wired`: You want Wired's design language as a reference.
- `design-wise`: You want Wise's design language as a reference.
- `design-xai`: You want xAI's design language as a reference.
- `design-zapier`: You want Zapier's design language as a reference.

### token-optimize items

- `caveman`: You want short, token-conscious agent responses.
- `i-have-adhd`: You want structured, scannable answers whose important actions stay findable; this skill is invoked by the user.
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
Engineering Flow with no optional Enhancements. Every project also receives
architecture and requirements skeletons as generation infrastructure. Every
generated project receives the chain `setup-project` → `grill-with-docs` →
`to-spec` → `to-tickets` → `implement` → `improve-codebase-architecture`.
Select user-facing Categories with `--categories IDS`. Narrow Enhancements
within each selected Category with `--dev`, `--security`, `--quality`,
`--design`, or `--token-optimize`. Choose the Engineering Flow with `--flow ID`
if the manifest offers more than one. Select native Agent Target configuration
independently with `--agents IDS`.

Every selection flag accepts:

- `all` selects every current Enhancement on that flag.
- `none` selects no Category, item, or Agent Target on that flag.
- A comma-separated list selects those ids. Do not add spaces inside the list.

Every generated project resolves its Engineering Flow, which cannot be
declined; `--categories none` and `--dev none` decline Enhancements without
removing it. The former selectable ids `spec-loop`, `tdd`, `diagnosing-bugs`,
`code-review`, and `setup-all` now exit 2 when passed to `--dev`, because
their content is part of the mandatory Engineering Flow. Treat the resolved
selection shown in the report and stamp as authoritative.

Unknown Category ids, unknown item ids, unknown Agent Target ids, unknown
Engineering Flow ids, and conflicting flags are exit 2 failures; surface the
error instead of guessing a replacement.
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
uvx dev-ready init focused-app --yes --flow mattpocock --categories dev,design,token-optimize --dev none --design frontend-design,design-stripe --token-optimize code-memory --agents claude --dir ./focused-app
```

Run exactly one selected command. Do not invent flags for language, overwriting, or cleanup.

This skill creates new projects only. For an existing generated project, use
`check` or `upgrade`; `init` must never be aimed at a generated project.

## Handle the result

Treat only exit 0 as success. Every nonzero exit is a failure:

- exit 1: abort or unexpected generation error;
- exit 2: invalid arguments, unknown item id, or conflicting flags;
- exit 3: network, Git, or pinned-template fetch failure;
- exit 4: target conflict;
- exit 5: generated project failed verification.

Report the command, exit code, and error text. Do not hide the failure, weaken the selection, or retry destructively.

After exit 0, verify that the requested target exists, contains `.dev-ready.json`, and matches the final generation report. Check representative selected outputs when relevant, such as `docs/architecture.md`, `.claude/skills/to-spec/SKILL.md`, or `.mcp.json`. Only then report generation as successful and present the CLI's next steps.
