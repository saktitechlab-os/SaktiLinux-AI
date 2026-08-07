"""SaktiAI — ContextEngine.

Senses live system context used to make the brain context-aware:

    active app            (via Wayland / WM heuristics, best-effort)
    CPU / RAM usage       (psutil when available)
    current directory     (cwd of the caller, or shell env)
    current project       (git-root detection from cwd)
    internet status       (fast connectivity probe, cached)

Deliberately dependency-light: `psutil` is optional; everything else is
stdlib + subprocess. All probes degrade gracefully and never raise.
"""

from __future__ import annotations

import logging
import os
import shutil
import socket
import subprocess
import threading
import time
from dataclasses import dataclass
from typing import Optional

from ..core.types import ContextSnapshot

LOG = logging.getLogger(__name__)


class ContextEngine:
    """Captures a ContextSnapshot. Safe to call frequently."""

    def __init__(self, cwd: Optional[str] = None,
                 timeout_ms: int = 800) -> None:
        self._cwd = cwd or os.getcwd()
        self._timeout = timeout_ms / 1000.0
        self._internet_cache: dict = {"at": 0.0, "value": False}

    # ---------------------------------------------------------- capture
    def capture(self) -> ContextSnapshot:
        return ContextSnapshot(
            cwd=self._cwd,
            username=self._user(),
            os_name=self._os_name(),
            cpu_percent=self._cpu(),
            mem_percent=self._memory(),
            active_app=self._active_app(),
            active_project=self._git_project(self._cwd),
            internet=self._internet(),
        )

    # ----------------------------------------------------------- probes
    @staticmethod
    def _user() -> str:
        try:
            return os.environ.get("USER") or os.environ.get("USERNAME") or ""
        except Exception:
            return ""

    @staticmethod
    def _os_name() -> str:
        try:
            if os.name == "nt":
                return "windows"
            if shutil.which("uname"):
                out = subprocess.run(["uname", "-sr"], capture_output=True,
                                     text=True, timeout=3)
                return out.stdout.strip() or "linux"
            return "linux"
        except Exception:
            return "linux"

    @staticmethod
    def _cpu() -> float:
        try:
            import psutil  # optional
            return float(psutil.cpu_percent(interval=0.05))
        except Exception:
            return 0.0

    @staticmethod
    def _memory() -> float:
        try:
            import psutil  # optional
            return float(psutil.virtual_memory().percent)
        except Exception:
            return 0.0

    @staticmethod
    def _active_app() -> str:
        """Best-effort active app via KDE/KWin or X11 heuristics."""
        try:
            if os.name != "nt" and shutil.which("qdbus"):
                out = subprocess.run(
                    ["qdbus", "org.kde.KWin", "/KWin", "activeWindow"],
                    capture_output=True, text=True, timeout=3)
                if out.returncode == 0 and out.stdout.strip():
                    return out.stdout.strip()
        except Exception:
            pass
        return ""

    @staticmethod
    def _git_project(cwd: str) -> str:
        """Find nearest git root name (project detection)."""
        d = os.path.abspath(cwd)
        while True:
            if os.path.isdir(os.path.join(d, ".git")):
                return os.path.basename(d)
            parent = os.path.dirname(d)
            if parent == d:
                return ""
            d = parent

    def _internet(self) -> bool:
        now = time.time()
        if now - self._internet_cache["at"] < 15:  # 15s cache
            return self._internet_cache["value"]
        value = self._probe_internet()
        self._internet_cache = {"at": now, "value": value}
        return value

    def _probe_internet(self) -> bool:
        """Fast dual-stack UDP/TCP probe; no DNS dependency."""
        try:
            with socket.create_connection(("1.1.1.1", 53),
                                          timeout=self._timeout):
                return True
        except OSError:
            try:
                with socket.create_connection(("8.8.8.8", 53),
                                              timeout=self._timeout):
                    return True
            except OSError:
                return False