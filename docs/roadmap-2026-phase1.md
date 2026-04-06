# 2026 Product Refresh Roadmap

Updated: 2026-04-06

## Why

Agent Work Harness has the right core model:

- repo-local canonical files
- guided single-agent as the default
- explicit verification and handoff artifacts
- optional escalation to evaluator, planner, multi-agent, and automation

However, by 2026 the bar for agent harnesses is higher.
Recent public guidance and research emphasize:

- stricter evidence-based verification
- long-running task support through structured state
- tighter context engineering and higher-signal exports
- stronger skepticism about benchmark-only evaluation
- more selective use of multi-agent coordination

## Phase 1

Ship the highest-leverage fixes without changing the canonical model.

### Goals

- make `verify` content-aware instead of file-existence-only
- make `doctor` recommend the next concrete action
- add `--dry-run` to write commands
- remove confusing CLI behavior around `task augment`
- preserve simple repo-local markdown as the canonical truth

### Concrete Changes

1. Verification

- fail `awh verify` when repo files still contain template placeholders
- fail task verification when `contract.md` and `handoff.md` are still effectively blank
- keep file-existence checks, but add readiness checks on top

2. Doctor

- report incomplete repo-level guidance before suggesting new tasks
- report incomplete task content before claiming a task is healthy
- suggest the next command or document to update

3. CLI UX

- add `--dry-run` to `init`, `task new`, `task augment`, and `export`
- keep `task augment` defaulting to only-missing behavior
- stop advertising a redundant `--only-missing` flag in help output

4. Tests

- update tests so success means "ready enough to use", not just "files exist"
- cover dry-run behavior and content-aware verification

## Next Phases

### Phase 2: Long-Running Task Support

Add optional structured artifacts alongside markdown:

- `feature_list.json`
- `progress.md` or `progress.jsonl`
- `init.sh`
- `evidence/manifest.json`

### Phase 3: Export Packets

Move exports from document dumps toward compact briefings:

- current focus
- exact next step
- recent evidence
- mutable surface
- unresolved risks
- references to canonical files instead of full duplication where possible

### Phase 4: Stricter Evaluation

- add `verify --strict`
- require explicit automated and runtime/manual evidence
- make benchmark-oriented claims secondary to repo-local verification evidence

Status on 2026-04-05:

- implemented in the CLI and core validators
- strict mode now checks repo-level regression guard, rollback, and human confirmation
- strict mode now checks task-level review, QA, and collected evidence artifacts

Follow-up on 2026-04-06:

- export now requires the same basic repo/task readiness as `verify`
- placeholder long-running JSON values now fail validation instead of silently passing

### Phase 5: Multi-Agent Policy

- keep multi-agent docs available
- tighten the criteria for recommending multi-agent execution
- prefer centralized coordination and explicit evaluator separation

Status on 2026-04-05:

- implemented as a conservative doctor/export policy layer
- multi-agent docs are recommended only when plan, filled evaluator signals, ownership, and long-running signals are strong enough
- policy output now prefers centralized coordination and a separate evaluator gate

## Source Notes

This roadmap is aligned with:

- Anthropic, "Building effective agents" (2024-12-19)
- OpenAI, "A practical guide to building agents"
- Anthropic, "Effective context engineering for AI agents" (2025-09-29)
- Anthropic, "Effective harnesses for long-running agents" (2025-11-26)
- Anthropic, "Designing AI-resistant technical evaluations" (2026-01-21)
- OpenAI, "Why SWE-bench Verified no longer measures frontier coding capabilities" (2026-02-23)
- Anthropic, "Harness design for long-running application development" (2026-03-24)
- AMA-Bench (2026-03-04)
- "Towards a Science of Scaling Agent Systems" (2025-12-17)
