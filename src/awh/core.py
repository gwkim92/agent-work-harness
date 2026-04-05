from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any, Iterable
import shutil


TEMPLATE_PLACEHOLDER_RE = re.compile(r"\[[A-Z0-9_]+\]")


REPO_PROFILE_FILES = {
    "minimal": (
        ("templates/repo/AGENTS.md", "AGENTS.md"),
        ("templates/repo/docs/verification-plan.md", "docs/verification-plan.md"),
        ("templates/repo/docs/tasks/README.md", "docs/tasks/README.md"),
    ),
    "default": (
        ("templates/repo/AGENTS.md", "AGENTS.md"),
        ("templates/repo/docs/verification-plan.md", "docs/verification-plan.md"),
        ("templates/repo/docs/tasks/README.md", "docs/tasks/README.md"),
        ("templates/repo/docs/escalation-rules.md", "docs/escalation-rules.md"),
    ),
}

TASK_OPTION_SPECS = {
    "contract": ("templates/task/contract.md", "contract.md"),
    "handoff": ("templates/task/handoff.md", "handoff.md"),
    "plan": ("templates/task/plan.md", "plan.md"),
    "feature_list": ("templates/task/feature_list.json", "feature_list.json"),
    "progress": ("templates/task/progress.md", "progress.md"),
    "init_script": ("templates/task/init.sh", "init.sh"),
    "review": ("templates/task/review.md", "review.md"),
    "qa": ("templates/task/qa.md", "qa.md"),
    "roles": ("templates/task/roles.md", "roles.md"),
    "topology": ("templates/task/topology.md", "topology.md"),
    "evidence_manifest": ("templates/task/evidence_manifest.json", "evidence/manifest.json"),
    "loop_contract": ("templates/task/loop_contract.md", "loop_contract.md"),
}

LONG_RUNNING_TASK_OPTIONS = (
    "feature_list",
    "progress",
    "init_script",
    "evidence_manifest",
)

FEATURE_STATUS_VALUES = {"todo", "in_progress", "done", "blocked"}
FEATURE_PRIORITY_VALUES = {"low", "medium", "high"}
EVIDENCE_KIND_VALUES = {"automated", "manual", "browser", "runtime", "log", "screenshot", "other"}
EVIDENCE_STATUS_VALUES = {"planned", "collected", "failed"}

TASK_PROFILE_OPTIONS = {
    "general": set(),
    "web": {"review", "qa"},
    "backend": {"review"},
    "research": {"review"},
    "dependency": {"plan", "review"},
}

REQUIRED_REPO_FILES = (
    "AGENTS.md",
    "docs/verification-plan.md",
    "docs/tasks/README.md",
)

REQUIRED_TASK_FILES = ("contract.md", "handoff.md")


@dataclass(frozen=True)
class CopyOperation:
    source: Path
    destination: Path


@dataclass(frozen=True)
class WriteOperation:
    destination: Path
    content: str


def kit_root() -> Path:
    return Path(__file__).resolve().parents[2]


def ensure_target_repo(path: str | Path) -> Path:
    repo = Path(path).expanduser().resolve()
    if not repo.is_dir():
        raise HarnessError(f"Target repository does not exist: {repo}")
    return repo


def validate_task_slug(slug: str) -> None:
    if not slug or slug.startswith("/") or ".." in slug:
        raise HarnessError(f"Unsafe task slug: {slug}")


def repo_plan(profile: str, repo: Path) -> list[CopyOperation]:
    if profile not in REPO_PROFILE_FILES:
        raise HarnessError(f"Unknown repo profile: {profile}")
    root = kit_root()
    return [
        CopyOperation(root / source, repo / destination)
        for source, destination in REPO_PROFILE_FILES[profile]
    ]


def task_plan(
    profile: str,
    repo: Path,
    slug: str,
    extra_options: set[str] | None = None,
) -> list[CopyOperation]:
    if profile not in TASK_PROFILE_OPTIONS:
        raise HarnessError(f"Unknown task profile: {profile}")

    validate_task_slug(slug)
    options = {"contract", "handoff"} | TASK_PROFILE_OPTIONS[profile]
    if extra_options:
        options |= set(extra_options)

    root = kit_root()
    task_dir = repo / "docs" / "tasks" / slug
    return [
        CopyOperation(root / TASK_OPTION_SPECS[name][0], task_dir / TASK_OPTION_SPECS[name][1])
        for name in _ordered_task_options(options)
    ]


def _ordered_task_options(options: set[str]) -> list[str]:
    ordered_names = [
        "contract",
        "handoff",
        "plan",
        "feature_list",
        "progress",
        "init_script",
        "review",
        "qa",
        "roles",
        "topology",
        "evidence_manifest",
        "loop_contract",
    ]
    return [name for name in ordered_names if name in options]


def preflight_copy(
    operations: Iterable[CopyOperation],
    *,
    force: bool = False,
    only_missing: bool = False,
) -> tuple[list[CopyOperation], list[Path], list[Path]]:
    effective: list[CopyOperation] = []
    skipped: list[Path] = []
    conflicts: list[Path] = []

    for operation in operations:
        if operation.destination.exists() and not force:
            if only_missing:
                skipped.append(operation.destination)
            else:
                conflicts.append(operation.destination)
            continue
        effective.append(operation)

    return effective, skipped, conflicts


def apply_copy_plan(operations: Iterable[CopyOperation]) -> list[Path]:
    written: list[Path] = []
    for operation in operations:
        operation.destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(operation.source, operation.destination)
        written.append(operation.destination)
    return written


