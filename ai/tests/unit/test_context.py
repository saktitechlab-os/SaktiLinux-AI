"""Tests for ai/context engine (dependency-free probes)."""

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from ai.context import ContextEngine


class TestContextEngine(unittest.TestCase):
    def setUp(self):
        self.engine = ContextEngine(cwd=os.getcwd())

    def test_capture_returns_snapshot_fields(self):
        snap = self.engine.capture()
        self.assertEqual(snap.cwd, os.getcwd())
        self.assertIsInstance(snap.os_name, str)
        self.assertIsInstance(snap.internet, bool)

    def test_cpu_and_mem_floats(self):
        snap = self.engine.capture()
        self.assertIsInstance(snap.cpu_percent, float)
        self.assertIsInstance(snap.mem_percent, float)

    def test_git_project_detection(self):
        # The repo root has .git, engine should find it from cwd.
        snap = self.engine.capture()
        self.assertTrue(snap.active_project)


if __name__ == "__main__":
    unittest.main()