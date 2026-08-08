"""SaktiAI — Automation Engine (Phase 5).

Turns one natural-language task into an ordered plan and executes it
to completion: plan -> tool readiness -> execute step by step
(fail-fast) -> single smart retry on failure -> live logs -> history
records.

`run(task, dry_run=True)` plans without touching the system.
"""

from __future__ import annotations

import dataclasses
import time
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Tuple

from ..core.types import ActionResult
from ..dev.history import DevHistory, STATUS_FAIL, STATUS_SUCCESS
from .executor import StepExecutor
from .planner import AutomationPlanner, AutomationStep, PlanError
from .retry import RetryAnalyzer, RetryPlan

LogFn = Callable[[str], None]


@dataclass
class AutomationReport:
    """Outcome of one `AutomationEngine.run(...)` call."""

    task: str = ""
    steps: List[dict] = field(default_factory=list)
    results: List[Tuple[int, ActionResult]] = field(default_factory=list)
    success: bool = False
    dry_run: bool = False
    plan_error: Optional[str] = None
    retried: List[Tuple[int, str]] = field(default_factory=list)
    started_at: float = field(default_factory=time.time)
    finished_at: Optional[float] = None

    @property
    def elapsed_ms(self) -> float:
        end = self.finished_at or time.time()
        return round((end - self.started_at) * 1000.0, 2)

    @property
    def failed_step(self) -> Optional[str]:
        for order, result in self.results:
            if not result.success:
                return f"step {order} failed: {result.stderr[:240]}"
        return None

    def to_dict(self) -> dict:
        return {
            "task": self.task,
            "steps": self.steps,
            "results": [(order, result.success, result.exit_code,
                         result.stdout[:160], result.stderr[:240])
                        for order, result in self.results],
            "success": self.success,
            "dry_run": self.dry_run,
            "plan_error": self.plan_error,
            "retried": self.retried,
            "elapsed_ms": self.elapsed_ms,
        }


class AutomationEngine:
    """Planner -> tool readiness -> execute -> retry -> report."""

    def __init__(self,
                 planner: Optional[AutomationPlanner] = None,
                 executor: Optional[StepExecutor] = None,
                 analyzer: Optional[RetryAnalyzer] = None,
                 confirm: Optional[Callable[[str, str], bool]] = None,
                 history: Optional[DevHistory] = None,
                 log: Optional[LogFn] = None) -> None:
        self.planner = planner or AutomationPlanner()
        self.executor = executor or StepExecutor()
        self.analyzer = analyzer or RetryAnalyzer()
        self.confirm = confirm
        self.history = history
        self.log = log or (lambda _msg: None)

    # ------------------------------------------------------------ api
    def run(self, task: str, dry_run: bool = False,
            yes: bool = False,
            cwd: Optional[str] = None) -> AutomationReport:
        report = AutomationReport(task=task, dry_run=dry_run)
        try:
            steps = self.planner.plan(task)
        except PlanError as exc:
            report.plan_error = str(exc)
            report.finished_at = time.time()
            return report

        report.steps = [s.to_dict() for s in steps]
        self._log(f"Planned {len(steps)} step(s) for: {task}")
        for step in steps:
            self._log(f"  {step.summary()}"
                      f"{'  (dry run)' if dry_run else ''}")

        if dry_run:
            report.success = True
            report.finished_at = time.time()
            return report

        for step in steps:
            self._log(f"[run] {step.summary()}")
            if not self._ensure_tools(step, yes=yes):
                report.results.append(
                    (step.order,
                     self._fail(f"missing tool(s) {step.needs_tools} and "
                                f"refused to install")))
                report.finished_at = time.time()
                return report

            result = self.executor.execute(step, cwd=cwd)
            self._record(step, result)
            if result.success:
                report.results.append((step.order, result))
                continue

            plan = self.analyzer.analyze(step, result)
            if not plan.retry or result.dry_run:
                report.results.append((step.order, result))
                report.finished_at = time.time()
                return report

            self._log(f"    [retry] {plan.summary}")
            report.retried.append((step.order, plan.reason))
            if plan.install_tool:
                self.executor.tools.install_tool(plan.install_tool)
            retry_step = (self._restep(step, plan)
                          if plan.command else step)
            retried = self.executor.execute(retry_step, cwd=cwd)
            self._record(step, retried)
            report.results.append((step.order, retried))
            if retried.success:
                continue

            report.results.append((step.order, result))
            report.finished_at = time.time()
            return report

        report.success = True
        report.finished_at = time.time()
        return report

    # ------------------------------------------------------ internals
    def _ensure_tools(self, step: AutomationStep, yes: bool) -> bool:
        for tool in step.needs_tools:
            if self.executor.available(tool):
                continue
            self._log(f"    [tool] '{tool}' missing — installing")
            command = f"sakti-ai tools install {tool}"
            if not yes and self.confirm is not None \
                    and not self.confirm(tool, command):
                return False
            result = self.executor.tools.install_tool(tool)
            if not result.success:
                return False
        return True

    @staticmethod
    def _restep(step: AutomationStep, plan: RetryPlan) -> AutomationStep:
        return dataclasses.replace(step, command=plan.command)

    def _record(self, step: AutomationStep, result: ActionResult) -> None:
        if self.history is None:
            return
        self.history.add(
            command=step.command or step.description,
            action="automation",
            cwd=step.path or "",
            status=STATUS_SUCCESS if result.success else STATUS_FAIL,
            exit_code=result.exit_code)

    @staticmethod
    def _fail(reason: str) -> ActionResult:
        return ActionResult.fail(reason, exit_code=-3)

    def _log(self, message: str) -> None:
        self.log(message)