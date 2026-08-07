"""Tests for Phase 4A Developer Core — detection and command construction."""

import json
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from ai.dev import DevCommandEngine, DevContextDetector
from ai.dev.errors import diagnose


class Fixture:
    """Builds throwaway project dirs for detection tests."""

    def __init__(self):
        self.base = tempfile.mkdtemp(prefix="sakti_dev_")
        self.addCleanup = None

    def node(self, name="demo", deps=None, scripts=None, lock="package-lock.json"):
        d = os.path.join(self.base, "node")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "package.json"), "w") as fh:
            json.dump({"name": name, "dependencies": deps or {},
                       "scripts": scripts or {}}, fh)
        if lock:
            open(os.path.join(d, lock), "w").close()
        return d

    def python(self, name="demo", toml=True, requirements=True, lock=None):
        d = os.path.join(self.base, "py")
        os.makedirs(d, exist_ok=True)
        if toml:
            with open(os.path.join(d, "pyproject.toml"), "w") as fh:
                fh.write(f'[project]\nname = "{name}"\n'
                         'dependencies = ["fastapi>=0.1"]\n')
        if requirements:
            open(os.path.join(d, "requirements.txt"), "w").close()
        if lock:
            open(os.path.join(d, lock), "w").close()
        return d

    def php(self, name="demo", require=None, lock=True):
        d = os.path.join(self.base, "php")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "composer.json"), "w") as fh:
            json.dump({"name": name, "require": require or {}}, fh)
        if lock:
            open(os.path.join(d, "composer.lock"), "w").close()
        return d

    def destroy(self):
        shutil.rmtree(self.base, ignore_errors=True)


class TestDevContextDetector(unittest.TestCase):
    def setUp(self):
        self.fx = Fixture()
        self.detector = DevContextDetector()

    def tearDown(self):
        self.fx.destroy()

    def test_node_detection(self):
        d = self.fx.node(deps={"react": "^18"}, scripts={"dev": "vite"})
        ctx = self.detector.detect(d)
        self.assertEqual(ctx.project_type, "node")
        self.assertEqual(ctx.language, "javascript")
        self.assertEqual(ctx.framework, "react")
        self.assertEqual(ctx.package_manager, "npm")
        self.assertEqual(ctx.scripts.get("dev"), "vite")
        self.assertTrue(ctx.detected)

    def test_node_yarn_manager(self):
        d = self.fx.node(lock="yarn.lock")
        self.assertEqual(self.detector.detect(d).package_manager, "yarn")

    def test_node_pnpm_manager(self):
        d = self.fx.node(lock="pnpm-lock.yaml")
        self.assertEqual(self.detector.detect(d).package_manager, "pnpm")

    def test_python_pyproject_framework(self):
        d = self.fx.python()
        ctx = self.detector.detect(d)
        self.assertEqual(ctx.project_type, "python")
        self.assertEqual(ctx.language, "python")
        self.assertEqual(ctx.framework, "fastapi")
        self.assertEqual(ctx.package_manager, "pip")

    def test_python_poetry(self):
        d = self.fx.python(lock="poetry.lock")
        self.assertEqual(self.detector.detect(d).package_manager, "poetry")

    def test_python_uv(self):
        d = self.fx.python(lock="uv.lock")
        self.assertEqual(self.detector.detect(d).package_manager, "uv")

    def test_php_detection(self):
        d = self.fx.php(require={"laravel/framework": "^10"})
        ctx = self.detector.detect(d)
        self.assertEqual(ctx.project_type, "php")
        self.assertEqual(ctx.language, "php")
        self.assertEqual(ctx.framework, "laravel")
        self.assertEqual(ctx.package_manager, "composer")

    def test_empty_dir_unknown(self):
        d = os.path.join(self.fx.base, "empty")
        os.makedirs(d, exist_ok=True)
        ctx = self.detector.detect(d)
        self.assertFalse(ctx.detected)
        self.assertEqual(ctx.project_type, "unknown")

    def test_missing_dir_unknown(self):
        ctx = self.detector.detect(os.path.join(self.fx.base, "nope"))
        self.assertFalse(ctx.detected)


