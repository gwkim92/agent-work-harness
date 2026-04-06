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


def verify_repo_strict_contents(repo: Path) -> list[str]:
    verification_text = _read_optional_file(repo / "docs" / "verification-plan.md")
    if not verification_text:
        return []

    issues: list[str] = []
    regression_behaviors = _extract_all_labeled_entries(
        verification_text,
        "유지되어야 하는 기존 동작",
        "regression guard",
    )
    regression_checks = _extract_all_labeled_entries(
        verification_text,
        "그것을 지키는 체크",
        "regression check",
    )
    rollback = _extract_all_labeled_entries(
        verification_text,
        "실패 시 끄거나 되돌리는 방법",
        "rollback",
    )
    human_confirmation = _extract_all_labeled_entries(
        verification_text,
        "여전히 사람이 판단해야 하는 항목",
        "human confirmation",
    )

    if not regression_behaviors or not regression_checks:
        issues.append("Add a filled `Regression Guard` section to `docs/verification-plan.md`.")
    if not rollback:
        issues.append("Add a filled `Rollback` section to `docs/verification-plan.md`.")
    if not human_confirmation:
        issues.append("Add at least one `Human Confirmation` item to `docs/verification-plan.md`.")
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


def verify_task_strict_contents(repo: Path, slug: str) -> list[str]:
    validate_task_slug(slug)
    task_dir = repo / "docs" / "tasks" / slug
    issues: list[str] = []

    review_path = task_dir / "review.md"
    qa_path = task_dir / "qa.md"
    evidence_manifest_path = task_dir / "evidence" / "manifest.json"

    if not review_path.exists():
        issues.append(f"Add `docs/tasks/{slug}/review.md` before running `verify --strict`.")
    else:
        review_text = _read_file(review_path)
        if not _extract_all_labeled_entries(review_text, "generator가 주장하는 완료 내용", "claimed outcome"):
            issues.append(f"Capture the claimed outcome in `docs/tasks/{slug}/review.md`.")
        if not _extract_all_labeled_entries(review_text, "실행한 명령", "commands run"):
            issues.append(f"Record at least one executed verification command in `docs/tasks/{slug}/review.md`.")
        if not (
            _extract_all_labeled_entries(review_text, "확인한 로그 또는 산출물", "checked outputs")
            or _extract_all_labeled_entries(review_text, "읽은 파일", "read files")
        ):
            issues.append(f"Record the checked evidence in `docs/tasks/{slug}/review.md`.")
        if not _extract_all_labeled_entries(review_text, "아직 남아 있는 위험", "residual risks"):
            issues.append(f"Capture residual risks in `docs/tasks/{slug}/review.md`.")
        if not _section_summary_items(review_text, "Verdict"):
            issues.append(f"Add a reviewer verdict to `docs/tasks/{slug}/review.md`.")

    if not qa_path.exists():
        issues.append(f"Add `docs/tasks/{slug}/qa.md` before running `verify --strict`.")
    else:
        qa_text = _read_file(qa_path)
        if not (
            _extract_all_labeled_entries(qa_text, "절차", "procedure")
            or _extract_all_labeled_entries(qa_text, "URL, route, endpoint, job", "runtime target")
        ):
            issues.append(f"Record at least one runtime or manual scenario in `docs/tasks/{slug}/qa.md`.")
        if not _extract_all_labeled_entries(qa_text, "실제 결과", "actual result"):
            issues.append(f"Record the actual QA result in `docs/tasks/{slug}/qa.md`.")
        if not _extract_all_labeled_entries(qa_text, "증거", "evidence"):
            issues.append(f"Record QA evidence in `docs/tasks/{slug}/qa.md`.")
        if not _section_summary_items(qa_text, "Verdict"):
            issues.append(f"Add a QA verdict to `docs/tasks/{slug}/qa.md`.")

    if not evidence_manifest_path.exists():
        issues.append(f"Add `docs/tasks/{slug}/evidence/manifest.json` before running `verify --strict`.")
    else:
        evidence_errors = _evidence_manifest_validation_errors(evidence_manifest_path)
        issues.extend(evidence_errors)
        if not evidence_errors:
            evidence_manifest = _load_evidence_manifest(evidence_manifest_path)
            collected = [
                artifact
                for artifact in evidence_manifest.get("artifacts", [])
                if isinstance(artifact, dict) and artifact.get("status") == "collected"
            ]
            if not collected:
                issues.append(
                    f"Record at least one collected evidence artifact in `docs/tasks/{slug}/evidence/manifest.json`."
                )

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


