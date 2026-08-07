"""SaktiAI — VoiceEngine.

Speech-to-text + text-to-speech using pluggable backends. Default
backends are built-in file/`say`/`espeak` based so they work offline;
an LLM provider can later supply a higher-quality voice backend.

Hardware integration (phrase = is listening, etc.) is stubbed through
`on_wake`/`on_speech` callbacks so the desktop shell can change its
icon state.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
from typing import Callable, Optional

LOG = logging.getLogger(__name__)


class VoiceEngine:
    """Listens / speaks. Backends auto-detected, never raises."""

    def __init__(self, stt_backend: str = "offline",
                 tts_backend: str = "env") -> None:
        self.stt = stt_backend
        self.tts = tts_backend
        self._listening = False

    # ---------------------------------------------------------- state
    @property
    def listening(self) -> bool:
        return self._listening

    def start(self) -> None:
        self._listening = True
        LOG.info("voice engine started")

    def stop(self) -> None:
        self._listening = False

    # ------------------------------------------------------------ stt
    def hear(self, audio_path: Optional[str] = None) -> str:
        """Transcribe; returns text. Offline backend returns ''."""
        if self.stt != "offline":
            return self._provider_stt(audio_path)
        return ""  # backend not bundled yet

    def _provider_stt(self, audio_path: Optional[str]) -> str:
        # Providers (ai.providers) may register an stt callback.
        from ...providers import ProviderManager
        try:
            pm = ProviderManager()
            provider = pm.provider("voice")
            if provider and hasattr(provider, "transcribe"):
                return provider.transcribe(audio_path or "")
        except Exception as exc:
            LOG.warning("voice provider stt failed: %s", exc)
        return ""

    # ------------------------------------------------------------ tts
    def speak(self, text: str) -> bool:
        """Speak text via an available TTS binary."""
        if not text:
            return False
        if self.tts == "env":
            return self._env_speak(text)
        return False

    def _env_speak(self, text: str) -> bool:
        for binary, args in (("espeak", ["-v", "en"]),
                             ("espeak-ng", []),
                             ("say", [])):
            path = shutil.which(binary)
            if not path:
                continue
            try:
                subprocess.run([path, *args, text], timeout=30)
                return True
            except Exception:
                continue
        LOG.info("no TTS binary found; text only: %s", text[:60])
        return False