"""Tests for ai/core domain types."""

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from ai.core import (ActionResult, ContextSnapshot, ExecutionReport, Intent,
                     IntentKind, Plan)


class TestIntent(unittest.TestCase):
    def test_intent_to_dict(self):
        intent = Intent(kind=IntentKind.INSTALL, raw="install docker",
                        parameters={"target": "docker"}, confidence=0.7)
        d = intent.to_dict()
        self.assertEqual(d["kind"], "install")
        self.assertEqual(d["raw"], "install docker")
        self.assertEqual(d["parameters"]["target"], "docker")

    def test_intent_defaults(self):
        intent = Intent(kind=IntentKind.GENERAL, raw="hi")
        self.assertEqual(intent.confidence, 0.0)
        self.assertEqual(intent.parameters, {})


class TestPlan(unittest.TestCase):
    def test_add_step_orders(self):
        plan = Plan(intent="install", summary="Install docker")
        plan.add_step("detect os")
        plan.add_step("install", command="pacman -S docker")
        self.assertEqual([s.order for s in plan.steps], [1, 2])
        self.assertEqual(plan.steps[1].command, "pacman -S docker")

    def test_plan_to_dict(self):
        plan = Plan(intent="create", summary="Buil")
        plan.add_step("scaffold", command="npx create-react-app")
        d = plan.to_dict()
        self.assertEqual(d["summary"], "Buil")

    def test_to_dict_contains_steps(self):
        plan = Plan(intent="deploy", summary="Deploy site")
        plan.add_step("build", command="npm run build")
        d = plan.to_dict()
        self.assertEqual(len(d["steps"]), 1)
        self.assertEqual(d["steps"][0]["order"], 1)


class TestActionResult(unittest.TestCase):
    def test_ok_factory(self):
        r = ActionResult.ok("done")
        self.assertTrue(r.success)
        self.assertEqual(r.exit_code, 0)

    def test_fail_factory(self):
        r = ActionResult.fail("boom", 2)
        self.assertFalse(r.success)
        self.assertEqual(r.exit_code, 2)


class TestExecutionReport(unittest.TestCase):
    def test_all_ok_empty_false(self):
        report = ExecutionReport()
        self.assertFalse(report.all_ok)

    def test_all_ok_true(self):
        report = ExecutionReport(results=[ActionResult.ok("a"),
                                          ActionResult.ok("b")])
        self.assertTrue(report.all_ok)

    def test_all_ok_partial(self):
        report = ExecutionReport(results=[ActionResult.ok("a"),
                                          ActionResult.fail("b")])
        self.assertFalse(report.all_ok)

    def test_duration_ms_positive(self):
        report = ExecutionReport()
        self.assertGreaterEqual(report.duration_ms, 0.0)

    def test_to_dict_top_level(self):
        report = ExecutionReport(intent=Intent(kind=IntentKind.SYSTEM,
                                               raw="system info"),
                                 plan=Plan(intent="system",
                                           summary="system"))
        d = report.to_dict()
        self.assertEqual(d["intent"]["kind"], "system")
        self.assertIn("elapsed_ms", d)


if __name__ == "__main__":
    unittest.main()