def preflight_write(
    operations: Iterable[WriteOperation],
    *,
    force: bool = False,
) -> tuple[list[WriteOperation], list[Path]]:
    effective: list[WriteOperation] = []
    conflicts: list[Path] = []

    for operation in operations:
        if operation.destination.exists() and not force:
            conflicts.append(operation.destination)
            continue
        effective.append(operation)

    return effective, conflicts


def apply_write_plan(operations: Iterable[WriteOperation]) -> list[Path]:
    written: list[Path] = []
    for operation in operations:
        operation.destination.parent.mkdir(parents=True, exist_ok=True)
        operation.destination.write_text(operation.content, encoding="utf-8")
        written.append(operation.destination)
    return written


def verify_repo(repo: Path) -> list[str]:
    missing = []
    for relative_path in REQUIRED_REPO_FILES:
        if not (repo / relative_path).exists():
            missing.append(relative_path)
    return missing


def verify_task(repo: Path, slug: str) -> list[str]:
    validate_task_slug(slug)
    task_dir = repo / "docs" / "tasks" / slug
    if not task_dir.exists():
        return [str(task_dir.relative_to(repo))]
    missing = []
    for file_name in REQUIRED_TASK_FILES:
        if not (task_dir / file_name).exists():
            missing.append(str((task_dir / file_name).relative_to(repo)))
    return missing


def verify_repo_contents(repo: Path) -> list[str]:
    issues: list[str] = []
    agents_text = _read_optional_file(repo / "AGENTS.md")
    verification_text = _read_optional_file(repo / "docs" / "verification-plan.md")

    if agents_text and TEMPLATE_PLACEHOLDER_RE.search(agents_text):
        issues.append("Fill placeholder tokens in `AGENTS.md`.")

    if verification_text:
        automated_commands = _extract_all_labeled_entries(verification_text, "명령", "command")
        manual_checks = _extract_all_labeled_entries(verification_text, "시나리오", "scenario")
        runtime_checks = _extract_all_labeled_entries(
            verification_text,
            "URL, route, job, endpoint",
            "browser or runtime checks",
        )
        if not automated_commands:
            issues.append("Add at least one automated check command to `docs/verification-plan.md`.")
        if not manual_checks and not runtime_checks:
            issues.append(
                "Add at least one manual scenario or browser/runtime check to `docs/verification-plan.md`."
            )

    return issues


def verify_task_contents(repo: Path, slug: str) -> list[str]:
    validate_task_slug(slug)
    task_dir = repo / "docs" / "tasks" / slug
    contract = _read_optional_file(task_dir / "contract.md")
    handoff = _read_optional_file(task_dir / "handoff.md")
    if not contract or not handoff:
        return []

    issues: list[str] = []
    if not _extract_all_labeled_entries(contract, "요청", "request"):
        issues.append(f"Add the task request to `docs/tasks/{slug}/contract.md`.")
    if not _extract_all_labeled_entries(
        contract,
        "이 작업이 끝났을 때 반드시 참이어야 하는 상태",
        "goal",
    ):
        issues.append(f"Add a concrete goal to `docs/tasks/{slug}/contract.md`.")
    if not _extract_all_labeled_entries(contract, "수정 가능한 파일", "editable files", "mutable surface"):
        issues.append(f"Define the mutable surface in `docs/tasks/{slug}/contract.md`.")
    if not _extract_all_labeled_entries(contract, "검증에 사용할 명령", "verification command"):
        issues.append(f"Add at least one verification command to `docs/tasks/{slug}/contract.md`.")
    if not (
        _extract_all_labeled_entries(handoff, "완료", "completed")
        or _extract_all_labeled_entries(handoff, "진행 중", "in progress")
    ):
        issues.append(f"Record the current status in `docs/tasks/{slug}/handoff.md`.")
    if not _extract_all_labeled_entries(handoff, "다음 세션은 이것부터 시작", "exact next step"):
        issues.append(f"Add the exact next step to `docs/tasks/{slug}/handoff.md`.")
    issues.extend(verify_task_long_running_contents(repo, slug))
    return issues


def verify_task_long_running_contents(repo: Path, slug: str) -> list[str]:
    issues: list[str] = []
    feature_list_path = task_artifact_path(repo, slug, "feature_list")
    evidence_manifest_path = task_artifact_path(repo, slug, "evidence_manifest")

    if feature_list_path.exists():
        issues.extend(_feature_list_validation_errors(feature_list_path))
    if evidence_manifest_path.exists():
        issues.extend(_evidence_manifest_validation_errors(evidence_manifest_path))

    return issues


def list_task_slugs(repo: Path) -> list[str]:
    tasks_dir = repo / "docs" / "tasks"
    if not tasks_dir.exists():
        return []
    return sorted(path.name for path in tasks_dir.iterdir() if path.is_dir())


def task_missing_evaluators(repo: Path, slug: str) -> bool:
    task_dir = repo / "docs" / "tasks" / slug
    return not ((task_dir / "review.md").exists() or (task_dir / "qa.md").exists())


def task_has_plan(repo: Path, slug: str) -> bool:
    return task_artifact_path(repo, slug, "plan").exists()


def task_artifact_path(repo: Path, slug: str, option_name: str) -> Path:
    validate_task_slug(slug)
    if option_name not in TASK_OPTION_SPECS:
        raise HarnessError(f"Unknown task artifact: {option_name}")
    return repo / "docs" / "tasks" / slug / TASK_OPTION_SPECS[option_name][1]


