"""SaktiAI — AI Automation Engine (Phase 5).

Multi-step task execution from a single natural-language instruction:

    task -> intent -> structured steps -> dependency check ->
    sequential execution (fail-fast) -> smart retry -> history

Modules:
    planner   natural language -> ordered AutomationSteps
    executor  run steps one-by-one against the real engines
    retry     analyze failures and retry once with a fix
    engine    AutomationEngine: plan + deps + execute + report
"""

from .engine import AutomationEngine
from .executor import StepExecutor
from .planner import AutomationPlanner, AutomationStep, PlanError
from .retry import RetryAnalyzer, RetryPlan

__all__ = [
    "AutomationEngine", "AutomationPlanner", "AutomationStep",
    "StepExecutor", "RetryAnalyzer", "RetryPlan", "PlanError",
]