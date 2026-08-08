"""SaktiAI — Automation Step Executor (Phase 5).

Dispatches one `AutomationStep` onto the real execution surfaces:

- `tool`       -> ToolManager.install_tool
- `install`    -> DevCommandEngine.install_dependency
- `create`     -> scaffold command via CommandRunner (npx create-*)
- `run/build`  -> DevCommandEngine.run_project / build_project
- `git*`       -> DevCommandEngine.git_*
- `docker-*`   -> DevCommandEngine.docker_*
- `opencode`   -> DevCommandEngine.opencode_run

Everything is real: no fake success, no dry-run shortcuts when the
caller asked for execution.
"""

from __future__ import annotations

from typing import Optional

from ..actions.runner import CommandRunner
from ..core.types import ActionResult
from ..dev.engine import DevCommandEngine
from ..tools.manager import ToolManager
from .planner import AutomationStep


class StepExecutor:
    """Runs a planned step against the real engine/tool stack."""

    def __init__(self, engine: Optional[DevCommandEngine] = None,
                 tools: Optional[ToolManager] = None,
                 runner: Optional[CommandRunner] = None) -> None:
        self.engine = engine or DevCommandEngine()
        self.tools = tools or ToolManager()
        self.runner = runner or CommandRunner()

    # ------------------------------------------------------------ api
    def execute(self, step: AutomationStep,
                dry_run: bool = False,
                cwd: Optional[str] = None) -> ActionResult:
        path = step.path or cwd
        action = step.action
        if action == "tool":
            return self.tools.install_tool(step.target, dry_run=dry_run)
        if action == "install":
            return self.engine.install_dependency(
                step.target, path=path, dry_run=dry_run)
        if action == "create" and step.command:
            return self.runner.run(step.command, cwd=cwd, dry_run=dry_run)
        if action == "run":
            return self.engine.run_project(path=path, dry_run=dry_run)
        if action == "build":
            return self.engine.build_project(path=path, dry_run=dry_run)
        if action == "git":
            return self.engine.git_commit(
                step.message or "automated commit", path=path,
                dry_run=dry_run)
        if action == "git-push":
            return self.engine.git_push(path=path, dry_run=dry_run)
        if action == "git-status":
            return self.engine.git_status(path=path, dry_run=dry_run)
        if action == "docker-build":
            return self.engine.docker_build(path=path, dry_run=dry_run)
        if action == "docker-run":
            return self.engine.docker_run(path=path, dry_run=dry_run)
        if action == "opencode":
            return self.engine.opencode_run(
                step.target or "fulfil the task", path=path,
                dry_run=dry_run)
        return ActionResult.fail(
            f"unknown step action '{action}' — nothing executed",
            exit_code=-1)

    # -------------------------------------------------------- helpers
    def available(self, tool: str) -> bool:
        """Best-effort availability check (registry, then PATH)."""
        try:
            if self.tools.registry.is_installed(tool):
                return True
        except Exception:
            pass
        import shutil
        return shutil.which(tool) is not None