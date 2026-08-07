"""SaktiAI — Provider base class.

Interface every AI provider (ollama, openai, anthropic, local llama.cpp)
must implement so the brain can swap backends transparently.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class Provider(ABC):
    """Abstract AI provider contract."""

    name: str = "base"

    def __init__(self, config: Optional[Dict[str, str]] = None) -> None:
        self.config = dict(config or {})

    # --------------------------------------------------- required
    @abstractmethod
    def complete(self, prompt: str, system: str = "",
                 **kwargs) -> str:
        """Single completion for a prompt."""

    @abstractmethod
    def available(self) -> bool:
        """True if this provider can serve requests right now."""

    # --------------------------------------------------- optional
    def models(self) -> List[str]:
        """List of model ids this provider exposes."""
        return []

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        raise NotImplementedError

    def transcribe(self, audio_path: str) -> str:
        raise NotImplementedError

    def embed(self, text: str) -> List[float]:
        raise NotImplementedError