def task_has_multi_agent_docs(repo: Path, slug: str) -> bool:
    return task_artifact_path(repo, slug, "roles").exists() or task_artifact_path(repo, slug, "topology").exists()


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
        multi_agent_policy = _task_multi_agent_policy(repo, slug)
        if multi_agent_policy["docs_present"] and multi_agent_policy["issues"]:
            notes.append(f"Task `{slug}` has multi-agent docs that still need attention.")
            notes.extend(multi_agent_policy["issues"])
        elif multi_agent_policy["recommended"]:
            notes.append(
                f"Task `{slug}` may justify multi-agent docs. "
                f"Prefer `{multi_agent_policy['preferred_pattern']}` and keep the evaluator separate. "
                f"Consider `awh task augment {slug} --roles --topology`."
            )
            if multi_agent_policy["signals"]:
                notes.append("Signals: " + "; ".join(multi_agent_policy["signals"]))
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
            "briefing": _task_briefing_payload(repo, task_slug),
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
    issues = verify_repo_contents(repo)
    if issues:
        raise HarnessError("Repository is not ready for export: " + "; ".join(issues))


def _require_task_long_running_export_state(repo: Path, task_slug: str) -> None:
    validate_task_slug(task_slug)
    missing = verify_task(repo, task_slug)
    if missing:
        raise HarnessError(f"Task `{task_slug}` is not ready for export: missing {', '.join(missing)}")
    issues = verify_task_contents(repo, task_slug)
    if issues:
        raise HarnessError(f"Task `{task_slug}` is not ready for export: {'; '.join(issues)}")


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
    briefing = _task_briefing_payload(repo, task_slug)
    long_running_lines = _codex_long_running_lines(repo, task_slug)
    coordination_lines = _codex_coordination_lines(briefing["multi_agent_policy"])
    return "\n".join(
        [
            f"# Codex Task Packet: {task_slug}",
            "",
            "Use this packet as a compact briefing, but prefer canonical task files when details diverge.",
            "",
            "## Read First",
            "",
            *[f"- `{path}`" for path in briefing["read_first"]],
            "",
            "## Task Summary",
            "",
            f"- name: {briefing['name']}",
            f"- goal: {briefing['goal'] or '_Not captured in a single field._'}",
            f"- mutable surface: {_join_briefing_items(briefing['mutable_surface'], '_Use the contract mutable surface section._')}",
            f"- scope includes: {_join_briefing_items(briefing['scope_includes'], '_Use the contract scope section._')}",
            f"- scope excludes: {_join_briefing_items(briefing['scope_excludes'], '_See contract.md._')}",
            "",
            "## Current State",
            "",
            f"- completed: {_join_briefing_items(briefing['completed'], '_See handoff.md._')}",
            f"- in progress: {_join_briefing_items(briefing['in_progress'], '_See handoff.md._')}",
            f"- blockers: {_join_briefing_items(briefing['blockers'], '_None captured._')}",
            f"- current focus: {briefing['current_focus'] or '_See progress.md._'}",
            f"- next step: {briefing['next_step'] or briefing['progress_next_step'] or '_See handoff.md._'}",
            f"- open risks: {_join_briefing_items(briefing['open_risks'], '_No open risks captured._')}",
            "",
            "## Verification And Evidence",
            "",
            f"- verification commands: {_join_briefing_items(briefing['verification_commands'], '_Add verification commands in contract.md._')}",
            f"- useful commands: {_join_briefing_items(briefing['useful_commands'], '_See verification plan._')}",
            f"- evidence status: {_counts_text(briefing['evidence_counts'], empty='_No evidence manifest._')}",
            f"- recent evidence: {_join_briefing_items(briefing['recent_evidence'], '_No collected evidence yet._')}",
            "",
            "## Long-Running State",
            "",
            *long_running_lines,
            "",
            "## Coordination Policy",
            "",
            *coordination_lines,
            "",
            "## Canonical References",
            "",
            *[f"- `{path}`" for path in briefing["references"]],
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
    briefing = _task_briefing_payload(repo, task_slug)
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
            f"- Current focus: {briefing['current_focus'] or '_See progress.md._'}",
            f"- Blockers: {_join_briefing_items(briefing['blockers'], '_None captured._')}",
            f"- Next step: {briefing['next_step'] or briefing['progress_next_step'] or '_See handoff.md._'}",
            f"- Verification commands: {_join_briefing_items(briefing['verification_commands'], '_See contract.md._')}",
            f"- Evidence status: {_counts_text(briefing['evidence_counts'], empty='_No evidence manifest._')}",
            f"- Multi-agent policy: {_copilot_multi_agent_policy_text(briefing['multi_agent_policy'])}",
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


def _task_briefing_payload(repo: Path, task_slug: str) -> dict[str, Any]:
    task_dir = repo / "docs" / "tasks" / task_slug
    contract = _read_file(task_dir / "contract.md")
    handoff = _read_file(task_dir / "handoff.md")
    progress_text = _read_optional_file(task_dir / "progress.md")

    feature_list_path = task_dir / "feature_list.json"
    evidence_manifest_path = task_dir / "evidence" / "manifest.json"
    feature_list = _load_feature_list(feature_list_path) if feature_list_path.exists() else None
    evidence_manifest = _load_evidence_manifest(evidence_manifest_path) if evidence_manifest_path.exists() else None

    current_focus_items = _section_labeled_entries(progress_text, "Current Focus", "focus", "current focus")
    if not current_focus_items:
        current_focus_items = _section_summary_items(progress_text, "Current Focus")
    recent_sessions = _section_summary_items(progress_text, "Recent Sessions")
    open_risks = _section_labeled_entries(progress_text, "Open Risks", "risk", "open risk")
    if not open_risks:
        open_risks = _section_summary_items(progress_text, "Open Risks")
    useful_commands = _section_labeled_entries(progress_text, "Useful Commands", "command", "useful command")
    if not useful_commands:
        useful_commands = _section_summary_items(progress_text, "Useful Commands")

    return {
        "task_slug": task_slug,
        "name": _extract_first_labeled_value(contract, "이름") or task_slug,
        "goal": _extract_first_labeled_value(contract, "이 작업이 끝났을 때 반드시 참이어야 하는 상태"),
        "mutable_surface": _extract_all_labeled_entries(contract, "수정 가능한 파일", "수정 가능한 범위", "mutable surface"),
        "scope_includes": _extract_all_labeled_entries(contract, "포함", "includes"),
        "scope_excludes": _extract_all_labeled_entries(contract, "제외", "excludes"),
        "verification_commands": _extract_all_labeled_entries(contract, "검증에 사용할 명령", "verification command"),
        "completed": _extract_all_labeled_entries(handoff, "완료", "completed"),
        "in_progress": _extract_all_labeled_entries(handoff, "진행 중", "in progress"),
        "blockers": _extract_all_labeled_entries(handoff, "막힌 점", "blocked", "blockers"),
        "next_step": _extract_first_labeled_value(handoff, "다음 세션은 이것부터 시작", "exact next step"),
        "current_focus": current_focus_items[0] if current_focus_items else None,
        "recent_sessions": recent_sessions,
        "open_risks": open_risks,
        "useful_commands": useful_commands,
        "progress_next_step": _progress_exact_next_step(progress_text) if progress_text else None,
        "feature_counts": _feature_counts(feature_list),
        "evidence_counts": _evidence_counts(evidence_manifest),
        "recent_evidence": _recent_evidence_summaries(evidence_manifest),
        "multi_agent_policy": _task_multi_agent_policy(repo, task_slug),
        "read_first": _task_read_first_paths(repo, task_slug),
        "references": _task_reference_paths(repo, task_slug),
    }


def _task_read_first_paths(repo: Path, task_slug: str) -> list[str]:
    candidates = [
        task_artifact_path(repo, task_slug, "contract"),
        task_artifact_path(repo, task_slug, "handoff"),
        task_artifact_path(repo, task_slug, "progress"),
        task_artifact_path(repo, task_slug, "feature_list"),
        task_artifact_path(repo, task_slug, "evidence_manifest"),
        task_artifact_path(repo, task_slug, "plan"),
        task_artifact_path(repo, task_slug, "review"),
        task_artifact_path(repo, task_slug, "qa"),
        task_artifact_path(repo, task_slug, "roles"),
        task_artifact_path(repo, task_slug, "topology"),
    ]
    return [str(path.relative_to(repo)) for path in candidates if path.exists()]


def _task_reference_paths(repo: Path, task_slug: str) -> list[str]:
    candidates = [
        task_artifact_path(repo, task_slug, "contract"),
        task_artifact_path(repo, task_slug, "handoff"),
        task_artifact_path(repo, task_slug, "plan"),
        task_artifact_path(repo, task_slug, "review"),
        task_artifact_path(repo, task_slug, "qa"),
        task_artifact_path(repo, task_slug, "roles"),
        task_artifact_path(repo, task_slug, "topology"),
        task_artifact_path(repo, task_slug, "feature_list"),
        task_artifact_path(repo, task_slug, "progress"),
        task_artifact_path(repo, task_slug, "init_script"),
        task_artifact_path(repo, task_slug, "evidence_manifest"),
    ]
    references: list[str] = []
    for path in candidates:
        if not path.exists():
            continue
        relative = str(path.relative_to(repo))
        if relative not in references:
            references.append(relative)
    return references


def _feature_counts(feature_list: dict[str, Any] | None) -> dict[str, int] | None:
    if feature_list is None:
        return None
    counts = {status: 0 for status in sorted(FEATURE_STATUS_VALUES)}
    for feature in feature_list.get("features", []):
        if isinstance(feature, dict) and feature.get("status") in counts:
            counts[feature["status"]] += 1
    return counts


def _evidence_counts(evidence_manifest: dict[str, Any] | None) -> dict[str, int] | None:
    if evidence_manifest is None:
        return None
    counts = {status: 0 for status in sorted(EVIDENCE_STATUS_VALUES)}
    for artifact in evidence_manifest.get("artifacts", []):
        if isinstance(artifact, dict) and artifact.get("status") in counts:
            counts[artifact["status"]] += 1
    return counts


def _recent_evidence_summaries(evidence_manifest: dict[str, Any] | None) -> list[str]:
    if evidence_manifest is None:
        return []
    summaries: list[str] = []
    for artifact in evidence_manifest.get("artifacts", []):
        if not isinstance(artifact, dict):
            continue
        if artifact.get("status") != "collected":
            continue
        summary = str(artifact.get("summary") or "").strip()
        artifact_id = str(artifact.get("id") or "").strip()
        location = str(artifact.get("location") or "").strip()
        parts = [part for part in (artifact_id, summary, location) if part]
        if parts:
            summaries.append(" | ".join(parts))
    return summaries[:3]


def _task_multi_agent_policy(repo: Path, task_slug: str) -> dict[str, Any]:
    task_dir = repo / "docs" / "tasks" / task_slug
    contract = _read_file(task_dir / "contract.md")
    review_text = _read_optional_file(task_dir / "review.md")
    qa_text = _read_optional_file(task_dir / "qa.md")
    roles_path = task_dir / "roles.md"
    topology_path = task_dir / "topology.md"
    roles_text = _read_optional_file(roles_path)
    topology_text = _read_optional_file(topology_path)
    feature_list_path = task_dir / "feature_list.json"
    feature_list = None
    if feature_list_path.exists() and not _feature_list_validation_errors(feature_list_path):
        feature_list = _load_feature_list(feature_list_path)

    mutable_surface_entries = _split_briefing_entries(
        _extract_all_labeled_entries(contract, "수정 가능한 파일", "수정 가능한 범위", "mutable surface")
    )
    non_done_features = 0
    total_features = 0
    if feature_list is not None:
        total_features = len(feature_list.get("features", []))
        non_done_features = sum(
            1
            for feature in feature_list.get("features", [])
            if isinstance(feature, dict) and feature.get("status") != "done"
        )

    has_plan = task_has_plan(repo, task_slug)
    review_signal = _review_artifact_has_signal(review_text)
    qa_signal = _qa_artifact_has_signal(qa_text)

    signals: list[str] = []
    if review_signal or qa_signal:
        signals.append("evaluator artifacts contain non-template verification notes")
    if len(mutable_surface_entries) >= 2:
        signals.append("mutable surface spans multiple areas")
    if non_done_features >= 2 or total_features >= 3:
        signals.append("long-running state tracks multiple items")

    preferred_pattern = "coordinator + specialists" if len(mutable_surface_entries) >= 2 else "planner -> generator -> evaluator"
    docs_present = roles_path.exists() or topology_path.exists()
    recommended = has_plan and (review_signal or qa_signal) and len(signals) >= 2 and not docs_present

    issues: list[str] = []
    chosen_pattern: str | None = None

    if roles_text:
        chosen_pattern = _extract_first_labeled_value(roles_text, "선택한 패턴", "chosen pattern")
        if not _extract_all_labeled_entries(roles_text, "왜 single-agent로는 부족한가", "why single-agent is insufficient"):
            issues.append(f"Explain why single-agent is insufficient in `docs/tasks/{task_slug}/roles.md`.")
        if not chosen_pattern:
            issues.append(f"Choose a concrete pattern in `docs/tasks/{task_slug}/roles.md`.")
        if not _extract_all_labeled_entries(roles_text, "최종 decision maker", "final decision maker"):
            issues.append(f"Define the final decision maker in `docs/tasks/{task_slug}/roles.md`.")

        parsed_roles = _parse_roles(roles_text)
        if not parsed_roles:
            issues.append(f"Add at least one filled role definition to `docs/tasks/{task_slug}/roles.md`.")
        else:
            role_types = {role.get("type", "").strip().lower() for role in parsed_roles if role.get("type")}
            implementation_roles = {
                role_type for role_type in role_types if role_type in {"generator", "specialist", "integrator", "coordinator", "planner"}
            }
            if len(implementation_roles) >= 2 and "evaluator" not in role_types:
                issues.append(
                    f"Separate an evaluator role in `docs/tasks/{task_slug}/roles.md` before relying on multi-agent execution."
                )
            for role in parsed_roles:
                role_name = role.get("name") or role.get("type") or "unnamed role"
                if not role.get("artifacts"):
                    issues.append(
                        f"Define artifact handoff outputs for role `{role_name}` in `docs/tasks/{task_slug}/roles.md`."
                    )
                if not role.get("editable"):
                    issues.append(
                        f"Define editable ownership for role `{role_name}` in `docs/tasks/{task_slug}/roles.md`."
                    )

    if topology_text:
        if not _extract_all_labeled_entries(topology_text, "왜 이 구조가 필요한가", "why this topology"):
            issues.append(f"Explain why the topology is needed in `docs/tasks/{task_slug}/topology.md`.")
        if not _extract_all_labeled_entries(topology_text, "누가 final gate를 쥐는가", "final gate"):
            issues.append(f"Define the final gate in `docs/tasks/{task_slug}/topology.md`.")
        if not _extract_all_labeled_entries(topology_text, "source of truth는 어디인가", "source of truth"):
            issues.append(f"Define the source of truth in `docs/tasks/{task_slug}/topology.md`.")
        if not _extract_all_labeled_entries(topology_text, "handoff artifact", "handoff artifact"):
            issues.append(f"Add explicit handoff artifacts to `docs/tasks/{task_slug}/topology.md`.")
    if chosen_pattern:
        lowered_pattern = chosen_pattern.lower()
        parsed_roles = _parse_roles(roles_text) if roles_text else []
        role_types = {role.get("type", "").strip().lower() for role in parsed_roles if role.get("type")}
        if "coordinator" in lowered_pattern and "coordinator" not in role_types:
            issues.append(f"Add a coordinator role to `docs/tasks/{task_slug}/roles.md` for the chosen topology.")
        if "integrator" in lowered_pattern and "integrator" not in role_types:
            issues.append(f"Add an integrator role to `docs/tasks/{task_slug}/roles.md` for the chosen topology.")
        if "evaluator" in lowered_pattern and "evaluator" not in role_types:
            issues.append(f"Add an evaluator role to `docs/tasks/{task_slug}/roles.md` for the chosen topology.")

    return {
        "docs_present": docs_present,
        "recommended": recommended,
        "preferred_pattern": preferred_pattern,
        "signals": signals,
        "issues": issues,
        "chosen_pattern": chosen_pattern,
    }


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


def _join_briefing_items(values: str | list[str] | None, empty: str) -> str:
    if values is None:
        return empty
    if isinstance(values, str):
        return values or empty
    filtered = [value for value in values if value]
    return "; ".join(filtered) if filtered else empty


def _split_briefing_entries(values: list[str]) -> list[str]:
    entries: list[str] = []
    for raw_value in values:
        for part in re.split(r"[;,]", raw_value):
            candidate = part.strip()
            if candidate:
                entries.append(candidate)
    return entries


def _counts_text(counts: dict[str, int] | None, *, empty: str) -> str:
    if not counts:
        return empty
    return ", ".join(f"{key}={counts[key]}" for key in sorted(counts))


def _codex_coordination_lines(policy: dict[str, Any]) -> list[str]:
    if policy["docs_present"] and policy["issues"]:
        return [f"- issue: {issue}" for issue in policy["issues"]]
    if policy["recommended"]:
        lines = [
            f"- recommendation: add `roles.md` and `topology.md` only if you will actually escalate coordination",
            f"- preferred pattern: {policy['preferred_pattern']}",
            "- coordination bias: keep a central coordinator and leave evaluation separate",
        ]
        if policy["signals"]:
            lines.append("- signals: " + "; ".join(policy["signals"]))
        return lines
    if policy["docs_present"]:
        return [
            f"- chosen pattern: {policy['chosen_pattern'] or '_See roles.md._'}",
            "- policy: keep coordination centralized and preserve a separate evaluator gate",
        ]
    return ["- policy: stay single-agent unless stronger parallel ownership signals appear"]


def _claude_multi_agent_lines(policy: dict[str, Any]) -> list[str]:
    if policy["docs_present"] and policy["issues"]:
        return [f"- {issue}" for issue in policy["issues"]]
    if policy["recommended"]:
        lines = [
            f"- preferred pattern: `{policy['preferred_pattern']}`",
            "- keep coordination centralized and avoid parallel execution without explicit ownership",
            "- keep the evaluator separate from implementation",
        ]
        if policy["signals"]:
            lines.append("- recommendation signals: " + "; ".join(policy["signals"]))
        return lines
    if policy["docs_present"]:
        return [
            f"- chosen pattern: `{policy['chosen_pattern'] or 'see roles.md'}`",
            "- preserve centralized coordination and an explicit evaluator gate",
        ]
    return ["- stay single-agent unless the task grows stronger coordination signals"]


def _copilot_multi_agent_policy_text(policy: dict[str, Any]) -> str:
    if policy["docs_present"] and policy["issues"]:
        return "repair `roles.md` / `topology.md` before treating the task as multi-agent-ready"
    if policy["recommended"]:
        return f"if you escalate, prefer `{policy['preferred_pattern']}` and keep evaluation separate"
    if policy["docs_present"]:
        return f"use `{policy['chosen_pattern'] or 'the documented pattern'}` and keep evaluation separate"
    return "stay single-agent by default"


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
    briefing = _task_briefing_payload(repo, task_slug)
    multi_agent_lines = _claude_multi_agent_lines(briefing["multi_agent_policy"])
    return "\n".join(
        [
            f"You coordinate the task `{task_slug}`.",
            "",
            "Canonical files to read first:",
            *[f"- `{path}`" for path in briefing["read_first"]],
            "",
            "Current briefing:",
            f"- goal: {briefing['goal'] or '_Not captured in a single field._'}",
            f"- mutable surface: {_join_briefing_items(briefing['mutable_surface'], '_Use contract.md._')}",
            f"- completed: {_join_briefing_items(briefing['completed'], '_See handoff.md._')}",
            f"- in progress: {_join_briefing_items(briefing['in_progress'], '_See handoff.md._')}",
            f"- blockers: {_join_briefing_items(briefing['blockers'], '_None captured._')}",
            f"- current focus: {briefing['current_focus'] or '_See progress.md._'}",
            f"- next step: {briefing['next_step'] or briefing['progress_next_step'] or '_See handoff.md._'}",
            "",
            "Verification path:",
            f"- verification commands: {_join_briefing_items(briefing['verification_commands'], '_See contract.md._')}",
            f"- evidence status: {_counts_text(briefing['evidence_counts'], empty='_No evidence manifest._')}",
            f"- recent evidence: {_join_briefing_items(briefing['recent_evidence'], '_No collected evidence yet._')}",
            "",
            "Coordination policy:",
            *multi_agent_lines,
            "",
            "Canonical references to consult as needed:",
            *[f"- `{path}`" for path in briefing["references"]],
            "",
            "Your job:",
            "- keep work aligned to the contract",
            "- route attention to the right task artifacts",
            "- avoid changing evaluation standards ad hoc",
            "- leave the task in a handoff-ready state",
        ]
    )


def _claude_reviewer_body(repo: Path, task_slug: str, review: str | None, qa: str | None) -> str:
    briefing = _task_briefing_payload(repo, task_slug)
    multi_agent_lines = _claude_multi_agent_lines(briefing["multi_agent_policy"])
    reviewer_paths = [
        f"docs/tasks/{task_slug}/review.md",
        f"docs/tasks/{task_slug}/qa.md",
        "docs/verification-plan.md",
        f"docs/tasks/{task_slug}/contract.md",
        f"docs/tasks/{task_slug}/handoff.md",
    ]
    evidence_manifest = task_artifact_path(repo, task_slug, "evidence_manifest")
    if evidence_manifest.exists():
        reviewer_paths.append(str(evidence_manifest.relative_to(repo)))
    return "\n".join(
        [
            f"You are the reviewer for task `{task_slug}`.",
            "",
            "Read these canonical files first:",
            *[f"- `{path}`" for path in reviewer_paths],
            "",
            "Current verification context:",
            f"- goal: {briefing['goal'] or '_Not captured in a single field._'}",
            f"- claimed completed work: {_join_briefing_items(briefing['completed'], '_See handoff.md._')}",
            f"- in progress: {_join_briefing_items(briefing['in_progress'], '_See handoff.md._')}",
            f"- blockers: {_join_briefing_items(briefing['blockers'], '_None captured._')}",
            f"- next step: {briefing['next_step'] or briefing['progress_next_step'] or '_See handoff.md._'}",
            f"- verification commands: {_join_briefing_items(briefing['verification_commands'], '_See contract.md._')}",
            f"- evidence status: {_counts_text(briefing['evidence_counts'], empty='_No evidence manifest._')}",
            f"- recent evidence: {_join_briefing_items(briefing['recent_evidence'], '_No collected evidence yet._')}",
            "",
            "Coordination policy:",
            *multi_agent_lines,
            "",
            "Priorities:",
            "- validate claims against canonical task artifacts",
            "- look for regressions, missing verification, and scope drift",
            "- prefer evidence over optimistic status",
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
    elif _is_blank_or_placeholder(payload["task_slug"]):
        issues.append(f"`{path}` must replace the scaffold `task_slug` placeholder with a real task slug.")
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
        elif _is_blank_or_placeholder(feature["id"]):
            issues.append(f"{prefix} must set `id` to a non-empty string.")
        if not isinstance(feature["description"], str):
            issues.append(f"{prefix} must set `description` to a string.")
        elif _is_blank_or_placeholder(feature["description"]):
            issues.append(f"{prefix} must set `description` to a non-empty string.")
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
        elif _is_blank_or_placeholder(artifact["id"]):
            issues.append(f"{prefix} must set `id` to a non-empty string.")
        if not isinstance(artifact["location"], str):
            issues.append(f"{prefix} must set `location` to a string.")
        elif _is_blank_or_placeholder(artifact["location"]):
            issues.append(f"{prefix} must set `location` to a non-empty string.")
        if not isinstance(artifact["summary"], str):
            issues.append(f"{prefix} must set `summary` to a string.")
        elif _is_blank_or_placeholder(artifact["summary"]):
            issues.append(f"{prefix} must set `summary` to a non-empty string.")
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


def _review_artifact_has_signal(text: str | None) -> bool:
    if not text:
        return False
    return bool(
        _extract_all_labeled_entries(text, "generator가 주장하는 완료 내용", "claimed outcome")
        or _extract_all_labeled_entries(text, "실행한 명령", "commands run")
        or _extract_all_labeled_entries(text, "확인한 로그 또는 산출물", "checked outputs")
        or _extract_all_labeled_entries(text, "읽은 파일", "read files")
        or _extract_all_labeled_entries(text, "아직 남아 있는 위험", "residual risks")
    )


def _qa_artifact_has_signal(text: str | None) -> bool:
    if not text:
        return False
    has_target = bool(
        _extract_all_labeled_entries(text, "절차", "procedure")
        or _extract_all_labeled_entries(text, "URL, route, endpoint, job", "runtime target")
    )
    has_result = bool(
        _extract_all_labeled_entries(text, "실제 결과", "actual result")
        or _extract_all_labeled_entries(text, "증거", "evidence")
    )
    return has_target and has_result


def _is_blank_or_placeholder(value: str) -> bool:
    return not value.strip() or _is_template_placeholder(value)


def _progress_exact_next_step(text: str) -> str | None:
    labeled = _section_labeled_entries(text, "Exact Next Step", "step", "next step")
    if labeled:
        return labeled[0]
    for line in _section_body_lines(text, "Exact Next Step"):
        normalized = _normalize_extracted_item(line)
        if normalized:
            return normalized
    return None


def _section_summary_items(text: str | None, heading: str) -> list[str]:
    if not text:
        return []
    items: list[str] = []
    for line in _section_body_lines(text, heading):
        normalized = _normalize_extracted_item(line)
        if normalized and not _is_template_placeholder(normalized):
            items.append(normalized)
    return items


def _section_labeled_entries(text: str | None, heading: str, *labels: str) -> list[str]:
    if not text:
        return []
    body_lines = _section_body_lines(text, heading)
    if not body_lines:
        return []
    return _extract_all_labeled_entries("\n".join(body_lines), *labels)


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
