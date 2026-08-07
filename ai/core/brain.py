"""SaktiAI — central orchestrator (the Brain).

Receives user input and routes it through the pipeline:

    input -> intent -> context -> planner -> command
          -> action pipeline -> memory -> response

The Brain is the single entry point used by the CLI, the desktop sidebar
(Phase 2), and the voice engine. All collaborators are injected (Dependency
Inversion) so tests can stub any stage.

Behaviour contract:
- `process()` ALWAYS returns an ExecutionReport with a non-empty `message`.
- No silent failures: exceptions are caught, logged, and surfaced in the
  report message.
- Debug lines are printed to stdout so the CLI shows what the brain did.
- If Ollama is registered but unreachable, the report says so clearly.
- If the AI pipeline cannot produce a result, a basic fallback response
  is returned.
"""

from __future__ import annotations

import logging
import time
import traceback
from typing import Dict, Optional

from .intent import IntentClassifier
from .types import ExecutionReport, Intent, ContextSnapshot

LOG = logging.getLogger(__name__)

# Pure-chat intents: never translated to commands, answered conversationally.
_CHAT_KINDS = {"general"}

FALLBACK_MESSAGE = (
    "SaktiAI is running but could not complete that request. "
    "Try 'install docker', 'create a react app', or 'scan network'."
)


def _debug(*parts) -> None:
    """Debug output for CLI visibility (never silent)."""
    print("[sakti]", *parts, flush=True)


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
        """Full pipeline run for one user request. Never raises."""
        _debug("SaktiBrain started; request:", repr(text)[:80])
        report = ExecutionReport()
        try:
            self._pipeline(report, text, snapshot, dry_run)
        except Exception as exc:  # noqa: BLE001 - must never die silently
            LOG.exception("brain pipeline crashed")
            report.message = (f"ERROR: {exc}\n"
                              f"traceback:\n{traceback.format_exc()}")
            _debug("BRAIN ERROR:", exc)
            if not report.message:
                report.message = FALLBACK_MESSAGE
        return report

    # ----------------------------------------------------------- stages
    def _pipeline(self, report: ExecutionReport, text: str,
                  snapshot: Optional[ContextSnapshot],
                  dry_run: bool) -> None:
        # 1. Intent
        report.intent = self.classifier.classify(text)
        _debug("intent detected:", report.intent.kind.value,
               f"(confidence={report.intent.confidence:.2f})")

        # 2. Context
        if self.context_engine is not None:
            report.context = snapshot or self.context_engine.capture()
        else:
            report.context = snapshot or ContextSnapshot()
        _debug("context: cwd=", report.context.cwd or "(none)",
               "project=", report.context.active_project or "(none)")

        # 2b. Chat-like intents: answer directly, no command execution.
        if report.intent.kind.value in _CHAT_KINDS:
            report.message = self._chat_reply(report.intent)
            report.finished_at = time.time()
            _debug("chat reply:", report.message[:80])
            return

        # 3. Plan
        if self.planner is not None:
            report.plan = self.planner.plan(report.intent, report.context)
            _debug(f"plan: {len(report.plan.steps)} step(s)")
            for step in report.plan.steps:
                _debug(f"  step {step.order}: {step.description} "
                       f"-> {step.command or '(no command)'}")
        else:
            report.message = (f"Understood intent: "
                              f"{report.intent.kind.value}, but no planner "
                              f"is attached.")
            report.finished_at = time.time()
            return

        # 4. Commands
        commands: Dict[int, str] = {}
        if self.command_engine is not None:
            commands = self.command_engine.translate(report.plan,
                                                     report.context)
            _debug("commands translated:",
                   {k: (v or "(blocked/empty)") for k, v in commands.items()})

        # 5. Execute
        if self.action_pipeline is not None:
            report.results = self.action_pipeline.execute(
                report.intent, report.plan, commands, dry_run=dry_run)
            report.verified = self.action_pipeline.verify(report.results)
            _debug(f"execution: {len(report.results)} result(s), "
                   f"verified={report.verified}")
            for result in report.results:
                _debug("  result:", "OK" if result.success else "FAIL",
                       "exit=", result.exit_code,
                       result.stdout[:60] if result.stdout else "")

        # 6. Memory
        if self.memory_store is not None:
            self._remember(report)

        report.finished_at = time.time()
        report.message = self._summarize(report)
        _debug("final message:", report.message[:120])

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
    def _chat_reply(self, intent: Intent) -> str:
        return (
            "Hello! I'm SaktiAI, your Linux AI assistant. "
            "I can install apps, create projects, scan networks, organize "
            "files, deploy sites, and more. "
            "Try something like: 'install docker', 'create a react app', "
            "or 'scan network'."
        )

    def _summarize(self, report: ExecutionReport) -> str:
        if not report.plan:
            return (f"Understood intent: "
                    f"{report.intent.kind.value if report.intent else '?'} "
                    f"(no planner attached).")
        if report.verified:
            return (f"Completed {len(report.results)} step(s) successfully "
                    f"in {round(report.duration_ms, 1)} ms.")
        blocked = [i + 1 for i, r in enumerate(report.results)
                   if not r.success]
        return (f"Executed {len(report.results)} step(s); "
                f"{len(blocked)} failed or blocked (steps "
                f"{blocked or 'none'}). Dry-run={report.results[0].dry_run if report.results else False}. "
                f"Run with --verbose for details.")

    def status(self) -> Dict[str, object]:
        """Health/status payload for UIs and the desktop sidebar."""
        llm_ok = False
        if self.provider_manager is not None:
            try:
                llm_ok = bool(self.provider_manager.available_providers())
            except Exception:
                llm_ok = False
        return {
            "engine": "sakti-brain",
            "version": __import__("ai", fromlist=["__version__"]).__version__,
            "ready": True,
            "ollama_running": llm_ok,
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