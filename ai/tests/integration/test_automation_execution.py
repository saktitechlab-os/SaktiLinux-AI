"""Real-world integration tests for Phase 5 AI Automation.

These tests drive the REAL AutomationEngine end-to-end: planning a
natural-language task, ensuring tools, executing subprocesses, and
recording into the dev history. Nothing is mocked; side effects are
confined to throwaway temp projects/repos.

Safety: no package installs happen here — tasks chosen only touch
Python main.py runs and real git commits inside temp repos.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from ai.automation import AutomationEngine
from ai.dev import DevHistory

REAL_GIT = shutil.which("git") is not None


def _write(dirpath, name, content):
    with open(os.path.join(dirpath, name), "w", encoding="utf-8") as fh:
        fh.write(content)


def _python_project(dirpath):
    _write(dirpath, "main.py", "print('real-automation-ok')\n")
    _write(dirpath, "pyproject.toml", '[project]\nname = "auto-demo"\n')
    open(os.path.join(dirpath, "requirements.txt"), "w").close()


class BaseAutomationCase(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="sakti_auto_")
        self.data = tempfile.mkdtemp(prefix="sakti_auto_data_")
        self._old_xdg = os.environ.get("XDG_DATA_HOME")
        os.environ["XDG_DATA_HOME"] = self.data

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)
        shutil.rmtree(self.data, ignore_errors=True)
        if self._old_xdg is None:
            os.environ.pop("XDG_DATA_HOME", None)
        else:
            os.environ["XDG_DATA_HOME"] = self._old_xdg

    def engine(self):
        return AutomationEngine(history=DevHistory(), log=lambda m: None)


class TestAutomationRealRun(BaseAutomationCase):
    """The engine executes real steps in a temp project."""

    def test_run_project_step_is_real(self):
        _python_project(self.dir)
        report = self.engine().run("run the project", cwd=self.dir)
        self.assertTrue(report.success, report.to_dict())
        self.assertIn("real-automation-ok",
                      report.results[0][1].stdout)

    def test_plan_error_does_not_touch_disk(self):
        report = self.engine().run("synchronize whale migration data")
        self.assertFalse(report.success)
        self.assertIsNotNone(report.plan_error)
        self.assertEqual(os.listdir(self.dir), [])

    def test_dry_run_executes_nothing(self):
        _python_project(self.dir)
        report = self.engine().run("run the project", dry_run=True,
                                   cwd=self.dir)
        self.assertTrue(report.success)
        self.assertEqual(report.results, [])
        self.assertEqual(len(os.listdir(self.dir)), 3)  # unchanged

    def test_history_records_real_automation_step(self):
        _python_project(self.dir)
        engine = self.engine()
        report = engine.run("run the project", cwd=self.dir)
        self.assertTrue(report.success)
        entries = DevHistory().list(action="automation")
        self.assertTrue(any("automation" in e.get("action", "")
                            for e in entries))
        self.assertTrue(any("dev run" in (e.get("command") or "")
                            for e in entries))


@unittest.skipUnless(REPLY_GIT := shutil.which("git") is not None,
                     "git not available on this host")
class TestRealGitCommit(BaseAutomationCase):
    """`do "commit ..."` performs a real git commit."""

    def test_commit_changes_end_to_end(self):
        subprocess.run(["git", "init", "-q"], cwd=self.dir, check=True)
        subprocess.run(["git", "config", "user.email", "t@t"],
                       cwd=self.dir, check=True)
        subprocess.run(["git", "config", "user.name", "T"],
                       cwd=self.dir, check=True)
        _write(self.dir, "code.txt", "hello\n")
        report = self.engine().run(
            "commit my changes with message automated test", cwd=self.dir)
        self.assertTrue(report.success, report.to_dict())
        log = subprocess.run(["git", "log", "--oneline", "-1"],
                             capture_output=True, text=True, cwd=self.dir)
        self.assertEqual(log.returncode, 0)
        self.assertIn("automated test", log.stdout)


class TestDoCli(BaseAutomationCase):
    """`sakti-ai do` CLI end-to-end (real subprocess)."""

    def _cli(self, *args):
        env = dict(os.environ)
        env["PYTHONPATH"] = ROOT + os.pathsep + env.get("PYTHONPATH", "")
        return subprocess.run(
            [sys.executable, "-m", "ai.cli", "do", *args],
            capture_output=True, text=True, cwd=self.dir, env=env)

    def test_cli_do_dry_run_plans_only(self):
        proc = self._cli("create a react app and run it", "--dry")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("plan:", proc.stdout)
        self.assertIn("dry run", proc.stdout)
        self.assertIn("scaffold a react project", proc.stdout)

    def test_cli_do_run_python_project(self):
        _python_project(self.dir)
        proc = self._cli("run the project")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("real-automation-ok", proc.stdout)
        self.assertIn("all 1 steps succeeded", proc.stdout)

    def test_cli_do_unplannable_returns_error(self):
        proc = self._cli("file my taxes with me")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("could not plan", proc.stderr)

    def test_cli_do_destructive_task_refused(self):
        proc = self._cli("delete everything with rm -rf /")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("refus", proc.stderr)

    def test_cli_do_history_flags_automation(self):
        _python_project(self.dir)
        self.assertEqual(self._cli("run the project").returncode, 0)
        hist = subprocess.run(
            [sys.executable, "-m", "ai.cli", "dev", "history",
             "--action", "automation"],
            capture_output=True, text=True, cwd=self.dir,
            env={**os.environ, "XDG_DATA_HOME": self.data,
                 "PYTHONPATH": ROOT + os.pathsep
                 + os.environ.get("PYTHONPATH", "")})
        self.assertEqual(hist.returncode, 0, hist.stderr)
        self.assertIn("automation", hist.stdout)


if __name__ == "__main__":
    unittest.main()