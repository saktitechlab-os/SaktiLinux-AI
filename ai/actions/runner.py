"""SaktiAI — CommandRunner.

Executes a single shell command with a timeout and captures stdout,
stderr, and exit code. Safe-by-default: supports dry-run mode and never
executes empty commands.

Uses `subprocess` with `creationflags`/`shell` handling so it works on
both POSIX and Windows hosts.
"""

from __future__ import annotations

import logging
import subprocess
import sys
from typing import Optional, Tuple

from ..core.types import ActionResult

LOG = logging.getLogger(__name__)


class CommandRunner:
    """Runs commands, returns ActionResult. Never raises on failure."""

    def __init__(self, timeout_seconds: float = 30.0,
                 shell: Optional[bool] = None) -> None:
        self.timeout = timeout_seconds
        self._shell = shell if shell is not None else (sys.platform == "win32")

    def run(self, command: str, dry_run: bool = False,
            cwd: Optional[str] = None) -> ActionResult:
        if not command:
            return ActionResult.fail("empty command", exit_code=-1)
        if dry_run:
            LOG.info("DRY-RUN: %s", command)
            return ActionResult(exit_code=0, stdout=f"[dry-run] {command}",
                                stderr="", success=True, dry_run=True)
        LOG.info("EXEC: %s", command)
        try:
            proc = subprocess.run(
                command,
                shell=self._shell,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=cwd,
            )
            ok = proc.returncode == 0
            return ActionResult(
                exit_code=proc.returncode,
                stdout=(proc.stdout or "").strip(),
                stderr=(proc.stderr or "").strip(),
                success=ok,
                dry_run=False,
            )
        except subprocess.TimeoutExpired:
            return ActionResult.fail(
                f"timeout after {self.timeout}s", exit_code=-2)
        except OSError as exc:
            return ActionResult.fail(f"os error: {exc}", exit_code=-3)