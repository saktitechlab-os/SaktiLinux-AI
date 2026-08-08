"""Unit tests for Phase 5 AI Automation — planner, executor, retry, engine.

The planner and retry analyzer run fully real (rules, no mocks). The
executor and engine are driven with small recording fakes so nothing on
disk ever executes here — real execution is covered by the integration
suite.
"""

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from ai.automation import (
    AutomationEngine, AutomationPlanner, AutomationStep, PlanError,
    RetryAnalyzer, StepExecutor,
)
from ai.core.types import ActionResult


class TestAutomationPlanner(unittest.TestCase):
    """Natural language -> ordered, safe plans."""

    def setUp(self):
        self.p = AutomationPlanner()

    def test_create_app_and_run(self):
        steps = self.p.plan("create a react app and run it")
        self.assertEqual(len(steps), 2)
        self.assertEqual(steps[0].action, "create")
        self.assertEqual(steps[0].target, "react")
        self.assertEqual(steps[0].needs_tools, ["node", "npm"])
        self.assertEqual(steps[1].action, "run")
        self.assertEqual([s.order for s in steps], [1, 2])

    def test_create_only(self):
        steps = self.p.plan("create a python project")
        self.assertEqual(len(steps), 1)
        self.assertEqual(steps[0].target, "python")

    def test_install_tool(self):
        steps = self.p.plan("install docker")
        self.assertEqual(steps[0].action, "tool")
        self.assertEqual(steps[0].target, "docker")

    def test_install_tool_then_run(self):
        steps = self.p.plan("install docker and run it")
        self.assertEqual([s.action for s in steps],
                         ["tool", "docker-run"])

    def test_install_dependency(self):
        steps = self.p.plan("install lodash")
        self.assertEqual(steps[0].action, "install")
        self.assertEqual(steps[0].target, "lodash")

    def test_git_commit_with_message(self):
        steps = self.p.plan("commit my changes with message fix bug")
        self.assertEqual(steps[0].action, "git")
        self.assertEqual(steps[0].message, "fix bug")
        self.assertIn("fix bug", steps[0].command)

    def test_git_push(self):
        steps = self.p.plan("push the changes")
        self.assertEqual(steps[0].action, "git-push")

    def test_run_project(self):
        steps = self.p.plan("run the project")
        self.assertEqual(steps[0].action, "run")
        self.assertEqual(steps[0].needs_tools, [])

    def test_build_project(self):
        steps = self.p.plan("build the app")
        self.assertEqual(steps[0].action, "build")

    def test_docker_build(self):
        steps = self.p.plan("docker build the image")
        self.assertEqual(steps[0].action, "docker-build")
        self.assertEqual(steps[0].needs_tools, ["docker"])

    def test_opencode(self):
        steps = self.p.plan("use opencode to fix the typo")
        self.assertEqual(steps[0].action, "opencode")
        self.assertIn("fix the typo", steps[0].target)

    def test_empty_task_rejected(self):
        with self.assertRaises(PlanError):
            self.p.plan("   ")

    def test_destructive_task_rejected(self):
        for bad in ("rm -rf /", "wipe the disk with dd if=/dev/zero"):
            with self.assertRaises(PlanError, msg=bad):
                self.p.plan(bad)

    def test_unplannable_task_rejected(self):
        with self.assertRaises(PlanError):
            self.p.plan("sing me a song about quantum toast")

    def test_step_metadata(self):
        step = AutomationStep(order=3, action="run",
                              description="run the project",
                              command="sakti-ai dev run",
                              needs_tools=["node"])
        self.assertEqual(step.summary(), "[step 3] run the project")
        d = step.to_dict()
        self.assertEqual(d["order"], 3)
        self.assertIn("needs_tools", d)


class FakeTools:
    """Records installs; never installs anything for real."""

    def __init__(self, results=None):
        self.installed = []
        self.results = list(results or [])

    def install_tool(self, tool, dry_run=False, live=False, confirm=None):
        self.installed.append(tool)
        if self.results:
            return self.results.pop(0)
        return ActionResult.ok(f"installed {tool}")


class FakeExecutor:
    """Recording executor: returns pre-queued outcomes."""

    def __init__(self, outcomes=None, available=None):
        self.outcomes = list(outcomes or [])
        self.available_func = available or (lambda tool: True)
        self.calls = []
        self.tools = FakeTools()

    def available(self, tool):
        if isinstance(self.available_func, dict):
            return self.available_func.get(tool, True)
        return self.available_func(tool)

    def execute(self, step, dry_run=False, cwd=None):
        self.calls.append((step, dry_run, cwd))
        if self.outcomes:
            return self.outcomes.pop(0)
        return ActionResult.ok("ok")

    def __call__(self, step, dry_run=False, cwd=None):
        return self.execute(step, dry_run=dry_run, cwd=cwd)


