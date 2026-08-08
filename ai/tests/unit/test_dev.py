"""Tests for Phase 4A Developer Core — detection and command construction."""

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

from ai.core.types import ActionResult
from ai.dev import (DevCommandEngine, DevContextDetector, DevHistory,
                    format_export)
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


class TestDevHistory(unittest.TestCase):
    """The JSON-backed store: timestamps, status, cap, persistence."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="sakti_hist_")
        self.path = os.path.join(self.dir, "dev_history.json")
        self.store = DevHistory(path=self.path, limit=3)

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_add_records_status_and_timestamp(self):
        entry_id = self.store.add("npm run dev", "run", "/p", "success", 0)
        entry = self.store.get(entry_id)
        self.assertIsNotNone(entry)
        self.assertEqual(entry["command"], "npm run dev")
        self.assertEqual(entry["status"], "success")
        self.assertEqual(entry["exit_code"], 0)
        self.assertTrue(entry["timestamp"])
        self.assertGreater(entry["ts"], 0)

    def test_fail_status_recorded(self):
        entry_id = self.store.add("bad-cmd", "build", "", "fail", 1)
        self.assertEqual(self.store.get(entry_id)["status"], "fail")

    def test_dry_run_status_recorded(self):
        entry_id = self.store.add("echo x", "run", "", "dry-run", 0)
        self.assertEqual(self.store.get(entry_id)["status"], "dry-run")

    def test_cap_trims_oldest(self):
        ids = [self.store.add(f"cmd-{i}", "run", "", "success", 0)
               for i in range(6)]
        entries = self.store.list()
        self.assertEqual(len(entries), 3)
        newest = entries[0]
        self.assertEqual(newest["command"], "cmd-5")
        # oldest id may still be readable if kept; trimmed ones gone
        self.assertIsNone(self.store.get(ids[0]))
        self.assertIsNotNone(self.store.get(ids[-1]))

    def test_list_is_newest_first(self):
        for i in range(3):
            self.store.add(f"cmd-{i}", "run", "", "success", 0)
        entries = self.store.list()
        self.assertEqual([e["id"] for e in entries], [3, 2, 1])

    def test_default_limit_is_50(self):
        store = DevHistory(path=os.path.join(self.dir, "default_hist.json"))
        for i in range(60):
            store.add(f"cmd-{i}", "run", "", "success", 0)
        entries = store.list()
        self.assertEqual(len(entries), 50)
        self.assertTrue(all(e["id"] > 10 for e in entries))

    def test_list_slices_to_given_limit(self):
        for i in range(5):
            self.store.add(f"cmd-{i}", "run", "", "success", 0)
        self.assertEqual(len(self.store.list(limit=2)), 2)
        self.assertEqual(self.store.list(limit=0), [])

    def test_get_unknown_id_returns_none(self):
        self.store.add("x", "run", "", "success", 0)
        self.assertIsNone(self.store.get(999))
        self.assertIsNone(self.store.get(0))

    def test_get_returns_copy_not_mutation(self):
        entry_id = self.store.add("x", "run", "", "success", 0)
        entry = self.store.get(entry_id)
        entry["command"] = "mutated"
        self.assertEqual(self.store.get(entry_id)["command"], "x")

    def test_ids_are_monotonic_across_adds(self):
        ids = [self.store.add(f"c{i}", "run", "", "success", 0)
               for i in range(5)]
        self.assertEqual(ids, [1, 2, 3, 4, 5])

    def test_ids_continue_across_reload(self):
        self.store.add("a", "run", "", "success", 0)
        self.store.add("b", "run", "", "success", 0)
        reloaded = DevHistory(path=self.path, limit=3)
        new_id = reloaded.add("c", "install", "", "success", 0)
        self.assertEqual(new_id, 3)
        self.assertEqual(len(reloaded), 3)

    def test_persistence_across_reload(self):
        self.store.add("persist-this", "install", "/p", "success", 0)
        reloaded = DevHistory(path=self.path, limit=3)
        entries = reloaded.list()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["command"], "persist-this")

    def test_clear_empties(self):
        self.store.add("x", "run", "", "success", 0)
        self.store.clear()
        self.assertEqual(len(self.store), 0)

    def _seed(self, limit=50):
        self.store = DevHistory(path=self.path, limit=limit)
        self.store.add("npm run dev", "run", "/p", "success", 0)
        self.store.add("npm install docker", "install", "/p", "fail", 1)
        self.store.add("pytest", "build", "/p", "success", 0)
        self.store.add("npm run dev", "run", "/p", "dry-run", 0)

    def test_list_filter_by_status(self):
        self._seed()
        self.assertEqual(len(self.store.list(status="fail")), 1)
        self.assertEqual(self.store.list(status="fail")[0]["command"],
                         "npm install docker")
        self.assertEqual(len(self.store.list(status="success")), 2)
        self.assertEqual(len(self.store.list(status="dry-run")), 1)

    def test_list_filter_by_action(self):
        self._seed()
        self.assertEqual(len(self.store.list(action="run")), 2)
        self.assertEqual(len(self.store.list(action="build")), 1)
        self.assertEqual(len(self.store.list(action="install")), 1)
        self.assertEqual(len(self.store.list(action="replay")), 0)

    def test_list_filter_then_limit(self):
        self._seed()
        self.assertEqual(len(self.store.list(action="run", limit=1)), 1)
        self.assertEqual(self.store.list(action="run", limit=1)[0]["command"],
                         "npm run dev")

    def test_search_finds_command_substring(self):
        self._seed()
        hits = self.store.search("docker")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["action"], "install")

    def test_search_is_case_insensitive(self):
        self._seed()
        self.assertEqual(len(self.store.search("NPM RUN")), 2)

    def test_search_matches_cwd(self):
        self._seed()
        self.assertEqual(len(self.store.search("/p")), 4)
        self.assertEqual(len(self.store.search("/other")), 0)

    def test_search_empty_query_returns_nothing(self):
        self._seed()
        self.assertEqual(self.store.search(""), [])
        self.assertEqual(self.store.search("   "), [])

    def test_search_with_status_filter(self):
        self._seed()
        hits = self.store.search("npm", status="fail")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["status"], "fail")

    def test_export_json_roundtrip(self):
        self._seed()
        text = format_export(self.store.list(), "json")
        parsed = json.loads(text)
        self.assertEqual(len(parsed), 4)
        self.assertEqual(parsed[0]["action"], "run")

    def test_export_csv_has_header_and_rows(self):
        self._seed()
        text = format_export(self.store.list(), "csv")
        lines = text.strip().splitlines()
        self.assertTrue(lines[0].startswith("id,timestamp,action,status"))
        self.assertEqual(len(lines), 5)

    def test_export_markdown_table(self):
        self._seed()
        text = format_export(self.store.list(), "md")
        self.assertIn("| id | timestamp |", text)
        self.assertIn("npm install docker", text)

    def test_export_unknown_format_raises(self):
        with self.assertRaises(ValueError):
            format_export([], "xml")
        self.assertEqual(self.store.list(), [])


class TestDevHistoryRecording(unittest.TestCase):
    """Engine writes every executed command to its history store."""

    def setUp(self):
        self.fx = Fixture()
        self.dir = tempfile.mkdtemp(prefix="sakti_hist_rec_")
        self.store = DevHistory(path=os.path.join(self.dir, "h.json"),
                                limit=50)
        self.runner = _RecordingRunner()
        self.engine = DevCommandEngine(runner=self.runner,
                                       history=self.store)

    def tearDown(self):
        self.fx.destroy()
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_history_list_returns_recorded_entries(self):
        d = self.fx.node(scripts={"dev": "vite"})
        self.engine.run_project(d)
        entries = self.engine.history_list()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["action"], "run")
        self.assertEqual(entries[0]["exit_code"], 0)

    def test_history_list_respects_limit(self):
        for i in range(4):
            self.store.add(f"cmd-{i}", "build", "/p", "success", 0)
        entries = self.engine.history_list(limit=2)
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0]["command"], "cmd-3")

    def test_history_list_without_store_is_empty(self):
        engine = DevCommandEngine(runner=self.runner)
        self.assertEqual(engine.history_list(), [])

    def test_engine_records_run(self):
        d = self.fx.node(scripts={"dev": "vite"})
        self.engine.run_project(d)
        entries = self.store.list()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["action"], "run")
        self.assertEqual(entries[0]["status"], "success")
        self.assertIn("npm run dev", entries[0]["command"])

    def test_engine_records_install(self):
        d = self.fx.node()
        self.engine.install_dependency("lodash", path=d,
                                       confirm=lambda dep, cmd: True)
        entries = self.store.list()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["action"], "install")
        self.assertEqual(entries[0]["command"], "npm install lodash")

    def test_replay_runs_stored_command(self):
        d = self.fx.node(scripts={"dev": "vite"})
        self.engine.run_project(d)
        entry_id = self.store.list()[0]["id"]
        self.engine.replay(entry_id)
        self.assertEqual(len(self.store.list()), 2)
        self.assertEqual(self.store.list()[0]["action"], "replay")
        self.assertIn("npm run dev", self.store.list()[0]["command"])

    def test_replay_unknown_id_fails(self):
        result = self.engine.replay(999)
        self.assertFalse(result.success)
        self.assertEqual(result.exit_code, -5)

    def test_replay_dry_run_records_dry(self):
        d = self.fx.node(scripts={"dev": "vite"})
        self.engine.run_project(d)
        entry_id = self.store.list()[0]["id"]
        self.engine.replay(entry_id, dry_run=True)
        self.assertEqual(self.store.list()[0]["status"], "dry-run")

    def test_no_history_store_still_runs(self):
        engine = DevCommandEngine(runner=self.runner)
        d = self.fx.node(scripts={"dev": "vite"})
        result = engine.run_project(d)
        self.assertTrue(result.success)
        self.assertEqual(engine.history_list(), [])


class _ToolRunner(_RecordingRunner):
    """Runner that returns success with canned output for tool commands."""

    def __init__(self):
        super().__init__()
        self.canned = {}

    def run(self, command, dry_run=False, cwd=None):
        self.commands.append(command)
        if dry_run:
            return ActionResult(exit_code=0,
                                stdout=f"[dry-run] {command}", stderr="",
                                success=True, dry_run=True)
        out = "ok"
        for key, value in self.canned.items():
            if key in command:
                out = value
                break
        return ActionResult(exit_code=0, stdout=out, stderr="",
                            success=True)

    def run_live(self, command, on_line=None, cwd=None, timeout=None):
        return self.run(command, cwd=cwd)


def git_bin():
    import shutil
    return shutil.which("git") or "git"


class TestDevToolEngine(unittest.TestCase):
    """Engine git/docker/opencode methods: planning + recording."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="sakti_engine_tools_")
        self.store = DevHistory(path=os.path.join(self.dir, "h.json"),
                                limit=50)
        self.runner = _ToolRunner()
        self.engine = DevCommandEngine(runner=self.runner,
                                       history=self.store,
                                       live=False)

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def _make_repo(self):
        sub_directory = os.path.join(self.dir, "repo")
        os.makedirs(sub_directory)
        subprocess.run([git_bin(), "init", "-q"], cwd=sub_directory,
                       check=False, capture_output=True)
        subprocess.run([git_bin(), "config", "user.email", "a@b"],
                       cwd=sub_directory, check=False, capture_output=True)
        subprocess.run([git_bin(), "config", "user.name", "T"],
                       cwd=sub_directory, check=False, capture_output=True)
        with open(os.path.join(sub_directory, "f.txt"), "w") as fh:
            fh.write("hi")
        return sub_directory

    def test_git_status_not_a_repo_fails(self):
        result = self.engine.git_status(self.dir)
        self.assertFalse(result.success)
        self.assertEqual(result.exit_code, -1)

    def test_git_status_records_history(self):
        repo = self._make_repo()
        result = self.engine.git_status(repo, dry_run=True)
        self.assertTrue(result.success)
        entries = self.store.list()
        self.assertEqual(entries[0]["action"], "git")
        self.assertEqual(entries[0]["status"], "dry-run")
        self.assertIn("status", entries[0]["command"])

    def test_git_status_marks_dirty(self):
        repo = self._make_repo()
        subprocess.run([git_bin(), "add", "-A"], cwd=repo, check=False,
                       capture_output=True)
        subprocess.run([git_bin(), "commit", "-m", "init"], cwd=repo,
                       check=False, capture_output=True)
        with open(os.path.join(repo, "f.txt"), "w") as fh:
            fh.write("changed")
        result = self.engine.git_status(repo)
        self.assertTrue(result.success)
        self.assertIn("git status", result.stdout)

    def test_git_commit_missing_message_fails(self):
        repo = self._make_repo()
        result = self.engine.git_commit("", path=repo)
        self.assertFalse(result.success)
        self.assertIn("commit message", result.stderr)

    def test_git_commit_records_and_runs(self):
        repo = self._make_repo()
        result = self.engine.git_commit("hello world", path=repo,
                                        dry_run=True)
        self.assertTrue(result.success)
        entries = self.store.list()
        self.assertEqual(entries[0]["action"], "git")
        self.assertIn("commit -m \"hello world\"", entries[0]["command"])

    def test_git_commit_confirm_abort(self):
        repo = self._make_repo()
        result = self.engine.git_commit("x", path=repo,
                                        confirm=lambda a, b: False)
        self.assertFalse(result.success)
        self.assertEqual(result.exit_code, -4)

    def test_docker_build_missing_dockerfile_fails(self):
        result = self.engine.docker_build(self.dir)
        self.assertFalse(result.success)
        self.assertIn("no Dockerfile", result.stderr)

    def test_docker_build_plan_and_record(self):
        with open(os.path.join(self.dir, "Dockerfile"), "w") as fh:
            fh.write("FROM x")
        result = self.engine.docker_build(self.dir, dry_run=True)
        self.assertTrue(result.success)
        entries = self.store.list()
        self.assertEqual(entries[0]["action"], "docker")
        self.assertIn("docker build", entries[0]["command"])

    def test_docker_run_plan(self):
        with open(os.path.join(self.dir, "Dockerfile"), "w") as fh:
            fh.write("FROM x")
        result = self.engine.docker_run(self.dir, image="app:v2",
                                        ports="3000:80", dry_run=True)
        self.assertTrue(result.success)
        self.assertIn("app:v2", self.runner.commands[-1])

    def test_opencode_run_empty_prompt_fails(self):
        result = self.engine.opencode_run("", path=self.dir)
        self.assertFalse(result.success)

    def test_opencode_run_plan_and_record(self):
        result = self.engine.opencode_run("write api", path=self.dir,
                                          dry_run=True)
        self.assertTrue(result.success)
        entries = self.store.list()
        self.assertEqual(entries[0]["action"], "opencode")
        self.assertIn("write api", entries[0]["command"])

    def test_opencode_generate_plan(self):
        result = self.engine.opencode_generate("script please",
                                               path=self.dir,
                                               output_file="gen.py",
                                               dry_run=True)
        self.assertTrue(result.success)
        self.assertIn("gen.py", self.runner.commands[-1])


if __name__ == "__main__":
    unittest.main()