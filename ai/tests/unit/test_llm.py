"""Tests for the LLM client and registry (no network: transport mocked)."""

import io
import json
import os
import sys
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from ai.llm import LLMClient, LLMRegistry


class _FakeResponse:
    def __init__(self, payload):
        self._payload = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return self._payload


def _fake_urlopen(payload):
    return mock.patch("urllib.request.urlopen", return_value=_FakeResponse(payload))


LOCAL = "http://localhost:9999/v1"


class TestLLMClient(unittest.TestCase):
    def test_complete_parses_and_strips(self):
        client = LLMClient(model="test", base_url=LOCAL)
        payload = {"choices": [{"message": {"content": "  hi there  "}}]}
        with _fake_urlopen(payload):
            out = client.complete("hello")
        self.assertEqual(out, "hi there")

    def test_chat_posts_message_list(self):
        client = LLMClient(model="test", base_url=LOCAL)
        payload = {"choices": [{"message": {"content": "ok"}}]}
        with _fake_urlopen(payload):
            out = client.chat([{"role": "user", "content": "hi"}])
        self.assertEqual(out, "ok")

    def test_transport_failure_returns_empty(self):
        client = LLMClient(model="test", base_url=LOCAL)
        with mock.patch("urllib.request.urlopen", side_effect=OSError("no")):
            self.assertEqual(client.complete("hi"), "")

    def test_bad_payload_returns_empty(self):
        client = LLMClient(model="test", base_url=LOCAL)
        with _fake_urlopen({"choices": []}):
            self.assertEqual(client.complete("hi"), "")


class TestLLMRegistry(unittest.TestCase):
    def test_known_models(self):
        reg = LLMRegistry()
        self.assertIn("llama3.2", reg.list())

    def test_register(self):
        reg = LLMRegistry()
        reg.register("my-model", "custom", "http://x/v1")
        self.assertEqual(reg.get("my-model")["provider"], "custom")

    def test_by_purpose(self):
        reg = LLMRegistry()
        self.assertTrue(reg.by_purpose("chat"))

    def test_unknown_get(self):
        reg = LLMRegistry()
        self.assertEqual(reg.get("nope"), {})


if __name__ == "__main__":
    unittest.main()