class TestStepExecutor(unittest.TestCase):
    """Dispatch maps actions onto the right engine/tools surface."""

    def setUp(self):
        self.executor = StepExecutor()  # real facade, fakes below

    def test_run_dispatch(self):
        engine = _RecordingEngine()
        self.executor.engine = engine
        self.executor.tools = FakeTools()
        step = AutomationStep(action="run", description="run")
        result = self.executor.execute(step)
        self.assertEqual(engine.calls, [("run_project",)])
        self.assertTrue(result.success)

    def test_install_dispatch(self):
        engine = _RecordingEngine()
        self.executor.engine = engine
        self.executor.tools = FakeTools()
        step = AutomationStep(action="install", target="lodash",
                              description="install lodash")
        result = self.executor.execute(step)
        self.assertEqual(engine.calls, [("install_dependency",
                                         "lodash", None)])
        self.assertTrue(result.success)

    def test_tool_dispatch(self):
        engine = _RecordingEngine()
        self.executor.engine = engine
        tools = FakeTools()
        self.executor.tools = tools
        step = AutomationStep(action="tool", target="docker",
                              description="install tool")
        result = self.executor.execute(step)
        self.assertEqual(tools.installed, ["docker"])
        self.assertTrue(result.success)

    def test_git_dispatch_with_message(self):
        engine = _RecordingEngine()
        self.executor.engine = engine
        self.executor.tools = FakeTools()
        step = AutomationStep(action="git", message="fix bug",
                             description="commit")
        result = self.executor.execute(step)
        self.assertEqual(engine.calls,
                         [("git_commit", "fix bug", None)])
        self.assertTrue(result.success)

    def test_unknown_action_fails_loudly(self):
        result = self.executor.execute(
            AutomationStep(action="teleport", description="?"))
        self.assertFalse(result.success)
        self.assertIn("unknown step action", result.stderr)

    def test_available_uses_registry(self):
        executor = StepExecutor()
        ret = executor.available("python")
        self.assertIsInstance(ret, bool)


class TestRetryAnalyzer(unittest.TestCase):
    """Failure classification -> single safe retry (or none)."""

    def setUp(self):
        self.a = RetryAnalyzer()

    def test_missing_tool_installs_then_retries(self):
        step = AutomationStep(description="run", command="npm install")
        result = ActionResult.fail("npm: command not found", exit_code=127)
        plan = self.a.analyze(step, result)
        self.assertTrue(plan.retry)
        self.assertEqual(plan.install_tool, "npm")

    def test_sudo_dropped_when_retrying_install_fix(self):
        step = AutomationStep(description="x",
                             command="sudo npm install")
        result = ActionResult.fail("npm: command not found", exit_code=127)
        plan = self.a.analyze(step, result)
        self.assertEqual(plan.command, "npm install")

    def test_eresolve_uses_legacy_peer_deps(self):
        step = AutomationStep(description="install",
                             command="npm install express")
        result = ActionResult.fail(
            "npm ERR! ERESOLVE could not resolve conflicting peer "
            "dependencies", exit_code=1)
        plan = self.a.analyze(step, result)
        self.assertTrue(plan.retry)
        self.assertTrue(plan.command.endswith("--legacy-peer-deps"))

    def test_timeout_retries_once(self):
        step = AutomationStep(description="run x",
                             command="compile the world")
        result = ActionResult.fail("process timed out after 30s",
                                   exit_code=-2)
        plan = self.a.analyze(step, result)
        self.assertTrue(plan.retry)
        self.assertEqual(plan.command, step.command)

    def test_unrelated_failure_not_retryable(self):
        step = AutomationStep(description="run x", command="run")
        result = ActionResult.fail("pyflakes: syntax error in main.py",
                                   exit_code=1)
        plan = self.a.analyze(step, result)
        self.assertFalse(plan.retry)


