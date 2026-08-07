"""Tests for ai/core brain orchestrator with stubbed collaborators."""

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from ai.actions import ActionPipeline, CommandRunner
from ai.command import CommandTranslator
from ai.context import ContextEngine
from ai.core import SaktiBrain, IntentKind
from ai.memory import MemoryStore
from ai.planner import TaskPlanner


def make_brain():
    return SaktiBrain(
        context_engine=ContextEngine(),
        planner=TaskPlanner(),
        command_engine=CommandTranslator(),
        action_pipeline=ActionPipeline(continue_on_error=True),
        memory_store=MemoryStore(),
    )


class TestSaktiBrain(unittest.TestCase):
    def test_minimal_brain(self):
        brain = SaktiBrain()
        report = brain.process("hello")
        self.assertIsNotNone(report.intent)
        self.assertIsNotNone(report.message)

    def test_full_pipeline_dry_run(self):
        brain = make_brain()
        report = brain.process("search for files", dry_run=True)
        self.assertEqual(report.intent.kind, IntentKind.SEARCH)
        self.assertGreater(len(report.results), 0)

    def test_memory_write(self):
        store = MemoryStore()
        brain = SaktiBrain(memory_store=store)
        brain.process("install docker", dry_run=True)
        history = store.recent_history(limit=3)
        self.assertTrue(any("install docker" in h for h in history))

    def test_status_payload(self):
        brain = make_brain()
        status = brain.status()
        self.assertEqual(status["engine"], "sakti-brain")
        self.assertIn("modules", status)


if __name__ == "__main__":
    unittest.main()