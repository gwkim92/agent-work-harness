# Phase 4 Strict Verification Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add `verify --strict` so Agent Work Harness can distinguish between basic task readiness and evidence-backed evaluation readiness.

**Architecture:** Extend the existing readiness checks instead of replacing them. Keep normal `verify` behavior stable, add strict repo/task validators in `src/awh/core.py`, surface them through the CLI, and cover the new failure modes in unit tests and docs.

**Tech Stack:** Python 3, argparse CLI, unittest, repo-local markdown/json artifacts

---

### Task 1: Add strict verification tests first

**Files:**
- Modify: `tests/test_cli.py`

**Step 1: Add CLI help assertions**

Require `awh verify --help` to show `--strict`.

**Step 2: Add strict repo and task failure tests**

Cover:
- repo strict failure when rollback / human confirmation / regression guard are missing
- task strict failure when `review.md`, `qa.md`, or evidence records are missing
- task strict success when review, QA, and evidence artifacts are meaningfully filled

### Task 2: Implement strict verification in the CLI and core

**Files:**
- Modify: `src/awh/cli.py`
- Modify: `src/awh/core.py`

**Step 1: Add `--strict` to `awh verify`**

Wire the flag through `run_verify`.

**Step 2: Add strict repo checks**

Validate that `docs/verification-plan.md` includes:
- automated checks
- manual or browser/runtime checks
- regression guard
- rollback
- human confirmation

**Step 3: Add strict task checks**

Validate that a strict task has:
- `review.md` with claimed outcome, checked evidence, residual risks, and verdict
- `qa.md` with runtime/manual scenario evidence and verdict
- `evidence/manifest.json` with at least one collected artifact

### Task 3: Update docs and verify

**Files:**
- Modify: `README.md`
- Modify: `docs/cli-ux.md`
- Modify: `docs/roadmap-2026-phase1.md`

**Step 1: Document `verify --strict`**

Explain that normal verify checks readiness while strict verify checks evaluation rigor.

**Step 2: Run verification**

Run:
- `PYTHONPATH=src python3 -m unittest discover -s tests -v`
- `python3 -m compileall src tests`

**Step 3: Commit**

```bash
git add src/awh/cli.py src/awh/core.py tests/test_cli.py README.md docs/cli-ux.md docs/roadmap-2026-phase1.md docs/plans/2026-04-05-phase4-strict-verification.md
git commit -m "Add strict verification mode"
```
