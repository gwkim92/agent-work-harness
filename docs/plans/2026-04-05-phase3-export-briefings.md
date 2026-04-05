# Phase 3 Export Briefings Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rework task-level exports so Codex, Claude, Copilot, and generic JSON outputs lead with compact briefing data instead of dumping full canonical task documents.

**Architecture:** Keep markdown and structured task files as the canonical source of truth. Add reusable summary extraction helpers in `src/awh/core.py`, expose the summary in generic JSON, and rewrite task-level adapter exports to reference canonical files while surfacing only the highest-signal state inline.

**Tech Stack:** Python 3, argparse CLI, unittest, repo-local markdown/json templates

---

### Task 1: Add Reusable Task Briefing Extraction

**Files:**
- Modify: `src/awh/core.py`
- Test: `tests/test_cli.py`

**Step 1: Write briefing extraction tests**

Add export assertions that require:
- Codex task packets to include current state, blockers, verification, evidence, and canonical references
- generic JSON task exports to include a parsed `briefing` object

**Step 2: Implement minimal summary helpers**

Add helpers that extract:
- task name, goal, mutable surface, verification commands
- completed work, in-progress work, blockers, next step
- current focus, open risks, useful commands
- feature counts and evidence counts

**Step 3: Run focused tests**

Run: `PYTHONPATH=src python3 -m unittest discover -s tests -v`

Expected: export-related tests fail first, then pass after implementation.

### Task 2: Rewrite Task-Level Adapter Exports Around Briefings

**Files:**
- Modify: `src/awh/core.py`
- Test: `tests/test_cli.py`

**Step 1: Rewrite Codex task export**

Replace full inline dumps of `contract.md`, `handoff.md`, `plan.md`, `review.md`, and `qa.md` with sections for:
- `Task Summary`
- `Current State`
- `Verification And Evidence`
- `Long-Running State`
- `Canonical References`

**Step 2: Rewrite Claude task exports**

Update coordinator and reviewer exports so they:
- read canonical files first
- include a compact task briefing
- point to plan, topology, review, QA, and evidence files as references instead of inlining them

**Step 3: Tighten Copilot task guidance**

Add compact state bullets for:
- current focus
- blockers
- next step
- verification and evidence references

### Task 3: Keep Docs And Tests Aligned

**Files:**
- Modify: `README.md`
- Modify: `docs/adapter-strategy.md`
- Test: `tests/test_cli.py`

**Step 1: Document briefing-first exports**

Update user-facing docs to say task exports are summaries over canonical files, not mirrored copies.

**Step 2: Run verification**

Run:
- `PYTHONPATH=src python3 -m unittest discover -s tests -v`
- `python3 -m compileall src tests`

Expected:
- All tests pass
- No syntax errors

**Step 3: Commit**

```bash
git add src/awh/core.py tests/test_cli.py README.md docs/adapter-strategy.md docs/plans/2026-04-05-phase3-export-briefings.md
git commit -m "Refocus task exports on compact briefings"
```
