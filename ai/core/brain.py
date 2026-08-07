"""SaktiAI — central orchestrator (the Brain).

Receives user input and routes it through the pipeline:

    input -> intent -> context -> planner -> command
          -> action pipeline -> memory -> response

The Brain is the single entry point used by the CLI, the desktop sidebar
(Phase 2), and the voice engine. All collaborators are injected (Dependency
Inversion) so tests can stub any stage.
"""

from __future__ import annotations

import dataclasses
import logging
import time
from typing import Dict, Optional

from .intent import IntentClassifier
from .types import ExecutionReport, Intent, ContextSnapshot

LOG = logging.getLogger(__name__)


class SaktiBrain:
    """Orchestrates the AI pipeline. Lazy-wires optional stages."""

    def __init__(self,
                 classifier: Optional[IntentClassifier] = None,
                 context_engine=None,
                 planner=None,
                 command_engine=None,
                 action_pipeline=None,
                 memory_store=None,
                 provider_manager=None,
                 llm_manager=None) -> None:
        self.classifier = classifier or IntentClassifier()
        self.context_engine = context_engine
        self.planner = planner
        self.command_engine = command_engine
        self.action_pipeline = action_pipeline
        self.memory_store = memory_store
        self.provider_manager = provider_manager
        self.llm_manager = llm_manager

    # ---------------------------------------------------------- process
    def process(self, text: str, snapshot: Optional[ContextSnapshot] = None,
                dry_run: bool = True) -> ExecutionReport:
        """Full pipeline run for one user request."""
        report = ExecutionReport()
        report.intent = self.classifier.classify(text)

        # Sense context (or accept an injected snapshot).
        if self.context_engine is not None:
            report.context = snapshot or self.context_engine.capture()
        else:
            report.context = snapshot or ContextSnapshot()

        # Plan the task.
        if self.planner is not None:
            report.plan = self.planner.plan(report.intent, report.context)

        # Translate plan steps to concrete commands.
        commands: Dict[int, str] = {}
        if self.command_engine is not None and report.plan is not None:
            commands = self.command_engine.translate(report.plan, report.context)

        # Execute via the action pipeline.
        if self.action_pipeline is not None:
            report.results = self.action_pipeline.execute(
                report.intent, report.plan, commands, dry_run=dry_run)
            report.verified = self.action_pipeline.verify(report.results)

        # Persist memory: remember what we did.
        if self.memory_store is not None:
            self._remember(report)

        report.finished_at = time.time()
        report.message = self._summarize(report)
        return report

    # ----------------------------------------------------------- memory
    def _remember(self, report: ExecutionReport) -> None:
        intent = report.intent
        if intent is None:
            return
        store = self.memory_store
        store.add_history(intent.raw)
        if intent.kind.value in ("install", "create", "deploy"):
            target = (intent.parameters.get("target") or
                      intent.parameters.get("stack") or intent.raw)
            store.remember_project(target, {"intent": intent.kind.value,
                                            "ok": report.all_ok})
        if report.all_ok and report.plan is not None:
            for step in report.plan.steps:
                if step.command:
                    store.add_recent_command(step.command)

    # -------------------------------------------------------- reporting
    @staticmethod
    def _summarize(report: ExecutionReport) -> str:
        if not report.plan:
            return f"Understood intent: {report.intent.kind.value if report.intent else '?'} (no planner attached)."
        if report.verified:
            return (f"Completed {len(report.results)} step(s) successfully "
                    f"in {round(report.duration_ms, 1)} ms.")
        return (f"Executed {len(report.results)} step(s); verification failed "
                f"or dry-run only.")

    def status(self) -> Dict[str, object]:
        """Health/status payload for UIs and the desktop sidebar."""
        return {
            "engine": "sakti-brain",
            "version": __import__("ai", fromlist=["__version__"]).__version__,
            "ready": True,
            "modules": {
                "context": self.context_engine is not None,
                "planner": self.planner is not None,
                "command": self.command_engine is not None,
                "actions": self.action_pipeline is not None,
                "memory": self.memory_store is not None,
                "provider": self.provider_manager is not None,
                "llm": self.llm_manager is not None,
            },
        }