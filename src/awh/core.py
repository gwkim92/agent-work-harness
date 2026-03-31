from __future__ import annotations

from dataclasses import dataclass
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