def present_long_running_artifacts(repo: Path, slug: str) -> list[str]:
    validate_task_slug(slug)
    present: list[str] = []
    for option_name in LONG_RUNNING_TASK_OPTIONS:
        artifact_path = task_artifact_path(repo, slug, option_name)
        if artifact_path.exists():
            present.append(str(artifact_path.relative_to(repo)))
    return present


def doctor_notes(repo: Path) -> list[str]:
    notes: list[str] = []
    missing_repo = verify_repo(repo)
    if missing_repo:
        notes.append("Harness is not fully installed. Run `awh init --profile default`.")
        notes.append("Missing repo files: " + ", ".join(missing_repo))
        return notes

    repo_issues = verify_repo_contents(repo)
    if repo_issues:
        notes.append("Repo-level harness files exist, but they still need project-specific content.")
        notes.extend(repo_issues)
        notes.append("Next: update `AGENTS.md` and `docs/verification-plan.md`, then run `awh verify`.")
        return notes

    task_slugs = list_task_slugs(repo)
    if not task_slugs:
        notes.append("Harness is installed, but there are no task directories yet.")
        notes.append("Next step: run `awh task new <slug> --profile backend` or another profile.")
        return notes

    notes.append(f"Harness is installed. Found {len(task_slugs)} task directory(s).")
    for slug in task_slugs:
        task_missing = verify_task(repo, slug)
        if task_missing:
            notes.append(f"Task `{slug}` is incomplete: missing {', '.join(task_missing)}.")
            continue
        long_running_notes = doctor_task_long_running_notes(repo, slug)
        task_issues = verify_task_contents(repo, slug)
        if task_issues:
            notes.append(f"Task `{slug}` exists but is not verification-ready yet.")
            notes.extend(task_issues)
            for note in long_running_notes:
                if note not in task_issues:
                    notes.append(note)
            if _has_non_long_running_task_issues(task_issues, slug):
                notes.append(f"Next: finish `docs/tasks/{slug}/contract.md` and `handoff.md`.")
            else:
                notes.append(f"Next: repair the long-running task state files under `docs/tasks/{slug}/`.")
            continue
        if task_has_plan(repo, slug) and not present_long_running_artifacts(repo, slug):
            notes.append(
                f"Task `{slug}` has a plan but no long-running support yet. "
                f"Consider `awh task augment {slug} --long-running`."
            )
        if long_running_notes:
            notes.append(f"Task `{slug}` has long-running artifacts that still need attention.")
            notes.extend(long_running_notes)
        if task_missing_evaluators(repo, slug):
            notes.append(
                f"Task `{slug}` has no evaluator artifacts yet. Consider "
                f"`awh task augment {slug} --review` or `--qa`."
            )
    if not any("evaluator artifacts" in note for note in notes):
        notes.append("All current tasks have base artifacts and at least one evaluator artifact.")
    return notes


class HarnessError(Exception):
    """User-facing error for CLI operations."""


def export_plan(target: str, repo: Path, task_slug: str | None = None) -> list[WriteOperation]:
    if target == "claude":
        return build_claude_export(repo, task_slug=task_slug)
    if target == "codex":
        return build_codex_export(repo, task_slug=task_slug)
    if target == "copilot":
        if task_slug:
            return build_copilot_task_export(repo, task_slug)
        return build_copilot_export(repo)
    if target == "generic-json":
        return build_generic_json_export(repo, task_slug=task_slug)
    raise HarnessError(f"Unknown export target: {target}")


def build_claude_export(repo: Path, task_slug: str | None = None) -> list[WriteOperation]:
    _require_repo_harness(repo)
    if task_slug:
        _require_task_long_running_export_state(repo, task_slug)
        return _claude_task_exports(repo, task_slug)
    return [
        WriteOperation(
            destination=repo / "CLAUDE.md",
            content=_claude_repo_content(repo),
        )
    ]


def build_codex_export(repo: Path, task_slug: str | None = None) -> list[WriteOperation]:
    _require_repo_harness(repo)
    if task_slug:
        _require_task_long_running_export_state(repo, task_slug)
        return [
            WriteOperation(
                destination=repo / "docs" / "exports" / "codex" / f"{task_slug}.md",
                content=_codex_task_content(repo, task_slug),
            )
        ]
    return [
        WriteOperation(
            destination=repo / "docs" / "exports" / "codex" / "repo.md",
            content=_codex_repo_content(repo),
        )
    ]


def build_copilot_export(repo: Path) -> list[WriteOperation]:
    _require_repo_harness(repo)
    return [
        WriteOperation(
            destination=repo / ".github" / "copilot-instructions.md",
            content=_copilot_repo_content(repo),
        )
    ]


def build_copilot_task_export(repo: Path, task_slug: str) -> list[WriteOperation]:
    _require_repo_harness(repo)
    _require_task_long_running_export_state(repo, task_slug)
    return [
        WriteOperation(
            destination=repo / ".github" / "instructions" / f"{task_slug}.instructions.md",
            content=_copilot_task_content(repo, task_slug),
        )
    ]


def build_generic_json_export(repo: Path, task_slug: str | None = None) -> list[WriteOperation]:
    _require_repo_harness(repo)
    if task_slug:
        _require_task_long_running_export_state(repo, task_slug)
        payload = {
            "kind": "task",
            "task_slug": task_slug,
            "files": _task_file_payload(repo, task_slug),
            "structured": _task_structured_payload(repo, task_slug),
        }
        destination = repo / "docs" / "exports" / "generic" / f"{task_slug}.json"
    else:
        payload = {
            "kind": "repo",
            "files": {
                "AGENTS.md": _read_file(repo / "AGENTS.md"),
                "docs/verification-plan.md": _read_file(repo / "docs" / "verification-plan.md"),
                "docs/escalation-rules.md": _read_optional_file(repo / "docs" / "escalation-rules.md"),
            },
            "tasks": list_task_slugs(repo),
        }
        destination = repo / "docs" / "exports" / "generic" / "repo.json"
    return [
        WriteOperation(
            destination=destination,
            content=json.dumps(payload, indent=2, ensure_ascii=True) + "\n",
        )
    ]


