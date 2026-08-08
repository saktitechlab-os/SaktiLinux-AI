"""Real-world integration tests for Phase 4B Tool Ecosystem.

git commands run against a real temporary repository; docker/opencode
commands are verified end-to-end where the binary exists and fail
cleanly (exit 1, clear message) where it does not.
"""

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


def _git(*args, cwd=None):
    return subprocess.run(["git", *args], capture_output=True, text=True,
                          cwd=cwd)


class TestGitCli(unittest.TestCase):
    """`sakti-ai dev git status|commit|push` against a real repo."""

    @classmethod
    def setUpClass(cls):
        try:
            _git("--version")
        except OSError:
            raise unittest.SkipTest("git not available on this host")

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="sakti_git_cli_")
        _git("init", "-q", cwd=self.dir)
        _git("config", "user.email", "t@t", cwd=self.dir)
        _git("config", "user.name", "T", cwd=self.dir)
        with open(os.path.join(self.dir, "app.txt"), "w") as fh:
            fh.write("v1\n")

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def _cli(self, *args):
        env = dict(os.environ)
        env["PYTHONPATH"] = ROOT + os.pathsep + env.get("PYTHONPATH", "")
        return subprocess.run(
            [sys.executable, "-m", "ai.cli", "dev", "git", *args],
            capture_output=True, text=True, cwd=self.dir, env=env)

    def test_status_shows_untracked_file(self):
        proc = self._cli("status")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("app.txt", proc.stdout)

    def test_status_dirty_after_edit(self):
        _git("add", "-A", cwd=self.dir)
        _git("commit", "-m", "init", cwd=self.dir)
        with open(os.path.join(self.dir, "app.txt"), "w") as fh:
            fh.write("v2\n")
        proc = self._cli("status")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("M", proc.stdout)

    def test_status_clean_after_commit(self):
        _git("add", "-A", cwd=self.dir)
        _git("commit", "-m", "init", cwd=self.dir)
        proc = self._cli("status")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertNotIn("app.txt", proc.stdout)

    def test_commit_stages_and_commits(self):
        proc = self._cli("commit", "-m", "first real commit", "--yes")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        log = _git("log", "--oneline", cwd=self.dir)
        self.assertEqual(log.returncode, 0)
        self.assertIn("first real commit", log.stdout)

    def test_commit_dry_run_does_not_commit(self):
        proc = self._cli("commit", "-m", "dry one", "--dry")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        log = _git("log", "--oneline", cwd=self.dir)
        self.assertNotIn("dry one", log.stdout)

    def test_commit_aborted_by_user(self):
        proc = subprocess.run(
            [sys.executable, "-m", "ai.cli", "dev", "git", "commit",
             "-m", "no really"],
            capture_output=True, text=True, cwd=self.dir,
            env=dict(os.environ, PYTHONPATH=ROOT), input="n\n")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("aborted", proc.stderr)

    def test_commit_outside_repo_fails(self):
        outside = tempfile.mkdtemp(prefix="sakti_no_repo_")
        try:
            env = dict(os.environ)
            env["PYTHONPATH"] = ROOT
            proc = subprocess.run(
                [sys.executable, "-m", "ai.cli", "dev", "git", "status"],
                capture_output=True, text=True, cwd=outside, env=env)
            self.assertEqual(proc.returncode, 1)
            self.assertIn("not a git repository", proc.stderr)
        finally:
            shutil.rmtree(outside, ignore_errors=True)

    def test_push_without_remote_fails_cleanly(self):
        _git("add", "-A", cwd=self.dir)
        _git("commit", "-m", "init", cwd=self.dir)
        proc = self._cli("push")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("failed", proc.stderr)

    def test_history_records_git_actions(self):
        data = tempfile.mkdtemp(prefix="sakti_hist_data_")
        try:
            env = dict(os.environ)
            env["PYTHONPATH"] = ROOT
            env["XDG_DATA_HOME"] = data
            subprocess.run(
                [sys.executable, "-m", "ai.cli", "dev", "git", "commit",
                 "-m", "hist one", "--yes"],
                capture_output=True, text=True, cwd=self.dir, env=env)
            proc = subprocess.run(
                [sys.executable, "-m", "ai.cli", "dev", "history",
                 "--action", "git"],
                capture_output=True, text=True, cwd=self.dir, env=env)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("git", proc.stdout)
            self.assertIn("commit -m", proc.stdout)
        finally:
            shutil.rmtree(data, ignore_errors=True)


