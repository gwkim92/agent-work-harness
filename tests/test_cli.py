from __future__ import annotations

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
            self.assertIn("Repository passed required file checks", verify_repo.stdout)

            verify_task = self.run_cli("verify", "--repo", str(repo), "--task", "bootstrap-api")
            self.assertEqual(verify_task.returncode, 0)
            self.assertIn("passed required file checks", verify_task.stdout)

            doctor_after = self.run_cli("doctor", "--repo", str(repo))
            self.assertEqual(doctor_after.returncode, 0)
            self.assertIn("no evaluator artifacts", doctor_after.stdout)

    def test_export_commands_generate_expected_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            self.assertEqual(self.run_cli("init", "--repo", str(repo)).returncode, 0)
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

            claude_repo = self.run_cli("export", "claude", "--repo", str(repo))
            self.assertEqual(claude_repo.returncode, 0, claude_repo.stdout + claude_repo.stderr)
            self.assertTrue((repo / "CLAUDE.md").exists())

            claude_task = self.run_cli("export", "claude", "--repo", str(repo), "--task", "bootstrap-api")
            self.assertEqual(claude_task.returncode, 0, claude_task.stdout + claude_task.stderr)
            coordinator = repo / ".claude" / "agents" / "bootstrap-api-coordinator.md"
            reviewer = repo / ".claude" / "agents" / "bootstrap-api-reviewer.md"
            self.assertTrue(coordinator.exists())
            self.assertTrue(reviewer.exists())
            self.assertIn("name: bootstrap-api-coordinator", coordinator.read_text(encoding="utf-8"))
            self.assertIn("tools: Read, Grep, Glob, Bash", coordinator.read_text(encoding="utf-8"))
            self.assertIn("name: bootstrap-api-reviewer", reviewer.read_text(encoding="utf-8"))

            codex_task = self.run_cli("export", "codex", "--repo", str(repo), "--task", "bootstrap-api")
            self.assertEqual(codex_task.returncode, 0, codex_task.stdout + codex_task.stderr)
            codex_packet = repo / "docs" / "exports" / "codex" / "bootstrap-api.md"
            self.assertTrue(codex_packet.exists())
            self.assertIn("## Task Summary", codex_packet.read_text(encoding="utf-8"))

            copilot_repo = self.run_cli("export", "copilot", "--repo", str(repo))
            self.assertEqual(copilot_repo.returncode, 0, copilot_repo.stdout + copilot_repo.stderr)
            self.assertTrue((repo / ".github" / "copilot-instructions.md").exists())

            copilot_task = self.run_cli("export", "copilot", "--repo", str(repo), "--task", "bootstrap-api")
            self.assertEqual(copilot_task.returncode, 0, copilot_task.stdout + copilot_task.stderr)
            copilot_task_file = repo / ".github" / "instructions" / "bootstrap-api.instructions.md"
            self.assertTrue(copilot_task_file.exists())
            self.assertIn('applyTo: "**"', copilot_task_file.read_text(encoding="utf-8"))

            generic_task = self.run_cli("export", "generic-json", "--repo", str(repo), "--task", "bootstrap-api")
            self.assertEqual(generic_task.returncode, 0, generic_task.stdout + generic_task.stderr)
            self.assertTrue((repo / "docs" / "exports" / "generic" / "bootstrap-api.json").exists())
