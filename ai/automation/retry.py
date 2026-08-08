"""SaktiAI — Automation Retry Analysis (Phase 5).

Looks at a failed step and decides whether it can be retried once with
a concrete fix. Every fix must map onto a real, safe adjustment:

- tool missing        -> install the tool, then retry
- npm peer conflict   -> retry with --legacy-peer-deps
- command timed out   -> one plain retry (the first run may have
                         stalled on cold caches / locks)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from ..core.types import ActionResult
from .planner import AutomationStep

_KNOWN_TOOLS = ("git", "docker", "opencode", "node", "npm", "python",
                "pip", "composer", "code", "php")

_NOT_FOUND = re.compile(
    r"(?:command\s+not\s+found|not\s+recognized\s+as\s+an\s+internal|"
    r"no\s+such\s+file|is\s+not\s+installed)", re.I)

_TIMED_OUT = re.compile(
    r"(?:timed?\s*out|timeout|operation\s+took\s+too\s+long|"
    r"timed out)", re.I)

_PEER_CONFLICT = re.compile(r"(?:ERESOLVE|peer\s+dependenc|conflict\s+peer)",
                            re.I)


@dataclass
class RetryPlan:
    """What the engine should do after a failed step."""

    retry: bool = False
    reason: str = ""
    command: str = ""                 # adjusted command to run
    install_tool: Optional[str] = None  # tool to install before retry
    steps: List[str] = field(default_factory=list)  # human-readable plan

    @property
    def summary(self) -> str:
        if not self.retry:
            return "no retry"
        return " -> ".join(self.steps) if self.steps else self.reason


class RetryAnalyzer:
    """Classifies one failure into a single safe retry (or none)."""

    def __init__(self) -> None:
        self.max_retries: int = 1

    # ------------------------------------------------------------ api
    def analyze(self, step: AutomationStep,
                result: ActionResult) -> RetryPlan:
        text = f"{result.stdout or ''}\n{result.stderr or ''}"
        exit_code = result.exit_code

        # 1) tool missing -> install it, then retry the step
        if _NOT_FOUND.search(text):
            tool = self._missing_tool(text)
            if tool:
                return RetryPlan(
                    retry=True, reason=f"tool '{tool}' not found",
                    install_tool=tool,
                    command=self._drop_sudo_prefix(step.command),
                    steps=[f"install {tool}", "retry the step"])
            return RetryPlan(retry=False, reason="unknown missing tool")

        # 2) npm peer-dependency conflict -> legacy flags
        if _PEER_CONFLICT.search(text) and step.command:
            adjusted = step.command + " --legacy-peer-deps"
            return RetryPlan(
                retry=True, reason="npm peer dependency conflict",
                command=adjusted,
                steps=["retry with --legacy-peer-deps"])

        # 3) timeout -> one plain retry
        if _TIMED_OUT.search(text) or exit_code in (-2, 124):
            return RetryPlan(
                retry=True, reason=f"command timed out (exit {exit_code})",
                command=step.command,
                steps=["retry once"])

        return RetryPlan(retry=False, reason="not retryable")

    # -------------------------------------------------------- helpers
    def _missing_tool(self, text: str) -> Optional[str]:
        for tool in _KNOWN_TOOLS:
            if re.search(rf"\b{tool}\b", text, re.I):
                return tool
        return None

    @staticmethod
    def _drop_sudo_prefix(command: str) -> str:
        return re.sub(r"^\s*sudo\s+", "", command).strip()