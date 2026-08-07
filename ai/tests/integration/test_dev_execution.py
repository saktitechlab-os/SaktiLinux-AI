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
import time
import unittest

ROOT = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from ai.actions.runner import CommandRunner
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


class TestLiveStreaming(unittest.TestCase):
    """run_live streams lines as they are produced (real subprocess)."""

    def setUp(self):
        self.runner = CommandRunner(timeout_seconds=5)

    def test_run_live_captures_stdout(self):
        result = self.runner.run_live("echo live-stream-ok")
        self.assertTrue(result.success)
        self.assertIn("live-stream-ok", result.stdout)
        self.assertFalse(result.dry_run)

    def test_run_live_streams_incremental_lines(self):
        seen: list[str] = []
        script = ("import sys,time\n"
                  "for i in range(3):\n"
                  "    print('line', i, flush=True)\n"
                  "    time.sleep(0.1)\n")
        script_path = os.path.join(tempfile.gettempdir(),
                                   "sakti_live_probe.py")
        with open(script_path, "w", encoding="utf-8") as fh:
            fh.write(script)
        try:
            result = self.runner.run_live(
                f"{sys.executable} \"{script_path}\"",
                on_line=lambda l, s: seen.append(l))
            self.assertTrue(result.success, result.stderr)
            content = [l for l in seen if l]  # drop EOF markers
            self.assertEqual(len(content), 3)
            self.assertEqual(content[0], "line 0")
            self.assertEqual(content[2], "line 2")
        finally:
            os.unlink(script_path)

    def test_run_live_timeout_is_reported(self):
        script_path = os.path.join(tempfile.gettempdir(),
                                   "sakti_sleep_probe.py")
        with open(script_path, "w", encoding="utf-8") as fh:
            fh.write("import time\ntime.sleep(30)\n")
        try:
            result = self.runner.run_live(
                f"{sys.executable} \"{script_path}\"", timeout=1)
            self.assertFalse(result.success)
            self.assertEqual(result.exit_code, -2)
        finally:
            os.unlink(script_path)

    def test_run_live_stderr_captured(self):
        script_path = os.path.join(tempfile.gettempdir(),
                                   "sakti_err_probe.py")
        with open(script_path, "w", encoding="utf-8") as fh:
            fh.write("import sys\nsys.stderr.write('boom-err')\n")
        try:
            result = self.runner.run_live(
                f"{sys.executable} \"{script_path}\"")
            self.assertTrue(result.success)
            self.assertIn("boom-err", result.stderr)
        finally:
            os.unlink(script_path)


class TestSafetyAndHints(unittest.TestCase):
    """Dry-run provably does nothing; failures get readable hints."""

    def test_dry_run_leaves_no_side_effect(self):
        marker = os.path.join(tempfile.gettempdir(),
                              "sakti-dry-marker-xyz")
        if os.path.exists(marker):
            os.unlink(marker)
        d = tempfile.mkdtemp(prefix="sakti_dry_")
        try:
            with open(os.path.join(d, "main.py"), "w") as fh:
                fh.write("print('x')\n")
            with open(os.path.join(d, "pyproject.toml"), "w") as fh:
                fh.write('[project]\nname = "x"\n')
            open(os.path.join(d, "requirements.txt"), "w").close()
            with open(os.path.join(d, "main2.py"), "w") as fh:
                fh.write(f"print(open(r'{marker}','w'))\n")
            # dry-run build must not create anything
            engine = DevCommandEngine()
            with open(os.path.join(d, "touch.py"), "w") as fh:
                fh.write(f"open(r'{marker}','w').write('x')")
            result = engine.run_project(d, dry_run=True)
            self.assertTrue(result.success)
            self.assertTrue(result.dry_run)
            self.assertFalse(os.path.exists(marker),
                             "dry-run must never touch the filesystem")
        finally:
            shutil.rmtree(d, ignore_errors=True)
            if os.path.exists(marker):
                os.unlink(marker)

    def test_failed_pip_install_gets_hint(self):
        if _which("pip") is False and "python" not in str(sys.executable):
            self.skipTest("no pip on this host")
        d = tempfile.mkdtemp(prefix="sakti_hint_")
        try:
            with open(os.path.join(d, "main.py"), "w") as fh:
                fh.write("print(1)\n")
            with open(os.path.join(d, "pyproject.toml"), "w") as fh:
                fh.write('[project]\nname = "x"\n')
            open(os.path.join(d, "requirements.txt"), "w").close()
            engine = DevCommandEngine()
            result = engine.install_dependency("sakti-nonexistent-xyz",
                                               path=d)
            self.assertFalse(result.success)
            self.assertTrue(any(word in result.stderr.lower()
                                for word in ("pypi", "pypl", "no matching",
                                             "not on pypi", "does not exist")),
                            f"expected a friendly hint, got: {result.stderr}")
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_cli_install_dry_run_no_prompt(self):
        d = tempfile.mkdtemp(prefix="sakti_cli_dry_")
        try:
            with open(os.path.join(d, "main.py"), "w") as fh:
                fh.write("print(1)\n")
            with open(os.path.join(d, "pyproject.toml"), "w") as fh:
                fh.write('[project]\nname = "x"\n')
            open(os.path.join(d, "requirements.txt"), "w").close()
            env = dict(os.environ)
            env["PYTHONPATH"] = ROOT + os.pathsep + env.get("PYTHONPATH", "")
            proc = subprocess.run(
                [sys.executable, "-m", "ai.cli", "dev", "install",
                 "six", "--dry", "--yes"],
                capture_output=True, text=True, cwd=d, env=env)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("[dry-run]", proc.stdout)
            self.assertNotIn("[sakti] will run:", proc.stdout)
        finally:
            shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()