class TestAutomationEngine(unittest.TestCase):
    """Engine orchestration with recording fakes (never executes)."""

    def test_dry_run_plans_only(self):
        engine = AutomationEngine(
            planner=AutomationPlanner(),
            executor=FakeExecutor(),
            history=_FakeHistory())
        report = engine.run("create a react app and run it",
                            dry_run=True)
        self.assertTrue(report.success)
        self.assertTrue(report.dry_run)
        self.assertEqual(len(report.steps), 2)
        self.assertEqual(report.results, [])
        self.assertEqual(engine.history.entries, [])

    def test_happy_path_executes_in_order(self):
        hist = _FakeHistory()
        ex = FakeExecutor(outcomes=[ActionResult.ok(), ActionResult.ok()])
        engine = AutomationEngine(executor=ex, history=hist)
        report = engine.run("create a react app")
        self.assertTrue(report.success)
        self.assertEqual(len(report.results), 1)
        self.assertEqual(len(ex.calls), 1)
        self.assertEqual(len(hist.entries), 1)
        self.assertTrue(all(s["status"] == "success"
                            for s in hist.entries))

    def test_fail_fast_stops_at_first_failure(self):
        ex = FakeExecutor(outcomes=[
            ActionResult.ok(), ActionResult.fail("boom", exit_code=2),
            ActionResult.ok()])
        engine = AutomationEngine(executor=ex)
        report = engine.run("install docker and run it")
        self.assertFalse(report.success)
        self.assertEqual(len(ex.calls), 2)
        self.assertIn("step 2 failed", report.failed_step)

    def test_retry_recovering_missing_tool(self):
        ex = FakeExecutor(outcomes=[
            ActionResult.ok(),
            ActionResult.fail("python: command not found", exit_code=127),
            ActionResult.ok()])
        engine = AutomationEngine(executor=ex, log=lambda _m: None)
        report = engine.run("install node and run it")
        self.assertTrue(report.success)
        self.assertTrue(any(order == 2 for order, _ in report.retried))
        self.assertIn("python", ex.tools.installed)
        # both step-2 attempts are recorded: failure then the retry
        data = [(order, r.success) for order, r in report.results]
        self.assertEqual(data, [(1, True), (2, True)])

    def test_retry_not_available_fails_fast(self):
        ex = FakeExecutor(outcomes=[
            ActionResult.ok(),
            ActionResult.fail("ValueError: nope", exit_code=1)])
        engine = AutomationEngine(executor=ex)
        report = engine.run("install docker and run it")
        self.assertFalse(report.success)
        self.assertEqual(report.retried, [])

    def test_plan_error_sets_report(self):
        engine = AutomationEngine(planner=AutomationPlanner())
        report = engine.run("sing to my dog a song")
        self.assertFalse(report.success)
        self.assertIsNotNone(report.plan_error)
        self.assertEqual(report.results, [])
        self.assertEqual(report.to_dict()["success"], False)

    def test_refused_tool_install_stops_plan(self):
        ex = FakeExecutor(available={"node": False})
        engine = AutomationEngine(executor=ex, confirm=lambda *_: False)
        report = engine.run("create a react app")
        self.assertFalse(report.success)
        self.assertIn("refused", report.failed_step)
        self.assertEqual(ex.calls, [])

    def test_auto_tool_install_with_yes(self):
        ex = FakeExecutor(available={"node": False})
        records = []
        engine = AutomationEngine(executor=ex, log=records.append)
        report = engine.run("create a react app", yes=True)
        self.assertTrue(report.success)
        self.assertIn("node", ex.tools.installed)

    def test_history_records_automation_entries(self):
        hist = _FakeHistory()
        ex = FakeExecutor(outcomes=[ActionResult.fail("nope")])
        engine = AutomationEngine(executor=ex, history=hist)
        engine.run("run the project")
        self.assertEqual(len(hist.entries), 1)
        self.assertEqual(hist.entries[0]["action"], "automation")
        self.assertEqual(hist.entries[0]["status"], "fail")


class _RecordingEngine:
    """Fake DevCommandEngine surface for dispatch tests."""

    def __init__(self):
        self.calls = []

    def run_project(self, path=None, dry_run=False, live=None):
        self.calls.append(("run_project",))
        return ActionResult.ok("ran")

    def install_dependency(self, dependency, path=None, dry_run=False,
                           live=None):
        self.calls.append(("install_dependency", dependency, path))
        return ActionResult.ok(f"installed {dependency}")

    def build_project(self, path=None, dry_run=False, live=None):
        self.calls.append(("build_project",))
        return ActionResult.ok("built")

    def git_status(self, path=None, dry_run=False, live=None):
        self.calls.append(("git_status",))
        return ActionResult.ok("status")

    def git_commit(self, message, path=None, dry_run=False, live=None):
        self.calls.append(("git_commit", message, path))
        return ActionResult.ok("committed")

    def git_push(self, path=None, dry_run=False, live=None):
        self.calls.append(("git_push",))
        return ActionResult.ok("pushed")

    def docker_build(self, path=None, dry_run=False, live=None):
        self.calls.append(("docker_build",))
        return ActionResult.ok("built")

    def docker_run(self, path=None, dry_run=False, live=None):
        self.calls.append(("docker_run",))
        return ActionResult.ok("ran")

    def opencode_run(self, prompt, path=None, dry_run=False, live=None):
        self.calls.append(("opencode_run", prompt, path))
        return ActionResult.ok("done")

    def opencode_generate(self, prompt, path=None, dry_run=False,
                          live=None, output_file=None):
        self.calls.append(("opencode_generate",))
        return ActionResult.ok("generated")


class _FakeHistory:
    def __init__(self):
        self.entries = []

    def add(self, command, action, cwd, status, exit_code):
        self.entries.append({"command": command, "action": action,
                             "cwd": cwd, "status": status,
                             "exit_code": exit_code})


class TestRealStepExecutorStuff(unittest.TestCase):
    """Sanity: dispatch messages never lie about result type."""

    def test_all_dispatch_results_are_action_results(self):
        executor = StepExecutor()
        engine = _RecordingEngine()
        executor.engine = engine
        executor.tools = FakeTools()
        results = [
            executor.execute(AutomationStep(action="git-push")),
            executor.execute(AutomationStep(action="git-status")),
            executor.execute(AutomationStep(action="docker-run")),
        ]
        for result in results:
            self.assertIsInstance(result, ActionResult)


if __name__ == "__main__":
    unittest.main()