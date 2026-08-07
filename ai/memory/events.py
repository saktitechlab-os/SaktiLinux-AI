"""SaktiAI — MemoryBus.

An in-process pub/sub bus for memory events (used as a notification channel
so the desktop shell, voice, and other components can react to memory
updates without tight coupling).
"""

from __future__ import annotations

import threading
from typing import Callable, Dict, List

Handler = Callable[[str, str, object], None]  # (namespace, key, value)


class MemoryBus:
    """Tiny typed event bus. Namespace-scoped subscriptions."""

    def __init__(self) -> None:
        self._handlers: Dict[str, List[Handler]] = {}
        self._lock = threading.RLock()

    def subscribe(self, namespace: str, handler: Handler) -> None:
        with self._lock:
            self._handlers.setdefault(namespace, []).append(handler)

    def unsubscribe(self, namespace: str, handler: Handler) -> None:
        with self._lock:
            handlers = self._handlers.get(namespace)
            if handlers and handler in handlers:
                handlers.remove(handler)

    def publish(self, namespace: str, key: str, value: object) -> None:
        with self._lock:
            targets = list(self._handlers.get(namespace, []))
        for handler in targets:
            try:
                handler(namespace, key, value)
            except Exception:  # keep the bus resilient
                continue

    def subscribers(self, namespace: str) -> int:
        with self._lock:
            return len(self._handlers.get(namespace, []))