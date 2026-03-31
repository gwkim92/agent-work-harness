from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Iterable
import shutil


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

TASK_OPTION_FILES = {
    "contract": "templates/task/contract.md",
    "handoff": "templates/task/handoff.md",
    "plan": "templates/task/plan.md",
    "review": "templates/task/review.md",
    "qa": "templates/task/qa.md",
    "roles": "templates/task/roles.md",
    "topology": "templates/task/topology.md",
    "loop_contract": "templates/task/loop_contract.md",
}

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
        CopyOperation(root / TASK_OPTION_FILES[name], task_dir / f"{name}.md")
        for name in _ordered_task_options(options)
    ]


def _ordered_task_options(options: set[str]) -> list[str]:
    ordered_names = [
        "contract",
        "handoff",
        "plan",
        "review",
        "qa",
        "roles",
        "topology",
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
        shutil.copyfile(operation.source, operation.destination)
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


def list_task_slugs(repo: Path) -> list[str]:
    tasks_dir = repo / "docs" / "tasks"
    if not tasks_dir.exists():
        return []
    return sorted(path.name for path in tasks_dir.iterdir() if path.is_dir())


def task_missing_evaluators(repo: Path, slug: str) -> bool:
    task_dir = repo / "docs" / "tasks" / slug
    return not ((task_dir / "review.md").exists() or (task_dir / "qa.md").exists())


def doctor_notes(repo: Path) -> list[str]:
    notes: list[str] = []
    missing_repo = verify_repo(repo)
    if missing_repo:
        notes.append("Harness is not fully installed. Run `awh init --profile default`.")
        notes.append("Missing repo files: " + ", ".join(missing_repo))
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
        validate_task_slug(task_slug)
        missing = verify_task(repo, task_slug)
        if missing:
            raise HarnessError(f"Task `{task_slug}` is not ready for export: missing {', '.join(missing)}")
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
    validate_task_slug(task_slug)
    missing = verify_task(repo, task_slug)
    if missing:
        raise HarnessError(f"Task `{task_slug}` is not ready for export: missing {', '.join(missing)}")
    return [
        WriteOperation(
            destination=repo / ".github" / "instructions" / f"{task_slug}.instructions.md",
            content=_copilot_task_content(repo, task_slug),
        )
    ]


def build_generic_json_export(repo: Path, task_slug: str | None = None) -> list[WriteOperation]:
    _require_repo_harness(repo)
    if task_slug:
        validate_task_slug(task_slug)
        missing = verify_task(repo, task_slug)
        if missing:
            raise HarnessError(f"Task `{task_slug}` is not ready for export: missing {', '.join(missing)}")
        payload = {
            "kind": "task",
            "task_slug": task_slug,
            "files": _task_file_payload(repo, task_slug),
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
        "review.md": _read_optional_file(task_dir / "review.md"),
        "qa.md": _read_optional_file(task_dir / "qa.md"),
        "roles.md": _read_optional_file(task_dir / "roles.md"),
        "topology.md": _read_optional_file(task_dir / "topology.md"),
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
            if cleaned:
                return cleaned
    return None


def _extract_labeled_items(text: str, *labels: str) -> list[str]:
    normalized_labels = {label.strip().lower() for label in labels}
    lines = text.splitlines()
    for index, raw_line in enumerate(lines):
        match = re.match(r"^(\s*)-\s+([^:]+):(.*)$", raw_line)
        if not match:
            continue
        if match.group(2).strip().lower() not in normalized_labels:
            continue

        base_indent = len(match.group(1))
        items: list[str] = []
        inline_value = _normalize_extracted_item(match.group(3))
        if inline_value:
            items.append(inline_value)

        for next_line in lines[index + 1 :]:
            if re.match(r"^\s*##\s+", next_line):
                break
            next_match = re.match(r"^(\s*)-\s+([^:]+):(.*)$", next_line)
            if next_match and len(next_match.group(1)) <= base_indent:
                break

            normalized = _normalize_extracted_item(next_line)
            if normalized:
                items.append(normalized)
        return items
    return []


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