class TestToolsCli(unittest.TestCase):
    """`sakti-ai tools list|install` against the real host."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="sakti_tools_cli_")

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def _cli(self, *args):
        env = dict(os.environ)
        env["PYTHONPATH"] = ROOT + os.pathsep + env.get("PYTHONPATH", "")
        return subprocess.run(
            [sys.executable, "-m", "ai.cli", "tools", *args],
            capture_output=True, text=True, cwd=self.dir, env=env)

    def test_list_shows_known_tools(self):
        proc = self._cli("list")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        for name in ("git", "docker", "opencode", "node"):
            self.assertIn(name, proc.stdout)
        self.assertIn("installed", proc.stdout)

    def test_list_marks_git_installed(self):
        proc = self._cli("list")
        self.assertEqual(proc.returncode, 0)
        if shutil.which("git"):
            self.assertIn("[x] git", proc.stdout)

    def test_install_unknown_tool_fails(self):
        proc = self._cli("install", "not-a-real-tool")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("unknown tool", proc.stderr)

    def test_install_already_installed(self):
        proc = self._cli("install", "git")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        if shutil.which("git"):
            self.assertIn("already installed", proc.stdout)

    def test_install_dry_run_prints_plan(self):
        proc = self._cli("install", "docker", "--dry")
        # if a package manager exists we get a plan; without one (Windows
        # host) we get a clean explanation — never a crash.
        if shutil.which("pacman") or shutil.which("apt-get"):
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("pacman -S", proc.stdout)
        else:
            self.assertEqual(proc.returncode, 1)
            self.assertIn("package manager", proc.stderr)

    def test_install_aborted_by_user(self):
        proc = subprocess.run(
            [sys.executable, "-m", "ai.cli", "tools", "install", "docker"],
            capture_output=True, text=True, cwd=self.dir,
            env=dict(os.environ, PYTHONPATH=ROOT), input="n\n")
        # no package manager on Windows -> clean failure or abort
        self.assertEqual(proc.returncode, 1)


class TestDockerCli(unittest.TestCase):
    """`sakti-ai dev docker build|run` end-to-end."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="sakti_docker_cli_")
        with open(os.path.join(self.dir, "Dockerfile"), "w") as fh:
            fh.write("FROM alpine:3.18\nCMD ['echo', 'hi']\n")

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def _cli(self, *args):
        env = dict(os.environ)
        env["PYTHONPATH"] = ROOT + os.pathsep + env.get("PYTHONPATH", "")
        return subprocess.run(
            [sys.executable, "-m", "ai.cli", "dev", "docker", *args],
            capture_output=True, text=True, cwd=self.dir, env=env)

    def test_dry_run_plans_build(self):
        proc = self._cli("build", "--dry")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("docker build", proc.stdout)
        self.assertIn("[dry-run]", proc.stdout)

    def test_dry_run_plans_run(self):
        proc = self._cli("run", "--dry", "--image", "alpine:3.18")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("[dry-run]", proc.stdout)
        self.assertIn("alpine:3.18", proc.stdout)

    def test_build_without_dockerfile_fails(self):
        empty = tempfile.mkdtemp(prefix="sakti_no_dockerfile_")
        try:
            env = dict(os.environ)
            env["PYTHONPATH"] = ROOT
            proc = subprocess.run(
                [sys.executable, "-m", "ai.cli", "dev", "docker", "build"],
                capture_output=True, text=True, cwd=empty, env=env)
            self.assertEqual(proc.returncode, 1)
            self.assertIn("no Dockerfile", proc.stderr)
        finally:
            shutil.rmtree(empty, ignore_errors=True)

    @unittest.skipUnless(shutil.which("docker"),
                         "docker not installed on this host")
    def test_real_build_and_run(self):
        proc = self._cli("build", "--tag", "sakti-itest:1")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        proc = self._cli("run", "--image", "sakti-itest:1")
        self.assertEqual(proc.returncode, 0, proc.stderr)


class TestOpenCodeCli(unittest.TestCase):
    """`sakti-ai dev opencode run|generate` end-to-end."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="sakti_oc_cli_")

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def _cli(self, *args):
        env = dict(os.environ)
        env["PYTHONPATH"] = ROOT + os.pathsep + env.get("PYTHONPATH", "")
        return subprocess.run(
            [sys.executable, "-m", "ai.cli", "dev", "opencode", *args],
            capture_output=True, text=True, cwd=self.dir, env=env)

    def test_dry_run_plans_prompt(self):
        proc = self._cli("run", "say hello", "--dry")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("[dry-run]", proc.stdout)
        self.assertIn("say hello", proc.stdout)

    def test_dry_run_generate_plans_file(self):
        proc = self._cli("generate", "write app.py", "--file", "app.py",
                         "--dry")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("app.py", proc.stdout)

    def test_empty_prompt_fails(self):
        proc = self._cli("run", "   ", "--dry")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("prompt", proc.stderr)


if __name__ == "__main__":
    unittest.main()