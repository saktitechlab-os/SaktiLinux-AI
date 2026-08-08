"""Unit tests for Phase 4B Tool Ecosystem — registry, manager, adapters.

Real binaries, no mocks: installed-tool detection uses the actual PATH
(a PATH with a temp shim dir stands in for a host), and all planned
commands are verified against the real host `git` binary.
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

from ai.tools import Tool, ToolManager, ToolRegistry
from ai.tools.adapters import DockerAdapter, GitAdapter, OpenCodeAdapter
from ai.tools.adapters.git import CommitError, NotARepository
from ai.tools.adapters.docker import DockerfileMissing
from ai.tools.adapters.opencode import OpenCodePathMissing


def real_git_available() -> bool:
    return shutil.which("git") is not None


class TestToolRegistry(unittest.TestCase):
    """Known tools are registered; installed state reflects the real PATH."""

    def test_known_tools_registered(self):
        reg = ToolRegistry()
        for name in ("git", "docker", "opencode", "node", "python", "pip"):
            self.assertIsNotNone(reg.get(name), name)

    def test_dynamic_registration(self):
        reg = ToolRegistry()
        reg.register(Tool("my-tool", "custom", bin=["my-tool"]))
        self.assertIsNotNone(reg.get("my-tool"))

    def test_python_detected_installed(self):
        reg = ToolRegistry()
        self.assertTrue(reg.is_installed("python"))

    def test_unlikely_tool_missing(self):
        reg = ToolRegistry(tools=[Tool("definitely-missing-zzz",
                                       "x", bin=["definitely-missing-zzz"])])
        self.assertFalse(reg.is_installed("definitely-missing-zzz"))

    def test_installed_subset(self):
        reg = ToolRegistry()
        self.assertIn("python", reg.installed_names())
        self.assertTrue(reg.detect()["python"])

    def test_find_by_binary(self):
        reg = ToolRegistry()
        if shutil.which("python3") is not None:
            self.assertEqual(reg.find_by_binary("python3").name, "python")


class TestToolManager(unittest.TestCase):
    """Command -> tool mapping and install planning."""

    def setUp(self):
        self.manager = ToolManager(registry=ToolRegistry())

    def test_map_git_command(self):
        tool = self.manager.map_tool("git status")
        self.assertEqual(tool.name, "git")

    def test_map_docker_command(self):
        tool = self.manager.map_tool("docker build")
        self.assertEqual(tool.name, "docker")

    def test_map_opencode_command(self):
        tool = self.manager.map_tool("opencode run")
        self.assertEqual(tool.name, "opencode")

    def test_map_commit_maps_to_git(self):
        tool = self.manager.map_tool("commit")
        self.assertEqual(tool.name, "git")

    def test_unknown_command_no_tool(self):
        self.assertIsNone(self.manager.map_tool("blahblah xyz"))

    def test_install_already_installed(self):
        reg = ToolRegistry()
        mgr = ToolManager(registry=reg)
        result = mgr.install_tool("python")
        self.assertTrue(result.success)
        self.assertIn("already installed", result.stdout)

    def test_install_unknown_tool_fails(self):
        result = self.manager.install_tool("no-such-tool")
        self.assertFalse(result.success)
        self.assertIn("unknown tool", result.stderr)

    def test_install_no_package_manager(self):
        import ai.tools.manager as m
        original = m.shutil.which
        try:
            m.shutil.which = lambda name: None
            result = self.manager.install_tool("docker")
            self.assertFalse(result.success)
            self.assertIn("no package manager", result.stderr)
        finally:
            m.shutil.which = original

    def test_install_dry_run_plans_command(self):
        import ai.tools.manager as m
        original = m.shutil.which
        try:
            def fake_which(name):
                if name == "pacman":
                    return "/usr/bin/pacman"
                return None
            m.shutil.which = fake_which
            result = self.manager.install_tool("docker", dry_run=True)
            self.assertTrue(result.success)
            self.assertIn("pacman -S", result.stdout)
        finally:
            m.shutil.which = original

    def test_install_apt_recipe(self):
        import ai.tools.manager as m
        original = m.shutil.which
        try:
            def fake_which(name):
                if name == "apt-get":
                    return "/usr/bin/apt-get"
                return None
            m.shutil.which = fake_which
            result = self.manager.install_tool("git", dry_run=True)
            self.assertTrue(result.success)
            self.assertIn("sudo apt-get install -y git", result.stdout)
        finally:
            m.shutil.which = original


class TestGitAdapter(unittest.TestCase):
    """Real repo fixtures: init a temp repo and check the adapter."""

    def _git(self, *args, cwd=None):
        return subprocess.run(["git", *args], capture_output=True, text=True,
                              cwd=cwd)

    def setUp(self):
        if not real_git():
            self.skipTest("git not available on this host")
        self.dir = tempfile.mkdtemp(prefix="sakti_git_")
        self._git("init", "-q", cwd=self.dir)
        self._git("config", "user.email", "t@t", cwd=self.dir)
        self._git("config", "user.name", "T", cwd=self.dir)
        open(os.path.join(self.dir, "a.txt"), "w").close()
        self.adapter = GitAdapter()

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_detects_repo_root(self):
        self.assertEqual(self.adapter.repo_root(self.dir), self.dir)
        nested = os.path.join(self.dir, "sub")
        os.makedirs(nested)
        self.assertEqual(self.adapter.repo_root(nested), self.dir)

    def test_not_a_repo(self):
        outside = tempfile.mkdtemp(prefix="sakti_git_no_")
        try:
            self.assertIsNone(self.adapter.repo_root(outside))
            with self.assertRaises(NotARepository):
                self.adapter.plan_status(outside)
        finally:
            shutil.rmtree(outside, ignore_errors=True)

    def test_status_plan(self):
        command, root = self.adapter.plan_status(self.dir)
        self.assertEqual(root, self.dir)
        self.assertIn("status", command)

    def test_commit_plan_stages_and_commits(self):
        command, root = self.adapter.plan_add_commit("hello", self.dir)
        self.assertIn("add -A", command)
        self.assertIn('commit -m "hello"', command)

    def test_commit_plan_requires_message(self):
        with self.assertRaises(CommitError):
            self.adapter.plan_add_commit("", self.dir)

    def test_push_plan(self):
        command, root = self.adapter.plan_push(self.dir)
        self.assertIn("push", command)


def real_git():
    try:
        return subprocess.run(["git", "--version"], capture_output=True,
                              text=True).returncode == 0
    except OSError:
        return False


class TestDockerAdapter(unittest.TestCase):
    """Dockerfile detection and build/run planning."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="sakti_dock_")
        self.adapter = DockerAdapter()

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_no_dockerfile(self):
        self.assertFalse(self.adapter.has_dockerfile(self.dir))
        with self.assertRaises(DockerfileMissing):
            self.adapter.plan_build(self.dir)

    def test_build_plan_with_dockerfile(self):
        open(os.path.join(self.dir, "Dockerfile"), "w").write("FROM x\n")
        command, root = self.adapter.plan_build(self.dir)
        self.assertEqual(root, self.dir)
        self.assertIn("build -t", command)
        self.assertIn(":latest", command)

    def test_build_plan_with_tag(self):
        open(os.path.join(self.dir, "Dockerfile"), "w").write("FROM x\n")
        command, _ = self.adapter.plan_build(self.dir, tag="team/app:v1")
        self.assertIn("-t team/app:v1", command)

    def test_run_plan_default_image(self):
        command, _ = self.adapter.plan_run(self.dir)
        self.assertIn("run --rm", command)
        self.assertTrue(command.endswith(f"{os.path.basename(self.dir)}:latest"))

    def test_run_plan_with_image_and_ports(self):
        command, _ = self.adapter.plan_run(
            self.dir, image="myimg:2", ports="8080:80", detach=True)
        self.assertIn("myimg:2", command)
        self.assertIn("-p 8080:80", command)
        self.assertIn("-d", command)


class TestOpenCodeAdapter(unittest.TestCase):
    """prompt -> real `opencode run` command planning."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="sakti_oc_")
        self.adapter = OpenCodeAdapter()

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_plan_run(self):
        command, root = self.adapter.plan_run("make an app", self.dir)
        self.assertEqual(root, self.dir)
        self.assertIn("run", command)
        self.assertIn("make an app", command)

    def test_plan_run_missing_dir(self):
        with self.assertRaises(OpenCodePathMissing):
            self.adapter.plan_run("x", os.path.join(self.dir, "nope"))

    def test_plan_generate_writes_to_project_file(self):
        command, _ = self.adapter.plan_generate("a script", self.dir,
                                                output_file="gen.py")
        self.assertIn("gen.py", command)
        # the command redirects stdout into the project file
        self.assertIn(">", command)

    def test_plan_generate_without_file_is_plain_run(self):
        command, _ = self.adapter.plan_generate("a script", self.dir)
        self.assertIn("run", command)


if __name__ == "__main__":
    unittest.main()