def _require_repo_harness(repo: Path) -> None:
    missing = verify_repo(repo)
    if missing:
        raise HarnessError(
            "Repository is missing required harness files for export: " + ", ".join(missing)
        )


def _require_task_long_running_export_state(repo: Path, task_slug: str) -> None:
    validate_task_slug(task_slug)
    missing = verify_task(repo, task_slug)
    if missing:
        raise HarnessError(f"Task `{task_slug}` is not ready for export: missing {', '.join(missing)}")
    issues = verify_task_long_running_contents(repo, task_slug)
    if issues:
        raise HarnessError(f"Task `{task_slug}` has invalid long-running artifacts: {'; '.join(issues)}")


def _claude_repo_content(repo: Path) -> str:
    return "\n".join(
        [
            "# CLAUDE.md",
            "",
            "<!-- Generated by Agent Work Harness. Edit canonical repo files, then re-export. -->",
            "",
            "This repository uses Agent Work Harness.",
            "",
            "Treat these files as canonical:",
            "",
            "- `AGENTS.md`",
            "- `docs/verification-plan.md`",
            "- `docs/escalation-rules.md` when present",
            "- `docs/tasks/<task-slug>/` for active task state",
            "",
            "When starting work:",
            "",
            "1. Read `AGENTS.md` first.",
            "2. Read `docs/verification-plan.md` before claiming completion.",
            "3. If a task exists, use that task directory as the working state.",
            "4. Prefer canonical task docs over generated exports when they disagree.",
            "",
            "## Canonical Repository Instructions",
            "",
            _read_file(repo / "AGENTS.md"),
            "",
            "## Canonical Verification Plan",
            "",
            _read_file(repo / "docs" / "verification-plan.md"),
            "",
            "## Escalation Rules",
            "",
            _read_optional_file(repo / "docs" / "escalation-rules.md") or "_Not present._",
            "",
        ]
    )


def _claude_task_exports(repo: Path, task_slug: str) -> list[WriteOperation]:
    validate_task_slug(task_slug)
    missing = verify_task(repo, task_slug)
    if missing:
        raise HarnessError(f"Task `{task_slug}` is not ready for export: missing {', '.join(missing)}")

    task_dir = repo / "docs" / "tasks" / task_slug
    operations = [
        WriteOperation(
            destination=repo / ".claude" / "agents" / f"{task_slug}-coordinator.md",
            content=_claude_agent_file(
                name=f"{task_slug}-coordinator",
                description=f"Coordinate work for task {task_slug} using the canonical task artifacts.",
                tools="Read, Grep, Glob, Bash",
                body=_claude_coordinator_body(repo, task_slug),
            ),
        )
    ]

    for index, role in enumerate(_parse_roles(_read_optional_file(task_dir / "roles.md")), start=1):
        role_slug = _slugify(role.get("name") or role.get("type") or f"role-{index}")
        operations.append(
            WriteOperation(
                destination=repo / ".claude" / "agents" / f"{task_slug}-{role_slug}.md",
                content=_claude_agent_file(
                    name=f"{task_slug}-{role_slug}",
                    description=_claude_role_description(task_slug, role, index=index),
                    tools=_claude_role_tools(role),
                    body=_claude_role_body(repo, task_slug, role, index=index),
                ),
            )
        )

    review = _read_optional_file(task_dir / "review.md")
    qa = _read_optional_file(task_dir / "qa.md")
    if review or qa:
        operations.append(
            WriteOperation(
                destination=repo / ".claude" / "agents" / f"{task_slug}-reviewer.md",
                content=_claude_agent_file(
                    name=f"{task_slug}-reviewer",
                    description=f"Review and challenge work on task {task_slug} using review, QA, and verification artifacts.",
                    tools="Read, Grep, Glob, Bash",
                    body=_claude_reviewer_body(repo, task_slug, review, qa),
                ),
            )
        )
    return operations


def _codex_repo_content(repo: Path) -> str:
    tasks = list_task_slugs(repo)
    return "\n".join(
        [
            "# Codex Export Packet",
            "",
            "Use this packet as a compact map, but treat canonical repo files as the source of truth.",
            "",
            "## Read First",
            "",
            "- `AGENTS.md`",
            "- `docs/verification-plan.md`",
            "- `docs/escalation-rules.md` when present",
            "- `docs/tasks/<task-slug>/` for active task state",
            "",
            "## Repository Map",
            "",
            _read_file(repo / "AGENTS.md"),
            "",
            "## Verification",
            "",
            _read_file(repo / "docs" / "verification-plan.md"),
            "",
            "## Known Tasks",
            "",
            "\n".join(f"- `{slug}`" for slug in tasks) if tasks else "_No task directories yet._",
            "",
        ]
    )


