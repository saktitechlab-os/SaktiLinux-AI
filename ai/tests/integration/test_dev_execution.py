"""Real-world integration tests for Phase 4A Developer Core.

These tests drive the REAL DevCommandEngine against throwaway projects
on disk: detection runs against actual files, and run/install/build
spawn genuine subprocesses (no mocks, no dry-run).

Safety: npm-dependent tests are skipped when npm is not installed;
the only package ever installed is `six` (pure-python, tiny) into the
running interpreter — nothing touches system package state otherwise.
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

from ai.dev import DevCommandEngine


def _which(name: str) -> bool:
    return shutil.which(name) is not None


@unittest.skipUnless(_which("node") and _which("npm"),
                     "node/npm not available on this host")
class TestRealNodeExecution(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="sakti_dev_node_")
        with open(os.path.join(self.dir, "package.json"), "w") as fh:
            json.dump({"name": "demo", "scripts": {"dev": "echo real-dev-ok",
                                                   "build": "echo real-build-ok"},
                       "dependencies": {}}, fh)
        open(os.path.join(self.dir, "package-lock.json"), "w").close()
        self.engine = DevCommandEngine()

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_detects_node_project(self):
        ctx = self.engine.status(self.dir)
        self.assertEqual(ctx.project_type, "node")
        self.assertEqual(ctx.package_manager, "npm")

    def test_run_project_executes_real_script(self):
        result = self.engine.run_project(self.dir)
        self.assertTrue(result.success)
        self.assertIn("real-dev-ok", result.stdout)

    def test_build_project_executes_real_script(self):
        result = self.engine.build_project(self.dir)
        self.assertTrue(result.success)
        self.assertIn("real-build-ok", result.stdout)

    def test_install_dependency_real(self):
        result = self.engine.install_dependency("is-number", path=self.dir)
        self.assertTrue(result.success, result.stderr)
        self.assertTrue(os.path.exists(
            os.path.join(self.dir, "node_modules", "is-number")))


class TestRealPythonExecution(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="sakti_dev_py_")
        with open(os.path.join(self.dir, "pyproject.toml"), "w") as fh:
            fh.write('[project]\nname = "demo"\n'
                     'dependencies = ["six>=1.0"]\n')
        with open(os.path.join(self.dir, "main.py"), "w") as fh:
            fh.write("print('real-py-run-ok')\n")
        self.engine = DevCommandEngine()

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_detects_python_project(self):
        ctx = self.engine.status(self.dir)
        self.assertEqual(ctx.project_type, "python")
        self.assertEqual(ctx.package_manager, "pip")

    def test_run_project_executes_main_py(self):
        result = self.engine.run_project(self.dir)
        self.assertTrue(result.success, result.stderr)
        self.assertIn("real-py-run-ok", result.stdout)

    def test_install_dependency_real(self):
        result = self.engine.install_dependency("six", path=self.dir)
        self.assertTrue(result.success, result.stderr)
        probe = subprocess.run([sys.executable, "-c", "import six"],
                               capture_output=True, text=True)
        self.assertEqual(probe.returncode, 0)

    def test_build_python_module(self):
        result = self.engine.build_project(self.dir)
        self.assertTrue(result.success, result.stderr)
        self.assertIn("python", result.stdout.lower())


class TestRealCliDev(unittest.TestCase):
    """The `sakti-ai dev` CLI drives the real engine end-to-end."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="sakti_dev_cli_")
        with open(os.path.join(self.dir, "main.py"), "w") as fh:
            fh.write("print('cli-dev-ok')\n")
        with open(os.path.join(self.dir, "pyproject.toml"), "w") as fh:
            fh.write('[project]\nname = "cli-demo"\n')
        open(os.path.join(self.dir, "requirements.txt"), "w").close()

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def _cli(self, *args):
        env = dict(os.environ)
        env["PYTHONPATH"] = ROOT + os.pathsep + env.get("PYTHONPATH", "")
        return subprocess.run(
            [sys.executable, "-m", "ai.cli", "dev", *args],
            capture_output=True, text=True, cwd=self.dir, env=env)

    def test_dev_status(self):
        proc = self._cli("status")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("project type:", proc.stdout)
        self.assertIn("python", proc.stdout)

    def test_dev_run(self):
        proc = self._cli("run")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("cli-dev-ok", proc.stdout)

    def test_dev_status_no_project_exit_1(self):
        empty = tempfile.mkdtemp(prefix="sakti_dev_empty_")
        try:
            env = dict(os.environ)
            env["PYTHONPATH"] = ROOT + os.pathsep + env.get("PYTHONPATH", "")
            proc = subprocess.run(
                [sys.executable, "-m", "ai.cli", "dev", "status"],
                capture_output=True, text=True, cwd=empty, env=env)
            self.assertEqual(proc.returncode, 1)
            self.assertIn("no supported project", proc.stdout)
        finally:
            shutil.rmtree(empty, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()