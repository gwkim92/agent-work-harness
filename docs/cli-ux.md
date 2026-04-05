# CLI UX

This document describes the current CLI shape for Agent Work Harness and the next commands it should grow into.

## Naming

Recommended product name:

- Agent Work Harness

Recommended CLI binary:

- `awh`

Rationale:

- short enough for daily use
- maps cleanly to the repository name
- avoids overly generic binaries like `harness`

## Design Goals

- safe by default
- explicit about file writes
- works in existing repositories
- works in empty repositories
- supports incremental adoption
- preserves repo-local files as the source of truth

## Top-Level Commands

### `awh init`

Install repo-level files into the current repository.

Examples:

```bash
awh init
awh init --profile minimal
awh init --profile default
```

Expected behavior:

- detects repository root
- preflights collisions
- writes nothing on conflict unless `--force`
- supports `--dry-run` for previewing planned writes
- prints exactly which files were installed

### `awh task new <slug>`

Create a new task directory.

Examples:

```bash
awh task new bootstrap-api --profile backend
awh task new checkout-redesign --profile web --plan
awh task new checkout-redesign --profile web --plan --long-running
```

Expected behavior:

- creates `docs/tasks/<slug>/`
- installs profile-appropriate files
- can add optional long-running state files with `--long-running` or per-file flags
- supports `--dry-run` for previewing planned writes
- prints next suggested steps

### `awh task augment <slug>`

Add missing files to an existing task.

Examples:

```bash
awh task augment bootstrap-api --qa
awh task augment migration-audit --plan --roles --topology
awh task augment migration-audit --long-running
```

Expected behavior:

- adds only missing files by default
- supports additive long-running state scaffolds without changing the task profile
- supports `--dry-run` for previewing planned writes
- does not overwrite existing task artifacts unless `--force`

### `awh verify`

Check repository harness health.

Examples:

```bash
awh verify
awh verify --task bootstrap-api
awh verify --task bootstrap-api --strict
```

Expected behavior:

- validates required repo files
- validates that repo-level files are filled enough to be usable
- validates that task directories are both complete and meaningfully filled
- validates optional long-running JSON files when they are present
- supports `--strict` to require stronger regression, rollback, review, QA, and evidence records
- prints gaps without editing files

### `awh doctor`

Explain what is missing and what to do next.

Expected behavior:

- detects repository maturity
- recommends the next concrete command or document to edit
- suggests missing verification or evaluator artifacts
- suggests long-running scaffolds for planned tasks that need session state

### `awh upgrade`

Update repo-level files from the upstream harness release.

Expected behavior:

- shows diff targets first
- supports `--only-missing`
- supports `--force`
- should support `--dry-run`
- prefers non-destructive updates

## User Flows

### New Repository

```bash
awh init --profile default
awh task new bootstrap-api --profile backend --plan --long-running
```

### Existing Repository

```bash
cd existing-repo
awh init --profile default
awh task new add-billing --profile backend
awh task augment add-billing --qa --plan --long-running
```

## UX Rules

- always show planned writes before mutating
- never overwrite without explicit confirmation or `--force`
- treat missing repo root as an actionable error
- default `task augment` to only-missing behavior
- treat blank scaffolds as incomplete in `verify`
- keep markdown canonical while allowing structured long-running companion files
- recommend the next command after every successful write

## Non-Goals

- hidden AI behavior inside the CLI
- closed state stored outside the repository
- forcing multi-agent flows by default
