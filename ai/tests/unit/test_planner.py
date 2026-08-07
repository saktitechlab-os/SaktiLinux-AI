"""Tests for the planner (rule-based task decomposition)."""

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from ai.core import ContextSnapshot, Intent, IntentKind
from ai.planner import TaskPlanner


def intent_for(kind, text, params=None):
    return Intent(kind=kind, raw=text, parameters=params or {})


class TestTaskPlanner(unittest.TestCase):
    def setUp(self):
        self.planner = TaskPlanner()
        self.ctx = ContextSnapshot()

    def test_install_plan(self):
        plan = self.planner.plan(intent_for(IntentKind.INSTALL, "install docker",
                                            {"target": "docker"}), self.ctx)
        self.assertEqual(plan.intent, "install")
        self.assertGreaterEqual(len(plan.steps), 4)

    def test_create_plan(self):
        plan = self.planner.plan(intent_for(IntentKind.CREATE, "create react app",
                                            {"stack": "react"}), self.ctx)
        self.assertEqual(plan.summary, "Scaffold a react project")

    def test_unknown_kind_falls_back_to_generic(self):
        plan = self.planner.plan(intent_for(IntentKind.GENERAL, "hello"), self.ctx)
        self.assertEqual(len(plan.steps), 2)

    def test_all_step_orders_sequential(self):
        plan = self.planner.plan(intent_for(IntentKind.INSTALL, "install git",
                                            {"target": "git"}), self.ctx)
        self.assertEqual([s.order for s in plan.steps],
                         list(range(1, len(plan.steps) + 1)))


if __name__ == "__main__":
    unittest.main()