"""SaktiAI — MemoryStore.

A persistent JSON-backed store with namespaces for the things the OS
should remember: recent commands, projects, preferences, history, and
pinned items.

Design
------
- Single file: `~/.local/share/sakti/memory.json` (XDG_DATA_HOME aware).
- Thread-safe via a lock; atomic writes via temp-file + rename.
- Supports read / write / update / delete per key per namespace.
- Namespaces are validated against a fixed schema (no arbitrary keys).
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
import threading
import time
from typing import Any, Dict, List, Optional

LOG = logging.getLogger(__name__)

DEFAULT_NAMESPACES = {
    "history": "List of past natural-language requests.",
    "recent_commands": "Recently executed shell commands.",
    "projects": "Known projects and their metadata.",
    "preferences": "Long-term user preferences (IDE, mode, accent...).",
    "pinned": "Pinned files / projects / workspaces.",
    "workspaces": "Saved workspaces.",
}


def default_memory_path() -> str:
    base = os.environ.get("XDG_DATA_HOME") or os.path.join(
        os.path.expanduser("~"), ".local", "share")
    return os.path.join(base, "sakti", "memory.json")


class MemoryStore:
    """Persistent, schema-validated key/value + log memory."""

    def __init__(self, path: Optional[str] = None,
                 namespaces: Optional[Dict[str, str]] = None) -> None:
        self._path = path or default_memory_path()
        self._namespaces = dict(namespaces or DEFAULT_NAMESPACES)
        self._lock = threading.RLock()
        self._data: Dict[str, Dict[str, Any]] = {}
        self._load()

    # ---------------------------------------------------------- io
    def _load(self) -> None:
        os.makedirs(os.path.dirname(self._path), exist_ok=True)
        if not os.path.exists(self._path):
            self._data = {ns: {} for ns in self._namespaces}
            self._flush()
            return
        try:
            import json
            with open(self._path, encoding="utf-8") as fh:
                loaded = json.load(fh)
            self._data = {ns: loaded.get(ns, {}) for ns in self._namespaces}
        except (OSError, ValueError) as exc:
            LOG.warning("memory load failed (%s); starting fresh", exc)
            self._data = {ns: {} for ns in self._namespaces}

    def _flush(self) -> None:
        import json
        os.makedirs(os.path.dirname(self._path), exist_ok=True)
        fd, tmp = tempfile.mkstemp(
            dir=os.path.dirname(self._path), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(self._data, fh, indent=2)
            os.replace(tmp, self._path)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    def _namespace(self, namespace: str) -> dict:
        if namespace not in self._data:
            raise KeyError(f"unknown namespace: {namespace}")
        return self._data[namespace]

    # ------------------------------------------------------ CRUD
    def read(self, namespace: str, key: str) -> Optional[Any]:
        with self._lock:
            return self._namespace(namespace).get(key)

    def write(self, namespace: str, key: str, value: Any) -> None:
        self.update(namespace, key, value)

    def update(self, namespace: str, key: str, value: Any) -> None:
        with self._lock:
            self._namespace(namespace)[key] = value
            self._flush()

    def delete(self, namespace: str, key: str) -> bool:
        with self._lock:
            ns = self._namespace(namespace)
            existed = key in ns
            if existed:
                del ns[key]
                self._flush()
            return existed

    def list(self, namespace: str) -> Dict[str, Any]:
        with self._lock:
            return dict(self._namespace(namespace))

    # -------------------------------------------------------- convenience
    def add_history(self, request: str) -> None:
        self._append_log("history", request)

    def add_recent_command(self, command: str) -> None:
        self._append_log("recent_commands", command)

    def remember_project(self, name: str, metadata: Dict[str, Any]) -> None:
        existing = self.read("projects", name) or {}
        merged = {**existing, **metadata, "updated_at": time.time()}
        self.update("projects", name, merged)

    def set_preference(self, key: str, value: Any) -> None:
        self.update("preferences", key, value)

    def get_preference(self, key: str, default: Any = None) -> Any:
        return self.read("preferences", key) or default

    def recent_history(self, limit: int = 10) -> List[str]:
        with self._lock:
            items = self._data["history"].get("entries", [])
        return [e.get("value") for e in items][-limit:]

    def recent_commands(self, limit: int = 10) -> List[str]:
        with self._lock:
            items = self._data["recent_commands"].get("entries", [])
        return [e.get("value") for e in items][-limit:]

    # ----------------------------------------------------------- internal
    def _append_log(self, namespace: str, entry: Any, cap: int = 200) -> None:
        with self._lock:
            ns = self._namespace(namespace)
            entries = ns.get("entries", [])
            entries.append({"ts": time.time(), "value": entry})
            ns["entries"] = entries[-cap:]
            self._flush()

    def wipe(self) -> None:
        with self._lock:
            self._data = {ns: {} for ns in self._namespaces}
            self._flush()