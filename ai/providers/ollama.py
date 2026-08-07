"""SaktiAI — Ollama provider.

Connects to a local Ollama server (default http://localhost:11434) with
an OpenAI-compatible client. This is the default local provider so Sakti
works offline-first.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from ..llm.client import LLMClient
from .base import Provider

DEFAULT_ENDPOINT = "http://localhost:11434/v1"
DEFAULT_MODEL = "llama3.2"


class OllamaProvider(Provider):
    name = "ollama"

    def __init__(self, config: Optional[Dict[str, str]] = None,
                 model: str = DEFAULT_MODEL) -> None:
        super().__init__(config)
        base_url = self.config.get("endpoint", DEFAULT_ENDPOINT)
        self.model = self.config.get("model", model)
        self._client = LLMClient(model=self.model, base_url=base_url)

    # ---------------------------------------------------------- api
    def complete(self, prompt: str, system: str = "",
                 **kwargs) -> str:
        return self._client.complete(prompt, system=system, **kwargs)

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        return self._client.chat(messages, **kwargs)

    # -------------------------------------------------- availability
    def available(self) -> bool:
        try:
            import socket
            host, port = (self._client.base_url.replace("http://", "")
                          .split("/")[0].split(":"))
            with socket.create_connection((host, int(port)), timeout=2):
                return True
        except Exception:
            return False

    def models(self) -> List[str]:
        return [self.model]