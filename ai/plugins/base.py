"""SaktiAI — Plugin base.

Plugins extend the brain with new commands / intents. A plugin declares
the intents it handles and provides a `handle` callback. The plugin
loader discovers them under `~/.local/share/sakti/plugins/`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Optional

from ..core.types import ActionResult, Intent


class SaktiPlugin(ABC):
    """Base class for Sakti plugins."""

    name: str = "base-plugin"
    version: str = "1.0.0"
    description: str = ""
    intents: tuple = ()  # IntentKind values this plugin handles

    def __init__(self, brain=None) -> None:
        self.brain = brain

    @abstractmethod
    def handle(self, intent: Intent, **kwargs) -> Optional[ActionResult]:
        """Execute this plugin's logic for the given intent."""
        raise NotImplementedError

    def supports(self, intent: Intent) -> bool:
        return intent.kind.value in self.intents

    def metadata(self) -> Dict[str, str]:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "intents": ",".join(self.intents),
        }