"""SaktiAI — LLMRegistry.

Keeps track of known model endpoints so the brain can later route to a
recommended model per task (planning vs. chat vs. embeddings). Read-only
catalogue; actual selection lives in the provider manager / brain.
"""

from __future__ import annotations

from typing import Dict, List


class LLMRegistry:
    """Catalogue of known models and their capabilities."""

    # name -> {provider, endpoint-hint, purpose}
    KNOWN: Dict[str, Dict[str, str]] = {
        "llama3.2": {"provider": "ollama", "endpoint": "http://localhost:11434/v1",
                     "purpose": "chat + planning"},
        "mistral": {"provider": "ollama", "endpoint": "http://localhost:11434/v1",
                    "purpose": "chat"},
        "deepseek-r1": {"provider": "ollama", "endpoint": "http://localhost:11434/v1",
                        "purpose": "reasoning"},
    }

    def __init__(self) -> None:
        self._models = dict(self.KNOWN)

    def register(self, model_id: str, provider: str, endpoint: str,
                 purpose: str = "chat") -> None:
        self._models[model_id] = {
            "provider": provider, "endpoint": endpoint, "purpose": purpose,
        }

    def get(self, model_id: str) -> Dict[str, str]:
        return self._models.get(model_id, {})

    def list(self) -> List[str]:
        return list(self._models)

    def by_purpose(self, purpose: str) -> List[str]:
        return [m for m, spec in self._models.items()
                if spec.get("purpose") == purpose]