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
- prints exactly which files were installed

### `awh task new <slug>`

Create a new task directory.

Examples:

```bash
awh task new bootstrap-api --profile backend
awh task new checkout-redesign --profile web --plan
```

Expected behavior:

- creates `docs/tasks/<slug>/`
- installs profile-appropriate files
- prints next suggested steps

### `awh task augment <slug>`

Add missing files to an existing task.

Examples:

```bash
awh task augment bootstrap-api --qa
awh task augment migration-audit --plan --roles --topology
```

Expected behavior:

- adds only missing files by default
- does not overwrite existing task artifacts unless `--force`

### `awh verify`

Check repository harness health.

Examples:

```bash
awh verify
awh verify --task bootstrap-api
```

Expected behavior:

- validates required repo files
- validates task directory completeness
- prints gaps without editing files

### `awh doctor`

Explain what is missing and what to do next.

Expected behavior:

- detects repository maturity
- recommends next harness level
- suggests missing verification or evaluator artifacts

### `awh upgrade`

Update repo-level files from the upstream harness release.

Expected behavior:

- shows diff targets first
- supports `--only-missing`
- supports `--force`
- prefers non-destructive updates

## User Flows

### New Repository

```bash
awh init --profile default
awh task new bootstrap-api --profile backend --plan
```

### Existing Repository

```bash
cd existing-repo
awh init --profile default
awh task new add-billing --profile backend
awh task augment add-billing --qa --plan
```

## UX Rules

- always show planned writes before mutating
- never overwrite without explicit confirmation or `--force`
- treat missing repo root as an actionable error
- prefer `--only-missing` behavior for existing tasks
- recommend the next command after every successful write

## Non-Goals

- hidden AI behavior inside the CLI
- closed state stored outside the repository
- forcing multi-agent flows by default