class _RecordingRunner:
    """Fake runner capturing commands instead of executing them."""

    def __init__(self):
        self.commands = []
        self.dry_runs = []
        self.live_runs = 0

    def run(self, command, dry_run=False, cwd=None):
        self.commands.append(command)
        self.dry_runs.append(dry_run)
        return type("R", (), {
            "success": True, "exit_code": 0, "stdout": "ok",
            "stderr": "", "dry_run": dry_run})()

    def run_live(self, command, cwd=None, timeout=None, on_line=None):
        self.live_runs += 1
        self.commands.append(command)
        return type("R", (), {
            "success": True, "exit_code": 0, "stdout": "ok",
            "stderr": "", "dry_run": False})()


class TestDevCommandEngineConstruction(unittest.TestCase):
    def setUp(self):
        self.fx = Fixture()
        self.runner = _RecordingRunner()
        self.engine = DevCommandEngine(runner=self.runner)

    def tearDown(self):
        self.fx.destroy()

    def test_run_node_uses_dev_script(self):
        d = self.fx.node(scripts={"dev": "vite"})
        self.engine.run_project(d)
        self.assertTrue(any("npm run dev" in c for c in self.runner.commands))

    def test_run_node_with_custom_script(self):
        d = self.fx.node(scripts={"start": "node index.js"})
        self.engine.run_project(d, script="start")
        self.assertEqual(self.runner.commands, ["npm run start"])

    def test_run_python_uses_main_py(self):
        d = self.fx.python()
        with open(os.path.join(d, "main.py"), "w") as fh:
            fh.write("print('x')")
        self.engine.run_project(d)
        self.assertTrue(any(c.endswith("main.py") for c in self.runner.commands))

    def test_run_php_builtin_server(self):
        d = self.fx.php()
        self.engine.run_project(d)
        self.assertTrue(any("php -S" in c for c in self.runner.commands))

    def test_install_node_npm(self):
        d = self.fx.node()
        self.engine.install_dependency("lodash", path=d)
        self.assertEqual(self.runner.commands, ["npm install lodash"])

    def test_install_node_yarn(self):
        d = self.fx.node(lock="yarn.lock")
        self.engine.install_dependency("lodash", path=d)
        self.assertEqual(self.runner.commands, ["yarn add lodash"])

    def test_install_python_uses_interpreter_pip(self):
        d = self.fx.python()
        self.engine.install_dependency("requests", path=d)
        cmd = self.runner.commands[0]
        self.assertIn("-m pip install requests", cmd)

    def test_install_php_composer(self):
        d = self.fx.php()
        self.engine.install_dependency("monolog/monolog", path=d)
        self.assertEqual(self.runner.commands,
                         ["composer require monolog/monolog"])

    def test_install_empty_dependency_fails(self):
        d = self.fx.node()
        result = self.engine.install_dependency("", path=d)
        self.assertFalse(result.success)

    def test_build_node_uses_build_script(self):
        d = self.fx.node(scripts={"build": "vite build"})
        self.engine.build_project(d)
        self.assertEqual(self.runner.commands, ["npm run build"])

    def test_build_python_module(self):
        d = self.fx.python()
        self.engine.build_project(d)
        self.assertIn("-m compileall", self.runner.commands[0])

    def test_build_php_composer_install(self):
        d = self.fx.php()
        self.engine.build_project(d)
        self.assertTrue("composer install" in self.runner.commands[0])

    def test_unsupported_project_fails(self):
        d = os.path.join(self.fx.base, "unknown")
        os.makedirs(d, exist_ok=True)
        self.assertFalse(self.engine.run_project(d).success)
        self.assertFalse(self.engine.build_project(d).success)
        self.assertFalse(self.engine.install_dependency("x", path=d).success)

    def test_status_matches_detector(self):
        d = self.fx.node()
        ctx = self.engine.status(d)
        self.assertEqual(ctx.project_type, "node")


