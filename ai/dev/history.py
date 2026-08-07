"""SaktiAI — Developer command history (Phase 4A UX).

Persistent, capped log of executed developer commands with timestamps
and success/failure status. Like MemoryStore, it is a JSON file, written
atomically; the newest `limit` (default 50) entries are retained.

Each entry:
    id          monotonic integer (safe to replay after trimming)
    timestamp   ISO-8601 wall-clock of execution
    ts          epoch seconds (float) for sorting
    command     the full command line that ran
    action      run / install / build / replay
    cwd         project directory it ran in
    status      "success" | "fail" | "dry-run"
    exit_code   process exit code (0 on success)

    store = DevHistory()
    store.add(command="npm install x", action="install", cwd="/p")
    entries = store.list()       # newest first, at most `limit`
    entry = store.get(entry_id)
"""

from __future__ import annotations

import json
import os
import tempfile
import threading
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

LOG = __import__("logging").getLogger(__name__)

DEFAULT_LIMIT = 50

STATUS_SUCCESS = "success"
STATUS_FAIL = "fail"
STATUS_DRY = "dry-run"


def default_history_path() -> str:
    base = os.environ.get("XDG_DATA_HOME") or os.path.join(
        os.path.expanduser("~"), ".local", "share")
    return os.path.join(base, "sakti", "dev_history.json")


class DevHistory:
    """Persistent, capped log of dev commands."""

    def __init__(self, path: Optional[str] = None,
                 limit: int = DEFAULT_LIMIT) -> None:
        self._path = path or default_history_path()
        self._limit = max(1, int(limit))
        self._lock = threading.RLock()
        self._entries: List[Dict[str, Any]] = []
        self._counter = 1
        self._load()

    # ---------------------------------------------------------- io
    def _load(self) -> None:
        if not os.path.exists(self._path):
            self._flush()
            return
        try:
            with open(self._path, encoding="utf-8") as fh:
                data = json.load(fh)
            self._entries = list(data.get("entries") or [])
            self._counter = int(data.get("counter") or 1)
        except (OSError, ValueError) as exc:
            LOG.warning("dev history load failed (%s); starting fresh", exc)
            self._entries = []
            self._counter = 1

    def _flush(self) -> None:
        os.makedirs(os.path.dirname(self._path), exist_ok=True)
        fd, tmp = tempfile.mkstemp(
            dir=os.path.dirname(self._path), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump({"counter": self._counter,
                           "entries": self._entries}, fh, indent=2,
                          ensure_ascii=False)
            os.replace(tmp, self._path)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    # ---------------------------------------------------------- api
    def add(self, command: str, action: str, cwd: str,
            status: str, exit_code: int) -> int:
        """Append an entry, trim to limit, return its id."""
        with self._lock:
            entry_id = self._counter
            self._counter += 1
            entry = {
                "id": entry_id,
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "ts": round(time.time(), 3),
                "command": command,
                "action": action,
                "cwd": cwd or "",
                "status": status,
                "exit_code": int(exit_code or 0),
            }
            self._entries.append(entry)
            if len(self._entries) > self._limit:
                del self._entries[: len(self._entries) - self._limit]
            self._flush()
            return entry_id

    def list(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Newest-first entries (capped to the store limit)."""
        with self._lock:
            entries = list(self._entries)
        entries.reverse()
        if limit is not None:
            entries = entries[: max(0, int(limit))]
        return entries

    def get(self, entry_id: int) -> Optional[Dict[str, Any]]:
        with self._lock:
            for entry in self._entries:
                if entry.get("id") == entry_id:
                    return dict(entry)
        return None

    def clear(self) -> None:
        with self._lock:
            self._entries = []
            self._flush()

    def __len__(self) -> int:
        with self._lock:
            return len(self._entries)