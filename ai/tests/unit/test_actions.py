"""Tests for the actions pipeline (dry-run + fail-fast)."""

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from ai.actions import ActionPipeline
from ai.core import ActionResult, Intent, IntentKind, Plan


def plan_with(commands):
    plan = Plan(intent="test", summary="s")
    for cmd in commands:
        plan.add_step("step", command=cmd)
    return plan


class TestActionPipeline(unittest.TestCase):
    def setUp(self):
        self.intent = Intent(kind=IntentKind.GENERAL, raw="test")
        self.cmds = {1: "echo hi", 2: "echo there"}

    def test_dry_run_produces_success(self):
        pipeline = ActionPipeline()
        plan = plan_with(["echo hi"])
        results = pipeline.execute(self.intent, plan, self.cmds, dry_run=True)
        self.assertTrue(results[0].success)
        self.assertTrue(results[0].dry_run)

    def test_fail_fast(self):
        pipeline = ActionPipeline(continue_on_error=False)
        plan = Plan("test", "s")
        plan.add_step("a", command="echo a")
        plan.add_step("b", command="definitely-not-a-cmd")
        commands = {1: "echo a", 2: "definitely-not-a-cmd"}
        results = pipeline.execute(self.intent, plan, commands)
        self.assertEqual(len(results), 2)
        self.assertFalse(results[-1].success)

    def test_continue_on_error(self):
        pipeline = ActionPipeline(continue_on_error=True)
        plan = Plan("test", "s")
        plan.add_step("a", command="echo a")
        plan.add_step("b", command="bad-cmd-xyz")
        commands = {1: "echo a", 2: "bad-cmd-xyz"}
        results = pipeline.execute(self.intent, plan, commands)
        self.assertEqual(len(results), 2)
        self.assertFalse(_last_success(results))

    def test_verify_all_success(self):
        pipeline = ActionPipeline()
        ok = [ActionResult.ok("a"), ActionResult.ok("b")]
        self.assertTrue(pipeline.verify(ok))

    def test_verify_one_fail(self):
        pipeline = ActionPipeline()
        mixed = [ActionResult.ok("a"), ActionResult.fail("boom")]
        self.assertFalse(pipeline.verify(mixed))

    def test_verify_empty(self):
        pipeline = ActionPipeline()
        self.assertFalse(pipeline.verify([]))

    def test_no_plan_no_results(self):
        pipeline = ActionPipeline()
        self.assertEqual(pipeline.execute(self.intent, None, {}), [])


def _last_success(results):
    return results[-1].success


if __name__ == "__main__":
    unittest.main()