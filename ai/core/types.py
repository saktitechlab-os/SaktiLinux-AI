"""SaktiAI — domain types.

Immutable-ish dataclasses shared across the AI stack. Kept dependency-free
so every layer (memory, planner, actions, voice, providers) talks the same
language.
"""

from __future__ import annotations

import dataclasses
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class IntentKind(str, Enum):
    """High-level intents the classifier can recognise."""

    INSTALL = "install"            # install an application / tool
    CREATE = "create"              # scaffold a project
    BUILD = "build"                # compile/build Android/app/project
    DEPLOY = "deploy"              # deploy website or service
    SCAN_NETWORK = "scan_network"  # cyber reconnaissance
    ORGANIZE = "organize"          # file/directory housekeeping
    SEARCH = "search"              # ai search across files/web
    RUN = "run"                    # launch/run an app or command
    SYSTEM = "system"              # system status/info
    GENERAL = "general"            # free-form natural language


@dataclass
class Intent:
    """Parsed user intent."""

    kind: IntentKind
    raw: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kind": self.kind.value,
            "raw": self.raw,
            "parameters": self.parameters,
            "confidence": self.confidence,
        }


@dataclass
class Step:
    """A single planned action."""

    order: int
    description: str
    command: str = ""
    validator: Optional[str] = None  # name of policy needed
    expected: str = ""               # what "success" looks like

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)


@dataclass
class Plan:
    """Decomposed task as an ordered list of steps."""

    intent: str
    summary: str
    steps: List[Step] = field(default_factory=list)

    def add_step(self, description: str, command: str = "",
                 validator: Optional[str] = None, expected: str = "") -> None:
        self.steps.append(Step(len(self.steps) + 1, description,
                               command, validator, expected))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "intent": self.intent,
            "summary": self.summary,
            "steps": [s.to_dict() for s in self.steps],
        }


@dataclass
class ContextSnapshot:
    """Live system context sensed at request time."""

    cwd: str = ""
    username: str = ""
    os_name: str = ""
    cpu_percent: float = 0.0
    mem_percent: float = 0.0
    active_app: str = ""
    active_project: str = ""
    internet: bool = False
    captured_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)


@dataclass
class ActionResult:
    """Outcome of a single executed step."""

    exit_code: int
    stdout: str
    stderr: str
    success: bool
    dry_run: bool = False

    @classmethod
    def ok(cls, stdout: str = "", exit_code: int = 0) -> "ActionResult":
        return cls(exit_code=exit_code, stdout=stdout, stderr="",
                   success=True, dry_run=False)

    @classmethod
    def fail(cls, stderr: str, exit_code: int = 1) -> "ActionResult":
        return cls(exit_code=exit_code, stdout="", stderr=stderr,
                   success=False, dry_run=False)


@dataclass
class ExecutionReport:
    """Full report of the understand -> ... -> report pipeline."""

    intent: Optional[Intent] = None
    plan: Optional[Plan] = None
    context: Optional[ContextSnapshot] = None
    results: List[ActionResult] = field(default_factory=list)
    verified: bool = False
    message: str = ""
    started_at: float = field(default_factory=time.time)
    finished_at: Optional[float] = None

    @property
    def duration_ms(self) -> float:
        end = self.finished_at or time.time()
        return (end - self.started_at) * 1000.0

    @property
    def all_ok(self) -> bool:
        return bool(self.results) and all(r.success for r in self.results)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "intent": self.intent.to_dict() if self.intent else None,
            "plan": self.plan.to_dict() if self.plan else None,
            "context": self.context.to_dict() if self.context else None,
            "results": [dataclasses.asdict(r) for r in self.results],
            "verified": self.verified,
            "message": self.message,
            "all_ok": self.all_ok,
            "elapsed_ms": round(self.duration_ms, 2),
        }