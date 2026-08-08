"""SaktiAI — Automation Planner (Phase 5).

Turns a single natural-language task into an ordered, executable plan.
Each step maps onto a real dev/tool command (run, install, build, git,
docker, opencode, tool install) and declares the tools it needs so the
engine can auto-install missing ones (with confirmation).

Rule-based routing over the intent classifier; extensible so an LLM
planner can slot in later.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from ..core.intent import IntentClassifier

_TOOLS = ("git", "docker", "opencode", "node", "npm", "python",
          "pip", "composer", "code", "php")

_NODE_TOOLS = ["node", "npm"]

_UNSAFE = re.compile(
    r"(?:rm\s+-rf\s+(?:[/~]|[^\s:])|mkfs|format\s+\w:|dd\s+if=|"
    r"shutdown|reboot|:\(\)\s*\{|curl[^\n]*\|\s*sh|wget[^\n]*\|\s*sh)",
    re.I)


@dataclass
class AutomationStep:
    """One unit of work in an automation plan."""

    order: int = 0
    action: str = "run"              # run|install|build|git|git-push|
                                     # git-status|docker-build|docker-run|
                                     # opencode|tool|create
    description: str = ""
    command: str = ""                # headline command for display
    target: str = ""                 # dependency / tool / image name
    needs_tools: List[str] = field(default_factory=list)
    path: Optional[str] = None       # workdir
    message: Optional[str] = None    # e.g. git commit message

    def summary(self) -> str:
        return f"[step {self.order}] {self.description}"

    def to_dict(self) -> dict:
        return {"order": self.order, "action": self.action,
                "description": self.description, "command": self.command,
                "target": self.target, "needs_tools": list(self.needs_tools),
                "path": self.path, "message": self.message}


class PlanError(Exception):
    """Task could not be turned into an executable plan."""


class AutomationPlanner:
    """Rule-based planner: one user instruction -> ordered steps."""

    def __init__(self, classifier: Optional[IntentClassifier] = None) -> None:
        self.classifier = classifier or IntentClassifier()

    # ------------------------------------------------------------ api
    def plan(self, task: str) -> List[AutomationStep]:
        task = (task or "").strip()
        if not task:
            raise PlanError("refusing to plan an empty task")
        if _UNSAFE.search(task):
            raise PlanError(
                "refusing to plan that task: destructive command pattern "
                "detected")
        steps = self._route(task)
        if not steps:
            raise PlanError(
                f"could not plan '{task[:60]}' — try e.g. "
                f"'create a react app and run it'")
        for i, step in enumerate(steps, start=1):
            step.order = i
        return steps

    # ---------------------------------------------------------- route
    def _route(self, task: str) -> List[AutomationStep]:
        lowered = task.lower()
        intent = self.classifier.classify(task)
        kind = intent.kind.value

        # 1) install something
        if re.search(r"\binstall\b", lowered):
            tool = self._tool_in(lowered)
            if tool:
                steps = [AutomationStep(
                    action="tool", description=f"install the {tool} tool",
                    command=f"sakti-ai tools install {tool}", target=tool)]
                rest = lowered.replace(f" {tool}", " ", 1)
                if re.search(r"\b(?:run|start|serve|launch)\b", rest):
                    steps.append(AutomationStep(
                        description="start the service",
                        action="docker-run" if tool == "docker" else "run",
                        command=("sakti-ai dev docker run"
                                 if tool == "docker"
                                 else "sakti-ai dev run")))
                return steps
            if kind in ("install_dependency", "install"):
                dep = (intent.parameters.get("dependency")
                       or self._dep_of(lowered))
                if dep and dep not in _TOOLS:
                    return [AutomationStep(
                        action="install",
                        description=f"install the dependency {dep}",
                        command=f"sakti-ai dev install {dep}", target=dep)]
                if dep:
                    return [AutomationStep(
                        action="tool", description=f"install the {dep} tool",
                        command=f"sakti-ai tools install {dep}", target=dep)]

        # 2) create (+run): "create a react app and run it"
        if re.search(r"\b(?:create|make|scaffold|init)\b", lowered):
            stack = self._stack_of(lowered)
            steps = [AutomationStep(
                action="create",
                description=f"scaffold a {stack} project",
                command=f"npx create-{stack}-app@latest . --use-npm",
                target=stack, needs_tools=list(_NODE_TOOLS))]
            if re.search(r"\b(?:and|then|,)?\s*(?:run|start|serve)\b",
                         lowered):
                steps.append(AutomationStep(
                    action="run", description=f"run the {stack} project",
                    command="sakti-ai dev run",
                    needs_tools=list(_NODE_TOOLS)))
            return steps

        # 3) git tasks
        if kind == "git_commit" or re.search(r"\b(?:git|commit|push)\b",
                                             lowered):
            return self._plan_git(intent.parameters, task, lowered)

        # 4) docker tasks
        if "docker" in lowered:
            if re.search(r"\b(?:build|compile)\b", lowered):
                return [AutomationStep(
                    action="docker-build",
                    description="build the docker image",
                    command="sakti-ai dev docker build",
                    needs_tools=["docker"])]
            return [AutomationStep(
                action="docker-run", description="run a docker container",
                command="sakti-ai dev docker run",
                target=self._pkg_of(lowered), needs_tools=["docker"])]

        # 5) opencode
        if "opencode" in lowered:
            return [AutomationStep(
                action="opencode",
                description="run the prompt through opencode",
                command='sakti-ai dev opencode run "<prompt>"',
                target=self._opencode_prompt(task),
                needs_tools=["opencode"])]

        # 6) run / build the current project
        if re.search(r"\b(?:run|start|launch)\b", lowered):
            return [AutomationStep(
                action="run", description="run the project",
                command="sakti-ai dev run")]
        if re.search(r"\b(?:build|compile)\b", lowered):
            return [AutomationStep(
                action="build", description="build the project",
                command="sakti-ai dev build")]

        # 7) fallback
        return []

    # ---------------------------------------------------------- pieces
    def _plan_git(self, params: dict, task: str,
                  lowered: str) -> List[AutomationStep]:
        if "push" in lowered and "commit" not in lowered:
            return [AutomationStep(
                action="git-push", description="push the commits",
                command="sakti-ai dev git push")]
        msg = (self._commit_message(task)
               or params.get("message") or "automated commit")
        return [AutomationStep(
            action="git",
            description=f"git commit with message '{msg}'",
            command=f'sakti-ai dev git commit -m "{msg}"',
            message=msg)]

    def _commit_message(self, task: str) -> str:
        m = re.search(r"message\s*[:'\"]?\s*(.+)$", task, re.I | re.S)
        if m:
            label = m.group(1).strip()
        else:
            m = re.search(r"\b(?:commit|save)\b\s*(?:the\s+|my\s+)?"
                          r"(?:changes|work|code)?\s*(.+)$",
                          task, re.I | re.S)
            label = m.group(1).strip() if m else ""
        label = label.strip("\"'").rstrip(".,!? ")
        return label

    def _tool_in(self, lowered: str) -> Optional[str]:
        m = re.search(r"\binstall(?:\s+the)?\s+(%s)\b" % "|".join(_TOOLS),
                      lowered)
        return m.group(1) if m else None

    def _dep_of(self, lowered: str) -> Optional[str]:
        m = re.search(r"\b(?:install|add)\s+(?:the\s+)?([\w@/.\-]+)",
                      lowered)
        if not m:
            return None
        name = m.group(1).rstrip(".,!?")
        return None if name in _TOOLS else name

    def _pkg_of(self, lowered: str) -> Optional[str]:
        m = re.search(r"\b(?:install|add|use|run|start|open)\s+"
                      r"(?:the\s+|a\s+|an\s+)?"
                      r"(?:container\s+)?([\w.\-/:]+)\b", lowered)
        return m.group(1).rstrip(".,!?") if m else None

    def _stack_of(self, lowered: str) -> str:
        for stack in ("react", "next", "vue", "svelte", "node", "python"):
            if re.search(rf"\b{stack}\b", lowered):
                return stack
        return "react"

    def _opencode_prompt(self, task: str) -> str:
        m = re.search(r"opencode\s+(?:to\s+|and\s+)?(.+)$", task, re.I | re.S)
        return m.group(1).strip().strip("\"") if m else "fulfil the task"