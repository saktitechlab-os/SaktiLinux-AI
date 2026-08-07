"""SaktiAI — WakeWord.

Detects a wake phrase ("hey sakti") using a lightweight configurable
matcher. Intended to gate the voice engine so it only listens after a
wake word (like other smart assistants). Real audio detection can be
plugged in later; the default is a text-based matcher used by the CLI
and the desktop shell for testing.
"""

from __future__ import annotations

import re
from typing import List, Optional


class WakeWord:
    """Matches user text against configured wake phrases."""

    def __init__(self, phrases: Optional[List[str]] = None) -> None:
        self.phrases = phrases or ["hey sakti", "ok sakti",
                                   "sakti", "sakti listen"]

    def detect(self, text: str) -> Optional[str]:
        """Return the matched phrase or None."""
        lowered = text.lower().strip()
        for phrase in self.phrases:
            if phrase in lowered:
                return phrase
        return None

    def is_active(self, text: str) -> bool:
        return self.detect(text) is not None