from __future__ import annotations

import argparse
from typing import Sequence

from .core import (
    apply_write_plan,
    HarnessError,
    apply_copy_plan,
    doctor_notes,
    ensure_target_repo,
    export_plan,
    preflight_copy,
    preflight_write,
    repo_plan,
    task_plan,
    verify_repo,
    verify_repo_contents,
    verify_task,
    verify_task_contents,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="awh", description="Agent Work Harness CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Install repo-level harness files.")
    init_parser.add_argument("--profile", choices=("minimal", "default"), default="default")
    init_parser.add_argument("--repo", default=".", help="Target repository path. Defaults to the current directory.")
    init_parser.add_argument("--force", action="store_true")
    init_parser.add_argument("--dry-run", action="store_true", help="Show planned writes without changing files.")

    task_parser = subparsers.add_parser("task", help="Manage task-level artifacts.")
    task_subparsers = task_parser.add_subparsers(dest="task_command", required=True)

    task_new = task_subparsers.add_parser("new", help="Create a new task directory.")
    _add_task_common_arguments(task_new, include_only_missing=False)

    task_augment = task_subparsers.add_parser("augment", help="Add missing files to an existing task.")
    _add_task_common_arguments(task_augment, include_only_missing=True)

    verify_parser = subparsers.add_parser("verify", help="Check harness file health.")
    verify_parser.add_argument("--repo", default=".", help="Target repository path. Defaults to the current directory.")
    verify_parser.add_argument("--task", help="Task slug to validate in addition to the repo-level files.")

    doctor_parser = subparsers.add_parser("doctor", help="Suggest the next harness step.")
    doctor_parser.add_argument("--repo", default=".", help="Target repository path. Defaults to the current directory.")

    export_parser = subparsers.add_parser("export", help="Generate adapter outputs from canonical harness files.")
    export_parser.add_argument("target", choices=("claude", "codex", "copilot", "generic-json"))
    export_parser.add_argument("--repo", default=".", help="Target repository path. Defaults to the current directory.")
    export_parser.add_argument("--task", help="Task slug to export. Omit for repo-level export.")
    export_parser.add_argument("--force", action="store_true")
    export_parser.add_argument("--dry-run", action="store_true", help="Show planned writes without changing files.")

    return parser


def _add_task_common_arguments(parser: argparse.ArgumentParser, *, include_only_missing: bool) -> None:
    parser.add_argument("slug")
    parser.add_argument("--profile", choices=("general", "web", "backend", "research", "dependency"), default="general")
    parser.add_argument("--repo", default=".", help="Target repository path. Defaults to the current directory.")
    parser.add_argument("--plan", action="store_true", help="Add `plan.md`.")
    parser.add_argument(
        "--long-running",
        action="store_true",
        dest="long_running",
        help="Add long-running task support files (`feature_list.json`, `progress.md`, `init.sh`, `evidence/manifest.json`).",
    )
    parser.add_argument("--feature-list", action="store_true", dest="feature_list", help="Add `feature_list.json`.")
    parser.add_argument("--progress", action="store_true", help="Add `progress.md`.")
    parser.add_argument("--init-script", action="store_true", dest="init_script", help="Add `init.sh`.")
    parser.add_argument("--review", action="store_true", help="Add `review.md`.")
    parser.add_argument("--qa", action="store_true", help="Add `qa.md`.")
    parser.add_argument("--roles", action="store_true", help="Add `roles.md`.")
    parser.add_argument("--topology", action="store_true", help="Add `topology.md`.")
    parser.add_argument(
        "--evidence-manifest",
        action="store_true",
        dest="evidence_manifest",
        help="Add `evidence/manifest.json`.",
    )
    parser.add_argument("--loop-contract", action="store_true", dest="loop_contract", help="Add `loop_contract.md`.")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true", help="Show planned writes without changing files.")
    if include_only_missing:
        parser.add_argument("--only-missing", action="store_true", default=True, help=argparse.SUPPRESS)


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "init":
            return run_init(args.profile, args.repo, force=args.force, dry_run=args.dry_run)
        if args.command == "task":
            if args.task_command == "new":
                return run_task_write(
                    slug=args.slug,
                    profile=args.profile,
                    repo=args.repo,
                    extra_options=_task_options_from_args(args),
                    force=args.force,
                    only_missing=False,
                    dry_run=args.dry_run,
                )
            if args.task_command == "augment":
                return run_task_write(
                    slug=args.slug,
                    profile=args.profile,
                    repo=args.repo,
                    extra_options=_task_options_from_args(args),
                    force=args.force,
                    only_missing=True,
                    dry_run=args.dry_run,
                )
        if args.command == "verify":
            return run_verify(args.repo, task_slug=args.task)
        if args.command == "doctor":
            return run_doctor(args.repo)
        if args.command == "export":
            return run_export(args.target, args.repo, task_slug=args.task, force=args.force, dry_run=args.dry_run)
    except HarnessError as exc:
        print(exc)
        return 1

    parser.error("Unknown command")
    return 2


