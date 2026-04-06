# Adapter Strategy

This document explains how Agent Work Harness should support multiple agent tools and model environments without changing its canonical structure.

## Current Status

Initial support now exists for:

- `awh export claude`
- `awh export codex`
- `awh export copilot`
- `awh export generic-json`

This is a first-pass implementation.
It creates reproducible adapter outputs from canonical harness files.
Task-level exports are now briefing-first rather than full document dumps.

## Core Rule

Canonical files stay vendor-neutral.

Examples:

- `AGENTS.md`
- `docs/verification-plan.md`
- `docs/escalation-rules.md`
- `docs/tasks/<task-slug>/*`

Adapters should export from these files.
They should not replace them.

For task-level exports, the generated output should:

- inline only high-signal briefing data
- point back to canonical markdown and JSON files for full detail
- require the canonical repo/task files to pass basic readiness first
- stay safe to regenerate without becoming a second source of truth

## Why Adapters Matter

Different agent environments prefer different file layouts.

Examples:

- Claude favors `CLAUDE.md` and `.claude/agents/*`
- Codex favors repo-local instructions and task context
- Copilot favors `.github/copilot-instructions.md`

Users should not have to rewrite their harness every time they switch tools.

## Recommended Adapter Families

### 1. Tool Adapters

These produce files for specific agent tools.

Examples:

- `awh export claude`
- `awh export codex`
- `awh export copilot`
- `awh export cursor`

### 2. Runtime Adapters

These produce machine-readable packets for generic LLM APIs or orchestration layers.

Examples:

- `awh export generic-json`
- `awh export generic-prompt`

## Priority Order

Recommended implementation order:

1. `claude`
2. `codex`
3. `copilot`
4. `generic-json`

Why:

- Claude and Codex are the closest fit for repository-driven agent work
- Copilot is a strong enterprise distribution channel
- generic exports are useful once the canonical mapping is stable

## Adapter Outputs

### Claude

Goal:

- translate canonical repo files into Claude-friendly files

Expected outputs:

- `CLAUDE.md`
- `.claude/agents/*.md`

Typical mappings:

- `AGENTS.md` -> `CLAUDE.md`
- `roles.md` + `topology.md` -> `.claude/agents/*.md`
- task briefings -> coordinator and reviewer cards with canonical file references

Current export style:

- generated Claude subagents use YAML frontmatter
  - `name`
  - `description`
  - `tools`
- coordinator and reviewer cards are generated even when role parsing is minimal
- role-specific cards can be generated from `roles.md` when structured values exist

### Codex

Goal:

- preserve canonical files and optionally generate a compact Codex bootstrap packet

Expected outputs:

- usually no new mandatory files
- optional `docs/exports/codex/<task-slug>.md`

Typical mappings:

- `AGENTS.md` stays canonical
- task files are summarized into a compact execution packet
- full task markdown stays in `docs/tasks/<task-slug>/` and is referenced, not mirrored

Why not force more files:

- Codex already works well with repo-local markdown

### Copilot

Goal:

- produce repository instructions that fit GitHub Copilot conventions

Expected outputs:

- `.github/copilot-instructions.md`
- `.github/instructions/<task>.instructions.md` for task-scoped guidance

Typical mappings:

- `AGENTS.md` -> `.github/copilot-instructions.md`
- `verification-plan.md` contributes guardrails and check commands
- `contract.md` mutable surface can inform `applyTo` patterns
- compact task briefings add current focus, blockers, next step, and evidence status

### Cursor

Goal:

- generate `.cursor/rules/*` from canonical guidance

Expected outputs:

- `.cursor/rules/*.mdc`

This is lower priority than Claude, Codex, and Copilot.

### Generic JSON

Goal:

- export the repository harness into a portable machine-readable structure

Expected outputs:

- `docs/exports/generic/<task-slug>.json`

This is useful for:

- API-driven orchestration
- custom dashboards
- future tool integrations

Task payloads should include:

- `files` for raw canonical contents
- `structured` for parsed JSON state
- `briefing` for compact task execution state

## Recommended Commands

### Repo-Level Export

```bash
awh export claude --repo /path/to/repo
awh export codex --repo /path/to/repo
awh export copilot --repo /path/to/repo
```

### Task-Level Export

```bash
awh export claude --repo /path/to/repo --task bootstrap-api
awh export codex --repo /path/to/repo --task bootstrap-api
awh export generic-json --repo /path/to/repo --task bootstrap-api
```

## Safety Rules

- canonical files are always edited first
- exports should fail fast when canonical files are still placeholder scaffolds
- exports should be reproducible
- generated files should be safe to regenerate
- adapter-specific files should not hold the only copy of important meaning
- task exports should summarize, not clone, canonical task documents

## What Users Likely Prefer

Most users will prefer:

- one canonical repo structure
- one CLI
- optional adapters only when they actually need a tool-specific optimization

They generally do not want:

- separate parallel truth systems
- vendor-specific lock-in at the core layer

## Product Implication

Agent Work Harness should present itself as:

- one repo-local harness
- one CLI
- many adapter outputs

That keeps the user mental model simple even as tool support expands.
