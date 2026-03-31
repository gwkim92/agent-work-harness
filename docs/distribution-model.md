# Distribution Model

This document describes how Agent Work Harness should be delivered.

## Core Principle

The harness itself should always materialize as repo-local files.

That is the stable layer.

Everything else is a delivery mechanism.

## Recommended Shape

### 1. Repo Files As The Product

The real product is:

- `AGENTS.md`
- `docs/verification-plan.md`
- `docs/escalation-rules.md`
- `docs/tasks/<task-slug>/*`

This keeps the harness visible, reviewable, and portable across agents.

### 2. Standalone CLI As The Main Entry

The CLI should become the primary way users interact with the project.

Why:

- works for existing repositories
- works for new repositories
- can safely preflight changes
- can support upgrades without manual copying

The CLI is the main UX.
The repo files remain the main artifact.

### 3. GitHub Templates For Greenfield Starts

GitHub templates are useful when teams start a repository from scratch.

They are not enough on their own because they do not solve existing-repo adoption.

### 4. GitHub Actions For Enforcement

GitHub Actions should be treated as an organizational enforcement layer.

Examples:

- verify that required repo files exist
- verify that task directories are not empty
- verify that release branches have verification artifacts

Actions should not be the first install path.

## What Not To Make Primary

### Vendor-Embedded Only

Do not make the harness usable only inside one coding tool.

That would weaken the core goal of cross-project and cross-agent portability.

### Manual Copy Only

Manual copying is fine as a fallback, but it is not a strong public UX.

### GitHub-Only Automation

GitHub-native distribution is useful, but the harness should still be usable outside GitHub.

## Recommended Rollout

### Phase 1

- keep the repo-local templates as the source of truth
- ship script-based install flows

### Phase 2

- replace shell-centric installation with a cross-platform standalone CLI
- keep the current templates and examples as CLI payloads

### Phase 3

- publish GitHub starter templates
- publish a GitHub Action for policy checks

### Phase 4

- add optional adapters for tool-specific files if needed

Examples:

- `CLAUDE.md`
- `.github/copilot-instructions.md`
- other thin agent-specific wrappers