def _codex_task_content(repo: Path, task_slug: str) -> str:
    task_dir = repo / "docs" / "tasks" / task_slug
    contract = _read_file(task_dir / "contract.md")
    handoff = _read_file(task_dir / "handoff.md")
    plan = _read_optional_file(task_dir / "plan.md")
    review = _read_optional_file(task_dir / "review.md")
    qa = _read_optional_file(task_dir / "qa.md")
    mutable_surface = _extract_first_labeled_value(contract, "수정 가능한 파일", "수정 가능한 범위")
    task_name = _extract_first_labeled_value(contract, "이름")
    goal = _extract_first_labeled_value(contract, "이 작업이 끝났을 때 반드시 참이어야 하는 상태")
    next_step = _extract_first_labeled_value(handoff, "다음 세션은 이것부터 시작")
    completed = _extract_first_labeled_value(handoff, "완료")
    long_running_lines = _codex_long_running_lines(repo, task_slug)
    return "\n".join(
        [
            f"# Codex Task Packet: {task_slug}",
            "",
            "Use this packet as a compact briefing, but prefer canonical task files when details diverge.",
            "",
            "## Read First",
            "",
            f"- `docs/tasks/{task_slug}/contract.md`",
            f"- `docs/tasks/{task_slug}/handoff.md`",
            f"- `docs/tasks/{task_slug}/plan.md` when present",
            f"- `docs/tasks/{task_slug}/review.md` and `qa.md` when present",
            "",
            "## Task Summary",
            "",
            f"- name: {task_name or task_slug}",
            f"- goal: {goal or '_Not captured in a single field._'}",
            f"- mutable surface: {mutable_surface or '_Use the contract mutable surface section._'}",
            f"- completed status: {completed or '_See handoff.md._'}",
            f"- next step: {next_step or '_See handoff.md._'}",
            "",
            "## Long-Running State",
            "",
            *long_running_lines,
            "",
            "## Contract",
            "",
            contract,
            "",
            "## Handoff",
            "",
            handoff,
            "",
            "## Plan",
            "",
            plan or "_Not present._",
            "",
            "## Review",
            "",
            review or "_Not present._",
            "",
            "## QA",
            "",
            qa or "_Not present._",
            "",
        ]
    )


def _copilot_repo_content(repo: Path) -> str:
    return "\n".join(
        [
            "# Copilot Repository Instructions",
            "",
            "<!-- Generated by Agent Work Harness. Edit canonical repo files, then re-export. -->",
            "",
            "Use the repository harness as the source of truth.",
            "",
            "When working in this repository:",
            "",
            "- Read `AGENTS.md` before making broad changes.",
            "- Use `docs/verification-plan.md` as the completion gate.",
            "- Prefer task directories under `docs/tasks/` for current task state.",
            "- Keep generation and evaluation separate when review or QA artifacts exist.",
            "",
            "## AGENTS",
            "",
            _read_file(repo / "AGENTS.md"),
            "",
            "## Verification",
            "",
            _read_file(repo / "docs" / "verification-plan.md"),
            "",
        ]
    )


def _copilot_task_content(repo: Path, task_slug: str) -> str:
    contract = _read_file(repo / "docs" / "tasks" / task_slug / "contract.md")
    apply_to = _copilot_apply_to_patterns(contract)
    long_running_guidance = _copilot_long_running_lines(repo, task_slug)
    return "\n".join(
        [
            "---",
            f'applyTo: "{apply_to}"',
            'excludeAgent: "code-review"',
            "---",
            "",
            f"Use `docs/tasks/{task_slug}/contract.md` and `handoff.md` as the task source of truth.",
            "",
            "Task-specific guidance:",
            "",
            f"- Stay inside `docs/tasks/{task_slug}/contract.md` scope and mutable surface.",
            f"- Use `docs/tasks/{task_slug}/plan.md` if it exists before making large edits.",
            *long_running_guidance,
            f"- Update `docs/tasks/{task_slug}/review.md` and `qa.md` instead of inventing new evaluation standards.",
            f"- Refresh `docs/tasks/{task_slug}/handoff.md` before stopping work.",
            "",
        ]
    )


def _task_file_payload(repo: Path, task_slug: str) -> dict[str, str | None]:
    task_dir = repo / "docs" / "tasks" / task_slug
    return {
        "contract.md": _read_optional_file(task_dir / "contract.md"),
        "handoff.md": _read_optional_file(task_dir / "handoff.md"),
        "plan.md": _read_optional_file(task_dir / "plan.md"),
        "feature_list.json": _read_optional_file(task_dir / "feature_list.json"),
        "progress.md": _read_optional_file(task_dir / "progress.md"),
        "init.sh": _read_optional_file(task_dir / "init.sh"),
        "review.md": _read_optional_file(task_dir / "review.md"),
        "qa.md": _read_optional_file(task_dir / "qa.md"),
        "roles.md": _read_optional_file(task_dir / "roles.md"),
        "topology.md": _read_optional_file(task_dir / "topology.md"),
        "evidence/manifest.json": _read_optional_file(task_dir / "evidence" / "manifest.json"),
    }


def _task_structured_payload(repo: Path, task_slug: str) -> dict[str, Any]:
    task_dir = repo / "docs" / "tasks" / task_slug
    structured: dict[str, Any] = {}
    feature_list_path = task_dir / "feature_list.json"
    evidence_manifest_path = task_dir / "evidence" / "manifest.json"
    if feature_list_path.exists():
        structured["feature_list"] = _load_feature_list(feature_list_path)
    if evidence_manifest_path.exists():
        structured["evidence_manifest"] = _load_evidence_manifest(evidence_manifest_path)
    return structured


def _read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def _read_optional_file(path: Path) -> str | None:
    if not path.exists():
        return None
    return _read_file(path)


def _extract_first_labeled_value(text: str, *labels: str) -> str | None:
    normalized_labels = {label.strip().lower() for label in labels}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line.startswith("- "):
            continue
        body = line[2:]
        if ":" not in body:
            continue
        key, value = body.split(":", 1)
        if key.strip().lower() in normalized_labels:
            cleaned = value.strip()
            if cleaned and not _is_template_placeholder(cleaned):
                return cleaned
    return None


