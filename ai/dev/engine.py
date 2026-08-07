"""SaktiAI — Developer Command Engine (Phase 4A).

Real, on-disk command execution for developer workflows. Given a
project (detected by DevContextDetector) it:

- runs the project's dev server / entrypoint        (run_project)
- installs a dependency with the right tool          (install_dependency)
- runs the project's build step                      (build_project)

Only three ecosystems are supported (Node.js, Python, PHP) — anything
else yields a clear "unsupported" result. Execution is delegated to the
existing CommandRunner (real subprocesses; never a dry-run).

    engine = DevCommandEngine()
    result = engine.run_project(path="~/code/myapp")     # npm run dev...
    result = engine.install_dependency("lodash", path="~/code/myapp")
    result = engine.build_project(path="~/code/myapp")
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List, Optional

from ..actions.runner import CommandRunner
from ..core.types import ActionResult
from .detector import DevContext, DevContextDetector


def _python_cmd(*parts: str) -> str:
    py = getattr(sys, "executable", None) or "python"
    return " ".join([py, *parts])


def _pm_run(pm: str, script: str) -> str:
    return f"{pm} run {script}" if pm in ("npm", "pnpm") else f"{pm} {script}"


class DevCommandEngine:
    """Detects projects and executes developer commands for real."""

    def __init__(self, detector: Optional[DevContextDetector] = None,
                 runner: Optional[CommandRunner] = None) -> None:
        self.detector = detector or DevContextDetector()
        self.runner = runner or CommandRunner()

    # ------------------------------------------------------------ api
    def status(self, path: Optional[str] = None) -> DevContext:
        return self.detector.detect(path)

    def run_project(self, path: Optional[str] = None,
                    script: Optional[str] = None,
                    args: Optional[str] = None) -> ActionResult:
        ctx = self.detector.detect(path)
        if not ctx.detected:
            return _unsupported(ctx, "run")
        command, label = self._run_command(ctx, script, args)
        return self._execute(ctx, "run", label, [command])

    def install_dependency(self, dependency: str,
                           path: Optional[str] = None,
                           manager: Optional[str] = None) -> ActionResult:
        if not dependency or not dependency.strip():
            return ActionResult.fail("no dependency name given", exit_code=-1)
        ctx = self.detector.detect(path)
        if not ctx.detected:
            return _unsupported(ctx, "install")
        pm = manager or ctx.package_manager or "npm"
        if ctx.project_type == "python" and manager is None:
            base = _python_cmd("-m", "pip", "install")
        else:
            base = _command_install(pm)
        if not base:
            return ActionResult.fail(
                f"no installer known for package manager '{pm}'", exit_code=-1)
        return self._execute(ctx, "install", f"install {dependency}",
                             [f"{base} {dependency}"])

    def build_project(self, path: Optional[str] = None) -> ActionResult:
        ctx = self.detector.detect(path)
        if not ctx.detected:
            return _unsupported(ctx, "build")
        command, label = self._build_command(ctx)
        return self._execute(ctx, "build", label, [command])

    # ------------------------------------------------------- commands
    def _run_command(self, ctx: DevContext, script: Optional[str],
                     args: Optional[str]) -> tuple[str, str]:
        pm = ctx.package_manager
        if script:
            cmd = _pm_run(pm, script)
            return f"{cmd}{(' ' + args) if args else ''}", script
        if ctx.project_type == "node":
            if ctx.scripts.get("dev"):
                return (_pm_run(pm, "dev") + (f" {args}" if args else ""),
                        "dev script")
            return f"node index.js{(' ' + args) if args else ''}", "node entry"
        if ctx.project_type == "python":
            entry = self._python_entry(ctx)
            return f"{entry}{(' ' + args) if args else ''}", entry
        if ctx.project_type == "php":
            return "php -S 127.0.0.1:8000", "php built-in server"
        return "echo no run command", "unknown"

    def _python_entry(self, ctx: DevContext) -> str:
        for candidate in ("manage.py", "main.py", "app.py", "run.py",
                          "server.py"):
            if (Path(ctx.root) / candidate).exists():
                return _python_cmd(candidate)
        if ctx.package_manager in ("poetry", "uv") and ctx.name:
            return _python_cmd("-m", ctx.name)
        return _python_cmd("main.py")

    def _build_command(self, ctx: DevContext) -> tuple[str, str]:
        pm = ctx.package_manager
        if ctx.project_type == "node":
            if ctx.scripts.get("build"):
                return _pm_run(pm, "build"), "build script"
            return "npm run build", "npm build (default)"
        if ctx.project_type == "python":
            return _python_cmd("-m", "compileall", "-q", "."), \
                "python compileall"
        if ctx.project_type == "php":
            return "composer install --no-dev --optimize-autoloader", \
                "composer build (deps)"
        return "echo no build command", "unknown"

    # --------------------------------------------------------- execute
    def _execute(self, ctx: DevContext, action: str, label: str,
                 commands: List[str]) -> ActionResult:
        cwd = ctx.root
        if not commands or not commands[0]:
            return ActionResult.fail(
                f"no command available to {action} this project", exit_code=-1)
        command = commands[0]
        result = self.runner.run(command, cwd=cwd)
        result.stdout = f"[{action}] {label}\n{result.stdout}".strip() \
            if result.stdout else f"[{action}] {label}: (no output)"
        return result


def _command_install(pm: str) -> str:
    return _command_install_map.get(pm, "npm install")


_command_install_map: Dict[str, str] = {
    "npm": "npm install", "yarn": "yarn add", "pnpm": "pnpm add",
    "bun": "bun add", "pip": "pip install", "poetry": "poetry add",
    "uv": "uv add", "composer": "composer require",
}


def _unsupported(ctx: DevContext, action: str) -> ActionResult:
    return ActionResult.fail(
        f"cannot {action}: no supported project found "
        f"(expected Node.js, Python, or PHP) in {ctx.root or '(cwd)'}",
        exit_code=-1)