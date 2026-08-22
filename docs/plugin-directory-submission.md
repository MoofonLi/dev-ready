# Plugin directory submission cases

This is the Codex plugin-directory submission material for dev-ready — the
nine cases a directory reviewer walks through. Reuse this document at
the next version's submission rather than rewriting it.

Each case is a user prompt paired with the behaviour a reviewer should observe
with the Generation Skill loaded. Every command in a positive case is parsed
through the real CLI argument parser and answer builder by
`tests/unit/test_generate_skill.py`. The negative cases describe refusals the
skill already documents; they have no command to parse and are not
machine-checked.

Every positive case is taken from a worked example or an interview rule in
`skills/dev-ready/SKILL.md`. Every negative case is taken from a refusal that
file already states.

## Positive cases

### 1. Lean Default Set

A developer says, "I want a lean FastAPI app with the mandatory workflow."

The skill composes the first worked example:

```shell
uvx dev-ready init my-app --yes --dir ./my-app
```

### 2. Every Category, Enhancement, and Agent Target

A developer says, "I want every available Category, Enhancement, and Agent Target."

The skill composes the second worked example:

```shell
uvx dev-ready init full-app --yes --categories all --agents all --dir ./full-app
```

### 3. No optional Categories, Enhancements, or Agent Targets

A developer says, "I want the mandatory workflow and infrastructure, with no optional Categories, Enhancements, or Agent Targets."

The skill composes the third worked example:

```shell
uvx dev-ready init minimal-app --yes --categories none --agents none --dir ./minimal-app
```

### 4. Mixed selection with `--flow`

A developer says, "I am building a polished design-focused app and want token-conscious agents with Claude."

The skill composes the fourth worked example:

```shell
uvx dev-ready init focused-app --yes --flow mattpocock --categories dev,design,token-optimize --dev none --design frontend-design,design-stripe --token-optimize code-memory --agents claude --dir ./focused-app
```

### 5. Two named Agent Targets

A developer says, "I want a FastAPI app and I work with Claude and Windsurf."

The interview rule is: if two agents are named, include both matching targets.
Both `claude` and `windsurf` are Agent Targets, so both go in `--agents`. The
approved command is non-interactive and includes `--yes`:

```shell
uvx dev-ready init dual-app --yes --agents claude,windsurf --dir ./dual-app
```

### 6. Agent-driven Engineering Flow

A developer says, "I want the agent to start each step on its own, and
implementation can be split across fresh subagents."

The interview rule is the `superpowers` Engineering Flow criterion: "The agent starts each step on its own, and implementation can be split across fresh subagents."
Put it in `--flow`. The approved command is non-interactive and includes `--yes`:

```shell
uvx dev-ready init superpowers-app --yes --flow superpowers --dir ./superpowers-app
```

## Negative cases

These cases have no command to parse. The skill refuses before composing one,
so they are not machine-checked.

### 7. Init aimed at an existing generated project

A developer says, "Run init on my existing generated project to add Design."

The skill creates new projects only. For an existing generated project it uses
`check` or `upgrade`; `init` must never be aimed at a generated project.

### 8. Destination exists and is not empty

A developer says, "Create the project in `./my-app`" when `./my-app` already
exists and is not empty.

The skill inspects the destination first, stops, and asks the user to choose
another destination or resolve the existing content themselves. It does not
delete, empty, overwrite, or automatically retry into a non-empty target.

### 9. Retired Engineering Flow value

A developer says, "Use the spec-loop flow."

The skill does not compose a command. `--flow spec-loop` exits 2 with
`Engineering Flow id 'spec-loop' was renamed to 'mattpocock'`. Surface the
message and stop; do not guess a replacement.
