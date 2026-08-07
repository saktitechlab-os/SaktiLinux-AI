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
from threading import Thread
from typing import Callable, Optional

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

    def run_live(self, command: str,
                 on_line: Optional[Callable[[str, str], None]] = None,
                 cwd: Optional[str] = None,
                 timeout: Optional[float] = None) -> ActionResult:
        """Stream a command's output line-by-line as it is produced.

        `on_line(text, stream)` is called for every line of both stdout and
        stderr (`stream` in {"out", "err"}). Output is also aggregated and
        returned in the ActionResult (like `run`). The process is killed if
        it does not finish within `timeout` (defaults to the runner timeout).
        """
        if not command:
            return ActionResult.fail("empty command", exit_code=-1)
        limit = timeout if timeout is not None else self.timeout
        LOG.info("LIVE: %s", command)
        lines_out: list[str] = []
        lines_err: list[str] = []

        def _sink(stream: str):
            def _pump(fh):
                for raw in fh:
                    line = raw.rstrip("\r\n")
                    (lines_out if stream == "out" else lines_err).append(line)
                    if on_line:
                        on_line(line, stream)
                if on_line:
                    on_line("", stream)
                fh.close()
            return _pump

        try:
            proc = subprocess.Popen(
                command,
                shell=self._shell,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                cwd=cwd,
            )
        except OSError as exc:
            return ActionResult.fail(f"os error: {exc}", exit_code=-3)

        t_out = Thread(target=_sink("out"), args=(proc.stdout,), daemon=True)
        t_err = Thread(target=_sink("err"), args=(proc.stderr,), daemon=True)
        t_out.start()
        t_err.start()

        try:
            exit_code = proc.wait(timeout=limit)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            t_out.join(timeout=2)
            t_err.join(timeout=2)
            return ActionResult(
                exit_code=-2,
                stdout="\n".join(lines_out).strip(),
                stderr="timeout after {}s\n{}".format(
                    limit, "\n".join(lines_err).strip()).strip(),
                success=False,
                dry_run=False,
            )

        t_out.join(timeout=2)
        t_err.join(timeout=2)
        return ActionResult(
            exit_code=exit_code,
            stdout="\n".join(lines_out).strip(),
            stderr="\n".join(lines_err).strip(),
            success=exit_code == 0,
            dry_run=False,
        )