def _task_options_from_args(args: argparse.Namespace) -> set[str]:
    options = set()
    if args.plan:
        options.add("plan")
    if args.long_running:
        options |= {"feature_list", "progress", "init_script", "evidence_manifest"}
    if args.feature_list:
        options.add("feature_list")
    if args.progress:
        options.add("progress")
    if args.init_script:
        options.add("init_script")
    if args.review:
        options.add("review")
    if args.qa:
        options.add("qa")
    if args.roles:
        options.add("roles")
    if args.topology:
        options.add("topology")
    if args.evidence_manifest:
        options.add("evidence_manifest")
    if args.loop_contract:
        options.add("loop_contract")
    return options


def run_init(profile: str, repo_arg: str, *, force: bool, dry_run: bool) -> int:
    repo = ensure_target_repo(repo_arg)
    effective, skipped, conflicts = preflight_copy(repo_plan(profile, repo), force=force)
    if conflicts:
        if dry_run:
            _print_copy_preview(effective, skipped, conflicts, action="install")
        for conflict in conflicts:
            print(f"Refusing to overwrite existing file: {conflict}")
        print("No files were copied. Re-run with --force to overwrite.")
        return 1

    if dry_run:
        _print_copy_preview(effective, skipped, conflicts, action="install")
        print("Dry run only. No files were written.")
        return 0

    written = apply_copy_plan(effective)
    for path in written:
        print(f"installed {path}")
    if skipped:
        for path in skipped:
            print(f"skipped existing file: {path}")
    print(f"Next: fill {repo / 'AGENTS.md'} and {repo / 'docs/verification-plan.md'}")
    return 0


def run_task_write(
    *,
    slug: str,
    profile: str,
    repo: str,
    extra_options: set[str],
    force: bool,
    only_missing: bool,
    dry_run: bool,
) -> int:
    target_repo = ensure_target_repo(repo)
    operations = task_plan(profile, target_repo, slug, extra_options=extra_options)
    effective, skipped, conflicts = preflight_copy(operations, force=force, only_missing=only_missing)
    if conflicts:
        if dry_run:
            _print_copy_preview(effective, skipped, conflicts, action="install")
        for conflict in conflicts:
            print(f"Refusing to overwrite existing file: {conflict}")
        print("No files were copied. Re-run with --force to overwrite.")
        return 1

    if dry_run:
        _print_copy_preview(effective, skipped, conflicts, action="install")
        if not effective and skipped:
            print("Dry run only. No files would be written.")
            return 0
        print("Dry run only. No files were written.")
        return 0

    if not effective and skipped:
        for path in skipped:
            print(f"skipped existing file: {path}")
        print("No missing files to copy.")
        return 0

    for path in skipped:
        print(f"skipped existing file: {path}")
    written = apply_copy_plan(effective)
    for path in written:
        print(f"installed {path}")
    print(f"Next: fill {target_repo / 'docs' / 'tasks' / slug / 'contract.md'}")
    return 0


def run_verify(repo_arg: str, *, task_slug: str | None) -> int:
    repo = ensure_target_repo(repo_arg)
    missing = verify_repo(repo)
    if missing:
        print("Repository is missing required harness files:")
        for path in missing:
            print(f"- {path}")
        return 1

    repo_issues = verify_repo_contents(repo)
    if repo_issues:
        print("Repository harness files exist but still need project-specific content:")
        for issue in repo_issues:
            print(f"- {issue}")
        return 1

    if task_slug:
        missing_task = verify_task(repo, task_slug)
        if missing_task:
            print(f"Task `{task_slug}` is missing required files:")
            for path in missing_task:
                print(f"- {path}")
            return 1
        task_issues = verify_task_contents(repo, task_slug)
        if task_issues:
            print(f"Task `{task_slug}` has required files but is not ready yet:")
            for issue in task_issues:
                print(f"- {issue}")
            return 1
        print(f"Task `{task_slug}` passed readiness checks.")
        return 0

    print("Repository passed readiness checks.")
    return 0


def run_doctor(repo_arg: str) -> int:
    repo = ensure_target_repo(repo_arg)
    for note in doctor_notes(repo):
        print(f"- {note}")
    return 0


def run_export(target: str, repo_arg: str, *, task_slug: str | None, force: bool, dry_run: bool) -> int:
    repo = ensure_target_repo(repo_arg)
    operations = export_plan(target, repo, task_slug=task_slug)
    effective, conflicts = preflight_write(operations, force=force)
    if conflicts:
        if dry_run:
            _print_write_preview(effective, conflicts)
        for conflict in conflicts:
            print(f"Refusing to overwrite existing file: {conflict}")
        print("No files were exported. Re-run with --force to overwrite.")
        return 1

    if dry_run:
        _print_write_preview(effective, conflicts)
        print("Dry run only. No files were written.")
        return 0

    written = apply_write_plan(effective)
    for path in written:
        print(f"exported {path}")
    return 0


def _print_copy_preview(effective: Sequence[object], skipped: Sequence[object], conflicts: Sequence[object], *, action: str) -> None:
    if not effective and not skipped and not conflicts:
        print("No file changes planned.")
        return
    for operation in effective:
        print(f"would {action} {operation.destination}")
    for path in skipped:
        print(f"would skip existing file: {path}")
    for path in conflicts:
        print(f"would refuse to overwrite existing file: {path}")


def _print_write_preview(effective: Sequence[object], conflicts: Sequence[object]) -> None:
    if not effective and not conflicts:
        print("No file changes planned.")
        return
    for operation in effective:
        print(f"would export {operation.destination}")
    for path in conflicts:
        print(f"would refuse to overwrite existing file: {path}")