class TestDevCommandSafety(unittest.TestCase):
    """Dry-run, confirmation and live streaming plumbing."""

    def setUp(self):
        self.fx = Fixture()
        self.runner = _RecordingRunner()
        self.engine = DevCommandEngine(runner=self.runner)

    def tearDown(self):
        self.fx.destroy()

    def test_dry_run_never_executes(self):
        d = self.fx.node(scripts={"dev": "vite"})
        result = self.engine.run_project(d, dry_run=True)
        self.assertTrue(result.dry_run)
        self.assertTrue(result.success)
        self.assertTrue(all(self.runner.dry_runs))
        # Runner received dry_run=True so it never spawned a subprocess.

    def test_install_confirmation_declined(self):
        d = self.fx.node()
        result = self.engine.install_dependency("lodash", path=d,
                                                confirm=lambda dep, cmd: False)
        self.assertFalse(result.success)
        self.assertEqual(result.exit_code, -4)
        self.assertIn("aborted", result.stderr)
        self.assertEqual(self.runner.commands, [])

    def test_install_confirmation_accepted(self):
        d = self.fx.node()
        result = self.engine.install_dependency("lodash", path=d,
                                                confirm=lambda dep, cmd: True)
        self.assertTrue(result.success)
        self.assertEqual(self.runner.commands, ["npm install lodash"])

    def test_install_dry_run_skips_confirmation(self):
        d = self.fx.node()
        asked = []
        result = self.engine.install_dependency(
            "lodash", path=d, dry_run=True,
            confirm=lambda dep, cmd: asked.append(dep) or False)
        self.assertEqual(asked, [])
        self.assertEqual(self.runner.commands, ["npm install lodash"])
        self.assertTrue(self.runner.dry_runs)

    def test_live_streaming_uses_run_live(self):
        d = self.fx.node(scripts={"dev": "vite"})
        self.engine.run_project(d, live=True)
        self.assertEqual(self.runner.live_runs, 1)

    def test_default_not_live(self):
        d = self.fx.node(scripts={"dev": "vite"})
        self.engine.run_project(d)
        self.assertEqual(self.runner.live_runs, 0)


class TestErrorDiagnosis(unittest.TestCase):
    """Human-readable failure hints for pip/npm."""

    def test_pip_no_matching_distribution(self):
        hint = diagnose("pip install foo", 1, "",
                        "ERROR: No matching distribution found for foo")
        self.assertIsNotNone(hint)
        self.assertIn("PyPI", hint)

    def test_pip_externally_managed(self):
        hint = diagnose(
            "pip install foo", 1, "",
            "error: externally-managed-environment\n(PEP 668)")
        self.assertIsNotNone(hint)
        self.assertIn("virtualenv", hint)

    def test_npm_e404(self):
        hint = diagnose("npm install foo", 1, "",
                        "npm ERR! code E404\nnpm ERR! 404 Not Found")
        self.assertIsNotNone(hint)
        self.assertIn("registry", hint)

    def test_npm_eacces(self):
        hint = diagnose("npm install -g x", 1,
                        "", "npm ERR! code EACCES permission denied")
        self.assertIsNotNone(hint)
        self.assertIn("permission", hint)

    def test_command_not_found(self):
        hint = diagnose("frobnicate -x", 1, "",
                        "'frobnicate' is not recognized as an internal "
                        "or external command")
        self.assertIsNotNone(hint)
        self.assertIn("PATH", hint)

    def test_success_returns_none(self):
        self.assertIsNone(diagnose("echo hi", 0, "hi", ""))


if __name__ == "__main__":
    unittest.main()