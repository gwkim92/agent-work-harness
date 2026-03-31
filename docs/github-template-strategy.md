# GitHub Template Strategy

This document proposes how GitHub templates should be split.

The goal is to help new repositories start quickly without turning template maintenance into a burden.

## Principle

Keep the number of templates small.

The CLI should remain the main entrypoint.
GitHub templates should accelerate greenfield starts, not replace the CLI.

## Recommended Template Set

### 1. `agent-work-harness-template-minimal`

Contents:

- repo-level files only
- no project-type opinion beyond the harness itself

Use when:

- the team wants the lightest possible start
- the project type is still unclear

### 2. `agent-work-harness-template-web`

Contents:

- repo-level files
- web-oriented example verification notes
- starter CI checks for runtime or browser verification

Use when:

- the project is frontend-heavy
- browser or UI evidence matters

### 3. `agent-work-harness-template-backend`

Contents:

- repo-level files
- backend-oriented verification examples
- starter CI checks for endpoint and integration verification

Use when:

- the project centers on APIs, services, or workers

### 4. `agent-work-harness-template-research`

Contents:

- repo-level files
- experiment-oriented verification examples
- stronger hooks for evaluation loops and keep/discard decisions

Use when:

- the repository is experiment-heavy
- evaluation logic matters as much as implementation logic

## What Not To Template

Do not create too many narrowly sliced templates.

Avoid splitting by:

- framework minor variants
- database vendor
- cloud provider
- single feature category

Those differences belong in CLI flags, docs, or examples.

## Maintenance Rule

The canonical source should remain this repository.

Templates should be thin distributions of that source, not hand-maintained forks.

Good pattern:

- maintain one canonical harness repo
- generate or sync template repositories from it

Bad pattern:

- manually editing many divergent template repositories

## Relationship To GitHub Actions

Templates should install starter project structure.

GitHub Actions should enforce the structure after adoption.

That keeps bootstrapping and governance separate.
