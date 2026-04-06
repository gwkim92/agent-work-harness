# Phase 5 Multi-Agent Policy Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make Agent Work Harness conservative about multi-agent escalation by recommending it only when strong signals exist and by checking that `roles.md` and `topology.md` encode centralized coordination and separated evaluation clearly.

**Architecture:** Add a reusable multi-agent policy helper to `src/awh/core.py`, feed it into `doctor` and the task briefing payload, and expose the resulting guidance in task exports. Keep multi-agent artifacts optional, but surface clear issues when they exist and are still effectively blank.

**Tech Stack:** Python 3, repo-local markdown/json artifacts, unittest

---

### Task 1: Add policy tests first

**Files:**
- Modify: `tests/test_cli.py`

**Step 1: Add a recommendation test**

Require `doctor` to recommend `--roles --topology` only for a task with:
- `plan.md`
- evaluator artifacts
- long-running state
- multi-area mutable surface

**Step 2: Add an incomplete docs test**

Require `doctor` to flag blank or weak `roles.md` / `topology.md` and to mention evaluator separation or topology gaps.

**Step 3: Add export assertions**

Require task exports and generic JSON briefing payloads to expose multi-agent policy guidance.

### Task 2: Implement the policy helper

**Files:**
- Modify: `src/awh/core.py`

**Step 1: Extract multi-agent signals**

Use task artifacts to derive conservative signals:
- plan exists
- evaluator artifacts exist
- mutable surface spans multiple areas
- long-running state tracks multiple items

**Step 2: Produce recommendation and issues**

Recommend multi-agent docs only when the plan exists and at least two additional signals are present.
Bias toward:
- `planner -> generator -> evaluator` for sequential or evaluator-heavy work
- `coordinator + specialists` for broader multi-surface work

**Step 3: Validate existing docs**

When `roles.md` / `topology.md` exist, require:
- chosen pattern or topology type
- final gate / decision maker
- explicit ownership / handoff
- separated evaluator role when multiple implementation roles exist

### Task 3: Wire doctor and exports

**Files:**
- Modify: `src/awh/core.py`
- Modify: `README.md`
- Modify: `docs/cli-ux.md`
- Modify: `docs/roadmap-2026-phase1.md`

**Step 1: Update doctor**

Add conservative multi-agent recommendations and issue reporting.

**Step 2: Update briefing exports**

Expose multi-agent policy in:
- Codex task packet
- Claude coordinator/reviewer
- Copilot task instructions
- generic JSON `briefing`

**Step 3: Verify**

Run:
- `PYTHONPATH=src python3 -m unittest discover -s tests -v`
- `python3 -m compileall src tests`
