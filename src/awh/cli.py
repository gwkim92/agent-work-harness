from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from .core import (
    HarnessError,
    apply_copy_plan,
    doctor_notes,
    ensure_target_repo,
    preflight_copy,
    repo_plan,
    task_plan,
    verify_repo,
    verify_task,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="awh", description="Agent Work Harness CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Install repo-level harness files.")
    init_parser.add_argument("--profile", choices=("minimal", "default"), default="default")
    init_parser.add_argument("--repo", default=".")
    init_parser.add_argument("--force", action="store_true")

    task_parser = subparsers.add_parser("task", help="Manage task-level artifacts.")
    task_subparsers = task_parser.add_subparsers(dest="task_command", required=True)

    task_new = task_subparsers.add_parser("new", help="Create a new task directory.")
    _add_task_common_arguments(task_new, include_only_missing=False)

    task_augment = task_subparsers.add_parser("augment", help="Add missing files to an existing task.")
    _add_task_common_arguments(task_augment, include_only_missing=True)

    verify_parser = subparsers.add_parser("verify", help="Check harness file health.")
    verify_parser.add_argument("--repo", default=".")
    verify_parser.add_argument("--task")

    doctor_parser = subparsers.add_parser("doctor", help="Suggest the next harness step.")
    doctor_parser.add_argument("--repo", default=".")

    return parser


def _add_task_common_arguments(parser: argparse.ArgumentParser, *, include_only_missing: bool) -> None:
    parser.add_argument("slug")
    parser.add_argument("--profile", choices=("general", "web", "backend", "research", "dependency"), default="general")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--plan", action="store_true")
    parser.add_argument("--review", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--roles", action="store_true")
    parser.add_argument("--topology", action="store_true")
    parser.add_argument("--loop-contract", action="store_true", dest="loop_contract")
    parser.add_argument("--force", action="store_true")
    if include_only_missing:
        parser.add_argument("--only-missing", action="store_true", default=True)


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "init":
            return run_init(args.profile, args.repo, force=args.force)
        if args.command == "task":
            if args.task_command == "new":
                return run_task_write(
                    slug=args.slug,
                    profile=args.profile,
                    repo=args.repo,
                    extra_options=_task_options_from_args(args),
                    force=args.force,
                    only_missing=False,
                )
            if args.task_command == "augment":
                return run_task_write(
                    slug=args.slug,
                    profile=args.profile,
                    repo=args.repo,
                    extra_options=_task_options_from_args(args),
                    force=args.force,
                    only_missing=True,
                )
        if args.command == "verify":
            return run_verify(args.repo, task_slug=args.task)
        if args.command == "doctor":
            return run_doctor(args.repo)
    except HarnessError as exc:
        print(exc)
        return 1

    parser.error("Unknown command")
    return 2


def _task_options_from_args(args: argparse.Namespace) -> set[str]:
    options = set()
    if args.plan:
        options.add("plan")
    if args.review:
        options.add("review")
    if args.qa:
        options.add("qa")
    if args.roles:
        options.add("roles")
    if args.topology:
        options.add("topology")
    if args.loop_contract:
        options.add("loop_contract")
    return options


def run_init(profile: str, repo_arg: str, *, force: bool) -> int:
    repo = ensure_target_repo(repo_arg)
    effective, skipped, conflicts = preflight_copy(repo_plan(profile, repo), force=force)
    if conflicts:
        for conflict in conflicts:
            print(f"Refusing to overwrite existing file: {conflict}")
        print("No files were copied. Re-run with --force to overwrite.")
        return 1

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
) -> int:
    target_repo = ensure_target_repo(repo)
    operations = task_plan(profile, target_repo, slug, extra_options=extra_options)
    effective, skipped, conflicts = preflight_copy(operations, force=force, only_missing=only_missing)
    if conflicts:
        for conflict in conflicts:
            print(f"Refusing to overwrite existing file: {conflict}")
        print("No files were copied. Re-run with --force to overwrite.")
        return 1

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

    if task_slug:
        missing_task = verify_task(repo, task_slug)
        if missing_task:
            print(f"Task `{task_slug}` is missing required files:")
            for path in missing_task:
                print(f"- {path}")
            return 1
        print(f"Task `{task_slug}` passed required file checks.")
        return 0

    print("Repository passed required file checks.")
    return 0


def run_doctor(repo_arg: str) -> int:
    repo = ensure_target_repo(repo_arg)
    for note in doctor_notes(repo):
        print(f"- {note}")
    return 0

