"""Tests for the provider manager and ollama provider."""

import os
import sys
import tempfile
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from ai.providers import OllamaProvider, Provider, ProviderManager


class TestProviderBase(unittest.TestCase):
    def test_provider_is_abstract(self):
        with self.assertRaises(TypeError):
            Provider()


class TestOllamaProvider(unittest.TestCase):
    def test_complete_local(self):
        # Without a live ollama, transport fails -> empty, but no raise.
        provider = OllamaProvider(model="llama3.2")
        self.assertEqual(provider.complete("hi"), "")

    def test_available_false_when_down(self):
        provider = OllamaProvider()
        self.assertFalse(provider.available())

    def test_models(self):
        provider = OllamaProvider(model="mistral")
        self.assertEqual(provider.models(), ["mistral"])


class TestProviderManager(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp(prefix="sakti_prov_")
        self.config = os.path.join(self._tmp, "providers.json")

    def test_defaults_to_ollama(self):
        pm = ProviderManager(config_path=self.config)
        self.assertIn("ollama", pm._providers)

    def test_provider_none_when_unavailable(self):
        pm = ProviderManager(config_path=self.config)
        # ollama is down in CI -> provider() may return None; must not raise.
        pm.provider("chat")

    def test_register_unknown_fails(self):
        pm = ProviderManager(config_path=self.config)
        self.assertFalse(pm.register("not-a-provider"))

    def test_set_active(self):
        pm = ProviderManager(config_path=self.config)
        pm.set_active("chat", "ollama")
        self.assertEqual(pm._active["chat"], "ollama")


if __name__ == "__main__":
    unittest.main()