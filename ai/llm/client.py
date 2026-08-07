"""SaktiAI — LLMClient.

Minimal OpenAI-compatible chat client. Talks to any endpoint that exposes
the `/v1/chat/completions` shape (local Ollama / llama.cpp, or a cloud
provider via the provider manager). Kept dependency-free using urllib so
the core stays installable without extra packages.

Usage
-----
    client = LLMClient(base_url="http://localhost:11434/v1")
    reply = client.complete("tell me a joke", temperature=0.5)
"""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from typing import Dict, List, Optional

LOG = logging.getLogger(__name__)


class LLMClient:
    """Small OpenAI-compatible chat client (stdlib only)."""

    def __init__(self, model: str, base_url: str,
                 api_key: str = "", timeout_seconds: float = 60.0) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout_seconds

    # ---------------------------------------------------------- public
    def complete(self, prompt: str, system: str = "",
                 temperature: float = 0.7, max_tokens: int = 512) -> str:
        messages: List[Dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        return self.chat(messages, temperature=temperature,
                         max_tokens=max_tokens)

    def chat(self, messages: List[Dict[str, str]],
             temperature: float = 0.7, max_tokens: int = 512) -> str:
        body = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        data = self._post("/v1/chat/completions", body)
        if data is None:
            return ""
        try:
            return data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError) as exc:
            LOG.warning("unexpected LLM response shape: %s", exc)
            return ""

    # ------------------------------------------------------ transport
    def _post(self, path: str, body: dict) -> Optional[dict]:
        url = self.base_url + path
        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers=self._headers(),
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.load(resp)
        except (urllib.error.URLError, OSError, ValueError) as exc:
            LOG.warning("LLM call failed for %s: %s", self.model, exc)
            return None

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers