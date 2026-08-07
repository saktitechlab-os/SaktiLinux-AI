"""Tests for the voice engine and wake word."""

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from ai.voice import VoiceEngine, WakeWord


class TestVoiceEngine(unittest.TestCase):
    def test_start_stop(self):
        engine = VoiceEngine()
        self.assertFalse(engine.listening)
        engine.start()
        self.assertTrue(engine.listening)
        engine.stop()
        self.assertFalse(engine.listening)

    def test_offline_stt_returns_empty(self):
        engine = VoiceEngine(stt_backend="offline")
        self.assertEqual(engine.hear(), "")

    def test_speak_missing_binary_returns_false(self):
        engine = VoiceEngine(tts_backend="env")
        self.assertFalse(engine.speak("hello world"))


class TestWakeWord(unittest.TestCase):
    def setUp(self):
        self.wake = WakeWord()

    def test_detect_active(self):
        self.assertEqual(self.wake.detect("hey sakti, list files"),
                         "hey sakti")

    def test_no_match(self):
        self.assertIsNone(self.wake.detect("just regular text"))

    def test_is_active(self):
        self.assertTrue(self.wake.is_active("ok sakti run test"))
        self.assertFalse(self.wake.is_active("nothing to see"))

    def test_case_insensitive(self):
        self.assertTrue(self.wake.is_active("HEY SAKTI"))


if __name__ == "__main__":
    unittest.main()