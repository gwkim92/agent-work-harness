from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]


class AwhCliTests(unittest.TestCase):
    def run_cli(self, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(REPO_ROOT / "src")
        return subprocess.run(
            [sys.executable, "-m", "awh", *args],
            cwd=cwd or REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

    def fill_repo_harness(self, repo: Path) -> None:
        (repo / "AGENTS.md").write_text(
            "\n".join(
                [
                    "# Repository Working Map",
                    "",
                    "## Purpose",
                    "",
                    "이 저장소의 목적은 `Agent Work Harness`를 개발, 유지보수, 검증하는 것이다.",
                    "",
                    "에이전트는 아래를 우선한다.",
                    "",
                    "- 낙관보다 정확성",
                    "- 큰 수정보다 작고 검토 가능한 변경",
                    "- 완료 주장보다 검증 증거",
                    "",
                    "## Repository Map",
                    "",
                    "- 앱 코드: `src/awh/**`",
                    "- 테스트: `tests/**`",
                    "- 문서와 설계 노트: `docs/**`, `guides/**`",
                    "- 스크립트와 툴링: `scripts/**`",
                    "- 민감하거나 고위험인 경로: `pyproject.toml`",
                    "",
                    "## Core Commands",
                    "",
                    "- 설치: `python3 -m pip install -e .`",
                    "- 개발 서버 또는 실행: `PYTHONPATH=src python3 -m awh --help`",
                    "- 테스트: `PYTHONPATH=src python3 -m unittest discover -s tests -v`",
                    "- 린트: `python3 -m compileall src tests`",
                    "- 타입체크 또는 빌드: `python3 -m compileall src tests`",
                    "- E2E 또는 스모크: `PYTHONPATH=src python3 -m awh init --dry-run --repo .`",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        (repo / "docs" / "verification-plan.md").write_text(
            "\n".join(
                [
                    "# Verification Plan",
                    "",
                    "## Scope",
                    "",
                    "- 대상 기능군 또는 시스템: CLI install, verify, export flows",
                    "",
                    "## Automated Checks",
                    "",
                    "- 명령: `PYTHONPATH=src python3 -m unittest discover -s tests -v`",
                    "- 무엇을 증명하는가: CLI behavior stays correct",
                    "- 통과 조건: all tests pass",
                    "",
                    "## Manual Checks",
                    "",
                    "- 시나리오: run `awh init --dry-run` in a temp repo",
                    "- 기대 동작: planned writes are shown and no files are created",
                    "",
                    "## Browser Or Runtime Checks",
                    "",
                    "- URL, route, job, endpoint: `awh verify`",
                    "- 수행 경로: run after filling required repo files",
                    "- 확인할 증거: command exits with code 0",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

    def fill_strict_repo_harness(self, repo: Path) -> None:
        (repo / "docs" / "verification-plan.md").write_text(
            "\n".join(
                [
                    "# Verification Plan",
                    "",
                    "## Scope",
                    "",
                    "- 대상 기능군 또는 시스템: CLI install, verify, export flows",
                    "",
                    "## Automated Checks",
                    "",
                    "- 명령: `PYTHONPATH=src python3 -m unittest discover -s tests -v`",
                    "- 무엇을 증명하는가: CLI behavior stays correct",
                    "- 통과 조건: all tests pass",
                    "",
                    "## Manual Checks",
                    "",
                    "- 시나리오: run `awh init --dry-run` in a temp repo",
                    "- 기대 동작: planned writes are shown and no files are created",
                    "",
                    "## Browser Or Runtime Checks",
                    "",
                    "- URL, route, job, endpoint: `awh verify`",
                    "- 수행 경로: run after filling required repo files",
                    "- 확인할 증거: command exits with code 0",
                    "",
                    "## Regression Guard",
                    "",
                    "- 유지되어야 하는 기존 동작: `awh init` stays atomic on collisions",
                    "- 그것을 지키는 체크: `test_init_is_atomic_when_collision_exists`",
                    "",
                    "## Rollback",
                    "",
                    "- 실패 시 끄거나 되돌리는 방법: revert the CLI/core patch and rerun unit tests",
                    "",
                    "## Human Confirmation",
                    "",
                    "- 여전히 사람이 판단해야 하는 항목: exported task packets stay readable",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

    def fill_task_harness(self, repo: Path, slug: str) -> None:
        task_dir = repo / "docs" / "tasks" / slug
        (task_dir / "contract.md").write_text(
            "\n".join(
                [
                    "# Task Contract",
                    "",
                    "## Task",
                    "",
                    f"- 이름: {slug}",
                    "- 요청: tighten CLI verification behavior",
                    "- 담당: tests",
                    "- 날짜: 2026-04-05",
                    "",
                    "## Goal",
                    "",
                    "- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: readiness checks fail on blank scaffolds and pass on filled docs",
                    "",
                    "## Scope",
                    "",
                    "- 포함: `src/awh/**`, `tests/**`",
                    "- 제외: `templates/**` outside the tested task files",
                    "",
                    "## Mutable Surface",
                    "",
                    "- 수정 가능한 파일: `src/awh/**`, `tests/**`",
                    "- 수정 금지 파일: `README.md`",
                    "- 검증에 사용할 명령: `PYTHONPATH=src python3 -m unittest discover -s tests -v`",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        (task_dir / "handoff.md").write_text(
            "\n".join(
                [
                    "# Session Handoff",
                    "",
                    "## Current Status",
                    "",
                    "- 완료: repo-level setup captured",
                    "- 진행 중: task-level verification updates",
                    "- 막힌 점: none",
                    "",
                    "## Exact Next Step",
                    "",
                    "- 다음 세션은 이것부터 시작: rerun verification and continue implementation",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

    def fill_long_running_harness(self, repo: Path, slug: str) -> None:
        task_dir = repo / "docs" / "tasks" / slug
        (task_dir / "feature_list.json").write_text(
            json.dumps(
                {
                    "version": 1,
                    "task_slug": slug,
                    "features": [
                        {
                            "id": "feature-001",
                            "description": "Set up additive long-running support",
                            "status": "done",
                            "priority": "high",
                            "notes": "CLI and scaffolding are in place",
                            "evidence_refs": ["evidence-001"],
                        },
                        {
                            "id": "feature-002",
                            "description": "Export long-running state",
                            "status": "in_progress",
                            "priority": "medium",
                            "notes": "Codex export needs summary data",
                            "evidence_refs": [],
                        },
                        {
                            "id": "feature-003",
                            "description": "Tighten shell fallback coverage",
                            "status": "todo",
                            "priority": "low",
                            "notes": "",
                            "evidence_refs": [],
                        },
                    ],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (task_dir / "progress.md").write_text(
            "\n".join(
                [
                    "# Long-Running Progress",
                    "",
                    "## Current Focus",
                    "",
                    "- focus: finish export summaries",
                    "",
                    "## Recent Sessions",
                    "",
                    "- 2026-04-05:",
                    "  - did: added long-running artifacts",
                    "  - evidence: draft tests",
                    "",
                    "## Exact Next Step",
                    "",
                    "- step: wire parsed feature counts into the Codex task packet",
                    "",
                    "## Open Risks",
                    "",
                    "- risk: malformed JSON could break exports",
                    "- mitigation: validate before export",
                    "",
                    "## Useful Commands",
                    "",
                    "- command: `PYTHONPATH=src python3 -m unittest discover -s tests -v`",
                    "- why: confirm CLI behavior",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        (task_dir / "evidence").mkdir(parents=True, exist_ok=True)
        (task_dir / "evidence" / "manifest.json").write_text(
            json.dumps(
                {
                    "version": 1,
                    "artifacts": [
                        {
                            "id": "evidence-001",
                            "kind": "automated",
                            "location": "tests/test_cli.py",
                            "summary": "Unit test coverage for long-running support",
                            "status": "collected",
                        }
                    ],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    def fill_strict_task_evidence(self, repo: Path, slug: str) -> None:
        task_dir = repo / "docs" / "tasks" / slug
        (task_dir / "review.md").write_text(
            "\n".join(
                [
                    "# Review Notes",
                    "",
                    "## Review Scope",
                    "",
                    f"- 대상 task: {slug}",
                    "- 검토 대상 파일: `src/awh/core.py`, `tests/test_cli.py`",
                    "- 검토 기준: strict verification signals are evidence-backed",
                    "",
                    "## Claimed Outcome",
                    "",
                    "- generator가 주장하는 완료 내용: strict verify rejects weak evaluation records",
                    "",
                    "## Evidence Checked",
                    "",
                    "- 읽은 파일: `src/awh/core.py`, `tests/test_cli.py`",
                    "- 실행한 명령: `PYTHONPATH=src python3 -m unittest discover -s tests -v`",
                    "- 확인한 로그 또는 산출물: `docs/exports/generic/strict-task.json`",
                    "",
                    "## Findings",
                    "",
                    "- Finding: none",
                    "- Impact: low",
                    "- Evidence: review checks passed",
                    "- Suggested fix: none",
                    "",
                    "## Residual Risks",
                    "",
                    "- 아직 남아 있는 위험: export wording may still need product review",
                    "",
                    "## Open Questions",
                    "",
                    "- 질문: none",
                    "",
                    "## Verdict",
                    "",
                    "- pass with risks",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        (task_dir / "qa.md").write_text(
            "\n".join(
                [
                    "# QA Notes",
                    "",
                    "## QA Scope",
                    "",
                    f"- 대상 task: {slug}",
                    "- 환경: local test repo",
                    "- URL, route, endpoint, job: `awh verify --task strict-task --strict`",
                    "",
                    "## Scenarios",
                    "",
                    "### Scenario 1",
                    "",
                    "- 절차: run strict verification after filling review, QA, and evidence records",
                    "- 기대 결과: command exits with code 0",
                    "- 실제 결과: command passed",
                    "- 증거: terminal output captured in local test run",
                    "",
                    "## Regression Checks",
                    "",
                    "- 유지되어야 하는 기존 동작: normal `awh verify` still accepts non-strict-ready tasks",
                    "- 확인 결과: confirmed in unit tests",
                    "",
                    "## Issues Found",
                    "",
                    "- Issue: none",
                    "- Repro: n/a",
                    "- Severity: none",
                    "- Suggested next step: none",
                    "",
                    "## Verdict",
                    "",
                    "- pass",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        (task_dir / "evidence").mkdir(parents=True, exist_ok=True)
        (task_dir / "evidence" / "manifest.json").write_text(
            json.dumps(
                {
                    "version": 1,
                    "artifacts": [
                        {
                            "id": "evidence-101",
                            "kind": "automated",
                            "location": "tests/test_cli.py",
                            "summary": "Strict verification unit tests passed",
                            "status": "collected",
                        }
                    ],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    def test_init_default_installs_repo_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            result = self.run_cli("init", "--profile", "default", "--repo", str(repo))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue((repo / "AGENTS.md").exists())
            self.assertTrue((repo / "docs" / "verification-plan.md").exists())
            self.assertTrue((repo / "docs" / "escalation-rules.md").exists())
            self.assertIn("Next: fill", result.stdout)

    def test_init_is_atomic_when_collision_exists(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            docs_dir = repo / "docs"
            docs_dir.mkdir(parents=True)
            (docs_dir / "verification-plan.md").write_text("keep me\n", encoding="utf-8")

            result = self.run_cli("init", "--profile", "default", "--repo", str(repo))
            self.assertEqual(result.returncode, 1)
            self.assertFalse((repo / "AGENTS.md").exists())
            self.assertIn("No files were copied", result.stdout)

    def test_task_new_and_augment_create_expected_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            self.assertEqual(self.run_cli("init", "--repo", str(repo)).returncode, 0)

            created = self.run_cli(
                "task",
                "new",
                "bootstrap-api",
                "--repo",
                str(repo),
                "--profile",
                "backend",
                "--plan",
            )
            self.assertEqual(created.returncode, 0, created.stdout + created.stderr)
            task_dir = repo / "docs" / "tasks" / "bootstrap-api"
            self.assertTrue((task_dir / "contract.md").exists())
            self.assertTrue((task_dir / "handoff.md").exists())
            self.assertTrue((task_dir / "review.md").exists())
            self.assertTrue((task_dir / "plan.md").exists())
            self.assertFalse((task_dir / "qa.md").exists())

            augmented = self.run_cli(
                "task",
                "augment",
                "bootstrap-api",
                "--repo",
                str(repo),
                "--profile",
                "backend",
                "--qa",
            )
            self.assertEqual(augmented.returncode, 0, augmented.stdout + augmented.stderr)
            self.assertTrue((task_dir / "qa.md").exists())
            self.assertIn("skipped existing file", augmented.stdout)

    def test_long_running_task_artifacts_and_permissions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            self.assertEqual(self.run_cli("init", "--repo", str(repo)).returncode, 0)

            created = self.run_cli(
                "task",
                "new",
                "long-runner",
                "--repo",
                str(repo),
                "--profile",
                "general",
                "--feature-list",
            )
            self.assertEqual(created.returncode, 0, created.stdout + created.stderr)
            task_dir = repo / "docs" / "tasks" / "long-runner"
            feature_list = task_dir / "feature_list.json"
            progress = task_dir / "progress.md"
            init_script = task_dir / "init.sh"
            evidence_manifest = task_dir / "evidence" / "manifest.json"
            self.assertTrue(feature_list.exists())
            self.assertFalse(progress.exists())
            self.assertFalse(init_script.exists())
            self.assertFalse(evidence_manifest.exists())

            feature_list.write_text('{"version":1,"task_slug":"long-runner","features":[]}\n', encoding="utf-8")
            augmented = self.run_cli(
                "task",
                "augment",
                "long-runner",
                "--repo",
                str(repo),
                "--profile",
                "general",
                "--long-running",
            )
            self.assertEqual(augmented.returncode, 0, augmented.stdout + augmented.stderr)
            self.assertEqual(feature_list.read_text(encoding="utf-8"), '{"version":1,"task_slug":"long-runner","features":[]}\n')
            self.assertTrue(progress.exists())
            self.assertTrue(init_script.exists())
            self.assertTrue(evidence_manifest.exists())
            self.assertTrue(os.access(init_script, os.X_OK))

    def test_verify_and_doctor_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)

            missing = self.run_cli("verify", "--repo", str(repo))
            self.assertEqual(missing.returncode, 1)
            self.assertIn("Repository is missing required harness files", missing.stdout)

            doctor_before = self.run_cli("doctor", "--repo", str(repo))
            self.assertEqual(doctor_before.returncode, 0)
            self.assertIn("Harness is not fully installed", doctor_before.stdout)

            self.assertEqual(self.run_cli("init", "--repo", str(repo)).returncode, 0)
            verify_unfilled_repo = self.run_cli("verify", "--repo", str(repo))
            self.assertEqual(verify_unfilled_repo.returncode, 1)
            self.assertIn("still need project-specific content", verify_unfilled_repo.stdout)

            doctor_unfilled_repo = self.run_cli("doctor", "--repo", str(repo))
            self.assertEqual(doctor_unfilled_repo.returncode, 0)
            self.assertIn("still need project-specific content", doctor_unfilled_repo.stdout)

            self.fill_repo_harness(repo)
            self.assertEqual(
                self.run_cli(
                    "task",
                    "new",
                    "bootstrap-api",
                    "--repo",
                    str(repo),
                    "--profile",
                    "general",
                ).returncode,
                0,
            )

            verify_repo = self.run_cli("verify", "--repo", str(repo))
            self.assertEqual(verify_repo.returncode, 0)
            self.assertIn("Repository passed readiness checks", verify_repo.stdout)

            verify_task = self.run_cli("verify", "--repo", str(repo), "--task", "bootstrap-api")
            self.assertEqual(verify_task.returncode, 1)
            self.assertIn("is not ready yet", verify_task.stdout)

            doctor_after_task_create = self.run_cli("doctor", "--repo", str(repo))
            self.assertEqual(doctor_after_task_create.returncode, 0)
            self.assertIn("not verification-ready yet", doctor_after_task_create.stdout)

            self.fill_task_harness(repo, "bootstrap-api")
            verify_task = self.run_cli("verify", "--repo", str(repo), "--task", "bootstrap-api")
            self.assertEqual(verify_task.returncode, 0)
            self.assertIn("passed readiness checks", verify_task.stdout)

            doctor_after = self.run_cli("doctor", "--repo", str(repo))
            self.assertEqual(doctor_after.returncode, 0)
            self.assertIn("no evaluator artifacts", doctor_after.stdout)

    def test_verify_rejects_invalid_long_running_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            self.assertEqual(self.run_cli("init", "--repo", str(repo)).returncode, 0)
            self.fill_repo_harness(repo)
            self.assertEqual(
                self.run_cli(
                    "task",
                    "new",
                    "broken",
                    "--repo",
                    str(repo),
                    "--profile",
                    "general",
                    "--long-running",
                ).returncode,
                0,
            )
            self.fill_task_harness(repo, "broken")

            (repo / "docs" / "tasks" / "broken" / "feature_list.json").write_text("{not-json}\n", encoding="utf-8")
            result = self.run_cli("verify", "--repo", str(repo), "--task", "broken")
            self.assertEqual(result.returncode, 1)
            self.assertIn("feature_list.json", result.stdout)
            self.assertIn("invalid JSON", result.stdout)

            self.fill_long_running_harness(repo, "broken")
            (repo / "docs" / "tasks" / "broken" / "evidence" / "manifest.json").write_text(
                json.dumps(
                    {
                        "version": 1,
                        "artifacts": [
                            {
                                "id": "evidence-001",
                                "kind": "unknown",
                                "location": "logs/output.txt",
                                "summary": "bad enum",
                                "status": "planned",
                            }
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            result = self.run_cli("verify", "--repo", str(repo), "--task", "broken")
            self.assertEqual(result.returncode, 1)
            self.assertIn("manifest.json", result.stdout)
            self.assertIn("invalid `kind`", result.stdout)

    def test_verify_strict_requires_repo_evaluation_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            self.assertEqual(self.run_cli("init", "--repo", str(repo)).returncode, 0)
            self.fill_repo_harness(repo)

            result = self.run_cli("verify", "--repo", str(repo), "--strict")
            self.assertEqual(result.returncode, 1)
            self.assertIn("Regression Guard", result.stdout)
            self.assertIn("Rollback", result.stdout)
            self.assertIn("Human Confirmation", result.stdout)

            self.fill_strict_repo_harness(repo)
            result = self.run_cli("verify", "--repo", str(repo), "--strict")
            self.assertEqual(result.returncode, 0)
            self.assertIn("passed strict readiness checks", result.stdout)

    def test_verify_strict_requires_task_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            self.assertEqual(self.run_cli("init", "--repo", str(repo)).returncode, 0)
            self.fill_repo_harness(repo)
            self.fill_strict_repo_harness(repo)
            self.assertEqual(
                self.run_cli(
                    "task",
                    "new",
                    "strict-task",
                    "--repo",
                    str(repo),
                    "--profile",
                    "general",
                ).returncode,
                0,
            )
            self.fill_task_harness(repo, "strict-task")

            result = self.run_cli("verify", "--repo", str(repo), "--task", "strict-task", "--strict")
            self.assertEqual(result.returncode, 1)
            self.assertIn("review.md", result.stdout)
            self.assertIn("qa.md", result.stdout)
            self.assertIn("evidence/manifest.json", result.stdout)

            self.assertEqual(
                self.run_cli(
                    "task",
                    "augment",
                    "strict-task",
                    "--repo",
                    str(repo),
                    "--profile",
                    "general",
                    "--review",
                    "--qa",
                    "--evidence-manifest",
                ).returncode,
                0,
            )
            self.fill_strict_task_evidence(repo, "strict-task")

            result = self.run_cli("verify", "--repo", str(repo), "--task", "strict-task", "--strict")
            self.assertEqual(result.returncode, 0)
            self.assertIn("passed strict readiness checks", result.stdout)

    def test_doctor_recommends_long_running_for_plan_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            self.assertEqual(self.run_cli("init", "--repo", str(repo)).returncode, 0)
            self.fill_repo_harness(repo)
            self.assertEqual(
                self.run_cli(
                    "task",
                    "new",
                    "planner-task",
                    "--repo",
                    str(repo),
                    "--profile",
                    "backend",
                    "--plan",
                ).returncode,
                0,
            )
            self.fill_task_harness(repo, "planner-task")

            doctor = self.run_cli("doctor", "--repo", str(repo))
            self.assertEqual(doctor.returncode, 0)
            self.assertIn("awh task augment planner-task --long-running", doctor.stdout)

    def test_doctor_points_to_long_running_repairs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            self.assertEqual(self.run_cli("init", "--repo", str(repo)).returncode, 0)
            self.fill_repo_harness(repo)
            self.assertEqual(
                self.run_cli(
                    "task",
                    "new",
                    "repair-me",
                    "--repo",
                    str(repo),
                    "--profile",
                    "general",
                    "--long-running",
                ).returncode,
                0,
            )
            self.fill_task_harness(repo, "repair-me")
            (repo / "docs" / "tasks" / "repair-me" / "feature_list.json").write_text("{bad-json}\n", encoding="utf-8")

            doctor = self.run_cli("doctor", "--repo", str(repo))
            self.assertEqual(doctor.returncode, 0)
            self.assertIn("feature_list.json", doctor.stdout)
            self.assertIn("repair the long-running task state files", doctor.stdout)

    def test_export_commands_generate_expected_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            self.assertEqual(self.run_cli("init", "--repo", str(repo)).returncode, 0)
            self.fill_repo_harness(repo)
            self.assertEqual(
                self.run_cli(
                    "task",
                    "new",
                    "bootstrap-api",
                    "--repo",
                    str(repo),
                    "--profile",
                    "backend",
                    "--plan",
                    "--roles",
                    "--topology",
                    "--qa",
                ).returncode,
                0,
            )
            self.fill_task_harness(repo, "bootstrap-api")

            claude_repo = self.run_cli("export", "claude", "--repo", str(repo))
            self.assertEqual(claude_repo.returncode, 0, claude_repo.stdout + claude_repo.stderr)
            self.assertTrue((repo / "CLAUDE.md").exists())

            claude_task = self.run_cli("export", "claude", "--repo", str(repo), "--task", "bootstrap-api")
            self.assertEqual(claude_task.returncode, 0, claude_task.stdout + claude_task.stderr)
            coordinator = repo / ".claude" / "agents" / "bootstrap-api-coordinator.md"
            reviewer = repo / ".claude" / "agents" / "bootstrap-api-reviewer.md"
            self.assertTrue(coordinator.exists())
            self.assertTrue(reviewer.exists())
            self.assertEqual(
                sorted(path.name for path in (repo / ".claude" / "agents").glob("*.md")),
                ["bootstrap-api-coordinator.md", "bootstrap-api-reviewer.md"],
            )
            coordinator_text = coordinator.read_text(encoding="utf-8")
            reviewer_text = reviewer.read_text(encoding="utf-8")
            self.assertIn("name: bootstrap-api-coordinator", coordinator_text)
            self.assertIn("tools: Read, Grep, Glob, Bash", coordinator_text)
            self.assertIn("Current briefing", coordinator_text)
            self.assertIn("Verification path", coordinator_text)
            self.assertIn("name: bootstrap-api-reviewer", reviewer_text)
            self.assertIn("Current verification context", reviewer_text)

            codex_task = self.run_cli("export", "codex", "--repo", str(repo), "--task", "bootstrap-api")
            self.assertEqual(codex_task.returncode, 0, codex_task.stdout + codex_task.stderr)
            codex_packet = repo / "docs" / "exports" / "codex" / "bootstrap-api.md"
            self.assertTrue(codex_packet.exists())
            codex_text = codex_packet.read_text(encoding="utf-8")
            self.assertIn("## Task Summary", codex_text)
            self.assertIn("## Current State", codex_text)
            self.assertIn("## Verification And Evidence", codex_text)
            self.assertIn("## Canonical References", codex_text)
            self.assertNotIn("# Task Contract", codex_text)

            copilot_repo = self.run_cli("export", "copilot", "--repo", str(repo))
            self.assertEqual(copilot_repo.returncode, 0, copilot_repo.stdout + copilot_repo.stderr)
            self.assertTrue((repo / ".github" / "copilot-instructions.md").exists())

            copilot_task = self.run_cli("export", "copilot", "--repo", str(repo), "--task", "bootstrap-api")
            self.assertEqual(copilot_task.returncode, 0, copilot_task.stdout + copilot_task.stderr)
            copilot_task_file = repo / ".github" / "instructions" / "bootstrap-api.instructions.md"
            self.assertTrue(copilot_task_file.exists())
            copilot_text = copilot_task_file.read_text(encoding="utf-8")
            self.assertIn('applyTo: "src/awh/**,tests/**"', copilot_text)
            self.assertIn("Current focus", copilot_text)
            self.assertIn("Next step", copilot_text)

            generic_task = self.run_cli("export", "generic-json", "--repo", str(repo), "--task", "bootstrap-api")
            self.assertEqual(generic_task.returncode, 0, generic_task.stdout + generic_task.stderr)
            generic_payload = json.loads(
                (repo / "docs" / "exports" / "generic" / "bootstrap-api.json").read_text(encoding="utf-8")
            )
            self.assertIn("briefing", generic_payload)
            self.assertEqual(generic_payload["briefing"]["next_step"], "rerun verification and continue implementation")

    def test_long_running_exports_include_structured_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            self.assertEqual(self.run_cli("init", "--repo", str(repo)).returncode, 0)
            self.fill_repo_harness(repo)
            self.assertEqual(
                self.run_cli(
                    "task",
                    "new",
                    "long-export",
                    "--repo",
                    str(repo),
                    "--profile",
                    "backend",
                    "--plan",
                    "--long-running",
                ).returncode,
                0,
            )
            self.fill_task_harness(repo, "long-export")
            self.fill_long_running_harness(repo, "long-export")

            codex_task = self.run_cli("export", "codex", "--repo", str(repo), "--task", "long-export")
            self.assertEqual(codex_task.returncode, 0, codex_task.stdout + codex_task.stderr)
            codex_text = (repo / "docs" / "exports" / "codex" / "long-export.md").read_text(encoding="utf-8")
            self.assertIn("## Current State", codex_text)
            self.assertIn("## Verification And Evidence", codex_text)
            self.assertIn("## Long-Running State", codex_text)
            self.assertIn("## Canonical References", codex_text)
            self.assertIn("docs/tasks/long-export/feature_list.json", codex_text)
            self.assertIn("feature counts:", codex_text)
            self.assertIn("current focus:", codex_text)
            self.assertIn("progress next step: wire parsed feature counts into the Codex task packet", codex_text)
            self.assertNotIn("# Task Contract", codex_text)
            self.assertNotIn("# Session Handoff", codex_text)

            claude_task = self.run_cli("export", "claude", "--repo", str(repo), "--task", "long-export")
            self.assertEqual(claude_task.returncode, 0, claude_task.stdout + claude_task.stderr)
            claude_text = (repo / ".claude" / "agents" / "long-export-coordinator.md").read_text(encoding="utf-8")
            self.assertIn("Current briefing", claude_text)
            self.assertIn("Verification path", claude_text)
            self.assertIn("docs/tasks/long-export/feature_list.json", claude_text)
            self.assertIn("docs/tasks/long-export/progress.md", claude_text)
            self.assertNotIn("Plan:\n\n# Task Plan", claude_text)

            reviewer_text = (repo / ".claude" / "agents" / "long-export-reviewer.md").read_text(encoding="utf-8")
            self.assertIn("Current verification context", reviewer_text)
            self.assertIn("docs/tasks/long-export/evidence/manifest.json", reviewer_text)

            copilot_task = self.run_cli("export", "copilot", "--repo", str(repo), "--task", "long-export")
            self.assertEqual(copilot_task.returncode, 0, copilot_task.stdout + copilot_task.stderr)
            copilot_text = (repo / ".github" / "instructions" / "long-export.instructions.md").read_text(encoding="utf-8")
            self.assertIn("Current focus", copilot_text)
            self.assertIn("Next step", copilot_text)
            self.assertIn("docs/tasks/long-export/progress.md", copilot_text)
            self.assertIn("docs/tasks/long-export/evidence/manifest.json", copilot_text)

            generic_task = self.run_cli("export", "generic-json", "--repo", str(repo), "--task", "long-export")
            self.assertEqual(generic_task.returncode, 0, generic_task.stdout + generic_task.stderr)
            generic_payload = json.loads(
                (repo / "docs" / "exports" / "generic" / "long-export.json").read_text(encoding="utf-8")
            )
            self.assertIn("structured", generic_payload)
            self.assertIn("briefing", generic_payload)
            self.assertEqual(generic_payload["structured"]["feature_list"]["task_slug"], "long-export")
            self.assertEqual(generic_payload["structured"]["evidence_manifest"]["artifacts"][0]["id"], "evidence-001")
            self.assertEqual(generic_payload["briefing"]["current_focus"], "finish export summaries")
            self.assertEqual(
                generic_payload["briefing"]["progress_next_step"],
                "wire parsed feature counts into the Codex task packet",
            )

    def test_export_parses_multiline_contract_and_role_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            self.assertEqual(self.run_cli("init", "--repo", str(repo)).returncode, 0)
            self.fill_repo_harness(repo)
            self.assertEqual(
                self.run_cli(
                    "task",
                    "new",
                    "demo",
                    "--repo",
                    str(repo),
                    "--profile",
                    "general",
                    "--roles",
                ).returncode,
                0,
            )
            self.fill_task_harness(repo, "demo")

            (repo / "docs" / "tasks" / "demo" / "contract.md").write_text(
                "\n".join(
                    [
                        "# Task Contract",
                        "",
                        "## Task",
                        "",
                        "- 이름: demo",
                        "- 요청: parse multiline fields",
                        "",
                        "## Goal",
                        "",
                        "- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: multiline parsing remains stable",
                        "",
                        "## Mutable Surface",
                        "",
                        "- 수정 가능한 파일:",
                        "  - src/api/**",
                        "  - tests/api/**",
                        "- 수정 금지 파일:",
                        "  - docs/**",
                        "- 검증에 사용할 명령: `PYTHONPATH=src python3 -m unittest discover -s tests -v`",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            (repo / "docs" / "tasks" / "demo" / "roles.md").write_text(
                "\n".join(
                    [
                        "# Multi-Agent Roles",
                        "",
                        "## Role 1",
                        "",
                        "- 이름: Planner",
                        "- 타입: planner",
                        "- 책임:",
                        "  - define execution order",
                        "  - keep scope aligned",
                        "- 성공 조건:",
                        "  - plan exists",
                        "  - handoff is clear",
                        "- handoff 대상: Generator",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            claude_task = self.run_cli("export", "claude", "--repo", str(repo), "--task", "demo")
            self.assertEqual(claude_task.returncode, 0, claude_task.stdout + claude_task.stderr)
            planner = repo / ".claude" / "agents" / "demo-planner.md"
            self.assertTrue(planner.exists())
            planner_text = planner.read_text(encoding="utf-8")
            self.assertIn("Responsibility: define execution order; keep scope aligned", planner_text)
            self.assertIn("Success condition: plan exists; handoff is clear", planner_text)

            copilot_task = self.run_cli("export", "copilot", "--repo", str(repo), "--task", "demo")
            self.assertEqual(copilot_task.returncode, 0, copilot_task.stdout + copilot_task.stderr)
            copilot_text = (repo / ".github" / "instructions" / "demo.instructions.md").read_text(encoding="utf-8")
            self.assertIn('applyTo: "src/api/**,tests/api/**"', copilot_text)

    def test_generic_json_export_requires_existing_task(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            self.assertEqual(self.run_cli("init", "--repo", str(repo)).returncode, 0)
            self.fill_repo_harness(repo)

            result = self.run_cli("export", "generic-json", "--repo", str(repo), "--task", "missing-task")
            self.assertEqual(result.returncode, 1)
            self.assertIn("Task `missing-task` is not ready for export", result.stdout)
            self.assertFalse((repo / "docs" / "exports" / "generic" / "missing-task.json").exists())

    def test_dry_run_and_help_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)

            init_dry_run = self.run_cli("init", "--repo", str(repo), "--dry-run")
            self.assertEqual(init_dry_run.returncode, 0, init_dry_run.stdout + init_dry_run.stderr)
            self.assertIn("would install", init_dry_run.stdout)
            self.assertIn("Dry run only", init_dry_run.stdout)
            self.assertFalse((repo / "AGENTS.md").exists())

            self.assertEqual(self.run_cli("init", "--repo", str(repo)).returncode, 0)
            self.fill_repo_harness(repo)
            self.assertEqual(
                self.run_cli("task", "new", "demo", "--repo", str(repo), "--dry-run").returncode,
                0,
            )
            self.assertFalse((repo / "docs" / "tasks" / "demo").exists())

            help_result = self.run_cli("task", "augment", "--help")
            self.assertEqual(help_result.returncode, 0)
            self.assertIn("--dry-run", help_result.stdout)
            self.assertIn("--long-running", help_result.stdout)
            self.assertIn("--feature-list", help_result.stdout)
            self.assertIn("--evidence-manifest", help_result.stdout)
            self.assertNotIn("--only-missing", help_result.stdout)

            new_help = self.run_cli("task", "new", "--help")
            self.assertEqual(new_help.returncode, 0)
            self.assertIn("--long-running", new_help.stdout)
            self.assertIn("--init-script", new_help.stdout)

            verify_help = self.run_cli("verify", "--help")
            self.assertEqual(verify_help.returncode, 0)
            self.assertIn("--strict", verify_help.stdout)

    def test_shell_new_task_supports_long_running(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            result = subprocess.run(
                [str(REPO_ROOT / "scripts" / "new-task.sh"), "backend", str(repo), "shell-task", "--with-long-running"],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            task_dir = repo / "docs" / "tasks" / "shell-task"
            self.assertTrue((task_dir / "feature_list.json").exists())
            self.assertTrue((task_dir / "progress.md").exists())
            self.assertTrue((task_dir / "init.sh").exists())
            self.assertTrue((task_dir / "evidence" / "manifest.json").exists())
            self.assertTrue(os.access(task_dir / "init.sh", os.X_OK))
