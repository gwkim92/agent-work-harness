# Agent Work Harness

Portable repo-local harness for coding agents.

Agent Work Harness helps any repository adopt a lightweight operating model for agent work:

- repo-level instructions and verification rules
- task-level artifacts such as `contract`, `handoff`, `review`, and `qa`
- explicit escalation rules for planning, multi-agent coordination, and automation

The core idea is simple:

- the real product lives in repo files
- the preferred user entrypoint should become a CLI
- GitHub templates should help new repositories start fast
- GitHub Actions should help teams enforce the rules later

## Why This Exists

Most agent setups fail for the same reasons:

- the root instructions are too vague
- task state lives only in chat history
- generation and evaluation are mixed together
- teams have no clean path from single-agent work to stronger harnesses

This repository packages a reusable answer to those problems.

It is intentionally vendor-neutral. The harness should work with Codex, Claude, Copilot, or any workflow that can read repo-local guidance.

## What Ships Today

- `templates/repo/`
  - install-once repository files
- `templates/task/`
  - per-task artifact templates
- `scripts/scaffold.sh`
  - install repo-level files into a target repository
- `scripts/new-task.sh`
  - create or augment task directories
- `guides/`
  - distilled principles, adoption levels, escalation rules
- `examples/`
  - web, backend, research, and dependency-adoption examples

## Core Model

### Repo-Level

Installed once per repository:

- `AGENTS.md`
- `docs/verification-plan.md`
- `docs/escalation-rules.md`
- `docs/tasks/README.md`

### Task-Level

Created per task:

```text
docs/tasks/<task-slug>/
```

Common files:

- `contract.md`
- `handoff.md`
- `plan.md`
- `review.md`
- `qa.md`
- `roles.md`
- `topology.md`
- `loop_contract.md`

This means task state accumulates per task instead of overwriting a single shared `docs/contract.md`.

## Quick Start

Today the repository ships shell scripts. They are the current reference implementation.

```bash
KIT=/absolute/path/to/agent-work-harness
REPO=/absolute/path/to/repo

"$KIT/scripts/scaffold.sh" default "$REPO"
"$KIT/scripts/new-task.sh" backend "$REPO" bootstrap-api --with-plan
```

To add missing task artifacts later without overwriting existing files:

```bash
KIT=/absolute/path/to/agent-work-harness
REPO=/absolute/path/to/repo

"$KIT/scripts/new-task.sh" backend "$REPO" bootstrap-api --with-qa --only-missing
```

## Current Distribution vs Future Direction

Current:

- repo-local templates
- shell-based install scripts

Recommended long-term product shape:

- repo-local files remain the source of truth
- a standalone CLI becomes the main user entrypoint
- GitHub templates cover greenfield project starts
- GitHub Actions cover team-level enforcement

Design notes for that direction:

- [Distribution Model](docs/distribution-model.md)
- [CLI UX](docs/cli-ux.md)
- [GitHub Template Strategy](docs/github-template-strategy.md)

## Script Profiles

### Repo Install

`scripts/scaffold.sh` supports:

- `minimal`
- `default`

Example:

```bash
KIT=/absolute/path/to/agent-work-harness
REPO=/absolute/path/to/repo

"$KIT/scripts/scaffold.sh" minimal "$REPO"
"$KIT/scripts/scaffold.sh" default "$REPO"
```

Behavior:

- preflights all collisions first
- copies nothing if a collision exists
- overwrites only with `--force`

### Task Creation

`scripts/new-task.sh` supports:

- `general`
- `web`
- `backend`
- `research`
- `dependency`

Optional flags:

- `--with-plan`
- `--with-review`
- `--with-qa`
- `--with-roles`
- `--with-topology`
- `--with-loop-contract`
- `--only-missing`
- `--force`

Example:

```bash
KIT=/absolute/path/to/agent-work-harness
REPO=/absolute/path/to/repo

"$KIT/scripts/new-task.sh" web "$REPO" checkout-redesign --with-plan
"$KIT/scripts/new-task.sh" general "$REPO" migration-audit --with-roles --with-topology
"$KIT/scripts/new-task.sh" general "$REPO" migration-audit --with-plan --only-missing
```

## Research Basis

This project was distilled from local research across harness engineering, agent runtimes, evaluator design, and staged adoption patterns.

Relevant internal research notes include:

- `하네스_엔지니어링_통합_가이드.md`
- `gstack_agent_reference.md`
- `ADK_에이전트_설계_가이드.md`
- `agentscope_detailed_report.md`
- `karpathy_autoresearch_상세분석_및_활용가이드.md`
- `pretext-adoption-report.md`

## When This Is Useful

- multi-file work
- interrupted sessions
- runtime or browser verification
- experimental dependency or framework adoption
- teams that need explainable, reviewable agent behavior

## When This May Be Too Much

- single-file changes
- very low-risk toy projects
- work with almost no verification requirements

In those cases, start with `minimal` and add task artifacts only when needed.
