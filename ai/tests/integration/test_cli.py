"""CLI smoke tests — the commands in the Phase-3 acceptance list.

These run the REAL entrypoints (scripts/sakti-ai, python -m ai.cli,
python -m ai.core) as subprocesses and assert they produce output and
exit 0. They are the "must work" commands:

    python scripts/sakti-ai chat "hello"
    python scripts/sakti-ai status
    python scripts/sakti-ai memory list
"""

import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def run_cli(*args, cwd=ROOT):
    return subprocess.run([sys.executable, *args],
                          capture_output=True, text=True, cwd=cwd,
                          timeout=60)


class TestScriptsSaktiAi(unittest.TestCase):
    """`python scripts/sakti-ai <cmd>` must work."""

    SCRIPT = os.path.join(ROOT, "scripts", "sakti-ai")

    def test_chat_hello_returns_output(self):
        result = run_cli(self.SCRIPT, "chat", "hello")
        self.assertEqual(result.returncode, 0,
                         f"stderr: {result.stderr}")
        self.assertIn("SaktiAI", result.stdout)

    def test_chat_install_docker_prints_plan_and_result(self):
        result = run_cli(self.SCRIPT, "chat", "install docker")
        self.assertEqual(result.returncode, 0,
                         f"stderr: {result.stderr}")
        self.assertIn("intent detected: install", result.stdout)
        self.assertIn("step", result.stdout.lower())

    def test_status_output(self):
        result = run_cli(self.SCRIPT, "status")
        self.assertEqual(result.returncode, 0,
                         f"stderr: {result.stderr}")
        self.assertIn("engine=sakti-brain", result.stdout)
        self.assertIn("modules:", result.stdout)

    def test_memory_list_output(self):
        result = run_cli(self.SCRIPT, "memory", "list")
        self.assertEqual(result.returncode, 0,
                         f"stderr: {result.stderr}")
        self.assertIn("entries", result.stdout)

    def test_memory_list_projects(self):
        result = run_cli(self.SCRIPT, "memory", "list", "projects")
        self.assertEqual(result.returncode, 0,
                         f"stderr: {result.stderr}")
        self.assertIn("projects", result.stdout)


class TestModuleEntrypoints(unittest.TestCase):
    """`python -m ai.cli` / `python -m ai.core` must work."""

    def test_module_cli_chat(self):
        result = run_cli("-m", "ai.cli", "chat", "hello")
        self.assertEqual(result.returncode, 0,
                         f"stderr: {result.stderr}")
        self.assertIn("SaktiAI", result.stdout)

    def test_module_core_requires_ai(self):
        result = run_cli("-m", "ai.core", "hello")
        self.assertEqual(result.returncode, 0,
                         f"stderr: {result.stderr}")
        self.assertIn("SaktiAI", result.stdout)


if __name__ == "__main__":
    unittest.main()