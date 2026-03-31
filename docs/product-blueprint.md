# Product Blueprint

This document describes the simplest product shape for Agent Work Harness.

## Short Answer

Users are most likely to prefer:

- repo-local files as the product
- a standalone CLI as the default entrypoint
- GitHub templates for new repositories
- GitHub Actions for team enforcement

Why:

- it works for both new and existing repositories
- it keeps the source of truth inside git
- it avoids hard lock-in to one agent tool
- it gives teams a clear adoption path from solo use to shared policy

## What The User Is Actually Buying

Users are not primarily buying a CLI.

They are buying:

- a way to make agent work reviewable
- a way to make task state survive chat resets
- a way to separate generation from evaluation
- a way to scale from simple work to stronger harnesses

The CLI is only the easiest way to install and manage that system.

## First-Time User Experience

The first experience should feel like this:

### 1. Install

```bash
python3 -m pip install agent-work-harness
```

or during development:

```bash
python3 -m pip install -e .
```

### 2. Initialize A Repository

```bash
awh init --profile default --repo /path/to/repo
```

The user should see:

- which files were written
- which profile was applied
- what to fill next

### 3. Start The First Task

```bash
awh task new bootstrap-api --profile backend --repo /path/to/repo --plan
```

The user should immediately get:

- a concrete task directory
- a contract to scope the work
- a handoff file
- optional plan and evaluator files based on the profile

### 4. Ask The Agent To Work

At this point the repository is ready for the user to tell any agent:

- what they want to build
- which task slug to use
- what verification matters

The repo-local files provide the working context.

### 5. Tighten Team Policy Later

Once the team likes the structure, they can add:

- GitHub templates for new repos
- GitHub Actions for policy checks
- tool-specific exports for Claude, Codex, Copilot, or others

## What Should Feel Easy

The easiest actions should be:

- install the harness
- create the next task
- augment an existing task
- verify harness health
- understand the next missing step

That leads to this default CLI shape:

- `awh init`
- `awh task new`
- `awh task augment`
- `awh export`
- `awh verify`
- `awh doctor`

## Distribution Priorities

### 1. CLI First

The CLI should be the main path because it works for:

- existing repositories
- greenfield repositories
- local experimentation
- team rollout

### 2. Repo Files Remain Canonical

The CLI writes files, but the files are the product.

This keeps the harness:

- inspectable
- reviewable
- diffable
- portable

### 3. GitHub Templates Are A Fast Start, Not The Whole Product

Templates are useful for new repos, but they do not solve retrofitting existing repos.

### 4. GitHub Actions Are Governance, Not Bootstrapping

Actions should validate and enforce.
They should not be the main install path.

## Recommended Launch Sequence

### Stage 1

- repo-local templates
- CLI for install and task lifecycle

### Stage 2

- export adapters for major agent tools

### Stage 3

- GitHub templates
- GitHub Action starter

### Stage 4

- upgrade and sync workflows across versions

## One-Line Product Positioning

Agent Work Harness is a repo-local operating model for agent work, delivered through a CLI and adaptable to multiple agent ecosystems.
