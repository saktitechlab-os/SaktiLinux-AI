"""End-to-end brain integration tests (dry-run, temp memory file)."""

import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from ai.actions import ActionPipeline
from ai.command import CommandTranslator
from ai.context import ContextEngine
from ai.core import SaktiBrain, IntentKind
from ai.memory import MemoryStore
from ai.planner import TaskPlanner


class TestEndToEnd(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp(prefix="sakti_e2e_")
        store = MemoryStore(path=os.path.join(self._tmp, "memory.json"))
        self.brain = SaktiBrain(
            context_engine=ContextEngine(),
            planner=TaskPlanner(),
            command_engine=CommandTranslator(),
            action_pipeline=ActionPipeline(continue_on_error=True),
            memory_store=store,
        )

    def test_full_install_pipeline(self):
        report = self.brain.process("install docker", dry_run=True)
        self.assertEqual(report.intent.kind, IntentKind.INSTALL)
        self.assertGreater(len(report.plan.steps), 0)
        self.assertGreater(len(report.results), 0)
        self.assertIn("intent", report.to_dict())

    def test_memory_remembers_project(self):
        store = MemoryStore(path=os.path.join(self._tmp, "memory2.json"))
        brain = SaktiBrain(
            context_engine=ContextEngine(),
            planner=TaskPlanner(),
            memory_store=store,
        )
        brain.process("install docker", dry_run=True)
        self.assertTrue(store.read("projects", "docker"))

    def test_report_timestamps(self):
        report = self.brain.process("system status", dry_run=True)
        self.assertIsNotNone(report.started_at)
        self.assertIsNotNone(report.finished_at)
        self.assertGreaterEqual(report.duration_ms, 0)


if __name__ == "__main__":
    unittest.main()