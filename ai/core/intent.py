"""SaktiAI — intent classification.

Rule-based natural-language classifier that maps user text onto
`IntentKind` with parameters and a confidence score. Kept pluggable so a
local LLM (Phase-3 llm/ and provider manager) can later rank candidates.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional

from .types import Intent, IntentKind

# (regex, kind, [param-name])  -- first match wins, ordered
_PATTERNS: List[tuple] = [
    (r"\binstal+l?\b.+?(\S+)", IntentKind.INSTALL, ["target"]),
    (r"\bcreate\b.+?(react|next|vue|node|android|flutter|rust|python|portfolio)\b",
     IntentKind.CREATE, ["stack"]),
    (r"\b(deploy|publish|upload)\b", IntentKind.DEPLOY, []),
    (r"\bscan\b.*\b(network|wifi|ports?)\b", IntentKind.SCAN_NETWORK, []),
    (r"\borg(anize|anize)?\s+downloads\b", IntentKind.ORGANIZE, []),
    (r"\bsearch\b", IntentKind.SEARCH, []),
    (r"\brun\b.+?", IntentKind.RUN, ["target"]),
    (r"\b(status|info|system info|how fast|uptime)\b", IntentKind.SYSTEM, []),
]

_REACT_PROJECT = re.compile(r"\b(react|next|vue)\b", re.I)


class IntentClassifier:
    """Maps free text onto an Intent."""

    def __init__(self) -> None:
        self._patterns = _PATTERNS

    def classify(self, text: str) -> Intent:
        lowered = text.lower().strip()
        for regex, kind, _params in self._patterns:
            match = re.search(regex, lowered)
            if match:
                params: Dict[str, object] = {}
                if kind is IntentKind.CREATE and _REACT_PROJECT.search(lowered):
                    params["stack"] = "react"
                    params["framework"] = "react"
                if kind is IntentKind.INSTALL and len(match.groups()):
                    params["target"] = match.group(1).strip()
                return Intent(kind=kind, raw=text,
                              parameters=params, confidence=0.7)
        return Intent(kind=IntentKind.GENERAL, raw=text,
                      parameters={}, confidence=0.3)

    # Future: rank alternative intents when an LLM provider is plugged in.
    def candidates(self, text: str, top: int = 3) -> List[Intent]:
        return [self.classify(text)]

    def supported_kinds(self) -> List[str]:
        return [k.value for k in IntentKind]