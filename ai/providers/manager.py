"""SaktiAI — ProviderManager.

Registry + factory for AI providers. Holds a config (JSON file) of
enabled providers, knows how to activate the best available one, and
returns the active provider for a given purpose (chat / planner / voice).

Config lives at `~/.config/sakti/providers.json` by default.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Dict, Optional

from .base import Provider
from .ollama import OllamaProvider

LOG = logging.getLogger(__name__)

BUILTIN_PROVIDERS = {
    "ollama": OllamaProvider,
}


def default_config_path() -> str:
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(
        os.path.expanduser("~"), ".config")
    return os.path.join(base, "sakti", "providers.json")


class ProviderManager:
    """Registry + activation for AI providers."""

    def __init__(self, config_path: Optional[str] = None) -> None:
        self._config_path = config_path or default_config_path()
        self._providers: Dict[str, Provider] = {}
        self._active: Dict[str, str] = {}  # purpose -> provider name
        self._load()

    # ----------------------------------------------------------- io
    def _load_config(self) -> Dict[str, object]:
        try:
            import json
            with open(self._config_path, encoding="utf-8") as fh:
                return json.load(fh)
        except (OSError, ValueError):
            return {}

    def _load(self) -> None:
        cfg = self._load_config()
        enabled = cfg.get("enabled", []) or ["ollama"]
        for name in enabled:
            self.register(name, cfg.get("providers", {}).get(name))
        active = cfg.get("active", {})
        self._active = {"chat": active.get("chat", "ollama")}

    # -------------------------------------------------- registration
    def register(self, name: str, config: Optional[Dict[str, str]] = None
                 ) -> bool:
        factory = BUILTIN_PROVIDERS.get(name)
        if not factory:
            LOG.warning("unknown provider: %s", name)
            return False
        try:
            self._providers[name] = factory(config or {})
            return True
        except Exception as exc:
            LOG.error("failed to load provider %s: %s", name, exc)
            return False

    def available_providers(self) -> list:
        return [p.name for p in self._providers.values()
                if p.available()]

    def provider(self, purpose: str = "chat",
                 prefer_available: bool = True) -> Optional[Provider]:
        """Return the provider to use for `purpose`, or None."""
        target = self._active.get(purpose) or self._active.get("chat")
        if not target:
            target = next(iter(self._providers), None)
        provider = self._providers.get(target or "")
        if provider is None:
            return None
        if prefer_available and not provider.available():
            LOG.info("preferred provider %s unavailable", target)
            for name, cand in self._providers.items():
                if cand.available():
                    return cand
            return None
        return provider

    def set_active(self, purpose: str, name: str) -> None:
        if name in self._providers:
            self._active[purpose] = name