def _extract_labeled_items(text: str, *labels: str) -> list[str]:
    groups = _collect_labeled_item_groups(text, *labels)
    if not groups:
        return []
    return groups[0]


def _extract_all_labeled_entries(text: str, *labels: str) -> list[str]:
    return ["; ".join(group) for group in _collect_labeled_item_groups(text, *labels)]


def _collect_labeled_item_groups(text: str, *labels: str) -> list[list[str]]:
    normalized_labels = {label.strip().lower() for label in labels}
    lines = text.splitlines()
    groups: list[list[str]] = []
    for index, raw_line in enumerate(lines):
        match = re.match(r"^(\s*)-\s+([^:]+):(.*)$", raw_line)
        if not match:
            continue
        if match.group(2).strip().lower() not in normalized_labels:
            continue

        base_indent = len(match.group(1))
        items: list[str] = []
        inline_value = _normalize_extracted_item(match.group(3))
        if inline_value and not _is_template_placeholder(inline_value):
            items.append(inline_value)

        for next_line in lines[index + 1 :]:
            if re.match(r"^\s*##\s+", next_line):
                break
            next_match = re.match(r"^(\s*)-\s+([^:]+):(.*)$", next_line)
            if next_match and len(next_match.group(1)) <= base_indent:
                break

            normalized = _normalize_extracted_item(next_line)
            if normalized and not _is_template_placeholder(normalized):
                items.append(normalized)
        if items:
            groups.append(items)
    return groups


def _extract_labeled_text(text: str, *labels: str) -> str | None:
    items = _extract_labeled_items(text, *labels)
    if not items:
        return None
    return "; ".join(items)


