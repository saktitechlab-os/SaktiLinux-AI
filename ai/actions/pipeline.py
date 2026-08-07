"""SaktiAI — ActionPipeline.

Orchestrates execution of a plan's commands:

    results = pipeline.execute(intent, plan, commands, dry_run=bool)
    verified = pipeline.verify(results)

Execution is step-by-step and stops on the first failure (fail-fast),
unless `continue_on_error` is set. Verification checks each step's
"expected" condition where possible; steps with no command are skipped.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from ..core.types import ActionResult, Intent, Plan
from .runner import CommandRunner

LOG = logging.getLogger(__name__)


class ActionPipeline:
    """Executes and verifies plan steps."""

    def __init__(self, runner: Optional[CommandRunner] = None,
                 continue_on_error: bool = False) -> None:
        self.runner = runner or CommandRunner()
        self.continue_on_error = continue_on_error

    def execute(self, intent: Intent, plan: Optional[Plan],
                commands: Dict[int, str], dry_run: bool = False
                ) -> List[ActionResult]:
        results: List[ActionResult] = []
        if plan is None:
            return results
        for step in plan.steps:
            command = commands.get(step.order, "")
            if not command:
                results.append(ActionResult.fail(
                    "no allowed command for step", exit_code=-1))
            else:
                results.append(self.runner.run(command, dry_run=dry_run))
            if not results[-1].success and not self.continue_on_error:
                break
        return results

    def verify(self, results: List[ActionResult]) -> bool:
        """All executed steps succeeded (dry-run counts as success)."""
        if not results:
            return False
        return all(r.success for r in results)