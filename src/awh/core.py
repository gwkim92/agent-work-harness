from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
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
            raise HarnessError("Task-scoped Copilot export is not supported yet.")
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


def build_generic_json_export(repo: Path, task_slug: str | None = None) -> list[WriteOperation]:
    _require_repo_harness(repo)
    if task_slug:
        validate_task_slug(task_slug)
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
            "This file is a Claude-oriented mirror of the canonical repository harness.",
            "",
            "## Canonical Source Of Truth",
            "",
            "- `AGENTS.md`",
            "- `docs/verification-plan.md`",
            "- `docs/escalation-rules.md` when present",
            "- `docs/tasks/` for task state",
            "",
            "## Repository Instructions",
            "",
            _read_file(repo / "AGENTS.md"),
            "",
            "## Verification Plan",
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
            destination=repo / ".claude" / "agents" / f"{task_slug}-orchestrator.md",
            content="\n".join(
                [
                    f"# {task_slug} Orchestrator",
                    "",
                    "<!-- Generated by Agent Work Harness. Edit canonical task files, then re-export. -->",
                    "",
                    "Use these task files as the source of truth:",
                    "",
                    f"- `docs/tasks/{task_slug}/contract.md`",
                    f"- `docs/tasks/{task_slug}/handoff.md`",
                    f"- `docs/tasks/{task_slug}/plan.md` when present",
                    f"- `docs/tasks/{task_slug}/roles.md` when present",
                    f"- `docs/tasks/{task_slug}/topology.md` when present",
                    "",
                    "## Contract",
                    "",
                    _read_file(task_dir / "contract.md"),
                    "",
                    "## Handoff",
                    "",
                    _read_file(task_dir / "handoff.md"),
                    "",
                    "## Plan",
                    "",
                    _read_optional_file(task_dir / "plan.md") or "_Not present._",
                    "",
                    "## Roles",
                    "",
                    _read_optional_file(task_dir / "roles.md") or "_Not present._",
                    "",
                    "## Topology",
                    "",
                    _read_optional_file(task_dir / "topology.md") or "_Not present._",
                    "",
                ]
            ),
        )
    ]

    review = _read_optional_file(task_dir / "review.md")
    qa = _read_optional_file(task_dir / "qa.md")
    if review or qa:
        operations.append(
            WriteOperation(
                destination=repo / ".claude" / "agents" / f"{task_slug}-reviewer.md",
                content="\n".join(
                    [
                        f"# {task_slug} Reviewer",
                        "",
                        "<!-- Generated by Agent Work Harness. Edit canonical task files, then re-export. -->",
                        "",
                        "Use this file to keep evaluation separate from generation.",
                        "",
                        "## Review Notes",
                        "",
                        review or "_Not present._",
                        "",
                        "## QA Notes",
                        "",
                        qa or "_Not present._",
                        "",
                    ]
                ),
            )
        )
    return operations


def _codex_repo_content(repo: Path) -> str:
    return "\n".join(
        [
            "# Codex Export Packet",
            "",
            "This packet mirrors the canonical repository harness for Codex-oriented workflows.",
            "",
            "## Canonical Files",
            "",
            "- `AGENTS.md`",
            "- `docs/verification-plan.md`",
            "- `docs/tasks/`",
            "",
            "## AGENTS",
            "",
            _read_file(repo / "AGENTS.md"),
            "",
            "## Verification",
            "",
            _read_file(repo / "docs" / "verification-plan.md"),
            "",
            "## Known Tasks",
            "",
            "\n".join(f"- `{slug}`" for slug in list_task_slugs(repo)) or "_No task directories yet._",
            "",
        ]
    )


def _codex_task_content(repo: Path, task_slug: str) -> str:
    task_dir = repo / "docs" / "tasks" / task_slug
    return "\n".join(
        [
            f"# Codex Task Packet: {task_slug}",
            "",
            "Use the canonical task files below as the source of truth.",
            "",
            "## Contract",
            "",
            _read_file(task_dir / "contract.md"),
            "",
            "## Handoff",
            "",
            _read_file(task_dir / "handoff.md"),
            "",
            "## Plan",
            "",
            _read_optional_file(task_dir / "plan.md") or "_Not present._",
            "",
            "## Review",
            "",
            _read_optional_file(task_dir / "review.md") or "_Not present._",
            "",
            "## QA",
            "",
            _read_optional_file(task_dir / "qa.md") or "_Not present._",
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