def _normalize_extracted_item(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        return ""
    if cleaned.startswith("- "):
        cleaned = cleaned[2:].strip()
    return cleaned.replace("`", "").strip()


def _is_template_placeholder(value: str) -> bool:
    return bool(TEMPLATE_PLACEHOLDER_RE.fullmatch(value.strip()))


def _parse_roles(text: str | None) -> list[dict[str, str]]:
    if not text:
        return []
    matches = list(re.finditer(r"^## Role \d+\s*$", text, flags=re.MULTILINE))
    roles: list[dict[str, str]] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        block = text[start:end]
        role = {
            "name": _extract_first_labeled_value(block, "이름", "name") or "",
            "type": _extract_first_labeled_value(block, "타입", "type") or "",
            "responsibility": _extract_labeled_text(block, "책임", "responsibility") or "",
            "success": _extract_labeled_text(block, "성공 조건", "success condition") or "",
            "inputs": _extract_labeled_text(block, "입력", "inputs") or "",
            "outputs": _extract_labeled_text(block, "출력", "outputs") or "",
            "artifacts": _extract_labeled_text(block, "생성하거나 갱신할 artifact", "artifacts") or "",
            "editable": _extract_labeled_text(block, "수정 가능한 범위", "editable scope") or "",
            "forbidden": _extract_labeled_text(block, "수정 금지 범위", "forbidden scope") or "",
            "handoff": _extract_first_labeled_value(block, "handoff 대상", "handoff target") or "",
            "escalation": _extract_labeled_text(block, "escalation trigger", "에스컬레이션 트리거") or "",
        }
        if any(role.values()):
            roles.append(role)
    return roles


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "agent"


def _claude_agent_file(*, name: str, description: str, tools: str, body: str) -> str:
    return "\n".join(
        [
            "---",
            f"name: {name}",
            f"description: {description}",
            f"tools: {tools}",
            "---",
            "",
            "<!-- Generated by Agent Work Harness. Edit canonical task files, then re-export. -->",
            "",
            body.strip(),
            "",
        ]
    )


def _claude_coordinator_body(repo: Path, task_slug: str) -> str:
    task_dir = repo / "docs" / "tasks" / task_slug
    topology = _read_optional_file(task_dir / "topology.md")
    plan = _read_optional_file(task_dir / "plan.md")
    long_running_lines = _claude_long_running_lines(repo, task_slug)
    return "\n".join(
        [
            f"You coordinate the task `{task_slug}`.",
            "",
            "Canonical files to read first:",
            f"- `docs/tasks/{task_slug}/contract.md`",
            f"- `docs/tasks/{task_slug}/handoff.md`",
            f"- `docs/tasks/{task_slug}/plan.md` when present",
            f"- `docs/tasks/{task_slug}/roles.md` when present",
            f"- `docs/tasks/{task_slug}/topology.md` when present",
            *long_running_lines,
            "",
            "Your job:",
            "- keep work aligned to the contract",
            "- route attention to the right task artifacts",
            "- avoid changing evaluation standards ad hoc",
            "- leave the task in a handoff-ready state",
            "",
            "Plan:",
            "",
            plan or "_Not present._",
            "",
            "Topology:",
            "",
            topology or "_Not present._",
        ]
    )


def _claude_reviewer_body(repo: Path, task_slug: str, review: str | None, qa: str | None) -> str:
    return "\n".join(
        [
            f"You are the reviewer for task `{task_slug}`.",
            "",
            "Priorities:",
            "- validate claims against canonical task artifacts",
            "- look for regressions, missing verification, and scope drift",
            "- prefer evidence over optimistic status",
            "",
            "Canonical files:",
            f"- `docs/tasks/{task_slug}/review.md`",
            f"- `docs/tasks/{task_slug}/qa.md`",
            f"- `docs/verification-plan.md`",
            "",
            "Review Notes:",
            "",
            review or "_Not present._",
            "",
            "QA Notes:",
            "",
            qa or "_Not present._",
        ]
    )


def _claude_role_description(task_slug: str, role: dict[str, str], *, index: int) -> str:
    role_name = role.get("name") or role.get("type") or f"role {index}"
    responsibility = role.get("responsibility") or "Handle the assigned portion of the task."
    return f"{role_name} for task {task_slug}. {responsibility}"


def _claude_role_body(repo: Path, task_slug: str, role: dict[str, str], *, index: int) -> str:
    role_name = role.get("name") or role.get("type") or f"role {index}"
    return "\n".join(
        [
            f"You are `{role_name}` for task `{task_slug}`.",
            "",
            "Canonical files:",
            f"- `docs/tasks/{task_slug}/contract.md`",
            f"- `docs/tasks/{task_slug}/handoff.md`",
            f"- `docs/tasks/{task_slug}/roles.md`",
            f"- `docs/tasks/{task_slug}/topology.md`",
            "",
            f"Role type: {role.get('type') or '_Not specified._'}",
            f"Responsibility: {role.get('responsibility') or '_Not specified._'}",
            f"Success condition: {role.get('success') or '_Not specified._'}",
            f"Inputs: {role.get('inputs') or '_Not specified._'}",
            f"Outputs: {role.get('outputs') or '_Not specified._'}",
            f"Artifacts to update: {role.get('artifacts') or '_Not specified._'}",
            f"Editable scope: {role.get('editable') or '_Use the contract mutable surface._'}",
            f"Forbidden scope: {role.get('forbidden') or '_Use the contract exclusions._'}",
            f"Handoff target: {role.get('handoff') or '_Not specified._'}",
            f"Escalation trigger: {role.get('escalation') or '_Not specified._'}",
        ]
    )


def _claude_role_tools(role: dict[str, str]) -> str:
    role_type = (role.get("type") or "").strip().lower()
    if role_type in {"generator", "integrator"}:
        return "Read, Grep, Glob, Edit, Write, Bash"
    return "Read, Grep, Glob, Bash"


def _copilot_apply_to_patterns(contract_text: str) -> str:
    raw_items = _extract_labeled_items(
        contract_text,
        "수정 가능한 파일",
        "editable files",
        "mutable surface",
    )
    if not raw_items:
        return "**"
    candidates: list[str] = []
    seen: set[str] = set()
    for raw_item in raw_items:
        for part in raw_item.split(","):
            candidate = part.strip()
            if not candidate or candidate.startswith("_") or candidate in seen:
                continue
            seen.add(candidate)
            candidates.append(candidate)
    return ",".join(candidates) if candidates else "**"


def _has_non_long_running_task_issues(issues: list[str], slug: str) -> bool:
    long_running_markers = (
        f"docs/tasks/{slug}/feature_list.json",
        f"docs/tasks/{slug}/progress.md",
        f"docs/tasks/{slug}/evidence/manifest.json",
    )
    return any(not any(marker in issue for marker in long_running_markers) for issue in issues)


def doctor_task_long_running_notes(repo: Path, slug: str) -> list[str]:
    notes: list[str] = []
    feature_list_path = task_artifact_path(repo, slug, "feature_list")
    evidence_manifest_path = task_artifact_path(repo, slug, "evidence_manifest")
    progress_path = task_artifact_path(repo, slug, "progress")

    if feature_list_path.exists():
        feature_errors = _feature_list_validation_errors(feature_list_path)
        if feature_errors:
            notes.extend(feature_errors)
        else:
            feature_list = _load_feature_list(feature_list_path)
            if not feature_list["features"]:
                notes.append(
                    f"`docs/tasks/{slug}/feature_list.json` is still empty. "
                    f"Next: add at least one tracked feature."
                )

    if evidence_manifest_path.exists():
        evidence_errors = _evidence_manifest_validation_errors(evidence_manifest_path)
        if evidence_errors:
            notes.extend(evidence_errors)
        else:
            evidence_manifest = _load_evidence_manifest(evidence_manifest_path)
            if not evidence_manifest["artifacts"]:
                notes.append(
                    f"`docs/tasks/{slug}/evidence/manifest.json` is still empty. "
                    f"Next: add at least one planned or collected evidence artifact."
                )

    progress_text = _read_optional_file(progress_path)
    if progress_text and not _progress_exact_next_step(progress_text):
        notes.append(
            f"`docs/tasks/{slug}/progress.md` is present but missing an exact next step. "
            f"Next: update the `Exact Next Step` section."
        )

    return notes


def _feature_list_validation_errors(path: Path) -> list[str]:
    try:
        payload = _load_json_file(path)
    except HarnessError as exc:
        return [str(exc)]

    issues: list[str] = []
    if not isinstance(payload, dict):
        return [f"`{path}` must contain a JSON object."]
    if payload.get("version") != 1:
        issues.append(f"`{path}` must set `version` to `1`.")
    if not isinstance(payload.get("task_slug"), str):
        issues.append(f"`{path}` must set `task_slug` to a string.")
    features = payload.get("features")
    if not isinstance(features, list):
        issues.append(f"`{path}` must set `features` to an array.")
        return issues
    for index, feature in enumerate(features):
        prefix = f"`{path}` feature #{index + 1}"
        if not isinstance(feature, dict):
            issues.append(f"{prefix} must be an object.")
            continue
        missing_keys = {"id", "description", "status", "priority", "notes", "evidence_refs"} - set(feature)
        if missing_keys:
            issues.append(f"{prefix} is missing keys: {', '.join(sorted(missing_keys))}.")
            continue
        if feature["status"] not in FEATURE_STATUS_VALUES:
            issues.append(
                f"{prefix} has invalid `status` `{feature['status']}`. "
                f"Use one of: {', '.join(sorted(FEATURE_STATUS_VALUES))}."
            )
        if feature["priority"] not in FEATURE_PRIORITY_VALUES:
            issues.append(
                f"{prefix} has invalid `priority` `{feature['priority']}`. "
                f"Use one of: {', '.join(sorted(FEATURE_PRIORITY_VALUES))}."
            )
        if not isinstance(feature["id"], str):
            issues.append(f"{prefix} must set `id` to a string.")
        if not isinstance(feature["description"], str):
            issues.append(f"{prefix} must set `description` to a string.")
        if not isinstance(feature["notes"], str):
            issues.append(f"{prefix} must set `notes` to a string.")
        if not isinstance(feature["evidence_refs"], list) or not all(
            isinstance(ref, str) for ref in feature["evidence_refs"]
        ):
            issues.append(f"{prefix} must set `evidence_refs` to an array of strings.")
    return issues


def _evidence_manifest_validation_errors(path: Path) -> list[str]:
    try:
        payload = _load_json_file(path)
    except HarnessError as exc:
        return [str(exc)]

    issues: list[str] = []
    if not isinstance(payload, dict):
        return [f"`{path}` must contain a JSON object."]
    if payload.get("version") != 1:
        issues.append(f"`{path}` must set `version` to `1`.")
    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, list):
        issues.append(f"`{path}` must set `artifacts` to an array.")
        return issues
    for index, artifact in enumerate(artifacts):
        prefix = f"`{path}` artifact #{index + 1}"
        if not isinstance(artifact, dict):
            issues.append(f"{prefix} must be an object.")
            continue
        missing_keys = {"id", "kind", "location", "summary", "status"} - set(artifact)
        if missing_keys:
            issues.append(f"{prefix} is missing keys: {', '.join(sorted(missing_keys))}.")
            continue
        if artifact["kind"] not in EVIDENCE_KIND_VALUES:
            issues.append(
                f"{prefix} has invalid `kind` `{artifact['kind']}`. "
                f"Use one of: {', '.join(sorted(EVIDENCE_KIND_VALUES))}."
            )
        if artifact["status"] not in EVIDENCE_STATUS_VALUES:
            issues.append(
                f"{prefix} has invalid `status` `{artifact['status']}`. "
                f"Use one of: {', '.join(sorted(EVIDENCE_STATUS_VALUES))}."
            )
        if not isinstance(artifact["id"], str):
            issues.append(f"{prefix} must set `id` to a string.")
        if not isinstance(artifact["location"], str):
            issues.append(f"{prefix} must set `location` to a string.")
        if not isinstance(artifact["summary"], str):
            issues.append(f"{prefix} must set `summary` to a string.")
    return issues


def _load_json_file(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise HarnessError(f"`{path}` contains invalid JSON: {exc.msg}.") from exc


def _load_feature_list(path: Path) -> dict[str, Any]:
    payload = _load_json_file(path)
    if not isinstance(payload, dict):
        raise HarnessError(f"`{path}` must contain a JSON object.")
    return payload


def _load_evidence_manifest(path: Path) -> dict[str, Any]:
    payload = _load_json_file(path)
    if not isinstance(payload, dict):
        raise HarnessError(f"`{path}` must contain a JSON object.")
    return payload


def _progress_exact_next_step(text: str) -> str | None:
    for line in _section_body_lines(text, "Exact Next Step"):
        normalized = _normalize_extracted_item(line)
        if normalized:
            return normalized
    return None


def _section_body_lines(text: str, heading: str) -> list[str]:
    lines = text.splitlines()
    start: int | None = None
    for index, line in enumerate(lines):
        if line.strip() == f"## {heading}":
            start = index + 1
            break
    if start is None:
        return []

    body: list[str] = []
    for line in lines[start:]:
        if re.match(r"^\s*##\s+", line):
            break
        body.append(line)
    return body


def _codex_long_running_lines(repo: Path, task_slug: str) -> list[str]:
    lines: list[str] = []
    present = present_long_running_artifacts(repo, task_slug)
    if not present:
        return ["_Not present._"]

    for relative_path in present:
        lines.append(f"- artifact: `{relative_path}`")

    feature_list_path = task_artifact_path(repo, task_slug, "feature_list")
    if feature_list_path.exists():
        feature_list = _load_feature_list(feature_list_path)
        features = feature_list.get("features", [])
        if features:
            counts = {status: 0 for status in sorted(FEATURE_STATUS_VALUES)}
            for feature in features:
                if isinstance(feature, dict) and feature.get("status") in counts:
                    counts[feature["status"]] += 1
            lines.append(
                "- feature counts: "
                + ", ".join(f"{status}={counts[status]}" for status in sorted(counts))
            )
        else:
            lines.append("- feature counts: no tracked features yet")

    progress_text = _read_optional_file(task_artifact_path(repo, task_slug, "progress"))
    if progress_text:
        lines.append(f"- progress next step: {_progress_exact_next_step(progress_text) or '_See progress.md._'}")

    return lines


def _claude_long_running_lines(repo: Path, task_slug: str) -> list[str]:
    present = present_long_running_artifacts(repo, task_slug)
    if not present:
        return []
    return [f"- `{relative_path}` when present" for relative_path in present]


def _copilot_long_running_lines(repo: Path, task_slug: str) -> list[str]:
    present = present_long_running_artifacts(repo, task_slug)
    return [f"- Read `{relative_path}` when it exists before resuming long-running work." for relative_path in present]
